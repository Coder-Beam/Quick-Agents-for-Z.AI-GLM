"""
CodeAuditTracker - 实时文件变更追踪

核心功能:
- record_change(): 记录文件变更（write/edit 触发）
- get_changes(): 查询变更记录
- get_session_summary(): 会话变更摘要
- get_file_history(): 文件变更历史
- Diff 统计（lines_added/lines_removed）
- 轻量摘要（write/edit 时）+ 完整 diff（commit 时）

设计原则:
- 依赖注入：通过构造函数接收 ConnectionManager
- 低开销：仅记录必要信息，diff 按需计算
- 可查询：支持多种维度检索审计日志
"""

import logging
import time
import uuid
from difflib import unified_diff
from typing import Optional, List, Dict, Any

from .models import AuditLog, ChangeType, QualityStatus

logger = logging.getLogger(__name__)


class CodeAuditTracker:
    """
    代码审计追踪器

    使用方式:
        tracker = CodeAuditTracker(conn_mgr)

        # 记录文件变更
        tracker.record_change(
            file_path='src/auth.py',
            change_type='MODIFY',
            diff='--- a/src/auth.py\\n+++ b/src/auth.py\\n...',
            tool_name='edit',
            session_id='sess-001',
            task_id='T001'
        )

        # 查询变更
        changes = tracker.get_changes(session_id='sess-001')

        # 会话摘要
        summary = tracker.get_session_summary('sess-001')
    """

    def __init__(self, connection_manager):
        """
        初始化追踪器

        Args:
            connection_manager: ConnectionManager 实例
        """
        self.conn_mgr = connection_manager

    def record_change(
        self,
        file_path: str,
        change_type: str,
        diff: Optional[str] = None,
        tool_name: Optional[str] = None,
        session_id: str = "",
        task_id: Optional[str] = None,
        summary: Optional[str] = None,
    ) -> AuditLog:
        """
        记录文件变更

        Args:
            file_path: 变更文件路径
            change_type: 变更类型 (CREATE/MODIFY/DELETE)
            diff: unified diff 内容
            tool_name: 触发工具名 (write/edit)
            session_id: 会话 ID
            task_id: 关联任务 ID
            summary: 轻量变更摘要

        Returns:
            AuditLog: 审计日志记录
        """
        log = AuditLog(
            id=uuid.uuid4().hex[:16],
            session_id=session_id,
            task_id=task_id,
            file_path=file_path,
            change_type=ChangeType(change_type),
            diff_content=diff,
            lines_added=_count_lines(diff, "+") if diff else 0,
            lines_removed=_count_lines(diff, "-") if diff else 0,
            tool_name=tool_name,
            quality_status=QualityStatus.PENDING,
            summary=summary,
            created_at=time.time(),
        )

        with self.conn_mgr.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO audit_log
                    (id, session_id, task_id, file_path, change_type,
                     diff_content, lines_added, lines_removed, tool_name,
                     quality_status, summary, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log.id,
                    log.session_id,
                    log.task_id,
                    log.file_path,
                    log.change_type.value,
                    log.diff_content,
                    log.lines_added,
                    log.lines_removed,
                    log.tool_name,
                    log.quality_status.value,
                    log.summary,
                    log.created_at,
                ),
            )
            conn.commit()

        logger.debug(f"Audit: {log.change_type.value} {log.file_path} (+{log.lines_added}/-{log.lines_removed})")
        return log

    def record_change_with_diff(
        self,
        file_path: str,
        old_content: str,
        new_content: str,
        tool_name: Optional[str] = None,
        session_id: str = "",
        task_id: Optional[str] = None,
    ) -> AuditLog:
        """
        通过对比旧/新内容自动计算 diff 并记录变更

        Args:
            file_path: 文件路径
            old_content: 变更前内容（空字符串表示新建）
            new_content: 变更后内容（空字符串表示删除）
            tool_name: 触发工具名
            session_id: 会话 ID
            task_id: 关联任务 ID

        Returns:
            AuditLog: 审计日志记录
        """
        if not old_content and new_content:
            change_type = ChangeType.CREATE
        elif old_content and not new_content:
            change_type = ChangeType.DELETE
        else:
            change_type = ChangeType.MODIFY

        diff_lines = list(
            unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}",
            )
        )
        diff_content = "".join(diff_lines)

        return self.record_change(
            file_path=file_path,
            change_type=change_type.value,
            diff=diff_content if diff_content else None,
            tool_name=tool_name,
            session_id=session_id,
            task_id=task_id,
        )

    def update_quality_status(self, log_id: str, status: str) -> bool:
        """
        更新审计日志的质量状态

        Args:
            log_id: 审计日志 ID
            status: 质量状态 (PENDING/PASSED/FAILED/SKIPPED)

        Returns:
            bool: 是否更新成功
        """
        try:
            with self.conn_mgr.get_connection() as conn:
                cursor = conn.execute(
                    "UPDATE audit_log SET quality_status = ? WHERE id = ?",
                    (status, log_id),
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to update quality status: {e}")
            return False

    def get_changes(
        self,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        file_path: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """
        查询变更记录

        Args:
            session_id: 按会话过滤
            task_id: 按任务过滤
            file_path: 按文件过滤
            limit: 返回数量限制

        Returns:
            List[AuditLog]: 审计日志列表
        """
        conditions = []
        params: list = []

        if session_id is not None:
            conditions.append("session_id = ?")
            params.append(session_id)
        if task_id is not None:
            conditions.append("task_id = ?")
            params.append(task_id)
        if file_path is not None:
            conditions.append("file_path = ?")
            params.append(file_path)

        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        sql = f"SELECT * FROM audit_log{where} ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(sql, params)
            return [_row_to_audit_log(row) for row in cursor.fetchall()]

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话变更摘要

        Args:
            session_id: 会话 ID

        Returns:
            Dict: 摘要信息
        """
        with self.conn_mgr.get_connection() as conn:
            # 总体统计
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total_changes,
                    COUNT(DISTINCT file_path) as unique_files,
                    SUM(lines_added) as total_added,
                    SUM(lines_removed) as total_removed
                FROM audit_log WHERE session_id = ?
                """,
                (session_id,),
            )
            row = cursor.fetchone()

            total_changes = row[0] if row else 0
            unique_files = row[1] if row else 0
            total_added = row[2] if row else 0
            total_removed = row[3] if row else 0

            # 按变更类型统计
            cursor = conn.execute(
                """
                SELECT change_type, COUNT(*)
                FROM audit_log WHERE session_id = ?
                GROUP BY change_type
                """,
                (session_id,),
            )
            by_type = {row[0]: row[1] for row in cursor.fetchall()}

            # 按质量状态统计
            cursor = conn.execute(
                """
                SELECT quality_status, COUNT(*)
                FROM audit_log WHERE session_id = ?
                GROUP BY quality_status
                """,
                (session_id,),
            )
            by_status = {row[0]: row[1] for row in cursor.fetchall()}

            # 最近变更的文件
            cursor = conn.execute(
                """
                SELECT file_path, change_type, created_at
                FROM audit_log WHERE session_id = ?
                ORDER BY created_at DESC LIMIT 10
                """,
                (session_id,),
            )
            recent_files = [{"file_path": r[0], "change_type": r[1], "created_at": r[2]} for r in cursor.fetchall()]

        return {
            "session_id": session_id,
            "total_changes": total_changes,
            "unique_files": unique_files,
            "total_lines_added": total_added or 0,
            "total_lines_removed": total_removed or 0,
            "by_change_type": by_type,
            "by_quality_status": by_status,
            "recent_files": recent_files,
        }

    def get_file_history(self, file_path: str, limit: int = 50) -> List[AuditLog]:
        """
        获取文件变更历史

        Args:
            file_path: 文件路径
            limit: 返回数量限制

        Returns:
            List[AuditLog]: 变更历史列表（按时间倒序）
        """
        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM audit_log
                WHERE file_path = ?
                ORDER BY created_at DESC LIMIT ?
                """,
                (file_path, limit),
            )
            return [_row_to_audit_log(row) for row in cursor.fetchall()]

    def get_stats(self) -> Dict[str, Any]:
        """
        获取全局统计

        Returns:
            Dict: 统计信息
        """
        with self.conn_mgr.get_connection() as conn:
            # 总记录数
            cursor = conn.execute("SELECT COUNT(*) FROM audit_log")
            total = cursor.fetchone()[0]

            # 按会话统计
            cursor = conn.execute("SELECT COUNT(DISTINCT session_id) FROM audit_log")
            sessions = cursor.fetchone()[0]

            # 按文件统计
            cursor = conn.execute("SELECT COUNT(DISTINCT file_path) FROM audit_log")
            files = cursor.fetchone()[0]

        return {
            "total_changes": total,
            "total_sessions": sessions,
            "total_files": files,
        }

    def cleanup_old_logs(self, days: int = 90) -> int:
        """
        清理过期日志（仅保留统计信息）

        Args:
            days: 保留天数

        Returns:
            int: 清理的记录数
        """
        cutoff = time.time() - (days * 86400)

        with self.conn_mgr.get_connection() as conn:
            # 清除 diff_content（保留统计字段）
            cursor = conn.execute(
                """
                UPDATE audit_log
                SET diff_content = NULL, summary = NULL
                WHERE created_at < ? AND diff_content IS NOT NULL
                """,
                (cutoff,),
            )
            cleaned = cursor.rowcount
            conn.commit()

        if cleaned > 0:
            logger.info(f"Cleaned diff content for {cleaned} old audit logs (>{days}d)")

        return cleaned


# ==================== 辅助函数 ====================


def _count_lines(diff: str, prefix: str) -> int:
    """统计 diff 中以指定前缀开头的行数"""
    count = 0
    for line in diff.splitlines():
        if line.startswith(prefix) and not line.startswith(f"{prefix}{prefix}{prefix}"):
            count += 1
    return count


def _row_to_audit_log(row: tuple) -> AuditLog:
    """数据库行转 AuditLog 实体"""
    return AuditLog(
        id=row[0],
        session_id=row[1],
        task_id=row[2],
        file_path=row[3],
        change_type=ChangeType(row[4]),
        diff_content=row[5],
        lines_added=row[6] or 0,
        lines_removed=row[7] or 0,
        tool_name=row[8],
        quality_status=QualityStatus(row[9]),
        summary=row[10],
        created_at=row[11],
    )
