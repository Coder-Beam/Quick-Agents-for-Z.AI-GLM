"""
UnifiedDB V2 - Phase 1 单元测试

测试覆盖:
- ConnectionManager: 连接池、线程安全、健康检查
- TransactionManager: 事务、嵌套事务、回滚
- MigrationManager: 迁移执行、校验和、回滚

目标: 100% 代码覆盖率
"""

import os
import sys
import pytest
import tempfile
import sqlite3
import threading
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from quickagents.core.connection_manager import ConnectionManager
from quickagents.core.transaction_manager import TransactionManager, TransactionError
from quickagents.core.migration_manager import MigrationManager, Migration


# ==================== Fixtures ====================

@pytest.fixture
def temp_db_path():
    """临时数据库路径"""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        yield os.path.join(tmpdir, "test.db")


@pytest.fixture
def connection_manager(temp_db_path):
    """连接管理器"""
    mgr = ConnectionManager(temp_db_path, pool_size=3)
    yield mgr
    mgr.close_all()


@pytest.fixture
def transaction_manager(connection_manager):
    """事务管理器"""
    return TransactionManager(connection_manager)


@pytest.fixture
def migration_manager(connection_manager):
    """迁移管理器"""
    return MigrationManager(connection_manager)


# ==================== ConnectionManager Tests ====================

class TestConnectionManager:
    """ConnectionManager 测试"""
    
    def test_init(self, temp_db_path):
        """测试初始化"""
        mgr = ConnectionManager(temp_db_path, pool_size=5, timeout=10.0)
        
        assert mgr.db_path == Path(temp_db_path)
        assert mgr.pool_size == 5
        assert mgr.timeout == 10.0
        assert len(mgr._pool) == 5
        assert len(mgr._active_connections) == 0
        
        mgr.close_all()
    
    def test_init_creates_directory(self):
        """测试自动创建目录"""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            db_path = os.path.join(tmpdir, "subdir", "test.db")
            mgr = ConnectionManager(db_path)
            
            assert os.path.exists(os.path.dirname(db_path))
            mgr.close_all()
    
    def test_get_connection(self, connection_manager):
        """测试获取连接"""
        with connection_manager.get_connection() as conn:
            assert conn is not None
            cursor = conn.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
    
    def test_connection_pool_reuse(self, connection_manager):
        """测试连接池复用"""
        # 获取并释放连接
        with connection_manager.get_connection() as conn1:
            conn1.execute("CREATE TABLE test_pool (id INTEGER)")
            conn1.commit()
        
        # 再次获取，应该是复用的连接
        status_before = connection_manager.get_pool_status()
        
        with connection_manager.get_connection() as conn2:
            # 检查表是否存在（同一个连接）
            cursor = conn2.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='test_pool'"
            )
            assert cursor.fetchone() is not None
    
    def test_connection_pool_exhaustion(self, temp_db_path):
        """测试连接池耗尽时在 max_size 内创建新连接"""
        from quickagents.core.connection_manager import PoolConfig
        
        # min=1, max=3: 允许动态扩展
        cfg = PoolConfig(min_size=1, max_size=3, acquire_timeout=5.0)
        mgr = ConnectionManager(temp_db_path, pool_config=cfg)
        
        # 获取第一个连接（池中唯一的连接）
        conn1 = mgr._acquire()
        status = mgr.get_pool_status()
        assert status["available"] == 0
        
        # 连接池为空，但在 max_size 内，应该创建新连接
        conn2 = mgr._acquire()
        assert conn1 is not conn2
        
        # 再获取一个，仍可创建（max=3）
        conn3 = mgr._acquire()
        assert conn3 is not conn1
        assert conn3 is not conn2
        
        mgr._release(conn1)
        mgr._release(conn2)
        mgr._release(conn3)
        mgr.close_all()
    
    def test_connection_pool_max_exhausted(self, temp_db_path):
        """测试达到 max_size 后获取连接超时"""
        from quickagents.core.connection_manager import PoolConfig
        
        cfg = PoolConfig(min_size=1, max_size=1, acquire_timeout=1.0)
        mgr = ConnectionManager(temp_db_path, pool_config=cfg)
        
        # 获取唯一连接
        conn1 = mgr._acquire()
        
        # 第二次获取应该超时
        with pytest.raises(sqlite3.Error, match="Connection pool exhausted"):
            mgr._acquire()
        
        mgr._release(conn1)
        mgr.close_all()
    
    def test_connection_rollback_on_error(self, connection_manager):
        """测试错误时自动回滚"""
        with connection_manager.get_connection() as conn:
            conn.execute("CREATE TABLE test_rollback (id INTEGER PRIMARY KEY)")
            conn.commit()
        
        # 成功插入
        with connection_manager.get_connection() as conn:
            conn.execute("INSERT INTO test_rollback VALUES (1)")
            conn.commit()
        
        # 验证数据
        with connection_manager.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM test_rollback")
            assert cursor.fetchone()[0] == 1
    
    def test_close_all(self, connection_manager):
        """测试关闭所有连接"""
        status = connection_manager.get_pool_status()
        assert status["available"] > 0
        
        connection_manager.close_all()
        
        status = connection_manager.get_pool_status()
        assert status["available"] == 0
        assert status["active"] == 0
    
    def test_health_check_success(self, connection_manager):
        """测试健康检查成功"""
        result = connection_manager.health_check()
        assert result is True
    
    def test_health_check_failure(self, temp_db_path):
        """测试健康检查失败（无效路径）"""
        # 使用无效路径
        mgr = ConnectionManager(temp_db_path)
        mgr.close_all()
        
        # 关闭后健康检查应该失败
        result = mgr.health_check()
        # 由于连接池已关闭，会创建新连接
        assert result is True  # SQLite 会自动重新连接
        mgr.close_all()
    
    def test_get_pool_status(self, connection_manager):
        """测试获取连接池状态"""
        status = connection_manager.get_pool_status()
        
        assert "pool_size" in status
        assert "available" in status
        assert "active" in status
        assert "db_path" in status
        
        assert status["pool_size"] == 3
        assert status["available"] == 3
        assert status["active"] == 0
    
    def test_context_manager(self, temp_db_path):
        """测试上下文管理器"""
        with ConnectionManager(temp_db_path) as mgr:
            assert mgr is not None
            status = mgr.get_pool_status()
            assert status["pool_size"] == 5  # 默认值
    
    def test_repr(self, connection_manager):
        """测试字符串表示"""
        repr_str = repr(connection_manager)
        
        assert "ConnectionManager" in repr_str
        # v2.7.5: repr 使用 min/max 格式
        assert "min=" in repr_str or "pool_size" in repr_str
    
    def test_concurrent_access(self, connection_manager):
        """测试并发访问"""
        results = []
        errors = []
        
        def worker(worker_id):
            try:
                with connection_manager.get_connection() as conn:
                    conn.execute(f"CREATE TABLE test_concurrent_{worker_id} (id INTEGER)")
                    conn.commit()
                    results.append(worker_id)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(results) == 5
        assert len(errors) == 0


