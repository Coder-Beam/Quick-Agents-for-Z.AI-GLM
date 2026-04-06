"""
愚公循环进度日志

Append-only 经验记录:
- 记录每次迭代的关键信息
- 支持经验提取和学习
- 支持按 Story / 时间查询
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class LogEntry:
    """日志条目"""

    story_id: str
    iteration: int
    log_type: str  # decision, learning, error, quality, progress
    message: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return asdict(self)


class ProgressLogger:
    """
    进度日志

    Append-only 设计, 所有记录不可删除
    """

    def __init__(self):
        self._entries: list[LogEntry] = []

    def log(self, story_id: str, iteration: int, log_type: str, message: str) -> None:
        """记录一条日志"""
        self._entries.append(
            LogEntry(
                story_id=story_id,
                iteration=iteration,
                log_type=log_type,
                message=message,
            )
        )

    def log_decision(self, story_id: str, iteration: int, message: str) -> None:
        """记录决策"""
        self.log(story_id, iteration, "decision", message)

    def log_learning(self, story_id: str, iteration: int, message: str) -> None:
        """记录经验"""
        self.log(story_id, iteration, "learning", message)

    def log_error(self, story_id: str, iteration: int, message: str) -> None:
        """记录错误"""
        self.log(story_id, iteration, "error", message)

    def log_quality(self, story_id: str, iteration: int, message: str) -> None:
        """记录质量"""
        self.log(story_id, iteration, "quality", message)

    def log_progress(self, story_id: str, iteration: int, message: str) -> None:
        """记录进度"""
        self.log(story_id, iteration, "progress", message)

    # === 查询 ===

    def get_all(self) -> list[LogEntry]:
        """获取所有日志"""
        return list(self._entries)

    def get_by_story(self, story_id: str) -> list[LogEntry]:
        """按 Story 查询"""
        return [e for e in self._entries if e.story_id == story_id]

    def get_by_type(self, log_type: str) -> list[LogEntry]:
        """按类型查询"""
        return [e for e in self._entries if e.log_type == log_type]

    def get_recent(self, limit: int = 10) -> list[LogEntry]:
        """获取最近 N 条日志"""
        return list(self._entries[-limit:])

    def get_learnings(self, limit: int = 10) -> list[str]:
        """获取最近的经验"""
        entries = self.get_by_type("learning")
        entries = entries[-limit:]
        return [e.message for e in entries]

    def get_errors(self, story_id: Optional[str] = None) -> list[LogEntry]:
        """获取错误记录"""
        errors = self.get_by_type("error")
        if story_id:
            errors = [e for e in errors if e.story_id == story_id]
        return errors

    @property
    def count(self) -> int:
        """日志条数"""
        return len(self._entries)

    def clear(self) -> None:
        """清空日志 (仅用于测试)"""
        self._entries.clear()

    def to_list(self) -> list[dict]:
        """序列化"""
        return [e.to_dict() for e in self._entries]

    def from_list(self, data: list[dict]) -> None:
        """反序列化"""
        self._entries.clear()
        for item in data:
            self._entries.append(LogEntry(**item))
