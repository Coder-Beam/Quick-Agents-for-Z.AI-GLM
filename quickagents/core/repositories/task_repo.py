"""
TaskRepository - 任务仓储

核心功能:
- CRUD 操作
- 按状态/优先级查询
- 状态流转
- 统计分析
"""

import time
import json
import logging
from typing import List, Optional, Dict, Any

from .base import BaseRepository
from .models import Task, TaskStatus, TaskPriority

logger = logging.getLogger(__name__)


class TaskRepository(BaseRepository[Task]):
    """
    任务仓储

    使用方式:
        repo = TaskRepository(conn_mgr, tx_mgr)

        # 添加任务
        task = Task(id="T001", name="实现认证", priority=TaskPriority.P0)
        repo.add(task)

        # 更新状态
        repo.update_status("T001", TaskStatus.IN_PROGRESS)

        # 查询任务
        tasks = repo.get_by_status(TaskStatus.PENDING)
    """

    @property
    def table_name(self) -> str:
        return "tasks"

    # ==================== 实体转换 ====================

    def _row_to_entity(self, row: tuple) -> Task:
        """行转实体"""
        return Task(
            id=row[0],
            name=row[1],
            priority=TaskPriority(row[2]),
            status=TaskStatus(row[3]),
            assignee=row[4],
            start_time=row[5],
            end_time=row[6],
            created_at=row[7],
            updated_at=row[8],
            metadata=json.loads(row[9]) if len(row) > 9 and row[9] else {},
        )

    def _entity_to_dict(self, entity: Task) -> Dict[str, Any]:
        """实体转字典"""
        return {
            "id": entity.id,
            "name": entity.name,
            "priority": entity.priority.value,
            "status": entity.status.value,
            "assignee": entity.assignee,
            "start_time": entity.start_time,
            "end_time": entity.end_time,
            "created_at": entity.created_at,
            "updated_at": entity.updated_at,
            "metadata": json.dumps(entity.metadata, ensure_ascii=False),
        }

    # ==================== 专用查询方法 ====================

    def get_by_status(self, status: TaskStatus, limit: int = 100) -> List[Task]:
        """
        获取指定状态的任务

        Args:
            status: 任务状态
            limit: 返回数量限制

        Returns:
            List[Task]: 任务列表
        """
        return self.get_all(
            filters={"status": status.value},
            order_by="priority ASC, created_at ASC",
            limit=limit,
        )

    def get_by_priority(
        self, priority: TaskPriority, status: Optional[TaskStatus] = None, limit: int = 100
    ) -> List[Task]:
        """
        获取指定优先级的任务

        Args:
            priority: 任务优先级
            status: 任务状态（可选）
            limit: 返回数量限制

        Returns:
            List[Task]: 任务列表
        """
        filters = {"priority": priority.value}
        if status:
            filters["status"] = status.value

        return self.get_all(filters=filters, order_by="created_at ASC", limit=limit)

    def get_by_assignee(
        self, assignee: str, status: Optional[TaskStatus] = None, limit: int = 100
    ) -> List[Task]:
        """
        获取指定负责人的任务

        Args:
            assignee: 负责人
            status: 任务状态（可选）
            limit: 返回数量限制

        Returns:
            List[Task]: 任务列表
        """
        filters = {"assignee": assignee}
        if status:
            filters["status"] = status.value

        return self.get_all(
            filters=filters, order_by="priority ASC, created_at ASC", limit=limit
        )

    def get_pending(self, limit: int = 100) -> List[Task]:
        """
        获取待处理任务（PENDING + IN_PROGRESS）

        Args:
            limit: 返回数量限制

        Returns:
            List[Task]: 任务列表
        """
        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(
                f"""
                SELECT * FROM {self.table_name}
                WHERE status IN ('pending', 'in_progress')
                ORDER BY
                    CASE priority
                        WHEN 'P0' THEN 1
                        WHEN 'P1' THEN 2
                        WHEN 'P2' THEN 3
                        WHEN 'P3' THEN 4
                    END,
                    created_at ASC
                LIMIT ?
                """,
                (limit,),
            )
            return [self._row_to_entity(row) for row in cursor.fetchall()]

    def get_blocked(self, limit: int = 100) -> List[Task]:
        """
        获取阻塞的任务

        Args:
            limit: 返回数量限制

        Returns:
            List[Task]: 任务列表
        """
        return self.get_by_status(TaskStatus.BLOCKED, limit)

    def get_next_task(self) -> Optional[Task]:
        """
        获取下一个待处理的任务（最高优先级）

        Returns:
            Optional[Task]: 任务实体
        """
        tasks = self.get_all(
            filters={"status": TaskStatus.PENDING.value},
            order_by="""
                CASE priority
                    WHEN 'P0' THEN 1
                    WHEN 'P1' THEN 2
                    WHEN 'P2' THEN 3
                    WHEN 'P3' THEN 4
                END,
                created_at ASC
            """,
            limit=1,
        )
        return tasks[0] if tasks else None

    # ==================== 写入方法 ====================

    def add(self, task: Task) -> Task:
        """
        添加任务

        Args:
            task: 任务实体

        Returns:
            Task: 添加后的任务
        """
        task.created_at = time.time()
        task.updated_at = time.time()

        data = self._entity_to_dict(task)

        with self.conn_mgr.get_connection() as conn:
            conn.execute(
                f"""
                INSERT INTO {self.table_name} (
                    id, name, priority, status, assignee,
                    start_time, end_time, created_at, updated_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["id"],
                    data["name"],
                    data["priority"],
                    data["status"],
                    data["assignee"],
                    data["start_time"],
                    data["end_time"],
                    data["created_at"],
                    data["updated_at"],
                    data["metadata"],
                ),
            )
            conn.commit()

        return task

    def update(self, task: Task) -> Task:
        """
        更新任务

        Args:
            task: 任务实体

        Returns:
            Task: 更新后的任务
        """
        task.updated_at = time.time()

        data = self._entity_to_dict(task)

        with self.conn_mgr.get_connection() as conn:
            conn.execute(
                f"""
                UPDATE {self.table_name} SET
                    name = ?, priority = ?, status = ?, assignee = ?,
                    start_time = ?, end_time = ?, updated_at = ?, metadata = ?
                WHERE id = ?
                """,
                (
                    data["name"],
                    data["priority"],
                    data["status"],
                    data["assignee"],
                    data["start_time"],
                    data["end_time"],
                    data["updated_at"],
                    data["metadata"],
                    data["id"],
                ),
            )
            conn.commit()

        return task

    # ==================== 状态流转方法 ====================

    def update_status(
        self, task_id: str, status: TaskStatus, notes: Optional[str] = None
    ) -> Optional[Task]:
        """
        更新任务状态

        Args:
            task_id: 任务 ID
            status: 新状态
            notes: 备注（可选）

        Returns:
            Optional[Task]: 更新后的任务
        """
        task = self.get(task_id)
        if not task:
            return None

        current_time = time.time()
        updates = {"status": status.value, "updated_at": current_time}

        # 状态变更时更新时间戳
        if status == TaskStatus.IN_PROGRESS and task.status == TaskStatus.PENDING:
            updates["start_time"] = current_time
        elif status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
            updates["end_time"] = current_time

        # 添加备注到 metadata
        if notes:
            metadata = task.metadata or {}
            if "notes" not in metadata:
                metadata["notes"] = []
            metadata["notes"].append(
                {"time": current_time, "status": status.value, "note": notes}
            )
            updates["metadata"] = json.dumps(metadata, ensure_ascii=False)

        # 执行更新
        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [task_id]

        with self.conn_mgr.get_connection() as conn:
            conn.execute(
                f"UPDATE {self.table_name} SET {set_clause} WHERE id = ?", values
            )
            conn.commit()

        return self.get(task_id)

    def start_task(self, task_id: str) -> Optional[Task]:
        """
        开始任务

        Args:
            task_id: 任务 ID

        Returns:
            Optional[Task]: 更新后的任务
        """
        return self.update_status(task_id, TaskStatus.IN_PROGRESS)

    def complete_task(self, task_id: str, notes: Optional[str] = None) -> Optional[Task]:
        """
        完成任务

        Args:
            task_id: 任务 ID
            notes: 完成备注

        Returns:
            Optional[Task]: 更新后的任务
        """
        return self.update_status(task_id, TaskStatus.COMPLETED, notes)

    def block_task(self, task_id: str, reason: Optional[str] = None) -> Optional[Task]:
        """
        阻塞任务

        Args:
            task_id: 任务 ID
            reason: 阻塞原因

        Returns:
            Optional[Task]: 更新后的任务
        """
        return self.update_status(task_id, TaskStatus.BLOCKED, reason)

    def cancel_task(self, task_id: str, reason: Optional[str] = None) -> Optional[Task]:
        """
        取消任务

        Args:
            task_id: 任务 ID
            reason: 取消原因

        Returns:
            Optional[Task]: 更新后的任务
        """
        return self.update_status(task_id, TaskStatus.CANCELLED, reason)

    def unblock_task(self, task_id: str) -> Optional[Task]:
        """
        解除阻塞（恢复到 IN_PROGRESS）

        Args:
            task_id: 任务 ID

        Returns:
            Optional[Task]: 更新后的任务
        """
        return self.update_status(task_id, TaskStatus.IN_PROGRESS)

    # ==================== 统计方法 ====================

    def count_by_status(self) -> Dict[str, int]:
        """
        按状态统计任务数量

        Returns:
            Dict[str, int]: 状态 -> 数量
        """
        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(
                f"""
                SELECT status, COUNT(*) as count
                FROM {self.table_name}
                GROUP BY status
                """
            )
            return {row[0]: row[1] for row in cursor.fetchall()}

    def count_by_priority(self) -> Dict[str, int]:
        """
        按优先级统计任务数量

        Returns:
            Dict[str, int]: 优先级 -> 数量
        """
        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(
                f"""
                SELECT priority, COUNT(*) as count
                FROM {self.table_name}
                GROUP BY priority
                """
            )
            return {row[0]: row[1] for row in cursor.fetchall()}

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取任务统计

        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "total": self.count(),
            "by_status": self.count_by_status(),
            "by_priority": self.count_by_priority(),
            "pending": self.count({"status": TaskStatus.PENDING.value}),
            "in_progress": self.count({"status": TaskStatus.IN_PROGRESS.value}),
            "completed": self.count({"status": TaskStatus.COMPLETED.value}),
            "blocked": self.count({"status": TaskStatus.BLOCKED.value}),
        }
