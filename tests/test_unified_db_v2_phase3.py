"""
UnifiedDB V2 - Phase 3 单元测试

测试覆盖:
- UnifiedDB Facade: 统一 API
- V1 API 兼容性
- 组件集成

目标: 100% 代码覆盖率
"""

import os
import sys
import pytest
import tempfile
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from quickagents.core.unified_db import UnifiedDB, get_unified_db, reset_global_db
from quickagents.core.repositories.models import (
    MemoryType,
    TaskStatus,
    TaskPriority,
    FeedbackType
)


# ==================== Fixtures ====================

@pytest.fixture
def temp_db_path():
    """临时数据库路径"""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        yield os.path.join(tmpdir, "test.db")


@pytest.fixture
def unified_db(temp_db_path):
    """UnifiedDB 实例"""
    db = UnifiedDB(temp_db_path)
    yield db
    db.close()


# ==================== 初始化测试 ====================

class TestUnifiedDBInit:
    """UnifiedDB 初始化测试"""
    
    def test_init(self, temp_db_path):
        """测试初始化"""
        db = UnifiedDB(temp_db_path)
        
        assert db.db_path == Path(temp_db_path)
        assert db.connection_manager is not None
        assert db.transaction_manager is not None
        assert db.migration_manager is not None
        
        db.close()
    
    def test_auto_migration(self, temp_db_path):
        """测试自动迁移"""
        db = UnifiedDB(temp_db_path)
        
        # 验证表已创建
        with db.connection_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='memory'"
            )
            assert cursor.fetchone() is not None
        
        db.close()
    
    def test_context_manager(self, temp_db_path):
        """测试上下文管理器"""
        with UnifiedDB(temp_db_path) as db:
            assert db.health_check() is True
    
    def test_health_check(self, unified_db):
        """测试健康检查"""
        assert unified_db.health_check() is True
    
    def test_repr(self, unified_db):
        """测试字符串表示"""
        repr_str = repr(unified_db)
        assert "UnifiedDB" in repr_str


# ==================== 记忆 API 测试 ====================

class TestMemoryAPI:
    """记忆 API 测试"""
    
    def test_set_memory(self, unified_db):
        """测试设置记忆"""
        result = unified_db.set_memory(
            key="test.key",
            value="test value",
            memory_type=MemoryType.FACTUAL
        )
        
        assert result is not None
        assert result.key == "test.key"
        assert result.value == '"test value"' or result.value == "test value"
    
    def test_get_memory(self, unified_db):
        """测试获取记忆"""
        unified_db.set_memory("get.key", "get value")
        
        result = unified_db.get_memory("get.key")
        
        assert result == '"get value"' or result == "get value"
    
    def test_get_memory_not_found(self, unified_db):
        """测试获取不存在的记忆"""
        result = unified_db.get_memory("not.exist")
        
        assert result is None
    
    def test_get_memory_with_default(self, unified_db):
        """测试获取记忆（带默认值）"""
        result = unified_db.get_memory("not.exist", default="default")
        
        assert result == "default"
    
    def test_search_memory(self, unified_db):
        """测试搜索记忆"""
        unified_db.set_memory("search.1", "authentication module")
        unified_db.set_memory("search.2", "authorization module")
        
        results = unified_db.search_memory("auth")
        
        assert len(results) >= 2
    
    def test_delete_memory(self, unified_db):
        """测试删除记忆"""
        unified_db.set_memory("delete.key", "delete value")
        
        result = unified_db.delete_memory("delete.key")
        assert result is True
        
        # 验证已删除
        deleted = unified_db.get_memory("delete.key")
        assert deleted is None
    
    def test_get_memories_by_type(self, unified_db):
        """测试按类型获取记忆"""
        unified_db.set_memory("type.factual", "factual value", MemoryType.FACTUAL)
        unified_db.set_memory("type.working", "working value", MemoryType.WORKING)
        
        results = unified_db.get_memories_by_type(MemoryType.FACTUAL)
        
        assert len(results) >= 1
        assert all(m.memory_type == MemoryType.FACTUAL for m in results)
    
    def test_set_memory_with_category(self, unified_db):
        """测试设置记忆（带分类）"""
        result = unified_db.set_memory(
            key="category.key",
            value="category value",
            memory_type=MemoryType.FACTUAL,
            category="test-category"
        )
        
        assert result.category == "test-category"
    
    def test_set_memory_with_importance(self, unified_db):
        """测试设置记忆（带重要性）"""
        result = unified_db.set_memory(
            key="importance.key",
            value="important value",
            importance_score=0.9
        )
        
        assert result.importance_score == 0.9


