"""
CategoryRouter - 任务分类路由

通过关键词匹配将任务描述映射到任务类别，再路由到合适的模型层级。
完全本地化，0 Token消耗。

使用方式:
    router = CategoryRouter()
    category = router.classify('修复登录页面的Bug')
    print(category.name)      # 'debugging'
    print(category.tier)      # 'lightweight'
    print(category.model_id)  # 'glm-4-flash'

    # 批量分类
    results = router.classify_batch([
        '写一个单元测试',
        '重构数据库模块',
        '更新README文档',
    ])
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class TaskTier(Enum):
    """模型层级"""

    LIGHTWEIGHT = "lightweight"  # 轻量级: 简单任务
    STANDARD = "standard"  # 标准级: 一般任务
    HEAVYWEIGHT = "heavyweight"  # 重量级: 复杂任务


@dataclass
class TaskCategory:
    """任务类别"""

    name: str
    display_name: str
    tier: TaskTier
    model_id: Optional[str] = None  # None表示使用tier对应的默认模型
    keywords: List[str] = field(default_factory=list)
    description: str = ""


# 任务类别定义
CATEGORIES: Dict[str, TaskCategory] = {
    "testing": TaskCategory(
        name="testing",
        display_name="测试",
        tier=TaskTier.LIGHTWEIGHT,
        keywords=[
            "test",
            "测试",
            "unit test",
            "单元测试",
            "integration test",
            "集成测试",
            "coverage",
            "覆盖率",
            "pytest",
            "jest",
            "vitest",
            "mock",
            "assert",
            "断言",
            "fixture",
            "snapshot",
            "快照测试",
        ],
        description="编写/运行测试用例",
    ),
    "debugging": TaskCategory(
        name="debugging",
        display_name="调试",
        tier=TaskTier.STANDARD,
        keywords=[
            "debug",
            "调试",
            "fix",
            "修复",
            "bug",
            "error",
            "错误",
            "exception",
            "异常",
            "traceback",
            "stack trace",
            "堆栈",
            "crash",
            "崩溃",
            "regression",
            "回归",
            "investigate",
            "排查",
        ],
        description="调试/修复Bug",
    ),
    "documentation": TaskCategory(
        name="documentation",
        display_name="文档",
        tier=TaskTier.LIGHTWEIGHT,
        keywords=[
            "doc",
            "文档",
            "readme",
            "changelog",
            "变更日志",
            "comment",
            "注释",
            "api doc",
            "api文档",
            "guide",
            "指南",
            "tutorial",
            "教程",
            "md",
            "markdown",
        ],
        description="编写/更新文档",
    ),
    "refactoring": TaskCategory(
        name="refactoring",
        display_name="重构",
        tier=TaskTier.HEAVYWEIGHT,
        keywords=[
            "refactor",
            "重构",
            "restructure",
            "重组",
            "clean up",
            "清理",
            "simplify",
            "简化",
            "optimize",
            "优化",
            "rename",
            "重命名",
            "extract",
            "提取",
            "inline",
            "内联",
            "decompose",
            "拆分",
        ],
        description="代码重构/优化",
    ),
    "feature": TaskCategory(
        name="feature",
        display_name="新功能",
        tier=TaskTier.HEAVYWEIGHT,
        keywords=[
            "implement",
            "实现",
            "add feature",
            "添加功能",
            "new feature",
            "新功能",
            "create",
            "创建",
            "build",
            "构建",
            "develop",
            "开发",
            "integrate",
            "集成",
            "migrate",
            "迁移",
        ],
        description="新功能开发",
    ),
    "review": TaskCategory(
        name="review",
        display_name="审查",
        tier=TaskTier.STANDARD,
        keywords=[
            "review",
            "审查",
            "code review",
            "代码审查",
            "audit",
            "审计",
            "check",
            "检查",
            "inspect",
            "检视",
            "analyze",
            "分析",
            "security",
            "安全",
            "vulnerability",
            "漏洞",
        ],
        description="代码审查/安全审计",
    ),
    "styling": TaskCategory(
        name="styling",
        display_name="样式/UI",
        tier=TaskTier.LIGHTWEIGHT,
        keywords=[
            "style",
            "样式",
            "css",
            "ui",
            "界面",
            "layout",
            "布局",
            "design",
            "设计",
            "color",
            "颜色",
            "font",
            "字体",
            "responsive",
            "响应式",
            "animation",
            "动画",
            "theme",
            "主题",
        ],
        description="UI/样式调整",
    ),
    "configuration": TaskCategory(
        name="configuration",
        display_name="配置",
        tier=TaskTier.LIGHTWEIGHT,
        keywords=[
            "config",
            "配置",
            "setup",
            "设置",
            "setting",
            "设置",
            "env",
            "环境变量",
            "docker",
            "deploy",
            "部署",
            "ci/cd",
            "pipeline",
            "流水线",
            "build",
            "构建",
        ],
        description="配置/部署相关",
    ),
    "database": TaskCategory(
        name="database",
        display_name="数据库",
        tier=TaskTier.STANDARD,
        keywords=[
            "database",
            "数据库",
            "sql",
            "query",
            "查询",
            "migration",
            "迁移",
            "schema",
            "模式",
            "table",
            "表",
            "index",
            "索引",
            "model",
            "模型",
            "orm",
            "seed",
        ],
        description="数据库操作/迁移",
    ),
    "general": TaskCategory(
        name="general",
        display_name="通用",
        tier=TaskTier.STANDARD,
        keywords=[],
        description="通用任务（默认分类）",
    ),
}


class CategoryRouter:
    """
    任务分类路由器

    通过关键词匹配将任务描述映射到任务类别和模型层级。
    完全本地化，0 Token消耗。

    使用方式:
        router = CategoryRouter()
        category = router.classify('修复登录页面的Bug')
    """

    def __init__(self, default_model_map: Optional[Dict[TaskTier, str]] = None):
        """
        初始化路由器

        Args:
            default_model_map: 层级 → 默认模型映射
                如果不提供，使用内置默认映射
        """
        self.categories = CATEGORIES.copy()

        # 默认模型映射 (层级 → 模型ID)
        self.model_map = default_model_map or {
            TaskTier.LIGHTWEIGHT: "glm-4-flash",
            TaskTier.STANDARD: "glm-4-plus",
            TaskTier.HEAVYWEIGHT: "glm-5",
        }

    def classify(self, task_description: str) -> TaskCategory:
        """
        分类单个任务

        Args:
            task_description: 任务描述文本

        Returns:
            TaskCategory 任务类别
        """
        text = task_description.lower()

        best_category = self.categories["general"]
        best_score = 0

        for cat in self.categories.values():
            score = self._calculate_score(text, cat)
            if score > best_score:
                best_score = score
                best_category = cat

        return best_category

    def classify_with_model(self, task_description: str) -> Tuple[TaskCategory, str]:
        """
        分类任务并返回推荐的模型ID

        Args:
            task_description: 任务描述文本

        Returns:
            (TaskCategory, model_id) 元组
        """
        category = self.classify(task_description)

        # 优先使用类别特定的模型，否则用层级默认
        model_id = category.model_id or self.model_map.get(category.tier, "glm-4-plus")

        return category, model_id

    def classify_batch(self, tasks: List[str]) -> List[Tuple[str, TaskCategory]]:
        """
        批量分类

        Args:
            tasks: 任务描述列表

        Returns:
            [(task, category), ...] 列表
        """
        return [(task, self.classify(task)) for task in tasks]

    def _calculate_score(self, text: str, category: TaskCategory) -> int:
        """
        计算文本与类别的匹配分数

        使用关键词匹配 + 权重计算
        """
        score = 0

        for keyword in category.keywords:
            if keyword.lower() in text:
                # 精确匹配关键词加分
                score += 10

                # 关键词出现在开头额外加分
                if text.strip().startswith(keyword.lower()):
                    score += 5

        return score

    def get_all_categories(self) -> Dict[str, TaskCategory]:
        """获取所有类别"""
        return self.categories.copy()

    def get_tier_for_category(self, category_name: str) -> TaskTier:
        """获取类别的层级"""
        cat = self.categories.get(category_name, self.categories["general"])
        return cat.tier

    def get_model_for_tier(self, tier: TaskTier) -> str:
        """获取层级对应的模型"""
        return self.model_map.get(tier, "glm-4-plus")


# 全局实例
_global_router: Optional[CategoryRouter] = None


def get_category_router() -> CategoryRouter:
    """获取全局分类路由器"""
    global _global_router
    if _global_router is None:
        _global_router = CategoryRouter()
    return _global_router


def classify_task(task_description: str) -> Tuple[TaskCategory, str]:
    """便捷函数：分类任务并返回推荐模型"""
    return get_category_router().classify_with_model(task_description)
