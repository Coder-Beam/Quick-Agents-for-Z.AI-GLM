"""
愚公循环任务编排器测试

测试覆盖:
- Story CRUD (增删改查)
- Story 选择策略 (优先级 + 依赖)
- 进度统计
- 序列化/反序列化
"""

import pytest
from quickagents.yugong.task_orchestrator import TaskOrchestrator
from quickagents.yugong.models import (
    UserStory,
    StoryPriority,
    StoryStatus,
    ParsedRequirement,
)


def _story(
    sid: str,
    title: str = "",
    priority: StoryPriority = StoryPriority.MEDIUM,
    status: StoryStatus = StoryStatus.PENDING,
    dependencies: list[str] | None = None,
    max_attempts: int = 3,
    attempts: int = 0,
) -> UserStory:
    """快速创建测试用 Story"""
    s = UserStory(
        id=sid,
        title=title or f"Story {sid}",
        description=f"Description for {sid}",
        priority=priority,
        status=status,
        dependencies=dependencies or [],
        max_attempts=max_attempts,
    )
    s.attempts = attempts
    return s


class TestStoryCRUD:
    """Story 增删改查"""

    def test_add_and_get(self):
        orch = TaskOrchestrator()
        story = _story("US-001")
        orch.add_story(story)

        assert orch.get_story("US-001") is story
        assert orch.total_stories == 1

    def test_add_stories_batch(self):
        orch = TaskOrchestrator()
        stories = [_story("US-001"), _story("US-002"), _story("US-003")]
        orch.add_stories(stories)

        assert orch.total_stories == 3

    def test_get_nonexistent(self):
        orch = TaskOrchestrator()
        assert orch.get_story("US-999") is None

    def test_update_story(self):
        orch = TaskOrchestrator()
        orch.add_story(_story("US-001", title="Original"))

        updated = _story("US-001", title="Updated")
        orch.update_story(updated)

        assert orch.get_story("US-001").title == "Updated"

    def test_remove_story(self):
        orch = TaskOrchestrator()
        orch.add_story(_story("US-001"))
        orch.add_story(_story("US-002"))

        assert orch.remove_story("US-001") is True
        assert orch.total_stories == 1
        assert orch.remove_story("US-999") is False

    def test_load_from_requirement(self):
        orch = TaskOrchestrator()
        req = ParsedRequirement(
            project_name="test",
            branch_name="yugong/test",
            description="test project",
            user_stories=[_story("US-001"), _story("US-002")],
            raw_source="...",
            format="json",
        )
        orch.load_from_requirement(req)

        assert orch.total_stories == 2
        assert orch.get_story("US-001") is not None


class TestStorySelection:
    """Story 选择策略"""

    def test_select_highest_priority(self):
        orch = TaskOrchestrator()
        orch.add_stories(
            [
                _story("US-003", priority=StoryPriority.LOW),
                _story("US-001", priority=StoryPriority.CRITICAL),
                _story("US-002", priority=StoryPriority.HIGH),
            ]
        )

        next_story = orch.get_next_story()
        assert next_story.id == "US-001"
        assert next_story.priority == StoryPriority.CRITICAL

    def test_select_by_id_when_same_priority(self):
        orch = TaskOrchestrator()
        orch.add_stories(
            [
                _story("US-003", priority=StoryPriority.MEDIUM),
                _story("US-001", priority=StoryPriority.MEDIUM),
                _story("US-002", priority=StoryPriority.MEDIUM),
            ]
        )

        next_story = orch.get_next_story()
        assert next_story.id == "US-001"

    def test_skip_completed_stories(self):
        orch = TaskOrchestrator()
        orch.add_stories(
            [
                _story("US-001", status=StoryStatus.PASSED),
                _story("US-002", priority=StoryPriority.HIGH),
            ]
        )

        next_story = orch.get_next_story()
        assert next_story.id == "US-002"

    def test_retry_failed_story(self):
        orch = TaskOrchestrator()
        orch.add_stories(
            [
                _story("US-001", status=StoryStatus.FAILED, max_attempts=3, attempts=1),
            ]
        )

        next_story = orch.get_next_story()
        assert next_story is not None
        assert next_story.id == "US-001"

    def test_skip_failed_story_max_attempts(self):
        orch = TaskOrchestrator()
        orch.add_stories(
            [
                _story("US-001", status=StoryStatus.FAILED, max_attempts=3, attempts=3),
            ]
        )

        next_story = orch.get_next_story()
        assert next_story is None

    def test_dependency_blocks(self):
        orch = TaskOrchestrator()
        orch.add_stories(
            [
                _story("US-001", status=StoryStatus.PENDING),
                _story("US-002", dependencies=["US-001"]),
            ]
        )

        # US-002 blocked because US-001 is not PASSED
        next_story = orch.get_next_story()
        assert next_story.id == "US-001"

    def test_dependency_satisfied(self):
        orch = TaskOrchestrator()
        orch.add_stories(
            [
                _story("US-001", status=StoryStatus.PASSED),
                _story("US-002", dependencies=["US-001"]),
            ]
        )

        next_story = orch.get_next_story()
        assert next_story.id == "US-002"

    def test_no_executable_stories(self):
        orch = TaskOrchestrator()
        orch.add_stories(
            [
                _story("US-001", status=StoryStatus.PASSED),
                _story("US-002", status=StoryStatus.PASSED),
            ]
        )

        assert orch.get_next_story() is None

    def test_empty_orchestrator(self):
        orch = TaskOrchestrator()
        assert orch.get_next_story() is None


