"""
愚公循环 (YuGong Loop) - 自主开发循环模块

让QuickAgents实现从需求到完整项目的全自动化执行。
"""

from .models import (
    UserStory,
    LoopResult,
    LoopState,
    ParsedRequirement,
    StoryPriority,
    StoryStatus,
)
from .config import YuGongConfig
from .task_orchestrator import TaskOrchestrator
from .autonomous_loop import YuGongLoop
from .db import YuGongDB
from .llm_client import LLMClient, LLMConfig
from .tool_executor import ToolExecutor
from .agent_executor import AgentExecutor, AgentConfig

__all__ = [
    # 数据模型
    "UserStory",
    "LoopResult",
    "LoopState",
    "ParsedRequirement",
    "StoryPriority",
    "StoryStatus",
    # 配置
    "YuGongConfig",
    # 任务编排
    "TaskOrchestrator",
    # 核心引擎
    "YuGongLoop",
    # 持久化
    "YuGongDB",
    # LLM 客户端
    "LLMClient",
    "LLMConfig",
    # 工具执行
    "ToolExecutor",
    # Agent 执行器
    "AgentExecutor",
    "AgentConfig",
]
