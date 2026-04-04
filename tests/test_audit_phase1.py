"""
AuditGuard - Phase 1 单元测试

测试覆盖:
- Models: AuditLog, AuditIssue, AuditLesson, QualityResult, GateReport
- AuditConfig: 配置加载、验证、默认值
- CodeAuditTracker: 变更记录、查询、摘要
- AuditReporter: 报告生成（Markdown/JSON）

目标: >= 80% 代码覆盖率
"""

import os
import sys
import json
import pytest
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from quickagents.core.connection_manager import ConnectionManager
from quickagents.core.migration_manager import MigrationManager, Migration
from quickagents.audit.models import (
    AuditLog,
    AuditIssue,
    AuditLesson,
    QualityResult,
    GateReport,
    ChangeType,
    IssueSeverity,
    IssueType,
    IssueStatus,
    LessonType,
    QualityStatus,
)
from quickagents.audit.audit_config import AuditConfig, _deep_merge
from quickagents.audit.code_audit import CodeAuditTracker
from quickagents.audit.audit_reporter import AuditReporter


# ==================== Fixtures ====================


@pytest.fixture
def temp_db_path():
    """临时数据库路径"""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        yield os.path.join(tmpdir, "test_audit.db")


@pytest.fixture
def connection_manager(temp_db_path):
    """连接管理器"""
    mgr = ConnectionManager(temp_db_path, pool_size=3)
    yield mgr
    mgr.close_all()


@pytest.fixture
def migration_manager(connection_manager):
    """迁移管理器（含 audit 迁移注册）"""
    mgr = MigrationManager(connection_manager)

    # 注册 audit 迁移
    audit_sql = Path(__file__).parent.parent / "quickagents" / "audit" / "migrations" / "003_audit_tables.sql"
    audit_rollback = (
        Path(__file__).parent.parent / "quickagents" / "audit" / "migrations" / "003_audit_tables_rollback.sql"
    )

    if audit_sql.exists():
        migration = Migration(
            version="003",
            name="audit_tables",
            up_sql=audit_sql.read_text(encoding="utf-8"),
            down_sql=(audit_rollback.read_text(encoding="utf-8") if audit_rollback.exists() else ""),
            source="registered",
        )
        mgr.register_migration(migration)

    return mgr


@pytest.fixture
def setup_db(migration_manager, connection_manager):
    """初始化数据库（执行迁移）"""
    migration_manager.migrate()
    return connection_manager


@pytest.fixture
def tracker(setup_db):
    """CodeAuditTracker 实例"""
    return CodeAuditTracker(setup_db)


@pytest.fixture
def reporter(tracker):
    """AuditReporter 实例"""
    return AuditReporter(tracker)


# ==================== Models 测试 ====================


class TestModels:
    """数据模型测试"""

    def test_audit_log_defaults(self):
        """测试 AuditLog 默认值"""
        log = AuditLog()
        assert log.id  # 自动生成 ID
        assert log.change_type == ChangeType.MODIFY
        assert log.quality_status == QualityStatus.PENDING
        assert log.lines_added == 0
        assert log.lines_removed == 0
        assert log.created_at > 0

    def test_audit_log_custom(self):
        """测试 AuditLog 自定义值"""
        log = AuditLog(
            session_id="sess-001",
            task_id="T001",
            file_path="src/main.py",
            change_type=ChangeType.CREATE,
            diff_content="+++ new file",
            lines_added=10,
            lines_removed=0,
            tool_name="write",
        )
        assert log.session_id == "sess-001"
        assert log.change_type == ChangeType.CREATE
        assert log.lines_added == 10

    def test_audit_issue_defaults(self):
        """测试 AuditIssue 默认值"""
        issue = AuditIssue(error_message="test error")
        assert issue.severity == IssueSeverity.P2
        assert issue.status == IssueStatus.OPEN
        assert issue.occurrence_count == 1

    def test_audit_lesson_defaults(self):
        """测试 AuditLesson 默认值"""
        lesson = AuditLesson(title="test", description="desc")
        assert lesson.lesson_type == LessonType.PITFALL
        assert lesson.id

    def test_quality_result(self):
        """测试 QualityResult"""
        result = QualityResult(
            check_name="ruff",
            passed=False,
            output="E501 line too long",
            duration_ms=150.5,
            error_count=3,
        )
        assert result.check_name == "ruff"
        assert not result.passed
        assert result.error_count == 3

    def test_gate_report(self):
        """测试 GateReport"""
        checks = [
            QualityResult(check_name="ruff", passed=True),
            QualityResult(check_name="mypy", passed=False, error_count=2),
            QualityResult(check_name="pytest", passed=True, skipped=True),
        ]
        report = GateReport(all_passed=False, checks=checks, report_type="atomic")
        assert not report.all_passed
        assert len(report.failed_checks) == 1
        assert report.failed_checks[0].check_name == "mypy"
        assert report.total_errors == 2

    def test_enums_values(self):
        """测试枚举值"""
        assert ChangeType.CREATE.value == "CREATE"
        assert IssueSeverity.P0.value == "P0"
        assert IssueType.LINT.value == "lint"
        assert IssueStatus.OPEN.value == "OPEN"
        assert LessonType.PITFALL.value == "pitfall"
        assert QualityStatus.PASSED.value == "PASSED"


