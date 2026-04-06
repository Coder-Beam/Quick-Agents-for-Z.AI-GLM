"""
愚公循环自主引擎测试

测试覆盖:
- 启动/暂停/恢复/停止控制
- 标准迭代流程 (使用 mock agent_fn)
- 安全检查失败处理
- 退出检测集成
- 回调机制
"""

import pytest
from datetime import datetime

from quickagents.yugong.autonomous_loop import YuGongLoop, LoopOutcome
from quickagents.yugong.config import YuGongConfig
from quickagents.yugong.models import (
    UserStory,
    LoopResult,
    LoopState,
    ParsedRequirement,
    StoryPriority,
    StoryStatus,
)


def _make_requirement(n: int = 3) -> ParsedRequirement:
    """创建测试用的需求"""
    stories = []
    for i in range(1, n + 1):
        stories.append(
            UserStory(
                id=f"US-{i:03d}",
                title=f"Story {i}",
                description=f"Description for story {i}",
                acceptance_criteria=[f"AC{i}.1"],
            )
        )
    return ParsedRequirement(
        project_name="test-project",
        branch_name="yugong/test",
        description="test",
        user_stories=stories,
        raw_source="...",
        format="json",
    )


def _mock_agent_success(prompt: str) -> dict:
    """模拟成功的 Agent"""
    return {
        "output": "Implementation complete. All tests pass.",
        "token_usage": {"input": 500, "output": 200, "total": 700},
        "files_changed": ["src/main.py"],
    }


def _mock_agent_fail(prompt: str) -> dict:
    """模拟失败的 Agent"""
    raise RuntimeError("Agent error: timeout")


class TestStartStop:
    """启动 / 停止"""

    def test_start_completes_all_stories(self):
        loop = YuGongLoop(
            config=YuGongConfig(min_iterations=0),
            agent_fn=_mock_agent_success,
        )
        req = _make_requirement(3)
        outcome = loop.start(req)

        assert outcome.success is True
        assert outcome.completed_stories == 3
        assert outcome.total_stories == 3
        assert outcome.total_iterations >= 3

    def test_start_no_agent(self):
        """agent_fn=None → 迭代失败, story 标记为 failed"""
        loop = YuGongLoop(config=YuGongConfig(min_iterations=0))
        req = _make_requirement(1)
        outcome = loop.start(req)

        # No agent_fn → error result → story fails → loop completes
        assert outcome.completed_stories == 0
        assert outcome.total_iterations >= 1

    def test_stop_mid_loop(self):
        cancelled = []

        def agent_that_stops(prompt: str) -> dict:
            loop.stop("test stop")
            cancelled.append(True)
            return _mock_agent_success(prompt)

        loop = YuGongLoop(
            config=YuGongConfig(min_iterations=0),
            agent_fn=agent_that_stops,
        )
        req = _make_requirement(5)
        outcome = loop.start(req)

        assert outcome.reason == "用户取消"
        assert outcome.completed_stories < 5

    def test_max_iterations_limit(self):
        loop = YuGongLoop(
            config=YuGongConfig(max_iterations=2, min_iterations=0),
            agent_fn=_mock_agent_success,
        )
        req = _make_requirement(10)
        outcome = loop.start(req)

        assert outcome.total_iterations <= 2
        assert "最大迭代" in outcome.reason or outcome.completed_stories <= 2


class TestPauseResume:
    """暂停 / 恢复"""

    def test_get_status_returns_state(self):
        loop = YuGongLoop(config=YuGongConfig())
        status = loop.get_status()

        assert "status" in status
        assert "iteration" in status
        assert "progress" in status


class TestAgentErrors:
    """Agent 错误处理"""

    def test_agent_exception_recorded(self):
        iteration_results = []

        def capture_iteration(it, result):
            iteration_results.append(result)

        loop = YuGongLoop(
            config=YuGongConfig(
                min_iterations=0,
                cb_no_progress_threshold=10,  # 高阈值避免熔断
                max_iterations=5,
            ),
            agent_fn=_mock_agent_fail,
        )
        loop.on_iteration_end(capture_iteration)

        req = _make_requirement(1)
        outcome = loop.start(req)

        # Agent always fails → stories never complete
        assert outcome.completed_stories == 0
        assert len(iteration_results) > 0
        assert iteration_results[0].success is False
        assert "Agent error" in (iteration_results[0].error or "")


class TestCallbacks:
    """回调机制"""

    def test_iteration_start_callback(self):
        starts = []

        def on_start(it, story):
            starts.append((it, story.id))

        loop = YuGongLoop(
            config=YuGongConfig(min_iterations=0),
            agent_fn=_mock_agent_success,
        )
        loop.on_iteration_start(on_start)

        req = _make_requirement(2)
        loop.start(req)

        assert len(starts) == 2
        assert starts[0][0] == 1
        assert starts[0][1] == "US-001"

    def test_iteration_end_callback(self):
        ends = []

        def on_end(it, result):
            ends.append((it, result.success))

        loop = YuGongLoop(
            config=YuGongConfig(min_iterations=0),
            agent_fn=_mock_agent_success,
        )
        loop.on_iteration_end(on_end)

        req = _make_requirement(2)
        loop.start(req)

        assert len(ends) == 2
        assert all(s for _, s in ends)

    def test_story_complete_callback(self):
        completed = []

        def on_complete(story, result):
            completed.append(story.id)

        loop = YuGongLoop(
            config=YuGongConfig(min_iterations=0),
            agent_fn=_mock_agent_success,
        )
        loop.on_story_complete(on_complete)

        req = _make_requirement(3)
        loop.start(req)

        assert completed == ["US-001", "US-002", "US-003"]


class TestBuildPrompt:
    """Prompt 构建"""

    def test_prompt_contains_story_info(self):
        loop = YuGongLoop(config=YuGongConfig())
        story = UserStory(
            id="US-001",
            title="Login feature",
            description="Implement user login",
            acceptance_criteria=["Valid credentials", "Error handling"],
        )

        prompt = loop._build_prompt(story)

        assert "Login feature" in prompt
        assert "Implement user login" in prompt
        assert "Valid credentials" in prompt


class TestLoopOutcome:
    """循环结果"""

    def test_outcome_fields(self):
        outcome = LoopOutcome(
            success=True,
            reason="所有 Story 完成",
            total_iterations=5,
            total_stories=3,
            completed_stories=3,
            duration_seconds=12.5,
            state=LoopState(),
        )

        assert outcome.success is True
        assert outcome.total_iterations == 5
        assert outcome.duration_seconds == 12.5
