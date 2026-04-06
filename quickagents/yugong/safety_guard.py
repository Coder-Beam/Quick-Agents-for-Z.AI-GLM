"""
愚公循环安全守护

复用 LoopDetector V3 + 新增:
- 速率限制 (每小时 API 调用限制)
- Token 预算
- 熔断器 (CLOSED → HALF_OPEN → OPEN)
- API 5小时限制 (4h50m预警, 5h硬停止)
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from .config import YuGongConfig
from .models import LoopResult

logger = logging.getLogger(__name__)


@dataclass
class SafetyCheckResult:
    """安全检查结果"""

    safe: bool
    reason: str
    should_wait: bool = False
    wait_seconds: int = 0


class SafetyGuard:
    """安全守护"""

    def __init__(self, config: YuGongConfig):
        self.config = config

        # 尝试导入 LoopDetector (可选依赖)
        self._loop_detector = None
        try:
            from ..core.loop_detector import LoopDetector

            self._loop_detector = LoopDetector()
        except ImportError as e:
            logger.debug("LoopDetector not available, loop detection disabled: %s", e)

        # 速率限制
        self.hourly_calls: int = 0
        self.hourly_tokens: int = 0
        self.hour_start: datetime = datetime.now()

        # 循环开始时间 (API 5h 限制)
        self.loop_start_time: datetime = datetime.now()

        # 熔断器状态
        self.circuit_breaker_open: bool = False
        self.circuit_breaker_open_time: Optional[datetime] = None
        self.consecutive_no_progress: int = 0
        self.error_counts: dict[str, int] = {}

    def check_before_iteration(self) -> SafetyCheckResult:
        """每次迭代前检查是否安全"""

        # 0. 重置小时计数器（如果已过1小时）
        self._reset_hourly_if_needed()

        # 1. API 5小时硬停止
        if self.config.api_5h_limit_hard_stop:
            elapsed = (datetime.now() - self.loop_start_time).total_seconds()
            if elapsed >= 5 * 3600:
                return SafetyCheckResult(False, "API 5小时限制已到达，强制暂停")

        # 2. API 5小时预警
        elapsed = (datetime.now() - self.loop_start_time).total_seconds()
        warning_at = (5 * 3600) - (self.config.api_5h_limit_warning_minutes * 60)
        if warning_at <= elapsed < 5 * 3600:
            remaining_min = int((5 * 3600 - elapsed) / 60)
            return SafetyCheckResult(
                True,
                f"⚠️ 接近API 5小时限制，剩余约{remaining_min}分钟 (warning)",
            )

        # 3. 熔断器
        if self.circuit_breaker_open:
            if self._should_attempt_recovery():
                return SafetyCheckResult(True, "熔断器尝试恢复 (HALF_OPEN)")
            remaining = self._remaining_cooldown_seconds()
            return SafetyCheckResult(
                False,
                f"熔断器已打开，冷却中 (需等待{remaining}秒)",
                should_wait=True,
                wait_seconds=remaining,
            )

        # 4. 速率限制
        if self.config.max_calls_per_hour > 0:
            if self.hourly_calls >= self.config.max_calls_per_hour:
                return SafetyCheckResult(
                    False,
                    f"达到每小时调用限制({self.config.max_calls_per_hour})",
                    should_wait=True,
                    wait_seconds=self._seconds_until_next_hour(),
                )

        # 5. Token 预算
        if self.config.max_tokens_per_hour > 0:
            if self.hourly_tokens >= self.config.max_tokens_per_hour:
                return SafetyCheckResult(
                    False,
                    f"达到每小时Token预算({self.config.max_tokens_per_hour})",
                    should_wait=True,
                    wait_seconds=self._seconds_until_next_hour(),
                )

        # 6. LoopDetector (可选)
        if self._loop_detector:
            try:
                is_loop, info = self._loop_detector.check("yugong_iteration", {})
                if is_loop:
                    return SafetyCheckResult(False, f"检测到循环模式: {info}")
            except Exception as e:
                logger.debug(f"LoopDetector check failed: {e}")

        return SafetyCheckResult(True, "安全")

    def record_iteration(self, result: LoopResult) -> None:
        """记录迭代结果"""
        self.hourly_calls += 1
        self.hourly_tokens += result.token_usage.get("total", 0)

        if self._loop_detector:
            try:
                self._loop_detector.record_tool_call("yugong_iteration", result.to_dict())
            except Exception as e:
                logger.debug(f"LoopDetector record failed: {e}")

        if not result.success:
            self.consecutive_no_progress += 1
            error_key = (result.error or "unknown")[:100]
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

            if self.consecutive_no_progress >= self.config.cb_no_progress_threshold:
                self._open_circuit_breaker("连续无进展")
            elif self.error_counts[error_key] >= self.config.cb_same_error_threshold:
                self._open_circuit_breaker(f"重复错误: {error_key}")
        else:
            self.consecutive_no_progress = 0

    def reset_circuit_breaker(self) -> None:
        """手动重置熔断器"""
        self.circuit_breaker_open = False
        self.circuit_breaker_open_time = None
        self.consecutive_no_progress = 0
        self.error_counts.clear()

    def get_status(self) -> dict:
        """返回安全状态"""
        return {
            "hourly_calls": self.hourly_calls,
            "hourly_tokens": self.hourly_tokens,
            "max_calls_per_hour": self.config.max_calls_per_hour,
            "max_tokens_per_hour": self.config.max_tokens_per_hour,
            "circuit_breaker_open": self.circuit_breaker_open,
            "consecutive_no_progress": self.consecutive_no_progress,
            "error_counts": self.error_counts,
            "loop_elapsed_minutes": (datetime.now() - self.loop_start_time).total_seconds() / 60,
        }

    # === 私有方法 ===

    def _reset_hourly_if_needed(self) -> None:
        now = datetime.now()
        if (now - self.hour_start) >= timedelta(hours=1):
            self.hourly_calls = 0
            self.hourly_tokens = 0
            self.hour_start = now

    def _open_circuit_breaker(self, reason: str) -> None:
        self.circuit_breaker_open = True
        self.circuit_breaker_open_time = datetime.now()

    def _should_attempt_recovery(self) -> bool:
        if not self.circuit_breaker_open_time:
            return False
        elapsed_min = (datetime.now() - self.circuit_breaker_open_time).total_seconds() / 60
        return elapsed_min >= self.config.cb_cooldown_minutes

    def _remaining_cooldown_seconds(self) -> int:
        if not self.circuit_breaker_open_time:
            return 0
        elapsed = (datetime.now() - self.circuit_breaker_open_time).total_seconds()
        remaining = self.config.cb_cooldown_minutes * 60 - elapsed
        return max(0, int(remaining))

    def _seconds_until_next_hour(self) -> int:
        now = datetime.now()
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        return int((next_hour - now).total_seconds())
