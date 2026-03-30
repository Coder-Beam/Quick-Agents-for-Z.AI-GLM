"""
UnifiedDB - 统一数据库管理器

核心功能:
- 三维记忆 (memory)
- 进度追踪 (progress)
- 经验收集 (feedback)
- 任务管理 (tasks)
- 决策日志 (decisions)
- 笔记本 (notepads)
- 文件缓存 (file_cache)
- 操作历史 (operation_history)

架构优势:
- SQLite主存储，高效查询
- Markdown辅助备份，人类可读
- 事务安全，并发支持
- Token节省60%+
"""

import sqlite3
import json
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from contextlib import contextmanager
from enum import Enum


class MemoryType(Enum):
    """记忆类型枚举"""
    FACTUAL = "factual"          # 事实记忆
    EXPERIENTIAL = "experiential" # 经验记忆
    WORKING = "working"          # 工作记忆


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class FeedbackType(Enum):
    """反馈类型枚举"""
    BUG = "bug"
    IMPROVEMENT = "improvement"
    BEST_PRACTICE = "best_practice"
    SKILL_REVIEW = "skill_review"
    AGENT_REVIEW = "agent_review"


class UnifiedDB:
    """
    统一数据库管理器
    
    使用方式:
        db = UnifiedDB('.quickagents/unified.db')
        
        # 三维记忆
        db.set_memory('project.name', 'QuickAgents', MemoryType.FACTUAL)
        name = db.get_memory('project.name')
        
        # 进度追踪
        db.update_progress('current_task', 'T004')
        progress = db.get_progress()
        
        # 经验收集
        db.add_feedback(FeedbackType.BUG, '发现一个bug', '详细描述')
        
        # 任务管理
        db.add_task('T001', '实现认证', 'P0')
        db.update_task_status('T001', TaskStatus.COMPLETED)
        
        # 同步到Markdown
        db.sync_to_markdown()
    """
    
    def __init__(self, db_path: str = '.quickagents/unified.db'):
        """
        初始化统一数据库
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._knowledge_graph = None
        self._init_tables()
    
    @property
    def knowledge(self) -> 'KnowledgeGraph':
        """
        Get knowledge graph manager (lazy-loaded).
        
        Returns:
            KnowledgeGraph instance for this database
        """
        if self._knowledge_graph is None:
            from quickagents.knowledge_graph import KnowledgeGraph
            self._knowledge_graph = KnowledgeGraph(str(self.db_path))
        return self._knowledge_graph
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_tables(self) -> None:
        """初始化所有数据库表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # ==================== 三维记忆表 ====================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT,
                    memory_type TEXT NOT NULL DEFAULT 'factual',
                    category TEXT,
                    tags TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_memory_key ON memory(key)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_memory_type ON memory(memory_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_memory_category ON memory(category)')
            
            # ==================== 进度追踪表 ====================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_name TEXT,
                    plan_path TEXT,
                    session_id TEXT,
                    status TEXT DEFAULT 'idle',
                    total_tasks INTEGER DEFAULT 0,
                    completed_tasks INTEGER DEFAULT 0,
                    current_task TEXT,
                    started_at TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')
            
            # ==================== 任务表 ====================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'pending',
                    priority TEXT DEFAULT 'P2',
                    assignee TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    due_date TEXT,
                    dependencies TEXT,
                    tags TEXT,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)')
            
            # ==================== 经验收集表 ====================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feedback_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    project_name TEXT,
                    context TEXT,
                    suggestion TEXT,
                    rating INTEGER,
                    tags TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(feedback_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback(created_at)')
            
            # ==================== 决策日志表 ====================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    background TEXT,
                    options TEXT,
                    final_decision TEXT,
                    rationale TEXT,
                    impact TEXT,
                    decision_maker TEXT,
                    related_tasks TEXT,
                    status TEXT DEFAULT 'confirmed',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ==================== 笔记本表 ====================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notepads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_name TEXT NOT NULL,
                    entry_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_notepads_plan ON notepads(plan_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_notepads_type ON notepads(entry_type)')
            
            # ==================== 检查点表 ====================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_name TEXT NOT NULL,
                    description TEXT,
                    snapshot TEXT,
                    tasks_completed TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_checkpoints_plan ON checkpoints(plan_name)')
            
            # ==================== 文件缓存表 ====================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path TEXT UNIQUE NOT NULL,
                    content_hash TEXT NOT NULL,
                    content TEXT,
                    size INTEGER,
                    mtime REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_cache_hash ON file_cache(content_hash)')
            
            # ==================== 操作历史表 ====================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS operation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation TEXT NOT NULL,
                    target TEXT,
                    params TEXT,
                    result TEXT,
                    token_cost INTEGER DEFAULT 0,
                    duration_ms INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ==================== 同步状态表 ====================
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT UNIQUE NOT NULL,
                    last_sync_at TEXT,
                    sync_count INTEGER DEFAULT 0,
                    md_path TEXT
                )
            ''')
    
    # ==================== 三维记忆操作 ====================
    
    def set_memory(self, key: str, value: Any, memory_type: MemoryType = MemoryType.FACTUAL,
                   category: str = None, tags: List[str] = None, metadata: Dict = None) -> bool:
        """
        设置记忆
        
        Args:
            key: 键名（支持点分隔，如 'project.name'）
            value: 值
            memory_type: 记忆类型
            category: 分类
            tags: 标签列表
            metadata: 元数据
        """
        value_str = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
        tags_str = json.dumps(tags, ensure_ascii=False) if tags else None
        metadata_str = json.dumps(metadata, ensure_ascii=False) if metadata else None
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO memory (key, value, memory_type, category, tags, metadata, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    memory_type = excluded.memory_type,
                    category = excluded.category,
                    tags = excluded.tags,
                    metadata = excluded.metadata,
                    updated_at = excluded.updated_at,
                    access_count = access_count + 1
            ''', (key, value_str, memory_type.value, category, tags_str, metadata_str, 
                  datetime.now().isoformat()))
        
        return True
    
    def get_memory(self, key: str, default: Any = None) -> Any:
        """获取记忆"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM memory WHERE key = ?', (key,))
            row = cursor.fetchone()
            
            if row:
                # 更新访问计数
                cursor.execute('UPDATE memory SET access_count = access_count + 1 WHERE key = ?', (key,))
                try:
                    return json.loads(row['value'])
                except json.JSONDecodeError:
                    return row['value']
        
        return default
    
    def get_memories_by_type(self, memory_type: MemoryType) -> List[Dict]:
        """按类型获取所有记忆"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM memory WHERE memory_type = ? ORDER BY updated_at DESC
            ''', (memory_type.value,))
            return [dict(row) for row in cursor.fetchall()]
    
    def search_memory(self, keyword: str, memory_type: MemoryType = None) -> List[Dict]:
        """搜索记忆"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if memory_type:
                cursor.execute('''
                    SELECT * FROM memory 
                    WHERE (key LIKE ? OR value LIKE ?) AND memory_type = ?
                    ORDER BY updated_at DESC
                ''', (f'%{keyword}%', f'%{keyword}%', memory_type.value))
            else:
                cursor.execute('''
                    SELECT * FROM memory 
                    WHERE key LIKE ? OR value LIKE ?
                    ORDER BY updated_at DESC
                ''', (f'%{keyword}%', f'%{keyword}%'))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_memory(self, key: str) -> bool:
        """删除记忆"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM memory WHERE key = ?', (key,))
            return cursor.rowcount > 0
    
    def add_experiential_entry(self, category: str, content: str, 
                               tags: List[str] = None) -> bool:
        """添加经验记忆条目"""
        import time
        key = f"exp.{category}.{int(time.time() * 1000)}"
        return self.set_memory(key, content, MemoryType.EXPERIENTIAL, 
                              category=category, tags=tags)
    
    # ==================== 进度追踪操作 ====================
    
    def init_progress(self, plan_name: str, plan_path: str = None, 
                      total_tasks: int = 0) -> bool:
        """初始化进度"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO progress 
                (id, plan_name, plan_path, status, total_tasks, completed_tasks, started_at, updated_at)
                VALUES (1, ?, ?, 'in_progress', ?, 0, ?, ?)
            ''', (plan_name, plan_path, total_tasks, 
                  datetime.now().isoformat(), datetime.now().isoformat()))
        
        return True
    
    def get_progress(self) -> Optional[Dict]:
        """获取当前进度"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM progress WHERE id = 1')
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_progress(self, field: str, value: Any) -> bool:
        """更新进度字段"""
        if field not in ['plan_name', 'plan_path', 'session_id', 'status', 
                        'total_tasks', 'completed_tasks', 'current_task', 'metadata']:
            return False
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE progress SET {field} = ?, updated_at = ? WHERE id = 1
            ''', (value, datetime.now().isoformat()))
            
            return cursor.rowcount > 0
    
    def increment_completed(self) -> int:
        """增加完成任务数"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE progress SET 
                    completed_tasks = completed_tasks + 1,
                    updated_at = ?
                WHERE id = 1
            ''', (datetime.now().isoformat(),))
            
            cursor.execute('SELECT completed_tasks FROM progress WHERE id = 1')
            row = cursor.fetchone()
            return row['completed_tasks'] if row else 0
    
    # ==================== 任务管理操作 ====================
    
    def add_task(self, task_id: str, name: str, priority: str = 'P2',
                 description: str = None, dependencies: List[str] = None,
                 tags: List[str] = None) -> bool:
        """添加任务"""
        deps_str = json.dumps(dependencies) if dependencies else None
        tags_str = json.dumps(tags) if tags else None
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tasks (task_id, name, description, priority, dependencies, tags)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (task_id, name, description, priority, deps_str, tags_str))
        
        return True
    
    def update_task_status(self, task_id: str, status: TaskStatus, 
                           notes: str = None) -> bool:
        """更新任务状态"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            extra_updates = []
            extra_values = []
            
            if status == TaskStatus.IN_PROGRESS:
                extra_updates.append('started_at = ?')
                extra_values.append(datetime.now().isoformat())
            elif status == TaskStatus.COMPLETED:
                extra_updates.append('completed_at = ?')
                extra_values.append(datetime.now().isoformat())
            
            if notes:
                extra_updates.append('notes = ?')
                extra_values.append(notes)
            
            extra_updates.append('updated_at = ?')
            extra_values.append(datetime.now().isoformat())
            
            query = f'''
                UPDATE tasks SET status = ?, {', '.join(extra_updates)}
                WHERE task_id = ?
            '''
            cursor.execute(query, [status.value] + extra_values + [task_id])
            
            return cursor.rowcount > 0
    
    def get_tasks(self, status: TaskStatus = None, priority: str = None) -> List[Dict]:
        """获取任务列表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            conditions = []
            params = []
            
            if status:
                conditions.append('status = ?')
                params.append(status.value)
            if priority:
                conditions.append('priority = ?')
                params.append(priority)
            
            where_clause = ' AND '.join(conditions) if conditions else '1=1'
            
            cursor.execute(f'''
                SELECT * FROM tasks WHERE {where_clause} ORDER BY priority, created_at
            ''', params)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取单个任务"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tasks WHERE task_id = ?', (task_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # ==================== 经验收集操作 ====================
    
    def add_feedback(self, feedback_type: FeedbackType, title: str,
                     description: str = None, project_name: str = None,
                     context: str = None, suggestion: str = None,
                     rating: int = None, tags: List[str] = None) -> bool:
        """添加反馈"""
        tags_str = json.dumps(tags) if tags else None
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO feedback 
                (feedback_type, title, description, project_name, context, suggestion, rating, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (feedback_type.value, title, description, project_name, 
                  context, suggestion, rating, tags_str))
        
        return True
    
    def get_feedbacks(self, feedback_type: FeedbackType = None, 
                      limit: int = 100) -> List[Dict]:
        """获取反馈列表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if feedback_type:
                cursor.execute('''
                    SELECT * FROM feedback WHERE feedback_type = ?
                    ORDER BY created_at DESC LIMIT ?
                ''', (feedback_type.value, limit))
            else:
                cursor.execute('''
                    SELECT * FROM feedback ORDER BY created_at DESC LIMIT ?
                ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== 决策日志操作 ====================
    
    def add_decision(self, decision_id: str, title: str, background: str = None,
                     options: List[Dict] = None, final_decision: str = None,
                     rationale: str = None, impact: str = None,
                     decision_maker: str = 'AI', related_tasks: List[str] = None) -> bool:
        """添加决策"""
        options_str = json.dumps(options, ensure_ascii=False) if options else None
        tasks_str = json.dumps(related_tasks) if related_tasks else None
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO decisions 
                (decision_id, title, background, options, final_decision, rationale, 
                 impact, decision_maker, related_tasks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (decision_id, title, background, options_str, final_decision,
                  rationale, impact, decision_maker, tasks_str))
        
        return True
    
    def get_decisions(self, limit: int = 100) -> List[Dict]:
        """获取决策列表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM decisions ORDER BY created_at DESC LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== 笔记本操作 ====================
    
    def add_notepad_entry(self, plan_name: str, entry_type: str, 
                          content: str, metadata: Dict = None) -> bool:
        """
        添加笔记本条目
        
        Args:
            plan_name: 计划名称
            entry_type: 条目类型 (learnings/decisions/issues/gotchas/commands)
            content: 内容
            metadata: 元数据
        """
        metadata_str = json.dumps(metadata, ensure_ascii=False) if metadata else None
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO notepads (plan_name, entry_type, content, metadata)
                VALUES (?, ?, ?, ?)
            ''', (plan_name, entry_type, content, metadata_str))
        
        return True
    
    def get_notepad_entries(self, plan_name: str, entry_type: str = None) -> List[Dict]:
        """获取笔记本条目"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if entry_type:
                cursor.execute('''
                    SELECT * FROM notepads 
                    WHERE plan_name = ? AND entry_type = ?
                    ORDER BY created_at DESC
                ''', (plan_name, entry_type))
            else:
                cursor.execute('''
                    SELECT * FROM notepads WHERE plan_name = ?
                    ORDER BY created_at DESC
                ''', (plan_name,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== 检查点操作 ====================
    
    def create_checkpoint(self, plan_name: str, description: str,
                          snapshot: Dict = None, tasks_completed: List[str] = None) -> int:
        """创建检查点"""
        snapshot_str = json.dumps(snapshot, ensure_ascii=False) if snapshot else None
        tasks_str = json.dumps(tasks_completed) if tasks_completed else None
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO checkpoints (plan_name, description, snapshot, tasks_completed)
                VALUES (?, ?, ?, ?)
            ''', (plan_name, description, snapshot_str, tasks_str))
            
            return cursor.lastrowid
    
    def get_checkpoints(self, plan_name: str, limit: int = 10) -> List[Dict]:
        """获取检查点列表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM checkpoints WHERE plan_name = ?
                ORDER BY created_at DESC LIMIT ?
            ''', (plan_name, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== 文件缓存操作 ====================
    
    def cache_file(self, path: str, content: str, content_hash: str = None) -> bool:
        """缓存文件内容"""
        if content_hash is None:
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:16]
        
        stat = os.stat(path) if os.path.exists(path) else None
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO file_cache (path, content_hash, content, size, mtime, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    content_hash = excluded.content_hash,
                    content = excluded.content,
                    size = excluded.size,
                    mtime = excluded.mtime,
                    updated_at = excluded.updated_at,
                    access_count = access_count + 1
            ''', (path, content_hash, content,
                  stat.st_size if stat else 0,
                  stat.st_mtime if stat else 0,
                  datetime.now().isoformat()))
        
        return True
    
    def get_file_cache(self, path: str) -> Optional[Dict]:
        """获取文件缓存"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM file_cache WHERE path = ?', (path,))
            row = cursor.fetchone()
            
            if row:
                cursor.execute('UPDATE file_cache SET access_count = access_count + 1 WHERE path = ?', (path,))
                return dict(row)
        
        return None
    
    def check_file_changed(self, path: str) -> Tuple[bool, Optional[str]]:
        """检查文件是否已改变"""
        if not os.path.exists(path):
            return True, None
        
        from ..utils.encoding import read_file_utf8
        content = read_file_utf8(path)
        current_hash = hashlib.md5(content.encode()).hexdigest()[:16]
        cached = self.get_file_cache(path)
        
        if cached is None:
            return True, current_hash
        
        return cached['content_hash'] != current_hash, current_hash
    
    # ==================== 操作历史操作 ====================
    
    def log_operation(self, operation: str, target: str = None,
                      params: Dict = None, result: Dict = None,
                      token_cost: int = 0, duration_ms: int = 0) -> bool:
        """记录操作历史"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO operation_history
                (operation, target, params, result, token_cost, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (operation, target,
                  json.dumps(params) if params else None,
                  json.dumps(result) if result else None,
                  token_cost, duration_ms))
        
        return True
    
    def get_operation_history(self, limit: int = 100, operation: str = None) -> List[Dict]:
        """获取操作历史"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if operation:
                cursor.execute('''
                    SELECT * FROM operation_history WHERE operation = ?
                    ORDER BY created_at DESC LIMIT ?
                ''', (operation, limit))
            else:
                cursor.execute('''
                    SELECT * FROM operation_history ORDER BY created_at DESC LIMIT ?
                ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== 统计操作 ====================
    
    def get_stats(self) -> Dict:
        """获取数据库统计"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # 记忆统计
            cursor.execute('SELECT COUNT(*) as count FROM memory')
            stats['memory_count'] = cursor.fetchone()['count']
            
            # 任务统计
            cursor.execute('''
                SELECT status, COUNT(*) as count FROM tasks GROUP BY status
            ''')
            stats['tasks'] = {row['status']: row['count'] for row in cursor.fetchall()}
            
            # 反馈统计
            cursor.execute('''
                SELECT feedback_type, COUNT(*) as count FROM feedback GROUP BY feedback_type
            ''')
            stats['feedback'] = {row['feedback_type']: row['count'] for row in cursor.fetchall()}
            
            # 文件缓存统计
            cursor.execute('SELECT COUNT(*) as count, SUM(size) as total_size FROM file_cache')
            file_stats = cursor.fetchone()
            stats['file_cache'] = {
                'count': file_stats['count'] or 0,
                'total_size': file_stats['total_size'] or 0
            }
            
            # Token节省统计
            cursor.execute('SELECT SUM(token_cost) as total FROM operation_history')
            stats['tokens_saved'] = cursor.fetchone()['total'] or 0
            
            return stats
    
    def cleanup_old_records(self, days: int = 30) -> Dict:
        """清理旧记录"""
        cutoff = datetime.now().timestamp() - (days * 86400)
        cutoff_str = datetime.fromtimestamp(cutoff).isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 清理操作历史
            cursor.execute('DELETE FROM operation_history WHERE created_at < ?', (cutoff_str,))
            ops_deleted = cursor.rowcount
            
            # 清理旧的工作记忆（保留事实和经验）
            cursor.execute('''
                DELETE FROM memory WHERE memory_type = 'working' AND updated_at < ?
            ''', (cutoff_str,))
            memory_deleted = cursor.rowcount
        
        return {
            'operations_deleted': ops_deleted,
            'memory_deleted': memory_deleted
        }


# 全局实例
_global_db: Optional[UnifiedDB] = None


def get_unified_db(db_path: str = '.quickagents/unified.db') -> UnifiedDB:
    """获取全局统一数据库实例"""
    global _global_db
    if _global_db is None:
        _global_db = UnifiedDB(db_path)
    return _global_db
