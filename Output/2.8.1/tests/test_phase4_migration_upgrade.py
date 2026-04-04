"""
Phase 4 - MigrationManager 升级测试

测试覆盖:
- 外部迁移文件加载 (load_external_migrations)
- 增强迁移日志 (MigrationResult, get_last_results)
- MigrationResult dataclass
- 向后兼容性验证
"""

import os
import pytest
import tempfile
import time
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from quickagents.core.migration_manager import MigrationManager, Migration, MigrationResult
from quickagents.core.connection_manager import ConnectionManager


# ==================== Fixtures ====================

@pytest.fixture
def temp_dir():
    """临时目录（用于迁移文件）"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def db_path():
    """临时数据库路径"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield os.path.join(tmpdir, "test.db")


@pytest.fixture
def conn_mgr(db_path):
    """独立的 ConnectionManager"""
    mgr = ConnectionManager(db_path)
    yield mgr
    mgr.close_all()


@pytest.fixture
def mm(conn_mgr):
    """MigrationManager 实例"""
    return MigrationManager(conn_mgr)


# ==================== MigrationResult 测试 ====================

class TestMigrationResult:
    """MigrationResult dataclass 测试"""

    def test_success_result(self):
        result = MigrationResult(version="001", name="test", success=True, duration_ms=12.5)
        assert result.version == "001"
        assert result.success is True
        assert result.duration_ms == 12.5
        assert result.error is None
        assert result.applied_at > 0

    def test_failure_result(self):
        result = MigrationResult(version="002", name="fail", success=False, duration_ms=5.0, error="syntax error")
        assert result.success is False
        assert result.error == "syntax error"

    def test_default_values(self):
        result = MigrationResult(version="003", name="default", success=True)
        assert result.duration_ms == 0.0
        assert result.error is None
        assert result.applied_at > 0


# ==================== 外部迁移文件加载 ====================

class TestExternalMigrations:
    """外部迁移文件加载测试"""

    def test_load_nonexistent_dir(self, mm):
        count = mm.load_external_migrations("/nonexistent/path")
        assert count == 0

    def test_load_empty_dir(self, mm, temp_dir):
        count = mm.load_external_migrations(temp_dir)
        assert count == 0

    def test_load_single_migration(self, mm, temp_dir):
        mig_file = Path(temp_dir) / "003_add_notes_table.sql"
        mig_file.write_text("CREATE TABLE IF NOT EXISTS notes (id TEXT PRIMARY KEY, title TEXT);", encoding='utf-8')
        
        count = mm.load_external_migrations(temp_dir)
        assert count == 1
        
        mig = next(m for m in mm.migrations if m.version == "003")
        assert mig.name == "add_notes_table"
        assert mig.source == "external"
        assert mig.down_sql == ""

    def test_load_with_rollback(self, mm, temp_dir):
        up_file = Path(temp_dir) / "004_add_tags.sql"
        up_file.write_text("CREATE TABLE IF NOT EXISTS tags (id TEXT PRIMARY KEY);", encoding='utf-8')
        down_file = Path(temp_dir) / "004_add_tags_rollback.sql"
        down_file.write_text("DROP TABLE IF EXISTS tags;", encoding='utf-8')
        
        count = mm.load_external_migrations(temp_dir)
        assert count == 1
        
        mig = next(m for m in mm.migrations if m.version == "004")
        assert mig.down_sql == "DROP TABLE IF EXISTS tags;"

    def test_load_multiple_migrations(self, mm, temp_dir):
        for i in range(3, 7):
            f = Path(temp_dir) / f"00{i}_feature_{i}.sql"
            f.write_text(f"CREATE TABLE t{i} (id TEXT);", encoding='utf-8')
        
        count = mm.load_external_migrations(temp_dir)
        assert count == 4
        
        versions = [m.version for m in mm.migrations]
        assert versions == sorted(versions)

    def test_skip_duplicate_version(self, mm, temp_dir):
        f = Path(temp_dir) / "001_duplicate.sql"
        f.write_text("SELECT 1;", encoding='utf-8')
        
        count = mm.load_external_migrations(temp_dir)
        assert count == 0

    def test_skip_invalid_filename(self, mm, temp_dir):
        f = Path(temp_dir) / "invalid.sql"
        f.write_text("SELECT 1;", encoding='utf-8')
        
        count = mm.load_external_migrations(temp_dir)
        assert count == 0

    def test_skip_rollback_only_files(self, mm, temp_dir):
        f = Path(temp_dir) / "005_test_rollback.sql"
        f.write_text("DROP TABLE t;", encoding='utf-8')
        
        count = mm.load_external_migrations(temp_dir)
        assert count == 0

    def test_external_migration_executes(self, conn_mgr, mm, temp_dir):
        mig_file = Path(temp_dir) / "003_ext_table.sql"
        mig_file.write_text("CREATE TABLE IF NOT EXISTS ext_table (id TEXT PRIMARY KEY, value TEXT);", encoding='utf-8')
        
        mm.load_external_migrations(temp_dir)
        count = mm.migrate()
        assert count >= 1
        
        with conn_mgr.get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ext_table'")
            assert cursor.fetchone() is not None


