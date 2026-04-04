"""
Phase 5 测试 - Session 接口统一

测试范围:
1. Session 类基本功能 (query/transaction/read_only/execute/executescript/query_one/query_all)
2. ConnectionManager 公共 acquire()/release() 接口
3. UnifiedDB.session 属性
4. _get_connection() 通过 Session 委托
5. 线程安全
6. 嵌套事务
"""

import os
import tempfile
import threading
import pytest

from quickagents.core.connection_manager import ConnectionManager, PoolConfig
from quickagents.core.transaction_manager import TransactionManager
from quickagents.core.session import Session
from quickagents.core.unified_db import UnifiedDB


# ==================== Fixtures ====================

@pytest.fixture
def db_path():
    """创建临时数据库"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def conn_mgr(db_path):
    """创建连接管理器"""
    mgr = ConnectionManager(db_path, pool_size=3)
    yield mgr
    mgr.close_all()


@pytest.fixture
def tx_mgr(conn_mgr):
    """创建事务管理器"""
    return TransactionManager(conn_mgr)


@pytest.fixture
def session(conn_mgr, tx_mgr):
    """创建 Session"""
    return Session(conn_mgr, tx_mgr)


@pytest.fixture
def db(db_path):
    """创建 UnifiedDB"""
    database = UnifiedDB(db_path)
    yield database
    database.close()


@pytest.fixture
def setup_test_table(session):
    """创建测试表"""
    session.executescript("""
        CREATE TABLE IF NOT EXISTS test_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            value INTEGER DEFAULT 0
        )
    """)


# ==================== 1. Session 基本功能 ====================

class TestSessionBasic:
    """Session 基本功能测试"""
    
    def test_session_creation(self, session, conn_mgr, tx_mgr):
        """测试 Session 创建"""
        assert session.connection_manager is conn_mgr
        assert session.transaction_manager is tx_mgr
    
    def test_session_repr(self, session):
        """测试 Session repr"""
        r = repr(session)
        assert 'Session' in r
    
    def test_session_query_readonly(self, session, setup_test_table):
        """测试 query() 只读查询"""
        # 先插入数据
        session.execute("INSERT INTO test_data (name, value) VALUES (?, ?)", ('test1', 10))
        
        # 通过 query 读取
        with session.query() as conn:
            cursor = conn.execute("SELECT * FROM test_data")
            rows = cursor.fetchall()
            assert len(rows) >= 1
    
    def test_session_transaction_commit(self, session, setup_test_table):
        """测试 transaction() 正常提交"""
        with session.transaction() as conn:
            conn.execute("INSERT INTO test_data (name, value) VALUES (?, ?)", ('tx_test', 42))
        
        # 验证数据已提交
        row = session.query_one("SELECT name, value FROM test_data WHERE name = ?", ('tx_test',))
        assert row is not None
        assert row[0] == 'tx_test'
        assert row[1] == 42
    
    def test_session_transaction_rollback(self, session, setup_test_table):
        """测试 transaction() 异常回滚"""
        # 先插入一条
        session.execute("INSERT INTO test_data (name, value) VALUES (?, ?)", ('before', 1))
        
        # 事务中插入但抛异常
        with pytest.raises(ValueError):
            with session.transaction() as conn:
                conn.execute("INSERT INTO test_data (name, value) VALUES (?, ?)", ('should_not_exist', 99))
                raise ValueError("force rollback")
        
        # 验证回滚的数据不存在
        row = session.query_one("SELECT * FROM test_data WHERE name = ?", ('should_not_exist',))
        assert row is None
        
        # 之前的数据还在
        row = session.query_one("SELECT * FROM test_data WHERE name = ?", ('before',))
        assert row is not None
    
    def test_session_read_only(self, session, setup_test_table):
        """测试 read_only() 只读事务"""
        # 先插入数据
        session.execute("INSERT INTO test_data (name, value) VALUES (?, ?)", ('ro_test', 5))
        
        with session.read_only() as conn:
            cursor = conn.execute("SELECT * FROM test_data WHERE name = ?", ('ro_test',))
            row = cursor.fetchone()
            assert row is not None
    
    def test_session_execute_insert(self, session, setup_test_table):
        """测试 execute() 插入"""
        cursor = session.execute("INSERT INTO test_data (name, value) VALUES (?, ?)", ('exec_test', 100))
        assert cursor is not None
        
        row = session.query_one("SELECT value FROM test_data WHERE name = ?", ('exec_test',))
        assert row[0] == 100
    
    def test_session_execute_no_params(self, session, setup_test_table):
        """测试 execute() 无参数"""
        cursor = session.execute("INSERT INTO test_data (name, value) VALUES ('no_params', 0)")
        assert cursor is not None
    
    def test_session_executescript(self, session):
        """测试 executescript()"""
        session.executescript("""
            CREATE TABLE IF NOT EXISTS script_test (
                id INTEGER PRIMARY KEY,
                data TEXT
            );
            INSERT INTO script_test (data) VALUES ('hello');
        """)
        
        row = session.query_one("SELECT data FROM script_test WHERE id = 1")
        assert row[0] == 'hello'
    
    def test_session_query_one(self, session, setup_test_table):
        """测试 query_one()"""
        session.execute("INSERT INTO test_data (name, value) VALUES (?, ?)", ('q1', 1))
        session.execute("INSERT INTO test_data (name, value) VALUES (?, ?)", ('q1', 2))
        
        row = session.query_one("SELECT SUM(value) FROM test_data WHERE name = ?", ('q1',))
        assert row[0] == 3
    
    def test_session_query_one_none(self, session, setup_test_table):
        """测试 query_one() 无结果返回 None"""
        row = session.query_one("SELECT * FROM test_data WHERE name = ?", ('nonexistent',))
        assert row is None
    
    def test_session_query_all(self, session, setup_test_table):
        """测试 query_all()"""
        session.execute("INSERT INTO test_data (name, value) VALUES (?, ?)", ('qa', 1))
        session.execute("INSERT INTO test_data (name, value) VALUES (?, ?)", ('qa', 2))
        session.execute("INSERT INTO test_data (name, value) VALUES (?, ?)", ('qa', 3))
        
        rows = session.query_all("SELECT * FROM test_data WHERE name = ? ORDER BY value", ('qa',))
        assert len(rows) == 3
        assert rows[0][2] == 1  # value column
    
    def test_session_query_all_empty(self, session, setup_test_table):
        """测试 query_all() 无结果返回空列表"""
        rows = session.query_all("SELECT * FROM test_data WHERE name = ?", ('nonexistent',))
        assert rows == []


# ==================== 2. ConnectionManager 公共接口 ====================

class TestConnectionManagerPublicAPI:
    """ConnectionManager acquire()/release() 公共接口测试"""
    
    def test_acquire_release_basic(self, conn_mgr, setup_test_table):
        """测试基本的 acquire/release"""
        conn = conn_mgr.acquire()
        assert conn is not None
        
        cursor = conn.execute("SELECT 1")
        assert cursor.fetchone()[0] == 1
        
        conn_mgr.release(conn)
    
    def test_acquire_release_multiple(self, conn_mgr):
        """测试多次 acquire/release"""
        conns = []
        for _ in range(3):
            conn = conn_mgr.acquire()
            conns.append(conn)
        
        # 所有连接应该不同
        assert len(set(id(c) for c in conns)) == 3
        
        for conn in conns:
            conn_mgr.release(conn)
    
    def test_acquire_release_data_persistence(self, conn_mgr, setup_test_table):
        """测试通过 acquire/release 的数据持久化"""
        # 获取连接，创建表并插入
        conn = conn_mgr.acquire()
        conn.execute("INSERT INTO test_data (name, value) VALUES (?, ?)", ('persist', 42))
        conn.commit()
        conn_mgr.release(conn)
        
        # 新连接验证
        conn = conn_mgr.acquire()
        cursor = conn.execute("SELECT value FROM test_data WHERE name = ?", ('persist',))
        row = cursor.fetchone()
        assert row[0] == 42
        conn_mgr.release(conn)
    
    def test_public_api_same_behavior_as_private(self, conn_mgr):
        """测试公共接口和私有接口行为一致"""
        # 公共接口
        conn1 = conn_mgr.acquire()
        status = conn_mgr.get_pool_status()
        active_public = status['active']
        conn_mgr.release(conn1)
        
        # 私有接口（向后兼容）
        conn2 = conn_mgr._acquire()
        status = conn_mgr.get_pool_status()
        active_private = status['active']
        conn_mgr._release(conn2)
        
        # 行为一致：都有 1 个活跃连接
        assert active_public == active_private


# ==================== 3. UnifiedDB Session 集成 ====================

class TestUnifiedDBSession:
    """UnifiedDB Session 集成测试"""
    
    def test_session_property(self, db):
        """测试 session 属性存在且类型正确"""
        assert hasattr(db, 'session')
        assert isinstance(db.session, Session)
    
    def test_session_property_identity(self, db):
        """测试多次调用返回同一实例"""
        s1 = db.session
        s2 = db.session
        assert s1 is s2
    
    def test_session_delegates_to_cm_tm(self, db):
        """测试 Session 委托给正确的 CM 和 TM"""
        session = db.session
        assert session.connection_manager is db.connection_manager
        assert session.transaction_manager is db.transaction_manager
    
    def test_get_connection_uses_session(self, db):
        """测试 _get_connection() 通过 Session 委托"""
        # 通过 _get_connection 插入数据
        with db._get_connection() as conn:
            conn.execute(
                "INSERT INTO memory (key, value, memory_type) VALUES (?, ?, ?)",
                ('test.v1.compat', 'hello', 'factual')
            )
        
        # 通过 Session 查询验证
        row = db.session.query_one(
            "SELECT value FROM memory WHERE key = ?",
            ('test.v1.compat',)
        )
        assert row is not None
        assert row[0] == 'hello'
    
    def test_get_connection_row_factory(self, db):
        """测试 _get_connection() 设置了 row_factory"""
        with db._get_connection() as conn:
            # 插入数据
            conn.execute(
                "INSERT OR REPLACE INTO memory (key, value, memory_type) VALUES (?, ?, ?)",
                ('test.row_factory', 'test', 'factual')
            )
            # 验证 row_factory 为 sqlite3.Row
            import sqlite3
            assert conn.row_factory is sqlite3.Row
            
            cursor = conn.execute("SELECT * FROM memory WHERE key = ?", ('test.row_factory',))
            row = cursor.fetchone()
            # sqlite3.Row 支持列名访问
            assert row['key'] == 'test.row_factory'


# ==================== 4. Session 嵌套事务 ====================

class TestSessionNestedTransactions:
    """Session 嵌套事务测试"""
    
    def test_nested_transaction_success(self, session, setup_test_table):
        """测试嵌套事务正常提交"""
        with session.transaction() as conn1:
            conn1.execute("INSERT INTO test_data (name, value) VALUES (?, ?)", ('outer', 1))
            
            with session.transaction() as conn2:
                assert conn2 is conn1  # 嵌套复用同一连接
                conn2.execute("INSERT INTO test_data (name, value) VALUES (?, ?)", ('inner', 2))
        
        # 两条数据都提交
        rows = session.query_all("SELECT * FROM test_data ORDER BY name")
        names = [r[1] for r in rows]
        assert 'outer' in names
        assert 'inner' in names
    
    def test_nested_transaction_inner_rollback(self, session, setup_test_table):
        """测试嵌套事务内层回滚"""
        with session.transaction() as conn1:
            conn1.execute("INSERT INTO test_data (name, value) VALUES (?, ?)", ('outer_ok', 1))
            
            try:
                with session.transaction() as conn2:
                    conn2.execute("INSERT INTO test_data (name, value) VALUES (?, ?)", ('inner_fail', 2))
                    raise ValueError("inner error")
            except ValueError:
                pass  # 内层回滚，外层继续
        
        # 外层数据存在
        row = session.query_one("SELECT * FROM test_data WHERE name = ?", ('outer_ok',))
        assert row is not None
    
    def test_nested_transaction_outer_rollback(self, session, setup_test_table):
        """测试外层回滚时全部回滚"""
        with pytest.raises(ValueError):
            with session.transaction() as conn1:
                conn1.execute("INSERT INTO test_data (name, value) VALUES (?, ?)", ('both_fail', 1))
                
                with session.transaction() as conn2:
                    conn2.execute("INSERT INTO test_data (name, value) VALUES (?, ?)", ('both_fail', 2))
                
                raise ValueError("outer error")
        
        # 全部回滚
        row = session.query_one("SELECT * FROM test_data WHERE name = ?", ('both_fail',))
        assert row is None


# ==================== 5. 线程安全 ====================

class TestSessionThreadSafety:
    """Session 线程安全测试"""
    
    def test_concurrent_transactions(self, session, setup_test_table):
        """测试并发事务"""
        errors = []
        results = []
        
        def worker(thread_id, name):
            try:
                with session.transaction() as conn:
                    conn.execute(
                        "INSERT INTO test_data (name, value) VALUES (?, ?)",
                        (f'thread_{name}', thread_id)
                    )
                results.append(thread_id)
            except Exception as e:
                errors.append(e)
        
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker, args=(i, f't{i}'))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join(timeout=10)
        
        assert len(errors) == 0, f"Thread errors: {errors}"
        assert len(results) == 5
        
        # 验证所有数据都写入
        rows = session.query_all(
            "SELECT name FROM test_data WHERE name LIKE 'thread_%'"
        )
        assert len(rows) == 5
    
    def test_concurrent_query(self, session, setup_test_table):
        """测试并发查询"""
        # 先插入数据
        for i in range(10):
            session.execute("INSERT INTO test_data (name, value) VALUES (?, ?)", (f'cq_{i}', i))
        
        errors = []
        results = []
        
        def reader(reader_id):
            try:
                rows = session.query_all("SELECT * FROM test_data WHERE name LIKE 'cq_%'")
                results.append((reader_id, len(rows)))
            except Exception as e:
                errors.append(e)
        
        threads = []
        for i in range(5):
            t = threading.Thread(target=reader, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join(timeout=10)
        
        assert len(errors) == 0, f"Thread errors: {errors}"
        assert len(results) == 5
        for reader_id, count in results:
            assert count == 10


# ==================== 6. Session 导入测试 ====================

class TestSessionImport:
    """Session 导入测试"""
    
    def test_import_from_core(self):
        """测试从 core 包导入 Session"""
        from quickagents.core import Session
        assert Session is not None
    
    def test_session_in_all(self):
        """测试 Session 在 __all__ 中"""
        from quickagents.core import __all__
        assert 'Session' in __all__
    
    def test_import_from_quickagents(self):
        """测试从 quickagents 包导入 Session"""
        from quickagents.core.session import Session
        assert Session is not None


# ==================== 7. Session 与 Repository 集成 ====================

class TestSessionRepositoryIntegration:
    """Session 与 Repository 集成测试"""
    
    def test_session_with_memory_repo(self, db):
        """测试 Session 与 MemoryRepository 协作"""
        from quickagents.core.repositories import MemoryType
        # 通过 UnifiedDB API 写入
        db.set_memory('session.test.key', 'hello_session', memory_type=MemoryType.FACTUAL)
        
        # 通过 Session 读取验证
        row = db.session.query_one(
            "SELECT value FROM memory WHERE key = ?",
            ('session.test.key',)
        )
        assert row is not None
        assert row[0] == 'hello_session'
    
    def test_session_with_task_repo(self, db):
        """测试 Session 与 TaskRepository 协作"""
        # 通过 UnifiedDB API 写入
        db.add_task('T-P5-001', 'Phase 5 测试任务', priority='P0')
        
        # 通过 Session 读取验证
        row = db.session.query_one(
            "SELECT name FROM tasks WHERE id = ?",
            ('T-P5-001',)
        )
        assert row is not None
        assert row[0] == 'Phase 5 测试任务'