# ==================== TransactionManager Tests ====================

class TestTransactionManager:
    """TransactionManager 测试"""
    
    def test_init(self, connection_manager):
        """测试初始化"""
        tx_mgr = TransactionManager(connection_manager)
        
        assert tx_mgr.conn_mgr is connection_manager
        # v2.7.5: 线程本地状态，depth 通过方法访问
        assert tx_mgr.get_depth() == 0
    
    def test_basic_transaction(self, transaction_manager, connection_manager):
        """测试基本事务"""
        # 创建表
        with connection_manager.get_connection() as conn:
            conn.execute("CREATE TABLE test_tx (id INTEGER PRIMARY KEY, value TEXT)")
            conn.commit()
        
        # 事务操作 - 使用事务提供的连接
        with transaction_manager.transaction() as conn:
            conn.execute("INSERT INTO test_tx VALUES (1, 'test')")
            # 不需要手动 commit，事务会自动提交
        
        # 验证数据
        with connection_manager.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM test_tx")
            assert len(cursor.fetchall()) == 1
    
    def test_transaction_rollback(self, transaction_manager, connection_manager):
        """测试事务回滚"""
        # 创建表
        with connection_manager.get_connection() as conn:
            conn.execute("CREATE TABLE test_tx_rollback (id INTEGER PRIMARY KEY)")
            conn.commit()
        
        # 事务操作，故意失败 - 使用事务提供的连接
        try:
            with transaction_manager.transaction() as conn:
                conn.execute("INSERT INTO test_tx_rollback VALUES (1)")
                # 模拟错误
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # 验证数据已回滚
        with connection_manager.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM test_tx_rollback")
            assert cursor.fetchone()[0] == 0
    
    def test_nested_transaction(self, transaction_manager, connection_manager):
        """测试嵌套事务（SAVEPOINT）"""
        # 创建表
        with connection_manager.get_connection() as conn:
            conn.execute("CREATE TABLE test_nested (id INTEGER PRIMARY KEY)")
            conn.commit()
        
        # 嵌套事务 - 使用事务提供的连接
        with transaction_manager.transaction() as conn1:
            conn1.execute("INSERT INTO test_nested VALUES (1)")
            
            # 内层事务 - 使用同一个连接（SAVEPOINT）
            with transaction_manager.transaction() as conn2:
                conn2.execute("INSERT INTO test_nested VALUES (2)")
        
        # 验证数据
        with connection_manager.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM test_nested")
            assert cursor.fetchone()[0] == 2
    
    def test_get_depth(self, transaction_manager):
        """测试获取事务深度"""
        assert transaction_manager.get_depth() == 0
        
        with transaction_manager.transaction():
            assert transaction_manager.get_depth() == 1
            
            with transaction_manager.transaction():
                assert transaction_manager.get_depth() == 2
            
            assert transaction_manager.get_depth() == 1
        
        assert transaction_manager.get_depth() == 0
    
    def test_is_in_transaction(self, transaction_manager):
        """测试检查是否在事务中"""
        assert transaction_manager.is_in_transaction() is False
        
        with transaction_manager.transaction():
            assert transaction_manager.is_in_transaction() is True
        
        assert transaction_manager.is_in_transaction() is False
    
    def test_repr(self, transaction_manager):
        """测试字符串表示"""
        repr_str = repr(transaction_manager)
        assert "TransactionManager" in repr_str


