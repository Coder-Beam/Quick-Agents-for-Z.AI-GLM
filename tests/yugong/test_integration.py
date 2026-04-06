"""
愚公循环集成测试

端到端场景测试:
- 完整流程: 需求解析 → 任务编排 → 循环执行 → 退出检测
- 安全守护集成: 熔断器触发 → 循环暂停
- 上下文注入集成: Prompt 构建验证
- 进度日志集成: 日志记录验证
- 依赖链场景: Story 有依赖关系时的执行顺序
- 错误恢复场景: Agent 失败后重试
"""

import json
import json
import pytest
from datetime import datetime, timedelta

from quickagents.yugong import (
    YuGongLoop,
    YuGongConfig,
    TaskOrchestrator,
    UserStory,
    LoopResult,
    LoopState,
    ParsedRequirement,
    StoryPriority,
    StoryStatus,
)
from quickagents.yugong.context_injector import ContextInjector
from quickagents.yugong.progress_logger import ProgressLogger
from quickagents.yugong.safety_guard import SafetyGuard
from quickagents.yugong.exit_detector import ExitDetector
from quickagents.yugong.requirement_parser import RequirementParser


def _make_requirement(stories_data: list[dict]) -> ParsedRequirement:
    """从数据创建需求"""
    stories = []
    for sd in stories_data:
        stories.append(
            UserStory(
                id=sd["id"],
                title=sd["title"],
                description=sd.get("description", sd["title"]),
                acceptance_criteria=sd.get("acceptance_criteria", []),
                priority=sd.get("priority", StoryPriority.MEDIUM),
                dependencies=sd.get("dependencies", []),
            )
        )
    return ParsedRequirement(
        project_name="integration-test",
        branch_name="yugong/test",
        description="Integration test project",
        user_stories=stories,
        raw_source="...",
        format="json",
    )


class TestFullPipeline:
    """完整流程: 需求 → 编排 → 执行 → 退出"""

    def test_three_stories_all_pass(self):
        """3个Story全部通过"""
        call_count = 0

        def mock_agent(prompt: str) -> dict:
            nonlocal call_count
            call_count += 1
            return {
                "output": f"Story #{call_count} done. Tests pass.",
                "token_usage": {"input": 100, "output": 50, "total": 150},
                "files_changed": [f"src/{call_count}.py"],
            }

        loop = YuGongLoop(
            config=YuGongConfig(min_iterations=0),
            agent_fn=mock_agent,
        )
        req = _make_requirement(
            [
                {"id": "US-001", "title": "Setup project"},
                {"id": "US-002", "title": "Add auth"},
                {"id": "US-003", "title": "Add tests"},
            ]
        )

        outcome = loop.start(req)

        assert outcome.success is True
        assert outcome.completed_stories == 3
        assert outcome.total_iterations == 3
        assert call_count == 3

    def test_five_stories_with_priorities(self):
        """5个Story, 按优先级执行"""
        execution_order = []

        def mock_agent(prompt: str) -> dict:
            # 从 prompt 中提取 Story ID
            for line in prompt.split("\n"):
                if line.startswith("# Current Task:"):
                    parts = line.split(":", 1)
                    if len(parts) >= 2:
                        story_id = parts[1].strip().split(" ")[0]
                        execution_order.append(story_id)
            return {
                "output": "Done",
                "token_usage": {"total": 100},
                "files_changed": [],
            }

        loop = YuGongLoop(
            config=YuGongConfig(min_iterations=0),
            agent_fn=mock_agent,
        )
        req = _make_requirement(
            [
                {"id": "US-003", "title": "Low", "priority": StoryPriority.LOW},
                {"id": "US-001", "title": "Critical", "priority": StoryPriority.CRITICAL},
                {"id": "US-004", "title": "Trivial", "priority": StoryPriority.TRIVIAL},
                {"id": "US-002", "title": "High", "priority": StoryPriority.HIGH},
                {"id": "US-005", "title": "Medium", "priority": StoryPriority.MEDIUM},
            ]
        )

        outcome = loop.start(req)

        assert outcome.success is True
        assert execution_order == ["US-001", "US-002", "US-005", "US-003", "US-004"]

    def test_dependencies_respected(self):
        """依赖链: US-002 依赖 US-001, 顺序执行"""
        execution_order = []

        def mock_agent(prompt: str) -> dict:
            for line in prompt.split("\n"):
                if line.startswith("# Current Task:"):
                    story_id = line.split(":")[1].strip().split(" ")[0]
                    execution_order.append(story_id)
            return {
                "output": "Done",
                "token_usage": {"total": 100},
                "files_changed": [],
            }

        loop = YuGongLoop(
            config=YuGongConfig(min_iterations=0),
            agent_fn=mock_agent,
        )
        req = _make_requirement(
            [
                {"id": "US-002", "title": "Auth API", "dependencies": ["US-001"]},
                {"id": "US-001", "title": "User Model"},
                {"id": "US-003", "title": "Tests", "dependencies": ["US-001", "US-002"]},
            ]
        )

        outcome = loop.start(req)

        assert outcome.success is True
        assert execution_order.index("US-001") < execution_order.index("US-002")
        assert execution_order.index("US-002") < execution_order.index("US-003")