# ==================== 任务 API 测试 ====================

class TestTaskAPI:
    """任务 API 测试"""
    
    def test_add_task(self, unified_db):
        """测试添加任务"""
        result = unified_db.add_task(
            task_id="TASK-001",
            name="实现认证",
            priority="P0"
        )
        
        assert result.id == "TASK-001"
        assert result.name == "实现认证"
        assert result.priority == TaskPriority.P0
    
    def test_get_task(self, unified_db):
        """测试获取任务"""
        unified_db.add_task("TASK-002", "测试任务")
        
        result = unified_db.get_task("TASK-002")
        
        assert result is not None
        assert result.name == "测试任务"
    
    def test_update_task_status(self, unified_db):
        """测试更新任务状态"""
        unified_db.add_task("TASK-003", "状态任务")
        
        result = unified_db.update_task_status("TASK-003", "in_progress")
        
        assert result.status == TaskStatus.IN_PROGRESS
        assert result.start_time is not None
    
    def test_complete_task(self, unified_db):
        """测试完成任务"""
        unified_db.add_task("TASK-004", "完成任务")
        unified_db.update_task_status("TASK-004", "in_progress")
        
        result = unified_db.complete_task("TASK-004")
        
        assert result.status == TaskStatus.COMPLETED
        assert result.end_time is not None
    
    def test_block_task(self, unified_db):
        """测试阻塞任务"""
        unified_db.add_task("TASK-005", "阻塞任务")
        unified_db.update_task_status("TASK-005", "in_progress")
        
        result = unified_db.block_task("TASK-005", "等待依赖")
        
        assert result.status == TaskStatus.BLOCKED
    
    def test_get_tasks(self, unified_db):
        """测试获取任务列表"""
        unified_db.add_task("TASK-006", "任务6", priority="P0")
        unified_db.add_task("TASK-007", "任务7", priority="P1")
        
        results = unified_db.get_tasks()
        
        assert len(results) >= 2
    
    def test_get_pending_tasks(self, unified_db):
        """测试获取待处理任务"""
        unified_db.add_task("TASK-008", "待处理任务")
        unified_db.add_task("TASK-009", "已完成任务")
        unified_db.complete_task("TASK-009")
        
        results = unified_db.get_pending_tasks()
        
        assert all(t.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS) for t in results)
    
    def test_get_next_task(self, unified_db):
        """测试获取下一个任务"""
        unified_db.add_task("TASK-010", "低优先级", priority="P3")
        unified_db.add_task("TASK-011", "高优先级", priority="P0")
        
        result = unified_db.get_next_task()
        
        assert result.priority == TaskPriority.P0


# ==================== 进度 API 测试 ====================

class TestProgressAPI:
    """进度 API 测试"""
    
    def test_init_progress(self, unified_db):
        """测试初始化进度"""
        result = unified_db.init_progress("test-project", total_tasks=10)
        
        assert result.project_name == "test-project"
        assert result.total_tasks == 10
        assert result.completed_tasks == 0
    
    def test_get_progress(self, unified_db):
        """测试获取进度"""
        unified_db.init_progress("progress-project")
        
        result = unified_db.get_progress("progress-project")
        
        assert result is not None
        assert result.project_name == "progress-project"
    
    def test_update_progress(self, unified_db):
        """测试更新进度"""
        unified_db.init_progress("update-project", total_tasks=5)
        
        result = unified_db.update_progress(
            "update-project",
            current_task="TASK-001",
            completed_increment=1
        )
        
        assert result.current_task == "TASK-001"
        assert result.completed_tasks == 1
    
    def test_increment_progress(self, unified_db):
        """测试增加进度"""
        unified_db.init_progress("increment-project", total_tasks=5)
        
        unified_db.increment_progress("increment-project")
        unified_db.increment_progress("increment-project")
        
        result = unified_db.get_progress("increment-project")
        
        assert result.completed_tasks == 2
    
    def test_save_checkpoint(self, unified_db):
        """测试保存检查点"""
        unified_db.init_progress("checkpoint-project")
        
        result = unified_db.save_checkpoint("checkpoint-project", "Phase 1 完成")
        
        assert result.last_checkpoint == "Phase 1 完成"


