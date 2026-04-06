"""
ReportGenerator 测试

验证双格式输出 (Markdown + JSON)
"""

import json
import pytest
from pathlib import Path
from datetime import datetime

from quickagents.yugong.db import YuGongDB
from quickagents.yugong.models import (
    UserStory,
    LoopResult,
    LoopState,
    ParsedRequirement,
    StoryPriority,
    StoryStatus,
)
from quickagents.yugong.autonomous_loop import LoopOutcome
from quickagents.yugong.report_generator import ReportGenerator


def _make_outcome(
    success: bool = True,
    iterations: int = 3,
    total: int = 5,
    completed: int = 4,
) -> LoopOutcome:
    """创建测试用 LoopOutcome"""
    state = LoopState(
        status="completed" if success else "failed",
        current_iteration=iterations,
        total_stories=total,
        completed_stories=completed,
    )
    return LoopOutcome(
        success=success,
        reason="所有 Story 完成" if success else "部分失败",
        total_iterations=iterations,
        total_stories=total,
        completed_stories=completed,
        duration_seconds=42.5,
        state=state,
    )


class TestMarkdownReport:
    """Markdown 格式报告"""

    def test_basic_report(self):
        db = YuGongDB(":memory:")
        gen = ReportGenerator(db)
        outcome = _make_outcome()

        md = gen.generate_markdown(outcome)

        assert "# 愚公循环执行报告" in md
        assert "## 概要" in md
        assert "✅" in md
        assert "42.5s" in md
        assert "3" in md
        assert "4/5" in md

    def test_failed_report(self):
        db = YuGongDB(":memory:")
        gen = ReportGenerator(db)
        outcome = _make_outcome(success=False)

        md = gen.generate_markdown(outcome)

        assert "⚠️" in md
        assert "部分失败" in md

    def test_report_with_stories(self):
        db = YuGongDB(":memory:")

        # 添加 Stories
        db.save_story(UserStory(id="US-001", title="Auth", description="Auth module"))
        db.save_story(UserStory(id="US-002", title="Dashboard", description="User dashboard"))

        gen = ReportGenerator(db)
        outcome = _make_outcome(total=2, completed=2)

        md = gen.generate_markdown(outcome)
        assert "## Story 详情" in md
        assert "Auth" in md
        assert "Dashboard" in md

    def test_report_with_iterations(self):
        db = YuGongDB(":memory:")

        # 添加迭代记录
        db.save_iteration(
            LoopResult(
                iteration=1,
                story_id="US-001",
                success=True,
                output="Done",
                duration_ms=5000,
                token_usage={"total": 100},
            )
        )
        db.save_iteration(
            LoopResult(
                iteration=2,
                story_id="US-002",
                success=True,
                output="Done",
                duration_ms=3000,
                token_usage={"total": 80},
            )
        )

        gen = ReportGenerator(db)
        outcome = _make_outcome()

        md = gen.generate_markdown(outcome)
        assert "## 迭代历史" in md
        assert "5000ms" in md


class TestJSONReport:
    """JSON 格式报告"""

    def test_basic_json(self):
        db = YuGongDB(":memory:")
        gen = ReportGenerator(db)
        outcome = _make_outcome()

        data = gen.generate_json(outcome)

        assert data["outcome"]["success"] is True
        assert data["outcome"]["total_iterations"] == 3
        assert data["outcome"]["total_stories"] == 5
        assert data["outcome"]["completed_stories"] == 4
        assert data["outcome"]["duration_seconds"] == 42.5
        assert "report_time" in data
        assert "stories" in data
        assert "iterations" in data
        assert "db_stats" in data

    def test_json_with_stories(self):
        db = YuGongDB(":memory:")

        db.save_story(UserStory(id="US-001", title="Auth", description="Auth module"))
        db.save_story(UserStory(id="US-002", title="Dashboard", description="User dashboard"))

        gen = ReportGenerator(db)
        outcome = _make_outcome(total=2, completed=2)

        data = gen.generate_json(outcome)

        assert len(data["stories"]) == 2
        assert data["stories"][0]["id"] == "US-001"

    def test_json_serializable(self):
        db = YuGongDB(":memory:")
        gen = ReportGenerator(db)
        outcome = _make_outcome()

        data = gen.generate_json(outcome)

        # 确保可以序列化
        json_str = json.dumps(data, ensure_ascii=False)
        assert isinstance(json_str, str)

        # 反序列化验证
        parsed = json.loads(json_str)
        assert parsed["outcome"]["success"] is True


class TestSaveReport:
    """保存报告到文件"""

    def test_save_markdown_only(self, tmp_path):
        db = YuGongDB(":memory:")
        gen = ReportGenerator(db)
        outcome = _make_outcome()

        saved = gen.save(outcome, output_dir=str(tmp_path), formats=["markdown"])

        assert "markdown" in saved
        assert saved["markdown"].exists()
        content = saved["markdown"].read_text(encoding="utf-8")
        assert "# 愚公循环执行报告" in content

    def test_save_json_only(self, tmp_path):
        db = YuGongDB(":memory:")
        gen = ReportGenerator(db)
        outcome = _make_outcome()

        saved = gen.save(outcome, output_dir=str(tmp_path), formats=["json"])

        assert "json" in saved
        data = json.loads(saved["json"].read_text(encoding="utf-8"))
        assert data["outcome"]["success"] is True

    def test_save_both_formats(self, tmp_path):
        db = YuGongDB(":memory:")
        gen = ReportGenerator(db)
        outcome = _make_outcome()

        saved = gen.save(outcome, output_dir=str(tmp_path), formats=["markdown", "json"])

        assert len(saved) == 2
        assert "markdown" in saved
        assert "json" in saved

    def test_save_default_formats(self, tmp_path):
        db = YuGongDB(":memory:")
        gen = ReportGenerator(db)
        outcome = _make_outcome()

        saved = gen.save(outcome, output_dir=str(tmp_path))

        # 默认两种格式
        assert len(saved) == 2

    def test_save_creates_directory(self, tmp_path):
        db = YuGongDB(":memory:")
        gen = ReportGenerator(db)
        outcome = _make_outcome()

        nested_dir = str(tmp_path / "reports" / "nested")
        saved = gen.save(outcome, output_dir=nested_dir, formats=["markdown"])

        assert saved["markdown"].exists()
