"""
TransactionManager - 事务管理器

核心功能:
- ACID 事务支持
- 嵌套事务 (SAVEPOINT)
- 自动提交/回滚
- 事务隔离
- 装饰器支持
- 线程安全

设计原则:
- 单一职责：仅负责事务生命周期管理
- 依赖注入：通过构造函数接收 ConnectionManager
- 异常安全：确保事务正确回滚
"""

import logging
import functools
import threading
from typing import Callable, TypeVar, Generator, Optional
from contextlib import contextmanager

from .connection_manager import ConnectionManager

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TransactionError(Exception):
    """事务错误"""
    pass


class TransactionManager:
    """
    事务管理器
    
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
        - 线程安全：使用锁保护状态
    """
    
    def __init__(self, connection_manager: ConnectionManager):
        """
        初始化事务管理器
        
        Args:
            connection_manager: 连接管理器实例
        """
        self.conn_mgr = connection_manager
        self._lock = threading.Lock()
        self._transaction_depth = 0
        self._current_conn: Optional[object] = None
    
    def transaction(self):
        """
        事务上下文管理器
        
        - 根事务：获取新连接，BEGIN IMMEDIATE
        - 嵌套事务：复用连接，SAVEPOINT
        
        Yields:
            sqlite3.Connection: 数据库连接
        
        Raises:
            TransactionError: 事务错误
        """
        conn = None
        is_root = False
        
        with self._lock:
            is_root = (self._transaction_depth == 0)
            
            if is_root:
                # 根事务：获取新连接
                conn = self.conn_mgr._acquire()
                self._current_conn = conn
            else:
                # 嵌套事务：复用当前连接
                conn = self._current_conn
            
            self._transaction_depth += 1
        
        try:
            if is_root:
                # 根事务：开始新事务
                conn.execute("BEGIN IMMEDIATE")
            else:
                # 嵌套事务：创建保存点
                savepoint_name = f"sp_{self._transaction_depth - 1}"
                conn.execute(f"SAVEPOINT {savepoint_name}")
            
            try:
                yield conn
                
                # 成功：提交或释放保存点
                if is_root:
                    conn.commit()
                    logger.debug("Transaction committed")
                else:
                    savepoint_name = f"sp_{self._transaction_depth - 1}"
                    conn.execute(f"RELEASE SAVEPOINT {savepoint_name}")
                    logger.debug(f"Savepoint released: {savepoint_name}")
                    
            except Exception as e:
                # 失败：回滚
                if is_root:
                    conn.rollback()
                    logger.error(f"Transaction rolled back: {e}")
                else:
                    savepoint_name = f"sp_{self._transaction_depth - 1}"
                    conn.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name}")
                    logger.warning(f"Rolled back to savepoint: {savepoint_name}")
                raise
                
        finally:
            with self._lock:
                self._transaction_depth -= 1
                
                if is_root:
                    self._current_conn = None
                    self.conn_mgr._release(conn)
    
    transaction = contextmanager(transaction)
    
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
        获取当前事务深度
        
        Returns:
            int: 事务深度（0表示无事务）
        """
        with self._lock:
            return self._transaction_depth
    
    def is_in_transaction(self) -> bool:
        """
        检查是否在事务中
        
        Returns:
            bool: 是否在事务中
        """
        with self._lock:
            return self._transaction_depth > 0
    
    @contextmanager
    def read_only(self) -> Generator[object, None, None]:
        """
        只读事务上下文管理器
        
        使用 BEGIN 代替 BEGIN IMMEDIATE，允许多个读取
        
        Yields:
            sqlite3.Connection: 数据库连接
        """
        conn = self.conn_mgr._acquire()
        
        try:
            conn.execute("BEGIN")
            with self._lock:
                self._transaction_depth += 1
            
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Read-only transaction rolled back: {e}")
                raise
                
        finally:
            with self._lock:
                self._transaction_depth -= 1
            self.conn_mgr._release(conn)
    
    def __repr__(self) -> str:
        with self._lock:
            return (
                f"TransactionManager(depth={self._transaction_depth}, "
                f"in_transaction={self._transaction_depth > 0})"
            )