# ==================== 反馈 API 测试 ====================

class TestFeedbackAPI:
    """反馈 API 测试"""
    
    def test_add_feedback(self, unified_db):
        """测试添加反馈"""
        result = unified_db.add_feedback(
            feedback_type="bug",
            title="发现一个bug",
            description="详细描述",
            project_name="test-project"
        )
        
        assert result is not None
        assert result.feedback_type == FeedbackType.BUG
        assert result.title == "发现一个bug"
    
    def test_get_feedbacks(self, unified_db):
        """测试获取反馈列表"""
        unified_db.add_feedback("bug", "Bug 1")
        unified_db.add_feedback("improvement", "改进 1")
        
        results = unified_db.get_feedbacks()
        
        assert len(results) >= 2
    
    def test_get_feedbacks_by_type(self, unified_db):
        """测试按类型获取反馈"""
        unified_db.add_feedback("bug", "Bug 2")
        unified_db.add_feedback("improvement", "改进 2")
        
        results = unified_db.get_feedbacks(feedback_type="bug")
        
        assert all(f.feedback_type == FeedbackType.BUG for f in results)


# ==================== 统计 API 测试 ====================

class TestStatsAPI:
    """统计 API 测试"""
    
    def test_get_stats(self, unified_db):
        """测试获取统计"""
        # 添加一些数据
        unified_db.set_memory("stats.key", "stats value")
        unified_db.add_task("STATS-001", "统计任务")
        unified_db.add_feedback("bug", "统计反馈")
        
        stats = unified_db.get_stats()
        
        assert "memory" in stats
        assert "tasks" in stats
        assert "progress" in stats
        assert "feedback" in stats
        
        assert stats["memory"]["total"] >= 1
        assert stats["tasks"]["total"] >= 1
        assert stats["feedback"]["total"] >= 1


# ==================== 全局实例测试 ====================

class TestGlobalInstance:
    """全局实例测试"""
    
    def test_get_unified_db(self, temp_db_path):
        """测试获取全局实例"""
        reset_global_db()
        
        db1 = get_unified_db(temp_db_path)
        db2 = get_unified_db(temp_db_path)
        
        assert db1 is db2
        
        reset_global_db()
    
    def test_reset_global_db(self, temp_db_path):
        """测试重置全局实例"""
        db1 = get_unified_db(temp_db_path)
        
        reset_global_db()
        
        db2 = get_unified_db(temp_db_path)
        
        assert db1 is not db2
        
        reset_global_db()


# ==================== V1 兼容性测试 ====================

class TestV1Compatibility:
    """V1 API 兼容性测试"""
    
    def test_memory_operations(self, unified_db):
        """测试记忆操作（V1兼容）"""
        # V1 风格
        unified_db.set_memory("v1.key", "v1 value")
        result = unified_db.get_memory("v1.key")
        
        assert result is not None
    
    def test_task_operations(self, unified_db):
        """测试任务操作（V1兼容）"""
        # V1 风格
        unified_db.add_task("V1-001", "V1任务")
        unified_db.update_task_status("V1-001", "in_progress")
        
        task = unified_db.get_task("V1-001")
        
        assert task.status == TaskStatus.IN_PROGRESS
    
    def test_progress_operations(self, unified_db):
        """测试进度操作（V1兼容）"""
        # V1 风格
        unified_db.init_progress("v1-project", total_tasks=5)
        unified_db.increment_progress("v1-project")
        
        progress = unified_db.get_progress("v1-project")
        
        assert progress.completed_tasks == 1


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