class TestProgress:
    """进度统计"""

    def test_progress_all_pending(self):
        orch = TaskOrchestrator()
        orch.add_stories([_story("US-001"), _story("US-002"), _story("US-003")])

        progress = orch.get_progress()
        assert progress["total"] == 3
        assert progress["completed"] == 0
        assert progress["pending"] == 3
        assert progress["progress_pct"] == 0.0

    def test_progress_partial(self):
        orch = TaskOrchestrator()
        orch.add_stories(
            [
                _story("US-001", status=StoryStatus.PASSED),
                _story("US-002", status=StoryStatus.PASSED),
                _story("US-003"),
            ]
        )

        progress = orch.get_progress()
        assert progress["completed"] == 2
        assert progress["progress_pct"] == pytest.approx(66.67, rel=0.01)

    def test_progress_empty(self):
        orch = TaskOrchestrator()
        progress = orch.get_progress()
        assert progress["total"] == 0
        assert progress["progress_pct"] == 0.0

    def test_all_done(self):
        orch = TaskOrchestrator()
        orch.add_stories(
            [
                _story("US-001", status=StoryStatus.PASSED),
                _story("US-002", status=StoryStatus.SKIPPED),
            ]
        )
        assert orch.all_done is True

    def test_not_all_done(self):
        orch = TaskOrchestrator()
        orch.add_stories(
            [
                _story("US-001", status=StoryStatus.PASSED),
                _story("US-002"),
            ]
        )
        assert orch.all_done is False

    def test_get_stories_by_status(self):
        orch = TaskOrchestrator()
        orch.add_stories(
            [
                _story("US-001", status=StoryStatus.PASSED),
                _story("US-002", status=StoryStatus.PASSED),
                _story("US-003"),
            ]
        )

        passed = orch.get_stories_by_status(StoryStatus.PASSED)
        assert len(passed) == 2

    def test_get_blocked_stories(self):
        orch = TaskOrchestrator()
        orch.add_stories(
            [
                _story("US-001"),
                _story("US-002", dependencies=["US-001"]),
            ]
        )

        blocked = orch.get_blocked_stories()
        assert len(blocked) == 1
        assert blocked[0].id == "US-002"


class TestSerialization:
    """序列化 / 反序列化"""

    def test_to_list_and_from_list(self):
        orch = TaskOrchestrator()
        orch.add_stories(
            [
                _story("US-001", priority=StoryPriority.HIGH),
                _story("US-002", priority=StoryPriority.LOW),
            ]
        )

        data = orch.to_list()
        assert len(data) == 2

        # 重建
        orch2 = TaskOrchestrator()
        orch2.from_list(data)
        assert orch2.total_stories == 2
        assert orch2.get_story("US-001").priority == StoryPriority.HIGH

    def test_from_list_clears_existing(self):
        orch = TaskOrchestrator()
        orch.add_stories([_story("US-001")])

        orch.from_list([_story("US-099").to_dict()])
        assert orch.total_stories == 1
        assert orch.get_story("US-099") is not None
        assert orch.get_story("US-001") is None
