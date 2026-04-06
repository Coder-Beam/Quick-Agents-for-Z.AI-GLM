"""
ModelRouter - 多模型路由与fallback

管理模型注册表，根据任务需求路由到最优模型，失败时自动fallback。
完全本地化，0 Token消耗。

使用方式:
    router = ModelRouter()

    # 注册模型
    router.register('glm-5', provider='zhipuai', tier='heavyweight',
                     context_window=204800, cost_per_1k=0.05)

    # 路由任务
    result = router.route('实现用户认证系统')
    print(result.model_id)       # 'glm-5'
    print(result.provider)       # 'zhipuai'
    print(result.fallback_chain) # ['glm-4-plus', 'glm-4-flash']

    # Fallback
    try:
        response = call_llm(result.model_id, prompt)
    except LLMApiError:
        next_model = router.get_fallback(result.model_id)
        response = call_llm(next_model, prompt)
"""

import os
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum


class ModelTier(Enum):
    """模型能力层级"""

    LIGHTWEIGHT = "lightweight"
    STANDARD = "standard"
    HEAVYWEIGHT = "heavyweight"


@dataclass
class ModelInfo:
    """模型信息"""

    model_id: str
    provider: str
    tier: ModelTier
    context_window: int = 8192
    max_output: int = 4096
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    supports_function_calling: bool = False
    supports_vision: bool = False
    supports_streaming: bool = True
    rate_limit_rpm: int = 60
    available: bool = True
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "model_id": self.model_id,
            "provider": self.provider,
            "tier": self.tier.value,
            "context_window": self.context_window,
            "max_output": self.max_output,
            "cost_per_1k_input": self.cost_per_1k_input,
            "cost_per_1k_output": self.cost_per_1k_output,
            "supports_function_calling": self.supports_function_calling,
            "supports_vision": self.supports_vision,
            "available": self.available,
        }


@dataclass
class RouteResult:
    """路由结果"""

    model_id: str
    provider: str
    tier: ModelTier
    context_window: int
    reason: str = ""
    fallback_chain: List[str] = field(default_factory=list)
    estimated_cost: float = 0.0


# 内置默认模型注册表
_DEFAULT_MODELS: Dict[str, ModelInfo] = {
    "glm-5": ModelInfo(
        model_id="glm-5",
        provider="zhipuai",
        tier=ModelTier.HEAVYWEIGHT,
        context_window=204800,
        max_output=16384,
        cost_per_1k_input=0.05,
        cost_per_1k_output=0.05,
        supports_function_calling=True,
        supports_vision=True,
        rate_limit_rpm=60,
    ),
    "glm-4-plus": ModelInfo(
        model_id="glm-4-plus",
        provider="zhipuai",
        tier=ModelTier.STANDARD,
        context_window=128000,
        max_output=4096,
        cost_per_1k_input=0.05,
        cost_per_1k_output=0.05,
        supports_function_calling=True,
        supports_vision=False,
        rate_limit_rpm=100,
    ),
    "glm-4-flash": ModelInfo(
        model_id="glm-4-flash",
        provider="zhipuai",
        tier=ModelTier.LIGHTWEIGHT,
        context_window=128000,
        max_output=4096,
        cost_per_1k_input=0.0001,
        cost_per_1k_output=0.0001,
        supports_function_calling=True,
        supports_vision=False,
        rate_limit_rpm=500,
    ),
    "glm-4-long": ModelInfo(
        model_id="glm-4-long",
        provider="zhipuai",
        tier=ModelTier.HEAVYWEIGHT,
        context_window=1048576,
        max_output=4096,
        cost_per_1k_input=0.001,
        cost_per_1k_output=0.001,
        supports_function_calling=False,
        supports_vision=False,
        rate_limit_rpm=60,
    ),
}

# 默认fallback链
_DEFAULT_FALLBACK_CHAINS: Dict[ModelTier, List[str]] = {
    ModelTier.HEAVYWEIGHT: ["glm-5", "glm-4-plus", "glm-4-flash"],
    ModelTier.STANDARD: ["glm-4-plus", "glm-4-flash", "glm-5"],
    ModelTier.LIGHTWEIGHT: ["glm-4-flash", "glm-4-plus", "glm-5"],
}


