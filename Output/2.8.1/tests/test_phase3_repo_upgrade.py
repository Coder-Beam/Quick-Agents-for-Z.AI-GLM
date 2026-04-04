"""
Phase 3 - Repository 层升级测试

测试覆盖:
- QueryBuilder: 链式查询构建器
- 批量操作优化: add_batch 使用批量 VALUES
- BaseRepository.query() 集成
- 向后兼容性验证

目标: 100% 新增代码覆盖
"""

import os
import sys
import time
import pytest
import tempfile
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from quickagents.core.unified_db import UnifiedDB
from quickagents.core.repositories.models import (
    Memory, Task, Progress, Feedback,
    MemoryType, TaskStatus, TaskPriority, FeedbackType,
)
from quickagents.core.repositories.query_builder import (
    QueryBuilder, FilterOp, FilterCondition, _SUFFIX_TO_OP,
)
from quickagents.core.repositories.memory_repo import MemoryRepository
from quickagents.core.repositories.task_repo import TaskRepository


# ==================== Fixtures ====================

@pytest.fixture
def temp_db_path():
    """临时数据库路径"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield os.path.join(tmpdir, "test_phase3.db")


@pytest.fixture
def db(temp_db_path):
    """UnifiedDB 实例"""
    db = UnifiedDB(temp_db_path)
    yield db
    db.close()


@pytest.fixture
def memory_repo(db):
    """记忆仓储"""
    return db._memory_repo


@pytest.fixture
def task_repo(db):
    """任务仓储"""
    return db._task_repo


@pytest.fixture
def seed_memories(memory_repo):
    """预填记忆数据"""
    items = []
    for i in range(20):
        m = Memory(
            id=f"mem-{i:03d}",
            memory_type=MemoryType.FACTUAL if i % 3 == 0 else (
                MemoryType.EXPERIENTIAL if i % 3 == 1 else MemoryType.WORKING
            ),
            key=f"key.{i}",
            value=f"value {i} {'auth' if i < 5 else 'other'}",
            category="pitfalls" if i < 7 else "general",
            importance_score=round(0.1 + (i * 0.045), 2),
        )
        m.created_at = time.time() - (20 - i) * 100  # 越新越大
        memory_repo.add(m)
        items.append(m)
    return items


# ==================== QueryBuilder 单元测试 ====================

class TestQueryBuilderParsing:
    """查询构建器条件解析测试"""

    def test_eq_filter(self, memory_repo):
        """精确匹配"""
        results = memory_repo.query().filter(memory_type=MemoryType.FACTUAL.value).all()
        assert all(m.memory_type == MemoryType.FACTUAL for m in results)

    def test_gt_filter(self, memory_repo, seed_memories):
        """大于操作符"""
        results = memory_repo.query().filter(importance_score__gt=0.5).all()
        assert all(m.importance_score > 0.5 for m in results)

    def test_gte_filter(self, memory_repo, seed_memories):
        """大于等于操作符"""
        results = memory_repo.query().filter(importance_score__gte=0.5).all()
        assert all(m.importance_score >= 0.5 for m in results)

    def test_lt_filter(self, memory_repo, seed_memories):
        """小于操作符"""
        results = memory_repo.query().filter(importance_score__lt=0.5).all()
        assert all(m.importance_score < 0.5 for m in results)

    def test_lte_filter(self, memory_repo, seed_memories):
        """小于等于操作符"""
        results = memory_repo.query().filter(importance_score__lte=0.5).all()
        assert all(m.importance_score <= 0.5 for m in results)

    def test_contains_filter(self, memory_repo, seed_memories):
        """包含操作符"""
        results = memory_repo.query().filter(value__contains='auth').all()
        assert all('auth' in m.value for m in results)
        assert len(results) >= 5  # 前5个包含 'auth'

    def test_startswith_filter(self, memory_repo, seed_memories):
        """前缀匹配操作符"""
        results = memory_repo.query().filter(key__startswith='key.1').all()
        assert all(m.key.startswith('key.1') for m in results)

    def test_in_filter(self, memory_repo, seed_memories):
        """IN 操作符"""
        types = [MemoryType.FACTUAL.value, MemoryType.WORKING.value]
        results = memory_repo.query().filter(memory_type__in=types).all()
        assert all(m.memory_type in (MemoryType.FACTUAL, MemoryType.WORKING) for m in results)

    def test_ne_filter(self, memory_repo, seed_memories):
        """不等于操作符"""
        results = memory_repo.query().filter(memory_type__ne=MemoryType.FACTUAL.value).all()
        assert all(m.memory_type != MemoryType.FACTUAL for m in results)

    def test_none_value_becomes_is_null(self, memory_repo, seed_memories):
        """None 值转为 IS NULL"""
        # memory_repo 没有 NULL category 的记录，这里测试的是查询不报错
        results = memory_repo.query().filter(category=None).all()
        assert isinstance(results, list)

    def test_in_empty_list_raises(self, memory_repo):
        """__in 空列表抛出异常"""
        with pytest.raises(ValueError, match="不能为空列表"):
            memory_repo.query().filter(memory_type__in=[]).all()

    def test_in_non_list_raises(self, memory_repo):
        """__in 非列表抛出异常"""
        with pytest.raises(ValueError, match="列表/元组/集合"):
            memory_repo.query().filter(memory_type__in="not_list").all()


class TestQueryBuilderChaining:
    """查询构建器链式操作测试"""

    def test_multiple_filters(self, memory_repo, seed_memories):
        """多个 filter 链式调用（AND）"""
        results = memory_repo.query() \
            .filter(memory_type=MemoryType.FACTUAL.value) \
            .filter(category="pitfalls") \
            .all()
        assert all(
            m.memory_type == MemoryType.FACTUAL and m.category == "pitfalls"
            for m in results
        )

    def test_exclude(self, memory_repo, seed_memories):
        """exclude 排除条件"""
        results = memory_repo.query() \
            .filter(category="pitfalls") \
            .exclude(memory_type=MemoryType.FACTUAL.value) \
            .all()
        assert all(m.category == "pitfalls" and m.memory_type != MemoryType.FACTUAL for m in results)

    def test_order_by_asc(self, memory_repo, seed_memories):
        """升序排序"""
        results = memory_repo.query().order_by('importance_score').limit(5).all()
        scores = [m.importance_score for m in results]
        assert scores == sorted(scores)

    def test_order_by_desc(self, memory_repo, seed_memories):
        """降序排序"""
        results = memory_repo.query().order_by('-importance_score').limit(5).all()
        scores = [m.importance_score for m in results]
        assert scores == sorted(scores, reverse=True)

    def test_order_by_multiple(self, memory_repo, seed_memories):
        """多字段排序"""
        results = memory_repo.query().order_by('memory_type', '-importance_score').all()
        assert len(results) > 0
        # 验证排序方向正确
        for i in range(len(results) - 1):
            a, b = results[i], results[i + 1]
            assert (a.memory_type.value, -a.importance_score) <= (b.memory_type.value, -b.importance_score)

    def test_limit(self, memory_repo, seed_memories):
        """LIMIT"""
        results = memory_repo.query().order_by('-created_at').limit(5).all()
        assert len(results) <= 5

    def test_offset(self, memory_repo, seed_memories):
        """OFFSET"""
        page1 = memory_repo.query().order_by('id').limit(5).all()
        page2 = memory_repo.query().order_by('id').limit(5).offset(5).all()
        assert len(page1) == 5
        assert page1[0].id != page2[0].id

    def test_only(self, memory_repo, seed_memories):
        """选择字段（only 选择子集，row_mapper 需全字段才能映射为实体）"""
        # 使用不带 mapper 的 QueryBuilder 测试 only
        qb = QueryBuilder(
            table_name='memory',
            row_mapper=None,
            conn_provider=memory_repo.conn_mgr.get_connection
        )
        results = qb.filter(memory_type=MemoryType.FACTUAL.value).only(['key', 'value']).all()
        assert len(results) > 0
        # 没有 mapper，返回原始行
        for row in results:
            assert len(row) == 2  # key, value

    def test_first(self, memory_repo, seed_memories):
        """first() 返回单条"""
        result = memory_repo.query().order_by('-importance_score').first()
        assert result is not None
        assert isinstance(result, Memory)

    def test_first_empty(self, memory_repo):
        """first() 空结果返回 None"""
        result = memory_repo.query().filter(key="__nonexistent__").first()
        assert result is None

    def test_count(self, memory_repo, seed_memories):
        """count()"""
        total = memory_repo.query().count()
        assert total == len(seed_memories)

        factual_count = memory_repo.query().filter(memory_type=MemoryType.FACTUAL.value).count()
        assert factual_count == len([m for m in seed_memories if m.memory_type == MemoryType.FACTUAL])

    def test_exists(self, memory_repo, seed_memories):
        """exists()"""
        assert memory_repo.query().filter(key="key.0").exists() is True
        assert memory_repo.query().filter(key="__nonexistent__").exists() is False

    def test_delete(self, memory_repo, seed_memories):
        """delete() 通过构建器删除"""
        initial_count = memory_repo.query().count()
        deleted = memory_repo.query().filter(category="general").delete()
        assert deleted > 0
        assert memory_repo.query().count() == initial_count - deleted

    def test_immutability(self, memory_repo):
        """链式调用不可变性"""
        q1 = memory_repo.query()
        q2 = q1.filter(memory_type=MemoryType.FACTUAL.value)
        q3 = q1.filter(memory_type=MemoryType.WORKING.value)

        # q1 不受影响
        assert len(q1._filters) == 0
        # q2, q3 独立
        assert len(q2._filters) == 1
        assert len(q3._filters) == 1
        assert q2._filters[0].value != q3._filters[0].value


class TestQueryBuilderRepr:
    """查询构建器 repr 测试"""

    def test_repr_basic(self, memory_repo):
        """基础 repr"""
        r = repr(memory_repo.query())
        assert "QueryBuilder" in r
        assert "memory" in r

    def test_repr_with_filters(self, memory_repo):
        """带条件的 repr"""
        r = repr(memory_repo.query().filter(key='test').filter(value='v'))
        assert "filters=2" in r

    def test_repr_with_order(self, memory_repo):
        """带排序的 repr"""
        r = repr(memory_repo.query().order_by('-created_at'))
        assert "order=" in r

    def test_repr_with_limit(self, memory_repo):
        """带限制的 repr"""
        r = repr(memory_repo.query().limit(10))
        assert "limit=10" in r


# ==================== FilterCondition 单元测试 ====================

class TestFilterCondition:
    """过滤条件测试"""

    def test_filter_condition_repr(self):
        """FilterCondition repr"""
        fc = FilterCondition('key', FilterOp.EQ, 'value')
        r = repr(fc)
        assert 'key' in r
        assert 'value' in r

    def test_filter_op_values(self):
        """FilterOp 枚举值"""
        assert FilterOp.EQ.value == '='
        assert FilterOp.NE.value == '!='
        assert FilterOp.GT.value == '>'
        assert FilterOp.GTE.value == '>='
        assert FilterOp.LT.value == '<'
        assert FilterOp.LTE.value == '<='
        assert FilterOp.LIKE.value == 'LIKE'
        assert FilterOp.NOT_LIKE.value == 'NOT LIKE'
        assert FilterOp.IN.value == 'IN'
        assert FilterOp.NOT_IN.value == 'NOT IN'
        assert FilterOp.IS_NULL.value == 'IS NULL'
        assert FilterOp.IS_NOT_NULL.value == 'IS NOT NULL'


class TestSuffixToOp:
    """后缀映射测试"""

    def test_suffix_mapping(self):
        """验证所有后缀映射"""
        assert _SUFFIX_TO_OP[''] == FilterOp.EQ
        assert _SUFFIX_TO_OP['__gt'] == FilterOp.GT
        assert _SUFFIX_TO_OP['__gte'] == FilterOp.GTE
        assert _SUFFIX_TO_OP['__lt'] == FilterOp.LT
        assert _SUFFIX_TO_OP['__lte'] == FilterOp.LTE
        assert _SUFFIX_TO_OP['__contains'] == FilterOp.LIKE
        assert _SUFFIX_TO_OP['__startswith'] == FilterOp.LIKE
        assert _SUFFIX_TO_OP['__in'] == FilterOp.IN
        assert _SUFFIX_TO_OP['__ne'] == FilterOp.NE


# ==================== 批量操作测试 ====================

class TestBatchOperations:
    """批量操作优化测试"""

    def test_add_batch_basic(self, task_repo):
        """批量添加基本功能"""
        tasks = []
        for i in range(10):
            tasks.append(Task(
                id=f"BATCH-{i:03d}",
                name=f"批量任务 {i}",
                priority=TaskPriority.P1,
            ))
        
        count = task_repo.add_batch(tasks)
        assert count == 10
        
        # 验证数据
        for i in range(10):
            t = task_repo.get(f"BATCH-{i:03d}")
            assert t is not None
            assert t.name == f"批量任务 {i}"

    def test_add_batch_empty(self, task_repo):
        """空列表不报错"""
        count = task_repo.add_batch([])
        assert count == 0

    def test_add_batch_large(self, task_repo):
        """大批量添加 (>100 触发分批)"""
        tasks = []
        for i in range(250):
            tasks.append(Task(
                id=f"LARGE-{i:03d}",
                name=f"大批量任务 {i}",
                priority=TaskPriority.P2,
            ))
        
        count = task_repo.add_batch(tasks)
        assert count == 250
        
        # 验证所有数据
        total = task_repo.count()
        assert total >= 250

    def test_update_batch(self, task_repo):
        """批量更新"""
        # 先批量添加
        tasks = []
        for i in range(5):
            tasks.append(Task(id=f"UB-{i}", name=f"原始{i}", priority=TaskPriority.P2))
        task_repo.add_batch(tasks)
        
        # 批量更新
        for t in tasks:
            t.name = f"更新{t.id}"
            t.priority = TaskPriority.P0
        count = task_repo.update_batch(tasks)
        assert count == 5
        
        # 验证
        t = task_repo.get("UB-0")
        assert t.name == "更新UB-0"
        assert t.priority == TaskPriority.P0

    def test_delete_batch(self, task_repo):
        """批量删除"""
        tasks = [Task(id=f"DB-{i}", name=f"删除{i}") for i in range(5)]
        task_repo.add_batch(tasks)
        
        count = task_repo.delete_batch([f"DB-{i}" for i in range(3)])
        assert count == 3
        
        assert task_repo.get("DB-0") is None
        assert task_repo.get("DB-3") is not None

    def test_add_batch_single_field_consistency(self, memory_repo):
        """批量添加字段一致性"""
        memories = []
        for i in range(5):
            memories.append(Memory(
                id=f"BF-{i}",
                memory_type=MemoryType.FACTUAL,
                key=f"batch.{i}",
                value=f"batch value {i}",
            ))
        
        count = memory_repo.add_batch(memories)
        assert count == 5
        
        m = memory_repo.get_by_key("batch.0")
        assert m is not None
        assert m.value == "batch value 0"


# ==================== 向后兼容性测试 ====================

class TestBackwardCompatibility:
    """向后兼容性测试"""

    def test_get_all_still_works(self, memory_repo, seed_memories):
        """get_all 旧 API 仍然可用"""
        results = memory_repo.get_all(
            filters={'memory_type': MemoryType.FACTUAL.value},
            order_by='created_at DESC',
            limit=5
        )
        assert len(results) <= 5
        assert all(isinstance(m, Memory) for m in results)

    def test_count_still_works(self, memory_repo, seed_memories):
        """count 旧 API 仍然可用"""
        total = memory_repo.count()
        assert total == len(seed_memories)

    def test_exists_still_works(self, memory_repo, seed_memories):
        """exists 旧 API 仍然可用"""
        assert memory_repo.exists("mem-000") is True
        assert memory_repo.exists("__nonexistent__") is False

    def test_get_by_ids_still_works(self, memory_repo, seed_memories):
        """get_by_ids 旧 API 仍然可用"""
        results = memory_repo.get_by_ids(["mem-000", "mem-001", "__nope__"])
        assert len(results) == 2

    def test_add_update_delete_still_works(self, task_repo):
        """add/update/delete 旧 API 仍然可用"""
        task = Task(id="COMPAT-1", name="兼容测试", priority=TaskPriority.P1)
        task_repo.add(task)
        
        task.name = "更新后"
        task_repo.update(task)
        
        fetched = task_repo.get("COMPAT-1")
        assert fetched.name == "更新后"
        
        assert task_repo.delete("COMPAT-1") is True
        assert task_repo.get("COMPAT-1") is None

    def test_delete_all_still_works(self, memory_repo):
        """delete_all 旧 API 仍然可用"""
        memory_repo.add(Memory(
            id="DA-1", memory_type=MemoryType.WORKING,
            key="del.key", value="del val"
        ))
        memory_repo.add(Memory(
            id="DA-2", memory_type=MemoryType.WORKING,
            key="del.key2", value="del val2"
        ))
        
        count = memory_repo.delete_all(filters={'memory_type': MemoryType.WORKING.value})
        assert count >= 2


# ==================== Task Repository query() 测试 ====================

class TestTaskQueryBuilder:
    """Task 仓储 QueryBuilder 测试"""

    def test_query_by_status(self, task_repo):
        """通过 QueryBuilder 按状态查询"""
        task_repo.add(Task(id="TQ-1", name="待处理", priority=TaskPriority.P0))
        task_repo.add(Task(id="TQ-2", name="已完成", priority=TaskPriority.P1))
        task_repo.update_status("TQ-2", TaskStatus.COMPLETED)
        
        pending = task_repo.query().filter(status=TaskStatus.PENDING.value).all()
        assert any(t.id == "TQ-1" for t in pending)
        assert not any(t.id == "TQ-2" for t in pending)

    def test_query_by_priority(self, task_repo):
        """通过 QueryBuilder 按优先级查询"""
        task_repo.add(Task(id="TP-1", name="紧急", priority=TaskPriority.P0))
        task_repo.add(Task(id="TP-2", name="普通", priority=TaskPriority.P2))
        
        urgent = task_repo.query().filter(priority=TaskPriority.P0.value).all()
        assert len(urgent) >= 1
        assert all(t.priority == TaskPriority.P0 for t in urgent)

    def test_query_order_by(self, task_repo):
        """通过 QueryBuilder 排序"""
        task_repo.add(Task(id="TO-1", name="P0任务", priority=TaskPriority.P0))
        task_repo.add(Task(id="TO-2", name="P3任务", priority=TaskPriority.P3))
        
        results = task_repo.query().order_by('priority').all()
        assert len(results) >= 2


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
