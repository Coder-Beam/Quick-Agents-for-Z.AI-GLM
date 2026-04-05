"""
AuditGuard - 审计问责门面类

统一入口，协调 CodeAuditTracker + QualityGate + AccountabilityEngine。

使用方式:
    guard = AuditGuard()

    # 文件变更追踪
    guard.on_file_change('src/main.py', 'create', diff='...', tool_name='write')

    # Git commit 触发原子检查
    guard.on_git_commit(['src/main.py', 'tests/test_main.py'])

    # Task 完成触发全量检查
    guard.on_task_complete('T001')

    # 查看审计摘要
    summary = guard.get_audit_summary()

    guard.close()
"""

import logging
from typing import Optional, List, Dict, Any

from .audit_config import AuditConfig
from .code_audit import CodeAuditTracker
from .quality_gate import QualityGate
from .accountability import AccountabilityEngine
from .audit_reporter import AuditReporter
from .models import GateReport, AuditIssue, AuditLesson

logger = logging.getLogger(__name__)


class AuditGuard:
    """
    AuditGuard 门面类

    协调三大子模块:
    - CodeAuditTracker: 文件变更追踪
    - QualityGate: 质量门禁
    - AccountabilityEngine: 问责引擎
    """

    def __init__(
        self,
        db_path: str = ".quickagents/unified.db",
        config_path: Optional[str] = None,
    ):
        """
        初始化 AuditGuard

        Args:
            db_path: 数据库路径
            config_path: 配置文件路径（可选）
        """
        from ..core.connection_manager import ConnectionManager

        self.db_path = db_path
        self.config = AuditConfig.from_file(config_path) if config_path else AuditConfig()

        # 初始化连接管理器（触发迁移）
        self.conn_mgr = ConnectionManager(db_path)

        # 初始化子模块（注意各模块签名不同）
        self.tracker = CodeAuditTracker(self.conn_mgr)
        self.gate = QualityGate(".", self.config)
        self.accountability = AccountabilityEngine(self.conn_mgr, self.config)
        self.reporter = AuditReporter(self.tracker)

        logger.info("AuditGuard initialized")

    # ==================== 文件变更追踪 ====================

    def on_file_change(
        self,
        file_path: str,
        change_type: str,
        diff: Optional[str] = None,
        tool_name: Optional[str] = None,
        session_id: str = "",
        task_id: Optional[str] = None,
        summary: Optional[str] = None,
    ) -> Optional[str]:
        """
        记录文件变更

        Args:
            file_path: 文件路径
            change_type: create/modify/delete
            diff: diff 内容
            tool_name: 触发工具名
            session_id: 会话 ID
            task_id: 关联任务 ID
            summary: 变更摘要

        Returns:
            审计日志 ID，如果追踪禁用返回 None
        """
        if not self.config.code_audit_enabled:
            return None

        log_id = self.tracker.record_change(
            file_path=file_path,
            change_type=change_type,
            diff_content=diff,
            tool_name=tool_name,
            session_id=session_id,
            task_id=task_id,
            summary=summary,
        )
        logger.debug(f"File change tracked: {change_type} {file_path}")
        return log_id

    # ==================== Git commit 触发 ====================

    def on_git_commit(
        self,
        staged_files: Optional[List[str]] = None,
        session_id: str = "",
    ) -> Optional[GateReport]:
        """
        Git commit 触发原子级质量检查

        Args:
            staged_files: 变更文件列表
            session_id: 会话 ID

        Returns:
            GateReport，如果门禁禁用返回 None
        """
        if not self.config.quality_gate_enabled:
            return None

        report = self.gate.run_atomic_checks(staged_files or [])

        if not report.passed:
            # 分析失败并记录问题
            issues = self.accountability.analyze_failure(
                report,
                session_id=session_id,
            )
            for issue in issues:
                self.accountability.record_issue(issue)
                # 检测修复循环
                loop = self.accountability.check_fix_loop(issue)
                if loop.get("loop_detected"):
                    logger.warning(f"Fix loop detected: {loop['action']} (count={loop['occurrence_count']})")

            # 提取学习经验
            self.accountability.extract_lessons(issues)

            # 生成反馈
            feedback = self.accountability.generate_feedback(issues)
            if feedback:
                logger.info(feedback)

        return report

    # ==================== Task 完成触发 ====================

    def on_task_complete(
        self,
        task_id: str,
        session_id: str = "",
    ) -> Optional[GateReport]:
        """
        Task 完成触发全量级质量检查

        Args:
            task_id: 任务 ID
            session_id: 会话 ID

        Returns:
            GateReport，如果门禁禁用返回 None
        """
        if not self.config.quality_gate_enabled:
            return None

        report = self.gate.run_full_checks()

        if not report.passed:
            # 分析失败并记录问题
            issues = self.accountability.analyze_failure(
                report,
                session_id=session_id,
                task_id=task_id,
            )
            for issue in issues:
                self.accountability.record_issue(issue)

            # 提取学习经验
            self.accountability.extract_lessons(issues)
        else:
            # 自动解决该 task 的所有 OPEN 问题
            open_issues = self.accountability.get_issues(
                status="OPEN",
                limit=100,
            )
            for issue in open_issues:
                if issue.task_id == task_id:
                    self.accountability.resolve_issue(
                        issue.id,
                        fix_strategy="auto_resolved",
                        fix_commit="quality_gate_passed",
                    )

        return report

    # ==================== 查询方法 ====================

    def get_audit_summary(self) -> Dict[str, Any]:
        """获取审计摘要"""
        tracker_stats = self.tracker.get_stats()
        accountability_stats = self.accountability.get_stats()

        return {
            "tracker": tracker_stats,
            "accountability": accountability_stats,
            "config": {
                "code_audit_enabled": self.config.code_audit_enabled,
                "quality_gate_enabled": self.config.quality_gate_enabled,
                "lesson_extraction": self.config.lesson_extraction,
            },
        }

    def get_issues(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 50,
    ) -> List[AuditIssue]:
        """查询问题列表"""
        return self.accountability.get_issues(
            status=status,
            severity=severity,
            limit=limit,
        )

    def get_lessons(
        self,
        category: Optional[str] = None,
        limit: int = 50,
    ) -> List[AuditLesson]:
        """查询学习经验"""
        return self.accountability.get_lessons(category=category, limit=limit)

    def generate_report(
        self,
        session_id: str = "",
        file_path: str = "",
        fmt: str = "markdown",
    ) -> str:
        """
        生成审计报告

        Args:
            session_id: 会话 ID（按会话生成）
            file_path: 文件路径（按文件生成）
            fmt: 报告格式 markdown/json

        Returns:
            报告内容字符串
        """
        if session_id:
            return self.reporter.session_report(
                session_id,
                fmt=fmt,
            )
        elif file_path:
            return self.reporter.file_report(
                file_path,
                fmt=fmt,
            )
        else:
            return self.reporter.summary(fmt=fmt)

    # ==================== 生命周期 ====================

    def close(self):
        """关闭资源"""
        if hasattr(self, "conn_mgr"):
            self.conn_mgr.close()
            logger.info("AuditGuard closed")