class TestErrorRecovery:
    """错误恢复场景"""

    def test_retry_on_failure_then_succeed(self):
        """先失败, 重试后成功"""
        call_count = 0

        def flaky_agent(prompt: str) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise RuntimeError("Connection timeout")
            return {
                "output": "Finally works",
                "token_usage": {"total": 100},
                "files_changed": [],
            }

        loop = YuGongLoop(
            config=YuGongConfig(
                min_iterations=0,
                max_iterations=20,
                cb_no_progress_threshold=10,
            ),
            agent_fn=flaky_agent,
        )
        req = _make_requirement(
            [
                {"id": "US-001", "title": "Flaky feature"},
            ]
        )

        outcome = loop.start(req)

        # 2 failures (iterations 1,2), then success (iteration 3)
        # But: each failure marks story as FAILED. Next iteration picks FAILED story (can_retry=True)
        # On 3rd call, succeeds and marks PASSED.
        assert call_count >= 3
        assert outcome.completed_stories == 1

    def test_max_attempts_exhausted(self):
        """超过最大尝试次数, Story 不可重试"""
        call_count = 0

        def always_fail(prompt: str) -> dict:
            nonlocal call_count
            call_count += 1
            raise RuntimeError("Always fails")

        loop = YuGongLoop(
            config=YuGongConfig(
                min_iterations=0,
                max_iterations=20,
                cb_no_progress_threshold=10,
            ),
            agent_fn=always_fail,
        )
        # Story with max_attempts=2
        req = _make_requirement(
            [
                {"id": "US-001", "title": "Bad feature"},
            ]
        )
        req.user_stories[0].max_attempts = 2

        outcome = loop.start(req)

        # 2 attempts for US-001, then no more executable stories
        assert outcome.completed_stories == 0


class TestContextInjectorIntegration:
    """上下文注入集成"""

    def test_full_prompt_built(self):
        """验证完整 Prompt 包含所有层级"""
        inj = ContextInjector(
            requirement=_make_requirement(
                [
                    {"id": "US-001", "title": "Login", "acceptance_criteria": ["Valid JWT"]},
                ]
            ),
            learnings=["Use bcrypt for passwords"],
            tech_stack="Python, FastAPI",
        )

        orch = TaskOrchestrator()
        orch.load_from_requirement(inj.requirement)
        story = orch.get_next_story()
        state = LoopState(current_iteration=3)

        prompt = inj.build_prompt(story, state, orch)

        # 验证各层内容
        assert "autonomous" in prompt.lower()  # 系统层
        assert "integration-test" in prompt  # 项目层
        assert "Login" in prompt  # 任务层
        assert "Valid JWT" in prompt  # 验收标准
        assert "Iteration: 3" in prompt  # 进度层
        assert "bcrypt" in prompt  # 经验层
        assert "FastAPI" in prompt  # 技术栈
        assert "EXIT_SIGNAL" in prompt  # 信号层

    def test_progress_shows_completed(self):
        """Prompt 包含已完成 Stories 的进度"""
        inj = ContextInjector(
            requirement=_make_requirement(
                [
                    {"id": "US-001", "title": "Setup"},
                    {"id": "US-002", "title": "Auth"},
                ]
            )
        )

        orch = TaskOrchestrator()
        orch.load_from_requirement(inj.requirement)

        # 标记 US-001 完成
        story = orch.get_story("US-001")
        story.mark_passed()
        orch.update_story(story)

        state = LoopState(current_iteration=1, completed_stories=1)
        current = orch.get_next_story()

        prompt = inj.build_prompt(current, state, orch)

        assert "Completed: 1/2" in prompt
        assert "50.0%" in prompt


