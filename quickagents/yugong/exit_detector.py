"""
愚公循环智能退出检测

基于 frankbria/ralph-claude-code 的双条件门设计:
- 条件1: completion_indicators >= threshold (语义模式匹配)
- 条件2: EXIT_SIGNAL (显式信号)
- 两个条件都满足才退出 (或所有 Story 完成)
"""

from dataclasses import dataclass

from .config import YuGongConfig
from .models import LoopState


@dataclass
class ExitCheckResult:
    """退出检查结果"""

    should_exit: bool
    reason: str
    completion_indicators: int = 0
    exit_signal: bool = False


class ExitDetector:
    """
    双条件退出检测

    三种退出路径:
    1. 所有 Story 完成 (最可靠)
    2. 双条件门: completion_indicators >= threshold AND exit_signal
    3. 达到最大迭代次数 (由循环引擎处理)
    """

    COMPLETION_PATTERNS = [
        "all tasks complete",
        "project ready",
        "all stories pass",
        "implementation complete",
        "all features implemented",
        "project is complete",
        "all requirements met",
        "<promise>COMPLETE</promise>",
        "<promise>DONE</promise>",
    ]

    EXIT_SIGNAL_PATTERNS = [
        "EXIT_SIGNAL: true",
        "EXIT_SIGNAL:true",
        "RALPH_STATUS: COMPLETE",
        "RALPH_STATUS:COMPLETE",
    ]

    def __init__(self, config: YuGongConfig):
        self.config = config

    def check(self, output: str, state: LoopState) -> ExitCheckResult:
        """执行退出检查"""

        # 检查最小迭代次数 (最高优先级)
        if state.current_iteration < self.config.min_iterations:
            return ExitCheckResult(
                False,
                f"低于最小迭代次数({state.current_iteration}<{self.config.min_iterations})",
            )

        # 路径1: 所有 Story 完成
        if state.total_stories > 0 and state.completed_stories >= state.total_stories:
            return ExitCheckResult(True, "所有UserStory已完成")

        # 统计完成指标和退出信号
        completion_count = self.count_completion_indicators(output)
        exit_signal = self.detect_exit_signal(output)

        # 路径2: 双条件门
        if completion_count >= self.config.completion_threshold and exit_signal:
            return ExitCheckResult(
                True,
                f"双条件满足: indicators={completion_count}, signal=True",
                completion_count,
                exit_signal,
            )

        return ExitCheckResult(False, "继续执行", completion_count, exit_signal)

    def count_completion_indicators(self, output: str) -> int:
        """统计输出中的完成指标数量"""
        output_lower = output.lower()
        count = 0
        for pattern in self.COMPLETION_PATTERNS:
            if pattern.lower() in output_lower:
                count += 1
        return count

    def detect_exit_signal(self, output: str) -> bool:
        """检测显式的退出信号"""
        output_lower = output.lower()
        for pattern in self.EXIT_SIGNAL_PATTERNS:
            if pattern.lower() in output_lower:
                return True
        return False
