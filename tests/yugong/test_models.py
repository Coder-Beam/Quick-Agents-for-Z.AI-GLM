"""
愚公循环数据模型单元测试

测试覆盖:
- UserStory: 创建、序列化、反序列化
- LoopResult: 创建、字段验证
- LoopState: 状态转换、序列化
- ParsedRequirement: 需求解析结果
"""

import pytest
from datetime import datetime
from quickagents.yugong.models import (
    UserStory,
    LoopResult,
    LoopState,
    ParsedRequirement,
    StoryPriority,
    StoryStatus,
)


class TestUserStory:
    """UserStory 数据模型测试"""

    def test_create_minimal_user_story(self):
        """测试创建最小化的 UserStory"""
        story = UserStory(
            id="US-001",
            title="添加用户认证",
            description="实现JWT认证功能",
        )

        assert story.id == "US-001"
        assert story.title == "添加用户认证"
        assert story.description == "实现JWT认证功能"
        assert story.priority == StoryPriority.MEDIUM
        assert story.status == StoryStatus.PENDING
        assert story.passes is False
        assert story.attempts == 0
        assert story.max_attempts == 3

    def test_create_full_user_story(self):
        """测试创建完整字段的 UserStory"""
        story = UserStory(
            id="US-002",
            title="数据库迁移",
            description="创建用户表",
            acceptance_criteria=["表已创建", "索引已添加"],
            priority=StoryPriority.HIGH,
            dependencies=["US-001"],
            estimated_complexity="medium",
            tags=["database", "migration"],
            category="backend",
            max_attempts=5,
        )

        assert story.id == "US-002"
        assert story.priority == StoryPriority.HIGH
        assert story.dependencies == ["US-001"]
        assert story.acceptance_criteria == ["表已创建", "索引已添加"]
        assert story.tags == ["database", "migration"]

    def test_user_story_to_dict(self):
        """测试 UserStory 序列化为字典"""
        story = UserStory(
            id="US-003",
            title="API端点",
            description="创建REST API",
            acceptance_criteria=["返回200"],
        )

        data = story.to_dict()

        assert data["id"] == "US-003"
        assert data["title"] == "API端点"
        assert data["acceptance_criteria"] == ["返回200"]
        assert "created_at" in data
        assert "updated_at" in data

    def test_user_story_from_dict(self):
        """测试从字典反序列化 UserStory"""
        data = {
            "id": "US-004",
            "title": "测试功能",
            "description": "编写单元测试",
            "acceptance_criteria": ["覆盖率>=80%"],
            "priority": 1,
            "passes": True,
            "notes": "已完成",
            "attempts": 2,
        }

        story = UserStory.from_dict(data)

        assert story.id == "US-004"
        assert story.passes is True
        assert story.attempts == 2
        assert story.notes == "已完成"

    def test_user_story_increment_attempts(self):
        """测试增加尝试次数"""
        story = UserStory(id="US-005", title="测试", description="测试")

        story.increment_attempts()
        assert story.attempts == 1

        story.increment_attempts()
        assert story.attempts == 2

    def test_user_story_can_retry(self):
        """测试是否可以重试"""
        story = UserStory(id="US-006", title="测试", description="测试", max_attempts=3)

        assert story.can_retry() is True

        story.attempts = 3
        assert story.can_retry() is False

    def test_user_story_mark_passed(self):
        """测试标记为通过"""
        story = UserStory(id="US-007", title="测试", description="测试")

        story.mark_passed("学到了重要经验")

        assert story.passes is True
        assert story.status == StoryStatus.PASSED
        assert story.notes == "学到了重要经验"
        assert story.completed_at is not None

    def test_user_story_mark_failed(self):
        """测试标记为失败"""
        story = UserStory(id="US-008", title="测试", description="测试")

        story.mark_failed("测试失败原因")

        assert story.passes is False
        assert story.status == StoryStatus.FAILED
        assert "测试失败原因" in story.error_log


