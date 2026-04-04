"""
AuditGuard - Phase 3 单元测试 (AccountabilityEngine)

测试覆盖:
- analyze_failure(): 错误解析、归因、分级
- record_issue() / resolve_issue(): 问题生命周期
- extract_lesson() / extract_lessons(): 学习经验提取
- check_fix_loop(): 修复循环检测
- generate_feedback(): 自动反馈生成
- 查询方法: get_issues / get_lessons / get_stats
- 错误行解析: ruff/mypy/pytest/coverage
"""

import os
import sys
import pytest
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from quickagents.core.connection_manager import ConnectionManager
from quickagents.core.migration_manager import MigrationManager, Migration
from quickagents.audit.accountability import AccountabilityEngine
from quickagents.audit.models import (
    AuditIssue,
    AuditLesson,
    IssueSeverity,
    IssueType,
    IssueStatus,
    LessonType,
    QualityResult,
    GateReport,
)
from quickagents.audit.audit_config import AuditConfig


# ==================== Fixtures ====================


@pytest.fixture
def temp_db_path():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        yield os.path.join(tmpdir, "test_audit.db")


@pytest.fixture
def connection_manager(temp_db_path):
    mgr = ConnectionManager(temp_db_path, pool_size=3)
    yield mgr
    mgr.close_all()


@pytest.fixture
def setup_db(connection_manager):
    """初始化数据库（执行迁移）"""
    mgr = MigrationManager(connection_manager)
    audit_sql = Path(__file__).parent.parent / "quickagents" / "audit" / "migrations" / "003_audit_tables.sql"
    if audit_sql.exists():
        migration = Migration(
            version="003",
            name="audit_tables",
            up_sql=audit_sql.read_text(encoding="utf-8"),
            down_sql="",
            source="registered",
        )
        mgr.register_migration(migration)
    mgr.migrate()
    return connection_manager


@pytest.fixture
def engine(setup_db):
    return AccountabilityEngine(setup_db)


# ==================== analyze_failure 测试 ====================


class TestAnalyzeFailure:
    """分析失败报告测试"""

    def test_empty_report(self, engine):
        """测试无失败时返回空列表"""
        report = GateReport(
            all_passed=True,
            checks=[
                QualityResult(check_name="lint", passed=True, output="All clear"),
            ],
        )
        issues = engine.analyze_failure(report, session_id="s1")
        assert len(issues) == 0

    def test_lint_failure(self, engine):
        """测试解析 lint 失败"""
        report = GateReport(
            all_passed=False,
            checks=[
                QualityResult(
                    check_name="lint",
                    passed=False,
                    output="src/main.py:10:5: E501 line too long (120 > 100 characters)",
                ),
            ],
        )
        issues = engine.analyze_failure(report, session_id="s1", task_id="T001")
        assert len(issues) == 1
        assert issues[0].file_path == "src/main.py"
        assert issues[0].line_number == 10
        assert issues[0].error_code == "E501"
        assert issues[0].issue_type == IssueType.LINT
        assert issues[0].session_id == "s1"
        assert issues[0].task_id == "T001"

    def test_mypy_failure(self, engine):
        """测试解析 mypy 失败"""
        report = GateReport(
            all_passed=False,
            checks=[
                QualityResult(
                    check_name="typecheck",
                    passed=False,
                    output="src/auth.py:42: error: Incompatible types in assignment [arg-type]",
                ),
            ],
        )
        issues = engine.analyze_failure(report, session_id="s1")
        assert len(issues) == 1
        assert issues[0].file_path == "src/auth.py"
        assert issues[0].error_code == "arg-type"
        assert issues[0].severity == IssueSeverity.P0  # arg-type → P0

    def test_pytest_failure(self, engine):
        """测试解析 pytest 失败"""
        report = GateReport(
            all_passed=False,
            checks=[
                QualityResult(
                    check_name="test",
                    passed=False,
                    output="FAILED tests/test_auth.py::test_login",
                ),
            ],
        )
        issues = engine.analyze_failure(report, session_id="s1")
        assert len(issues) == 1
        assert issues[0].file_path == "tests/test_auth.py"
        assert issues[0].error_code == "FAILED"
        assert issues[0].severity == IssueSeverity.P0

    def test_coverage_failure(self, engine):
        """测试解析覆盖率不足"""
        report = GateReport(
            all_passed=False,
            checks=[
                QualityResult(
                    check_name="coverage",
                    passed=False,
                    output="FAIL Required test coverage of 80% not reached. Total coverage: 65%",
                ),
            ],
        )
        issues = engine.analyze_failure(report, session_id="s1")
        assert len(issues) >= 1

    def test_multiple_checks(self, engine):
        """测试多个检查失败"""
        report = GateReport(
            all_passed=False,
            checks=[
                QualityResult(check_name="lint", passed=False, output="a.py:1:1: E501 msg"),
                QualityResult(check_name="typecheck", passed=False, output="b.py:5: error: bad type [type-error]"),
            ],
        )
        issues = engine.analyze_failure(report, session_id="s1")
        assert len(issues) == 2
        assert issues[0].issue_type == IssueType.LINT
        assert issues[1].issue_type == IssueType.TYPE

    def test_severity_classification(self, engine):
        """测试严重级别分类"""
        # P0: type error
        report = GateReport(
            all_passed=False,
            checks=[
                QualityResult(check_name="typecheck", passed=False, output="a.py:1: error: bad [type-error]"),
            ],
        )
        issues = engine.analyze_failure(report)
        assert issues[0].severity == IssueSeverity.P0

        # P1: F401 unused import
        report = GateReport(
            all_passed=False,
            checks=[
                QualityResult(check_name="lint", passed=False, output="a.py:1:1: F401 unused import"),
            ],
        )
        issues = engine.analyze_failure(report)
        assert issues[0].severity == IssueSeverity.P1

        # P2: E501 line too long
        report = GateReport(
            all_passed=False,
            checks=[
                QualityResult(check_name="lint", passed=False, output="a.py:1:1: E501 too long"),
            ],
        )
        issues = engine.analyze_failure(report)
        assert issues[0].severity == IssueSeverity.P2

    def test_root_cause_inference(self, engine):
        """测试根因推断"""
        report = GateReport(
            all_passed=False,
            checks=[
                QualityResult(check_name="lint", passed=False, output="a.py:1:1: E501 msg"),
            ],
        )
        issues = engine.analyze_failure(report)
        assert issues[0].root_cause is not None


