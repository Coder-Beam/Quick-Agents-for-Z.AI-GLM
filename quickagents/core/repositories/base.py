"""
BaseRepository - Repository 基类

核心功能:
- CRUD 操作抽象
- 过滤查询
- 计数统计
- 事务支持
- 查询构建器 (QueryBuilder)
- 批量操作优化 (executemany / 批量 VALUES)

设计原则:
- 模板方法模式：定义算法骨架，子类实现具体步骤
- 依赖注入：通过构造函数接收 ConnectionManager 和 TransactionManager
- 单一职责：仅负责数据访问
"""

import logging
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any

from ..connection_manager import ConnectionManager
from ..transaction_manager import TransactionManager
from .query_builder import QueryBuilder

logger = logging.getLogger(__name__)

T = TypeVar('T')

# 批量 VALUES 子句的最大行数
# SQLite 编译 SQL 有上限，过大的 VALUES 子句会触发 SQLITE_TOOBIG
_BATCH_INSERT_SIZE = 100


class BaseRepository(ABC, Generic[T]):
    """
    Repository 基类
    
    使用方式:
        class MemoryRepository(BaseRepository[Memory]):
            @property
            def table_name(self) -> str:
                return "memory"
            
            def _row_to_entity(self, row: tuple) -> Memory:
                return Memory(...)
            
            def _entity_to_dict(self, entity: Memory) -> Dict[str, Any]:
                return {...}
    
    特性:
        - 泛型支持：支持任意实体类型
        - CRUD 操作：get, get_all, add, update, delete
        - 过滤查询：支持条件过滤
        - 事务支持：与 TransactionManager 集成
        - 查询构建器：链式 API，支持复杂条件
        - 批量优化：executemany / 批量 VALUES 提升写入性能
    """
    
    def __init__(
        self,
        connection_manager: ConnectionManager,
        transaction_manager: TransactionManager
    ):
        """
        初始化 Repository
        
        Args:
            connection_manager: 连接管理器
            transaction_manager: 事务管理器
        """
        self.conn_mgr = connection_manager
        self.tx_mgr = transaction_manager
    
    @property
    @abstractmethod
    def table_name(self) -> str:
        """
        表名
        
        Returns:
            str: 数据库表名
        """
        pass
    
    @abstractmethod
    def _row_to_entity(self, row: tuple) -> T:
        """
        行转实体
        
        Args:
            row: 数据库行（元组）
        
        Returns:
            T: 实体对象
        """
        pass
    
    @abstractmethod
    def _entity_to_dict(self, entity: T) -> Dict[str, Any]:
        """
        实体转字典
        
        Args:
            entity: 实体对象
        
        Returns:
            Dict[str, Any]: 字典表示
        """
        pass
    
    # ==================== 查询构建器 ====================
    
    def query(self) -> QueryBuilder[T]:
        """
        创建链式查询构建器
        
        Returns:
            QueryBuilder[T]: 查询构建器实例
        
        示例:
            # 简单过滤
            results = repo.query().filter(type='factual').order_by('-created_at').limit(10).all()
            
            # 复杂条件
            results = repo.query() \\
                .filter(importance_score__gte=0.8) \\
                .filter(category__in=['pitfalls', 'best-practices']) \\
                .exclude(key__contains='temp') \\
                .order_by('-updated_at') \\
                .limit(20) \\
                .all()
            
            # 聚合
            count = repo.query().filter(type='factual').count()
        """
        return QueryBuilder(
            table_name=self.table_name,
            row_mapper=self._row_to_entity,
            conn_provider=self.conn_mgr.get_connection
        )
    
    # ==================== 查询操作 ====================
    
    def get(self, id: str) -> Optional[T]:
        """
        根据 ID 获取实体
        
        Args:
            id: 实体 ID
        
        Returns:
            Optional[T]: 实体对象，不存在则返回 None
        """
        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(
                f"SELECT * FROM {self.table_name} WHERE id = ?",
                (id,)
            )
            row = cursor.fetchone()
            return self._row_to_entity(row) if row else None
    
    def get_all(
        self,
        filters: Dict[str, Any] = None,
        order_by: str = None,
        limit: int = None,
        offset: int = None
    ) -> List[T]:
        """
        获取所有实体（支持过滤）
        
        Args:
            filters: 过滤条件 {"field": value}
            order_by: 排序字段（如 "created_at DESC"）
            limit: 返回数量限制
            offset: 偏移量（分页）
        
        Returns:
            List[T]: 实体列表
        """
        sql = f"SELECT * FROM {self.table_name}"
        params = []
        
        if filters:
            conditions = []
            for key, value in filters.items():
                if value is None:
                    conditions.append(f"{key} IS NULL")
                else:
                    conditions.append(f"{key} = ?")
                    params.append(value)
            sql += " WHERE " + " AND ".join(conditions)
        
        if order_by:
            sql += f" ORDER BY {order_by}"
        
        if limit:
            sql += f" LIMIT {limit}"
        
        if offset:
            sql += f" OFFSET {offset}"
        
        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(sql, params)
            return [self._row_to_entity(row) for row in cursor.fetchall()]
    
    def get_by_ids(self, ids: List[str]) -> List[T]:
        """
        根据 ID 列表获取实体
        
        Args:
            ids: ID 列表
        
        Returns:
            List[T]: 实体列表
        """
        if not ids:
            return []
        
        placeholders = ", ".join("?" * len(ids))
        sql = f"SELECT * FROM {self.table_name} WHERE id IN ({placeholders})"
        
        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(sql, ids)
            return [self._row_to_entity(row) for row in cursor.fetchall()]
    
    def exists(self, id: str) -> bool:
        """
        检查实体是否存在
        
        Args:
            id: 实体 ID
        
        Returns:
            bool: 是否存在
        """
        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(
                f"SELECT 1 FROM {self.table_name} WHERE id = ?",
                (id,)
            )
            return cursor.fetchone() is not None
    
    def count(self, filters: Dict[str, Any] = None) -> int:
        """
        计数
        
        Args:
            filters: 过滤条件
        
        Returns:
            int: 数量
        """
        sql = f"SELECT COUNT(*) FROM {self.table_name}"
        params = []
        
        if filters:
            conditions = []
            for key, value in filters.items():
                if value is None:
                    conditions.append(f"{key} IS NULL")
                else:
                    conditions.append(f"{key} = ?")
                    params.append(value)
            sql += " WHERE " + " AND ".join(conditions)
        
        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(sql, params)
            return cursor.fetchone()[0]
    
    # ==================== 写入操作 ====================
    
    def add(self, entity: T) -> T:
        """
        添加实体
        
        Args:
            entity: 实体对象
        
        Returns:
            T: 添加后的实体
        """
        data = self._entity_to_dict(entity)
        fields = ", ".join(data.keys())
        placeholders = ", ".join("?" * len(data))
        
        with self.conn_mgr.get_connection() as conn:
            conn.execute(
                f"INSERT INTO {self.table_name} ({fields}) VALUES ({placeholders})",
                tuple(data.values())
            )
            conn.commit()
        
        return entity
    
    def add_batch(self, entities: List[T]) -> int:
        """
        批量添加实体（使用批量 VALUES 优化）
        
        相比逐条 INSERT，使用批量 VALUES 子句可提升写入性能 5-10x。
        当数据量超过 _BATCH_INSERT_SIZE 时自动分批执行。
        
        Args:
            entities: 实体列表
        
        Returns:
            int: 添加数量
        """
        if not entities:
            return 0
        
        data_list = [self._entity_to_dict(e) for e in entities]
        fields = list(data_list[0].keys())
        field_str = ", ".join(fields)
        single_placeholder = "(" + ", ".join("?" * len(fields)) + ")"
        
        # 分批执行
        for i in range(0, len(data_list), _BATCH_INSERT_SIZE):
            batch = data_list[i:i + _BATCH_INSERT_SIZE]
            
            # 构建批量 VALUES: INSERT INTO t (a,b,c) VALUES (?,?,?), (?,?,?), ...
            values_clause = ", ".join([single_placeholder for _ in batch])
            sql = f"INSERT INTO {self.table_name} ({field_str}) VALUES {values_clause}"
            
            # 展平参数
            flat_params = []
            for data in batch:
                flat_params.extend(data[f] for f in fields)
            
            with self.conn_mgr.get_connection() as conn:
                conn.execute(sql, flat_params)
                conn.commit()
        
        return len(entities)
    
    def update(self, entity: T) -> T:
        """
        更新实体
        
        Args:
            entity: 实体对象
        
        Returns:
            T: 更新后的实体
        """
        data = self._entity_to_dict(entity)
        
        # 移除 ID（不更新主键）
        if 'id' in data:
            entity_id = data.pop('id')
        else:
            entity_id = getattr(entity, 'id', None)
        
        set_clause = ", ".join(f"{k} = ?" for k in data.keys())
        
        with self.conn_mgr.get_connection() as conn:
            conn.execute(
                f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?",
                tuple(data.values()) + (entity_id,)
            )
            conn.commit()
        
        return entity
    
    def update_batch(self, entities: List[T]) -> int:
        """
        批量更新实体
        
        Args:
            entities: 实体列表
        
        Returns:
            int: 更新数量
        """
        if not entities:
            return 0
        
        with self.tx_mgr.transaction() as conn:
            for entity in entities:
                data = self._entity_to_dict(entity)
                entity_id = data.pop('id')
                set_clause = ", ".join(f"{k} = ?" for k in data.keys())
                conn.execute(
                    f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?",
                    tuple(data.values()) + (entity_id,)
                )
        
        return len(entities)
    
    def delete(self, id: str) -> bool:
        """
        删除实体
        
        Args:
            id: 实体 ID
        
        Returns:
            bool: 是否删除成功
        """
        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(
                f"DELETE FROM {self.table_name} WHERE id = ?",
                (id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_batch(self, ids: List[str]) -> int:
        """
        批量删除实体
        
        Args:
            ids: ID 列表
        
        Returns:
            int: 删除数量
        """
        if not ids:
            return 0
        
        placeholders = ", ".join("?" * len(ids))
        
        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(
                f"DELETE FROM {self.table_name} WHERE id IN ({placeholders})",
                ids
            )
            conn.commit()
            return cursor.rowcount
    
    def delete_all(self, filters: Dict[str, Any] = None) -> int:
        """
        删除所有匹配的实体
        
        Args:
            filters: 过滤条件
        
        Returns:
            int: 删除数量
        """
        sql = f"DELETE FROM {self.table_name}"
        params = []
        
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            sql += " WHERE " + " AND ".join(conditions)
        
        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor.rowcount
    
    # ==================== 工具方法 ====================
    
    def _execute_in_transaction(self, func, *args, **kwargs):
        """
        在事务中执行函数
        
        Args:
            func: 要执行的函数
            *args, **kwargs: 函数参数
        
        Returns:
            函数返回值
        """
        with self.tx_mgr.transaction() as conn:
            return func(conn, *args, **kwargs)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(table={self.table_name})"
