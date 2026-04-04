"""
ConnectionManager - 连接管理器

核心功能:
- 动态连接池（按需创建，空闲回收）
- 线程安全
- 连接验证 (pre_ping)
- PRAGMA 性能优化（mmap, temp_store, wal_autocheckpoint）
- 连接池指标收集
- WAL 自动 Checkpoint

设计原则:
- 单一职责：仅负责连接生命周期管理
- 依赖注入：通过构造函数接收配置
- 资源安全：确保连接正确释放
- 向后兼容：保持 v2.7.0 公共接口不变

v2.7.5 升级:
- 动态连接池（min_size/max_size 替代固定 pool_size）
- pre_ping 连接验证
- PRAGMA 增强 (mmap_size, temp_store, page_size, wal_autocheckpoint)
- 连接池指标 (hit_rate, wait_time, created_count, error_count)
- 空闲连接超时回收
- WAL 自动 Checkpoint
"""

import sqlite3
import time
import logging
import atexit
import threading
from dataclasses import dataclass, field
from typing import Optional, Generator, Dict, Any, List
from contextlib import contextmanager
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PoolConfig:
    """
    连接池配置

    Attributes:
        min_size: 最小连接数（预创建）
        max_size: 最大连接数
        idle_timeout: 空闲连接超时（秒），超时后自动关闭
        max_lifetime: 连接最大存活时间（秒），超时后重建
        pre_ping: 获取连接前是否验证存活
        acquire_timeout: 获取连接超时（秒）
    """

    min_size: int = 1
    max_size: int = 10
    idle_timeout: float = 300.0
    max_lifetime: float = 3600.0
    pre_ping: bool = True
    acquire_timeout: float = 30.0


@dataclass
class _PooledConnection:
    """池化连接包装，携带元数据"""

    conn: sqlite3.Connection
    created_at: float = field(default_factory=time.time)
    last_used_at: float = field(default_factory=time.time)

    @property
    def age(self) -> float:
        """连接存活时间（秒）"""
        return time.time() - self.created_at

    @property
    def idle_time(self) -> float:
        """空闲时间（秒）"""
        return time.time() - self.last_used_at

    def touch(self):
        """更新最后使用时间"""
        self.last_used_at = time.time()


@dataclass
class PoolMetrics:
    """连接池指标"""

    created_count: int = 0  # 总创建数
    reused_count: int = 0  # 复用次数
    total_wait_ms: float = 0.0  # 总等待时间（毫秒）
    error_count: int = 0  # 错误次数
    pre_ping_failures: int = 0  # pre_ping 失败次数
    evicted_count: int = 0  # 驱逐（超时回收）次数

    @property
    def hit_rate(self) -> float:
        """连接池命中率"""
        total = self.created_count + self.reused_count
        if total == 0:
            return 0.0
        return self.reused_count / total

    @property
    def avg_wait_ms(self) -> float:
        """平均等待时间（毫秒）"""
        total = self.created_count + self.reused_count
        if total == 0:
            return 0.0
        return self.total_wait_ms / total


