"""
QuickAgents Core - 核心模块

包含:
- ConnectionManager: 连接管理器
- TransactionManager: 事务管理器
- MigrationManager: 迁移管理器
- UnifiedDB: 统一数据库（V2）
- Repositories: 数据仓储层
- LoopDetector: 循环检测器
- FileManager: 文件管理器
- MarkdownSync: Markdown同步器
- Reminder: 事件提醒
- Evolution: 自我进化
"""

# V2 核心组件
from .connection_manager import ConnectionManager, PoolConfig
from .transaction_manager import TransactionManager, TransactionError, RetryConfig
from .migration_manager import MigrationManager, Migration, MigrationResult
from .session import Session

# V2 UnifiedDB
from .unified_db import UnifiedDB, get_unified_db, reset_global_db

# V1 备份（已归档到 archive/ 目录）
try:
    from .unified_db_v1_backup import UnifiedDB as UnifiedDBV1
except ImportError:
    UnifiedDBV1 = None

# Repositories
from .repositories import (
    BaseRepository,
    QueryBuilder,
    MemoryRepository,
    TaskRepository,
    ProgressRepository,
    FeedbackRepository,
    # Models
    Memory,
    Task,
    Progress,
    Feedback,
    MemoryType,
    TaskStatus,
    TaskPriority,
    FeedbackType,
    SearchResult,
    RetrievalConfig,
)

# 其他模块
from .loop_detector import LoopDetector, LoopDetectorConfig
from .file_manager import FileManager
from .markdown_sync import MarkdownSync
from .reminder import Reminder
from .evolution import SkillEvolution

__all__ = [
    # V2 核心组件
    "ConnectionManager",
    "PoolConfig",
    "TransactionManager",
    "TransactionError",
    "RetryConfig",
    "MigrationManager",
    "Migration",
    "MigrationResult",
    "Session",
    "Session",
    # V2 UnifiedDB
    "UnifiedDB",
    "get_unified_db",
    "reset_global_db",
    # V1 备份
    "UnifiedDBV1",
    # Repositories
    "BaseRepository",
    "QueryBuilder",
    "MemoryRepository",
    "TaskRepository",
    "ProgressRepository",
    "FeedbackRepository",
    # Models
    "Memory",
    "Task",
    "Progress",
    "Feedback",
    "MemoryType",
    "TaskStatus",
    "TaskPriority",
    "FeedbackType",
    "SearchResult",
    "RetrievalConfig",
    # 其他模块
    "LoopDetector",
    "LoopDetectorConfig",
    "FileManager",
    "MarkdownSync",
    "Reminder",
    "SkillEvolution",
]
