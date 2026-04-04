"""
Memory Helper - 记忆更新辅助工具

解决 AI 代理直接 write MEMORY.md 导致的同步冲突问题。
提供统一的记忆更新接口，自动处理 SQLite 写入和 Markdown 同步。

使用方式:
    from quickagents.utils.memory_helper import update_memory, update_memories

    # 更新单个记忆
    update_memory('project.name', 'MyProject')

    # 批量更新记忆
    update_memories({
        'project.name': 'MyProject',
        'project.version': '1.0.0',
        'current.task': '实现认证'
    })
"""

from typing import Dict, Any
from ..core.unified_db import UnifiedDB, MemoryType, get_unified_db
from ..core.markdown_sync import MarkdownSync, get_markdown_sync


def update_memory(
    key: str,
    value: Any,
    memory_type: MemoryType = MemoryType.FACTUAL,
    category: str = None,
    auto_sync: bool = True,
    db: UnifiedDB = None,
    sync: MarkdownSync = None,
) -> bool:
    """
    更新单个记忆项

    Args:
        key: 键名（支持点分隔，如 'project.name'）
        value: 值
        memory_type: 记忆类型（默认 FACTUAL）
        category: 分类（可选）
        auto_sync: 是否自动同步到 Markdown（默认 True）
        db: UnifiedDB 实例（可选，默认自动创建）
        sync: MarkdownSync 实例（可选，默认自动创建）

    Returns:
        是否成功

    Example:
        >>> update_memory('project.name', 'QuickAgents')
        >>> update_memory('current.task', '实现认证', MemoryType.WORKING)
        >>> update_memory('lesson.001', '避免过度工程', MemoryType.EXPERIENTIAL, category='pitfalls')
    """
    db = db or get_unified_db()

    # 写入 SQLite
    success = db.set_memory(key, value, memory_type, category=category)

    # 自动同步到 Markdown
    if success and auto_sync:
        sync = sync or get_markdown_sync(db)
        sync.sync_memory()

    return success


def update_memories(
    memories: Dict[str, Any],
    memory_type: MemoryType = MemoryType.FACTUAL,
    categories: Dict[str, str] = None,
    auto_sync: bool = True,
    db: UnifiedDB = None,
    sync: MarkdownSync = None,
) -> Dict[str, bool]:
    """
    批量更新记忆

    Args:
        memories: 记忆字典 {key: value}
        memory_type: 记忆类型（默认 FACTUAL）
        categories: 分类字典 {key: category}（可选）
        auto_sync: 是否自动同步到 Markdown（默认 True）
        db: UnifiedDB 实例（可选）
        sync: MarkdownSync 实例（可选）

    Returns:
        结果字典 {key: success}

    Example:
        >>> update_memories({
        ...     'project.name': 'QuickAgents',
        ...     'project.version': '1.0.0',
        ...     'current.task': '实现认证'
        ... })
    """
    db = db or get_unified_db()
    categories = categories or {}
    results = {}

    # 批量写入 SQLite
    for key, value in memories.items():
        category = categories.get(key)
        results[key] = db.set_memory(key, value, memory_type, category=category)

    # 统一同步到 Markdown（只同步一次，提高效率）
    if auto_sync and any(results.values()):
        sync = sync or get_markdown_sync(db)
        sync.sync_memory()

    return results


def add_experiential_memory(
    content: str,
    category: str = "general",
    auto_sync: bool = True,
    db: UnifiedDB = None,
    sync: MarkdownSync = None,
) -> bool:
    """
    添加经验记忆（快捷方法）

    Args:
        content: 经验内容
        category: 分类（默认 'general'）
        auto_sync: 是否自动同步
        db: UnifiedDB 实例
        sync: MarkdownSync 实例

    Returns:
        是否成功

    Example:
        >>> add_experiential_memory('避免在循环中调用API', category='pitfalls')
    """
    from datetime import datetime

    # 生成唯一键名
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    key = f"exp.{category}.{timestamp}"

    return update_memory(
        key,
        content,
        MemoryType.EXPERIENTIAL,
        category=category,
        auto_sync=auto_sync,
        db=db,
        sync=sync,
    )


def update_working_memory(
    key: str,
    value: Any,
    auto_sync: bool = True,
    db: UnifiedDB = None,
    sync: MarkdownSync = None,
) -> bool:
    """
    更新工作记忆（快捷方法）

    Args:
        key: 键名
        value: 值
        auto_sync: 是否自动同步
        db: UnifiedDB 实例
        sync: MarkdownSync 实例

    Returns:
        是否成功

    Example:
        >>> update_working_memory('current.task', '实现认证')
    """
    return update_memory(
        key, value, MemoryType.WORKING, auto_sync=auto_sync, db=db, sync=sync
    )


def sync_all_memory(db: UnifiedDB = None) -> Dict[str, bool]:
    """
    同步所有记忆到 Markdown

    Args:
        db: UnifiedDB 实例

    Returns:
        同步结果

    Example:
        >>> sync_all_memory()
    """
    db = db or get_unified_db()
    sync = get_markdown_sync(db)
    return sync.sync_all()


# 便捷导出
__all__ = [
    "update_memory",
    "update_memories",
    "add_experiential_memory",
    "update_working_memory",
    "sync_all_memory",
]
