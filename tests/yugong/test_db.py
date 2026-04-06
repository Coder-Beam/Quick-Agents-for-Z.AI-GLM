"""
YuGongDB 持久化层测试

覆盖设计文档 Section 24 定义的 7 张表:
- yugong_stories: UserStory 存储
- yugong_iterations: 迭代历史
- yugong_progress: 进度日志
- yugong_context: 待注入上下文
- yugong_state: 循环状态
- yugong_checkpoints: 检查点
- yugong_logs: 日志记录
"""

import json
import pytest
from datetime import datetime

from quickagents.yugong.models import (
    UserStory,
    StoryPriority,
    StoryStatus,
    LoopResult,
    LoopState,
    ParsedRequirement,
)
from quickagents.yugong.db import YuGongDB


@pytest.fixture
def db():
    """内存数据库实例"""
    return YuGongDB(":memory:")


@pytest.fixture
def sample_story():
    """示例 UserStory"""
    return UserStory(
        id="US-001",
        title="实现用户认证",
        description="实现 JWT 认证系统",
        acceptance_criteria=["用户可以登录", "返回 JWT token"],
        priority=StoryPriority.HIGH,
        dependencies=[],
        tags=["auth", "security"],
        category="backend",
        estimated_complexity="medium",
    )


@pytest.fixture
def sample_story_with_dep():
    """带依赖的 UserStory"""
    return UserStory(
        id="US-002",
        title="实现权限控制",
        description="基于角色的权限控制",
        dependencies=["US-001"],
        priority=StoryPriority.MEDIUM,
    )


@pytest.fixture
def sample_result():
    """示例 LoopResult"""
    return LoopResult(
        iteration=1,
        story_id="US-001",
        success=True,
        output="认证系统已实现",
        duration_ms=5000,
        token_usage={"input": 100, "output": 200, "total": 300},
        files_changed=["src/auth.py", "tests/test_auth.py"],
    )


@pytest.fixture
def sample_state():
    """示例 LoopState"""
    return LoopState(
        status="running",
        current_iteration=3,
        total_stories=5,
        completed_stories=2,
    )


# ================================================================
# Test 1: 数据库初始化 & 表创建
# ================================================================


class TestDBInit:
    def test_create_tables(self, db):
        """所有 7 张表应该被创建"""
        cursor = db._execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        expected = {
            "yugong_stories",
            "yugong_iterations",
            "yugong_progress",
            "yugong_context",
            "yugong_state",
            "yugong_checkpoints",
            "yugong_logs",
        }
        assert expected.issubset(tables), f"Missing tables: {expected - tables}"

    def test_can_reopen(self, tmp_path):
        """数据库可以被重新打开且保持数据"""
        db_path = str(tmp_path / "test.db")
        db1 = YuGongDB(db_path)
        db1.save_story(UserStory(id="US-001", title="test", description="desc"))
        db1.close()

        db2 = YuGongDB(db_path)
        story = db2.get_story("US-001")
        assert story is not None
        assert story.title == "test"
        db2.close()


# ================================================================
# Test 2: Story CRUD
# ================================================================


class TestStoryCRUD:
    def test_save_and_get(self, db, sample_story):
        """保存并读取 Story"""
        db.save_story(sample_story)
        loaded = db.get_story("US-001")
        assert loaded is not None
        assert loaded.id == "US-001"
        assert loaded.title == "实现用户认证"
        assert loaded.priority == StoryPriority.HIGH
        assert loaded.acceptance_criteria == ["用户可以登录", "返回 JWT token"]
        assert loaded.tags == ["auth", "security"]

    def test_get_nonexistent(self, db):
        """读取不存在的 Story 返回 None"""
        assert db.get_story("US-999") is None

    def test_update_story(self, db, sample_story):
        """更新 Story 状态"""
        db.save_story(sample_story)
        sample_story.mark_passed("完成")
        db.save_story(sample_story)

        loaded = db.get_story("US-001")
        assert loaded.status == StoryStatus.PASSED
        assert loaded.passes is True

    def test_get_all_stories(self, db, sample_story, sample_story_with_dep):
        """获取所有 Stories"""
        db.save_story(sample_story)
        db.save_story(sample_story_with_dep)
        stories = db.get_all_stories()
        assert len(stories) == 2

    def test_get_stories_by_status(self, db, sample_story, sample_story_with_dep):
        """按状态筛选 Stories"""
        db.save_story(sample_story)
        sample_story_with_dep.status = StoryStatus.RUNNING
        db.save_story(sample_story_with_dep)

        pending = db.get_stories_by_status(StoryStatus.PENDING)
        running = db.get_stories_by_status(StoryStatus.RUNNING)
        assert len(pending) == 1
        assert len(running) == 1

    def test_delete_story(self, db, sample_story):
        """删除 Story"""
        db.save_story(sample_story)
        db.delete_story("US-001")
        assert db.get_story("US-001") is None

    def test_count_stories(self, db, sample_story, sample_story_with_dep):
        """统计 Story 数量"""
        assert db.count_stories() == 0
        db.save_story(sample_story)
        assert db.count_stories() == 1
        db.save_story(sample_story_with_dep)
        assert db.count_stories() == 2


# ================================================================
# Test 3: Iteration 历史
# ================================================================


