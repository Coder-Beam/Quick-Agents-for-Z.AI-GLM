"""
愚公循环配置类单元测试

测试覆盖:
- YuGongConfig: 默认值、自定义值、文件加载/保存
- 配置验证
- 配置合并
"""

import pytest
import json
import tempfile
from pathlib import Path
from quickagents.yugong.config import YuGongConfig


class TestYuGongConfig:
    """YuGongConfig 配置类测试"""

    def test_default_config(self):
        """测试默认配置值"""
        config = YuGongConfig()

        # 循环参数
        assert config.max_iterations == 50
        assert config.max_calls_per_hour == 100
        assert config.max_tokens_per_hour == 500000

        # 熔断器
        assert config.cb_no_progress_threshold == 3
        assert config.cb_same_error_threshold == 5
        assert config.cb_cooldown_minutes == 30
        assert config.cb_auto_reset is False

        # API 5小时限制
        assert config.api_5h_limit_warning_minutes == 10
        assert config.api_5h_limit_hard_stop is True

        # 退出检测
        assert config.min_iterations == 2
        assert config.completion_threshold == 2

        # 质量检查
        assert config.run_typecheck is True
        assert config.run_lint is True
        assert config.run_tests is True
        assert config.run_coverage is False
        assert config.run_security_scan is False
        assert config.coverage_threshold == 80

        # 提交策略
        assert config.auto_commit is True
        assert config.commit_per_story is True
        assert config.atomic_commits is True

        # 会话
        assert config.session_expiry_hours == 24
        assert config.checkpoint_every_iteration is False
        assert config.checkpoint_on_story_complete is True

        # 其他
        assert config.context_injection_enabled is True
        assert config.db_path == ".quickagents/unified.db"

    def test_custom_config(self):
        """测试自定义配置"""
        config = YuGongConfig(
            max_iterations=100,
            max_calls_per_hour=200,
            max_tokens_per_hour=1000000,
            cb_no_progress_threshold=5,
            coverage_threshold=90,
            auto_commit=False,
        )

        assert config.max_iterations == 100
        assert config.max_calls_per_hour == 200
        assert config.max_tokens_per_hour == 1000000
        assert config.cb_no_progress_threshold == 5
        assert config.coverage_threshold == 90
        assert config.auto_commit is False

    def test_config_to_dict(self):
        """测试配置序列化为字典"""
        config = YuGongConfig(max_iterations=30)

        data = config.to_dict()

        assert isinstance(data, dict)
        assert data["max_iterations"] == 30
        assert "max_calls_per_hour" in data
        assert "db_path" in data

    def test_config_from_dict(self):
        """测试从字典创建配置"""
        data = {
            "max_iterations": 75,
            "max_calls_per_hour": 150,
            "auto_commit": False,
            "custom_field": "ignored",  # 未知字段应被忽略
        }

        config = YuGongConfig.from_dict(data)

        assert config.max_iterations == 75
        assert config.max_calls_per_hour == 150
        assert config.auto_commit is False

    def test_config_save_and_load(self):
        """测试配置保存和加载"""
        config = YuGongConfig(
            max_iterations=60,
            max_tokens_per_hour=800000,
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = Path(f.name)

        try:
            # 保存
            config.to_file(temp_path)

            # 验证文件内容
            with open(temp_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert data["max_iterations"] == 60
            assert data["max_tokens_per_hour"] == 800000

            # 加载
            loaded = YuGongConfig.from_file(temp_path)
            assert loaded.max_iterations == 60
            assert loaded.max_tokens_per_hour == 800000
        finally:
            temp_path.unlink(missing_ok=True)

    def test_config_validate_success(self):
        """测试配置验证 - 有效配置"""
        config = YuGongConfig()

        errors = config.validate()

        assert errors == []

    def test_config_validate_invalid_values(self):
        """测试配置验证 - 无效值"""
        config = YuGongConfig(
            max_iterations=-1,  # 无效: 负数
            max_calls_per_hour=0,  # 无效: 零 → 触发 "必须大于 0"
            coverage_threshold=150,  # 无效: 超过100
            cb_cooldown_minutes=-5,  # 无效: 负数
        )

        errors = config.validate()

        assert len(errors) >= 3
        assert any("max_iterations" in e for e in errors)
        assert any("coverage_threshold" in e for e in errors)
        assert any("max_calls_per_hour" in e for e in errors)

    def test_config_merge(self):
        """测试配置合并"""
        base = YuGongConfig(max_iterations=50, max_calls_per_hour=100)
        override = {"max_iterations": 100, "auto_commit": False}

        merged = base.merge(override)

        assert merged.max_iterations == 100  # 被覆盖
        assert merged.max_calls_per_hour == 100  # 保持原值
        assert merged.auto_commit is False  # 被覆盖

    def test_config_for_conservative_mode(self):
        """测试保守模式配置"""
        config = YuGongConfig.conservative()

        assert config.max_iterations == 20
        assert config.max_calls_per_hour == 50
        assert config.cb_no_progress_threshold == 2
        assert config.cb_cooldown_minutes == 60

    def test_config_for_aggressive_mode(self):
        """测试激进模式配置"""
        config = YuGongConfig.aggressive()

        assert config.max_iterations == 100
        assert config.max_calls_per_hour == 200
        assert config.cb_no_progress_threshold == 5
        assert config.cb_cooldown_minutes == 15


class TestConfigValidation:
    """配置验证边界测试"""

    def test_max_iterations_boundary(self):
        """测试 max_iterations 边界"""
        # 有效值
        config = YuGongConfig(max_iterations=1)
        assert config.validate() == []

        config = YuGongConfig(max_iterations=1000)
        assert config.validate() == []

        # 无效值
        config = YuGongConfig(max_iterations=0)
        assert len(config.validate()) > 0

        config = YuGongConfig(max_iterations=-1)
        assert len(config.validate()) > 0

    def test_coverage_threshold_boundary(self):
        """测试 coverage_threshold 边界"""
        # 有效值
        config = YuGongConfig(coverage_threshold=0)
        assert config.validate() == []

        config = YuGongConfig(coverage_threshold=100)
        assert config.validate() == []

        # 无效值
        config = YuGongConfig(coverage_threshold=-1)
        assert len(config.validate()) > 0

        config = YuGongConfig(coverage_threshold=101)
        assert len(config.validate()) > 0

    def test_db_path_validation(self):
        """测试 db_path 验证"""
        # 有效路径
        config = YuGongConfig(db_path=".quickagents/unified.db")
        assert config.validate() == []

        config = YuGongConfig(db_path="/absolute/path/to/db.sqlite")
        assert config.validate() == []

        # 空路径
        config = YuGongConfig(db_path="")
        assert len(config.validate()) > 0
