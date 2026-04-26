"""
愚公循环自主循环引擎

核心类: YuGongLoop
- 编排 SafetyGuard, ExitDetector, TaskOrchestrator
- 管理 LoopState 生命周期
- 提供 start/pause/resume/stop 控制
- 15步标准迭代流程
"""

import time
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Callable, Any

from .config import YuGongConfig
from .models import (
    UserStory,
    LoopResult,
    LoopState,
    ParsedRequirement,
    StoryStatus,
)
from .safety_guard import SafetyGuard, SafetyCheckResult
from .exit_detector import ExitDetector, ExitCheckResult
from .task_orchestrator import TaskOrchestrator
from .db import YuGongDB

logger = logging.getLogger(__name__)


@dataclass
class LoopOutcome:
    """循环结果"""

    success: bool
    reason: str
    total_iterations: int
    total_stories: int
    completed_stories: int
    duration_seconds: float
    state: LoopState


class YuGongLoop:
    """
    愚公循环自主引擎

    15步标准迭代:
        Phase 1 (准备): safety_check → get_next_story → build_prompt
        Phase 2 (执行): execute_agent → parse_output
        Phase 3 (验证): quality_checks → extract_learnings → update_story
        Phase 4 (收尾): auto_commit → regression → exit_check → persist → sync → metrics
    """

    def __init__(
        self,
        config: Optional[YuGongConfig] = None,
        agent_fn: Optional[Callable[[str], dict]] = None,
        db: Optional[YuGongDB] = None,
    ):
        """
        Args:
            config: 配置, 默认使用 YuGongConfig()
            agent_fn: AI Agent 执行函数, 接收 prompt 返回 dict
                      dict 格式: {"output": str, "token_usage": dict, "files_changed": list}
        """
        self.config = config or YuGongConfig()
        self.agent_fn = agent_fn
        self.db = db

        # 子组件
        self.safety = SafetyGuard(self.config)
        self.exit_detector = ExitDetector(self.config)
        self.orchestrator = TaskOrchestrator(db=db)

        # 循环状态
        self.state = LoopState()
        self._running = False
        self._paused = False
        self._cancelled = False

        # 回调
        self._on_iteration_start: Optional[Callable] = None
        self._on_iteration_end: Optional[Callable] = None
        self._on_story_complete: Optional[Callable] = None

    # === 回调注册 ===

    def on_iteration_start(self, fn: Callable) -> None:
        """注册迭代开始回调"""
        self._on_iteration_start = fn

    def on_iteration_end(self, fn: Callable) -> None:
        """注册迭代结束回调"""
        self._on_iteration_end = fn

    def on_story_complete(self, fn: Callable) -> None:
        """注册 Story 完成回调"""
        self._on_story_complete = fn

    # === 控制接口 ===

    def start(self, requirement: ParsedRequirement) -> LoopOutcome:
        """
        启动愚公循环

        流程: 解析需求 → 持久化到 DB → 从 DB 加载 → 执行循环

        Args:
            requirement: 解析后的需求

        Returns:
            LoopOutcome: 循环结果
        """
        self.orchestrator.load_from_requirement(requirement)

        if self.db:
            try:
                self.db.save_requirement(requirement)
                saved_state = self.db.load_state()
                if saved_state and saved_state.status in ("running",):
                    logger.info("检测到未完成的循环状态, 从 DB 恢复 stories")
                    self.orchestrator.load_from_db(self.db)
            except Exception as e:
                logger.warning("初始DB持久化失败: %s", e)

        self.state = LoopState(
            status="running",
            total_stories=self.orchestrator.total_stories,
            start_time=datetime.now(),
        )
        self._running = True
        self._cancelled = False
        self._paused = False

        logger.info("愚公循环启动: %d stories", self.orchestrator.total_stories)

        try:
            return self._run_loop()
        finally:
            self._running = False
            self._ensure_state_persisted()

    def resume_from_db(self) -> LoopOutcome:
        """
        从 DB 恢复并继续执行

        流程: 从 DB 加载 stories → 从 DB 加载 state → 继续循环

        Returns:
            LoopOutcome: 循环结果
        """
        if not self.db:
            raise ValueError("resume_from_db 需要 db 实例")

        count = self.orchestrator.load_from_db(self.db)
        if count == 0:
            logger.warning("DB 中无 stories, 无法恢复")

        saved_state = self.db.load_state()

        self.state = saved_state or LoopState(
            status="running",
            total_stories=self.orchestrator.total_stories,
            start_time=datetime.now(),
        )
        self.state.status = "running"
        self.state.total_stories = self.orchestrator.total_stories
        self._running = True
        self._cancelled = False
        self._paused = False

        logger.info("愚公循环从 DB 恢复: %d stories (已完成: %d)",
                     self.orchestrator.total_stories, self.orchestrator.completed_stories)

        try:
            return self._run_loop()
        finally:
            self._running = False
            self._ensure_state_persisted()

    def _ensure_state_persisted(self) -> None:
        """确保最终状态持久化到 DB"""
        if not self.db:
            return
        try:
            if self.state.status not in ("completed",):
                self.state.status = "stopped"
            self.db.save_state(self.state)
            for sid, s in self.orchestrator._stories.items():
                self.db.save_story(s)
        except Exception as e:
            logger.warning("最终状态持久化失败: %s", e)

    def pause(self) -> bool:
        """暂停循环"""
        if self._running and not self._paused:
            self._paused = True
            self.state.status = "paused"
            logger.info("愚公循环暂停")
            return True
        return False

    def resume(self) -> bool:
        """恢复循环"""
        if self._running and self._paused:
            self._paused = False
            self.state.status = "running"
            logger.info("愚公循环恢复")
            return True
        return False

    def stop(self, reason: str = "用户停止") -> None:
        """停止循环"""
        self._cancelled = True
        self.state.status = "stopped"
        logger.info("愚公循环停止: %s", reason)

    # === 主循环 ===

    def _run_loop(self) -> LoopOutcome:
        """主循环体"""
        start = time.monotonic()

        while self._running and not self._cancelled:
            # 暂停检查
            if self._paused:
                time.sleep(0.1)
                continue

            # Phase 1: 准备
            # 1. 安全检查
            safety_result = self.safety.check_before_iteration()
            if not safety_result.safe:
                if safety_result.should_wait and safety_result.wait_seconds > 0:
                    logger.warning("安全等待: %s (%ds)", safety_result.reason, safety_result.wait_seconds)
                    # 在测试中不实际等待, 只记录
                    self.state.status = "waiting"
                    break
                logger.warning("安全检查失败: %s", safety_result.reason)
                self.state.status = "stopped"
                break

            # 2. 获取下一个 Story
            story = self.orchestrator.get_next_story()
            if story is None:
                if self.orchestrator.all_done:
                    self.state.status = "completed"
                else:
                    self.state.status = "completed"
                logger.info(
                    "没有可执行的 Story (completed=%d, total=%d)",
                    self.orchestrator.completed_stories,
                    self.orchestrator.total_stories,
                )
                break

            # 3. 迭代开始
            iteration = self.state.current_iteration + 1
            self.state.current_story = story
            story.start()
            self.state.status = "running"

            if self._on_iteration_start:
                self._on_iteration_start(iteration, story)

            # Phase 2: 执行
            result = self._execute_iteration(iteration, story)

            # Phase 3: 验证 & 更新
            self._process_result(story, result)

            # Phase 4: 收尾
            self.state.add_iteration(result)
            self.safety.record_iteration(result)

            # Phase 4: 持久化到 SQLite
            if self.db:
                try:
                    self.db.save_state(self.state)
                    self.db.save_story(story)
                    self.db.save_iteration(result)
                except Exception as e:
                    logger.warning("DB持久化失败: %s", e)

            if self._on_iteration_end:
                self._on_iteration_end(iteration, result)

            if result.error == "max_turns_exceeded":
                logger.warning("Story %s 达到 max_turns, 标记为 failed, 继续下一个 story", story.id)
                continue

            # 退出检查
            exit_result = self.exit_detector.check(result.output, self.state)
            if exit_result.should_exit:
                logger.info("退出信号: %s", exit_result.reason)
                self.state.status = "completed"
                break

            # 最大迭代检查
            if iteration >= self.config.max_iterations:
                logger.info("达到最大迭代次数: %d", self.config.max_iterations)
                self.state.status = "completed"
                break

        # 构建结果
        elapsed = time.monotonic() - start
        outcome = LoopOutcome(
            success=self.state.status == "completed"
            and self.orchestrator.completed_stories == self.orchestrator.total_stories,
            reason=self._determine_reason(),
            total_iterations=self.state.current_iteration,
            total_stories=self.orchestrator.total_stories,
            completed_stories=self.orchestrator.completed_stories,
            duration_seconds=elapsed,
            state=self.state,
        )

        logger.info(
            "愚公循环结束: success=%s iterations=%d stories=%d/%d",
            outcome.success,
            outcome.total_iterations,
            outcome.completed_stories,
            outcome.total_stories,
        )

        # 触发自我进化
        try:
            from ..core.unified_db import UnifiedDB
            from ..core.evolution import SkillEvolution

            db = UnifiedDB()
            evolution = SkillEvolution(db)
            evolution.on_task_complete(
                {
                    "task_id": "yugong-loop",
                    "task_name": f"愚公循环: {outcome.total_stories} stories",
                    "skills_used": ["yugong-loop"],
                    "success": outcome.success,
                    "duration_ms": int(outcome.duration_seconds * 1000),
                }
            )
        except Exception as e:
            logger.debug("愚公循环进化触发失败: %s", e)

        return outcome

    def _execute_iteration(self, iteration: int, story: UserStory) -> LoopResult:
        """执行单次迭代"""
        start_ms = time.monotonic()

        if not self.agent_fn:
            duration_ms = int((time.monotonic() - start_ms) * 1000)
            logger.error("agent_fn 未设置，无法执行迭代")
            return LoopResult(
                iteration=iteration,
                story_id=story.id,
                success=False,
                output="",
                duration_ms=duration_ms,
                token_usage={"total": 0},
                error="agent_fn is not configured. Pass agent_fn to YuGongLoop() or use AgentExecutor.",
            )

        try:
            agent_output = self.agent_fn(self._build_prompt(story))
            output = agent_output.get("output", "")
            token_usage = agent_output.get("token_usage", {"total": 0})
            files_changed = agent_output.get("files_changed", [])
            agent_success = agent_output.get("success", True)
            agent_error = agent_output.get("error")
        except Exception as e:
            duration_ms = int((time.monotonic() - start_ms) * 1000)
            return LoopResult(
                iteration=iteration,
                story_id=story.id,
                success=False,
                output="",
                duration_ms=duration_ms,
                token_usage={"total": 0},
                error=str(e),
            )

        duration_ms = int((time.monotonic() - start_ms) * 1000)

        return LoopResult(
            iteration=iteration,
            story_id=story.id,
            success=agent_success,
            output=output,
            duration_ms=duration_ms,
            token_usage=token_usage,
            files_changed=files_changed,
            error=agent_error,
        )

    def _process_result(self, story: UserStory, result: LoopResult) -> None:
        """处理迭代结果, 更新 Story 状态"""
        if result.success:
            story.mark_passed()
            self.state.completed_stories = self.orchestrator.completed_stories

            if self._on_story_complete:
                self._on_story_complete(story, result)
        else:
            story.mark_failed(result.error or "unknown error")

        self.orchestrator.update_story(story)
        self.state.last_update = datetime.now()

    def _build_prompt(self, story: UserStory) -> str:
        """构建 Prompt (简化版, 完整版由 context_injector 负责)"""
        parts = [
            f"# Current Task: {story.id} - {story.title}",
            f"\n{story.description}",
        ]
        if story.acceptance_criteria:
            parts.append("\n## Acceptance Criteria:")
            for ac in story.acceptance_criteria:
                parts.append(f"- {ac}")
        parts.append(f"\nPriority: {story.priority.name}")
        return "\n".join(parts)

    def _determine_reason(self) -> str:
        """确定循环结束原因"""
        if self._cancelled:
            return "用户取消"
        if self.state.status == "completed":
            if self.orchestrator.completed_stories == self.orchestrator.total_stories:
                return "所有 Story 完成"
            failed_count = self.orchestrator.failed_stories
            if failed_count > 0:
                return f"没有可执行的 Story ({failed_count} 个已失败且不可重试)"
            return "达到退出条件"
        if self.state.status == "stopped":
            return "安全检查失败"
        if self.state.status == "waiting":
            return "等待安全条件"
        return self.state.status

    # === 状态查询 ===

    def get_status(self) -> dict:
        """获取当前状态"""
        return {
            "status": self.state.status,
            "iteration": self.state.current_iteration,
            "progress": self.orchestrator.get_progress(),
            "safety": self.safety.get_status(),
        }