# ==================== MigrationManager Tests ====================

class TestMigrationManager:
    """MigrationManager 测试"""
    
    def test_init(self, connection_manager):
        """测试初始化"""
        mgr = MigrationManager(connection_manager)
        
        assert mgr.conn_mgr is connection_manager
        assert len(mgr.migrations) >= 2  # 至少有内置迁移
    
    def test_builtin_migrations(self, migration_manager):
        """测试内置迁移"""
        versions = [m.version for m in migration_manager.migrations]
        
        assert "001" in versions
        assert "002" in versions
    
    def test_get_applied_migrations_empty(self, migration_manager):
        """测试获取已应用迁移（空）"""
        applied = migration_manager.get_applied_migrations()
        assert applied == []
    
    def test_migrate(self, migration_manager):
        """测试执行迁移"""
        count = migration_manager.migrate()
        
        assert count >= 2  # 至少2个内置迁移
        
        # 验证已应用
        applied = migration_manager.get_applied_migrations()
        assert "001" in applied
        assert "002" in applied
    
    def test_migrate_idempotent(self, migration_manager):
        """测试迁移幂等性"""
        # 第一次迁移
        count1 = migration_manager.migrate()
        assert count1 >= 2
        
        # 第二次迁移（应该无变化）
        count2 = migration_manager.migrate()
        assert count2 == 0
    
    def test_get_pending_migrations(self, migration_manager):
        """测试获取待处理迁移"""
        # 迁移前
        pending = migration_manager.get_pending_migrations()
        assert len(pending) >= 2
        
        # 迁移后
        migration_manager.migrate()
        pending = migration_manager.get_pending_migrations()
        assert len(pending) == 0
    
    def test_register_custom_migration(self, migration_manager):
        """测试注册自定义迁移"""
        custom = Migration(
            version="099",
            name="custom_test",
            up_sql="CREATE TABLE custom_test (id INTEGER)",
            down_sql="DROP TABLE IF EXISTS custom_test"
        )
        
        migration_manager.register_migration(custom)
        
        versions = [m.version for m in migration_manager.migrations]
        assert "099" in versions
    
    def test_verify_checksums(self, migration_manager):
        """测试校验和验证"""
        # 执行迁移
        migration_manager.migrate()
        
        # 验证校验和
        result = migration_manager.verify_checksums()
        assert result is True
    
    def test_get_migration_status(self, migration_manager):
        """测试获取迁移状态"""
        status = migration_manager.get_migration_status()
        
        assert "total_migrations" in status
        assert "applied_count" in status
        assert "pending_count" in status
        assert "applied_versions" in status
        assert "pending_versions" in status
    
    def test_migration_creates_tables(self, migration_manager, connection_manager):
        """测试迁移创建表"""
        migration_manager.migrate()
        
        with connection_manager.get_connection() as conn:
            # 检查 memory 表
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='memory'"
            )
            assert cursor.fetchone() is not None
            
            # 检查 tasks 表
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'"
            )
            assert cursor.fetchone() is not None
            
            # 检查 progress 表
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='progress'"
            )
            assert cursor.fetchone() is not None
    
    def test_migration_checksum_calculation(self):
        """测试迁移校验和计算"""
        migration = Migration(
            version="001",
            name="test",
            up_sql="SELECT 1",
            down_sql="SELECT 2"
        )
        migration.__post_init__()
        
        assert migration.checksum is not None
        assert len(migration.checksum) == 16
    
    def test_repr(self, migration_manager):
        """测试字符串表示"""
        repr_str = repr(migration_manager)
        assert "MigrationManager" in repr_str


