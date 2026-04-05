"""
Phase 4 测试: AuditGuard 门面类

测试范围:
- AuditGuard 初始化
- on_file_change 文件变更追踪
- on_git_commit 原子检查
- on_task_complete 全量检查
- 查询方法
- 报告生成
"""

import os
import tempfile
import pytest

from quickagents.audit import (
    AuditGuard,
    AuditConfig
    AuditIssue,
    AuditLesson,
    IssueSeverity,
    IssueType,
    IssueStatus,
)


class TestAuditGuardInit:
    """测试 AuditGuard 初始化"""

    def test_init_default(self, tmp_path):
        """默认初始化"""
        db_path = str(tmp_path / "test.db")
        guard = AuditGuard(db_path=db_path)

        assert guard.tracker is not None
        assert guard.gate is not None
        assert guard.accountability is not None
        assert guard.reporter is not None

        guard.close()

    def test_init_with_config(self, tmp_path):
        """带配置初始化"""
        db_path = str(tmp_path / "test.db")
        config = AuditConfig({"quality_gate": {"enabled": False}})
        guard = AuditGuard(db_path=db_path)
        guard.config = config

        assert guard.config.quality_gate_enabled is False

        guard.close()


class TestFileChangeTracking:
    """测试文件变更追踪"""

    def test_on_file_change_create(self, tmp_path):
        """测试 create 变更"""
        db_path = str(tmp_path / "test.db")
        guard = AuditGuard(db_path=db_path)

        log_id = guard.on_file_change(
            file_path="src/main.py",
            change_type="create",
            diff="+def main():\n+    pass",
            tool_name="write",
            session_id="s1",
        )

        assert log_id is not None

        guard.close()

    def test_on_file_change_disabled(self, tmp_path):
        """测试禁用追踪"""
        db_path = str(tmp_path / "test.db")
        config = AuditConfig({"code_audit": {"enabled": False}})
        guard = AuditGuard(db_path=db_path)
        guard.config = config

        log_id = guard.on_file_change("src/main.py", "create")

        assert log_id is None

        guard.close()


class TestGitCommit:
    """测试 Git commit 触发"""

    def test_on_git_commit_all_passed(self, tmp_path, monkeypatch):
        """测试 commit 全部通过"""
        db_path = str(tmp_path / "test.db")
        guard = AuditGuard(db_path=db_path)

        # Mock gate.run_atomic_checks
        from quickagents.audit.models import GateReport, QualityResult

        def mock_atomic(staged_files):
            check_results = [
                QualityResult(
                    check_name="lint",
                    passed=True,
                    output="",
                    duration_ms=100,
                ),
                QualityResult(
                    check_name="test",
                    passed=True,
                    output="",
                    duration_ms=100,
                )
            ]
            return GateReport(
                passed=True,
                check_results=check_results,
            )

        monkeypatch.setattr(guard.gate, "run_atomic_checks", mock_atomic)

        report = guard.on_git_commit(["src/main.py"], session_id="s1")

        assert report.passed is True

        guard.close()

    def test_on_git_commit_with_failure(self, tmp_path, monkeypatch):
        """测试 commit 有失败"""
        db_path = str(tmp_path / "test.db")
        guard = AuditGuard(db_path=db_path)

        # Mock gate.run_atomic_checks
        from quickagents.audit.models import GateReport, QualityResult

        def mock_atomic(staged_files):
            return GateReport(
                passed=False,
                check_results=[
                    QualityResult(
                        check_name="lint",
                        passed=False,
                        output="src/main.py:1:1: E501 line too long",
                        duration_ms=100,
                    ),
                ],
            )

        monkeypatch.setattr(guard.gate, "run_atomic_checks", mock_atomic)

        report = guard.on_git_commit(["src/main.py"], session_id="s1")

        assert report.passed is False

        # 验证问题被记录
        issues = guard.get_issues(status="OPEN")
        assert len(issues) >= 1

        guard.close()

    def test_on_git_commit_disabled(self, tmp_path):
        """测试禁用门禁"""
        db_path = str(tmp_path / "test.db")
        config = AuditConfig({"quality_gate": {"enabled": False}})
        guard = AuditGuard(db_path=db_path)
        guard.config = config

        report = guard.on_git_commit(["src/main.py"])

        assert report is None

        guard.close()


