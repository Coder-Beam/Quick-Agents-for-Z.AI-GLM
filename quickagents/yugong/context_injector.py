"""
愚公循环上下文注入器

@note 此模块尚未集成到生产管道。当前 autonomous_loop.py 使用内联 _build_prompt()。
      本模块实现了 8 层 Prompt 架构（系统/项目/需求/进度/任务/经验/质量/信号），
      可在需要更丰富的上下文注入时启用。

负责构建完整的 Prompt 上下文:
- 系统层: 角色定义、工作规则
- 项目层: 技术栈、约束条件
- 需求层: 完整需求文档
- 进度层: 当前进度、已完成 Stories
- 任务层: 当前 Story 详情
- 经验层: 经验教训
- 质量层: 质量要求
- 信号层: 退出信号指令
"""

from typing import Optional

from .models import UserStory, LoopState, ParsedRequirement
from .task_orchestrator import TaskOrchestrator


class ContextInjector:
    """
    运行时上下文注入

    按设计文档的 10 部分 Prompt 结构组装上下文
    """

    def __init__(
        self,
        requirement: Optional[ParsedRequirement] = None,
        learnings: Optional[list[str]] = None,
        tech_stack: Optional[str] = None,
    ):
        self.requirement = requirement
        self.learnings = learnings or []
        self.tech_stack = tech_stack or ""

    def build_prompt(
        self,
        story: UserStory,
        state: LoopState,
        orchestrator: TaskOrchestrator,
    ) -> str:
        """
        构建完整 Prompt

        Args:
            story: 当前 Story
            state: 循环状态
            orchestrator: 任务编排器

        Returns:
            组装好的完整 Prompt
        """
        parts = []

        # Part 1: 系统层
        parts.append(self._system_context())

        # Part 2: 项目层
        parts.append(self._project_context())

        # Part 3: 需求层
        parts.append(self._requirement_context())

        # Part 4: 进度层
        parts.append(self._progress_context(state, orchestrator))

        # Part 5: 任务层
        parts.append(self._story_context(story))

        # Part 6: 经验层
        parts.append(self._learnings_context())

        # Part 7: 质量层
        parts.append(self._quality_context())

        # Part 8: 信号层
        parts.append(self._signal_context())

        return "\n\n".join(parts)

    # === 各层构建 ===

    def _system_context(self) -> str:
        """系统层: 角色定义"""
        return """# System Context

You are an autonomous coding agent executing tasks in a loop.
Each task is a User Story that must be fully implemented with tests.
Follow TDD: write failing tests first, then implement, then refactor."""

    def _project_context(self) -> str:
        """项目层: 技术栈"""
        parts = ["# Project Context"]
        if self.requirement:
            parts.append(f"Project: {self.requirement.project_name}")
            parts.append(f"Branch: {self.requirement.branch_name}")
            parts.append(f"Description: {self.requirement.description}")
        if self.tech_stack:
            parts.append(f"Tech Stack: {self.tech_stack}")
        return "\n".join(parts)

    def _requirement_context(self) -> str:
        """需求层"""
        if not self.requirement:
            return "# Requirements\nNo requirements loaded."
        parts = ["# Requirements"]
        parts.append(self.requirement.description)
        if self.requirement.user_stories:
            parts.append("\n## All User Stories:")
            for s in self.requirement.user_stories:
                status = s.status.value if hasattr(s, "status") else "pending"
                parts.append(f"- [{status.upper()}] {s.id}: {s.title}")
        return "\n".join(parts)

    def _progress_context(self, state: LoopState, orch: TaskOrchestrator) -> str:
        """进度层"""
        progress = orch.get_progress()
        return f"""# Progress
- Iteration: {state.current_iteration}
- Completed: {progress["completed"]}/{progress["total"]} ({progress["progress_pct"]:.1f}%)
- Pending: {progress["pending"]}
- Failed: {progress["failed"]}"""

    def _story_context(self, story: UserStory) -> str:
        """任务层: 当前 Story 详情"""
        parts = [f"# Current Task: {story.id} - {story.title}"]
        parts.append(story.description)
        if story.acceptance_criteria:
            parts.append("\n## Acceptance Criteria:")
            for ac in story.acceptance_criteria:
                parts.append(f"- [ ] {ac}")
        if story.dependencies:
            parts.append(f"\nDependencies: {', '.join(story.dependencies)}")
        parts.append(f"Priority: {story.priority.name}")
        parts.append(f"Complexity: {story.estimated_complexity}")
        parts.append(f"Attempt: {story.attempts + 1}/{story.max_attempts}")
        return "\n".join(parts)

    def _learnings_context(self) -> str:
        """经验层"""
        if not self.learnings:
            return "# Learnings\nNo previous learnings."
        parts = ["# Learnings (from previous iterations)"]
        for i, learning in enumerate(self.learnings[-10:], 1):
            parts.append(f"{i}. {learning}")
        return "\n".join(parts)

    def _quality_context(self) -> str:
        """质量层"""
        return """# Quality Requirements
- All code must pass typecheck
- All code must pass lint
- All tests must pass
- No TODO comments in production code
- Follow existing code style"""

    def _signal_context(self) -> str:
        """信号层"""
        return """# Completion Signal
When ALL stories are complete, include in your output:
- EXIT_SIGNAL: true
- "all tasks complete"
- "project ready"
This signals the loop to exit."""
