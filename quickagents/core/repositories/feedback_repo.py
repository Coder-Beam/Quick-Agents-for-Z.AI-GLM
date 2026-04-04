"""
FeedbackRepository - 反馈仓储

核心功能:
- CRUD 操作
- 按类型/项目查询
- 统计分析
"""

import time
import json
import logging
from typing import List, Dict, Any

from .base import BaseRepository
from .models import Feedback, FeedbackType

logger = logging.getLogger(__name__)


class FeedbackRepository(BaseRepository[Feedback]):
    """
    反馈仓储

    使用方式:
        repo = FeedbackRepository(conn_mgr, tx_mgr)

        # 添加反馈
        feedback = Feedback(
            id="FB001",
            feedback_type=FeedbackType.BUG,
            title="发现一个bug",
            description="详细描述"
        )
        repo.add(feedback)

        # 查询反馈
        bugs = repo.get_by_type(FeedbackType.BUG)
    """

    @property
    def table_name(self) -> str:
        return "feedback"

    # ==================== 实体转换 ====================

    def _row_to_entity(self, row: tuple) -> Feedback:
        """行转实体"""
        return Feedback(
            id=row[0],
            feedback_type=FeedbackType(row[1]),
            title=row[2],
            description=row[3],
            project_name=row[4],
            metadata=json.loads(row[5]) if len(row) > 5 and row[5] else {},
            created_at=row[6] if len(row) > 6 else time.time(),
        )

    def _entity_to_dict(self, entity: Feedback) -> Dict[str, Any]:
        """实体转字典"""
        return {
            "id": entity.id,
            "feedback_type": entity.feedback_type.value,
            "title": entity.title,
            "description": entity.description,
            "project_name": entity.project_name,
            "metadata": json.dumps(entity.metadata, ensure_ascii=False),
            "created_at": entity.created_at,
        }

    # ==================== 专用查询方法 ====================

    def get_by_type(
        self, feedback_type: FeedbackType, limit: int = 100
    ) -> List[Feedback]:
        """
        获取指定类型的反馈

        Args:
            feedback_type: 反馈类型
            limit: 返回数量限制

        Returns:
            List[Feedback]: 反馈列表
        """
        return self.get_all(
            filters={"feedback_type": feedback_type.value},
            order_by="created_at DESC",
            limit=limit,
        )

    def get_by_project(
        self, project_name: str, feedback_type: FeedbackType = None, limit: int = 100
    ) -> List[Feedback]:
        """
        获取指定项目的反馈

        Args:
            project_name: 项目名
            feedback_type: 反馈类型（可选）
            limit: 返回数量限制

        Returns:
            List[Feedback]: 反馈列表
        """
        filters = {"project_name": project_name}
        if feedback_type:
            filters["feedback_type"] = feedback_type.value

        return self.get_all(filters=filters, order_by="created_at DESC", limit=limit)

    def get_recent(self, limit: int = 10) -> List[Feedback]:
        """
        获取最近的反馈

        Args:
            limit: 返回数量限制

        Returns:
            List[Feedback]: 反馈列表
        """
        return self.get_all(order_by="created_at DESC", limit=limit)

    def search(
        self, query: str, feedback_type: FeedbackType = None, limit: int = 20
    ) -> List[Feedback]:
        """
        搜索反馈

        Args:
            query: 搜索关键词
            feedback_type: 反馈类型（可选）
            limit: 返回数量限制

        Returns:
            List[Feedback]: 反馈列表
        """
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE title LIKE ? OR description LIKE ?
        """
        params = [f"%{query}%", f"%{query}%"]

        if feedback_type:
            sql += " AND feedback_type = ?"
            params.append(feedback_type.value)

        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(sql, params)
            return [self._row_to_entity(row) for row in cursor.fetchall()]

    # ==================== 写入方法 ====================

    def add(self, feedback: Feedback) -> Feedback:
        """添加反馈"""
        feedback.created_at = time.time()

        data = self._entity_to_dict(feedback)

        with self.conn_mgr.get_connection() as conn:
            conn.execute(
                f"""
                INSERT INTO {self.table_name} (
                    id, feedback_type, title, description,
                    project_name, metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"],
                    data["feedback_type"],
                    data["title"],
                    data["description"],
                    data["project_name"],
                    data["metadata"],
                    data["created_at"],
                ),
            )
            conn.commit()

        return feedback

    def add_feedback(
        self,
        feedback_type: FeedbackType,
        title: str,
        description: str = None,
        project_name: str = None,
        metadata: Dict[str, Any] = None,
    ) -> Feedback:
        """
        添加反馈（便捷方法）

        Args:
            feedback_type: 反馈类型
            title: 标题
            description: 描述
            project_name: 项目名
            metadata: 元数据

        Returns:
            Feedback: 反馈实体
        """
        import uuid

        feedback = Feedback(
            id=str(uuid.uuid4()),
            feedback_type=feedback_type,
            title=title,
            description=description,
            project_name=project_name,
            metadata=metadata or {},
        )
        return self.add(feedback)

    # ==================== 统计方法 ====================

    def count_by_type(self) -> Dict[str, int]:
        """
        按类型统计反馈数量

        Returns:
            Dict[str, int]: 类型 -> 数量
        """
        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(
                f"""
                SELECT feedback_type, COUNT(*) as count
                FROM {self.table_name}
                GROUP BY feedback_type
                """
            )
            return {row[0]: row[1] for row in cursor.fetchall()}

    def count_by_project(self) -> Dict[str, int]:
        """
        按项目统计反馈数量

        Returns:
            Dict[str, int]: 项目 -> 数量
        """
        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(
                f"""
                SELECT project_name, COUNT(*) as count
                FROM {self.table_name}
                WHERE project_name IS NOT NULL
                GROUP BY project_name
                """
            )
            return {row[0]: row[1] for row in cursor.fetchall()}

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取反馈统计

        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "total": self.count(),
            "by_type": self.count_by_type(),
            "by_project": self.count_by_project(),
        }
