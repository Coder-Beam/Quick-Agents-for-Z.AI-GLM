"""
QuickAgents - AI Agent Enhancement Toolkit

A Python package that provides local implementations of QuickAgents skills,
reducing token consumption by handling common operations locally.

Features:
- File operations with hash-based caching (SQLite backend)
- Memory management
- Loop detection
- Event reminders
- CLI tools

Installation:
    pip install -e .
    # or
    pip install quickagents

Usage:
    from quickagents import MemoryManager, LoopDetector, FileManager, CacheDB
    
    # SQLite-based file operations with caching
    fm = FileManager()
    content = fm.read('path/to/file.md')  # Cached read
    fm.edit('path/to/file.md', old, new)   # Auto-validates cache
    
    # Memory management
    memory = MemoryManager('.opencode/memory/MEMORY.md')
    memory.set('project.name', 'MyProject')
    name = memory.get('project.name')
    
    # Loop detection
    detector = LoopDetector()
    result = detector.check('read', {'path': 'file.md'})
    if result and result['detected']:
        print(f"Loop detected: {result['count']} times")
    
    # Direct SQLite cache access
    db = CacheDB('.quickagents/cache.db')
    stats = db.get_stats()

CLI Usage:
    qa read <file>           # 智能读取
    qa write <file> <content> # 写入
    qa edit <file> <old> <new> # 编辑
    qa cache stats           # 缓存统计
    qa memory get <key>      # 获取记忆
    qa loop check            # 循环检测
    qa stats                 # 整体统计
"""

__version__ = '1.0.0'
__author__ = 'QuickAgents Team'

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

# Windows脚本替代工具（可选依赖）
from .utils.script_helper import ScriptHelper

__all__ = [
    # Core modules
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
    # Version
    '__version__',
]
