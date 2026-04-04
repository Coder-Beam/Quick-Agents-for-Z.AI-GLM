"""
LoopDetector V3 单元测试

测试内容:
- 配置加载
- 失败检测
- 阈值检查
- 指数退避
- 状态管理
- 持久化
"""

import pytest
import time
import os
import sys

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


from quickagents.core.loop_detector import (
    LoopDetector,
    LoopDetectorConfig,
    ThresholdStrategy,
    FailureType,
    AgentState,
    get_loop_detector,
    reset_loop_detector
)


class TestLoopDetectorConfig:
    """测试 LoopDetectorConfig"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = LoopDetectorConfig()
        
        assert config.threshold_strategy == ThresholdStrategy.NORMAL
        assert config.max_tool_calls == 100
        assert config.max_time_seconds == 600
        assert config.max_retries == 5
        assert config.backoff_base_ms == 2000
        assert config.backoff_multiplier == 2
        assert config.max_backoff_ms == 30000
        assert config.deep_check_interval == 5
    
    def test_threshold_strategies(self):
        """测试阈值策略"""
        config = LoopDetectorConfig()
        
        # Normal 策略
        thresholds = config.get_thresholds()
        assert thresholds == (3, 5)
        
        # Strict 策略
        config_strict = LoopDetectorConfig(threshold_strategy=ThresholdStrategy.STRICT)
        thresholds = config_strict.get_thresholds()
        assert thresholds == (2, 3)
        
        # Relaxed 策略
        config_relaxed = LoopDetectorConfig(threshold_strategy=ThresholdStrategy.RELAXED)
        thresholds = config_relaxed.get_thresholds()
        assert thresholds == (5, 8)
        
        # Aggressive 策略
        config_aggressive = LoopDetectorConfig(threshold_strategy=ThresholdStrategy.AGGRESSIVE)
        thresholds = config_aggressive.get_thresholds()
        assert thresholds == (3, 3)
    
    def test_manual_threshold_override(self):
        """测试手动覆盖阈值"""
        config = LoopDetectorConfig(
            same_failure_threshold=10,
            consecutive_failure_threshold=15
        )
        thresholds = config.get_thresholds()
        assert thresholds == (10, 15)


    
    def test_custom_transient_error_patterns(self):
        """测试自定义临时错误模式"""
        config = LoopDetectorConfig(
            transient_error_patterns=["timeout", "network", "custom_error"]
        )
        
        assert "timeout" in config.transient_error_patterns
        assert "network" in config.transient_error_patterns
        assert "custom_error" in config.transient_error_patterns


class TestLoopDetectorBasic:
    """测试 LoopDetector 基本功能"""
    
    def setup_method(self):
        """每个测试前重置检测器"""
        reset_loop_detector()
    
    def test_initial_state(self):
        """测试初始状态"""
        detector = get_loop_detector()
        
        status = detector.get_status()
        assert status["state"] == "idle"
        assert status["total_calls"] == 0
        assert status["consecutive_failures"] == 0
    
    def test_check_no_failure(self):
        """测试无失败场景"""
        detector = LoopDetector()
        
        # 执行5次成功调用
        for i in range(5):
            is_loop, info = detector.check("read", {"path": f"file{i}.txt"})
            assert is_loop is False
        
        status = detector.get_status()
        assert status["total_calls"] == 5
        assert status["consecutive_failures"] == 0
        assert status["state"] == "busy"
    
    def test_check_with_transient_failure(self):
        """测试临时失败场景"""
        config = LoopDetectorConfig(
            threshold_strategy=ThresholdStrategy.NORMAL
        )
        detector = LoopDetector(config)
        
        # 临时失败
        result = {"error": "timeout: connection reset"}
        is_loop, info = detector.check("bash", {"cmd": "test"}, result)
        
        assert is_loop is False
        assert info.get("error_type") == "transient"
        assert info.get("is_transient") is True
    
    def test_check_with_permanent_failure(self):
        """测试永久失败场景"""
        detector = LoopDetector()
        
        # 永久失败
        result = {"error": "file not found"}
        is_loop, info = detector.check("read", {"path": "missing.txt"}, result)
        
        assert is_loop is False
        assert info.get("error_type") == "permanent"
        assert info.get("is_transient") is False


class TestLoopDetectorThresholds:
    """测试阈值检测"""
    
    def setup_method(self):
        reset_loop_detector()
    
    def test_same_failure_threshold_exceeded(self):
        """测试相同失败阈值超限"""
        config = LoopDetectorConfig(
            threshold_strategy=ThresholdStrategy.NORMAL
        )
        detector = LoopDetector(config)
        
        # 连续3次相同失败
        for i in range(3):
            result = {"error": "file not found"}
            is_loop, info = detector.check("read", {"path": "missing.txt"}, result)
        
        # 第3次应该触发循环
        assert is_loop is True
        assert info["pattern"] == "same_failure_exceeded"
        assert info["threshold"] == 3
        assert info["count"] == 3
    
    def test_consecutive_failure_threshold_exceeded(self):
        """测试连续失败阈值超限"""
        config = LoopDetectorConfig(
            threshold_strategy=ThresholdStrategy.NORMAL
        )
        detector = LoopDetector(config)
        
        # 连续5次不同失败
        for i in range(5):
            result = {"error": f"error {i}"}
            is_loop, info = detector.check("bash", {"cmd": f"cmd{i}"}, result)
        
        # 第5次应该触发循环
        assert is_loop is True
        assert info["pattern"] == "consecutive_failure_exceeded"
        assert info["threshold"] == 5
        assert info["count"] == 5
    
    def test_budget_exceeded_by_calls(self):
        """测试预算超限（调用次数)"""
        config = LoopDetectorConfig(
            max_tool_calls=5
        )
        detector = LoopDetector(config)
        
        # 执行5次调用
        for i in range(5):
            detector.check("read", {"path": f"file{i}.txt"})
        
        # 第6次应该超限
        is_loop, info = detector.check("read", {"path": "file6.txt"})
        assert is_loop is True
        assert info["type"] == "budget_exceeded"
        assert info["reason"] == "max_tool_calls_exceeded"
    
    def test_strict_strategy(self):
        """测试严格策略"""
        config = LoopDetectorConfig(
            threshold_strategy=ThresholdStrategy.STRICT
        )
        detector = LoopDetector(config)
        
        # 连续2次相同失败应该触发
        for i in range(2):
            result = {"error": "file not found"}
            is_loop, info = detector.check("read", {"path": "missing.txt"}, result)
        
        assert is_loop is True
        assert info["threshold"] == 2
    
    def test_aggressive_strategy(self):
        """测试激进策略"""
        config = LoopDetectorConfig(
            threshold_strategy=ThresholdStrategy.AGGRESSIVE
        )
        detector = LoopDetector(config)
        
        # 连续3次失败（任何类型)应该触发
        for i in range(3):
            result = {"error": f"error {i}"}
            is_loop, info = detector.check("bash", {"cmd": f"cmd{i}"}, result)
        
        assert is_loop is True
        assert info["threshold"] == 3


class TestLoopDetectorBackoff:
    """测试指数退避"""
    
    def test_backoff_delay_calculation(self):
        """测试退避延迟计算"""
        detector = LoopDetector()
        
        # OpenCode 方式的指数退避
        assert detector.get_backoff_delay(1) == 2000
        assert detector.get_backoff_delay(2) == 4000
        assert detector.get_backoff_delay(3) == 8000
        assert detector.get_backoff_delay(4) == 16000
        assert detector.get_backoff_delay(5) == 30000  # cap
        assert detector.get_backoff_delay(10) == 30000  # cap
    
    def test_backoff_delay_invalid_attempt(self):
        """测试无效重试次数"""
        detector = LoopDetector()
        
        assert detector.get_backoff_delay(0) == 0
        assert detector.get_backoff_delay(-1) == 0


class TestLoopDetectorStateManagement:
    """测试状态管理"""
    
    def setup_method(self):
        reset_loop_detector()
    
    def test_state_transitions(self):
        """测试状态转换"""
        detector = LoopDetector()
        
        # 初始: idle
        assert detector.state == AgentState.IDLE
        
        # 第一次调用: busy
        detector.check("read", {"path": "file.txt"})
        assert detector.state == AgentState.BUSY
        
        # 第一次失败: retry
        result = {"error": "failed"}
        detector.check("read", {"path": "file.txt"}, result)
        assert detector.state == AgentState.RETRY
        
        # 检测到循环: stuck
        for i in range(2):
            result = {"error": "failed"}
            detector.check("read", {"path": "file.txt"}, result)
        
        assert detector.state == AgentState.STUCK
    
    def test_reset(self):
        """测试重置"""
        detector = LoopDetector()
        
        # 添加一些调用
        for i in range(5):
            detector.check("read", {"path": f"file{i}.txt"})
        
        # 鷻加一些失败
        result = {"error": "failed"}
        detector.check("read", {"path": "file.txt"}, result)
        
        # 验证状态
        assert detector.total_calls > 0
        assert detector.consecutive_failures > 0
        
        # 重置
        detector.reset()
        
        # 验证重置后状态
        assert detector.total_calls == 0
        assert detector.consecutive_failures == 0
        assert detector.state == AgentState.IDLE


class TestLoopDetectorErrorClassification:
    """测试错误分类"""
    
    def setup_method(self):
        reset_loop_detector()
    
    def test_transient_errors(self):
        """测试临时错误识别"""
        detector = LoopDetector()
        
        transient_errors = [
            "timeout: connection reset",
            "rate_limit: too many requests",
            "network error: connection refused",
            "temporarily unavailable",
            "ECONNRESET",
            "ECONNREFUSED",
            "ETIMEDOUT"
        ]
        
        for error in transient_errors:
            result = {"error": error}
            is_loop, info = detector.check("bash", {"cmd": "test"}, result)
            
            assert info.get("error_type") == "transient"
            assert info.get("is_transient") is True
    
    def test_permanent_errors(self):
        """测试永久错误识别"""
        detector = LoopDetector()
        
        permanent_errors = [
            "file not found",
            "permission denied",
            "invalid argument",
            "syntax error",
            "import error"
        ]
        
        for error in permanent_errors:
            result = {"error": error}
            is_loop, info = detector.check("bash", {"cmd": "test"}, result)
            
            assert info.get("error_type") == "permanent"
            assert info.get("is_transient") is False


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
