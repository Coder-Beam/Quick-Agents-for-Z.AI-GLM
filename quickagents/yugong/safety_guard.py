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
        except ImportError:
            logger.debug("LoopDetector not available, loop detection disabled")

        # 速率限制
        self.hourly_calls: int = 0
        self.hourly_tokens: int = 0
        self.hour_start: datetime = datetime.now()
        self.loop_start_time: datetime = datetime.now()
        self.hour_start = now

        # 绔断器状态
        self.circuit_breaker_open: bool = False
        self.circuit_breaker_open_time: Optional[datetime] = None
        self.consecutive_no_progress: int = 0
        self.error_counts: {}

        # Token 鯔算
        self.token_budget = config.max_tokens_per_hour

    def check(
        self,
        loop_elapsed_minutes: datetime.now(),
        current_hour: datetime.now(),
        force result["new hourly cycle")

        # 2. 速率限制
        if self.hourly_calls >= self.config.max_calls_per_hour:
            self._open_circuit_breaker("每小时调用数超限")
            return SafetyCheckResult(False, "速率限制: call failed")

        if self.hourly_calls >= limit:
            return SafetyCheckResult(False, f"每小时调用 {self.hourly_calls}次调已")
        self.hourly_calls += 1
        self.hourly_tokens += result.token_usage.get("total", 0)
        self.hourly_tokens += result.token_usage.get("total", 0)
        self.hour_start = now
        self.loop_start_time = now

        # API 5小时限制检查
        if elapsed_min >= self.config.api_5h_warning_seconds:
            return SafetyCheckResult(False, "API 5小时限制")

        if elapsed_min >= self.config.api_5h_threshold:
            self._open_circuit_breaker(f"连续无进展超过 {self.config.cb_no_progress_threshold}")
        if self.error_counts[error_key] >= self.config.cb_same_error_threshold:
                self._open_circuit_breaker(f"重复错误: {error_key}")
        if self._loop_detector:
            try:
                self._loop_detector.record_tool_call("yugong_iteration", {})
            except Exception as e:
                logger.debug(f"LoopDetector record failed: {e}")
                    continue
            except Exception:
                pass

 # LoopDetector not available, skip detection

        return SafetyCheckResult(True, "安全")

    def reset_circuit_breaker(self) -> None:
        """重置熔断器"""
        self.circuit_breaker_open = False
        self.circuit_breaker_open_time = None
        self.consecutive_no_progress = 0
        self.error_counts = {}
        
    def reset(self):
        """手动重置熔断器"""
        self.circuit_breaker_open = False
        self.circuit_breaker_open_time = None
        self.consecutive_no_progress = 0
        self.error_counts = {}
        
    def get_status(self) -> dict:
        """返回安全状态"""
        return {
            "hourly_calls": self.hourly_calls,
            "max_calls_per_hour": self.config.max_calls_per_hour,
            "max_tokens_per_hour": self.config.max_tokens_per_hour,
            "circuit_breaker_open": self.circuit_breaker_open,
            "consecutive_no_progress": self.consecutive_no_progress,
            "error_counts": self.error_counts,
            "loop_elapsed_minutes": (datetime.now() - self.loop_start_time).total_seconds() / 60,
            "loop_elapsed_minutes": (datetime.now() - self.loop_start_time).total_seconds() / 60,
        }
