"""
CacheDB - SQLite本地缓存数据库

核心功能:
- 文件哈希缓存
- 记忆存储
- 操作历史
- 统计分析

优势:
- Python内置, 零安装
- 高性能, 支持复杂查询
- 事务安全
- 跨平台
"""

import sqlite3
import json
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from contextlib import contextmanager


class CacheDB:
    """
    SQLite缓存数据库管理器

    使用方式:
        db = CacheDB('.quickagents/cache.db')

        # 文件缓存
        db.cache_file('path/to/file.py', 'content...', 'hash123')
        cached = db.get_file_cache('path/to/file.py')

        # 记忆存储
        db.set_memory('project.name', 'QuickAgents')
        name = db.get_memory('project.name')

        # 操作历史
        db.log_operation('read', 'file.py', {'success': True})
        history = db.get_operation_history(limit=10)
    """

    def __init__(self, db_path: str = ".quickagents/cache.db"):
        """
        初始化数据库

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()

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
        """初始化数据库表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 文件缓存表
            cursor.execute("""
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
            """)

            # 创建索引
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_cache_hash 
                ON file_cache(content_hash)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_cache_path 
                ON file_cache(path)
            """)

            # 记忆存储表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT,
                    memory_type TEXT DEFAULT 'factual',
                    tags TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0
                )
            """)

            # 操作历史表
            cursor.execute("""
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
            """)

            # 循环检测表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS loop_detection (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fingerprint TEXT UNIQUE NOT NULL,
                    tool_name TEXT NOT NULL,
                    tool_args TEXT,
                    count INTEGER DEFAULT 1,
                    first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_seen TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 统计表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stat_key TEXT UNIQUE NOT NULL,
                    stat_value TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

    # ==================== 文件缓存操作 ====================

    def cache_file(self, path: str, content: str, content_hash: str = None) -> bool:
        """
        缓存文件内容

        Args:
            path: 文件路径
            content: 文件内容
            content_hash: 内容哈希（可选，自动计算）

        Returns:
            是否成功
        """
        if content_hash is None:
            content_hash = self._calculate_hash(content)

        stat = os.stat(path) if os.path.exists(path) else None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO file_cache (path, content_hash, content, size, mtime, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    content_hash = excluded.content_hash,
                    content = excluded.content,
                    size = excluded.size,
                    mtime = excluded.mtime,
                    updated_at = excluded.updated_at,
                    access_count = access_count + 1
            """,
                (
                    path,
                    content_hash,
                    content,
                    stat.st_size if stat else 0,
                    stat.st_mtime if stat else 0,
                    datetime.now().isoformat(),
                ),
            )

        return True

    def get_file_cache(self, path: str) -> Optional[Dict]:
        """
        获取文件缓存

        Args:
            path: 文件路径

        Returns:
            缓存数据或None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM file_cache WHERE path = ?
            """,
                (path,),
            )
            row = cursor.fetchone()

            if row:
                # 更新访问计数
                cursor.execute(
                    """
                    UPDATE file_cache SET access_count = access_count + 1 
                    WHERE path = ?
                """,
                    (path,),
                )

                return dict(row)

        return None

    def check_file_changed(self, path: str) -> Tuple[bool, Optional[str]]:
        """
        检查文件是否已改变

        Args:
            path: 文件路径

        Returns:
            (是否改变, 当前哈希)
        """
        if not os.path.exists(path):
            return True, None

        current_hash = self._calculate_file_hash(path)
        cached = self.get_file_cache(path)

        if cached is None:
            return True, current_hash

        return cached["content_hash"] != current_hash, current_hash

    def invalidate_file(self, path: str) -> bool:
        """使文件缓存失效"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM file_cache WHERE path = ?", (path,))
            return cursor.rowcount > 0

    def clear_file_cache(self) -> int:
        """清空所有文件缓存"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM file_cache")
            return cursor.rowcount

    # ==================== 记忆操作 ====================

    def set_memory(
        self, key: str, value: Any, memory_type: str = "factual", tags: List[str] = None
    ) -> bool:
        """
        设置记忆

        Args:
            key: 键名
            value: 值
            memory_type: 记忆类型 (factual/experiential/working)
            tags: 标签列表
        """
        value_str = (
            json.dumps(value, ensure_ascii=False)
            if not isinstance(value, str)
            else value
        )
        tags_str = json.dumps(tags, ensure_ascii=False) if tags else None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO memory (key, value, memory_type, tags, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    memory_type = excluded.memory_type,
                    tags = excluded.tags,
                    updated_at = excluded.updated_at,
                    access_count = access_count + 1
            """,
                (key, value_str, memory_type, tags_str, datetime.now().isoformat()),
            )

        return True

    def get_memory(self, key: str, default: Any = None) -> Any:
        """获取记忆"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM memory WHERE key = ?", (key,))
            row = cursor.fetchone()

            if row:
                try:
                    return json.loads(row["value"])
                except json.JSONDecodeError:
                    return row["value"]

        return default

    def search_memory(self, keyword: str, memory_type: str = None) -> List[Dict]:
        """搜索记忆"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if memory_type:
                cursor.execute(
                    """
                    SELECT * FROM memory 
                    WHERE (key LIKE ? OR value LIKE ?) AND memory_type = ?
                    ORDER BY updated_at DESC
                """,
                    (f"%{keyword}%", f"%{keyword}%", memory_type),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM memory 
                    WHERE key LIKE ? OR value LIKE ?
                    ORDER BY updated_at DESC
                """,
                    (f"%{keyword}%", f"%{keyword}%"),
                )

            return [dict(row) for row in cursor.fetchall()]

    def delete_memory(self, key: str) -> bool:
        """删除记忆"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memory WHERE key = ?", (key,))
            return cursor.rowcount > 0

    # ==================== 操作历史 ====================

    def log_operation(
        self,
        operation: str,
        target: str = None,
        params: Dict = None,
        result: Dict = None,
        token_cost: int = 0,
        duration_ms: int = 0,
    ) -> bool:
        """记录操作历史"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO operation_history 
                (operation, target, params, result, token_cost, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    operation,
                    target,
                    json.dumps(params) if params else None,
                    json.dumps(result) if result else None,
                    token_cost,
                    duration_ms,
                ),
            )

        return True

    def get_operation_history(
        self, limit: int = 100, operation: str = None
    ) -> List[Dict]:
        """获取操作历史"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if operation:
                cursor.execute(
                    """
                    SELECT * FROM operation_history 
                    WHERE operation = ?
                    ORDER BY created_at DESC LIMIT ?
                """,
                    (operation, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM operation_history 
                    ORDER BY created_at DESC LIMIT ?
                """,
                    (limit,),
                )

            return [dict(row) for row in cursor.fetchall()]

    # ==================== 循环检测 ====================

    def check_loop(
        self, tool_name: str, tool_args: Dict, threshold: int = 3
    ) -> Optional[Dict]:
        """
        检测循环调用

        Args:
            tool_name: 工具名称
            tool_args: 工具参数
            threshold: 阈值

        Returns:
            检测结果或None
        """
        fingerprint = self._calculate_fingerprint(tool_name, tool_args)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 查找现有记录
            cursor.execute(
                """
                SELECT * FROM loop_detection WHERE fingerprint = ?
            """,
                (fingerprint,),
            )
            row = cursor.fetchone()

            if row:
                # 更新计数
                new_count = row["count"] + 1
                cursor.execute(
                    """
                    UPDATE loop_detection 
                    SET count = ?, last_seen = ?
                    WHERE fingerprint = ?
                """,
                    (new_count, datetime.now().isoformat(), fingerprint),
                )

                if new_count >= threshold:
                    return {
                        "detected": True,
                        "fingerprint": fingerprint,
                        "tool_name": tool_name,
                        "count": new_count,
                        "first_seen": row["first_seen"],
                    }
            else:
                # 创建新记录
                cursor.execute(
                    """
                    INSERT INTO loop_detection (fingerprint, tool_name, tool_args)
                    VALUES (?, ?, ?)
                """,
                    (fingerprint, tool_name, json.dumps(tool_args)),
                )

        return None

    def reset_loop_detection(self) -> None:
        """重置循环检测"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM loop_detection")

    # ==================== 统计操作 ====================

    def get_stats(self) -> Dict:
        """获取缓存统计"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 文件缓存统计
            cursor.execute(
                "SELECT COUNT(*) as count, SUM(size) as total_size FROM file_cache"
            )
            file_stats = cursor.fetchone()

            # 记忆统计
            cursor.execute("SELECT COUNT(*) as count FROM memory")
            memory_count = cursor.fetchone()["count"]

            # 操作统计
            cursor.execute(
                "SELECT SUM(token_cost) as total_tokens FROM operation_history"
            )
            token_stats = cursor.fetchone()

            return {
                "file_cache": {
                    "count": file_stats["count"] or 0,
                    "total_size": file_stats["total_size"] or 0,
                    "total_kb": round((file_stats["total_size"] or 0) / 1024, 2),
                },
                "memory": {"count": memory_count},
                "tokens": {"total_saved": token_stats["total_tokens"] or 0},
            }

    def cleanup_old_records(self, days: int = 30) -> Dict:
        """清理旧记录"""
        cutoff = datetime.now().timestamp() - (days * 86400)
        cutoff_str = datetime.fromtimestamp(cutoff).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 清理操作历史
            cursor.execute(
                "DELETE FROM operation_history WHERE created_at < ?", (cutoff_str,)
            )
            ops_deleted = cursor.rowcount

            # 清理循环检测
            cursor.execute(
                "DELETE FROM loop_detection WHERE last_seen < ?", (cutoff_str,)
            )
            loops_deleted = cursor.rowcount

        return {"operations_deleted": ops_deleted, "loops_deleted": loops_deleted}

    # ==================== 工具方法 ====================

    def _calculate_hash(self, content: str) -> str:
        """计算内容哈希"""
        return hashlib.md5(content.encode("utf-8")).hexdigest()[:16]

    def _calculate_file_hash(self, path: str) -> str:
        """计算文件哈希"""
        from ..utils.encoding import read_file_utf8

        content = read_file_utf8(path)
        return self._calculate_hash(content)

    def _calculate_fingerprint(self, tool_name: str, tool_args: Dict) -> str:
        """计算工具调用指纹"""
        normalized = json.dumps(tool_args, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(f"{tool_name}:{normalized}".encode()).hexdigest()[:8]


# 全局实例
_global_db: Optional[CacheDB] = None


def get_cache_db(db_path: str = ".quickagents/cache.db") -> CacheDB:
    """获取全局缓存数据库实例"""
    global _global_db
    if _global_db is None:
        _global_db = CacheDB(db_path)
    return _global_db