class ModelRouter:
    """
    多模型路由器

    管理模型注册表，根据任务需求路由到最优模型。
    支持fallback链、成本估算、可用性管理。
    完全本地化，0 Token消耗。

    使用方式:
        router = ModelRouter()
        result = router.route_for_task('实现用户认证系统')
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化路由器

        Args:
            config_path: 可选的配置文件路径（JSON格式）
        """
        self.models: Dict[str, ModelInfo] = {}
        self.fallback_chains: Dict[ModelTier, List[str]] = {
            **_DEFAULT_FALLBACK_CHAINS,
        }
        self._usage_stats: Dict[str, int] = {}

        # 加载默认模型
        for model_id, info in _DEFAULT_MODELS.items():
            self.models[model_id] = info

        # 加载配置文件（如果存在）
        if config_path:
            self._load_config(config_path)

        # 检查环境变量覆盖
        self._apply_env_overrides()

    def register(
        self,
        model_id: str,
        provider: str,
        tier: str = "standard",
        context_window: int = 8192,
        max_output: int = 4096,
        cost_per_1k_input: float = 0.0,
        cost_per_1k_output: float = 0.0,
        supports_function_calling: bool = False,
        supports_vision: bool = False,
        rate_limit_rpm: int = 60,
    ) -> None:
        """
        注册模型

        Args:
            model_id: 模型ID
            provider: 提供商
            tier: 能力层级 (lightweight/standard/heavyweight)
            context_window: 上下文窗口大小
            max_output: 最大输出长度
            cost_per_1k_input: 每1K token输入成本
            cost_per_1k_output: 每1K token输出成本
            supports_function_calling: 是否支持函数调用
            supports_vision: 是否支持视觉
            rate_limit_rpm: 每分钟请求限制
        """
        tier_enum = ModelTier(tier)
        self.models[model_id] = ModelInfo(
            model_id=model_id,
            provider=provider,
            tier=tier_enum,
            context_window=context_window,
            max_output=max_output,
            cost_per_1k_input=cost_per_1k_input,
            cost_per_1k_output=cost_per_1k_output,
            supports_function_calling=supports_function_calling,
            supports_vision=supports_vision,
            rate_limit_rpm=rate_limit_rpm,
        )

    def unregister(self, model_id: str) -> bool:
        """
        注销模型

        Returns:
            是否成功注销
        """
        if model_id in self.models:
            del self.models[model_id]
            return True
        return False

    def route(
        self,
        tier: ModelTier,
        require_vision: bool = False,
        require_function_calling: bool = False,
        min_context: int = 0,
    ) -> RouteResult:
        """
        按条件路由到最优模型

        Args:
            tier: 目标层级
            require_vision: 是否需要视觉能力
            require_function_calling: 是否需要函数调用
            min_context: 最小上下文窗口

        Returns:
            RouteResult 路由结果
        """
        chain = self.fallback_chains.get(tier, [])

        # 过滤满足条件的模型
        candidates = []
        for model_id in chain:
            model = self.models.get(model_id)
            if not model or not model.available:
                continue
            if require_vision and not model.supports_vision:
                continue
            if require_function_calling and not model.supports_function_calling:
                continue
            if model.context_window < min_context:
                continue
            candidates.append(model)

        # 如果链中无可用模型，从所有模型中选择
        if not candidates:
            candidates = [
                m
                for m in self.models.values()
                if m.available
                and (not require_vision or m.supports_vision)
                and (not require_function_calling or m.supports_function_calling)
                and m.context_window >= min_context
            ]
            # 按层级优先排序
            tier_order = {ModelTier.HEAVYWEIGHT: 0, ModelTier.STANDARD: 1, ModelTier.LIGHTWEIGHT: 2}
            candidates.sort(key=lambda m: tier_order.get(m.tier, 1))

        if not candidates:
            # 最后手段：返回任意可用模型
            for model in self.models.values():
                if model.available:
                    return RouteResult(
                        model_id=model.model_id,
                        provider=model.provider,
                        tier=model.tier,
                        context_window=model.context_window,
                        reason="fallback: 无满足条件的模型",
                        fallback_chain=[],
                    )
            raise RuntimeError("没有可用的模型")

        primary = candidates[0]
        fb_chain = [m.model_id for m in candidates[1:]]

        return RouteResult(
            model_id=primary.model_id,
            provider=primary.provider,
            tier=primary.tier,
            context_window=primary.context_window,
            reason=f"匹配tier={tier.value}",
            fallback_chain=fb_chain,
        )

    def route_for_task(
        self,
        task_description: str,
        require_vision: bool = False,
        require_function_calling: bool = True,
        min_context: int = 0,
    ) -> RouteResult:
        """
        根据任务描述自动路由

        先通过CategoryRouter分类任务，再路由到对应模型。

        Args:
            task_description: 任务描述
            require_vision: 是否需要视觉
            require_function_calling: 是否需要函数调用
            min_context: 最小上下文窗口

        Returns:
            RouteResult
        """
        from .category_router import get_category_router

        router = get_category_router()
        category, _ = router.classify_with_model(task_description)

        # 将CategoryRouter的tier映射到ModelTier
        from .category_router import TaskTier

        tier_map = {
            TaskTier.LIGHTWEIGHT: ModelTier.LIGHTWEIGHT,
            TaskTier.STANDARD: ModelTier.STANDARD,
            TaskTier.HEAVYWEIGHT: ModelTier.HEAVYWEIGHT,
        }
        tier = tier_map.get(category.tier, ModelTier.STANDARD)

        result = self.route(
            tier=tier,
            require_vision=require_vision,
            require_function_calling=require_function_calling,
            min_context=min_context,
        )
        result.reason = f"category={category.name}, {result.reason}"

        return result

    def get_fallback(self, failed_model_id: str) -> Optional[str]:
        """
        获取下一个fallback模型

        Args:
            failed_model_id: 失败的模型ID

        Returns:
            下一个fallback模型ID，或None
        """
        model = self.models.get(failed_model_id)
        if not model:
            return None

        chain = self.fallback_chains.get(model.tier, [])

        found = False
        for model_id in chain:
            if found:
                next_model = self.models.get(model_id)
                if next_model and next_model.available:
                    return model_id
            if model_id == failed_model_id:
                found = True

        return None

    def mark_unavailable(self, model_id: str, error: str = "") -> None:
        """
        标记模型不可用

        Args:
            model_id: 模型ID
            error: 错误信息
        """
        model = self.models.get(model_id)
        if model:
            model.available = False
            model.last_error = error
            model.last_error_time = datetime.now()

    def mark_available(self, model_id: str) -> None:
        """标记模型可用"""
        model = self.models.get(model_id)
        if model:
            model.available = True
            model.last_error = None

    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """获取模型信息"""
        return self.models.get(model_id)

    def list_models(self, available_only: bool = False) -> List[ModelInfo]:
        """列出所有模型"""
        models = list(self.models.values())
        if available_only:
            models = [m for m in models if m.available]
        return models

    def estimate_cost(self, model_id: str, input_tokens: int, output_tokens: int) -> float:
        """
        估算调用成本

        Args:
            model_id: 模型ID
            input_tokens: 输入token数
            output_tokens: 输出token数

        Returns:
            估算成本（美元）
        """
        model = self.models.get(model_id)
        if not model:
            return 0.0

        input_cost = (input_tokens / 1000) * model.cost_per_1k_input
        output_cost = (output_tokens / 1000) * model.cost_per_1k_output

        return input_cost + output_cost

    def _load_config(self, config_path: str) -> None:
        """从JSON文件加载配置"""
        try:
            path = Path(config_path)
            if not path.exists():
                return

            data = json.loads(path.read_text(encoding="utf-8"))

            # 加载模型
            for model_data in data.get("models", []):
                model_id = model_data.get("model_id", "")
                if model_id:
                    self.register(
                        model_id=model_id,
                        provider=model_data.get("provider", "unknown"),
                        tier=model_data.get("tier", "standard"),
                        context_window=model_data.get("context_window", 8192),
                        max_output=model_data.get("max_output", 4096),
                        cost_per_1k_input=model_data.get("cost_per_1k_input", 0.0),
                        cost_per_1k_output=model_data.get("cost_per_1k_output", 0.0),
                        supports_function_calling=model_data.get("supports_function_calling", False),
                        supports_vision=model_data.get("supports_vision", False),
                        rate_limit_rpm=model_data.get("rate_limit_rpm", 60),
                    )

            # 加载fallback链
            for tier_str, chain in data.get("fallback_chains", {}).items():
                try:
                    tier = ModelTier(tier_str)
                    self.fallback_chains[tier] = chain
                except ValueError:
                    pass

        except (json.JSONDecodeError, OSError):
            pass

    def _apply_env_overrides(self) -> None:
        """应用环境变量覆盖"""
        # DEFAULT_MODEL 环境变量覆盖默认重型模型
        default_model = os.environ.get("QUICKAGENTS_DEFAULT_MODEL")
        if default_model and default_model in self.models:
            # 将该模型提升为重型fallback的首选
            for tier in ModelTier:
                chain = self.fallback_chains.get(tier, [])
                if default_model in chain:
                    chain.remove(default_model)
                chain.insert(0, default_model)
                self.fallback_chains[tier] = chain


# 全局实例
_global_router: Optional[ModelRouter] = None


def get_model_router() -> ModelRouter:
    """获取全局模型路由器"""
    global _global_router
    if _global_router is None:
        _global_router = ModelRouter()
    return _global_router


def route_task(task_description: str, **kwargs) -> RouteResult:
    """便捷函数：路由任务"""
    return get_model_router().route_for_task(task_description, **kwargs)