# ==================== 增强迁移日志 ====================

class TestMigrationLogging:
    """增强迁移日志测试"""

    def test_get_last_results_empty(self, mm):
        results = mm.get_last_results()
        assert results == []

    def test_get_last_results_after_migrate(self, mm):
        mm.migrate()
        
        results = mm.get_last_results()
        assert len(results) >= 2
        
        for r in results:
            assert isinstance(r, MigrationResult)
            assert r.success is True
            assert r.duration_ms >= 0

    def test_results_contain_version_info(self, mm):
        mm.migrate()
        
        results = mm.get_last_results()
        versions = [r.version for r in results]
        assert "001" in versions
        assert "002" in versions

    def test_results_have_duration(self, mm):
        mm.migrate()
        
        results = mm.get_last_results()
        for r in results:
            assert r.duration_ms >= 0

    def test_status_includes_last_results(self, mm):
        mm.migrate()
        
        status = mm.get_migration_status()
        assert "last_results" in status
        assert len(status["last_results"]) >= 2
        
        for item in status["last_results"]:
            assert "version" in item
            assert "name" in item
            assert "success" in item
            assert "duration_ms" in item

    def test_failed_migration_in_results(self, mm):
        bad_migration = Migration(version="999", name="will_fail", up_sql="INVALID SQL;", down_sql="")
        mm.register_migration(bad_migration)
        
        with pytest.raises(RuntimeError):
            mm.migrate()
        
        results = mm.get_last_results()
        failed = [r for r in results if r.version == "999"]
        assert len(failed) == 1
        assert failed[0].success is False
        assert failed[0].error is not None

    def test_idempotent_migrate_retains_results(self, mm):
        mm.migrate()
        
        count = mm.migrate()
        assert count == 0
        
        results = mm.get_last_results()
        assert len(results) >= 2


# ==================== Migration source 测试 ====================

class TestMigrationSource:
    """迁移来源标记测试"""

    def test_builtin_source(self, mm):
        for m in mm.migrations:
            if m.version in ("001", "002"):
                assert m.source == "builtin"

    def test_external_source(self, mm, temp_dir):
        f = Path(temp_dir) / "003_source_test.sql"
        f.write_text("SELECT 1;", encoding='utf-8')
        
        mm.load_external_migrations(temp_dir)
        
        mig = next(m for m in mm.migrations if m.version == "003")
        assert mig.source == "external"

    def test_registered_source(self, mm):
        m = Migration(version="099", name="registered_test", up_sql="SELECT 1;", down_sql="")
        mm.register_migration(m)
        
        registered = next(m for m in mm.migrations if m.version == "099")
        assert registered.source == "registered"


# ==================== 向后兼容性 ====================

class TestBackwardCompat:
    """向后兼容性测试"""

    def test_migrate_returns_count(self, mm):
        count = mm.migrate()
        assert isinstance(count, int)

    def test_rollback_still_works(self, mm):
        mm.migrate()
        result = mm.rollback("002")
        assert result is True

    def test_verify_checksums_still_works(self, mm):
        mm.migrate()
        assert mm.verify_checksums() is True

    def test_repr_unchanged(self, mm):
        r = repr(mm)
        assert "MigrationManager" in r
        assert "total=" in r


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