# ==================== AuditConfig 测试 ====================


class TestAuditConfig:
    """配置管理测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = AuditConfig()
        assert config.code_audit_enabled is True
        assert config.quality_gate_enabled is True
        assert config.accountability_enabled is True
        assert config.max_diff_lines == 500
        assert config.coverage_threshold == 80
        assert config.severity_threshold == "P2"
        assert config.report_format == "markdown"

    def test_from_file_not_exists(self):
        """测试从不存在的文件加载"""
        config = AuditConfig.from_file("/nonexistent/path.json")
        assert config.code_audit_enabled is True  # 回退到默认值

    def test_from_file_valid(self):
        """测试从有效文件加载"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "code_audit": {"enabled": False},
                        "accountability": {"severity_threshold": "P1"},
                    },
                    f,
                )
            config = AuditConfig.from_file(path)
            assert config.code_audit_enabled is False
            assert config.severity_threshold == "P1"
            # 其他值使用默认
            assert config.quality_gate_enabled is True

    def test_from_file_invalid_json(self):
        """测试从无效 JSON 文件加载"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.json")
            with open(path, "w", encoding="utf-8") as f:
                f.write("not valid json {{{")
            config = AuditConfig.from_file(path)
            assert config.code_audit_enabled is True  # 回退到默认值

    def test_custom_config(self):
        """测试自定义配置合并"""
        config = AuditConfig({"code_audit": {"enabled": False}})
        assert config.code_audit_enabled is False
        assert config.max_diff_lines == 500  # 默认值保留

    def test_to_dict(self):
        """测试导出为字典"""
        config = AuditConfig()
        d = config.to_dict()
        assert d["version"] == "1.0.0"
        assert "code_audit" in d
        assert "quality_gate" in d

    def test_save_and_load(self):
        """测试保存和重新加载"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "audit_config.json")
            config = AuditConfig({"accountability": {"severity_threshold": "P0"}})
            config.save(path)

            # 验证文件存在
            assert os.path.exists(path)

            # 重新加载
            loaded = AuditConfig.from_file(path)
            assert loaded.severity_threshold == "P0"

    def test_repr(self):
        """测试 repr"""
        config = AuditConfig()
        r = repr(config)
        assert "AuditConfig" in r
        assert "on" in r

    def test_deep_merge(self):
        """测试深度合并"""
        base = {"a": {"b": 1, "c": 2}, "d": 3}
        override = {"a": {"b": 10}, "e": 5}
        result = _deep_merge(base, override)
        assert result["a"]["b"] == 10  # 覆盖
        assert result["a"]["c"] == 2  # 保留
        assert result["d"] == 3  # 保留
        assert result["e"] == 5  # 新增

    def test_validate_runtime(self):
        """测试运行时验证"""
        config = AuditConfig()
        config.quality_gate_enabled  # noqa - 触发属性访问
        warnings = config.validate_runtime()
        # warnings 列表可能为空（如果工具存在）或有内容（如果不存在）
        assert isinstance(warnings, list)


# ==================== CodeAuditTracker 测试 ====================


