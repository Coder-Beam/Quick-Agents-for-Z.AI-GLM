"""
QueryBuilder - 链式查询构建器

核心功能:
- 链式 API 构建查询
- 参数化查询（防 SQL 注入）
- 支持 filter/exclude/order_by/limit/offset
- 支持 __gt, __gte, __lt, __lte, __contains, __in, __startswith 等操作符
- 支持 count()/exists()/all()/first()

设计原则:
- 不可变: 每次链式调用返回新实例
- 延迟执行: 构建完成后调用终结方法时才执行查询
- 安全: 所有值通过参数化传递
"""

import logging
from typing import List, Optional, Any, Tuple, TypeVar, Generic
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar("T")


class FilterOp(Enum):
    """过滤操作符"""

    EQ = "="  # 等于
    NE = "!="  # 不等于
    GT = ">"  # 大于
    GTE = ">="  # 大于等于
    LT = "<"  # 小于
    LTE = "<="  # 小于等于
    LIKE = "LIKE"  # 模糊匹配
    NOT_LIKE = "NOT LIKE"  # 不包含
    IN = "IN"  # 包含于
    NOT_IN = "NOT IN"  # 不包含于
    IS_NULL = "IS NULL"  # 为空
    IS_NOT_NULL = "IS NOT NULL"  # 不为空


# 操作符映射: 字段名后缀 -> FilterOp
_SUFFIX_TO_OP = {
    "": FilterOp.EQ,
    "__gt": FilterOp.GT,
    "__gte": FilterOp.GTE,
    "__lt": FilterOp.LT,
    "__lte": FilterOp.LTE,
    "__contains": FilterOp.LIKE,
    "__startswith": FilterOp.LIKE,
    "__in": FilterOp.IN,
    "__ne": FilterOp.NE,
}


class FilterCondition:
    """过滤条件"""

    __slots__ = ("field", "op", "value")

    def __init__(self, field: str, op: FilterOp, value: Any = None):
        self.field = field
        self.op = op
        self.value = value

    def __repr__(self) -> str:
        return f"FilterCondition({self.field} {self.op.value} {self.value!r})"


