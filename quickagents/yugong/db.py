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
"""

import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from .models import (
    UserStory,
    StoryStatus,
    StoryPriority,
    LoopResult,
    LoopState,
)

logger = logging.getLogger(__name__)

# SQL: 创建 7 张表
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


class YuGongDB:
    """
    愚公循环持久化层

    管理 7 张表的 CRUD 操作，支持内存数据库和文件数据库
    """

    def __init__(self, db_path: str = ".quickagents/unified.db"):
        self.db_path = db_path
        self._is_memory = db_path == ":memory:"
        self._conn: Optional[sqlite3.Connection] = None
        self._connect()
        self._create_tables()
        logger.debug("YuGongDB initialized: %s", db_path)

    def _connect(self) -> None:
        """建立数据库连接"""
        if self._is_memory:
            self._conn = sqlite3.connect(":memory:")
        else:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row

    def _create_tables(self) -> None:
        """创建所有表"""
        self._conn.executescript(_CREATE_TABLES_SQL)
        self._conn.commit()

    def _execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """执行 SQL"""
        return self._conn.execute(sql, params)

    def close(self) -> None:
        """关闭连接"""
        if self._conn:
            self._conn.close()
            self._conn = None

    # ==================== Story CRUD ====================

    def save_story(self, story: UserStory) -> None:
        """保存/更新 UserStory"""
        self._execute(
            """INSERT OR REPLACE INTO yugong_stories
            (id, title, description, acceptance_criteria, priority, status,
             dependencies, estimated_complexity, tags, category, passes,
             notes, files_changed, error_log, attempts, max_attempts,
             created_at, updated_at, started_at, completed_at, token_usage)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
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
            ),
        )
        self._conn.commit()

    def get_story(self, story_id: str) -> Optional[UserStory]:
        """获取单个 Story"""
        row = self._execute("SELECT * FROM yugong_stories WHERE id = ?", (story_id,)).fetchone()
        if not row:
            return None
        return self._row_to_story(row)

    def get_all_stories(self) -> list[UserStory]:
        """获取所有 Stories"""
        rows = self._execute("SELECT * FROM yugong_stories ORDER BY priority, id").fetchall()
        return [self._row_to_story(r) for r in rows]

    def get_stories_by_status(self, status: StoryStatus) -> list[UserStory]:
        """按状态筛选 Stories"""
        rows = self._execute(
            "SELECT * FROM yugong_stories WHERE status = ? ORDER BY priority",
            (status.value,),
        ).fetchall()
        return [self._row_to_story(r) for r in rows]

    def delete_story(self, story_id: str) -> None:
        """删除 Story"""
        self._execute("DELETE FROM yugong_stories WHERE id = ?", (story_id,))
        self._conn.commit()

    def count_stories(self) -> int:
        """统计 Story 数量"""
        row = self._execute("SELECT COUNT(*) FROM yugong_stories").fetchone()
        return row[0]

    def _row_to_story(self, row: sqlite3.Row) -> UserStory:
        """数据库行转 UserStory"""
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
        """保存迭代记录"""
        self._execute(
            """INSERT INTO yugong_iterations
            (iteration, story_id, success, output, duration_ms, token_usage,
             files_changed, error, exit_signal, completion_indicators, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
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
            ),
        )
        self._conn.commit()

    def get_iterations(self, story_id: Optional[str] = None) -> list[LoopResult]:
        """获取迭代记录"""
        if story_id:
            rows = self._execute(
                "SELECT * FROM yugong_iterations WHERE story_id = ? ORDER BY iteration",
                (story_id,),
            ).fetchall()
        else:
            rows = self._execute("SELECT * FROM yugong_iterations ORDER BY iteration").fetchall()
        return [self._row_to_iteration(r) for r in rows]

    def _row_to_iteration(self, row: sqlite3.Row) -> LoopResult:
        """数据库行转 LoopResult"""
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
        """保存循环状态（覆盖）"""
        state_json = json.dumps(state.to_dict(), ensure_ascii=False)
        self._execute(
            """INSERT OR REPLACE INTO yugong_state (id, state_json, updated_at)
            VALUES (1, ?, ?)""",
            (state_json, datetime.now().isoformat()),
        )
        self._conn.commit()

    def load_state(self) -> Optional[LoopState]:
        """加载循环状态"""
        row = self._execute("SELECT state_json FROM yugong_state WHERE id = 1").fetchone()
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
        """保存检查点"""
        state_json = json.dumps(state.to_dict(), ensure_ascii=False)
        self._execute(
            """INSERT INTO yugong_checkpoints (checkpoint_type, state_json, story_id)
            VALUES (?, ?, ?)""",
            (checkpoint_type, state_json, story_id),
        )
        self._conn.commit()

    def get_checkpoints(
        self,
        checkpoint_type: Optional[str] = None,
    ) -> list[dict]:
        """获取检查点列表"""
        if checkpoint_type:
            rows = self._execute(
                "SELECT * FROM yugong_checkpoints WHERE checkpoint_type = ? ORDER BY created_at DESC",
                (checkpoint_type,),
            ).fetchall()
        else:
            rows = self._execute("SELECT * FROM yugong_checkpoints ORDER BY created_at DESC").fetchall()
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
        """获取最新检查点"""
        rows = self._execute("SELECT * FROM yugong_checkpoints ORDER BY id DESC LIMIT 1").fetchall()
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
        """添加日志"""
        self._execute(
            """INSERT INTO yugong_logs (log_level, log_type, message, context)
            VALUES (?, ?, ?, ?)""",
            (level, log_type, message, json.dumps(context) if context else None),
        )
        self._conn.commit()

    def get_logs(
        self,
        level: Optional[str] = None,
        log_type: Optional[str] = None,
    ) -> list[dict]:
        """获取日志"""
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

        rows = self._execute(sql, tuple(params)).fetchall()
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
        """添加进度记录"""
        self._execute(
            "INSERT INTO yugong_progress (story_id, content) VALUES (?, ?)",
            (story_id, content),
        )
        self._conn.commit()

    def get_progress_entries(self, story_id: Optional[str] = None) -> list[dict]:
        """获取进度记录"""
        if story_id:
            rows = self._execute(
                "SELECT * FROM yugong_progress WHERE story_id = ? ORDER BY created_at",
                (story_id,),
            ).fetchall()
        else:
            rows = self._execute("SELECT * FROM yugong_progress ORDER BY created_at").fetchall()
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
        """添加待注入上下文"""
        self._execute("INSERT INTO yugong_context (content) VALUES (?)", (content,))
        self._conn.commit()

    def get_pending_contexts(self) -> list[str]:
        """获取待注入上下文"""
        rows = self._execute("SELECT content FROM yugong_context ORDER BY created_at").fetchall()
        return [r["content"] for r in rows]

    def clear_contexts(self) -> None:
        """清空已使用上下文"""
        self._execute("DELETE FROM yugong_context")
        self._conn.commit()

    # ==================== 统计 ====================

    def get_stats(self) -> dict:
        """获取统计信息"""
        total_stories = self._execute("SELECT COUNT(*) FROM yugong_stories").fetchone()[0]
        total_iterations = self._execute("SELECT COUNT(*) FROM yugong_iterations").fetchone()[0]
        total_logs = self._execute("SELECT COUNT(*) FROM yugong_logs").fetchone()[0]
        total_checkpoints = self._execute("SELECT COUNT(*) FROM yugong_checkpoints").fetchone()[0]

        # 按状态统计
        status_rows = self._execute("SELECT status, COUNT(*) as cnt FROM yugong_stories GROUP BY status").fetchall()
        status_counts = {r["status"]: r["cnt"] for r in status_rows}

        return {
            "total_stories": total_stories,
            "total_iterations": total_iterations,
            "total_logs": total_logs,
            "total_checkpoints": total_checkpoints,
            "stories_by_status": status_counts,
        }
