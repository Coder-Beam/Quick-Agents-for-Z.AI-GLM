"""
AuditReporter - 审计报告生成

核心功能:
- generate_session_report(): 会话级审计报告（Markdown）
- generate_file_report(): 文件级审计报告（Markdown）
- generate_summary(): 审计概览（Markdown）
- 支持 Markdown 和 JSON 格式输出

设计原则:
- 单一职责：仅负责报告生成
- 可扩展：支持自定义报告模板
- 零依赖：不依赖外部模板引擎
"""

import json
import logging
import time
from typing import Optional, List, Dict

from .models import (
    AuditLog,
    AuditIssue,
    AuditLesson,
)
from .code_audit import CodeAuditTracker

logger = logging.getLogger(__name__)


class AuditReporter:
    """
    审计报告生成器

    使用方式:
        reporter = AuditReporter(tracker)

        # 会话报告
        report = reporter.generate_session_report('sess-001')
        print(report)

        # 文件报告
        report = reporter.generate_file_report('src/auth.py')
        print(report)

        # 保存到文件
        reporter.save_report(report, '.quickagents/audit_reports/report.md')
    """

    def __init__(self, tracker: CodeAuditTracker):
        """
        初始化报告生成器

        Args:
            tracker: CodeAuditTracker 实例
        """
        self.tracker = tracker

    def generate_session_report(
        self,
        session_id: str,
        issues: Optional[List[AuditIssue]] = None,
        lessons: Optional[List[AuditLesson]] = None,
        format: str = "markdown",
    ) -> str:
        """
        生成会话级审计报告

        Args:
            session_id: 会话 ID
            issues: 关联的问题列表（可选）
            lessons: 关联的学习经验列表（可选）
            format: 输出格式 (markdown/json)

        Returns:
            str: 报告内容
        """
        summary = self.tracker.get_session_summary(session_id)
        changes = self.tracker.get_changes(session_id=session_id, limit=50)

        if format == "json":
            return self._session_report_json(summary, changes, issues, lessons)
        return self._session_report_md(summary, changes, issues, lessons)

    def generate_file_report(self, file_path: str, format: str = "markdown") -> str:
        """
        生成文件级审计报告

        Args:
            file_path: 文件路径
            format: 输出格式 (markdown/json)

        Returns:
            str: 报告内容
        """
        history = self.tracker.get_file_history(file_path)

        if format == "json":
            return self._file_report_json(file_path, history)
        return self._file_report_md(file_path, history)

    def generate_summary(self, format: str = "markdown") -> str:
        """
        生成审计概览

        Args:
            format: 输出格式 (markdown/json)

        Returns:
            str: 概览内容
        """
        stats = self.tracker.get_stats()

        if format == "json":
            return json.dumps(stats, indent=2, ensure_ascii=False)
        return self._summary_md(stats)

    def save_report(self, content: str, output_path: str) -> str:
        """
        保存报告到文件

        Args:
            content: 报告内容
            output_path: 输出路径

        Returns:
            str: 保存的文件路径
        """
        from pathlib import Path

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Saved audit report to: {output_path}")
        return str(path)

    # ==================== Markdown 报告 ====================

    def _session_report_md(
        self,
        summary: Dict,
        changes: List[AuditLog],
        issues: Optional[List[AuditIssue]] = None,
        lessons: Optional[List[AuditLesson]] = None,
    ) -> str:
        """生成会话 Markdown 报告"""
        lines = []
        lines.append(f"# 审计报告 — 会话 {summary['session_id'][:8]}")
        lines.append("")
        lines.append(f"生成时间: {_fmt_time(time.time())}")
        lines.append("")

        # 概览
        lines.append("## 概览")
        lines.append("")
        lines.append("| 指标 | 值 |")
        lines.append("|------|-----|")
        lines.append(f"| 总变更数 | {summary['total_changes']} |")
        lines.append(f"| 涉及文件 | {summary['unique_files']} |")
        lines.append(f"| 新增行数 | +{summary['total_lines_added']} |")
        lines.append(f"| 删除行数 | -{summary['total_lines_removed']} |")
        lines.append("")

        # 变更类型分布
        if summary["by_change_type"]:
            lines.append("### 变更类型分布")
            lines.append("")
            for ct, count in summary["by_change_type"].items():
                lines.append(f"- **{ct}**: {count}")
            lines.append("")

        # 质量状态分布
        if summary["by_quality_status"]:
            lines.append("### 质量状态")
            lines.append("")
            for qs, count in summary["by_quality_status"].items():
                icon = "✅" if qs == "PASSED" else "❌" if qs == "FAILED" else "⏳"
                lines.append(f"- {icon} **{qs}**: {count}")
            lines.append("")

        # 最近变更
        if summary["recent_files"]:
            lines.append("### 最近变更文件")
            lines.append("")
            lines.append("| 文件 | 类型 | 时间 |")
            lines.append("|------|------|------|")
            for f in summary["recent_files"]:
                lines.append(f"| `{f['file_path']}` | {f['change_type']} | {_fmt_time(f['created_at'])} |")
            lines.append("")

        # 问题
        if issues:
            lines.append("## 发现问题")
            lines.append("")
            for issue in issues:
                icon = {"P0": "🔴", "P1": "🟡", "P2": "🔵"}.get(issue.severity.value, "⚪")
                lines.append(f"### {icon} [{issue.severity.value}] {issue.error_message[:80]}")
                if issue.file_path:
                    lines.append(f"- 文件: `{issue.file_path}`")
                if issue.check_name:
                    lines.append(f"- 检查器: {issue.check_name}")
                lines.append(f"- 状态: {issue.status.value}")
                lines.append("")

        # 学习经验
        if lessons:
            lines.append("## 学习经验")
            lines.append("")
            for lesson in lessons:
                lines.append(f"### {lesson.title}")
                lines.append(f"- 类型: {lesson.lesson_type.value}")
                if lesson.category:
                    lines.append(f"- 分类: {lesson.category}")
                lines.append(f"- 描述: {lesson.description}")
                if lesson.prevention_tip:
                    lines.append(f"- 预防: {lesson.prevention_tip}")
                lines.append("")

        return "\n".join(lines)

    def _file_report_md(self, file_path: str, history: List[AuditLog]) -> str:
        """生成文件 Markdown 报告"""
        lines = []
        lines.append(f"# 文件审计报告 — `{file_path}`")
        lines.append("")
        lines.append(f"生成时间: {_fmt_time(time.time())}")
        lines.append(f"变更历史: {len(history)} 条记录")
        lines.append("")

        if not history:
            lines.append("无变更记录。")
            return "\n".join(lines)

        lines.append("## 变更历史")
        lines.append("")
        lines.append("| 时间 | 类型 | 工具 | +行/-行 | 状态 |")
        lines.append("|------|------|------|---------|------|")
        for log in history:
            status_icon = {"PASSED": "✅", "FAILED": "❌", "PENDING": "⏳"}.get(log.quality_status.value, "?")
            lines.append(
                f"| {_fmt_time(log.created_at)} "
                f"| {log.change_type.value} "
                f"| {log.tool_name or '-'} "
                f"| +{log.lines_added}/-{log.lines_removed} "
                f"| {status_icon} |"
            )
        lines.append("")

        return "\n".join(lines)

    def _summary_md(self, stats: Dict) -> str:
        """生成概览 Markdown"""
        lines = []
        lines.append("# 审计概览")
        lines.append("")
        lines.append("| 指标 | 值 |")
        lines.append("|------|-----|")
        lines.append(f"| 总变更数 | {stats['total_changes']} |")
        lines.append(f"| 总会话数 | {stats['total_sessions']} |")
        lines.append(f"| 总文件数 | {stats['total_files']} |")
        lines.append("")
        return "\n".join(lines)

    # ==================== JSON 报告 ====================

    def _session_report_json(
        self,
        summary: Dict,
        changes: List[AuditLog],
        issues: Optional[List[AuditIssue]] = None,
        lessons: Optional[List[AuditLesson]] = None,
    ) -> str:
        """生成会话 JSON 报告"""
        data = {
            "report_type": "session",
            "session_id": summary["session_id"],
            "generated_at": time.time(),
            "summary": summary,
            "changes": [
                {
                    "id": c.id,
                    "file_path": c.file_path,
                    "change_type": c.change_type.value,
                    "lines_added": c.lines_added,
                    "lines_removed": c.lines_removed,
                    "quality_status": c.quality_status.value,
                    "created_at": c.created_at,
                }
                for c in changes
            ],
            "issues": [
                {
                    "id": i.id,
                    "severity": i.severity.value,
                    "type": i.issue_type.value,
                    "file_path": i.file_path,
                    "error_message": i.error_message,
                    "status": i.status.value,
                }
                for i in (issues or [])
            ],
            "lessons": [
                {
                    "id": lesson.id,
                    "title": lesson.title,
                    "type": lesson.lesson_type.value,
                    "category": lesson.category,
                }
                for lesson in (lessons or [])
            ],
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _file_report_json(self, file_path: str, history: List[AuditLog]) -> str:
        """生成文件 JSON 报告"""
        data = {
            "report_type": "file",
            "file_path": file_path,
            "generated_at": time.time(),
            "history_count": len(history),
            "history": [
                {
                    "id": h.id,
                    "change_type": h.change_type.value,
                    "lines_added": h.lines_added,
                    "lines_removed": h.lines_removed,
                    "quality_status": h.quality_status.value,
                    "session_id": h.session_id,
                    "created_at": h.created_at,
                }
                for h in history
            ],
        }
        return json.dumps(data, indent=2, ensure_ascii=False)


# ==================== 辅助函数 ====================


def _fmt_time(timestamp: float) -> str:
    """格式化时间戳"""
    from datetime import datetime

    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
