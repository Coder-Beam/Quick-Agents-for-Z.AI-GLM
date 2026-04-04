"""
AuditGuard - Phase 2 单元测试 (QualityGate)

测试覆盖:
- QualityGate: 原子检查、全量检查、自定义检查
- 异步执行: submit_quality_check / wait_for_check
- 检测函数: lint/typecheck/test 命令自动检测
- 错误统计: ruff/mypy/pytest 输出解析
- _run_command: 命令执行

所有 subprocess 调用使用 mock
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from quickagents.audit.quality_gate import (
    QualityGate,
    CheckStatus,
    _run_command,
    _count_ruff_errors,
    _count_mypy_errors,
    _count_pytest_errors,
    _detect_lint_command,
    _detect_typecheck_command,
    _detect_test_command,
)
from quickagents.audit.models import GateReport
from quickagents.audit.audit_config import AuditConfig


# ==================== Fixtures ====================


@pytest.fixture
def temp_project(tmp_path):
    """临时项目目录"""
    return tmp_path


@pytest.fixture
def config():
    """默认配置"""
    return AuditConfig()


@pytest.fixture
def gate(temp_project, config):
    """QualityGate 实例"""
    return QualityGate(project_root=str(temp_project), config=config)


# ==================== QualityGate 基础测试 ====================


class TestQualityGateBasic:
    def test_init(self, temp_project):
        gate = QualityGate(project_root=str(temp_project))
        assert gate.project_root == temp_project.resolve()
        assert gate.config is not None

    def test_init_with_config(self, temp_project, config):
        gate = QualityGate(project_root=str(temp_project), config=config)
        assert gate.config is config

    def test_disabled_gate(self, temp_project):
        config = AuditConfig({"quality_gate": {"enabled": False}})
        gate = QualityGate(project_root=str(temp_project), config=config)
        report = gate.run_atomic_checks(["src/main.py"])
        assert report.all_passed is True
        assert len(report.checks) == 0


# ==================== 原子检查测试 ====================


class TestAtomicChecks:
    @patch("quickagents.audit.quality_gate._detect_test_command")
    @patch("quickagents.audit.quality_gate._detect_typecheck_command")
    @patch("quickagents.audit.quality_gate._detect_lint_command")
    @patch("quickagents.audit.quality_gate._run_command")
    def test_all_passed(self, mock_run, mock_lint, mock_type, mock_test, gate):
        mock_lint.return_value = ["ruff", "check", "."]
        mock_type.return_value = ["mypy", "."]
        mock_test.return_value = ["pytest", "-x", "-q"]
        mock_run.side_effect = [
            {"passed": True, "output": "All clear", "duration_ms": 100},
            {"passed": True, "output": "Success", "duration_ms": 200},
            {"passed": True, "output": "5 passed", "duration_ms": 300},
        ]
        report = gate.run_atomic_checks(["src/main.py"])
        assert report.all_passed is True
        assert report.report_type == "atomic"
        assert len(report.checks) == 3

    @patch("quickagents.audit.quality_gate._detect_test_command")
    @patch("quickagents.audit.quality_gate._detect_typecheck_command")
    @patch("quickagents.audit.quality_gate._detect_lint_command")
    @patch("quickagents.audit.quality_gate._run_command")
    def test_lint_failed(self, mock_run, mock_lint, mock_type, mock_test, gate):
        mock_lint.return_value = ["ruff", "check", "."]
        mock_type.return_value = ["mypy", "."]
        mock_test.return_value = ["pytest"]
        mock_run.side_effect = [
            {"passed": False, "output": "src/main.py:1: E501 line too long"},
            {"passed": True, "output": "Success"},
            {"passed": True, "output": "5 passed"},
        ]
        report = gate.run_atomic_checks(["src/main.py"])
        assert report.all_passed is False
        assert not report.checks[0].passed

    @patch("quickagents.audit.quality_gate._detect_test_command")
    @patch("quickagents.audit.quality_gate._detect_typecheck_command")
    @patch("quickagents.audit.quality_gate._detect_lint_command")
    def test_no_tools(self, mock_lint, mock_type, mock_test, gate):
        mock_lint.return_value = None
        mock_type.return_value = None
        mock_test.return_value = None
        report = gate.run_atomic_checks()
        assert report.all_passed is True
        assert all(c.skipped for c in report.checks)


# ==================== 全量检查测试 ====================


class TestFullChecks:
    @patch("quickagents.audit.quality_gate._command_exists")
    @patch("quickagents.audit.quality_gate._detect_test_command")
    @patch("quickagents.audit.quality_gate._detect_typecheck_command")
    @patch("quickagents.audit.quality_gate._detect_lint_command")
    @patch("quickagents.audit.quality_gate._run_command")
    def test_full_passed(self, mock_run, mock_lint, mock_type, mock_test, mock_cmd, gate):
        mock_lint.return_value = ["ruff", "check", "."]
        mock_type.return_value = ["mypy", "."]
        mock_test.return_value = ["pytest"]
        mock_cmd.return_value = True
        mock_run.side_effect = [
            {"passed": True, "output": "All clear", "duration_ms": 100},
            {"passed": True, "output": "Success", "duration_ms": 200},
            {"passed": True, "output": "50 passed", "duration_ms": 500},
            {"passed": True, "output": "TOTAL 95%", "duration_ms": 600},
        ]
        report = gate.run_full_checks()
        assert report.all_passed is True
        assert report.report_type == "full"
        assert len(report.checks) == 4  # lint + type + test + coverage


# ==================== 异步执行测试 ====================


class TestAsyncExecution:
    def test_submit_quality_check(self, gate):
        tid = gate.submit_quality_check("T001", file_paths=["src/main.py"])
        assert tid == "T001"
        status = gate.get_ticket_status("T001")
        assert status in (
            CheckStatus.PENDING.value,
            CheckStatus.RUNNING.value,
            CheckStatus.COMPLETED.value,
        )

    @patch.object(QualityGate, "run_atomic_checks")
    def test_wait_for_check(self, mock_run, gate):
        mock_report = GateReport(all_passed=True, report_type="atomic")
        mock_run.return_value = mock_report

        gate.submit_quality_check("T002", file_paths=["src/main.py"])

        # 模拟后台完成
        with gate._lock:
            gate._pending_tickets["T002"]["status"] = CheckStatus.COMPLETED
            gate._pending_tickets["T002"]["report"] = mock_report

        report = gate.wait_for_check("T002", timeout=1)
        assert report.all_passed is True

    def test_wait_for_check_timeout(self, gate):
        gate.submit_quality_check("T003")
        with pytest.raises(TimeoutError):
            gate.wait_for_check("T003", timeout=0.1)

    def test_wait_for_check_not_found(self, gate):
        with pytest.raises(KeyError):
            gate.wait_for_check("nonexistent", timeout=0.1)

    def test_get_ticket_status_not_found(self, gate):
        assert gate.get_ticket_status("nonexistent") is None


# ==================== 命令检测测试 ====================


class TestCommandDetection:
    @patch("quickagents.audit.quality_gate._command_exists")
    def test_detect_lint_ruff(self, mock):
        mock.return_value = True
        cmd = _detect_lint_command(Path("."))
        assert cmd is not None
        assert cmd[0] == "ruff"

    @patch("quickagents.audit.quality_gate._command_exists")
    def test_detect_lint_flake8(self, mock):
        mock.side_effect = lambda c: c == "flake8"
        cmd = _detect_lint_command(Path("."))
        assert cmd is not None
        assert cmd[0] == "flake8"

    @patch("quickagents.audit.quality_gate._command_exists")
    def test_detect_lint_none(self, mock):
        mock.return_value = False
        assert _detect_lint_command(Path(".")) is None

    @patch("quickagents.audit.quality_gate._command_exists")
    def test_detect_lint_with_files(self, mock):
        mock.return_value = True
        cmd = _detect_lint_command(Path("."), ["src/a.py", "src/b.py"])
        assert "src/a.py" in cmd
        assert "src/b.py" in cmd

    @patch("quickagents.audit.quality_gate._command_exists")
    def test_detect_typecheck_mypy(self, mock):
        mock.return_value = True
        cmd = _detect_typecheck_command(Path("."))
        assert cmd[0] == "mypy"
        assert "--ignore-missing-imports" in cmd

    @patch("quickagents.audit.quality_gate._command_exists")
    def test_detect_test_pytest(self, mock):
        mock.return_value = True
        cmd = _detect_test_command(Path("."))
        assert cmd[0] == "pytest"

    @patch("quickagents.audit.quality_gate._command_exists")
    def test_detect_test_with_files(self, mock):
        mock.return_value = True
        cmd = _detect_test_command(Path("."), ["tests/test_main.py"])
        assert "tests/test_main.py" in cmd

    @patch("quickagents.audit.quality_gate._command_exists")
    def test_detect_test_infer(self, mock, tmp_path):
        mock.return_value = True
        test_file = tmp_path / "tests" / "test_auth.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("# test")
        cmd = _detect_test_command(tmp_path, ["src/auth.py"])
        # 应该推断出测试文件
        found = any("test_auth.py" in str(c) for c in cmd)
        assert found


# ==================== 错误统计测试 ====================


class TestErrorCounting:
    def test_count_ruff_errors(self):
        output = "src/main.py:10:5: E501 line too long\nsrc/main.py:20:1: F401 unused import\nFound 2 errors"
        assert _count_ruff_errors(output) == 2

    def test_count_ruff_empty(self):
        assert _count_ruff_errors("") == 0

    def test_count_mypy_errors(self):
        output = "Found 3 errors in 2 files (checked 10 source files)"
        assert _count_mypy_errors(output) == 3

    def test_count_mypy_zero(self):
        assert _count_mypy_errors("Success: no issues found") == 0

    def test_count_pytest_errors(self):
        output = "5 passed, 2 failed, 1 error in 10s"
        assert _count_pytest_errors(output) == 3

    def test_count_pytest_all_passed(self):
        assert _count_pytest_errors("50 passed in 5s") == 0

    def test_count_pytest_empty(self):
        assert _count_pytest_errors("") == 0


# ==================== _run_command 测试 ====================


class TestRunCommand:
    @patch("subprocess.run")
    def test_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        result = _run_command(["echo", "test"], ".", 10)
        assert result["passed"] is True
        assert "ok" in result["output"]

    @patch("subprocess.run")
    def test_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        result = _run_command(["false"], ".", 10)
        assert result["passed"] is False

    @patch("subprocess.run")
    def test_timeout(self, mock_run):
        import subprocess as sp

        mock_run.side_effect = sp.TimeoutExpired(cmd="test", timeout=10)
        result = _run_command(["sleep", "100"], ".", 10)
        assert result["passed"] is False
        assert "timeout" in result["output"].lower()

    @patch("subprocess.run")
    def test_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError()
        result = _run_command(["nonexistent"], ".", 10)
        assert result["passed"] is True
        assert result["skipped"] is True

    @patch("subprocess.run")
    def test_generic_error(self, mock_run):
        mock_run.side_effect = OSError("permission denied")
        result = _run_command(["test"], ".", 10)
        assert result["passed"] is False