class TestLoopResult:
    """LoopResult 数据模型测试"""

    def test_create_loop_result_success(self):
        """测试创建成功的迭代结果"""
        result = LoopResult(
            iteration=1,
            story_id="US-001",
            success=True,
            output="任务完成",
            duration_ms=5000,
            token_usage={"input": 1000, "output": 500, "total": 1500},
            files_changed=["src/main.py", "tests/test_main.py"],
        )

        assert result.iteration == 1
        assert result.success is True
        assert result.output == "任务完成"
        assert result.duration_ms == 5000
        assert result.token_usage["total"] == 1500
        assert len(result.files_changed) == 2
        assert result.error is None

    def test_create_loop_result_failure(self):
        """测试创建失败的迭代结果"""
        result = LoopResult(
            iteration=2,
            story_id="US-002",
            success=False,
            output="执行失败",
            duration_ms=3000,
            token_usage={"input": 500, "output": 200, "total": 700},
            files_changed=[],
            error="TypeError: 'NoneType' object",
        )

        assert result.success is False
        assert result.error == "TypeError: 'NoneType' object"

    def test_loop_result_to_dict(self):
        """测试 LoopResult 序列化"""
        result = LoopResult(
            iteration=3,
            story_id="US-003",
            success=True,
            output="完成",
            duration_ms=1000,
            token_usage={"total": 500},
            files_changed=["a.py"],
        )

        data = result.to_dict()

        assert data["iteration"] == 3
        assert data["story_id"] == "US-003"
        assert "timestamp" in data


class TestLoopState:
    """LoopState 数据模型测试"""

    def test_create_initial_loop_state(self):
        """测试创建初始循环状态"""
        state = LoopState()

        assert state.status == "idle"
        assert state.current_iteration == 0
        assert state.current_story is None
        assert state.total_stories == 0
        assert state.completed_stories == 0
        assert state.token_budget_used == 0

    def test_loop_state_with_stories(self):
        """测试带有Story的状态"""
        story = UserStory(id="US-001", title="测试", description="测试")
        state = LoopState(
            status="running",
            current_iteration=5,
            current_story=story,
            total_stories=10,
            completed_stories=3,
        )

        assert state.status == "running"
        assert state.current_iteration == 5
        assert state.current_story.id == "US-001"
        assert state.progress_percentage == 30.0

    def test_loop_state_progress_percentage(self):
        """测试进度百分比计算"""
        state = LoopState(total_stories=10, completed_stories=5)
        assert state.progress_percentage == 50.0

        state = LoopState(total_stories=0, completed_stories=0)
        assert state.progress_percentage == 0.0

    def test_loop_state_to_dict(self):
        """测试 LoopState 序列化"""
        state = LoopState(
            status="running",
            current_iteration=3,
            total_stories=5,
            completed_stories=2,
        )

        data = state.to_dict()

        assert data["status"] == "running"
        assert data["current_iteration"] == 3
        assert data["total_stories"] == 5
        assert data["completed_stories"] == 2
        assert "start_time" in data
        assert "last_update" in data

    def test_loop_state_elapsed_seconds(self):
        """测试运行时间计算"""
        state = LoopState()

        # 刚创建时，运行时间应该接近0
        elapsed = state.elapsed_seconds
        assert elapsed >= 0
        assert elapsed < 1  # 小于1秒


class TestParsedRequirement:
    """ParsedRequirement 数据模型测试"""

    def test_create_parsed_requirement(self):
        """测试创建解析后的需求"""
        stories = [
            UserStory(id="US-001", title="功能1", description="描述1"),
            UserStory(id="US-002", title="功能2", description="描述2"),
        ]

        req = ParsedRequirement(
            project_name="测试项目",
            branch_name="yugong/test-feature",
            description="这是一个测试项目",
            user_stories=stories,
            raw_source="# 测试项目\n...",
            format="markdown",
        )

        assert req.project_name == "测试项目"
        assert req.branch_name == "yugong/test-feature"
        assert len(req.user_stories) == 2
        assert req.format == "markdown"

    def test_parsed_requirement_to_dict(self):
        """测试 ParsedRequirement 序列化"""
        req = ParsedRequirement(
            project_name="项目A",
            branch_name="yugong/a",
            description="描述",
            user_stories=[],
            raw_source="原始内容",
            format="json",
        )

        data = req.to_dict()

        assert data["project_name"] == "项目A"
        assert data["format"] == "json"
        assert data["user_stories"] == []
