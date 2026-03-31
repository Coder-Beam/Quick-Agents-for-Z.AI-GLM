"""
UnifiedDB V2 - Phase 2 单元测试

测试覆盖:
- BaseRepository: CRUD 操作
- MemoryRepository: 记忆操作
- TaskRepository: 任务操作
- ProgressRepository: 进度操作
- FeedbackRepository: 反馈操作

目标: 100% 代码覆盖率
"""

import os
import sys
import pytest
import tempfile
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from quickagents.core.connection_manager import ConnectionManager
from quickagents.core.transaction_manager import TransactionManager
from quickagents.core.migration_manager import MigrationManager
from quickagents.core.repositories.base import BaseRepository
from quickagents.core.repositories.memory_repo import MemoryRepository
from quickagents.core.repositories.task_repo import TaskRepository
from quickagents.core.repositories.progress_repo import ProgressRepository
from quickagents.core.repositories.feedback_repo import FeedbackRepository
from quickagents.core.repositories.models import (
    Memory, MemoryType,
    Task, TaskStatus, TaskPriority,
    Progress,
    Feedback, FeedbackType,
    SearchResult, RetrievalConfig
)


# ==================== Fixtures ====================

@pytest.fixture
def temp_db_path():
    """临时数据库路径"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield os.path.join(tmpdir, "test.db")


@pytest.fixture
def connection_manager(temp_db_path):
    """连接管理器"""
    mgr = ConnectionManager(temp_db_path, pool_size=2)
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


@pytest.fixture
def memory_repo(connection_manager, transaction_manager, migration_manager):
    """记忆仓储"""
    # 执行迁移
    migration_manager.migrate()
    return MemoryRepository(connection_manager, transaction_manager)


@pytest.fixture
def task_repo(connection_manager, transaction_manager, migration_manager):
    """任务仓储"""
    migration_manager.migrate()
    return TaskRepository(connection_manager, transaction_manager)


@pytest.fixture
def progress_repo(connection_manager, transaction_manager, migration_manager):
    """进度仓储"""
    migration_manager.migrate()
    return ProgressRepository(connection_manager, transaction_manager)


@pytest.fixture
def feedback_repo(connection_manager, transaction_manager, migration_manager):
    """反馈仓储"""
    migration_manager.migrate()
    return FeedbackRepository(connection_manager, transaction_manager)


# ==================== MemoryRepository Tests ====================

class TestMemoryRepository:
    """MemoryRepository 测试"""
    
    def test_add(self, memory_repo):
        """测试添加记忆"""
        memory = Memory(
            id="mem-1",
            memory_type=MemoryType.FACTUAL,
            key="test.key",
            value="test value"
        )
        
        result = memory_repo.add(memory)
        
        assert result.id == "mem-1"
        assert result.key == "test.key"
        assert result.value == "test value"
        assert result.content_hash is not None
    
    def test_get(self, memory_repo):
        """测试获取记忆"""
        memory = Memory(
            id="mem-2",
            memory_type=MemoryType.FACTUAL,
            key="get.test",
            value="get value"
        )
        memory_repo.add(memory)
        
        result = memory_repo.get("mem-2")
        
        assert result is not None
        assert result.key == "get.test"
    
    def test_get_by_key(self, memory_repo):
        """测试按键名获取"""
        memory = Memory(
            id="mem-3",
            memory_type=MemoryType.FACTUAL,
            key="unique.key",
            value="unique value"
        )
        memory_repo.add(memory)
        
        result = memory_repo.get_by_key("unique.key")
        
        assert result is not None
        assert result.value == "unique value"
    
    def test_get_by_type(self, memory_repo):
        """测试按类型获取"""
        # 添加不同类型记忆
        memory_repo.add(Memory(
            id="mem-factual",
            memory_type=MemoryType.FACTUAL,
            key="factual.1",
            value="factual value"
        ))
        memory_repo.add(Memory(
            id="mem-working",
            memory_type=MemoryType.WORKING,
            key="working.1",
            value="working value"
        ))
        
        results = memory_repo.get_by_type(MemoryType.FACTUAL)
        
        assert len(results) >= 1
        assert all(m.memory_type == MemoryType.FACTUAL for m in results)
    
    def test_search(self, memory_repo):
        """测试搜索"""
        memory_repo.add(Memory(
            id="mem-search",
            memory_type=MemoryType.FACTUAL,
            key="search.test",
            value="authentication module"
        ))
        
        results = memory_repo.search("authentication")
        
        assert len(results) >= 1
        assert "authentication" in results[0].value.lower()
    
    def test_upsert(self, memory_repo):
        """测试插入或更新"""
        # 第一次：插入
        result1 = memory_repo.upsert("upsert.key", "value1", MemoryType.FACTUAL)
        assert result1.value == "value1"
        
        # 第二次：更新
        result2 = memory_repo.upsert("upsert.key", "value2", MemoryType.FACTUAL)
        assert result2.value == "value2"
        assert result2.id == result1.id
    
    def test_touch(self, memory_repo):
        """测试访问更新"""
        memory = Memory(
            id="mem-touch",
            memory_type=MemoryType.FACTUAL,
            key="touch.key",
            value="touch value"
        )
        memory_repo.add(memory)
        
        initial_count = memory_repo.get("mem-touch").access_count
        
        memory_repo.touch("mem-touch")
        
        result = memory_repo.get("mem-touch")
        assert result.access_count == initial_count + 1
    
    def test_delete(self, memory_repo):
        """测试删除"""
        memory = Memory(
            id="mem-delete",
            memory_type=MemoryType.FACTUAL,
            key="delete.key",
            value="delete value"
        )
        memory_repo.add(memory)
        
        result = memory_repo.delete("mem-delete")
        assert result is True
        
        # 验证已删除
        deleted = memory_repo.get("mem-delete")
        assert deleted is None


# ==================== TaskRepository Tests ====================

class TestTaskRepository:
    """TaskRepository 测试"""
    
    def test_add(self, task_repo):
        """测试添加任务"""
        task = Task(
            id="task-1",
            name="实现认证",
            priority=TaskPriority.P0
        )
        
        result = task_repo.add(task)
        
        assert result.id == "task-1"
        assert result.name == "实现认证"
        assert result.status == TaskStatus.PENDING
    
    def test_get_by_status(self, task_repo):
        """测试按状态获取"""
        task_repo.add(Task(id="t-pending", name="Pending Task", priority=TaskPriority.P2))
        task_repo.add(Task(id="t-completed", name="Completed Task", priority=TaskPriority.P2))
        task_repo.update_status("t-completed", TaskStatus.COMPLETED)
        
        pending = task_repo.get_by_status(TaskStatus.PENDING)
        completed = task_repo.get_by_status(TaskStatus.COMPLETED)
        
        assert any(t.id == "t-pending" for t in pending)
        assert any(t.id == "t-completed" for t in completed)
    
    def test_update_status(self, task_repo):
        """测试更新状态"""
        task_repo.add(Task(id="t-status", name="Status Task", priority=TaskPriority.P2))
        
        result = task_repo.update_status("t-status", TaskStatus.IN_PROGRESS)
        
        assert result.status == TaskStatus.IN_PROGRESS
        assert result.start_time is not None
    
    def test_complete_task(self, task_repo):
        """测试完成任务"""
        task_repo.add(Task(id="t-complete", name="Complete Task", priority=TaskPriority.P2))
        task_repo.update_status("t-complete", TaskStatus.IN_PROGRESS)
        
        result = task_repo.complete_task("t-complete")
        
        assert result.status == TaskStatus.COMPLETED
        assert result.end_time is not None
    
    def test_block_task(self, task_repo):
        """测试阻塞任务"""
        task_repo.add(Task(id="t-block", name="Block Task", priority=TaskPriority.P2))
        task_repo.update_status("t-block", TaskStatus.IN_PROGRESS)
        
        result = task_repo.block_task("t-block", "等待依赖")
        
        assert result.status == TaskStatus.BLOCKED
    
    def test_get_next_task(self, task_repo):
        """测试获取下一个任务"""
        task_repo.add(Task(id="t-next-1", name="Low Priority", priority=TaskPriority.P3))
        task_repo.add(Task(id="t-next-2", name="High Priority", priority=TaskPriority.P0))
        
        result = task_repo.get_next_task()
        
        assert result.priority == TaskPriority.P0
    
    def test_count_by_status(self, task_repo):
        """测试按状态统计"""
        task_repo.add(Task(id="t-count-1", name="Task 1", priority=TaskPriority.P2))
        task_repo.add(Task(id="t-count-2", name="Task 2", priority=TaskPriority.P2))
        task_repo.update_status("t-count-1", TaskStatus.COMPLETED)
        
        stats = task_repo.count_by_status()
        
        assert TaskStatus.COMPLETED.value in stats
        assert TaskStatus.PENDING.value in stats


# ==================== ProgressRepository Tests ====================

class TestProgressRepository:
    """ProgressRepository 测试"""
    
    def test_init_progress(self, progress_repo):
        """测试初始化进度"""
        result = progress_repo.init_progress("test-project", total_tasks=10)
        
        assert result.project_name == "test-project"
        assert result.total_tasks == 10
        assert result.completed_tasks == 0
    
    def test_increment_completed(self, progress_repo):
        """测试增加完成计数"""
        progress_repo.init_progress("increment-project", total_tasks=5)
        
        result = progress_repo.increment_completed("increment-project")
        
        assert result.completed_tasks == 1
    
    def test_update_current_task(self, progress_repo):
        """测试更新当前任务"""
        progress_repo.init_progress("current-task-project")
        
        result = progress_repo.update_current_task("current-task-project", "TASK-001")
        
        assert result.current_task == "TASK-001"
    
    def test_save_checkpoint(self, progress_repo):
        """测试保存检查点"""
        progress_repo.init_progress("checkpoint-project")
        
        result = progress_repo.save_checkpoint("checkpoint-project", "Phase 1 完成")
        
        assert result.last_checkpoint == "Phase 1 完成"
    
    def test_percentage(self, progress_repo):
        """测试进度百分比"""
        progress = Progress(
            id="progress-test",
            project_name="percentage-test",
            total_tasks=10,
            completed_tasks=3
        )
        
        assert progress.percentage == 30.0
        assert progress.remaining_tasks == 7


# ==================== FeedbackRepository Tests ====================

class TestFeedbackRepository:
    """FeedbackRepository 测试"""
    
    def test_add_feedback(self, feedback_repo):
        """测试添加反馈"""
        result = feedback_repo.add_feedback(
            feedback_type=FeedbackType.BUG,
            title="发现一个bug",
            description="详细描述",
            project_name="test-project"
        )
        
        assert result.id is not None
        assert result.feedback_type == FeedbackType.BUG
        assert result.title == "发现一个bug"
    
    def test_get_by_type(self, feedback_repo):
        """测试按类型获取"""
        feedback_repo.add_feedback(FeedbackType.BUG, "Bug 1")
        feedback_repo.add_feedback(FeedbackType.IMPROVEMENT, "改进 1")
        
        bugs = feedback_repo.get_by_type(FeedbackType.BUG)
        
        assert len(bugs) >= 1
        assert all(f.feedback_type == FeedbackType.BUG for f in bugs)
    
    def test_get_by_project(self, feedback_repo):
        """测试按项目获取"""
        feedback_repo.add_feedback(
            FeedbackType.BUG,
            "Bug for project A",
            project_name="project-a"
        )
        feedback_repo.add_feedback(
            FeedbackType.BUG,
            "Bug for project B",
            project_name="project-b"
        )
        
        results = feedback_repo.get_by_project("project-a")
        
        assert len(results) >= 1
        assert all(f.project_name == "project-a" for f in results)
    
    def test_search(self, feedback_repo):
        """测试搜索反馈"""
        feedback_repo.add_feedback(FeedbackType.BUG, "认证模块报错")
        
        results = feedback_repo.search("认证")
        
        assert len(results) >= 1
    
    def test_count_by_type(self, feedback_repo):
        """测试按类型统计"""
        feedback_repo.add_feedback(FeedbackType.BUG, "Bug 1")
        feedback_repo.add_feedback(FeedbackType.BUG, "Bug 2")
        feedback_repo.add_feedback(FeedbackType.IMPROVEMENT, "改进 1")
        
        stats = feedback_repo.count_by_type()
        
        assert stats.get(FeedbackType.BUG.value, 0) >= 2
        assert stats.get(FeedbackType.IMPROVEMENT.value, 0) >= 1


# ==================== Integration Tests ====================

class TestRepositoryIntegration:
    """Repository 集成测试"""
    
    def test_full_workflow(self, temp_db_path):
        """测试完整工作流"""
        # 1. 初始化组件
        conn_mgr = ConnectionManager(temp_db_path)
        tx_mgr = TransactionManager(conn_mgr)
        mig_mgr = MigrationManager(conn_mgr)
        
        # 2. 执行迁移
        mig_mgr.migrate()
        
        # 3. 创建仓储
        memory_repo = MemoryRepository(conn_mgr, tx_mgr)
        task_repo = TaskRepository(conn_mgr, tx_mgr)
        
        # 4. 添加记忆
        memory = Memory(
            id="workflow-memory",
            memory_type=MemoryType.FACTUAL,
            key="project.name",
            value="QuickAgents"
        )
        memory_repo.add(memory)
        
        # 5. 添加任务
        task = Task(
            id="workflow-task",
            name="实现功能",
            priority=TaskPriority.P0
        )
        task_repo.add(task)
        task_repo.update_status("workflow-task", TaskStatus.IN_PROGRESS)
        
        # 6. 验证
        mem_result = memory_repo.get_by_key("project.name")
        assert mem_result.value == "QuickAgents"
        
        task_result = task_repo.get("workflow-task")
        assert task_result.status == TaskStatus.IN_PROGRESS
        
        # 7. 清理
        conn_mgr.close_all()
    
    def test_transaction_rollback(self, temp_db_path):
        """测试事务回滚"""
        conn_mgr = ConnectionManager(temp_db_path)
        tx_mgr = TransactionManager(conn_mgr)
        mig_mgr = MigrationManager(conn_mgr)
        mig_mgr.migrate()
        
        memory_repo = MemoryRepository(conn_mgr, tx_mgr)
        
        # 先添加一条数据
        memory_repo.add(Memory(
            id="rollback-test",
            memory_type=MemoryType.FACTUAL,
            key="rollback.key",
            value="initial value"
        ))
        
        # 在事务中更新，然后回滚
        try:
            with tx_mgr.transaction() as conn:
                conn.execute(
                    "UPDATE memory SET value = ? WHERE id = ?",
                    ("updated value", "rollback-test")
                )
                # 故意抛出异常
                raise ValueError("Test rollback")
        except ValueError:
            pass
        
        # 验证数据已回滚
        result = memory_repo.get("rollback-test")
        assert result.value == "initial value"
        
        conn_mgr.close_all()


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
