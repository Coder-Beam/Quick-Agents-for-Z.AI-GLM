"""
Session - 统一数据库会话接口

核心功能:
- 只读查询: session.query()
- 读写事务: session.transaction()
- 只读事务: session.read_only()
- 单条执行: session.execute()
- 批量执行: session.executescript()

设计原则:
- 薄封装: 委托给 ConnectionManager + TransactionManager
- 单一入口: 所有模块通过 Session 访问数据库
- 向后兼容: 不破坏任何现有公共 API
"""

import sqlite3
import logging
from contextlib import contextmanager
from typing import Any, Generator, Optional

logger = logging.getLogger(__name__)


class Session:
    """
    统一数据库会话接口

    使用方式:
        session = Session(conn_mgr, tx_mgr)

        # 只读查询
        with session.query() as conn:
            cursor = conn.execute('SELECT * FROM memory')
            rows = cursor.fetchall()

        # 读写事务
        with session.transaction() as conn:
            conn.execute('INSERT INTO memory (...) VALUES (...)')

        # 单条执行（自动 commit）
        session.execute('UPDATE memory SET value = ? WHERE key = ?', ('new_val', 'my.key'))

    特性:
        - 隐藏 ConnectionManager / TransactionManager 的实现细节
        - 所有数据库访问都通过 Session 进行
        - 完全线程安全（底层 CM/TM 保证）
    """

    def __init__(self, connection_manager, transaction_manager):
        """
        初始化 Session

        Args:
            connection_manager: ConnectionManager 实例
            transaction_manager: TransactionManager 实例
        """
        self._cm = connection_manager
        self._tm = transaction_manager

    @property
    def connection_manager(self):
        """底层连接管理器（向后兼容）"""
        return self._cm

    @property
    def transaction_manager(self):
        """底层事务管理器（向后兼容）"""
        return self._tm

    # ==================== 查询接口 ====================

    @contextmanager
    def query(self) -> Generator[sqlite3.Connection, None, None]:
        """
        获取只读连接（自动归还到连接池）

        适用于 SELECT 查询，不需要事务保护的场景。
        退出上下文时自动 commit（如果连接中有未提交事务）。

        Yields:
            sqlite3.Connection: 数据库连接
        """
        with self._cm.get_connection() as conn:
            yield conn

    # ==================== 事务接口 ====================

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """
        获取读写事务连接

        支持 BEGIN IMMEDIATE + SAVEPOINT 嵌套。
        自动重试（指数退避）。

        Yields:
            sqlite3.Connection: 事务中的数据库连接
        """
        with self._tm.transaction() as conn:
            yield conn

    @contextmanager
    def read_only(self) -> Generator[sqlite3.Connection, None, None]:
        """
        获取只读事务连接

        使用 BEGIN（非 IMMEDIATE），允许并发读取。
        独立于写事务的深度计数。

        Yields:
            sqlite3.Connection: 只读事务中的数据库连接
        """
        with self._tm.read_only() as conn:
            yield conn

    # ==================== 便捷方法 ====================

    def execute(self, sql: str, params: tuple = None) -> Any:
        """
        执行单条 SQL 语句（自动 commit）

        适用于不需要事务的简单写入操作。

        Args:
            sql: SQL 语句
            params: 参数元组

        Returns:
            cursor 执行结果
        """
        with self._cm.get_connection() as conn:
            if params:
                cursor = conn.execute(sql, params)
            else:
                cursor = conn.execute(sql)
            conn.commit()
            return cursor

    def executescript(self, sql: str) -> None:
        """
        执行多条 SQL 语句（自动 commit）

        适用于 DDL 操作（如迁移）。

        Args:
            sql: SQL 脚本（多条语句）
        """
        with self._cm.get_connection() as conn:
            conn.executescript(sql)
            conn.commit()

    def query_one(self, sql: str, params: tuple = None) -> Optional[tuple]:
        """
        查询单行

        Args:
            sql: SQL 语句
            params: 参数元组

        Returns:
            单行结果或 None
        """
        with self._cm.get_connection() as conn:
            if params:
                cursor = conn.execute(sql, params)
            else:
                cursor = conn.execute(sql)
            return cursor.fetchone()

    def query_all(self, sql: str, params: tuple = None) -> list:
        """
        查询所有行

        Args:
            sql: SQL 语句
            params: 参数元组

        Returns:
            行列表
        """
        with self._cm.get_connection() as conn:
            if params:
                cursor = conn.execute(sql, params)
            else:
                cursor = conn.execute(sql)
            return cursor.fetchall()

    def __repr__(self) -> str:
        return f"Session(cm={self._cm!r}, tm={self._tm!r})"
