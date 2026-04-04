"""
QualityGate - 质量门禁

核心功能:
- run_atomic_checks(): 原子级检查（commit 触发，仅变更文件）
- run_full_checks(): 全量检查（task 完成触发）
- submit_quality_check(): 非阻塞提交检查
- wait_for_check(): 阻塞等待检查完成

设计原则:
- 分层检查: 原子级(commit) vs 全量级(task完成)
- 异步执行: 不阻塞主流程
- 可配置: 通过 AuditConfig 自定义检查命令
- 可复用: 提取检查逻辑为独立函数（Q23 决策 B）
"""

import logging
import re
import subprocess
import os
import time
import threading
from pathlib import Path
from typing import Optional, List, Dict, Callable
from enum import Enum

from .models import QualityResult, GateReport
from .audit_config import AuditConfig

logger = logging.getLogger(__name__)


class CheckStatus(str, Enum):
    """检查状态"""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class QualityGate:
    """
    质量门禁

    使用方式:
        gate = QualityGate(project_root='.', config=config)

        # 原子检查（commit 触发）
        report = gate.run_atomic_checks(['src/auth.py'])

        # 全量检查（task 完成触发）
        report = gate.run_full_checks()

        if not report.all_passed:
            for check in report.failed_checks:
                print(f"[FAIL] {check.check_name}: {check.error_count} errors")
    """

    def __init__(
        self,
        project_root: str = ".",
        config: Optional[AuditConfig] = None,
    ):
        self.project_root = Path(project_root).resolve()
        self.config = config or AuditConfig()

        self.is_python = (
            (self.project_root / "pyproject.toml").exists()
            or (self.project_root / "setup.py").exists()
            or (self.project_root / "setup.cfg").exists()
        )
        self.is_node = (self.project_root / "package.json").exists()

        # 异步执行
        self._pending_tickets: Dict[str, Dict] = {}
        self._lock = threading.Lock()

    # ==================== 原子级检查 ====================

    def run_atomic_checks(self, file_paths: Optional[List[str]] = None) -> GateReport:
        """原子级质量检查（commit 触发，仅变更文件）"""
        if not self.config.quality_gate_enabled:
            return GateReport(all_passed=True, report_type="atomic")

        start = time.time()
        checks: List[QualityResult] = []
        all_passed = True

        for runner in (self._run_lint, self._run_typecheck, self._run_tests):
            result = runner(file_paths)
            checks.append(result)
            if not result.passed and not result.skipped:
                all_passed = False

        duration = (time.time() - start) * 1000
        return GateReport(
            all_passed=all_passed,
            checks=checks,
            duration_ms=round(duration, 2),
            report_type="atomic",
        )

    # ==================== 全量检查 ====================

    def run_full_checks(self) -> GateReport:
        """全量质量检查（task 完成触发）"""
        if not self.config.quality_gate_enabled:
            return GateReport(all_passed=True, report_type="full")

        start = time.time()
        checks: List[QualityResult] = []
        all_passed = True

        # 1-3: lint + typecheck + test（全量，file_paths=None）
        for runner in (self._run_lint, self._run_typecheck, self._run_tests):
            result = runner(None)
            checks.append(result)
            if not result.passed and not result.skipped:
                all_passed = False

        # 4: coverage
        coverage = self._run_coverage()
        checks.append(coverage)
        if not coverage.passed and not coverage.skipped:
            all_passed = False

        # 5-6: 自定义检查（e2e / integration）
        for name, cmd_str in [
            ("e2e", self.config.e2e_command),
            ("integration", self.config.integration_command),
        ]:
            if cmd_str:
                import shlex

                result = self._run_external(name, shlex.split(cmd_str))
                checks.append(result)
                if not result.passed and not result.skipped:
                    all_passed = False

        duration = (time.time() - start) * 1000
        return GateReport(
            all_passed=all_passed,
            checks=checks,
            duration_ms=round(duration, 2),
            report_type="full",
        )

    # ==================== 异步检查（Ticket 机制）====================

    def submit_quality_check(
        self,
        ticket_id: str,
        check_type: str = "atomic",
        file_paths: Optional[List[str]] = None,
        on_complete: Optional[Callable[[GateReport], None]] = None,
    ) -> str:
        """非阻塞提交质量检查，返回 ticket_id"""
        with self._lock:
            self._pending_tickets[ticket_id] = {
                "status": CheckStatus.PENDING,
                "report": None,
                "started_at": time.time(),
            }

        def _run():
            with self._lock:
                self._pending_tickets[ticket_id]["status"] = CheckStatus.RUNNING
            try:
                report = self.run_atomic_checks(file_paths) if check_type == "atomic" else self.run_full_checks()
                with self._lock:
                    self._pending_tickets[ticket_id]["status"] = CheckStatus.COMPLETED
                    self._pending_tickets[ticket_id]["report"] = report
                if on_complete:
                    on_complete(report)
            except Exception as e:
                logger.error(f"Quality check failed for ticket {ticket_id}: {e}")
                with self._lock:
                    self._pending_tickets[ticket_id]["status"] = CheckStatus.FAILED
                    self._pending_tickets[ticket_id]["error"] = str(e)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return ticket_id

    def wait_for_check(self, ticket_id: str, timeout: Optional[float] = None) -> GateReport:
        """阻塞等待检查完成"""
        max_wait = timeout or self.config.full_timeout
        start = time.time()

        while True:
            with self._lock:
                ticket = self._pending_tickets.get(ticket_id)
                if ticket is None:
                    raise KeyError(f"Ticket not found: {ticket_id}")
                if ticket["status"] in (CheckStatus.COMPLETED, CheckStatus.FAILED):
                    report = ticket["report"]
                    if report is None:
                        report = GateReport(all_passed=False, report_type="error")
                    return report
            if time.time() - start > max_wait:
                raise TimeoutError(f"Quality check timed out after {max_wait}s for ticket {ticket_id}")
            time.sleep(0.1)

    def get_ticket_status(self, ticket_id: str) -> Optional[str]:
        """获取 Ticket 状态字符串"""
        with self._lock:
            ticket = self._pending_tickets.get(ticket_id)
            if ticket is None:
                return None
            status = ticket["status"]
            return status.value if isinstance(status, CheckStatus) else str(status)

    # ==================== 内部检查方法 ====================

    def _run_lint(self, file_paths: Optional[List[str]] = None) -> QualityResult:
        cmd = _detect_lint_command(self.project_root, file_paths)
        if cmd is None:
            return QualityResult(
                check_name="lint",
                passed=True,
                output="No lint tool available",
                skipped=True,
            )
        timeout = self.config.atomic_timeout if file_paths else self.config.full_timeout
        start = time.time()
        result = _run_command(cmd, str(self.project_root), timeout)
        duration = (time.time() - start) * 1000
        return QualityResult(
            check_name="lint",
            passed=result["passed"],
            output=result["output"],
            duration_ms=round(duration, 2),
            file_paths=file_paths or [],
            error_count=_count_ruff_errors(result["output"]) if not result["passed"] else 0,
        )

    def _run_typecheck(self, file_paths: Optional[List[str]] = None) -> QualityResult:
        cmd = _detect_typecheck_command(self.project_root, file_paths)
        if cmd is None:
            return QualityResult(
                check_name="typecheck",
                passed=True,
                output="No type checker available",
                skipped=True,
            )
        timeout = self.config.atomic_timeout if file_paths else self.config.full_timeout
        start = time.time()
        result = _run_command(cmd, str(self.project_root), timeout)
        duration = (time.time() - start) * 1000
        return QualityResult(
            check_name="typecheck",
            passed=result["passed"],
            output=result["output"],
            duration_ms=round(duration, 2),
            file_paths=file_paths or [],
            error_count=_count_mypy_errors(result["output"]) if not result["passed"] else 0,
        )

    def _run_tests(self, file_paths: Optional[List[str]] = None) -> QualityResult:
        cmd = _detect_test_command(self.project_root, file_paths)
        if cmd is None:
            return QualityResult(
                check_name="test",
                passed=True,
                output="No test runner available",
                skipped=True,
            )
        timeout = self.config.full_timeout if file_paths is None else self.config.atomic_timeout
        start = time.time()
        result = _run_command(cmd, str(self.project_root), timeout)
        duration = (time.time() - start) * 1000
        return QualityResult(
            check_name="test",
            passed=result["passed"],
            output=result["output"],
            duration_ms=round(duration, 2),
            file_paths=file_paths or [],
            error_count=_count_pytest_errors(result["output"]) if not result["passed"] else 0,
        )

    def _run_coverage(self) -> QualityResult:
        if not _command_exists("pytest"):
            return QualityResult(
                check_name="coverage",
                passed=True,
                output="pytest not available",
                skipped=True,
            )
        cmd = [
            "pytest",
            "--cov=.",
            f"--cov-fail-under={self.config.coverage_threshold}",
            "--cov-report=term-missing",
            "-q",
        ]
        start = time.time()
        result = _run_command(cmd, str(self.project_root), self.config.full_timeout)
        duration = (time.time() - start) * 1000
        return QualityResult(
            check_name="coverage",
            passed=result["passed"],
            output=result["output"],
            duration_ms=round(duration, 2),
            error_count=0 if result["passed"] else 1,
        )

    def _run_external(self, name: str, cmd: List[str]) -> QualityResult:
        """运行外部命令（e2e/integration）"""
        start = time.time()
        result = _run_command(cmd, str(self.project_root), self.config.full_timeout)
        duration = (time.time() - start) * 1000
        return QualityResult(
            check_name=name,
            passed=result["passed"],
            output=result["output"],
            duration_ms=round(duration, 2),
        )