class TestCodeAuditTracker:
    """变更追踪测试"""

    def test_record_change(self, tracker):
        """测试记录文件变更"""
        log = tracker.record_change(
            file_path="src/main.py",
            change_type="CREATE",
            diff="+++ new file\n+line1\n+line2\n",
            tool_name="write",
            session_id="sess-001",
            task_id="T001",
        )
        assert log.id
        assert log.file_path == "src/main.py"
        assert log.change_type == ChangeType.CREATE
        assert log.lines_added == 2
        assert log.session_id == "sess-001"

    def test_record_change_modify(self, tracker):
        """测试记录文件修改"""
        log = tracker.record_change(
            file_path="src/auth.py",
            change_type="MODIFY",
            diff="--- a/src/auth.py\n+++ b/src/auth.py\n-old\n+new\n",
            tool_name="edit",
            session_id="sess-001",
        )
        assert log.lines_added == 1
        assert log.lines_removed == 1

    def test_record_change_delete(self, tracker):
        """测试记录文件删除"""
        log = tracker.record_change(
            file_path="src/old.py",
            change_type="DELETE",
            tool_name="write",
            session_id="sess-001",
        )
        assert log.change_type == ChangeType.DELETE

    def test_record_change_with_diff_create(self, tracker):
        """测试通过内容对比记录新建"""
        log = tracker.record_change_with_diff(
            file_path="src/new.py",
            old_content="",
            new_content="line1\nline2\nline3\n",
            tool_name="write",
            session_id="sess-001",
        )
        assert log.change_type == ChangeType.CREATE
        assert log.lines_added == 3

    def test_record_change_with_diff_modify(self, tracker):
        """测试通过内容对比记录修改"""
        log = tracker.record_change_with_diff(
            file_path="src/existing.py",
            old_content="old line\n",
            new_content="new line\n",
            tool_name="edit",
            session_id="sess-001",
        )
        assert log.change_type == ChangeType.MODIFY
        assert log.lines_added == 1
        assert log.lines_removed == 1

    def test_record_change_with_diff_delete(self, tracker):
        """测试通过内容对比记录删除"""
        log = tracker.record_change_with_diff(
            file_path="src/deleted.py",
            old_content="content\n",
            new_content="",
            tool_name="write",
            session_id="sess-001",
        )
        assert log.change_type == ChangeType.DELETE

    def test_update_quality_status(self, tracker):
        """测试更新质量状态"""
        log = tracker.record_change(
            file_path="src/main.py",
            change_type="MODIFY",
            session_id="sess-001",
        )
        assert log.quality_status == QualityStatus.PENDING

        result = tracker.update_quality_status(log.id, "PASSED")
        assert result is True

        changes = tracker.get_changes(session_id="sess-001")
        assert changes[0].quality_status == QualityStatus.PASSED

    def test_update_quality_status_not_found(self, tracker):
        """测试更新不存在记录的状态"""
        result = tracker.update_quality_status("nonexistent", "PASSED")
        assert result is False

    def test_get_changes_by_session(self, tracker):
        """测试按会话查询变更"""
        tracker.record_change("a.py", "CREATE", session_id="sess-001")
        tracker.record_change("b.py", "CREATE", session_id="sess-001")
        tracker.record_change("c.py", "CREATE", session_id="sess-002")

        changes = tracker.get_changes(session_id="sess-001")
        assert len(changes) == 2

    def test_get_changes_by_task(self, tracker):
        """测试按任务查询变更"""
        tracker.record_change("a.py", "CREATE", session_id="s1", task_id="T001")
        tracker.record_change("b.py", "CREATE", session_id="s1", task_id="T002")

        changes = tracker.get_changes(task_id="T001")
        assert len(changes) == 1
        assert changes[0].file_path == "a.py"

    def test_get_changes_by_file(self, tracker):
        """测试按文件查询变更"""
        tracker.record_change("src/main.py", "CREATE", session_id="s1")
        tracker.record_change("src/main.py", "MODIFY", session_id="s1")
        tracker.record_change("src/other.py", "CREATE", session_id="s1")

        changes = tracker.get_changes(file_path="src/main.py")
        assert len(changes) == 2

    def test_get_changes_limit(self, tracker):
        """测试查询数量限制"""
        for i in range(10):
            tracker.record_change(f"f{i}.py", "CREATE", session_id="s1")

        changes = tracker.get_changes(session_id="s1", limit=5)
        assert len(changes) == 5

    def test_get_session_summary(self, tracker):
        """测试会话摘要"""
        tracker.record_change("a.py", "CREATE", diff="+line1\n+line2\n", session_id="sess-001")
        tracker.record_change("b.py", "MODIFY", diff="-old\n+new\n", session_id="sess-001")
        tracker.record_change("c.py", "CREATE", session_id="sess-002")

        summary = tracker.get_session_summary("sess-001")
        assert summary["total_changes"] == 2
        assert summary["unique_files"] == 2
        assert summary["total_lines_added"] == 3  # +2 + +1
        assert summary["total_lines_removed"] == 1  # -1

    def test_get_session_summary_by_type(self, tracker):
        """测试会话摘要按类型分布"""
        tracker.record_change("a.py", "CREATE", session_id="s1")
        tracker.record_change("b.py", "MODIFY", session_id="s1")
        tracker.record_change("c.py", "MODIFY", session_id="s1")

        summary = tracker.get_session_summary("s1")
        assert summary["by_change_type"]["CREATE"] == 1
        assert summary["by_change_type"]["MODIFY"] == 2

    def test_get_file_history(self, tracker):
        """测试文件变更历史"""
        tracker.record_change("main.py", "CREATE", session_id="s1")
        tracker.record_change("main.py", "MODIFY", session_id="s2")
        tracker.record_change("other.py", "CREATE", session_id="s3")

        history = tracker.get_file_history("main.py")
        assert len(history) == 2
        # 最新的排前面
        assert history[0].change_type == ChangeType.MODIFY

    def test_get_file_history_limit(self, tracker):
        """测试文件变更历史限制"""
        for i in range(20):
            tracker.record_change("main.py", "MODIFY", session_id=f"s{i}")

        history = tracker.get_file_history("main.py", limit=10)
        assert len(history) == 10

    def test_get_stats(self, tracker):
        """测试全局统计"""
        tracker.record_change("a.py", "CREATE", session_id="s1")
        tracker.record_change("b.py", "MODIFY", session_id="s1")
        tracker.record_change("c.py", "CREATE", session_id="s2")

        stats = tracker.get_stats()
        assert stats["total_changes"] == 3
        assert stats["total_sessions"] == 2
        assert stats["total_files"] == 3

    def test_cleanup_old_logs(self, tracker):
        """测试清理过期日志"""
        # 记录一条旧日志（模拟 100 天前）
        old_time = time.time() - (100 * 86400)
        log = AuditLog(
            file_path="old.py",
            change_type=ChangeType.MODIFY,
            diff_content="old diff content",
            session_id="s-old",
            created_at=old_time,
        )

        with tracker.conn_mgr.get_connection() as conn:
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

        # 记录一条新日志
        tracker.record_change("new.py", "CREATE", session_id="s-new")

        # 清理 90 天前的
        cleaned = tracker.cleanup_old_logs(days=90)
        assert cleaned == 1

        # 旧日志的 diff 被清除
        history = tracker.get_file_history("old.py")
        assert len(history) == 1
        assert history[0].diff_content is None