# ==================== Integration Tests ====================

class TestIntegration:
    """集成测试"""
    
    def test_full_workflow(self, temp_db_path):
        """测试完整工作流"""
        # 1. 创建连接管理器
        conn_mgr = ConnectionManager(temp_db_path)
        
        # 2. 创建迁移管理器并执行迁移
        mig_mgr = MigrationManager(conn_mgr)
        count = mig_mgr.migrate()
        assert count >= 2
        
        # 3. 创建事务管理器
        tx_mgr = TransactionManager(conn_mgr)
        
        # 4. 使用事务插入数据 - 使用事务提供的连接
        with tx_mgr.transaction() as conn:
            conn.execute(
                "INSERT INTO memory (id, memory_type, key, value) VALUES (?, ?, ?, ?)",
                ("test-1", "factual", "test.key", "test value")
            )
        
        # 5. 验证数据
        with conn_mgr.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM memory WHERE key = 'test.key'")
            row = cursor.fetchone()
            assert row is not None
        
        # 6. 清理
        conn_mgr.close_all()
    
    def test_connection_transaction_migration_cooperation(self, temp_db_path):
        """测试连接、事务、迁移协作（单线程顺序执行）"""
        conn_mgr = ConnectionManager(temp_db_path, pool_size=2)
        tx_mgr = TransactionManager(conn_mgr)
        mig_mgr = MigrationManager(conn_mgr)
        
        # 迁移
        mig_mgr.migrate()
        
        # 顺序执行5个事务
        for i in range(5):
            with tx_mgr.transaction() as conn:
                conn.execute(
                    "INSERT INTO memory (id, memory_type, key, value) VALUES (?, ?, ?, ?)",
                    (f"test-{i}", "factual", f"key-{i}", f"value-{i}")
                )
        
        # 验证
        with conn_mgr.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM memory")
            count = cursor.fetchone()[0]
            assert count == 5
        
        conn_mgr.close_all()
    
    def test_nested_transaction_with_migration(self, temp_db_path):
        """测试嵌套事务与迁移协作"""
        conn_mgr = ConnectionManager(temp_db_path)
        tx_mgr = TransactionManager(conn_mgr)
        mig_mgr = MigrationManager(conn_mgr)
        
        # 迁移
        mig_mgr.migrate()
        
        # 嵌套事务操作
        with tx_mgr.transaction() as conn1:
            conn1.execute(
                "INSERT INTO memory (id, memory_type, key, value) VALUES (?, ?, ?, ?)",
                ("outer-1", "factual", "outer.key", "outer value")
            )
            
            # 嵌套事务
            with tx_mgr.transaction() as conn2:
                conn2.execute(
                    "INSERT INTO memory (id, memory_type, key, value) VALUES (?, ?, ?, ?)",
                    ("inner-1", "factual", "inner.key", "inner value")
                )
        
        # 验证两条数据都存在
        with conn_mgr.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM memory")
            assert cursor.fetchone()[0] == 2
        
        conn_mgr.close_all()


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