# ==================== 独立函数（可复用，Q23 决策 B）====================


def _run_command(cmd: List[str], cwd: str, timeout: int) -> Dict:
    """执行命令并返回标准化结果"""
    start = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout)
        duration = (time.time() - start) * 1000
        return {
            "passed": proc.returncode == 0,
            "output": proc.stdout + proc.stderr,
            "duration_ms": round(duration, 2),
        }
    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "output": f"Command timeout after {timeout}s",
            "duration_ms": round((time.time() - start) * 1000, 2),
        }
    except FileNotFoundError:
        return {
            "passed": True,
            "output": f"Command not found: {cmd[0]}",
            "skipped": True,
            "duration_ms": 0,
        }
    except Exception as e:
        return {
            "passed": False,
            "output": f"Command failed: {e}",
            "duration_ms": round((time.time() - start) * 1000, 2),
        }


def _detect_lint_command(project_root: Path, file_paths: Optional[List[str]] = None) -> Optional[List[str]]:
    """检测 lint 命令（ruff > flake8）"""
    for tool in ("ruff", "flake8"):
        if _command_exists(tool):
            cmd = [tool, "check"] if tool == "ruff" else [tool]
            if file_paths:
                py_files = [f for f in file_paths if f.endswith(".py")]
                cmd.extend(py_files if py_files else ["."])
            else:
                cmd.append(".")
            return cmd
    return None


