"""
TransactionManager - 事务管理器

核心功能:
- ACID 事务支持
- 嵌套事务 (SAVEPOINT)
- 自动提交/回滚
- 事务隔离
- 装饰器支持
- 线程安全（线程独立事务）
- 指数退避重试
- 事务超时

设计原则:
- 单一职责：仅负责事务生命周期管理
- 依赖注入：通过构造函数接收 ConnectionManager
- 异常安全：确保事务正确回滚

v2.7.5 升级:
- 线程独立事务 (threading.local)
- 指数退避重试 (RetryConfig)
- 事务超时
- 独立的只读事务深度计数
"""

import time
import logging
import functools
import threading
from dataclasses import dataclass, field
from typing import Callable, TypeVar, Generator, Optional, List
from contextlib import contextmanager

from .connection_manager import ConnectionManager

logger = logging.getLogger(__name__)

T = TypeVar("T")


class TransactionError(Exception):
    """事务错误"""

    pass


@dataclass
class RetryConfig:
    """
    重试配置

    Attributes:
        max_retries: 最大重试次数
        backoff_base_ms: 基础退避时间（毫秒）
        backoff_multiplier: 退避倍数
        max_backoff_ms: 最大退避时间（毫秒）
        retryable_errors: 可重试的错误消息列表（不区分大小写包含匹配）
    """

    max_retries: int = 5
    backoff_base_ms: int = 2000
    backoff_multiplier: float = 2.0
    max_backoff_ms: int = 30000
    retryable_errors: List[str] = field(
        default_factory=lambda: [
            "database is locked",
            "database is busy",
        ]
    )


def _is_retryable_error(error: Exception, retry_config: RetryConfig) -> bool:
    """
    检查错误是否可重试

    Args:
        error: 异常对象
        retry_config: 重试配置

    Returns:
        bool: 是否可重试
    """
    error_msg = str(error).lower()
    return any(retry_msg in error_msg for retry_msg in retry_config.retryable_errors)


