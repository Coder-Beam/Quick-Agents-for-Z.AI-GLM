"""
AccountabilityEngine - 问责引擎

核心功能:
- analyze_failure(): 从 QualityGate 抱告提取问题并归因
- record_issue(): 记录问题到 audit_issues 表
- resolve_issue(): 更新问题状态（修复闭环）
- extract_lesson(): 提取学习经验 → audit_lessons
- check_fix_loop(): 修复循环检测（3级升级）
- generate_feedback(): 生成自动反馈消息

设计原则:
- 依赖注入: 通过构造函数接收连接管理器
- 可配置: 通过 AuditConfig 控行为
- 零 Token: 所有分析逻辑本地执行
"""

import logging
import re
import time
from typing import Optional, List, Dict, Any

from .models import (
    AuditIssue,
    AuditLesson,
    IssueSeverity,
    IssueType,
    IssueStatus,
    LessonType,
    QualityResult,
    GateReport,
)
from .audit_config import AuditConfig

logger = logging.getLogger(__name__)


# ==================== 严重性映射表（Q20 决策 B+C）====================

DEFAULT_SEVERITY_MAP: Dict[str, IssueSeverity] = {
    # ruff
    "E501": IssueSeverity.P2,
    "E9xx": IssueSeverity.P2,
    "W2xx": IssueSeverity.P1,
    "F401": IssueSeverity.P1,
    "F841": IssueSeverity.P1,
    # mypy
    "type-error": IssueSeverity.P0,
    "arg-type": IssueSeverity.P0,
    "return-value": IssueSeverity.P1,
    "attr-defined": IssueSeverity.P1,
    "name-defined": IssueSeverity.P1,
    # pytest
    "FAILED": IssueSeverity.P0,
    "ERROR": IssueSeverity.P0,
    "coverage_gap": IssueSeverity.P2,
}


