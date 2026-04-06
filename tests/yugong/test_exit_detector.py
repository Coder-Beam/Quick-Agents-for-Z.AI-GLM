"""
愚公循环退出检测测试
"""

import pytest
from quickagents.yugong.exit_detector import ExitDetector, ExitCheckResult
from quickagents.yugong.models import LoopState
from quickagents.yugong.config import YuGongConfig


class TestAllStoriesComplete:
    """所有 Story 完成"""

    def test_all_pass(self):
        d = ExitDetector(YuGongConfig())
        state = LoopState(total_stories=5, completed_stories=5, current_iteration=5)
        assert d.check("", state).should_exit is True

    def test_not_all_pass(self):
        d = ExitDetector(YuGongConfig())
        state = LoopState(total_stories=5, completed_stories=3, current_iteration=3)
        assert d.check("", state).should_exit is False


class TestDualConditionGate:
    """双条件门"""

    def test_both_met(self):
        d = ExitDetector(YuGongConfig(completion_threshold=2, min_iterations=0))
        state = LoopState(total_stories=3, completed_stories=2, current_iteration=5)
        output = "all tasks complete. project ready.\nEXIT_SIGNAL: true"
        assert d.check(output, state).should_exit is True

    def test_only_signal(self):
        d = ExitDetector(YuGongConfig(completion_threshold=2, min_iterations=0))
        state = LoopState(total_stories=3, completed_stories=1, current_iteration=5)
        assert d.check("EXIT_SIGNAL: true", state).should_exit is False

    def test_only_indicators(self):
        d = ExitDetector(YuGongConfig(completion_threshold=2, min_iterations=0))
        state = LoopState(total_stories=3, completed_stories=1, current_iteration=5)
        assert d.check("all tasks complete. project ready.", state).should_exit is False

    def test_neither(self):
        d = ExitDetector(YuGongConfig(min_iterations=0))
        state = LoopState(total_stories=3, completed_stories=1, current_iteration=5)
        assert d.check("工作中...", state).should_exit is False


class TestMinIterations:
    """最小迭代次数"""

    def test_below_min(self):
        """测试 - 低于最小迭代次数，即使所有Story完成也不退出"""
        d = ExitDetector(YuGongConfig(min_iterations=2))
        state = LoopState(total_stories=5, completed_stories=5, current_iteration=1)
        output = "<promise>COMPLETE</promise>"
        assert d.check(output, state).should_exit is False

    def test_above_min(self):
        """测试 - 达到最小迭代次数，所有Story完成时退出"""
        d = ExitDetector(YuGongConfig(min_iterations=2))
        state = LoopState(total_stories=5, completed_stories=5, current_iteration=3)
        assert d.check("", state).should_exit is True


class TestPatternMatching:
    """模式匹配"""

    def test_promise_complete(self):
        d = ExitDetector(YuGongConfig())
        assert d.count_completion_indicators("<promise>COMPLETE</promise>") >= 1

    def test_multiple_indicators(self):
        d = ExitDetector(YuGongConfig())
        assert d.count_completion_indicators("all tasks complete. project ready.") >= 2

    def test_no_indicators(self):
        d = ExitDetector(YuGongConfig())
        assert d.count_completion_indicators("工作中...") == 0

    def test_exit_signal(self):
        d = ExitDetector(YuGongConfig())
        assert d.detect_exit_signal("EXIT_SIGNAL: true") is True
        assert d.detect_exit_signal("RALPH_STATUS: COMPLETE") is True
        assert d.detect_exit_signal("正常输出") is False
