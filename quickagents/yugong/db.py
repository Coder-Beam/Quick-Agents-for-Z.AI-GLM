"""
YuGongDB - 愚公循环持久化层

基于设计文档 Section 24 定义的 7 张 SQLite 表:
- yugong_stories: UserStory 存储
- yugong_iterations: 迭代历史
- yugong_progress: 进度日志
- yugong_context: 待注入上下文
- yugong_state: 循环状态
- yugong_checkpoints: 检查点
- yugong_logs: 日志记录

连接管理:
- 通过 ConnectionManager 管理数据库连接（连接池、线程安全、WAL）
- 支持 db_path（向后兼容，含 :memory:）或 ConnectionManager（共享连接池）
"""

import json
import sqlite3
import logging
from datetime import datetime
from typing import Optional, Union

from .models import (
    UserStory,
    StoryStatus,
    StoryPriority,
    LoopResult,
    LoopState,
)

logger = logging.getLogger(__name__)

_CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS yugong_stories (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    acceptance_criteria TEXT,
    priority INTEGER DEFAULT 3,
    status TEXT DEFAULT 'pending',
    dependencies TEXT,
    estimated_complexity TEXT DEFAULT 'medium',
    tags TEXT,
    category TEXT DEFAULT '',
    passes INTEGER DEFAULT 0,
    notes TEXT DEFAULT '',
    files_changed TEXT,
    error_log TEXT DEFAULT '',
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    token_usage TEXT
);