class QueryBuilder(Generic[T]):
    """
    链式查询构建器
    
    使用方式:
        # 简单查询
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
        exists = repo.query().filter(key='project.name').exists()
        
        # 选择字段
        results = repo.query().filter(type='factual').only(['key', 'value']).all()
    
    设计:
        - 不可变: 每次链式调用返回新的 QueryBuilder 实例
        - 延迟执行: 构建完成后调用终结方法 (all/count/exists/first) 才执行
    """

    def __init__(self, table_name: str, row_mapper=None, conn_provider=None):
        """
        初始化查询构建器

        Args:
            table_name: 表名
            row_mapper: 行转换函数 (row) -> entity
            conn_provider: 连接提供者，可调用对象返回 context manager
        """
        self._table_name = table_name
        self._row_mapper = row_mapper
        self._conn_provider = conn_provider

        # 查询状态
        self._filters: List[FilterCondition] = []
        self._excludes: List[FilterCondition] = []
        self._order_clauses: List[str] = []
        self._limit_value: Optional[int] = None
        self._offset_value: Optional[int] = None
        self._only_fields: Optional[List[str]] = None

    def _clone(self) -> "QueryBuilder[T]":
        """创建当前构建器的副本"""
        clone = QueryBuilder(self._table_name, self._row_mapper, self._conn_provider)
        clone._filters = list(self._filters)
        clone._excludes = list(self._excludes)
        clone._order_clauses = list(self._order_clauses)
        clone._limit_value = self._limit_value
        clone._offset_value = self._offset_value
        clone._only_fields = list(self._only_fields) if self._only_fields else None
        return clone

    # ==================== 链式方法 ====================

    def filter(self, **kwargs) -> "QueryBuilder[T]":
        """
        添加过滤条件（AND）

        支持 Django 风格的查询操作符:
            field=value          -> field = value
            field__gt=value      -> field > value
            field__gte=value     -> field >= value
            field__lt=value      -> field < value
            field__lte=value     -> field <= value
            field__contains=val  -> field LIKE '%val%'
            field__startswith=val -> field LIKE 'val%'
            field__in=[...]      -> field IN (...)
            field__ne=value      -> field != value

        Args:
            **kwargs: 过滤条件

        Returns:
            QueryBuilder: 新的查询构建器实例
        """
        clone = self._clone()
        for key, value in kwargs.items():
            condition = self._parse_filter(key, value)
            clone._filters.append(condition)
        return clone

    def exclude(self, **kwargs) -> "QueryBuilder[T]":
        """
        添加排除条件（AND NOT）

        Args:
            **kwargs: 排除条件（同 filter 语法）

        Returns:
            QueryBuilder: 新的查询构建器实例
        """
        clone = self._clone()
        for key, value in kwargs.items():
            condition = self._parse_filter(key, value)
            clone._excludes.append(condition)
        return clone

    def order_by(self, *fields) -> "QueryBuilder[T]":
        """
        排序

        Args:
            *fields: 排序字段，前缀 '-' 表示降序
                     例: order_by('-created_at', 'name')

        Returns:
            QueryBuilder: 新的查询构建器实例
        """
        clone = self._clone()
        for field in fields:
            field = field.strip()
            if field.startswith("-"):
                clone._order_clauses.append(f"{field[1:]} DESC")
            elif field.startswith("+"):
                clone._order_clauses.append(f"{field[1:]} ASC")
            else:
                clone._order_clauses.append(f"{field} ASC")
        return clone

    def limit(self, count: int) -> "QueryBuilder[T]":
        """
        限制返回数量

        Args:
            count: 数量限制

        Returns:
            QueryBuilder: 新的查询构建器实例
        """
        clone = self._clone()
        clone._limit_value = count
        return clone

    def offset(self, count: int) -> "QueryBuilder[T]":
        """
        偏移量（分页）

        Args:
            count: 偏移量

        Returns:
            QueryBuilder: 新的查询构建器实例
        """
        clone = self._clone()
        clone._offset_value = count
        return clone

    def only(self, fields: List[str]) -> "QueryBuilder[T]":
        """
        选择特定字段

        Args:
            fields: 字段列表

        Returns:
            QueryBuilder: 新的查询构建器实例
        """
        clone = self._clone()
        clone._only_fields = list(fields)
        return clone

    # ==================== 终结方法 ====================

    def all(self) -> List[T]:
        """
        执行查询，返回所有结果

        Returns:
            List[T]: 实体列表
        """
        sql, params = self._build_select_sql()

        with self._conn_provider() as conn:
            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()

            if self._only_fields and self._row_mapper:
                return [self._row_mapper(row) for row in rows]
            elif self._row_mapper:
                return [self._row_mapper(row) for row in rows]
            else:
                return list(rows)

    def first(self) -> Optional[T]:
        """
        执行查询，返回第一条结果

        Returns:
            Optional[T]: 实体或 None
        """
        clone = self._clone()
        clone._limit_value = 1
        results = clone.all()
        return results[0] if results else None

    def count(self) -> int:
        """
        计数

        Returns:
            int: 匹配的记录数
        """
        sql, params = self._build_count_sql()

        with self._conn_provider() as conn:
            cursor = conn.execute(sql, params)
            return cursor.fetchone()[0]

    def exists(self) -> bool:
        """
        判断是否存在匹配记录

        Returns:
            bool: 是否存在
        """
        return self.count() > 0

    def delete(self) -> int:
        """
        删除匹配的记录

        Returns:
            int: 删除数量
        """
        sql, params = self._build_delete_sql()

        with self._conn_provider() as conn:
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor.rowcount

    # ==================== SQL 构建 ====================

    def _parse_filter(self, key: str, value: Any) -> FilterCondition:
        """解析过滤条件键名为字段和操作符"""
        # 检查特殊值 None
        if value is None:
            return FilterCondition(key, FilterOp.IS_NULL)

        # 查找匹配的后缀
        for suffix, op in sorted(_SUFFIX_TO_OP.items(), key=lambda x: -len(x[0])):
            if suffix and key.endswith(suffix):
                field = key[: -len(suffix)]

                if op == FilterOp.IN:
                    if not isinstance(value, (list, tuple, set)):
                        raise ValueError(
                            f"__in 操作符需要列表/元组/集合，收到: {type(value)}"
                        )
                    if len(value) == 0:
                        raise ValueError("__in 操作符的值不能为空列表")
                    return FilterCondition(field, op, list(value))

                if op == FilterOp.LIKE and "__contains" in key:
                    return FilterCondition(field, op, f"%{value}%")

                if op == FilterOp.LIKE and "__startswith" in key:
                    return FilterCondition(field, op, f"{value}%")

                return FilterCondition(field, op, value)

        # 默认精确匹配
        return FilterCondition(key, FilterOp.EQ, value)

    def _build_where_clause(self) -> Tuple[str, List[Any]]:
        """
        构建 WHERE 子句

        Returns:
            Tuple[str, List]: (SQL片段, 参数列表)
        """
        conditions = []
        params = []

        # 正向过滤条件
        for cond in self._filters:
            sql, p = self._condition_to_sql(cond)
            conditions.append(sql)
            if p is not None:
                params.extend(p)

        # 排除条件（NOT）
        for cond in self._excludes:
            sql, p = self._condition_to_sql(cond)
            conditions.append(f"NOT ({sql})")
            if p is not None:
                params.extend(p)

        if not conditions:
            return "", []

        return " WHERE " + " AND ".join(conditions), params

    def _condition_to_sql(
        self, cond: FilterCondition
    ) -> Tuple[str, Optional[List[Any]]]:
        """将单个条件转为 SQL"""
        if cond.op == FilterOp.IS_NULL:
            return f"{cond.field} IS NULL", None

        if cond.op == FilterOp.IS_NOT_NULL:
            return f"{cond.field} IS NOT NULL", None

        if cond.op == FilterOp.IN:
            placeholders = ", ".join("?" * len(cond.value))
            return f"{cond.field} IN ({placeholders})", list(cond.value)

        if cond.op == FilterOp.NOT_IN:
            placeholders = ", ".join("?" * len(cond.value))
            return f"{cond.field} NOT IN ({placeholders})", list(cond.value)

        if cond.op == FilterOp.LIKE:
            return f"{cond.field} LIKE ?", [cond.value]

        if cond.op == FilterOp.NOT_LIKE:
            return f"{cond.field} NOT LIKE ?", [cond.value]

        # 标准比较操作符
        return f"{cond.field} {cond.op.value} ?", [cond.value]

    def _build_select_sql(self) -> Tuple[str, List[Any]]:
        """构建 SELECT SQL"""
        # 字段选择
        if self._only_fields:
            fields = ", ".join(self._only_fields)
        else:
            fields = "*"

        sql = f"SELECT {fields} FROM {self._table_name}"

        # WHERE
        where_sql, params = self._build_where_clause()
        sql += where_sql

        # ORDER BY
        if self._order_clauses:
            sql += " ORDER BY " + ", ".join(self._order_clauses)

        # LIMIT / OFFSET
        if self._limit_value is not None:
            sql += " LIMIT ?"
            params.append(self._limit_value)

        if self._offset_value is not None:
            if self._limit_value is None:
                sql += " LIMIT -1"  # SQLite: 无限制
            sql += " OFFSET ?"
            params.append(self._offset_value)

        return sql, params

    def _build_count_sql(self) -> Tuple[str, List[Any]]:
        """构建 COUNT SQL"""
        sql = f"SELECT COUNT(*) FROM {self._table_name}"

        where_sql, params = self._build_where_clause()
        sql += where_sql

        return sql, params

    def _build_delete_sql(self) -> Tuple[str, List[Any]]:
        """构建 DELETE SQL"""
        sql = f"DELETE FROM {self._table_name}"

        where_sql, params = self._build_where_clause()
        sql += where_sql

        return sql, params

    def __repr__(self) -> str:
        parts = [f"QueryBuilder(table={self._table_name}"]
        if self._filters:
            parts.append(f"filters={len(self._filters)}")
        if self._excludes:
            parts.append(f"excludes={len(self._excludes)}")
        if self._order_clauses:
            parts.append(f"order={self._order_clauses}")
        if self._limit_value:
            parts.append(f"limit={self._limit_value}")
        return ", ".join(parts) + ")"