# ==================== record_issue / resolve_issue 测试 ====================


class TestIssueLifecycle:
    """问题生命周期测试"""

    def test_record_issue(self, engine):
        issue = AuditIssue(
            session_id="s1",
            task_id="T001",
            issue_type=IssueType.LINT,
            severity=IssueSeverity.P1,
            file_path="src/main.py",
            error_message="E501 line too long",
            check_name="ruff",
            error_code="E501",
        )
        result = engine.record_issue(issue)
        assert result.id == issue.id

    def test_resolve_issue(self, engine):
        issue = AuditIssue(
            session_id="s1",
            issue_type=IssueType.LINT,
            severity=IssueSeverity.P1,
            error_message="test issue",
            check_name="ruff",
        )
        engine.record_issue(issue)
        ok = engine.resolve_issue(issue.id, fix_strategy="auto-fix", fix_commit="abc123")
        assert ok is True

        issues = engine.get_issues(status="RESOLVED")
        assert len(issues) == 1
        assert issues[0].fix_strategy == "auto-fix"
        assert issues[0].fix_commit == "abc123"

    def test_resolve_nonexistent(self, engine):
        ok = engine.resolve_issue("nonexistent")
        assert ok is False


# ==================== 学习经验测试 ====================


class TestLessonExtraction:
    """学习经验提取测试"""

    def test_extract_lesson(self, engine):
        issue = AuditIssue(
            issue_type=IssueType.LINT,
            severity=IssueSeverity.P1,
            error_message="F401 unused import",
            check_name="ruff",
            error_code="F401",
        )
        engine.record_issue(issue)
        lesson = engine.extract_lesson(issue)
        assert lesson is not None
        assert lesson.issue_id == issue.id
        assert lesson.lesson_type == LessonType.PITFALL
        assert lesson.category == "code-style"
        assert lesson.trigger_pattern == "ruff:F401"
        assert lesson.prevention_tip

    def test_extract_lesson_disabled(self, engine):
        config = AuditConfig({"accountability": {"lesson_extraction": False}})
        engine.config = config
        issue = AuditIssue(
            issue_type=IssueType.LINT,
            error_message="test",
            check_name="ruff",
        )
        lesson = engine.extract_lesson(issue)
        assert lesson is None

    def test_extract_lessons_batch(self, engine):
        issues = [
            AuditIssue(issue_type=IssueType.LINT, error_message="e1", check_name="ruff", error_code="E501"),
            AuditIssue(issue_type=IssueType.TYPE, error_message="e2", check_name="mypy", error_code="type-error"),
        ]
        for i in issues:
            engine.record_issue(i)
        lessons = engine.extract_lessons(issues)
        assert len(lessons) == 2

    def test_lesson_category_mapping(self, engine):
        """测试类别映射"""
        pairs = [
            (IssueType.LINT, "code-style"),
            (IssueType.TYPE, "type-safety"),
            (IssueType.TEST, "testing"),
            (IssueType.COVERAGE, "testing"),
        ]
        for issue_type, expected_cat in pairs:
            issue = AuditIssue(issue_type=issue_type, error_message="x", check_name="test")
            engine.record_issue(issue)
            lesson = engine.extract_lesson(issue)
            assert lesson.category == expected_cat


