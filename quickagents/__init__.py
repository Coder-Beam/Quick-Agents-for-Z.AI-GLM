"""
QuickAgents - AI Agent Enhancement Toolkit

A Python package that provides local implementations of QuickAgents skills,
reducing token consumption by handling common operations locally.

Architecture (v2.6.8):
- SQLite主存储：高效查询，Token节省60%+
- Markdown辅助备份：人类可读，Git版本控制
- 双向同步：SQLite <-> Markdown
- 自我进化系统：自动触发、统一存储、经验闭环

Features:
- UnifiedDB: 统一数据库管理（记忆/任务/进度/反馈/决策）
- SkillEvolution: 统一的Skills自我进化系统
- MarkdownSync: 自动同步到Markdown文件
- GitHooks: Git钩子集成，自动触发进化分析
- File operations with hash-based caching
- Loop detection & Event reminders
- CLI tools

Installation:
    pip install -e .
    # or
    pip install quickagents

Usage:
    from quickagents import UnifiedDB, SkillEvolution, MarkdownSync, MemoryType
    
    # 统一数据库（主存储）
    db = UnifiedDB('.quickagents/unified.db')
    
    # 自我进化系统
    evolution = SkillEvolution(db)
    
    # 任务完成时触发
    evolution.on_task_complete({
        'task_id': 'T001',
        'task_name': '实现认证',
        'skills_used': ['tdd-workflow-skill'],
        'success': True
    })
    
    # Git提交时触发（自动或手动）
    evolution.on_git_commit()
    
    # 检查定期优化
    if evolution.check_periodic_trigger():
        evolution.run_periodic_optimization()

CLI Usage:
    qa stats                 # 数据库统计
    qa sync                  # 同步到Markdown
    qa evolution status      # 进化系统状态
    qa evolution optimize    # 执行定期优化
    qa hooks install         # 安装Git钩子
    qa memory get <key>      # 获取记忆
    qa tasks list            # 任务列表
    qa progress              # 当前进度
"""

__version__ = '2.8.1'
__author__ = 'Coder-Beam'

from .core.unified_db import UnifiedDB, MemoryType, TaskStatus, FeedbackType, get_unified_db
from .core.markdown_sync import MarkdownSync, get_markdown_sync
from .core.evolution import SkillEvolution, EvolutionTrigger, get_evolution
from .core.git_hooks import GitHooks
from .core.file_manager import FileManager
from .core.memory import MemoryManager
from .core.loop_detector import LoopDetector
from .core.reminder import Reminder
from .core.cache_db import CacheDB
from .utils.hash_cache import HashCache
from .skills import (
    FeedbackCollector, get_feedback_collector,
    TDDWorkflow, TDDPhase, get_tdd_workflow,
    GitCommit, get_git_commit
)

from .knowledge_graph import (
    KnowledgeGraph,
    NodeType,
    EdgeType,
    KnowledgeNode,
    KnowledgeEdge,
    SearchResult,
    KnowledgeGraphError,
    NodeNotFoundError,
    EdgeNotFoundError,
    DuplicateNodeError,
    DuplicateEdgeError,
    InvalidNodeTypeError,
    InvalidEdgeTypeError,
    CircularDependencyError,
    DatabaseIntegrityError,
    ExtractionError,
    SyncError,
)

# Windows脚本替代工具（可选依赖）
from .utils.script_helper import ScriptHelper

# 记忆辅助工具（v2.6.8+）
from .utils.memory_helper import (
    update_memory,
    update_memories,
    add_experiential_memory,
    update_working_memory,
    sync_all_memory
)

# 智能编辑工具（v2.6.9+）
from .utils.smart_editor import (
    smart_edit,
    diagnose_edit
)

# 浏览器自动化（可选依赖）
from .browser import Browser, BrowserBackend, Page, ConsoleLog, NetworkRequest

__all__ = [
    # Unified database (v2.2.0+)
    'UnifiedDB',
    'MemoryType',
    'TaskStatus', 
    'FeedbackType',
    'get_unified_db',
    # Skill Evolution (v2.3.0+)
    'SkillEvolution',
    'EvolutionTrigger',
    'get_evolution',
    # Git Hooks (v2.3.0+)
    'GitHooks',
    # Markdown sync
    'MarkdownSync',
    'get_markdown_sync',
    # Core modules (legacy)
    'FileManager',
    'MemoryManager', 
    'LoopDetector',
    'Reminder',
    'CacheDB',
    'HashCache',
    # Skills modules (100% localized)
    'FeedbackCollector',
    'get_feedback_collector',
    'TDDWorkflow',
    'TDDPhase',
    'get_tdd_workflow',
    'GitCommit',
    'get_git_commit',
    # Windows script helper (optional)
    'ScriptHelper',
    # Memory helper (v2.6.8+)
    'update_memory',
    'update_memories',
    'add_experiential_memory',
    'update_working_memory',
    'sync_all_memory',
    # Browser automation
    'Browser',
    'BrowserBackend',
    'Page',
    'ConsoleLog',
    'NetworkRequest',
    # Knowledge Graph (v2.4.0+)
    'KnowledgeGraph',
    'NodeType',
    'EdgeType',
    'KnowledgeNode',
    'KnowledgeEdge',
    'SearchResult',
    'KnowledgeGraphError',
    'NodeNotFoundError',
    'EdgeNotFoundError',
    'DuplicateNodeError',
    'DuplicateEdgeError',
    'InvalidNodeTypeError',
    'InvalidEdgeTypeError',
    'CircularDependencyError',
    'DatabaseIntegrityError',
    'ExtractionError',
    'SyncError',
    # Version
    '__version__',
]