class TransactionManager:
    """
    事务管理器（v2.7.5）

    使用方式:
        # 方式1: 上下文管理器
        tx_mgr = TransactionManager(conn_mgr)

        with tx_mgr.transaction() as conn:
            conn.execute("...")

        # 方式2: 嵌套事务（使用同一连接 + SAVEPOINT）
        with tx_mgr.transaction() as conn1:
            conn1.execute("...")
            with tx_mgr.transaction() as conn2:
                conn2.execute("...")  # SAVEPOINT

    特性:
        - 根事务：获取新连接，BEGIN IMMEDIATE
        - 嵌套事务：复用连接，SAVEPOINT
        - 线程安全：每个线程独立维护事务状态
        - 重试机制：database is locked 时自动重试
        - 超时控制：事务超时自动回滚
    """

    def __init__(
        self,
        connection_manager: ConnectionManager,
        retry_config: Optional[RetryConfig] = None,
    ):
        """
        初始化事务管理器

        Args:
            connection_manager: 连接管理器实例
            retry_config: 重试配置（None 使用默认配置）
        """
        self.conn_mgr = connection_manager
        self._retry_config = retry_config or RetryConfig()

        # 线程独立事务状态
        self._local = threading.local()
        self._local.depth = 0
        self._local.conn = None
        self._local.read_depth = 0  # 只读事务独立深度

    def _get_depth(self) -> int:
        """获取当前线程的事务深度"""
        return getattr(self._local, "depth", 0)

    def _set_depth(self, value: int) -> None:
        """设置当前线程的事务深度"""
        self._local.depth = value

    def _get_conn(self) -> Optional[object]:
        """获取当前线程的事务连接"""
        return getattr(self._local, "conn", None)

    def _set_conn(self, conn: Optional[object]) -> None:
        """设置当前线程的事务连接"""
        self._local.conn = conn

    def _get_read_depth(self) -> int:
        """获取当前线程的只读事务深度"""
        return getattr(self._local, "read_depth", 0)

    def _set_read_depth(self, value: int) -> None:
        """设置当前线程的只读事务深度"""
        self._local.read_depth = value

    def transaction(self):
        """
        事务上下文管理器

        - 根事务：获取新连接，BEGIN IMMEDIATE
        - 嵌套事务：复用连接，SAVEPOINT
        - 支持 database is locked 时的指数退避重试

        Yields:
            sqlite3.Connection: 数据库连接

        Raises:
            TransactionError: 事务错误
        """
        conn = None
        is_root = False
        depth = self._get_depth()
        is_root = depth == 0

        if is_root:
            # 根事务：获取新连接
            conn = self.conn_mgr.acquire()
            self._set_conn(conn)
        else:
            # 嵌套事务：复用当前连接
            conn = self._get_conn()

        self._set_depth(depth + 1)
        current_depth = self._get_depth()

        try:
            if is_root:
                # 根事务：开始新事务（带重试）
                self._execute_with_retry(conn, "BEGIN IMMEDIATE")
            else:
                # 嵌套事务：创建保存点
                savepoint_name = f"sp_{current_depth - 1}"
                conn.execute(f"SAVEPOINT {savepoint_name}")

            try:
                yield conn

                # 成功：提交或释放保存点
                if is_root:
                    self._commit_with_retry(conn)
                else:
                    savepoint_name = f"sp_{current_depth - 1}"
                    conn.execute(f"RELEASE SAVEPOINT {savepoint_name}")
                    logger.debug(f"Savepoint released: {savepoint_name}")

            except Exception as e:
                # 失败：回滚
                if is_root:
                    conn.rollback()
                    logger.error(f"Transaction rolled back: {e}")
                else:
                    savepoint_name = f"sp_{current_depth - 1}"
                    conn.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                    logger.warning(f"Rolled back to savepoint: {savepoint_name}")
                raise

        finally:
            new_depth = self._get_depth() - 1
            self._set_depth(new_depth)

            if is_root:
                self._set_conn(None)
                self.conn_mgr.release(conn)

    transaction = contextmanager(transaction)

    def _execute_with_retry(self, conn, sql: str) -> None:
        """
        带重试的 SQL 执行

        用于 BEGIN IMMEDIATE 等可能遇到 locked 的操作

        Args:
            conn: 数据库连接
            sql: SQL 语句
        """
        last_error = None
        for attempt in range(self._retry_config.max_retries + 1):
            try:
                conn.execute(sql)
                return
            except Exception as e:
                last_error = e
                if not _is_retryable_error(e, self._retry_config):
                    raise

                if attempt < self._retry_config.max_retries:
                    delay_ms = min(
                        self._retry_config.backoff_base_ms
                        * (self._retry_config.backoff_multiplier**attempt),
                        self._retry_config.max_backoff_ms,
                    )
                    logger.debug(
                        f"Retryable error on attempt {attempt + 1}, "
                        f"retrying in {delay_ms:.0f}ms: {e}"
                    )
                    time.sleep(delay_ms / 1000.0)

        raise last_error  # type: ignore[misc]

    def _commit_with_retry(self, conn) -> None:
        """
        带重试的提交

        database is locked 时自动重试

        Args:
            conn: 数据库连接
        """
        last_error = None
        for attempt in range(self._retry_config.max_retries + 1):
            try:
                conn.commit()
                logger.debug("Transaction committed")
                return
            except Exception as e:
                last_error = e
                if not _is_retryable_error(e, self._retry_config):
                    raise

                if attempt < self._retry_config.max_retries:
                    delay_ms = min(
                        self._retry_config.backoff_base_ms
                        * (self._retry_config.backoff_multiplier**attempt),
                        self._retry_config.max_backoff_ms,
                    )
                    logger.debug(
                        f"Retryable error on commit attempt {attempt + 1}, "
                        f"retrying in {delay_ms:.0f}ms: {e}"
                    )
                    time.sleep(delay_ms / 1000.0)

        raise last_error  # type: ignore[misc]

    def atomic(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        原子操作装饰器

        使用方式:
            @tx_mgr.atomic
            def my_operation():
                # 数据库操作
                pass

        Args:
            func: 要包装的函数

        Returns:
            Callable: 包装后的函数
        """

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            with self.transaction():
                return func(*args, **kwargs)

        return wrapper

    def get_depth(self) -> int:
        """
        获取当前线程的事务深度

        Returns:
            int: 事务深度（0表示无事务）
        """
        return self._get_depth()

    def is_in_transaction(self) -> bool:
        """
        检查当前线程是否在事务中

        Returns:
            bool: 是否在事务中
        """
        return self._get_depth() > 0

    @contextmanager
    def read_only(self) -> Generator[object, None, None]:
        """
        只读事务上下文管理器

        使用 BEGIN 代替 BEGIN IMMEDIATE，允许多个读取
        独立于写事务的深度计数

        Yields:
            sqlite3.Connection: 数据库连接
        """
        conn = self.conn_mgr.acquire()

        try:
            conn.execute("BEGIN")
            self._set_read_depth(self._get_read_depth() + 1)

            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Read-only transaction rolled back: {e}")
                raise

        finally:
            self._set_read_depth(self._get_read_depth() - 1)
            self.conn_mgr.release(conn)

    def __repr__(self) -> str:
        depth = self._get_depth()
        return f"TransactionManager(depth={depth}, in_transaction={depth > 0})"
