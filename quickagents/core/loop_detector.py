"""
LoopDetector V3 - 基于失败检测的循环检测器

核心特性:
- 分段固定阈值（稳定可预测）
- 失败检测（区分临时/永久错误）
- 指数退避重试（OpenCode 方式）
- 持久化存储（UnifiedDB）
- 完全用户可配置

版本: 3.0.0
创建时间: 2026-03-31
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any


# ============================================================================
# 枚举定义
# ============================================================================


class AgentState(Enum):
    """Agent 状态"""

    IDLE = "idle"  # 空闲
    BUSY = "busy"  # 工作中
    RETRY = "retry"  # 重试中
    STUCK = "stuck"  # 卡住
    DONE = "done"  # 完成


class ThresholdStrategy(Enum):
    """阈值策略"""

    STRICT = "strict"  # 严格：same=2, consecutive=3
    NORMAL = "normal"  # 正常：same=3, consecutive=5（默认）
    RELAXED = "relaxed"  # 宽松：same=5, consecutive=8
    AGGRESSIVE = "aggressive"  # 激进：连续3次失败即触发


class FailureType(Enum):
    """失败类型"""

    TRANSIENT = "transient"  # 临时错误（可重试）
    PERMANENT = "permanent"  # 永久错误（不可重试）
    UNKNOWN = "unknown"  # 未知错误


# ============================================================================
# 数据类定义
# ============================================================================


@dataclass
class FailureRecord:
    """失败记录"""

    tool_name: str
    tool_args: Dict[str, Any]
    error_message: str
    error_type: FailureType
    timestamp: float
    fingerprint: str


@dataclass
class ToolCallRecord:
    """工具调用记录"""

    tool_name: str
    tool_args: Dict[str, Any]
    success: bool
    timestamp: float
    fingerprint: str


@dataclass
class LoopDetectorConfig:
    """LoopDetector 配置（完全用户可配置）

    配置文件位置: quickagents.json
        {
            "loop_detector": {
                "threshold_strategy": "normal",
                "same_failure_threshold": 3,
                ...
            }
        }
    """

    # 阈值策略
    threshold_strategy: ThresholdStrategy = ThresholdStrategy.NORMAL

    # 固定阈值（可手动覆盖策略默认值）
    same_failure_threshold: Optional[int] = None
    consecutive_failure_threshold: Optional[int] = None

    # 预算限制
    max_tool_calls: int = 100
    max_time_seconds: int = 600

    # 重试机制（OpenCode 方式）
    max_retries: int = 5
    backoff_base_ms: int = 2000
    backoff_multiplier: int = 2
    max_backoff_ms: int = 30000

    # 临时错误模式（用于错误分类）
    transient_error_patterns: List[str] = field(
        default_factory=lambda: [
            "timeout",
            "rate_limit",
            "rate limit",
            "network",
            "temporarily",
            "unavailable",
            "connection reset",
            "econnreset",
            "econnrefused",
            "etimedout",
        ]
    )

    # 深度检测触发频率
    deep_check_interval: int = 5  # 每5次调用触发一次深度检测

    @classmethod
    def from_file(cls, config_path: str = "quickagents.json") -> "LoopDetectorConfig":
        """从配置文件加载

        Args:
            config_path: 配置文件路径

        Returns:
            LoopDetectorConfig 实例
        """
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                    loop_config = config_data.get("loop_detector", {})

                    # 处理阈值策略
                    if "threshold_strategy" in loop_config:
                        try:
                            loop_config["threshold_strategy"] = ThresholdStrategy(
                                loop_config["threshold_strategy"]
                            )
                        except ValueError:
                            # 无效的策略值，使用默认值
                            loop_config["threshold_strategy"] = ThresholdStrategy.NORMAL

                    return cls(**loop_config)
            except (json.JSONDecodeError, IOError):
                pass  # 配置文件读取失败，使用默认配置

        return cls()

    def get_thresholds(self) -> Tuple[int, int]:
        """获取当前阈值（根据策略或手动覆盖）

        Returns:
            (same_failure_threshold, consecutive_failure_threshold)
        """
        # 策略对应的默认阈值
        strategy_thresholds = {
            ThresholdStrategy.STRICT: (2, 3),
            ThresholdStrategy.NORMAL: (3, 5),
            ThresholdStrategy.RELAXED: (5, 8),
            ThresholdStrategy.AGGRESSIVE: (3, 3),
        }

        default_same, default_consecutive = strategy_thresholds.get(
            self.threshold_strategy, (3, 5)
        )

        # 允许手动覆盖
        same = (
            self.same_failure_threshold
            if self.same_failure_threshold is not None
            else default_same
        )
        consecutive = (
            self.consecutive_failure_threshold
            if self.consecutive_failure_threshold is not None
            else default_consecutive
        )

        return (same, consecutive)


# ============================================================================
# 主类实现
# ============================================================================


class LoopDetector:
    """
    LoopDetector V3 - 基于失败检测的循环检测器

    核心特性：
    - 分段固定阈值（稳定可预测）
    - 失败检测（区分临时/永久错误）
    - 指数退避重试（OpenCode 方式）
    - 持久化存储（UnifiedDB）

    使用方式:
        detector = LoopDetector()

        # 记录工具调用
        is_loop, info = detector.check('read', {'path': 'file.md'})

        # 记录失败的调用
        is_loop, info = detector.check(
            'read',
            {'path': 'file.md'},
            result={'error': 'file not found'}
        )

        if is_loop:
            print(f"检测到循环: {info}")
    """

    def __init__(self, config: Optional[LoopDetectorConfig] = None):
        """
        初始化检测器

        Args:
            config: 配置实例（可选，默认从文件加载）
        """
        self.config = config or LoopDetectorConfig.from_file()

        # 状态
        self.state = AgentState.IDLE
        self.failure_history: List[FailureRecord] = []
        self.call_history: List[ToolCallRecord] = []
        self.session_start_time = time.time()

        # 计数器
        self.total_calls = 0
        self.consecutive_failures = 0

        # 指纹缓存（用于快速统计相同失败）
        self._fingerprint_cache: Dict[str, int] = {}

        # 持久化（延迟加载）
        self._db = None
        self._load_from_db()

    # ========================================================================
    # 核心方法
    # ========================================================================

    def check(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        result: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        检查工具调用是否触发循环

        Args:
            tool_name: 工具名称
            tool_args: 工具参数
            result: 工具执行结果（可选）
                - None: 调用前检查（仅预算检查）
                - {'error': '...'}: 调用失败
                - {'success': False}: 显式失败
                - {'success': True}: 成功

        Returns:
            (is_loop, info)
            - is_loop: 是否检测到循环
            - info: 详细信息
        """
        now = time.time()
        fingerprint = self._calculate_fingerprint(tool_name, tool_args)

        # 1. 检查预算
        budget_exceeded, budget_info = self._check_budget(now)
        if budget_exceeded:
            self.state = AgentState.STUCK
            return True, {
                "type": "budget_exceeded",
                "state": self.state.value,
                **budget_info,
            }

        # 2. 记录调用
        self._record_call(tool_name, tool_args, fingerprint, result)

        # 3. 如果有结果，分析失败
        failure_info: Dict[str, Any] = {}
        if result is not None:
            is_failure, failure_info = self._analyze_result(result)

            if is_failure:
                # 记录失败
                self._record_failure(tool_name, tool_args, fingerprint, failure_info)

                # 检查失败阈值
                failure_exceeded, failure_pattern = self._check_failure_threshold(
                    fingerprint
                )

                if failure_exceeded:
                    self.state = AgentState.STUCK
                    return True, {
                        "type": "failure_loop",
                        "state": self.state.value,
                        **failure_pattern,
                        **failure_info,  # 包含错误类型信息
                    }
            else:
                # 成功调用，重置连续失败计数
                self.consecutive_failures = 0

        # 4. 更新状态
        self._update_state()

        # 5. 返回正常（包含 failure_info）
        return False, {
            "state": self.state.value,
            "total_calls": self.total_calls,
            "consecutive_failures": self.consecutive_failures,
            **failure_info,  # 包含错误类型信息（即使未超过阈值）
        }

    def get_backoff_delay(self, attempt: int) -> int:
        """
        获取退避延迟（OpenCode 方式）

        指数退避计算:
        - attempt=1: 2000ms
        - attempt=2: 4000ms
        - attempt=3: 8000ms
        - attempt=4: 16000ms
        - attempt=5: 30000ms (cap)

        Args:
            attempt: 重试次数（1-based）

        Returns:
            延迟毫秒数
        """
        if attempt < 1:
            return 0

        delay = self.config.backoff_base_ms * (
            self.config.backoff_multiplier ** (attempt - 1)
        )
        return min(delay, self.config.max_backoff_ms)

    # ========================================================================
    # 内部方法
    # ========================================================================

    def _check_budget(self, now: float) -> Tuple[bool, Dict[str, Any]]:
        """检查预算是否超限"""
        # 检查调用次数
        if self.total_calls >= self.config.max_tool_calls:
            return True, {
                "reason": "max_tool_calls_exceeded",
                "limit": self.config.max_tool_calls,
                "current": self.total_calls,
            }

        # 检查时间
        elapsed = now - self.session_start_time
        if elapsed >= self.config.max_time_seconds:
            return True, {
                "reason": "max_time_exceeded",
                "limit": self.config.max_time_seconds,
                "elapsed": round(elapsed, 1),
            }

        return False, {}

    def _analyze_result(self, result: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """分析结果是否为失败"""
        # 检查显式错误
        if result.get("error"):
            error_msg = str(result["error"])
            error_type = self._classify_error(error_msg)
            return True, {
                "error": error_msg,
                "error_type": error_type.value,
                "is_transient": error_type == FailureType.TRANSIENT,
            }

        # 检查显式失败
        if result.get("success") is False:
            return True, {
                "error": "explicit_failure",
                "error_type": FailureType.PERMANENT.value,
                "is_transient": False,
            }

        return False, {}

    def _classify_error(self, error_message: str) -> FailureType:
        """分类错误类型"""
        error_lower = error_message.lower()

        for pattern in self.config.transient_error_patterns:
            if pattern.lower() in error_lower:
                return FailureType.TRANSIENT

        return FailureType.PERMANENT

    def _check_failure_threshold(self, fingerprint: str) -> Tuple[bool, Dict[str, Any]]:
        """检查失败是否超过阈值"""
        same_threshold, consecutive_threshold = self.config.get_thresholds()

        # 1. 检查相同失败次数
        same_failures = self._fingerprint_cache.get(fingerprint, 0)
        if same_failures >= same_threshold:
            return True, {
                "pattern": "same_failure_exceeded",
                "fingerprint": fingerprint[:16],
                "count": same_failures,
                "threshold": same_threshold,
            }

        # 2. 检查连续失败次数
        if self.consecutive_failures >= consecutive_threshold:
            return True, {
                "pattern": "consecutive_failure_exceeded",
                "count": self.consecutive_failures,
                "threshold": consecutive_threshold,
            }

        return False, {}

    def _calculate_fingerprint(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """计算工具调用指纹"""
        # 敏感参数脱敏
        sanitized_args = self._sanitize_args(tool_args)
        normalized = json.dumps(sanitized_args, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(f"{tool_name}:{normalized}".encode("utf-8")).hexdigest()

    def _sanitize_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """脱敏敏感参数"""
        if not args:
            return {}

        sensitive_keys = {"password", "token", "api_key", "secret", "credential", "key"}
        sanitized = {}

        for key, value in args.items():
            if key.lower() in sensitive_keys or any(
                s in key.lower() for s in sensitive_keys
            ):
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value

        return sanitized

    def _record_call(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        fingerprint: str,
        result: Optional[Dict[str, Any]],
    ):
        """记录工具调用"""
        self.total_calls += 1

        record = ToolCallRecord(
            tool_name=tool_name,
            tool_args=tool_args,
            success=result is None or result.get("success", True),
            timestamp=time.time(),
            fingerprint=fingerprint,
        )

        self.call_history.append(record)

        # 保持历史在合理范围
        if len(self.call_history) > 100:
            self.call_history = self.call_history[-50:]

    def _record_failure(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        fingerprint: str,
        failure_info: Dict[str, Any],
    ):
        """记录失败"""
        self.consecutive_failures += 1
        self._fingerprint_cache[fingerprint] = (
            self._fingerprint_cache.get(fingerprint, 0) + 1
        )

        record = FailureRecord(
            tool_name=tool_name,
            tool_args=tool_args,
            error_message=failure_info.get("error", ""),
            error_type=FailureType(failure_info.get("error_type", "unknown")),
            timestamp=time.time(),
            fingerprint=fingerprint,
        )

        self.failure_history.append(record)

        # 保持历史在合理范围
        if len(self.failure_history) > 50:
            self.failure_history = self.failure_history[-25:]

    def _update_state(self):
        """更新状态"""
        if self.consecutive_failures == 0:
            if self.total_calls > 0:
                self.state = AgentState.BUSY
        elif self.consecutive_failures > 0 and self.consecutive_failures < 3:
            self.state = AgentState.RETRY
        # STUCK 状态由检测到循环时设置

    # ========================================================================
    # 持久化方法
    # ========================================================================

    def _load_from_db(self):
        """从 UnifiedDB 加载状态"""
        try:
            from .unified_db import get_unified_db

            self._db = get_unified_db()
            # 暂时不实现历史状态加载，每次会话重新开始
        except Exception:
            pass  # UnifiedDB 不可用，使用内存状态

    def _save_to_db(self):
        """保存状态到 UnifiedDB"""
        try:
            if self._db is None:
                from .unified_db import get_unified_db

                self._db = get_unified_db()
            # 暂时不实现持久化，每次会话重新开始
        except Exception:
            pass

    # ========================================================================
    # 公共方法
    # ========================================================================

    def reset(self):
        """重置检测器状态"""
        self.state = AgentState.IDLE
        self.failure_history.clear()
        self.call_history.clear()
        self.consecutive_failures = 0
        self.total_calls = 0
        self._fingerprint_cache.clear()
        self.session_start_time = time.time()

    def get_status(self) -> Dict[str, Any]:
        """获取检测器状态"""
        same_threshold, consecutive_threshold = self.config.get_thresholds()

        return {
            "state": self.state.value,
            "total_calls": self.total_calls,
            "consecutive_failures": self.consecutive_failures,
            "failure_count": len(self.failure_history),
            "thresholds": {
                "same_failure": same_threshold,
                "consecutive_failure": consecutive_threshold,
            },
            "config": {
                "strategy": self.config.threshold_strategy.value,
                "max_tool_calls": self.config.max_tool_calls,
                "max_time_seconds": self.config.max_time_seconds,
            },
        }

    def get_tool_call_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取工具调用历史"""
        history = self.call_history[-limit:]
        return [
            {
                "tool": record.tool_name,
                "args": record.tool_args,
                "success": record.success,
                "timestamp": record.timestamp,
            }
            for record in history
        ]

    def analyze_patterns(self) -> Dict[str, Any]:
        """分析工具调用模式"""
        if not self.call_history:
            return {
                "total_calls": 0,
                "unique_tools": 0,
                "tool_distribution": {},
                "failure_distribution": {},
                "state": self.state.value,
            }

        from collections import Counter

        # 统计工具使用分布
        tool_counter = Counter(record.tool_name for record in self.call_history)

        # 统计失败分布
        failure_counter = Counter(record.tool_name for record in self.failure_history)

        return {
            "total_calls": len(self.call_history),
            "unique_tools": len(tool_counter),
            "tool_distribution": dict(tool_counter.most_common(10)),
            "failure_distribution": dict(failure_counter.most_common(10)),
            "state": self.state.value,
            "thresholds": self.config.get_thresholds(),
        }


# ============================================================================
# 全局实例
# ============================================================================

_global_detector: Optional[LoopDetector] = None


def get_loop_detector() -> LoopDetector:
    """获取全局循环检测器"""
    global _global_detector
    if _global_detector is None:
        _global_detector = LoopDetector()
    return _global_detector


def reset_loop_detector():
    """重置全局循环检测器"""
    global _global_detector
    if _global_detector is not None:
        _global_detector.reset()
    _global_detector = None