def _detect_typecheck_command(project_root: Path, file_paths: Optional[List[str]] = None) -> Optional[List[str]]:
    """检测类型检查命令（mypy）"""
    if _command_exists("mypy"):
        cmd = ["mypy", "--ignore-missing-imports"]
        if file_paths:
            py_files = [f for f in file_paths if f.endswith(".py")]
            cmd.extend(py_files if py_files else ["."])
        else:
            cmd.append(".")
        return cmd
    return None


def _detect_test_command(project_root: Path, file_paths: Optional[List[str]] = None) -> Optional[List[str]]:
    """检测测试命令（pytest），自动推断测试文件"""
    if _command_exists("pytest"):
        cmd = ["pytest", "-x", "-q"]
        if file_paths:
            test_files: List[str] = []
            for f in file_paths:
                if f.startswith("tests") or "test_" in f:
                    test_files.append(f)
                else:
                    parts = Path(f)
                    test_name = f"test_{parts.stem}{parts.suffix}"
                    test_path = str(Path("tests") / test_name)
                    if (project_root / test_path).exists():
                        test_files.append(test_path)
            if test_files:
                cmd.extend(test_files)
        return cmd
    return None


def _command_exists(cmd: str) -> bool:
    """检查系统命令是否可用"""
    try:
        check_cmd = ["where", cmd] if os.name == "nt" else ["which", cmd]
        result = subprocess.run(check_cmd, capture_output=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def _count_ruff_errors(output: str) -> int:
    """统计 ruff 错误数量"""
    count = 0
    for line in output.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("Found") and ":" in stripped:
            count += 1
    return count


def _count_mypy_errors(output: str) -> int:
    """统计 mypy 错误数量"""
    for line in reversed(output.splitlines()):
        line = line.strip()
        if line.startswith("Found ") and " error" in line:
            try:
                return int(line.split()[1])
            except (IndexError, ValueError):
                pass
    return sum(1 for line in output.splitlines() if ": error:" in line)


def _count_pytest_errors(output: str) -> int:
    """统计 pytest 失败+错误数量"""
    total = 0
    for line in output.splitlines():
        m = re.search(r"(\d+)\s+failed", line)
        if m:
            total += int(m.group(1))
        m = re.search(r"(\d+)\s+error", line)
        if m:
            total += int(m.group(1))
    return total