# ==================== 修复循环检测 ====================


class TestFixLoop:
    """修复循环检测测试"""

    def test_no_loop(self, engine):
        issue = AuditIssue(
            issue_type=IssueType.LINT,
            error_message="E501",
            check_name="ruff",
            error_code="E501",
        )
        result = engine.check_fix_loop(issue)
        assert result["loop_detected"] is False

    def test_loop_escalate(self, engine):
        """第二次出现：升级"""
        for _ in range(2):
            issue = AuditIssue(
                issue_type=IssueType.LINT,
                error_message="E501",
                check_name="ruff",
                error_code="E501",
            )
            engine.record_issue(issue)

        result = engine.check_fix_loop(issue)
        assert result["loop_detected"] is True
        assert result["action"] == "escalate"

    def test_loop_block(self, engine):
        """第三次出现：阻塞"""
        for _ in range(3):
            issue = AuditIssue(
                issue_type=IssueType.LINT,
                error_message="E501",
                check_name="ruff",
                error_code="E501",
            )
            engine.record_issue(issue)

        result = engine.check_fix_loop(issue)
        assert result["loop_detected"] is True
        assert result["action"] == "block"
        assert result["occurrence_count"] >= 3


# ==================== 自动反馈测试 ====================


class TestFeedback:
    """自动反馈测试"""

    def test_generate_feedback(self, engine):
        issues = [
            AuditIssue(
                severity=IssueSeverity.P0,
                issue_type=IssueType.TEST,
                error_message="FAILED test_login",
                file_path="tests/test_auth.py",
                check_name="pytest",
                root_cause="断言失败",
            ),
            AuditIssue(
                severity=IssueSeverity.P1,
                issue_type=IssueType.LINT,
                error_message="F401 unused import",
                file_path="src/main.py",
                check_name="ruff",
                root_cause="代码风格问题",
            ),
        ]
        feedback = engine.generate_feedback(issues)
        assert "[AuditGuard]" in feedback
        assert "P0" in feedback
        assert "P1" in feedback
        assert "test_auth.py" in feedback
        assert "建议" in feedback

    def test_generate_feedback_empty(self, engine):
        feedback = engine.generate_feedback([])
        assert feedback == ""


# ==================== 查询测试 ====================


class TestQueries:
    """查询方法测试"""

    def test_get_issues_by_status(self, engine):
        engine.record_issue(
            AuditIssue(
                session_id="s1",
                issue_type=IssueType.LINT,
                error_message="e1",
                check_name="ruff",
            )
        )
        engine.record_issue(
            AuditIssue(
                session_id="s1",
                issue_type=IssueType.TYPE,
                error_message="e2",
                check_name="mypy",
            )
        )

        open_issues = engine.get_issues(status="OPEN")
        assert len(open_issues) == 2

    def test_get_issues_by_session(self, engine):
        engine.record_issue(
            AuditIssue(
                session_id="s1",
                issue_type=IssueType.LINT,
                error_message="e1",
                check_name="ruff",
            )
        )
        engine.record_issue(
            AuditIssue(
                session_id="s2",
                issue_type=IssueType.LINT,
                error_message="e2",
                check_name="ruff",
            )
        )

        issues = engine.get_issues(session_id="s1")
        assert len(issues) == 1

    def test_get_lessons(self, engine):
        issue = AuditIssue(
            issue_type=IssueType.LINT,
            error_message="e",
            check_name="ruff",
            error_code="E501",
        )
        engine.record_issue(issue)
        engine.extract_lesson(issue)

        lessons = engine.get_lessons()
        assert len(lessons) >= 1

    def test_get_lessons_by_category(self, engine):
        issue = AuditIssue(
            issue_type=IssueType.LINT,
            error_message="e",
            check_name="ruff",
            error_code="E501",
        )
        engine.record_issue(issue)
        engine.extract_lesson(issue)

        lessons = engine.get_lessons(category="code-style")
        assert len(lessons) >= 1

    def test_get_stats(self, engine):
        engine.record_issue(
            AuditIssue(
                issue_type=IssueType.LINT,
                error_message="e1",
                check_name="ruff",
            )
        )

        issue2 = AuditIssue(
            issue_type=IssueType.LINT,
            error_message="e2",
            check_name="ruff",
        )
        engine.record_issue(issue2)
        engine.resolve_issue(issue2.id)

        stats = engine.get_stats()
        assert stats["total_issues"] == 2
        assert stats["total_lessons"] == 0