class ConnectionManager:
    """
    连接管理器（v2.7.5）

    使用方式:
        conn_mgr = ConnectionManager('.quickagents/unified.db')

        with conn_mgr.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM memory')
            results = cursor.fetchall()

    向后兼容:
        pool_size 参数仍然支持，内部转换为 min_size=max_size=pool_size
        timeout 参数仍然支持，映射到 acquire_timeout

    配置参数:
        db_path: 数据库文件路径
        pool_size: 连接池大小（向后兼容，设置 min=max=pool_size）
        timeout: 连接超时时间（秒）
        pool_config: 高级连接池配置（PoolConfig 实例）
    """

    def __init__(
        self,
        db_path: str = ".quickagents/unified.db",
        pool_size: int = 5,
        timeout: float = 30.0,
        pool_config: Optional[PoolConfig] = None,
    ):
        """
        初始化连接管理器

        Args:
            db_path: 数据库文件路径
            pool_size: 连接池大小（向后兼容）
            timeout: 连接超时时间（秒，向后兼容）
            pool_config: 高级连接池配置（优先于 pool_size）
        """
        self.db_path = Path(db_path)
        self.timeout = timeout

        # 连接池配置
        if pool_config is not None:
            self._pool_config = pool_config
        else:
            # 向后兼容：pool_size 同时设置 min 和 max
            self._pool_config = PoolConfig(
                min_size=pool_size, max_size=pool_size, acquire_timeout=timeout
            )

        # 向后兼容属性
        self.pool_size = self._pool_config.max_size

        # 线程安全锁
        self._lock = threading.Lock()
        # 获取连接的条件变量（用于等待连接释放）
        self._pool_condition = threading.Condition(self._lock)

        # 连接池：存储 _PooledConnection 包装对象
        self._pool: List[_PooledConnection] = []
        self._active_connections: set = set()

        # 连接池指标
        self._metrics = PoolMetrics()

        # WAL Checkpoint 控制
        self._last_checkpoint_time = time.time()
        self._checkpoint_interval = 300.0  # 5分钟
        self._operations_since_checkpoint = 0
        self._checkpoint_threshold = 1000  # 每1000次操作

        # 确保数据库目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 初始化连接池（创建 min_size 个连接）
        self._init_pool()

        # 注册退出清理
        atexit.register(self._cleanup)

        logger.debug(
            f"ConnectionManager initialized: {db_path}, "
            f"min={self._pool_config.min_size}, max={self._pool_config.max_size}, "
            f"pre_ping={self._pool_config.pre_ping}"
        )

    def _init_pool(self) -> None:
        """初始化连接池（创建 min_size 个连接）"""
        for _ in range(self._pool_config.min_size):
            conn = self._create_connection()
            self._pool.append(_PooledConnection(conn=conn))

    def _create_connection(self) -> sqlite3.Connection:
        """
        创建新连接并配置 PRAGMA

        Returns:
            sqlite3.Connection: 新的数据库连接
        """
        conn = sqlite3.connect(
            str(self.db_path), timeout=self.timeout, check_same_thread=False
        )

        # === PRAGMA 配置（v2.7.5 增强）===

        # 外键约束
        conn.execute("PRAGMA foreign_keys = ON")

        # WAL 模式（Write-Ahead Logging）- 并发读取
        conn.execute("PRAGMA journal_mode = WAL")

        # 忙碌超时（毫秒）
        conn.execute(f"PRAGMA busy_timeout = {int(self.timeout * 1000)}")

        # 同步模式 NORMAL - 性能与安全的平衡
        conn.execute("PRAGMA synchronous = NORMAL")

        # 缓存大小 -20MB（负数表示KB）
        conn.execute("PRAGMA cache_size = -20000")

        # === v2.7.5 新增 PRAGMA ===

        # mmap_size = 256MB - 内存映射提升读取性能 40%+
        try:
            conn.execute("PRAGMA mmap_size = 268435456")
        except sqlite3.Error as e:
            # 某些平台可能不支持 mmap，静默降级
            logger.debug(f"mmap_size not supported, falling back: {e}")

        # temp_store = MEMORY - 临时表在内存中
        conn.execute("PRAGMA temp_store = MEMORY")

        # page_size = 4096 - 4KB 页大小（需在创建数据库时设置）
        # 注意：对于已有数据库，page_size 不可更改，不执行
        # 仅在新建数据库时生效

        # wal_autocheckpoint = 1000 - 每1000页自动 checkpoint
        conn.execute("PRAGMA wal_autocheckpoint = 1000")

        return conn

    def _validate_connection(self, conn: sqlite3.Connection) -> bool:
        """
        验证连接是否存活

        Args:
            conn: 数据库连接

        Returns:
            bool: 连接是否存活
        """
        try:
            cursor = conn.execute("SELECT 1")
            return cursor.fetchone()[0] == 1
        except Exception:
            return False

    def _evict_idle_connections(self) -> None:
        """
        回收空闲超时的连接

        必须在持有锁的情况下调用
        """
        time.time()
        to_evict = []

        for pooled in self._pool:
            if pooled.idle_time > self._pool_config.idle_timeout:
                to_evict.append(pooled)

        for pooled in to_evict:
            self._pool.remove(pooled)
            try:
                pooled.conn.close()
            except Exception as e:
                logger.warning(f"Failed to close evicted connection: {e}")
            self._metrics.evicted_count += 1

        if to_evict:
            logger.debug(f"Evicted {len(to_evict)} idle connections")

    def _maybe_checkpoint_wal(self) -> None:
        """
        条件性 WAL Checkpoint

        每 checkpoint_threshold 次操作 或 checkpoint_interval 秒
        执行一次 PRAGMA wal_checkpoint(TRUNCATE)

        使用独立临时连接执行，避免影响池中连接状态。
        """
        self._operations_since_checkpoint += 1

        should_checkpoint = (
            self._operations_since_checkpoint >= self._checkpoint_threshold
            or (time.time() - self._last_checkpoint_time) >= self._checkpoint_interval
        )

        if not should_checkpoint:
            return

        # 尝试获取锁执行 checkpoint（非阻塞）
        # 如果锁被占用则跳过，下次再试
        if self._lock.acquire(blocking=False):
            try:
                # 使用独立临时连接，避免操作池中连接
                try:
                    checkpoint_conn = sqlite3.connect(
                        str(self.db_path), timeout=5.0, check_same_thread=False
                    )
                    try:
                        checkpoint_conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                        logger.debug("WAL checkpoint completed (TRUNCATE)")
                    finally:
                        checkpoint_conn.close()
                except Exception as e:
                    logger.warning(f"WAL checkpoint failed: {e}")

                self._operations_since_checkpoint = 0
                self._last_checkpoint_time = time.time()
            finally:
                self._lock.release()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        获取连接（上下文管理器）

        使用方式:
            with conn_mgr.get_connection() as conn:
                cursor = conn.execute('SELECT * FROM memory')
                results = cursor.fetchall()

        Yields:
            sqlite3.Connection: 数据库连接

        Raises:
            sqlite3.Error: 数据库错误
        """
        conn = self._acquire()
        try:
            yield conn
            conn.commit()  # 正常退出时自动提交
        except Exception:
            conn.rollback()  # 异常时回滚
            raise
        finally:
            self._release(conn)
            # 操作完成后检查 WAL checkpoint
            try:
                self._maybe_checkpoint_wal()
            except Exception:
                pass  # checkpoint 失败不影响业务

    def acquire(self) -> sqlite3.Connection:
        """
        从连接池获取连接（公共接口）

        获取后必须调用 release() 归还连接。
        推荐使用 get_connection() 上下文管理器自动管理。

        Returns:
            sqlite3.Connection: 数据库连接

        Example:
            conn = conn_mgr.acquire()
            try:
                conn.execute("SELECT 1")
            finally:
                conn_mgr.release(conn)
        """
        return self._acquire()

    def release(self, conn: sqlite3.Connection) -> None:
        """
        释放连接回连接池（公共接口）

        Args:
            conn: 要释放的连接
        """
        self._release(conn)

    def _acquire(self) -> sqlite3.Connection:
        """
        从连接池获取连接（内部实现）

        流程:
        1. 回收空闲超时连接
        2. 检查池中是否有可用连接
           - 有且 pre_ping=True → 验证存活
           - 有且 pre_ping=False → 直接使用
        3. 池空 → 在 max_size 限制内创建新连接
        4. 达到 max_size → 等待其他线程释放

        Returns:
            sqlite3.Connection: 数据库连接
        """
        start_time = time.time()

        with self._pool_condition:
            # 回收空闲连接
            self._evict_idle_connections()

            # 尝试从池中获取
            while True:
                if self._pool:
                    pooled = self._pool.pop(0)

                    # pre_ping 验证
                    if self._pool_config.pre_ping:
                        if not self._validate_connection(pooled.conn):
                            # 连接已死，关闭并创建新的
                            try:
                                pooled.conn.close()
                            except Exception:
                                pass
                            self._metrics.pre_ping_failures += 1
                            pooled = _PooledConnection(conn=self._create_connection())
                            self._metrics.created_count += 1
                        else:
                            self._metrics.reused_count += 1
                    else:
                        # 检查连接最大存活时间
                        if pooled.age > self._pool_config.max_lifetime:
                            try:
                                pooled.conn.close()
                            except Exception:
                                pass
                            pooled = _PooledConnection(conn=self._create_connection())
                            self._metrics.created_count += 1
                        else:
                            self._metrics.reused_count += 1

                    pooled.touch()
                    self._active_connections.add(pooled.conn)

                    # 记录等待时间
                    wait_ms = (time.time() - start_time) * 1000
                    self._metrics.total_wait_ms += wait_ms

                    return pooled.conn

                # 池空，检查是否可以创建新连接
                total_connections = len(self._active_connections) + len(self._pool)
                if total_connections < self._pool_config.max_size:
                    # 创建新连接
                    conn = self._create_connection()
                    self._active_connections.add(conn)
                    self._metrics.created_count += 1

                    wait_ms = (time.time() - start_time) * 1000
                    self._metrics.total_wait_ms += wait_ms

                    return conn

                # 达到上限，等待连接释放
                remaining = self._pool_config.acquire_timeout - (
                    time.time() - start_time
                )
                if remaining <= 0:
                    self._metrics.error_count += 1
                    raise sqlite3.Error(
                        f"Connection pool exhausted: max_size={self._pool_config.max_size}, "
                        f"active={len(self._active_connections)}, "
                        f"waited={self._pool_config.acquire_timeout}s"
                    )

                # 等待连接释放（最多等待 remaining 秒）
                self._pool_condition.wait(timeout=min(remaining, 1.0))

    def _release(self, conn: sqlite3.Connection) -> None:
        """
        释放连接回连接池

        Args:
            conn: 要释放的连接
        """
        with self._pool_condition:
            if conn in self._active_connections:
                self._active_connections.discard(conn)

                # 检查连接池是否还有空间（不超过 max_size）
                if len(self._pool) < self._pool_config.max_size:
                    # 检查连接是否还可用
                    if self._validate_connection(conn):
                        self._pool.append(_PooledConnection(conn=conn))
                    else:
                        try:
                            conn.close()
                        except Exception:
                            pass
                else:
                    # 连接池已满，关闭连接
                    try:
                        conn.close()
                    except Exception as e:
                        logger.warning(f"Failed to close excess connection: {e}")

                # 通知等待的线程
                self._pool_condition.notify()

    def close_all(self) -> None:
        """
        关闭所有连接（池中+活跃）

        用于优雅关闭
        """
        with self._lock:
            # 关闭池中连接
            for pooled in self._pool:
                try:
                    pooled.conn.close()
                except Exception as e:
                    logger.warning(f"Failed to close pooled connection: {e}")
            self._pool.clear()

            # 关闭活跃连接
            for conn in list(self._active_connections):
                try:
                    conn.close()
                except Exception as e:
                    logger.warning(f"Failed to close active connection: {e}")
            self._active_connections.clear()

            logger.debug("All connections closed")

    def _cleanup(self) -> None:
        """退出时清理资源"""
        try:
            self.close_all()
        except Exception:
            pass

    def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 数据库是否健康
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("SELECT 1")
                return cursor.fetchone()[0] == 1
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def get_pool_status(self) -> dict:
        """
        获取连接池状态

        Returns:
            dict: 连接池状态信息
        """
        with self._lock:
            return {
                "pool_size": self.pool_size,
                "available": len(self._pool),
                "active": len(self._active_connections),
                "db_path": str(self.db_path),
            }

    def get_pool_metrics(self) -> Dict[str, Any]:
        """
        获取连接池详细指标

        Returns:
            dict: 连接池指标
        """
        with self._lock:
            return {
                # 连接池状态
                "pool_size": self.pool_size,
                "min_size": self._pool_config.min_size,
                "max_size": self._pool_config.max_size,
                "available": len(self._pool),
                "active": len(self._active_connections),
                "db_path": str(self.db_path),
                # 配置
                "pre_ping": self._pool_config.pre_ping,
                "idle_timeout": self._pool_config.idle_timeout,
                "max_lifetime": self._pool_config.max_lifetime,
                # 指标
                "metrics": {
                    "created_count": self._metrics.created_count,
                    "reused_count": self._metrics.reused_count,
                    "hit_rate": round(self._metrics.hit_rate, 4),
                    "avg_wait_ms": round(self._metrics.avg_wait_ms, 2),
                    "total_wait_ms": round(self._metrics.total_wait_ms, 2),
                    "error_count": self._metrics.error_count,
                    "pre_ping_failures": self._metrics.pre_ping_failures,
                    "evicted_count": self._metrics.evicted_count,
                },
                # WAL 状态
                "wal": {
                    "operations_since_checkpoint": self._operations_since_checkpoint,
                    "last_checkpoint_time": self._last_checkpoint_time,
                },
            }

    @property
    def pool_config(self) -> PoolConfig:
        """获取连接池配置"""
        return self._pool_config

    def __enter__(self) -> "ConnectionManager":
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器退出"""
        self.close_all()

    def __repr__(self) -> str:
        return (
            f"ConnectionManager(db_path='{self.db_path}', "
            f"min={self._pool_config.min_size}, max={self._pool_config.max_size}, "
            f"available={len(self._pool)}, "
            f"active={len(self._active_connections)}, "
            f"hit_rate={self._metrics.hit_rate:.2%})"
        )

    def __del__(self):
        """垃圾回收时自动关闭连接"""
        try:
            self.close_all()
        except Exception:
            pass
