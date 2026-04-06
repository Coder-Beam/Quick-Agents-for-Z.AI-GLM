"""
QuickAgents Skills - 本地化技能模块

完全本地化的技能 (0 Token消耗):
- FeedbackCollector: 经验收集
- TDDWorkflow: TDD工作流
- GitCommit: Git提交管理
- ProjectDetector: 项目类型检测
- CategoryRouter: 任务分类路由
- ModelRouter: 多模型路由与fallback
"""

from .feedback_collector import FeedbackCollector, get_feedback_collector
from .tdd_workflow import TDDWorkflow, TDDPhase, get_tdd_workflow
from .git_commit import GitCommit, get_git_commit
from .project_detector import ProjectDetector, ProjectInfo, get_project_detector, detect_project
from .category_router import (
    CategoryRouter,
    TaskCategory,
    TaskTier as CategoryTaskTier,
    get_category_router,
    classify_task,
)
from .model_router import (
    ModelRouter,
    ModelInfo,
    ModelTier,
    RouteResult,
    get_model_router,
    route_task,
)

__all__ = [
    # Feedback
    "FeedbackCollector",
    "get_feedback_collector",
    # TDD
    "TDDWorkflow",
    "TDDPhase",
    "get_tdd_workflow",
    # Git
    "GitCommit",
    "get_git_commit",
    # Project Detection
    "ProjectDetector",
    "ProjectInfo",
    "get_project_detector",
    "detect_project",
    # Category Routing
    "CategoryRouter",
    "TaskCategory",
    "CategoryTaskTier",
    "get_category_router",
    "classify_task",
    # Model Routing
    "ModelRouter",
    "ModelInfo",
    "ModelTier",
    "RouteResult",
    "get_model_router",
    "route_task",
]
