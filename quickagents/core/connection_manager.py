"""
ConnectionManager - 连接管理器

核心功能:
- 连接池管理
- 线程安全
- 自动重连
- 连接健康检查
- WAL模式优化

设计原则:
- 单一职责：仅负责连接生命周期管理
- 依赖注入：通过构造函数接收配置
- 资源安全：确保连接正确释放
"""

import sqlite3
import logging
from typing import Optional, Generator
from contextlib import contextmanager
from threading import Lock
from pathlib import Path

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    连接管理器
    
    使用方式:
        conn_mgr = ConnectionManager('.quickagents/unified.db')
        
        with conn_mgr.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM memory')
            results = cursor.fetchall()
    
    配置参数:
        db_path: 数据库文件路径
        pool_size: 连接池大小（默认5）
        timeout: 连接超时时间（秒，默认30）
    """
    
    def __init__(
        self,
        db_path: str = ".quickagents/unified.db",
        pool_size: int = 5,
        timeout: float = 30.0
    ):
        """
        初始化连接管理器
        
        Args:
            db_path: 数据库文件路径
            pool_size: 连接池大小
            timeout: 连接超时时间（秒）
        """
        self.db_path = Path(db_path)
        self.pool_size = max(1, pool_size)
        self.timeout = timeout
        
        # 线程安全锁
        self._lock = Lock()
        
        # 连接池
        self._pool: list[sqlite3.Connection] = []
        self._active_connections: set[sqlite3.Connection] = set()
        
        # 确保数据库目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化连接池
        self._init_pool()
        
        logger.debug(f"ConnectionManager initialized: {db_path}, pool_size={pool_size}")
    
    def _init_pool(self) -> None:
        """初始化连接池"""
        for _ in range(self.pool_size):
            conn = self._create_connection()
            self._pool.append(conn)
    
    def _create_connection(self) -> sqlite3.Connection:
        """
        创建新连接
        
        Returns:
            sqlite3.Connection: 新的数据库连接
        """
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=self.timeout,
            check_same_thread=False
        )
        
        # 启用外键约束
        conn.execute("PRAGMA foreign_keys = ON")
        
        # 启用 WAL 模式（Write-Ahead Logging）
        # 优势：并发读取、更好的性能
        conn.execute("PRAGMA journal_mode = WAL")
        
        # 设置忙碌超时
        conn.execute(f"PRAGMA busy_timeout = {int(self.timeout * 1000)}")
        
        # 设置同步模式为 NORMAL（性能与安全的平衡）
        conn.execute("PRAGMA synchronous = NORMAL")
        
        # 设置缓存大小（负数表示KB，-64000表示64MB）
        conn.execute("PRAGMA cache_size = -64000")
        
        return conn
    
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
        except Exception:
            conn.rollback()
            raise
        finally:
            self._release(conn)
    
    def _acquire(self) -> sqlite3.Connection:
        """
        从连接池获取连接
        
        Returns:
            sqlite3.Connection: 数据库连接
        """
        with self._lock:
            if self._pool:
                conn = self._pool.pop()
            else:
                # 连接池为空，创建新连接
                conn = self._create_connection()
                logger.debug("Connection pool exhausted, creating new connection")
            
            self._active_connections.add(conn)
            return conn
    
    def _release(self, conn: sqlite3.Connection) -> None:
        """
        释放连接回连接池
        
        Args:
            conn: 要释放的连接
        """
        with self._lock:
            if conn in self._active_connections:
                self._active_connections.remove(conn)
                
                if len(self._pool) < self.pool_size:
                    # 连接池未满，放回池中
                    self._pool.append(conn)
                else:
                    # 连接池已满，关闭连接
                    try:
                        conn.close()
                    except Exception as e:
                        logger.warning(f"Failed to close connection: {e}")
    
    def close_all(self) -> None:
        """
        关闭所有连接（池中+活跃）
        
        用于优雅关闭
        """
        with self._lock:
            # 关闭池中连接
            for conn in self._pool:
                try:
                    conn.close()
                except Exception as e:
                    logger.warning(f"Failed to close pooled connection: {e}")
            self._pool.clear()
            
            # 关闭活跃连接
            for conn in self._active_connections:
                try:
                    conn.close()
                except Exception as e:
                    logger.warning(f"Failed to close active connection: {e}")
            self._active_connections.clear()
            
            logger.debug("All connections closed")
    
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
                "db_path": str(self.db_path)
            }
    
    def __enter__(self) -> 'ConnectionManager':
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器退出"""
        self.close_all()
    
    def __repr__(self) -> str:
        return (
            f"ConnectionManager(db_path='{self.db_path}', "
            f"pool_size={self.pool_size}, "
            f"available={len(self._pool)}, "
            f"active={len(self._active_connections)})"
        )
    
    def __del__(self):
        """Auto-close all connections on garbage collection"""
        try:
            self.close_all()
        except Exception:
            pass
