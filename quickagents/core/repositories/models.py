"""
Models - 数据模型（实体类）

包含:
- Memory: 记忆实体
- Task: 任务实体
- Progress: 进度实体
- Feedback: 反馈实体
- MemoryType, TaskStatus, TaskPriority, FeedbackType: 枚举
"""

import time
import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


# ==================== 枚举定义 ====================

class MemoryType(Enum):
    """记忆类型"""
    FACTUAL = "factual"           # 事实记忆
    EXPERIENTIAL = "experiential"  # 经验记忆
    WORKING = "working"           # 工作记忆


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class TaskPriority(Enum):
    """任务优先级"""
    P0 = "P0"  # 紧急
    P1 = "P1"  # 高
    P2 = "P2"  # 中
    P3 = "P3"  # 低


class FeedbackType(Enum):
    """反馈类型"""
    BUG = "bug"
    IMPROVEMENT = "improvement"
    BEST_PRACTICE = "best_practice"
    PITFALL = "pitfall"
    QUESTION = "question"
    SKILL_REVIEW = "skill_review"    # Skills评估反馈
    AGENT_REVIEW = "agent_review"    # Agent评估反馈


# ==================== 实体类定义 ====================

@dataclass
class Memory:
    """
    记忆实体
    
    属性:
        id: 唯一标识
        memory_type: 记忆类型
        key: 键名
        value: 值
        category: 分类
        importance_score: 重要性分数 (0.0-1.0)
        access_count: 访问次数
        last_accessed_at: 最后访问时间戳
        created_at: 创建时间戳
        updated_at: 更新时间戳
        metadata: 元数据
        content_hash: 内容哈希
    """
    id: str
    memory_type: MemoryType
    key: str
    value: str
    category: Optional[str] = None
    importance_score: float = 0.5
    access_count: int = 0
    last_accessed_at: Optional[float] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    content_hash: Optional[str] = None
    
    def touch(self) -> None:
        """更新访问时间和计数"""
        self.access_count += 1
        self.last_accessed_at = time.time()
        self.updated_at = time.time()
    
    def calculate_hash(self) -> str:
        """计算内容哈希"""
        content = f"{self.key}:{self.value}:{self.category or ''}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def update_hash(self) -> None:
        """更新内容哈希"""
        self.content_hash = self.calculate_hash()


@dataclass
class Task:
    """
    任务实体
    
    属性:
        id: 唯一标识
        name: 任务名称
        priority: 优先级
        status: 状态
        assignee: 负责人
        start_time: 开始时间戳
        end_time: 结束时间戳
        created_at: 创建时间戳
        updated_at: 更新时间戳
        metadata: 元数据
    """
    id: str
    name: str
    priority: TaskPriority = TaskPriority.P2
    status: TaskStatus = TaskStatus.PENDING
    assignee: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def start(self) -> None:
        """开始任务"""
        self.status = TaskStatus.IN_PROGRESS
        self.start_time = time.time()
        self.updated_at = time.time()
    
    def complete(self) -> None:
        """完成任务"""
        self.status = TaskStatus.COMPLETED
        self.end_time = time.time()
        self.updated_at = time.time()
    
    def block(self) -> None:
        """阻塞任务"""
        self.status = TaskStatus.BLOCKED
        self.updated_at = time.time()
    
    def cancel(self) -> None:
        """取消任务"""
        self.status = TaskStatus.CANCELLED
        self.end_time = time.time()
        self.updated_at = time.time()


@dataclass
class Progress:
    """
    进度实体
    
    属性:
        id: 唯一标识
        project_name: 项目名称
        current_task: 当前任务
        total_tasks: 总任务数
        completed_tasks: 已完成任务数
        last_checkpoint: 最后检查点
        created_at: 创建时间戳
        updated_at: 更新时间戳
    """
    id: str
    project_name: str
    current_task: Optional[str] = None
    total_tasks: int = 0
    completed_tasks: int = 0
    last_checkpoint: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    @property
    def percentage(self) -> float:
        """完成百分比"""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100
    
    @property
    def remaining_tasks(self) -> int:
        """剩余任务数"""
        return max(0, self.total_tasks - self.completed_tasks)
    
    def increment(self) -> None:
        """增加完成计数"""
        self.completed_tasks += 1
        self.updated_at = time.time()


@dataclass
class Feedback:
    """
    反馈实体
    
    属性:
        id: 唯一标识
        feedback_type: 反馈类型
        title: 标题
        description: 描述
        project_name: 项目名称
        metadata: 元数据
        created_at: 创建时间戳
    """
    id: str
    feedback_type: FeedbackType
    title: str
    description: Optional[str] = None
    project_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


# ==================== 检索结果模型 ====================

@dataclass
class SearchResult:
    """
    检索结果
    
    用于带评分的检索
    """
    memory: Memory
    relevance_score: float      # 相关性分数
    recency_score: float        # 时序分数
    importance_score: float     # 重要性分数
    final_score: float          # 综合分数
    
    @classmethod
    def calculate_final_score(
        cls,
        relevance: float,
        recency: float,
        importance: float,
        weights: Dict[str, float] = None
    ) -> float:
        """
        计算综合分数
        
        公式: S = α·R + β·γ + δ·I
        - R: 相关性
        - γ: 时序衰减
        - I: 重要性
        - α, β, δ: 权重系数
        """
        w = weights or {
            'relevance': 0.5,
            'recency': 0.3,
            'importance': 0.2
        }
        
        return (
            w['relevance'] * relevance +
            w['recency'] * recency +
            w['importance'] * importance
        )


@dataclass
class RetrievalConfig:
    """检索配置"""
    # 权重配置
    relevance_weight: float = 0.5
    recency_weight: float = 0.3
    importance_weight: float = 0.2
    
    # 时序衰减
    decay_rate: float = 0.995  # γ (0.99-0.999)
    
    # 检索限制
    max_results: int = 10
    
    # 最小分数阈值
    min_score: float = 0.3