CREATE TABLE IF NOT EXISTS yugong_iterations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    iteration INTEGER NOT NULL,
    story_id TEXT NOT NULL,
    success INTEGER NOT NULL,
    output TEXT,
    duration_ms INTEGER,
    token_usage TEXT,
    files_changed TEXT,
    error TEXT,
    exit_signal INTEGER DEFAULT 0,
    completion_indicators INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS yugong_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS yugong_context (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS yugong_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    state_json TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS yugong_checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    checkpoint_type TEXT NOT NULL,
    state_json TEXT NOT NULL,
    story_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS yugong_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_level TEXT NOT NULL,
    log_type TEXT NOT NULL,
    message TEXT NOT NULL,
    context TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def _get_connection_manager(conn_mgr_or_path):
    from ..core.connection_manager import ConnectionManager

    if isinstance(conn_mgr_or_path, ConnectionManager):
        return conn_mgr_or_path
    return ConnectionManager(str(conn_mgr_or_path))


class YuGongDB:
    """
    愚公循环持久化层

    管理 7 张表的 CRUD 操作，支持内存数据库和文件数据库。

    连接管理:
    - 通过 ConnectionManager 管理数据库连接
    - 支持 db_path（向后兼容，含 :memory:）或传入已有 ConnectionManager
    """

    def __init__(
        self,
        db_path: str = ".quickagents/unified.db",
        conn_mgr: Optional["ConnectionManager"] = None,
    ):
        self._conn_mgr = conn_mgr or _get_connection_manager(db_path)
        self._is_memory = (not conn_mgr) and (db_path == ":memory:")
        self._memory_conn: Optional[sqlite3.Connection] = None
        self._create_tables()
        logger.debug("YuGongDB initialized: %s", db_path)

    def _create_tables(self) -> None:
        if self._is_memory:
            self._memory_conn = sqlite3.connect(":memory:")
            self._memory_conn.row_factory = sqlite3.Row
            self._memory_conn.executescript(_CREATE_TABLES_SQL)
            self._memory_conn.commit()
            return

        with self._conn_mgr.get_connection() as conn:
            conn.executescript(_CREATE_TABLES_SQL)

    def _execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        if self._is_memory:
            return self._memory_conn.execute(sql, params)
        with self._conn_mgr.get_connection() as conn:
            return conn.execute(sql, params)

    def close(self) -> None:
        if self._memory_conn:
            self._memory_conn.close()
            self._memory_conn = None
        if not self._is_memory and hasattr(self, "_conn_mgr"):
            self._conn_mgr.close_all()

    # ==================== Story CRUD ====================

    def save_story(self, story: UserStory) -> None:
        params = (
            story.id,
            story.title,
            story.description,
            json.dumps(story.acceptance_criteria, ensure_ascii=False),
            story.priority.value,
            story.status.value,
            json.dumps(story.dependencies),
            story.estimated_complexity,
            json.dumps(story.tags),
            story.category,
            1 if story.passes else 0,
            story.notes,
            json.dumps(story.files_changed),
            story.error_log,
            story.attempts,
            story.max_attempts,
            story.created_at.isoformat() if isinstance(story.created_at, datetime) else story.created_at,
            story.updated_at.isoformat() if isinstance(story.updated_at, datetime) else story.updated_at,
            story.started_at.isoformat() if story.started_at else None,
            story.completed_at.isoformat() if story.completed_at else None,
            json.dumps(story.token_usage) if story.token_usage else None,
        )

        if self._is_memory:
            self._memory_conn.execute(
                """INSERT OR REPLACE INTO yugong_stories
                (id, title, description, acceptance_criteria, priority, status,
                 dependencies, estimated_complexity, tags, category, passes,
                 notes, files_changed, error_log, attempts, max_attempts,
                 created_at, updated_at, started_at, completed_at, token_usage)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                params,
            )
            self._memory_conn.commit()
            return

        with self._conn_mgr.get_connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO yugong_stories
                (id, title, description, acceptance_criteria, priority, status,
                 dependencies, estimated_complexity, tags, category, passes,
                 notes, files_changed, error_log, attempts, max_attempts,
                 created_at, updated_at, started_at, completed_at, token_usage)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                params,
            )

    def get_story(self, story_id: str) -> Optional[UserStory]:
        if self._is_memory:
            row = self._memory_conn.execute("SELECT * FROM yugong_stories WHERE id = ?", (story_id,)).fetchone()
        else:
            with self._conn_mgr.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute("SELECT * FROM yugong_stories WHERE id = ?", (story_id,)).fetchone()

        if not row:
            return None
        return self._row_to_story(row)

    def get_all_stories(self) -> list[UserStory]:
        if self._is_memory:
            rows = self._memory_conn.execute("SELECT * FROM yugong_stories ORDER BY priority, id").fetchall()
        else:
            with self._conn_mgr.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute("SELECT * FROM yugong_stories ORDER BY priority, id").fetchall()
        return [self._row_to_story(r) for r in rows]

    def get_stories_by_status(self, status: StoryStatus) -> list[UserStory]:
        if self._is_memory:
            rows = self._memory_conn.execute(
                "SELECT * FROM yugong_stories WHERE status = ? ORDER BY priority",
                (status.value,),
            ).fetchall()
        else:
            with self._conn_mgr.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT * FROM yugong_stories WHERE status = ? ORDER BY priority",
                    (status.value,),
                ).fetchall()
        return [self._row_to_story(r) for r in rows]

    def delete_story(self, story_id: str) -> None:
        if self._is_memory:
            self._memory_conn.execute("DELETE FROM yugong_stories WHERE id = ?", (story_id,))
            self._memory_conn.commit()
            return

        with self._conn_mgr.get_connection() as conn:
            conn.execute("DELETE FROM yugong_stories WHERE id = ?", (story_id,))

    def count_stories(self) -> int:
        if self._is_memory:
            return self._memory_conn.execute("SELECT COUNT(*) FROM yugong_stories").fetchone()[0]

        with self._conn_mgr.get_connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM yugong_stories").fetchone()[0]

    def _row_to_story(self, row) -> UserStory:
        return UserStory(
            id=row["id"],
            title=row["title"],
            description=row["description"] or "",
            acceptance_criteria=json.loads(row["acceptance_criteria"]) if row["acceptance_criteria"] else [],
            priority=StoryPriority(row["priority"]),
            status=StoryStatus(row["status"]),
            passes=bool(row["passes"]),
            dependencies=json.loads(row["dependencies"]) if row["dependencies"] else [],
            estimated_complexity=row["estimated_complexity"] or "medium",
            tags=json.loads(row["tags"]) if row["tags"] else [],
            category=row["category"] or "",
            notes=row["notes"] or "",
            files_changed=json.loads(row["files_changed"]) if row["files_changed"] else [],
            error_log=row["error_log"] or "",
            attempts=row["attempts"],
            max_attempts=row["max_attempts"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.now(),
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            token_usage=json.loads(row["token_usage"]) if row["token_usage"] else {},
        )

    # ==================== Iteration 历史 ====================

    def save_iteration(self, result: LoopResult) -> None:
        params = (
            result.iteration,
            result.story_id,
            1 if result.success else 0,
            result.output,
            result.duration_ms,
            json.dumps(result.token_usage),
            json.dumps(result.files_changed),
            result.error,
            1 if result.exit_signal else 0,
            result.completion_indicators,
            result.timestamp.isoformat() if isinstance(result.timestamp, datetime) else result.timestamp,
        )

        if self._is_memory:
            self._memory_conn.execute(
                """INSERT INTO yugong_iterations
                (iteration, story_id, success, output, duration_ms, token_usage,
                 files_changed, error, exit_signal, completion_indicators, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                params,
            )
            self._memory_conn.commit()
            return

        with self._conn_mgr.get_connection() as conn:
            conn.execute(
                """INSERT INTO yugong_iterations
                (iteration, story_id, success, output, duration_ms, token_usage,
                 files_changed, error, exit_signal, completion_indicators, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                params,
            )

    def get_iterations(self, story_id: Optional[str] = None) -> list[LoopResult]:
        if story_id:
            sql = "SELECT * FROM yugong_iterations WHERE story_id = ? ORDER BY iteration"
            params = (story_id,)
        else:
            sql = "SELECT * FROM yugong_iterations ORDER BY iteration"
            params = ()

        if self._is_memory:
            rows = self._memory_conn.execute(sql, params).fetchall()
        else:
            with self._conn_mgr.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(sql, params).fetchall()
        return [self._row_to_iteration(r) for r in rows]

    def _row_to_iteration(self, row) -> LoopResult:
        return LoopResult(
            iteration=row["iteration"],
            story_id=row["story_id"],
            success=bool(row["success"]),
            output=row["output"] or "",
            duration_ms=row["duration_ms"] or 0,
            token_usage=json.loads(row["token_usage"]) if row["token_usage"] else {},
            files_changed=json.loads(row["files_changed"]) if row["files_changed"] else [],
            error=row["error"],
            exit_signal=bool(row["exit_signal"]),
            completion_indicators=row["completion_indicators"] or 0,
            timestamp=datetime.fromisoformat(row["timestamp"]) if row["timestamp"] else datetime.now(),
        )

    # ==================== 循环状态 ====================

    def save_state(self, state: LoopState) -> None:
        state_json = json.dumps(state.to_dict(), ensure_ascii=False)
        params = (state_json, datetime.now().isoformat())

        if self._is_memory:
            self._memory_conn.execute(
                """INSERT OR REPLACE INTO yugong_state (id, state_json, updated_at)
                VALUES (1, ?, ?)""",
                params,
            )
            self._memory_conn.commit()
            return

        with self._conn_mgr.get_connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO yugong_state (id, state_json, updated_at)
                VALUES (1, ?, ?)""",
                params,
            )

    def load_state(self) -> Optional[LoopState]:
        if self._is_memory:
            row = self._memory_conn.execute("SELECT state_json FROM yugong_state WHERE id = 1").fetchone()
        else:
            with self._conn_mgr.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute("SELECT state_json FROM yugong_state WHERE id = 1").fetchone()

        if not row:
            return None
        return LoopState.from_dict(json.loads(row["state_json"]))

    # ==================== 检查点 ====================

    def save_checkpoint(
        self,
        checkpoint_type: str,
        state: LoopState,
        story_id: Optional[str] = None,
    ) -> None:
        state_json = json.dumps(state.to_dict(), ensure_ascii=False)
        params = (checkpoint_type, state_json, story_id)

        if self._is_memory:
            self._memory_conn.execute(
                """INSERT INTO yugong_checkpoints (checkpoint_type, state_json, story_id)
                VALUES (?, ?, ?)""",
                params,
            )
            self._memory_conn.commit()
            return

        with self._conn_mgr.get_connection() as conn:
            conn.execute(
                """INSERT INTO yugong_checkpoints (checkpoint_type, state_json, story_id)
                VALUES (?, ?, ?)""",
                params,
            )

    def get_checkpoints(
        self,
        checkpoint_type: Optional[str] = None,
    ) -> list[dict]:
        if checkpoint_type:
            sql = "SELECT * FROM yugong_checkpoints WHERE checkpoint_type = ? ORDER BY created_at DESC"
            params = (checkpoint_type,)
        else:
            sql = "SELECT * FROM yugong_checkpoints ORDER BY created_at DESC"
            params = ()

        if self._is_memory:
            rows = self._memory_conn.execute(sql, params).fetchall()
        else:
            with self._conn_mgr.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(sql, params).fetchall()

        return [
            {
                "id": r["id"],
                "type": r["checkpoint_type"],
                "state": LoopState.from_dict(json.loads(r["state_json"])),
                "story_id": r["story_id"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    def get_latest_checkpoint(self) -> Optional[dict]:
        if self._is_memory:
            rows = self._memory_conn.execute("SELECT * FROM yugong_checkpoints ORDER BY id DESC LIMIT 1").fetchall()
        else:
            with self._conn_mgr.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute("SELECT * FROM yugong_checkpoints ORDER BY id DESC LIMIT 1").fetchall()

        if not rows:
            return None
        r = rows[0]
        return {
            "id": r["id"],
            "type": r["checkpoint_type"],
            "story_id": r["story_id"],
            "created_at": r["created_at"],
        }

    # ==================== 日志 ====================

    def add_log(
        self,
        level: str,
        log_type: str,
        message: str,
        context: Optional[dict] = None,
    ) -> None:
        params = (level, log_type, message, json.dumps(context) if context else None)

        if self._is_memory:
            self._memory_conn.execute(
                """INSERT INTO yugong_logs (log_level, log_type, message, context)
                VALUES (?, ?, ?, ?)""",
                params,
            )
            self._memory_conn.commit()
            return

        with self._conn_mgr.get_connection() as conn:
            conn.execute(
                """INSERT INTO yugong_logs (log_level, log_type, message, context)
                VALUES (?, ?, ?, ?)""",
                params,
            )

    def get_logs(
        self,
        level: Optional[str] = None,
        log_type: Optional[str] = None,
    ) -> list[dict]:
        sql = "SELECT * FROM yugong_logs"
        conditions = []
        params = []

        if level:
            conditions.append("log_level = ?")
            params.append(level)
        if log_type:
            conditions.append("log_type = ?")
            params.append(log_type)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY created_at"

        if self._is_memory:
            rows = self._memory_conn.execute(sql, tuple(params)).fetchall()
        else:
            with self._conn_mgr.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(sql, tuple(params)).fetchall()

        return [
            {
                "id": r["id"],
                "level": r["log_level"],
                "type": r["log_type"],
                "message": r["message"],
                "context": json.loads(r["context"]) if r["context"] else None,
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    # ==================== 进度日志 ====================

    def add_progress(self, story_id: str, content: str) -> None:
        if self._is_memory:
            self._memory_conn.execute(
                "INSERT INTO yugong_progress (story_id, content) VALUES (?, ?)",
                (story_id, content),
            )
            self._memory_conn.commit()
            return

        with self._conn_mgr.get_connection() as conn:
            conn.execute(
                "INSERT INTO yugong_progress (story_id, content) VALUES (?, ?)",
                (story_id, content),
            )

    def get_progress_entries(self, story_id: Optional[str] = None) -> list[dict]:
        if story_id:
            sql = "SELECT * FROM yugong_progress WHERE story_id = ? ORDER BY created_at"
            params = (story_id,)
        else:
            sql = "SELECT * FROM yugong_progress ORDER BY created_at"
            params = ()

        if self._is_memory:
            rows = self._memory_conn.execute(sql, params).fetchall()
        else:
            with self._conn_mgr.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(sql, params).fetchall()

        return [
            {
                "id": r["id"],
                "story_id": r["story_id"],
                "content": r["content"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    # ==================== 上下文 ====================

    def add_context(self, content: str) -> None:
        if self._is_memory:
            self._memory_conn.execute("INSERT INTO yugong_context (content) VALUES (?)", (content,))
            self._memory_conn.commit()
            return

        with self._conn_mgr.get_connection() as conn:
            conn.execute("INSERT INTO yugong_context (content) VALUES (?)", (content,))

    def get_pending_contexts(self) -> list[str]:
        if self._is_memory:
            rows = self._memory_conn.execute("SELECT content FROM yugong_context ORDER BY created_at").fetchall()
        else:
            with self._conn_mgr.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute("SELECT content FROM yugong_context ORDER BY created_at").fetchall()
        return [r["content"] for r in rows]

    def clear_contexts(self) -> None:
        if self._is_memory:
            self._memory_conn.execute("DELETE FROM yugong_context")
            self._memory_conn.commit()
            return

        with self._conn_mgr.get_connection() as conn:
            conn.execute("DELETE FROM yugong_context")

    # ==================== 统计 ====================

    def get_stats(self) -> dict:
        if self._is_memory:
            total_stories = self._memory_conn.execute("SELECT COUNT(*) FROM yugong_stories").fetchone()[0]
            total_iterations = self._memory_conn.execute("SELECT COUNT(*) FROM yugong_iterations").fetchone()[0]
            total_logs = self._memory_conn.execute("SELECT COUNT(*) FROM yugong_logs").fetchone()[0]
            total_checkpoints = self._memory_conn.execute("SELECT COUNT(*) FROM yugong_checkpoints").fetchone()[0]
            status_rows = self._memory_conn.execute(
                "SELECT status, COUNT(*) as cnt FROM yugong_stories GROUP BY status"
            ).fetchall()
            status_counts = {r["status"]: r["cnt"] for r in status_rows}
        else:
            with self._conn_mgr.get_connection() as conn:
                total_stories = conn.execute("SELECT COUNT(*) FROM yugong_stories").fetchone()[0]
                total_iterations = conn.execute("SELECT COUNT(*) FROM yugong_iterations").fetchone()[0]
                total_logs = conn.execute("SELECT COUNT(*) FROM yugong_logs").fetchone()[0]
                total_checkpoints = conn.execute("SELECT COUNT(*) FROM yugong_checkpoints").fetchone()[0]
                status_rows = conn.execute(
                    "SELECT status, COUNT(*) as cnt FROM yugong_stories GROUP BY status"
                ).fetchall()
                status_counts = {r[0]: r[1] for r in status_rows}

        return {
            "total_stories": total_stories,
            "total_iterations": total_iterations,
            "total_logs": total_logs,
            "total_checkpoints": total_checkpoints,
            "stories_by_status": status_counts,
        }
