"""
愚公循环上下文注入器 + 进度日志 测试
"""

import pytest
from datetime import datetime

from quickagents.yugong.context_injector import ContextInjector
from quickagents.yugong.progress_logger import ProgressLogger, LogEntry
from quickagents.yugong.models import (
    UserStory,
    LoopState,
    ParsedRequirement,
    StoryPriority,
    StoryStatus,
)
from quickagents.yugong.task_orchestrator import TaskOrchestrator


# === ContextInjector Tests ===


def _make_story(**kwargs) -> UserStory:
    defaults = dict(
        id="US-001",
        title="Login",
        description="Implement login",
        acceptance_criteria=["Valid credentials", "Error handling"],
    )
    defaults.update(kwargs)
    return UserStory(**defaults)


def _make_req() -> ParsedRequirement:
    return ParsedRequirement(
        project_name="TestApp",
        branch_name="yugong/test-app",
        description="A test application",
        user_stories=[_make_story()],
        raw_source="...",
        format="json",
    )


class TestContextInjector:
    """上下文注入器"""

    def test_build_prompt_basic(self):
        inj = ContextInjector(requirement=_make_req())
        story = _make_story()
        state = LoopState(current_iteration=3)
        orch = TaskOrchestrator()
        orch.add_story(story)

        prompt = inj.build_prompt(story, state, orch)

        assert "Login" in prompt
        assert "US-001" in prompt
        assert "Valid credentials" in prompt
        assert "Iteration: 3" in prompt

    def test_system_context(self):
        inj = ContextInjector()
        ctx = inj._system_context()
        assert "autonomous" in ctx.lower() or "coding" in ctx.lower()

    def test_project_context(self):
        inj = ContextInjector(requirement=_make_req())
        ctx = inj._project_context()
        assert "TestApp" in ctx
        assert "yugong/test-app" in ctx

    def test_progress_context(self):
        inj = ContextInjector()
        state = LoopState(current_iteration=5)
        orch = TaskOrchestrator()
        orch.add_story(_make_story(status=StoryStatus.PASSED))
        orch.add_story(_make_story(id="US-002", title="Signup"))

        ctx = inj._progress_context(state, orch)
        assert "Iteration: 5" in ctx
        assert "Completed: 1" in ctx

    def test_story_context_with_deps(self):
        inj = ContextInjector()
        story = _make_story(dependencies=["US-000"])
        ctx = inj._story_context(story)
        assert "US-000" in ctx
        assert "Login" in ctx

    def test_learnings_context(self):
        inj = ContextInjector(learnings=["Always run tests first", "Use venv"])
        ctx = inj._learnings_context()
        assert "Always run tests first" in ctx
        assert "Use venv" in ctx

    def test_learnings_empty(self):
        inj = ContextInjector()
        ctx = inj._learnings_context()
        assert "No previous" in ctx

    def test_quality_context(self):
        inj = ContextInjector()
        ctx = inj._quality_context()
        assert "typecheck" in ctx.lower() or "tests" in ctx.lower()

    def test_signal_context(self):
        inj = ContextInjector()
        ctx = inj._signal_context()
        assert "EXIT_SIGNAL" in ctx

    def test_requirement_context_no_req(self):
        inj = ContextInjector()
        ctx = inj._requirement_context()
        assert "No requirements" in ctx

    def test_tech_stack(self):
        inj = ContextInjector(tech_stack="Python, FastAPI, SQLite")
        ctx = inj._project_context()
        assert "Python, FastAPI, SQLite" in ctx


# === ProgressLogger Tests ===


class TestProgressLogger:
    """进度日志"""

    def test_log_entry(self):
        logger = ProgressLogger()
        logger.log("US-001", 1, "progress", "Started implementation")

        assert logger.count == 1

    def test_log_decision(self):
        logger = ProgressLogger()
        logger.log("US-001", 1, "decision", "Using SQLite")

        entries = logger.get_by_type("decision")
        assert len(entries) == 1
        assert entries[0].message == "Using SQLite"

    def test_log_learning(self):
        logger = ProgressLogger()
        logger.log("US-001", 1, "learning", "Always mock external APIs")

        entries = logger.get_by_type("learning")
        assert len(entries) == 1

    def test_log_error(self):
        logger = ProgressLogger()
        logger.log("US-001", 1, "error", "ImportError: module not found")
        logger.log("US-002", 2, "error", "TypeError: 'NoneType'")

        errors = logger.get_errors()
        assert len(errors) == 2

        us001_errors = logger.get_errors(story_id="US-001")
        assert len(us001_errors) == 1
        assert us001_errors[0].story_id == "US-001"

    def test_get_recent(self):
        logger = ProgressLogger()
        for i in range(5):
            logger.log("US-001", i + 1, "progress", f"Step {i + 1}")

        recent = logger.get_recent(3)
        assert len(recent) == 3
        assert recent[0].message == "Step 3"

    def test_get_by_story(self):
        logger = ProgressLogger()
        logger.log("US-001", 1, "progress", "US-001 progress")
        logger.log("US-002", 1, "progress", "US-002 progress")
        logger.log("US-001", 2, "decision", "US-001 decision")

        us001 = logger.get_by_story("US-001")
        assert len(us001) == 2

    def test_serialization(self):
        logger = ProgressLogger()
        logger.log("US-001", 1, "learning", "Test learning")

        data = logger.to_list()
        assert len(data) == 1

        logger2 = ProgressLogger()
        logger2.from_list(data)
        assert logger2.count == 1

    def test_clear(self):
        logger = ProgressLogger()
        logger.log("US-001", 1, "progress", "test")
        logger.clear()
        assert logger.count == 0

    def test_log_entry_to_dict(self):
        entry = LogEntry(
            story_id="US-001",
            iteration=1,
            log_type="progress",
            message="test",
        )
        d = entry.to_dict()
        assert d["story_id"] == "US-001"
        assert d["log_type"] == "progress"
