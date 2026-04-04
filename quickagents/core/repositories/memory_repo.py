"""
MemoryRepository - 记忆仓储

核心功能:
- CRUD 操作
- 按 key/type/category 查询
- 搜索（文本匹配）
- 带评分的检索（RIF 公式）
- 访问统计
"""

import time
import json
import logging
from typing import List, Optional, Dict, Any

from .base import BaseRepository
from .models import Memory, MemoryType, SearchResult, RetrievalConfig

logger = logging.getLogger(__name__)


class MemoryRepository(BaseRepository[Memory]):
    """
    记忆仓储

    使用方式:
        repo = MemoryRepository(conn_mgr, tx_mgr)

        # 添加记忆
        memory = Memory(id="1", memory_type=MemoryType.FACTUAL, key="project.name", value="MyProject")
        repo.add(memory)

        # 查询记忆
        memory = repo.get_by_key("project.name")

        # 搜索记忆
        results = repo.search("认证")

        # 带评分的检索
        results = repo.search_with_scoring("认证", RetrievalConfig())
    """

    @property
    def table_name(self) -> str:
        return "memory"

    # ==================== 实体转换 ====================

    def _row_to_entity(self, row: tuple) -> Memory:
        """行转实体"""
        return Memory(
            id=row[0],
            memory_type=MemoryType(row[1]),
            category=row[2],
            key=row[3],
            value=row[4],
            importance_score=row[5],
            access_count=row[6],
            last_accessed_at=row[7],
            created_at=row[8],
            updated_at=row[9],
            metadata=json.loads(row[10]) if row[10] else {},
            content_hash=row[11] if len(row) > 11 else None,
        )

    def _entity_to_dict(self, entity: Memory) -> Dict[str, Any]:
        """实体转字典"""
        return {
            "id": entity.id,
            "memory_type": entity.memory_type.value,
            "category": entity.category,
            "key": entity.key,
            "value": entity.value,
            "importance_score": entity.importance_score,
            "access_count": entity.access_count,
            "last_accessed_at": entity.last_accessed_at,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
            "metadata": json.dumps(entity.metadata, ensure_ascii=False),
            "content_hash": entity.content_hash,
        }

    # ==================== 专用查询方法 ====================

    def get_by_key(
        self, key: str, memory_type: Optional[MemoryType] = None, category: Optional[str] = None
    ) -> Optional[Memory]:
        """
        根据 key 获取记忆

        Args:
            key: 键名
            memory_type: 记忆类型（可选）
            category: 分类（可选）

        Returns:
            Memory: 记忆实体，不存在则返回 None
        """
        filters = {"key": key}
        if memory_type:
            filters["memory_type"] = memory_type.value
        if category:
            filters["category"] = category

        results = self.get_all(filters=filters, limit=1)
        return results[0] if results else None

    def get_by_type(self, memory_type: MemoryType, limit: int = 100) -> List[Memory]:
        """
        获取指定类型的所有记忆

        Args:
            memory_type: 记忆类型
            limit: 返回数量限制

        Returns:
            List[Memory]: 记忆列表
        """
        return self.get_all(
            filters={"memory_type": memory_type.value},
            order_by="updated_at DESC",
            limit=limit,
        )

    def get_by_category(
        self, category: str, memory_type: Optional[MemoryType] = None, limit: int = 100
    ) -> List[Memory]:
        """
        获取指定分类的所有记忆

        Args:
            category: 分类名
            memory_type: 记忆类型（可选）
            limit: 返回数量限制

        Returns:
            List[Memory]: 记忆列表
        """
        filters = {"category": category}
        if memory_type:
            filters["memory_type"] = memory_type.value

        return self.get_all(filters=filters, order_by="updated_at DESC", limit=limit)

    def get_important(self, min_score: float = 0.7, limit: int = 10) -> List[Memory]:
        """
        获取高重要性记忆

        Args:
            min_score: 最小重要性分数
            limit: 返回数量限制

        Returns:
            List[Memory]: 记忆列表
        """
        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(
                f"""
                SELECT * FROM {self.table_name}
                WHERE importance_score >= ?
                ORDER BY importance_score DESC
                LIMIT ?
                """,
                (min_score, limit),
            )
            return [self._row_to_entity(row) for row in cursor.fetchall()]

    def get_recent(
        self, limit: int = 10, memory_type: Optional[MemoryType] = None
    ) -> List[Memory]:
        """
        获取最近访问的记忆

        Args:
            limit: 返回数量限制
            memory_type: 记忆类型（可选）

        Returns:
            List[Memory]: 记忆列表
        """
        if memory_type:
            with self.conn_mgr.get_connection() as conn:
                cursor = conn.execute(
                    f"""
                    SELECT * FROM {self.table_name}
                    WHERE memory_type = ?
                    ORDER BY last_accessed_at DESC NULLS LAST
                    LIMIT ?
                    """,
                    (memory_type.value, limit),
                )
                return [self._row_to_entity(row) for row in cursor.fetchall()]
        else:
            with self.conn_mgr.get_connection() as conn:
                cursor = conn.execute(
                    f"""
                    SELECT * FROM {self.table_name}
                    ORDER BY last_accessed_at DESC NULLS LAST
                    LIMIT ?
                    """,
                    (limit,),
                )
                return [self._row_to_entity(row) for row in cursor.fetchall()]

    # ==================== 搜索方法 ====================

    def search(
        self, query: str, memory_type: Optional[MemoryType] = None, limit: int = 10
    ) -> List[Memory]:
        """
        搜索记忆（简单文本匹配）

        Args:
            query: 搜索关键词
            memory_type: 记忆类型（可选）
            limit: 返回数量限制

        Returns:
            List[Memory]: 记忆列表
        """
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE value LIKE ? OR key LIKE ?
        """
        params = [f"%{query}%", f"%{query}%"]

        if memory_type:
            sql += " AND memory_type = ?"
            params.append(memory_type.value)

        sql += " ORDER BY importance_score DESC, updated_at DESC LIMIT ?"
        params.append(limit)  # type: ignore[arg-type]

        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(sql, params)
            return [self._row_to_entity(row) for row in cursor.fetchall()]

    def search_with_scoring(
        self, query: str, config: Optional[RetrievalConfig] = None, memory_type: Optional[MemoryType] = None
    ) -> List[SearchResult]:
        """
        带评分的检索

        使用 RIF 公式: S = α·R + β·γ + δ·I

        Args:
            query: 搜索关键词
            config: 检索配置
            memory_type: 记忆类型（可选）

        Returns:
            List[SearchResult]: 检索结果列表
        """
        config = config or RetrievalConfig()

        # 获取候选记忆
        memories = self.search(
            query=query,
            memory_type=memory_type,
            limit=config.max_results * 3,  # 获取更多候选
        )

        results = []
        current_time = time.time()

        for memory in memories:
            # 计算相关性分数（简单文本匹配）
            relevance = self._calculate_relevance(query, memory)

            # 计算时序分数
            time_diff = current_time - memory.created_at
            recency = config.decay_rate ** (time_diff / 86400)  # 按天衰减

            # 重要性分数
            importance = memory.importance_score

            # 综合分数
            final_score = SearchResult.calculate_final_score(
                relevance=relevance,
                recency=recency,
                importance=importance,
                weights={
                    "relevance": config.relevance_weight,
                    "recency": config.recency_weight,
                    "importance": config.importance_weight,
                },
            )

            if final_score >= config.min_score:
                results.append(
                    SearchResult(
                        memory=memory,
                        relevance_score=relevance,
                        recency_score=recency,
                        importance_score=importance,
                        final_score=final_score,
                    )
                )

        # 按综合分数排序
        results.sort(key=lambda r: r.final_score, reverse=True)

        return results[: config.max_results]

    def _calculate_relevance(self, query: str, memory: Memory) -> float:
        """
        计算相关性分数

        Args:
            query: 搜索词
            memory: 记忆实体

        Returns:
            float: 相关性分数 (0.0-1.0)
        """
        query_lower = query.lower()
        value_lower = memory.value.lower()
        key_lower = memory.key.lower()

        # 完全匹配
        if query_lower == value_lower or query_lower == key_lower:
            return 1.0

        # 包含匹配
        if query_lower in value_lower or query_lower in key_lower:
            # 根据匹配位置计算分数
            pos = value_lower.find(query_lower)
            if pos >= 0:
                return 0.8 - (pos / max(len(value_lower), 1)) * 0.3
            return 0.6

        # 单词匹配
        query_words = set(query_lower.split())
        value_words = set(value_lower.split())
        common = query_words & value_words
        if common:
            return len(common) / max(len(query_words), 1) * 0.5

        return 0.1

    # ==================== 写入方法 ====================

    def add(self, memory: Memory) -> Memory:
        """
        添加记忆

        Args:
            memory: 记忆实体

        Returns:
            Memory: 添加后的记忆
        """
        # 计算哈希
        memory.update_hash()
        memory.created_at = time.time()
        memory.updated_at = time.time()

        data = self._entity_to_dict(memory)

        with self.conn_mgr.get_connection() as conn:
            conn.execute(
                f"""
                INSERT INTO {self.table_name} (
                    id, memory_type, category, key, value,
                    importance_score, access_count, last_accessed_at,
                    created_at, updated_at, metadata, content_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"],
                    data["memory_type"],
                    data["category"],
                    data["key"],
                    data["value"],
                    data["importance_score"],
                    data["access_count"],
                    data["last_accessed_at"],
                    data["created_at"],
                    data["updated_at"],
                    data["metadata"],
                    data["content_hash"],
                ),
            )
            conn.commit()

        return memory

    def update(self, memory: Memory) -> Memory:
        """
        更新记忆

        Args:
            memory: 记忆实体

        Returns:
            Memory: 更新后的记忆
        """
        memory.updated_at = time.time()
        memory.update_hash()

        data = self._entity_to_dict(memory)

        with self.conn_mgr.get_connection() as conn:
            conn.execute(
                f"""
                UPDATE {self.table_name} SET
                    memory_type = ?, category = ?, key = ?, value = ?,
                    importance_score = ?, access_count = ?, last_accessed_at = ?,
                    updated_at = ?, metadata = ?, content_hash = ?
                WHERE id = ?
                """,
                (
                    data["memory_type"],
                    data["category"],
                    data["key"],
                    data["value"],
                    data["importance_score"],
                    data["access_count"],
                    data["last_accessed_at"],
                    data["updated_at"],
                    data["metadata"],
                    data["content_hash"],
                    data["id"],
                ),
            )
            conn.commit()

        return memory

    def upsert(
        self,
        key: str,
        value: str,
        memory_type: MemoryType = MemoryType.FACTUAL,
        category: Optional[str] = None,
        importance_score: Optional[float] = None,
    ) -> Memory:
        """
        插入或更新记忆

        Args:
            key: 键名
            value: 值
            memory_type: 记忆类型
            category: 分类
            importance_score: 重要性分数

        Returns:
            Memory: 记忆实体
        """
        existing = self.get_by_key(key, memory_type, category)

        if existing:
            # 更新
            existing.value = value
            existing.updated_at = time.time()
            if importance_score is not None:
                existing.importance_score = importance_score
            return self.update(existing)
        else:
            # 创建
            import uuid

            memory = Memory(
                id=str(uuid.uuid4()),
                memory_type=memory_type,
                key=key,
                value=value,
                category=category,
                importance_score=importance_score or 0.5,
            )
            return self.add(memory)

    def touch(self, id: str) -> None:
        """
        更新访问时间和计数

        Args:
            id: 记忆 ID
        """
        current_time = time.time()

        with self.conn_mgr.get_connection() as conn:
            conn.execute(
                f"""
                UPDATE {self.table_name} SET
                    access_count = access_count + 1,
                    last_accessed_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (current_time, current_time, id),
            )
            conn.commit()

    def set_importance(self, id: str, score: float) -> bool:
        """
        设置重要性分数

        Args:
            id: 记忆 ID
            score: 重要性分数 (0.0-1.0)

        Returns:
            bool: 是否成功
        """
        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(
                f"""
                UPDATE {self.table_name} SET
                    importance_score = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (score, time.time(), id),
            )
            conn.commit()
            return cursor.rowcount > 0