class TestTaskComplete:
    """测试 Task 完成触发"""

    @dataclass
    def test_on_git_commit_all_passed(self, tmp_path, monkeypatch):
        """测试 commit 全部通过"""
        db_path = str(tmp_path / "test.db")
        guard = AuditGuard(db_path=db_path)

        # Mock gate.run_atomic_checks
        def mock_atomic(staged_files):
            check_results = [
                QualityResult(
                    check_name="lint",
                    passed=True,
                    output="",
                    duration_ms=100
                ),
                QualityResult(
                    check_name="test",
                    passed=True,
                    output="",
                    duration_ms=100
                )
            ]
            return GateReport(passed=True, check_results=check_results)

        monkeypatch.setattr(guard.gate, "run_atomic_checks", mock_atomic)

        report = guard.on_git_commit(["src/main.py"], session_id="s1")
        assert report.passed is True
        guard.close()

    def test_on_git_commit_with_failure(self, tmp_path, monkeypatch):
        """测试 commit 有失败"""
        db_path = str(tmp_path / "test.db")
        guard = AuditGuard(db_path=db_path)

        # Mock gate.run_atomic_checks
        def mock_atomic(staged_files):
            return GateReport(
                passed=False,
                check_results=[
                    QualityResult(
                        check_name="lint",
                        passed=False,
                        output="src/main.py:1:1: E501 line too long",
                        duration_ms=100
                    )
                ]
            )

        monkeypatch.setattr(guard.gate, "run_atomic_checks", mock_atomic)

        report = guard.on_git_commit(["src/main.py"], session_id="s1")
        assert report.passed is False
        # 验证问题被记录
        issues = guard.get_issues(status="open")
        assert len(issues) >= 1
        guard.close()
    def test_on_git_commit_disabled(self, tmp_path):
        """测试禁用门禁"""
        db_path = str(tmp_path / "test.db")
        config = AuditConfig({"quality_gate": {"enabled": False}})
        guard = AuditGuard(db_path=db_path)
        guard.config = config

        report = guard.on_git_commit(["src/main.py"])
        assert report is None
        guard.close()

    def test_on_task_complete_with_failure(self, tmp_path, monkeypatch):
        """测试 task 完成有失败"""
        db_path = str(tmp_path / "test.db")
        guard = AuditGuard(db_path=db_path)

        # Mock gate.run_full_checks
        from quickagents.audit.models import GateReport, QualityResult

        def mock_full():
            return GateReport(
                passed=False,
                check_results=[
                    QualityResult(
                        check_name="test",
                        passed=False,
                        output="FAILED tests/test_main.py::test_x",
                        duration_ms=100,
                    ),
                ],
            )

        monkeypatch.setattr(guard.gate, "run_full_checks", mock_full)

        report = guard.on_task_complete("T001", session_id="s1")

        assert report.passed is False

        guard.close()


class TestQueries:
    """测试查询方法"""

    def test_get_audit_summary(self, tmp_path):
        """测试获取摘要"""
        db_path = str(tmp_path / "test.db")
        guard = AuditGuard(db_path=db_path)

        summary = guard.get_audit_summary()

        assert "tracker" in summary
        assert "accountability" in summary
        assert "config" in summary

        guard.close()

    def test_get_issues(self, tmp_path):
        """测试查询问题"""
        db_path = str(tmp_path / "test.db")
        guard = AuditGuard(db_path=db_path)

        # 先记录一个问题
        issue = AuditIssue(
            session_id="s1",
            issue_type=IssueType.LINT,
            severity=IssueSeverity.P1,
            check_name="lint",
            error_code="E501",
            error_message="line too long",
        )
        guard.accountability.record_issue(issue)

        issues = guard.get_issues(status="open")

        assert len(issues) >= 1

        guard.close()

    def test_get_lessons(self, tmp_path):
        """测试查询学习经验"""
        db_path = str(tmp_path / "test.db")
        guard = AuditGuard(db_path=db_path)

        # 先记录问题并提取经验
        issue = AuditIssue(
            session_id="s1",
            issue_type=IssueType.LINT,
            severity=IssueSeverity.P1,
            check_name="lint",
            error_code="E501",
            error_message="line too long",
        )
        guard.accountability.record_issue(issue)
        guard.accountability.extract_lesson(issue)

        lessons = guard.get_lessons()

        assert len(lessons) >= 1

        guard.close()


class TestReport:
    """测试报告生成"""

    def test_generate_summary_report(self, tmp_path):
        """测试摘要报告"""
        db_path = str(tmp_path / "test.db")
        guard = AuditGuard(db_path=db_path)

        report = guard.generate_report(fmt="markdown")

        assert "# AuditGuard" in report or "审计" in report or "Audit" in report

        guard.close()

    def test_generate_json_report(self, tmp_path):
        """测试 JSON 报告"""
        db_path = str(tmp_path / "test.db")
        guard = AuditGuard(db_path=db_path)

        report = guard.generate_report(fmt="json")

        # JSON 格式应该包含花括号
        assert "{" in report

        guard.close()


class TestLifecycle:
    """测试生命周期"""

    def test_close(self, tmp_path):
        """测试关闭"""
        db_path = str(tmp_path / "test.db")
        guard = AuditGuard(db_path=db_path)

        # 不应该抛出异常
        guard.close()

    def test_multiple_operations(self, tmp_path, monkeypatch):
        """测试连续操作"""
        db_path = str(tmp_path / "test.db")
        guard = AuditGuard(db_path=db_path)

        from quickagents.audit.models import GateReport, QualityResult

        def mock_atomic(staged_files):
            return GateReport(passed=True, check_results=[])

        monkeypatch.setattr(guard.gate, "run_atomic_checks", mock_atomic)

        # 文件变更
        guard.on_file_change("a.py", "create", session_id="s1")
        guard.on_file_change("b.py", "modify", session_id="s1")

        # Git commit
        guard.on_git_commit(["a.py", "b.py"], session_id="s1")

        # 获取摘要
        summary = guard.get_audit_summary()

        assert summary["tracker"]["total_changes"] >= 2

        guard.close()