class TestIterations:
    def test_save_and_get(self, db, sample_result):
        """保存并读取迭代记录"""
        db.save_iteration(sample_result)
        iterations = db.get_iterations(story_id="US-001")
        assert len(iterations) == 1
        assert iterations[0].iteration == 1
        assert iterations[0].success is True
        assert iterations[0].duration_ms == 5000

    def test_get_all_iterations(self, db, sample_result):
        """获取所有迭代"""
        db.save_iteration(sample_result)
        r2 = LoopResult(
            iteration=2,
            story_id="US-002",
            success=True,
            output="",
            duration_ms=3000,
            token_usage={"total": 100},
        )
        db.save_iteration(r2)
        all_iters = db.get_iterations()
        assert len(all_iters) == 2

    def test_iteration_fields(self, db, sample_result):
        """验证迭代记录字段完整性"""
        db.save_iteration(sample_result)
        it = db.get_iterations(story_id="US-001")[0]
        assert it.files_changed == ["src/auth.py", "tests/test_auth.py"]
        assert it.token_usage == {"input": 100, "output": 200, "total": 300}

    def test_get_iterations_empty(self, db):
        """空数据库返回空列表"""
        assert db.get_iterations() == []


# ================================================================
# Test 4: 循环状态持久化
# ================================================================


class TestLoopState:
    def test_save_and_load(self, db, sample_state):
        """保存并加载循环状态"""
        db.save_state(sample_state)
        loaded = db.load_state()
        assert loaded is not None
        assert loaded.status == "running"
        assert loaded.current_iteration == 3
        assert loaded.total_stories == 5
        assert loaded.completed_stories == 2

    def test_overwrite_state(self, db, sample_state):
        """状态只保留最新一条"""
        db.save_state(sample_state)
        sample_state.status = "completed"
        sample_state.completed_stories = 5
        db.save_state(sample_state)

        loaded = db.load_state()
        assert loaded.status == "completed"
        assert loaded.completed_stories == 5

    def test_load_empty(self, db):
        """空数据库返回 None"""
        assert db.load_state() is None


# ================================================================
# Test 5: 检查点
# ================================================================


class TestCheckpoints:
    def test_create_and_get(self, db, sample_state):
        """创建并获取检查点"""
        db.save_checkpoint("story_complete", sample_state, story_id="US-001")
        checkpoints = db.get_checkpoints()
        assert len(checkpoints) == 1
        assert checkpoints[0]["type"] == "story_complete"
        assert checkpoints[0]["story_id"] == "US-001"

    def test_get_by_type(self, db, sample_state):
        """按类型获取检查点"""
        db.save_checkpoint("iteration", sample_state)
        db.save_checkpoint("story_complete", sample_state, story_id="US-001")
        results = db.get_checkpoints(checkpoint_type="story_complete")
        assert len(results) == 1

    def test_get_latest(self, db, sample_state):
        """获取最新检查点"""
        db.save_checkpoint("iteration", sample_state)
        sample_state.current_iteration = 5
        db.save_checkpoint("story_complete", sample_state, story_id="US-002")
        latest = db.get_latest_checkpoint()
        assert latest is not None
        assert latest["type"] == "story_complete"


# ================================================================
# Test 6: 日志
# ================================================================


class TestLogs:
    def test_add_and_get(self, db):
        """添加并获取日志"""
        db.add_log("INFO", "progress", "Story US-001 开始执行")
        db.add_log("WARN", "quality", "测试覆盖率不足", {"coverage": 45})
        logs = db.get_logs()
        assert len(logs) == 2

    def test_get_by_level(self, db):
        """按级别获取日志"""
        db.add_log("INFO", "progress", "msg1")
        db.add_log("ERROR", "error", "msg2")
        db.add_log("INFO", "progress", "msg3")
        info_logs = db.get_logs(level="INFO")
        assert len(info_logs) == 2

    def test_get_by_type(self, db):
        """按类型获取日志"""
        db.add_log("INFO", "decision", "选择 SQLite")
        db.add_log("INFO", "error", "导入失败")
        decision_logs = db.get_logs(log_type="decision")
        assert len(decision_logs) == 1

    def test_log_context(self, db):
        """验证日志上下文字段"""
        db.add_log("INFO", "progress", "msg", {"key": "value"})
        logs = db.get_logs()
        assert logs[0]["context"] == {"key": "value"}


# ================================================================
# Test 7: 进度日志
# ================================================================


class TestProgress:
    def test_add_and_get(self, db):
        """添加并获取进度日志"""
        db.add_progress("US-001", "开始实现认证")
        db.add_progress("US-001", "JWT 模块完成")
        entries = db.get_progress_entries(story_id="US-001")
        assert len(entries) == 2

    def test_get_all_progress(self, db):
        """获取所有进度"""
        db.add_progress("US-001", "msg1")
        db.add_progress("US-002", "msg2")
        all_entries = db.get_progress_entries()
        assert len(all_entries) == 2


# ================================================================
# Test 8: 上下文注入存储
# ================================================================


class TestContext:
    def test_add_and_get(self, db):
        """添加并获取待注入上下文"""
        db.add_context("项目使用 TypeScript + Vue3")
        db.add_context("测试覆盖率要求 >= 80%")
        contexts = db.get_pending_contexts()
        assert len(contexts) == 2

    def test_clear_context(self, db):
        """清空已使用的上下文"""
        db.add_context("ctx1")
        db.add_context("ctx2")
        db.clear_contexts()
        assert len(db.get_pending_contexts()) == 0


# ================================================================
# Test 9: 统计信息
# ================================================================


class TestStats:
    def test_empty_stats(self, db):
        """空数据库统计"""
        stats = db.get_stats()
        assert stats["total_stories"] == 0
        assert stats["total_iterations"] == 0
        assert stats["total_logs"] == 0

    def test_with_data(self, db, sample_story, sample_result):
        """有数据时的统计"""
        db.save_story(sample_story)
        db.save_iteration(sample_result)
        db.add_log("INFO", "progress", "msg")
        stats = db.get_stats()
        assert stats["total_stories"] == 1
        assert stats["total_iterations"] == 1
        assert stats["total_logs"] == 1