# ==================== AuditReporter 测试 ====================


class TestAuditReporter:
    """报告生成测试"""

    def _setup_data(self, tracker):
        """创建测试数据"""
        tracker.record_change("src/main.py", "CREATE", diff="+line1\n+line2\n", session_id="sess-rpt", task_id="T001")
        tracker.record_change("src/auth.py", "MODIFY", diff="-old\n+new\n", session_id="sess-rpt", task_id="T001")
        tracker.update_quality_status(tracker.get_changes(session_id="sess-rpt")[0].id, "PASSED")

    def test_session_report_markdown(self, tracker, reporter):
        """测试会话 Markdown 报告"""
        self._setup_data(tracker)

        report = reporter.generate_session_report("sess-rpt")
        assert "审计报告" in report
        assert "sess-rpt"[:8] in report
        assert "概览" in report
        assert "总变更数" in report
        assert "2" in report  # 两条变更

    def test_session_report_json(self, tracker, reporter):
        """测试会话 JSON 报告"""
        self._setup_data(tracker)

        report = reporter.generate_session_report("sess-rpt", format="json")
        data = json.loads(report)
        assert data["report_type"] == "session"
        assert len(data["changes"]) == 2

    def test_session_report_with_issues(self, tracker, reporter):
        """测试带问题的会话报告"""
        self._setup_data(tracker)

        issues = [
            AuditIssue(
                severity=IssueSeverity.P1,
                issue_type=IssueType.LINT,
                error_message="E501 line too long",
                file_path="src/main.py",
                check_name="ruff",
            )
        ]
        report = reporter.generate_session_report("sess-rpt", issues=issues)
        assert "发现问题" in report
        assert "E501" in report

    def test_session_report_with_lessons(self, tracker, reporter):
        """测试带经验的会话报告"""
        self._setup_data(tracker)

        lessons = [
            AuditLesson(
                title="避免长行",
                description="保持行宽在 120 字符以内",
                lesson_type=LessonType.BEST_PRACTICE,
                category="code-style",
            )
        ]
        report = reporter.generate_session_report("sess-rpt", lessons=lessons)
        assert "学习经验" in report
        assert "避免长行" in report

    def test_file_report_markdown(self, tracker, reporter):
        """测试文件 Markdown 报告"""
        tracker.record_change("src/main.py", "CREATE", session_id="s1")
        tracker.record_change("src/main.py", "MODIFY", session_id="s2")

        report = reporter.generate_file_report("src/main.py")
        assert "文件审计报告" in report
        assert "src/main.py" in report
        assert "CREATE" in report
        assert "MODIFY" in report

    def test_file_report_json(self, tracker, reporter):
        """测试文件 JSON 报告"""
        tracker.record_change("src/main.py", "CREATE", session_id="s1")

        report = reporter.generate_file_report("src/main.py", format="json")
        data = json.loads(report)
        assert data["report_type"] == "file"
        assert data["history_count"] == 1

    def test_file_report_no_history(self, tracker, reporter):
        """测试无历史的文件报告"""
        report = reporter.generate_file_report("nonexistent.py")
        assert "无变更记录" in report

    def test_summary_markdown(self, tracker, reporter):
        """测试概览 Markdown"""
        tracker.record_change("a.py", "CREATE", session_id="s1")
        tracker.record_change("b.py", "MODIFY", session_id="s2")

        report = reporter.generate_summary()
        assert "审计概览" in report
        assert "2" in report  # 总变更数

    def test_summary_json(self, tracker, reporter):
        """测试概览 JSON"""
        tracker.record_change("a.py", "CREATE", session_id="s1")

        report = reporter.generate_summary(format="json")
        data = json.loads(report)
        assert data["total_changes"] == 1

    def test_save_report(self, tracker, reporter):
        """测试保存报告到文件"""
        report = "# Test Report"
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "subdir", "report.md")
            result = reporter.save_report(report, path)
            assert os.path.exists(result)
            with open(result, "r", encoding="utf-8") as f:
                assert f.read() == "# Test Report"


# ==================== 迁移集成测试 ====================


class TestAuditMigration:
    """审计表迁移测试"""

    def test_migration_applied(self, setup_db):
        """测试迁移成功执行"""
        with setup_db.get_connection() as conn:
            # 验证表存在
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name IN ('audit_log', 'audit_issues', 'audit_lessons')"
            )
            tables = {row[0] for row in cursor.fetchall()}
            assert "audit_log" in tables
            assert "audit_issues" in tables
            assert "audit_lessons" in tables

    def test_migration_indexes(self, setup_db):
        """测试索引创建"""
        with setup_db.get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_audit_%'")
            indexes = {row[0] for row in cursor.fetchall()}
            assert len(indexes) >= 5  # 至少 5 个索引

    def test_migration_idempotent(self, migration_manager, connection_manager):
        """测试迁移幂等性"""
        migration_manager.migrate()
        # 第二次执行不应报错
        migration_manager.migrate()

        with connection_manager.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM audit_log")
            assert cursor.fetchone()[0] == 0
