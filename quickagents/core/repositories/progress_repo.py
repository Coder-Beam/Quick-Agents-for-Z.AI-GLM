"""
ProgressRepository - 进度仓储

核心功能:
- CRUD 操作
- 项目进度管理
- 检查点管理
"""

import time
import logging
from typing import List, Optional, Dict, Any

from .base import BaseRepository
from .models import Progress

logger = logging.getLogger(__name__)


class ProgressRepository(BaseRepository[Progress]):
    """
    进度仓储

    使用方式:
        repo = ProgressRepository(conn_mgr, tx_mgr)

        # 初始化进度
        progress = repo.init_progress("my-project", total_tasks=10)

        # 更新进度
        repo.increment_completed("my-project")

        # 获取进度
        progress = repo.get_by_project("my-project")
    """

    @property
    def table_name(self) -> str:
        return "progress"

    # ==================== 实体转换 ====================

    def _row_to_entity(self, row: tuple) -> Progress:
        """行转实体"""
        return Progress(
            id=row[0],
            project_name=row[1],
            current_task=row[2],
            total_tasks=row[3],
            completed_tasks=row[4],
            last_checkpoint=row[5],
            created_at=row[6],
            updated_at=row[7],
        )

    def _entity_to_dict(self, entity: Progress) -> Dict[str, Any]:
        """实体转字典"""
        return {
            "id": entity.id,
            "project_name": entity.project_name,
            "current_task": entity.current_task,
            "total_tasks": entity.total_tasks,
            "completed_tasks": entity.completed_tasks,
            "last_checkpoint": entity.last_checkpoint,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
        }

    # ==================== 专用查询方法 ====================

    def get_by_project(self, project_name: str) -> Optional[Progress]:
        """
        根据项目名获取进度

        Args:
            project_name: 项目名

        Returns:
            Optional[Progress]: 进度实体
        """
        results = self.get_all(filters={"project_name": project_name}, limit=1)
        return results[0] if results else None

    def get_latest(self, limit: int = 10) -> List[Progress]:
        """
        获取最近更新的进度

        Args:
            limit: 返回数量限制

        Returns:
            List[Progress]: 进度列表
        """
        return self.get_all(order_by="updated_at DESC", limit=limit)

    # ==================== 写入方法 ====================

    def add(self, progress: Progress) -> Progress:
        """添加进度"""
        progress.created_at = time.time()
        progress.updated_at = time.time()

        data = self._entity_to_dict(progress)

        with self.conn_mgr.get_connection() as conn:
            conn.execute(
                f"""
                INSERT INTO {self.table_name} (
                    id, project_name, current_task, total_tasks,
                    completed_tasks, last_checkpoint, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"],
                    data["project_name"],
                    data["current_task"],
                    data["total_tasks"],
                    data["completed_tasks"],
                    data["last_checkpoint"],
                    data["created_at"],
                    data["updated_at"],
                ),
            )
            conn.commit()

        return progress

    def init_progress(self, project_name: str, total_tasks: int = 0) -> Progress:
        """
        初始化进度

        Args:
            project_name: 项目名
            total_tasks: 总任务数

        Returns:
            Progress: 进度实体
        """
        import uuid

        # 检查是否已存在
        existing = self.get_by_project(project_name)
        if existing:
            return existing

        progress = Progress(
            id=str(uuid.uuid4()), project_name=project_name, total_tasks=total_tasks
        )
        return self.add(progress)

    def update_current_task(
        self, project_name: str, current_task: str
    ) -> Optional[Progress]:
        """
        更新当前任务

        Args:
            project_name: 项目名
            current_task: 当前任务 ID

        Returns:
            Optional[Progress]: 更新后的进度
        """
        progress = self.get_by_project(project_name)
        if not progress:
            return None

        progress.current_task = current_task
        progress.updated_at = time.time()

        with self.conn_mgr.get_connection() as conn:
            conn.execute(
                f"""
                UPDATE {self.table_name} SET
                    current_task = ?, updated_at = ?
                WHERE project_name = ?
                """,
                (current_task, progress.updated_at, project_name),
            )
            conn.commit()

        return progress

    def increment_completed(
        self, project_name: str, increment: int = 1
    ) -> Optional[Progress]:
        """
        增加完成计数

        Args:
            project_name: 项目名
            increment: 增量

        Returns:
            Optional[Progress]: 更新后的进度
        """
        with self.conn_mgr.get_connection() as conn:
            conn.execute(
                f"""
                UPDATE {self.table_name} SET
                    completed_tasks = completed_tasks + ?,
                    updated_at = ?
                WHERE project_name = ?
                """,
                (increment, time.time(), project_name),
            )
            conn.commit()

        return self.get_by_project(project_name)

    def update_total(self, project_name: str, total_tasks: int) -> Optional[Progress]:
        """
        更新总任务数

        Args:
            project_name: 项目名
            total_tasks: 总任务数

        Returns:
            Optional[Progress]: 更新后的进度
        """
        with self.conn_mgr.get_connection() as conn:
            conn.execute(
                f"""
                UPDATE {self.table_name} SET
                    total_tasks = ?, updated_at = ?
                WHERE project_name = ?
                """,
                (total_tasks, time.time(), project_name),
            )
            conn.commit()

        return self.get_by_project(project_name)

    def save_checkpoint(self, project_name: str, checkpoint: str) -> Optional[Progress]:
        """
        保存检查点

        Args:
            project_name: 项目名
            checkpoint: 检查点描述

        Returns:
            Optional[Progress]: 更新后的进度
        """
        with self.conn_mgr.get_connection() as conn:
            conn.execute(
                f"""
                UPDATE {self.table_name} SET
                    last_checkpoint = ?, updated_at = ?
                WHERE project_name = ?
                """,
                (checkpoint, time.time(), project_name),
            )
            conn.commit()

        return self.get_by_project(project_name)
