"""
愚公循环配置类

基于30轮互动讨论设计 (Q10)
"""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Any
import json


@dataclass
class YuGongConfig:
    """
    愚公循环配置 [Q10]

    支持三种配置模式:
    - 默认模式: 平衡的安全性和效率
    - 保守模式: 更严格的安全限制
    - 激进模式: 更高的执行效率
    """

    # 循环参数
    max_iterations: int = 50  # 最大迭代次数
    max_calls_per_hour: int = 100  # 每小时最大API调用
    max_tokens_per_hour: int = 500000  # 每小时Token预算(0=不限)

    # 熔断器 [Q5]

    # === 熔断器 [Q5] ===
    cb_no_progress_threshold: int = 3  # 连续无进展次数阈值
    cb_same_error_threshold: int = 5  # 相同错误次数阈值
    cb_cooldown_minutes: int = 30  # 冷却时间(分钟)
    cb_auto_reset: bool = False  # 启动时自动重置熔断器

    # === API 5小时限制 ===
    api_5h_limit_warning_minutes: int = 10  # 5h限制预警时间(提前10分钟=4h50m)
    api_5h_limit_hard_stop: bool = True  # 5h限制到达时是否强制暂停

    # === 退出检测 [Q6] ===
    min_iterations: int = 2  # 最少迭代次数
    completion_threshold: int = 2  # 完成信号阈值

    # === 质量检查 [Q14] ===
    run_typecheck: bool = True  # 运行类型检查
    run_lint: bool = True  # 运行Lint检查
    run_tests: bool = True  # 运行测试
    run_coverage: bool = False  # 运行覆盖率检查(可选)
    run_security_scan: bool = False  # 运行安全扫描(可选)
    coverage_threshold: int = 80  # 覆盖率阈值

    # === 提交策略 [Q15] ===
    auto_commit: bool = True  # 自动提交
    commit_per_story: bool = True  # 每个Story完成后提交
    atomic_commits: bool = True  # 强制原子提交

    # === 会话 [Q18] ===
    session_expiry_hours: int = 24  # 会话过期时间
    checkpoint_every_iteration: bool = False  # 每次迭代保存检查点
    checkpoint_on_story_complete: bool = True  # Story完成时保存检查点

    # === 中间注入 [Q11] ===
    context_injection_enabled: bool = True  # 启用上下文注入

    # === 数据库 ===
    db_path: str = ".quickagents/unified.db"  # 数据库路径

    def to_dict(self) -> dict:
        """序列化为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "YuGongConfig":
        """从字典创建配置"""
        # 过滤未知字段
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)

    @classmethod
    def from_file(cls, path: Path | str) -> "YuGongConfig":
        """从配置文件加载"""
        path = Path(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_file(self, path: Path | str) -> None:
        """保存到配置文件"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    def merge(self, override: dict) -> "YuGongConfig":
        """
        合并配置

        Args:
            override: 要覆盖的配置项

        Returns:
            新的配置实例
        """
        base = self.to_dict()
        base.update(override)
        return YuGongConfig.from_dict(base)

    def validate(self) -> list[str]:
        """
        验证配置

        Returns:
            错误信息列表，空列表表示验证通过
        """
        errors = []

        # 循环参数验证
        if self.max_iterations <= 0:
            errors.append("max_iterations 必须大于 0")
        if self.max_calls_per_hour <= 0:
            errors.append("max_calls_per_hour 必须大于 0")
        if self.max_tokens_per_hour < 0:
            errors.append("max_tokens_per_hour 不能为负数")
        if self.cb_no_progress_threshold <= 0:
            errors.append("cb_no_progress_threshold must be >= 2")
        if self.cb_same_error_threshold <= 0:
            errors.append("cb_same_error_threshold must be >= 2")
        if self.cb_cooldown_minutes <= 0:
            errors.append("cb_cooldown_minutes 必须大于 0")
        if self.min_iterations <= 0:
            errors.append("min_iterations 必须大于 0")
        if self.coverage_threshold < 0 or self.coverage_threshold > 100:
            errors.append("coverage_threshold must be in 0-100")
        if not self.db_path:
            errors.append("db_path cannot为空")

        return errors

    @classmethod
    def conservative(cls) -> "YuGongConfig":
        """
        保守模式配置

        特点:
        - 更少的迭代次数
        - 更低的调用频率
        - 更严格的熔断器
        """
        return cls(
            max_iterations=20,
            max_calls_per_hour=50,
            max_tokens_per_hour=200000,
            cb_no_progress_threshold=2,
            cb_same_error_threshold=3,
            cb_cooldown_minutes=60,
            min_iterations=1,
            completion_threshold=3,
        )

    @classmethod
    def aggressive(cls) -> "YuGongConfig":
        """
        激进模式配置

        特点:
        - 更多的迭代次数
        - 更高的调用频率
        - 更宽松的熔断器
        """
        return cls(
            max_iterations=100,
            max_calls_per_hour=200,
            max_tokens_per_hour=1000000,
            cb_no_progress_threshold=5,
            cb_same_error_threshold=8,
            cb_cooldown_minutes=15,
            min_iterations=3,
            completion_threshold=1,
        )
