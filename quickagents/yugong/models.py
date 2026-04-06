"""
愚公循环数据模型

基于30轮互动讨论设计 (Q3, Q6)
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, Any
import json


class StoryPriority(Enum):
    """Story 优先级枚举"""

    CRITICAL = 1  # 最高优先级
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    TRIVIAL = 5  # 最低优先级


class StoryStatus(Enum):
    """Story 状态枚举 [Q2]"""

    PENDING = "pending"  # 待执行
    RUNNING = "running"  # 执行中
    PASSED = "passed"  # 通过验收
    FAILED = "failed"  # 失败
    BLOCKED = "blocked"  # 被阻塞(依赖未完成)
    SKIPPED = "skipped"  # 跳过
    CANCELLED = "cancelled"  # 取消


@dataclass
class UserStory:
    """
    用户故事 - Ralph prd.json 格式的结构化表示 [Q3]

    包含 20 个字段，支持完整的生命周期管理
    """

    # === 基础标识 ===
    id: str  # US-001
    title: str  # 标题
    description: str  # 详细描述

    # === 验收相关 ===
    acceptance_criteria: list[str] = field(default_factory=list)  # 验收标准
    priority: StoryPriority = StoryPriority.MEDIUM  # 优先级 (1=最高优先级)
    status: StoryStatus = StoryStatus.PENDING  # 状态
    passes: bool = False  # 是否通过验收

    # === 依赖与分类 ===
    dependencies: list[str] = field(default_factory=list)  # 依赖的 Story ID
    estimated_complexity: str = "medium"  # 预估复杂度 (low/medium/high)
    tags: list[str] = field(default_factory=list)  # 标签
    category: str = ""  # 分类

    # === 执行状态 ===
    notes: str = ""  # 备注/经验
    files_changed: list[str] = field(default_factory=list)  # 修改的文件列表
    error_log: str = ""  # 错误日志
    attempts: int = 0  # 尝试次数
    max_attempts: int = 3  # 最大尝试次数

    # === 时间追踪 ===
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None  # 开始执行时间
    completed_at: Optional[datetime] = None  # 完成时间

    # === 资源消耗 ===
    token_usage: dict = field(default_factory=dict)  # Token 消耗统计

    def increment_attempts(self) -> int:
        """增加尝试次数并返回新值"""
        self.attempts += 1
        self.updated_at = datetime.now()
        return self.attempts

    def can_retry(self) -> bool:
        """是否可以重试"""
        return self.attempts < self.max_attempts

    def is_blocked_by(self, stories: dict[str, "UserStory"]) -> bool:
        """检查是否被阻塞"""
        for dep_id in self.dependencies:
            if dep_id not in stories:
                return True
            dep = stories[dep_id]
            if not dep.passes:
                return True
        return False

    def start(self) -> None:
        """开始执行"""
        self.status = StoryStatus.RUNNING
        self.started_at = datetime.now()
        self.attempts += 1
        self.updated_at = datetime.now()

    def mark_passed(self, notes: str = "") -> None:
        """标记为通过"""
        self.passes = True
        self.status = StoryStatus.PASSED
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
        if notes:
            self.notes = notes

    def mark_failed(self, error: str = "") -> None:
        """标记为失败"""
        self.passes = False
        self.status = StoryStatus.FAILED
        self.updated_at = datetime.now()
        if error:
            self.error_log = error

    def mark_blocked(self, reason: str = "") -> None:
        """标记为阻塞"""
        self.status = StoryStatus.BLOCKED
        self.updated_at = datetime.now()
        if reason:
            self.notes = f"Blocked: {reason}"

    def to_dict(self) -> dict:
        """序列化为字典"""
        data = asdict(self)
        data["priority"] = self.priority.value
        data["status"] = self.status.value
        # 转换 datetime 为 ISO 字符串
        for key in ("created_at", "updated_at", "started_at", "completed_at"):
            val = data.get(key)
            if isinstance(val, datetime):
                data[key] = val.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "UserStory":
        """从字典反序列化"""
        data = data.copy()

        # 处理枚举
        if isinstance(data.get("priority"), int):
            data["priority"] = StoryPriority(data["priority"])
        if isinstance(data.get("status"), str):
            data["status"] = StoryStatus(data["status"])

        # 处理 datetime
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        if data.get("started_at"):
            data["started_at"] = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            data["completed_at"] = datetime.fromisoformat(data["completed_at"])

        return cls(**data)


@dataclass
class LoopResult:
    """
    单次迭代结果
    """

    iteration: int  # 迭代序号
    story_id: str  # 关联的 Story ID
    success: bool  # 是否成功
    output: str  # Agent 输出
    duration_ms: int  # 执行时长(毫秒)
    token_usage: dict  # Token 消耗 {input, output, total}
    files_changed: list[str] = field(default_factory=list)  # 修改的文件
    error: Optional[str] = None  # 错误信息
    exit_signal: bool = False  # 是否包含退出信号
    completion_indicators: int = 0  # 完成指标数量
    timestamp: datetime = field(default_factory=datetime.now)  # 时间戳

    def to_dict(self) -> dict:
        """序列化为字典"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "LoopResult":
        """从字典反序列化"""
        data = data.copy()
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class LoopState:
    """
    循环状态 [Q2]

    管理 9 个状态: idle, running, paused, waiting, recovering,
                 completed, failed, stopped, cancelled
    """

    status: str = "idle"  # 当前状态
    current_iteration: int = 0  # 当前迭代序号
    current_story: Optional[UserStory] = None  # 当前执行的 Story
    total_stories: int = 0  # 总 Story 数
    completed_stories: int = 0  # 已完成 Story 数
    start_time: datetime = field(default_factory=datetime.now)  # 开始时间
    last_update: datetime = field(default_factory=datetime.now)  # 最后更新时间
    token_budget_used: int = 0  # 已使用 Token 预算
    iterations_history: list[LoopResult] = field(default_factory=list)  # 迭代历史

    @property
    def progress_percentage(self) -> float:
        """计算进度百分比"""
        if self.total_stories == 0:
            return 0.0
        return (self.completed_stories / self.total_stories) * 100

    @property
    def elapsed_seconds(self) -> float:
        """计算已运行秒数"""
        return (datetime.now() - self.start_time).total_seconds()

    @property
    def elapsed_minutes(self) -> float:
        """计算已运行分钟数"""
        return self.elapsed_seconds / 60

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "status": self.status,
            "current_iteration": self.current_iteration,
            "current_story": self.current_story.to_dict() if self.current_story else None,
            "total_stories": self.total_stories,
            "completed_stories": self.completed_stories,
            "start_time": self.start_time.isoformat(),
            "last_update": self.last_update.isoformat(),
            "token_budget_used": self.token_budget_used,
            "progress_percentage": self.progress_percentage,
            "elapsed_seconds": self.elapsed_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LoopState":
        """从字典反序列化"""
        data = data.copy()

        # 处理时间字段
        if isinstance(data.get("start_time"), str):
            data["start_time"] = datetime.fromisoformat(data["start_time"])
        if isinstance(data.get("last_update"), str):
            data["last_update"] = datetime.fromisoformat(data["last_update"])

        # 处理 current_story
        if data.get("current_story") and isinstance(data["current_story"], dict):
            data["current_story"] = UserStory.from_dict(data["current_story"])

        # 处理 iterations_history
        if data.get("iterations_history"):
            data["iterations_history"] = [
                LoopResult.from_dict(r) if isinstance(r, dict) else r for r in data["iterations_history"]
            ]

        # 移除计算属性
        data.pop("progress_percentage", None)
        data.pop("elapsed_seconds", None)

        return cls(**data)

    def add_iteration(self, result: LoopResult) -> None:
        """添加迭代结果"""
        self.iterations_history.append(result)
        self.current_iteration = result.iteration
        self.last_update = datetime.now()
        self.token_budget_used += result.token_usage.get("total", 0)


@dataclass
class ParsedRequirement:
    """
    解析后的需求

    支持多种输入格式: JSON, Markdown, 纯文本
    """

    project_name: str  # 项目名称
    branch_name: str  # 分支名称 (yugong/feature-name)
    description: str  # 项目描述
    user_stories: list[UserStory]  # UserStory 列表
    raw_source: str  # 原始内容
    format: str  # 格式 (json/markdown/text)

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "project_name": self.project_name,
            "branch_name": self.branch_name,
            "description": self.description,
            "user_stories": [s.to_dict() for s in self.user_stories],
            "raw_source": self.raw_source,
            "format": self.format,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ParsedRequirement":
        """从字典反序列化"""
        data = data.copy()

        if data.get("user_stories"):
            data["user_stories"] = [UserStory.from_dict(s) if isinstance(s, dict) else s for s in data["user_stories"]]

        return cls(**data)