class TestProgressLoggerIntegration:
    """进度日志集成"""

    def test_log_during_loop(self):
        """循环中记录日志"""
        logger = ProgressLogger()

        def mock_agent(prompt: str) -> dict:
            return {
                "output": "Done",
                "token_usage": {"total": 100},
                "files_changed": [],
            }

        loop = YuGongLoop(
            config=YuGongConfig(min_iterations=0),
            agent_fn=mock_agent,
        )

        # 在回调中记录
        def on_iteration_end(it, result):
            logger.log_progress(result.story_id, it, f"Iteration {it} completed")

        loop.on_iteration_end(on_iteration_end)

        req = _make_requirement(
            [
                {"id": "US-001", "title": "Feature 1"},
                {"id": "US-002", "title": "Feature 2"},
            ]
        )
        loop.start(req)

        assert logger.count == 2
        learnings = logger.get_learnings()
        # No learnings logged, only progress
        assert len(learnings) == 0

        progress_entries = logger.get_by_type("progress")
        assert len(progress_entries) == 2

    def test_error_logging(self):
        """记录错误日志"""
        logger = ProgressLogger()

        call_count = 0

        def fail_agent(prompt: str) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("OOM")
            return {"output": "OK", "token_usage": {"total": 100}, "files_changed": []}

        loop = YuGongLoop(
            config=YuGongConfig(min_iterations=0, cb_no_progress_threshold=10, max_iterations=20),
            agent_fn=fail_agent,
        )

        def on_iteration_end(it, result):
            if not result.success:
                logger.log_error(result.story_id, it, result.error)

        loop.on_iteration_end(on_iteration_end)

        req = _make_requirement([{"id": "US-001", "title": "Feature"}])
        loop.start(req)

        errors = logger.get_errors()
        assert len(errors) >= 1
        assert "OOM" in errors[0].message


class TestRequirementParserIntegration:
    """需求解析器集成"""

    def test_parse_json_then_run(self):
        """JSON 需求解析后直接运行"""
        import tempfile
        from pathlib import Path

        parser = RequirementParser()

        json_content = json.dumps(
            {
                "project_name": "TodoApp",
                "branch_name": "yugong/todo-app",
                "description": "A simple todo app",
                "userStories": [
                    {
                        "id": "US-001",
                        "title": "Create todo",
                        "description": "User can create a todo item",
                        "acceptanceCriteria": ["Form validation", "Persist to DB"],
                    },
                    {
                        "id": "US-002",
                        "title": "List todos",
                        "description": "User can see all todos",
                        "acceptanceCriteria": ["Display list"],
                    },
                ],
            }
        )

        # Write to temp file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(json_content)

        req = parser.parse(f.name)

        loop = YuGongLoop(
            config=YuGongConfig(min_iterations=0),
            agent_fn=lambda p: {"output": "OK", "token_usage": {"total": 50}, "files_changed": []},
        )

        outcome = loop.start(req)

        assert outcome.success is True
        assert outcome.completed_stories == 2
        assert outcome.total_stories == 2


class TestSafetyGuardIntegration:
    """安全守护集成"""

    def test_max_iterations_stops_loop(self):
        """max_iterations 限制循环"""
        loop = YuGongLoop(
            config=YuGongConfig(max_iterations=2, min_iterations=0),
            agent_fn=lambda p: {"output": "OK", "token_usage": {"total": 50}, "files_changed": []},
        )

        req = _make_requirement([{"id": f"US-{i:03d}", "title": f"Story {i}"} for i in range(1, 11)])

        outcome = loop.start(req)

        assert outcome.total_iterations <= 2
        assert outcome.completed_stories <= 2

    def test_status_report(self):
        """状态报告"""
        loop = YuGongLoop(config=YuGongConfig())
        status = loop.get_status()

        assert "status" in status
        assert "iteration" in status
        assert "progress" in status
        assert "safety" in status
        assert "hourly_calls" in status["safety"]
