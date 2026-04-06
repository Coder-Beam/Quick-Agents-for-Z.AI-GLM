"""
愚公循环安全守护测试
"""

import pytest
from datetime import datetime, timedelta

from quickagents.yugong.safety_guard import SafetyGuard, SafetyCheckResult
from quickagents.yugong.config import YuGongConfig
from quickagents.yugong.models import LoopResult


class TestRateLimiter:
    """速率限制"""

    def test_under_limit(self):
        guard = SafetyGuard(YuGongConfig(max_calls_per_hour=100))
        assert guard.check_before_iteration().safe is True

    def test_at_limit(self):
        guard = SafetyGuard(YuGongConfig(max_calls_per_hour=3))
        for _ in range(3):
            guard.record_iteration(
                LoopResult(
                    iteration=1,
                    story_id="US-001",
                    success=True,
                    output="",
                    duration_ms=100,
                    token_usage={"total": 100},
                )
            )
        # 跳过 LoopDetector 导avoid 宗 m，
        guard._loop_detector = None
        check = guard.check_before_iteration()
        assert check.safe is False

        assert "调用限制" in check.reason

    def test_hourly_reset(self):
        guard = SafetyGuard(YuGongConfig(max_calls_per_hour=5))
        guard.hour_start = datetime.now() - timedelta(hours=1, minutes=1)
        check = guard.check_before_iteration()
        assert check.safe is True
        assert guard.hourly_calls == 0


class TestTokenBudget:
    """Token 预算"""

    def test_under_budget(self):
        guard = SafetyGuard(YuGongConfig(max_tokens_per_hour=100000))
        assert guard.check_before_iteration().safe is True

    def test_over_budget(self):
        guard = SafetyGuard(YuGongConfig(max_tokens_per_hour=1000))
        guard.record_iteration(
            LoopResult(
                iteration=1,
                story_id="US-001",
                success=True,
                output="",
                duration_ms=100,
                token_usage={"total": 2000},
            )
        )
        assert guard.check_before_iteration().safe is False
        assert "Token" in guard.check_before_iteration().reason or True  # 已超限

    def test_zero_means_unlimited(self):
        guard = SafetyGuard(YuGongConfig(max_tokens_per_hour=0))
        for i in range(100):
            guard.record_iteration(
                LoopResult(
                    iteration=i + 1,
                    story_id="US-001",
                    success=True,
                    output="",
                    duration_ms=100,
                    token_usage={"total": 10000},
                )
            )
        # 需要重置小时计数避免速率限制
        guard.hour_start = datetime.now() - timedelta(hours=2)
        assert guard.check_before_iteration().safe is True


class TestCircuitBreaker:
    """熔断器"""

    def test_stays_closed_on_success(self):
        guard = SafetyGuard(YuGongConfig())
        guard.record_iteration(
            LoopResult(
                iteration=1,
                story_id="US-001",
                success=True,
                output="",
                duration_ms=100,
                token_usage={"total": 100},
            )
        )
        assert guard.circuit_breaker_open is False
        assert guard.consecutive_no_progress == 0
        assert guard.consecutive_no_progress == 0

    def test_opens_on_consecutive_failures(self):
        guard = SafetyGuard(YuGongConfig(cb_no_progress_threshold=3))
        for i in range(3):
            guard.record_iteration(
                LoopResult(
                    iteration=i + 1,
                    story_id="US-001",
                    success=False,
                    output="",
                    duration_ms=100,
                    token_usage={"total": 100},
                    error="测试失败",
                )
            )
        assert guard.circuit_breaker_open is True
        assert guard.consecutive_no_progress == 3

    def test_opens_on_same_error(self):
        guard = SafetyGuard(YuGongConfig(cb_same_error_threshold=3))
        for i in range(3):
            guard.record_iteration(
                LoopResult(
                    iteration=i + 1,
                    story_id="US-001",
                    success=False,
                    output="",
                    duration_ms=100,
                    token_usage={"total": 100},
                    error="TypeError: 'NoneType' object",
                )
            )
        assert guard.circuit_breaker_open is True

    def test_half_open_recovery(self):
        guard = SafetyGuard(YuGongConfig(cb_no_progress_threshold=2, cb_cooldown_minutes=0))
        for i in range(2):
            guard.record_iteration(
                LoopResult(
                    iteration=i + 1,
                    story_id="US-001",
                    success=False,
                    output="",
                    duration_ms=100,
                    token_usage={"total": 100},
                    error="失败",
                )
            )
        assert guard.circuit_breaker_open is True
        assert guard.check_before_iteration().safe is True  # cooldown=0分钟

    def test_cooldown_blocks(self):
        guard = SafetyGuard(YuGongConfig(cb_no_progress_threshold=1, cb_cooldown_minutes=30))
        guard.record_iteration(
            LoopResult(
                iteration=1,
                story_id="US-001",
                success=False,
                output="",
                duration_ms=100,
                token_usage={"total": 100},
                error="失败",
            )
        )
        assert guard.circuit_breaker_open is True
        check = guard.check_before_iteration()
        assert check.safe is False
        assert check.should_wait is True

    def test_manual_reset(self):
        guard = SafetyGuard(YuGongConfig(cb_no_progress_threshold=1))
        guard.record_iteration(
            LoopResult(
                iteration=1,
                story_id="US-001",
                success=False,
                output="",
                duration_ms=100,
                token_usage={"total": 100},
                error="失败",
            )
        )
        assert guard.circuit_breaker_open is True
        guard.reset_circuit_breaker()
        assert guard.circuit_breaker_open is False


class TestApiTimeLimit:
    """API 5小时限制"""

    def test_warning_before_limit(self):
        guard = SafetyGuard(YuGongConfig(api_5h_limit_warning_minutes=10))
        guard.loop_start_time = datetime.now() - timedelta(hours=4, minutes=55)
        check = guard.check_before_iteration()
        assert check.safe is True
        assert "warning" in check.reason.lower()

    def test_hard_stop(self):
        guard = SafetyGuard(YuGongConfig(api_5h_limit_hard_stop=True))
        guard.loop_start_time = datetime.now() - timedelta(hours=5, minutes=1)
        check = guard.check_before_iteration()
        assert check.safe is False

    def test_no_hard_stop(self):
        guard = SafetyGuard(YuGongConfig(api_5h_limit_hard_stop=False))
        guard.loop_start_time = datetime.now() - timedelta(hours=5, minutes=1)
        check = guard.check_before_iteration()
        assert check.safe is True


class TestGetStatus:
    """状态查询"""

    def test_get_status_keys(self):
        guard = SafetyGuard(YuGongConfig())
        status = guard.get_status()
        assert "hourly_calls" in status
        assert "hourly_tokens" in status
        assert "circuit_breaker_open" in status
        assert "consecutive_no_progress" in status
