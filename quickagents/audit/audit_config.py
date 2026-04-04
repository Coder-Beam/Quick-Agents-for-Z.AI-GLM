"""
AuditConfig - 审计配置管理

核心功能:
- 从 JSON 文件加载配置
- 提供合理的默认值
- 配置验证（启动时 + 懒加载）
- 运行时修改（不持久化，需显式保存）

设计原则:
- 单一职责：仅负责配置读写和验证
- 防御性编程：所有字段都有默认值
- 项目级配置：audit_config.json 存放在项目根目录
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_CONFIG: Dict[str, Any] = {
    "version": "1.0.0",
    "code_audit": {
        "enabled": True,
        "ignore_patterns": [
            "**/.git/**",
            "**/__pycache__/**",
            "**/node_modules/**",
            "**/.quickagents/**",
            "**/*.pyc",
        ],
        "max_diff_lines": 500,
        "track_tool_calls": ["write", "edit"],
    },
    "quality_gate": {
        "enabled": True,
        "atomic_checks": {
            "lint_command": "auto",
            "typecheck_command": "auto",
            "test_command": "auto",
            "timeout_seconds": 30,
        },
        "full_checks": {
            "coverage_threshold": 80,
            "timeout_seconds": 120,
        },
        "e2e_command": None,
        "integration_command": None,
    },
    "accountability": {
        "enabled": True,
        "auto_feedback_enabled": False,
        "severity_threshold": "P2",
        "auto_resolve_on_fix": True,
        "lesson_extraction": True,
    },
    "reporting": {
        "output_dir": ".quickagents/audit_reports",
        "format": "markdown",
        "auto_report_on_task_complete": True,
    },
    "retention": {
        "full_diff_days": 30,
        "summary_days": 90,
        "stats_only_days": None,  # 超过 summary_days 的仅保留统计
    },
}


class AuditConfig:
    """
    审计配置管理器

    使用方式:
        # 从文件加载（不存在时使用默认值）
        config = AuditConfig.from_file('audit_config.json')

        # 从默认值创建
        config = AuditConfig()

        # 访问配置
        if config.code_audit_enabled:
            ...

        # 保存到文件
        config.save('audit_config.json')

    优先级:
        显式参数 > 文件配置 > 默认值
    """

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """
        初始化配置

        Args:
            config_dict: 配置字典（合并到默认值上）
        """
        self._raw = _deep_merge(DEFAULT_CONFIG.copy(), config_dict or {})
        self._validate()

    # ==================== 工厂方法 ====================

    @classmethod
    def from_file(cls, config_path: str) -> "AuditConfig":
        """
        从 JSON 文件加载配置

        Args:
            config_path: 配置文件路径

        Returns:
            AuditConfig: 配置实例
        """
        path = Path(config_path)
        if not path.exists():
            logger.info(f"Config file not found, using defaults: {config_path}")
            return cls()

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Loaded audit config from: {config_path}")
            return cls(data)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load config: {e}, using defaults")
            return cls()

    # ==================== CodeAudit 配置 ====================

    @property
    def code_audit_enabled(self) -> bool:
        return self._raw["code_audit"]["enabled"]

    @property
    def ignore_patterns(self) -> List[str]:
        return self._raw["code_audit"]["ignore_patterns"]

    @property
    def max_diff_lines(self) -> int:
        return self._raw["code_audit"]["max_diff_lines"]

    @property
    def track_tool_calls(self) -> List[str]:
        return self._raw["code_audit"]["track_tool_calls"]

    # ==================== QualityGate 配置 ====================

    @property
    def quality_gate_enabled(self) -> bool:
        return self._raw["quality_gate"]["enabled"]

    @property
    def lint_command(self) -> str:
        return self._raw["quality_gate"]["atomic_checks"]["lint_command"]

    @property
    def typecheck_command(self) -> str:
        return self._raw["quality_gate"]["atomic_checks"]["typecheck_command"]

    @property
    def test_command(self) -> str:
        return self._raw["quality_gate"]["atomic_checks"]["test_command"]

    @property
    def atomic_timeout(self) -> int:
        return self._raw["quality_gate"]["atomic_checks"]["timeout_seconds"]

    @property
    def coverage_threshold(self) -> int:
        return self._raw["quality_gate"]["full_checks"]["coverage_threshold"]

    @property
    def full_timeout(self) -> int:
        return self._raw["quality_gate"]["full_checks"]["timeout_seconds"]

    @property
    def e2e_command(self) -> Optional[str]:
        return self._raw["quality_gate"].get("e2e_command")

    @property
    def integration_command(self) -> Optional[str]:
        return self._raw["quality_gate"].get("integration_command")

    # ==================== Accountability 配置 ====================

    @property
    def accountability_enabled(self) -> bool:
        return self._raw["accountability"]["enabled"]

    @property
    def auto_feedback_enabled(self) -> bool:
        return self._raw["accountability"]["auto_feedback_enabled"]

    @property
    def severity_threshold(self) -> str:
        return self._raw["accountability"]["severity_threshold"]

    @property
    def auto_resolve_on_fix(self) -> bool:
        return self._raw["accountability"]["auto_resolve_on_fix"]

    @property
    def lesson_extraction(self) -> bool:
        return self._raw["accountability"]["lesson_extraction"]

    # ==================== Reporting 配置 ====================

    @property
    def report_output_dir(self) -> str:
        return self._raw["reporting"]["output_dir"]

    @property
    def report_format(self) -> str:
        return self._raw["reporting"]["format"]

    @property
    def auto_report_on_task_complete(self) -> bool:
        return self._raw["reporting"]["auto_report_on_task_complete"]

    # ==================== Retention 配置 ====================

    @property
    def full_diff_days(self) -> int:
        return self._raw["retention"]["full_diff_days"]

    @property
    def summary_days(self) -> int:
        return self._raw["retention"]["summary_days"]

    # ==================== 序列化 ====================

    def to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        import copy

        return copy.deepcopy(self._raw)

    def save(self, config_path: str) -> None:
        """
        保存配置到 JSON 文件

        Args:
            config_path: 目标文件路径
        """
        path = Path(config_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._raw, f, indent=4, ensure_ascii=False)

        logger.info(f"Saved audit config to: {config_path}")

    # ==================== 验证 ====================

    def _validate(self) -> None:
        """验证配置有效性（启动时验证）"""
        errors = []

        # 验证数值范围
        if self.max_diff_lines < 0:
            errors.append(f"max_diff_lines must be >= 0, got {self.max_diff_lines}")

        if self.atomic_timeout < 1:
            errors.append(f"atomic_timeout must be >= 1, got {self.atomic_timeout}")

        if self.full_timeout < 1:
            errors.append(f"full_timeout must be >= 1, got {self.full_timeout}")

        if not 0 <= self.coverage_threshold <= 100:
            errors.append(f"coverage_threshold must be 0-100, got {self.coverage_threshold}")

        if self.severity_threshold not in ("P0", "P1", "P2"):
            errors.append(f"severity_threshold must be P0/P1/P2, got {self.severity_threshold}")

        if self.report_format not in ("markdown", "json"):
            errors.append(f"report_format must be markdown/json, got {self.report_format}")

        if errors:
            for err in errors:
                logger.warning(f"Config validation: {err}")

    def validate_runtime(self, project_root: Optional[Path] = None) -> List[str]:
        """
        运行时验证（懒加载验证）

        检查依赖工具是否可用。

        Args:
            project_root: 项目根目录

        Returns:
            List[str]: 警告消息列表
        """
        warnings: List[str] = []

        if not self.quality_gate_enabled:
            return warnings

        # 检查 lint 工具
        if self.lint_command == "auto":
            if not _command_exists("ruff") and not _command_exists("flake8"):
                warnings.append("No lint tool found (ruff/flake8). QualityGate lint checks will be skipped.")

        # 检查 typecheck 工具
        if self.typecheck_command == "auto":
            if not _command_exists("mypy"):
                warnings.append("No type checker found (mypy). QualityGate type checks will be skipped.")

        # 检查测试工具
        if self.test_command == "auto":
            if not _command_exists("pytest"):
                warnings.append("No test runner found (pytest). QualityGate test checks will be skipped.")

        for w in warnings:
            logger.info(f"Runtime validation: {w}")

        return warnings

    def __repr__(self) -> str:
        return (
            f"AuditConfig("
            f"code_audit={'on' if self.code_audit_enabled else 'off'}, "
            f"quality_gate={'on' if self.quality_gate_enabled else 'off'}, "
            f"accountability={'on' if self.accountability_enabled else 'off'})"
        )


# ==================== 辅助函数 ====================


def _deep_merge(base: Dict, override: Dict) -> Dict:
    """深度合并字典，override 覆盖 base"""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _command_exists(cmd: str) -> bool:
    """检查系统命令是否可用"""
    import subprocess
    import os

    try:
        check_cmd = ["where", cmd] if os.name == "nt" else ["which", cmd]
        result = subprocess.run(check_cmd, capture_output=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False