class AccountabilityEngine:
    """
    问责引擎

    使用方式:
        engine = AccountabilityEngine(conn_mgr, config)

        # 分析质量门禁失败报告
        issues = engine.analyze_failure(report, session_id='s1')

        for issue in issues:
            engine.record_issue(issue)

        # 提取学习经验
        lessons = engine.extract_lessons(issues)
    """

    def __init__(self, connection_manager, config: Optional[AuditConfig] = None):
        self.conn_mgr = connection_manager
        self.config = config or AuditConfig()

    # ==================== 分析失败 ====================

    def analyze_failure(
        self,
        report: GateReport,
        session_id: str = "",
        task_id: Optional[str] = None,
    ) -> List[AuditIssue]:
        """
        从 QualityGate 报告中提取问题并归因

        解析每个失败的检查项，提取错误信息，
        自动归因到文件/行号/错误码级别。

        Args:
            report: QualityGate 报告
            session_id: 会话 ID
            task_id: 关联任务 ID

        Returns:
            List[AuditIssue]: 提取的问题列表
        """
        issues: List[AuditIssue] = []

        for check in report.failed_checks:
            parsed = self._parse_check_errors(check)
            for error_info in parsed:
                issue = AuditIssue(
                    session_id=session_id,
                    task_id=task_id,
                    issue_type=self._classify_issue_type(check.check_name, error_info),
                    severity=self._classify_severity(check.check_name, error_info),
                    file_path=error_info.get("file_path"),
                    line_number=error_info.get("line_number"),
                    check_name=check.check_name,
                    error_code=error_info.get("error_code"),
                    error_message=error_info["message"],
                    root_cause=self._infer_root_cause(check.check_name, error_info),
                )
                issues.append(issue)

        logger.info(f"Analyzed {len(issues)} issues from {len(report.failed_checks)} failed checks")
        return issues

    # ==================== 记录问题 ====================

    def record_issue(self, issue: AuditIssue) -> AuditIssue:
        """记录问题到 audit_issues 表"""
        with self.conn_mgr.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO audit_issues
                    (id, session_id, task_id, issue_type, severity,
                     file_path, line_number, check_name, error_code,
                     error_message, root_cause, status, created_at,
                     occurrence_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    issue.id,
                    issue.session_id,
                    issue.task_id,
                    issue.issue_type.value,
                    issue.severity.value,
                    issue.file_path,
                    issue.line_number,
                    issue.check_name,
                    issue.error_code,
                    issue.error_message,
                    issue.root_cause,
                    issue.status.value,
                    issue.created_at,
                    issue.occurrence_count,
                ),
            )
            conn.commit()

        logger.debug(f"Recorded issue: {issue.severity.value} {issue.error_message[:60]}")
        return issue

    # ==================== 解决问题 ====================

    def resolve_issue(
        self,
        issue_id: str,
        fix_strategy: Optional[str] = None,
        fix_commit: Optional[str] = None,
    ) -> bool:
        """更新问题状态为 RESOLVED"""
        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE audit_issues
                SET status = ?, resolved_at = ?, fix_strategy = ?, fix_commit = ?
                WHERE id = ?
                """,
                (
                    IssueStatus.RESOLVED.value,
                    time.time(),
                    fix_strategy,
                    fix_commit,
                    issue_id,
                ),
            )
            conn.commit()
            return cursor.rowcount > 0

    # ==================== 学习经验 ====================

    def extract_lesson(self, issue: AuditIssue) -> Optional[AuditLesson]:
        """从问题中提取学习经验，        写入 audit_lessons 表，同时可通过回调写入 Experiential Memory。"""
        if not self.config.lesson_extraction:
            return None

        lesson = AuditLesson(
            issue_id=issue.id,
            lesson_type=self._classify_lesson_type(issue),
            category=self._classify_category(issue),
            title=self._build_lesson_title(issue),
            description=issue.error_message,
            trigger_pattern=self._build_trigger_pattern(issue),
            prevention_tip=self._build_prevention_tip(issue),
        )

        with self.conn_mgr.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO audit_lessons
                    (id, issue_id, lesson_type, category,
                     title, description, trigger_pattern, prevention_tip, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lesson.id,
                    lesson.issue_id,
                    lesson.lesson_type.value,
                    lesson.category,
                    lesson.title,
                    lesson.description,
                    lesson.trigger_pattern,
                    lesson.prevention_tip,
                    lesson.created_at,
                ),
            )
            conn.commit()

        logger.info(f"Extracted lesson: {lesson.title[:60]}")
        return lesson

    def extract_lessons(self, issues: List[AuditIssue]) -> List[AuditLesson]:
        """批量提取学习经验"""
        lessons: List[AuditLesson] = []
        for issue in issues:
            lesson = self.extract_lesson(issue)
            if lesson:
                lessons.append(lesson)
        return lessons

    # ==================== 修复循环检测 ====================

    def check_fix_loop(self, issue: AuditIssue) -> Dict[str, Any]:
        """
        修复循环检测（3级升级）

        规则:
        - 同一 pattern 出现 1 次: P2（正常）
        - 同一 pattern 出现 2 次: 升级到 P1
        - 同一 pattern 出现 3+ 次: 升级到 P0 + 标记阻塞

        Returns:
            Dict: {loop_detected, severity_escalated, occurrence_count, action}
        """
        pattern = self._build_trigger_pattern(issue)
        if not pattern:
            return {
                "loop_detected": False,
                "severity_escalated": False,
                "occurrence_count": 1,
                "action": "monitor",
            }

        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM audit_issues
                WHERE check_name = ? AND error_code = ?
                """,
                (issue.check_name, issue.error_code),
            )
            count = cursor.fetchone()[0]

        # 3级升级
        if count >= 3:
            return {
                "loop_detected": True,
                "severity_escalated": True,
                "occurrence_count": count,
                "action": "block",
            }
        elif count >= 2:
            return {
                "loop_detected": True,
                "severity_escalated": True,
                "occurrence_count": count,
                "action": "escalate",
            }

        return {
            "loop_detected": False,
            "severity_escalated": False,
            "occurrence_count": count,
            "action": "monitor",
        }

    # ==================== 自动反馈 ====================

    def generate_feedback(self, issues: List[AuditIssue]) -> str:
        """生成自动反馈消息"""
        if not issues:
            return ""

        lines = ["[AuditGuard] 质量问题反馈", ""]
        lines.append(f"发现 {len(issues)} 个问题:")

        for issue in issues:
            icon = {"P0": "🔴", "P1": "🟡", "P2": "🔵"}.get(issue.severity.value, "⚪")
            lines.append(f"  {icon} [{issue.severity.value}] {issue.error_message[:80]}")
            if issue.file_path:
                lines.append(f"    文件: {issue.file_path}")
            if issue.root_cause:
                lines.append(f"    根因: {issue.root_cause}")

        lines.append("")
        lines.append("建议:")
        for issue in issues:
            if issue.check_name:
                lines.append(f"  - 运行 `{issue.check_name}` 修复 {issue.file_path or '相关文件'}")

        return "\n".join(lines)

    # ==================== 查询方法 ====================

    def get_issues(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        issue_type: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[AuditIssue]:
        """查询问题列表"""
        conditions: List[str] = []
        params: list = []

        if status is not None:
            conditions.append("status = ?")
            params.append(status)
        if severity is not None:
            conditions.append("severity = ?")
            params.append(severity)
        if issue_type is not None:
            conditions.append("issue_type = ?")
            params.append(issue_type)
        if session_id is not None:
            conditions.append("session_id = ?")
            params.append(session_id)

        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        sql = f"SELECT * FROM audit_issues{where} ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(sql, params)
            return [_row_to_issue(row) for row in cursor.fetchall()]

    def get_lessons(
        self,
        category: Optional[str] = None,
        lesson_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[AuditLesson]:
        """查询学习经验"""
        conditions: List[str] = []
        params: list = []

        if category is not None:
            conditions.append("category = ?")
            params.append(category)
        if lesson_type is not None:
            conditions.append("lesson_type = ?")
            params.append(lesson_type)

        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        sql = f"SELECT * FROM audit_lessons{where} ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(sql, params)
            return [_row_to_lesson(row) for row in cursor.fetchall()]

    def get_stats(self) -> Dict[str, Any]:
        """获取问责统计"""
        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM audit_issues")
            total_issues = cursor.fetchone()[0]

            cursor = conn.execute("SELECT status, COUNT(*) FROM audit_issues GROUP BY status")
            by_status = {row[0]: row[1] for row in cursor.fetchall()}

            cursor = conn.execute("SELECT COUNT(*) FROM audit_lessons")
            total_lessons = cursor.fetchone()[0]

        return {
            "total_issues": total_issues,
            "by_status": by_status,
            "total_lessons": total_lessons,
        }

    # ==================== 内部方法：错误解析 ====================

    def _parse_check_errors(self, result: QualityResult) -> List[Dict[str, Any]]:
        """解析检查输出中的错误"""
        errors: List[Dict[str, Any]] = []

        for line in result.output.splitlines():
            line = line.strip()
            if not line:
                continue
            parsed = self._parse_error_line(line, result.check_name)
            if parsed:
                errors.append(parsed)

        # 无法解析时记录原始输出
        if not errors and not result.passed:
            errors.append(
                {
                    "message": result.output[:200],
                    "check_name": result.check_name,
                }
            )

        return errors

    def _parse_error_line(self, line: str, check_name: str) -> Optional[Dict[str, Any]]:
        """解析单行错误"""
        if check_name == "lint":
            return self._parse_ruff_line(line)
        elif check_name == "typecheck":
            return self._parse_mypy_line(line)
        elif check_name == "test":
            return self._parse_pytest_line(line)
        elif check_name == "coverage":
            return self._parse_coverage_line(line)
        return None

    @staticmethod
    def _parse_ruff_line(line: str) -> Optional[Dict[str, Any]]:
        """解析 ruff: file:line:col: CODE message"""
        m = re.match(r"^(.+?):(\d+):(\d+):\s+([A-Z]\d+)\s+(.+)$", line)
        if m:
            return {
                "file_path": m.group(1),
                "line_number": int(m.group(2)),
                "error_code": m.group(4),
                "message": m.group(5),
            }
        return None

    @staticmethod
    def _parse_mypy_line(line: str) -> Optional[Dict[str, Any]]:
        """解析 mypy: file:line: error: message [code]"""
        m = re.match(r"^(.+?):(\d+):\s+error:\s+(.+?)(?:\s+\[([\w-]+)\])?$", line)
        if m:
            return {
                "file_path": m.group(1),
                "line_number": int(m.group(2)),
                "error_code": m.group(4) or "type-error",
                "message": m.group(3),
            }
        return None

    @staticmethod
    def _parse_pytest_line(line: str) -> Optional[Dict[str, Any]]:
        """解析 pytest 失败行"""
        m = re.match(r"^FAILED\s+(.+?)::(.+?)$", line)
        if m:
            return {
                "file_path": m.group(1),
                "error_code": "FAILED",
                "message": f"Test failed: {m.group(2)}",
            }
        m = re.match(r"^ERROR\s+(.+?)::(.+?)$", line)
        if m:
            return {
                "file_path": m.group(1),
                "error_code": "ERROR",
                "message": f"Test error: {m.group(2)}",
            }
        return None

    @staticmethod
    def _parse_coverage_line(line: str) -> Optional[Dict[str, Any]]:
        """解析覆盖率不足行"""
        if "FAIL" in line and "coverage" in line.lower():
            return {
                "error_code": "coverage_gap",
                "message": line.strip(),
            }
        return None

    # ==================== 内部方法：分类 ====================

    def _classify_severity(self, check_name: str, error_info: Dict) -> IssueSeverity:
        """分类问题严重级别"""
        error_code = error_info.get("error_code", "")

        # 精确匹配
        if error_code in DEFAULT_SEVERITY_MAP:
            return DEFAULT_SEVERITY_MAP[error_code]

        # 按检查类型回退
        if check_name in ("test",) and error_code in ("FAILED", "ERROR"):
            return IssueSeverity.P0
        if check_name == "typecheck":
            return IssueSeverity.P0
        if check_name == "lint":
            return IssueSeverity.P1
        return IssueSeverity.P2

    @staticmethod
    def _classify_issue_type(check_name: str, error_info: Dict) -> IssueType:
        """分类问题类型"""
        type_map = {
            "lint": IssueType.LINT,
            "typecheck": IssueType.TYPE,
            "test": IssueType.TEST,
            "coverage": IssueType.COVERAGE,
            "e2e": IssueType.E2E,
            "integration": IssueType.INTEGRATION,
        }
        return type_map.get(check_name, IssueType.LINT)

    @staticmethod
    def _classify_lesson_type(issue: AuditIssue) -> LessonType:
        """分类学习经验类型"""
        if issue.issue_type in (IssueType.LINT, IssueType.TYPE):
            return LessonType.PITFALL
        if issue.issue_type == IssueType.TEST:
            return LessonType.PATTERN
        return LessonType.BEST_PRACTICE

    @staticmethod
    def _classify_category(issue: AuditIssue) -> str:
        """分类学习经验类别"""
        category_map = {
            IssueType.LINT: "code-style",
            IssueType.TYPE: "type-safety",
            IssueType.TEST: "testing",
            IssueType.COVERAGE: "testing",
            IssueType.E2E: "testing",
            IssueType.INTEGRATION: "testing",
            IssueType.PERF: "performance",
        }
        return category_map.get(issue.issue_type, "general")

    @staticmethod
    def _build_trigger_pattern(issue: AuditIssue) -> str:
        """构建触发模式（用于未来自动匹配）"""
        parts = []
        if issue.check_name:
            parts.append(issue.check_name)
        if issue.error_code:
            parts.append(issue.error_code)
        return ":".join(parts) if parts else ""

    @staticmethod
    def _build_prevention_tip(issue: AuditIssue) -> str:
        """构建预防建议"""
        tips = {
            IssueType.LINT: "启用 ruff 自动格式化，配置 pre-commit 钩子",
            IssueType.TYPE: "添加 type hints 或使用更严格的类型标注",
            IssueType.TEST: "编写更全面的测试用例，覆盖边界条件",
            IssueType.COVERAGE: "增加测试覆盖率，补充缺失的测试场景",
            IssueType.E2E: "完善端到端测试流程，增加异常场景覆盖",
        }
        return tips.get(issue.issue_type, "注意代码质量")

    @staticmethod
    def _build_lesson_title(issue: AuditIssue) -> str:
        """构建学习经验标题"""
        parts = [issue.issue_type.value, issue.severity.value]
        if issue.error_code:
            parts.append(issue.error_code)
        return " - ".join(parts)

    @staticmethod
    def _infer_root_cause(check_name: str, error_info: Dict) -> Optional[str]:
        """推断根因"""
        message = error_info.get("message", "")
        if check_name == "lint":
            return "代码风格/质量问题"
        if check_name == "typecheck":
            return "类型不匹配或类型标注缺失"
        if check_name == "test":
            if "assert" in message.lower():
                return "断言失败：实现逻辑与测试预期不符"
            return "测试失败"
        if check_name == "coverage":
            return "测试覆盖不足"
        return None


# ==================== 行转实体 ====================


def _row_to_issue(row: tuple) -> AuditIssue:
    """数据库行转 AuditIssue"""
    return AuditIssue(
        id=row[0],
        session_id=row[1],
        task_id=row[2],
        issue_type=IssueType(row[3]),
        severity=IssueSeverity(row[4]),
        file_path=row[5],
        line_number=row[6],
        check_name=row[7],
        error_code=row[8],
        error_message=row[9],
        root_cause=row[10],
        status=IssueStatus(row[11]),
        created_at=row[12],
        resolved_at=row[13],
        fix_strategy=row[14],
        fix_commit=row[15],
        occurrence_count=row[16] or 1,
    )


def _row_to_lesson(row: tuple) -> AuditLesson:
    """数据库行转 AuditLesson"""
    return AuditLesson(
        id=row[0],
        issue_id=row[1],
        lesson_type=LessonType(row[2]),
        category=row[3],
        title=row[4],
        description=row[5],
        trigger_pattern=row[6],
        prevention_tip=row[7],
        created_at=row[8],
    )
