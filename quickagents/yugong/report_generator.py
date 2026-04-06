"""
ReportGenerator - 循环结果报告生成器

支持双格式输出 (D3 决策):
- Markdown: 人类可读报告
- JSON: 机器可解析的结构化数据

用法:
    from quickagents.yugong.report_generator import ReportGenerator
    from quickagents.yugong.db import YuGongDB
    from quickagents.yugong.autonomous_loop import LoopOutcome

    gen = ReportGenerator(db)
    md = gen.generate_markdown(outcome)
    json = gen.generate_json(outcome)
    gen.save(outcome, output_dir="reports/")
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from .db import YuGongDB
from .autonomous_loop import LoopOutcome
from .models import LoopResult, LoopState, UserStory

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    愚公循环结果报告生成器

    支持输出格式:
    - Markdown: 人类可读的进度报告
    - JSON: 机器可解析的结构化数据
    """

    def __init__(self, db: YuGongDB):
        self.db = db

    def generate_markdown(self, outcome: LoopOutcome) -> str:
        """
        生成 Markdown 格式报告

        Args:
            outcome: 循环结果

        Returns:
            Markdown 字符串
        """
        lines = []
        lines.append("# 愚公循环执行报告")
        lines.append("")
        lines.append(f"> 生成时间: {datetime.now().isoformat()}")
        lines.append("")

        # 概要
        lines.append("## 概要")
        lines.append("")
        status_icon = "✅" if outcome.success else "⚠️"
        lines.append(f"| 指标 | 值 |")
        lines.append(f"|------|-----|")
        lines.append(f"| 状态 | {status_icon} {'成功' if outcome.success else '未完成'} |")
        lines.append(f"| 结束原因 | {outcome.reason} |")
        lines.append(f"| 总迭代 | {outcome.total_iterations} |")
        lines.append(f"| Stories | {outcome.completed_stories}/{outcome.total_stories} |")
        lines.append(f"| 耗时 | {outcome.duration_seconds:.1f}s |")
        lines.append("")

        # Story 详情
        stories = self.db.get_all_stories()
        if stories:
            lines.append("## Story 详情")
            lines.append("")
            lines.append("| ID | 标题 | 状态 | 优先级 | 尝试 |")
            lines.append("|----|------|------|--------|------|")
            for s in stories:
                status_map = {
                    "pending": "⏳",
                    "running": "🔄",
                    "passed": "✅",
                    "failed": "❌",
                    "blocked": "🚫",
                    "skipped": "⏭️",
                    "cancelled": "🚫",
                }
                icon = status_map.get(s.status.value, "?")
                lines.append(f"| {s.id} | {s.title} | {icon} {s.status.value} | P{s.priority.value} | {s.attempts} |")
            lines.append("")

        # 迭代历史
        iterations = self.db.get_iterations()
        if iterations:
            lines.append("## 迭代历史")
            lines.append("")
            for it in iterations:
                result_icon = "✅" if it.success else "❌"
                lines.append(f"### 迭代 {it.iteration} ({result_icon})")
                lines.append(f"- Story: {it.story_id}")
                lines.append(f"- 耗时: {it.duration_ms}ms")
                if it.files_changed:
                    lines.append(f"- 文件变更: {', '.join(it.files_changed)}")
                if it.error:
                    lines.append(f"- 错误: {it.error}")
                if it.output:
                    # 截断过长的输出
                    output_preview = it.output[:500]
                    if len(it.output) > 500:
                        output_preview += "..."
                    lines.append(f"- 输出摘要: {output_preview}")
                lines.append("")

        # Token 消耗
        total_tokens = sum(it.token_usage.get("total_tokens", it.token_usage.get("total", 0)) for it in iterations)
        if total_tokens > 0:
            lines.append("## Token 消耗")
            lines.append("")
            lines.append(f"| 指标 | 值 |")
            lines.append(f"|------|-----|")
            lines.append(f"| 总 Token | {total_tokens:,} |")
            prompt_tokens = sum(it.token_usage.get("prompt_tokens", 0) for it in iterations)
            completion_tokens = sum(it.token_usage.get("completion_tokens", 0) for it in iterations)
            lines.append(f"| Prompt Tokens | {prompt_tokens:,} |")
            lines.append(f"| Completion Tokens | {completion_tokens:,} |")
            lines.append("")

        return "\n".join(lines)

    def generate_json(self, outcome: LoopOutcome) -> dict:
        """
        生成 JSON 格式报告 (dict)

        Args:
            outcome: 循环结果

        Returns:
            可 JSON 序列化的 dict
        """
        stories = self.db.get_all_stories()
        iterations = self.db.get_iterations()
        logs = self.db.get_logs()
        stats = self.db.get_stats()

        # 计算总 token
        total_tokens = sum(it.token_usage.get("total_tokens", it.token_usage.get("total", 0)) for it in iterations)

        return {
            "report_time": datetime.now().isoformat(),
            "outcome": {
                "success": outcome.success,
                "reason": outcome.reason,
                "total_iterations": outcome.total_iterations,
                "total_stories": outcome.total_stories,
                "completed_stories": outcome.completed_stories,
                "duration_seconds": round(outcome.duration_seconds, 2),
            },
            "stories": [
                {
                    "id": s.id,
                    "title": s.title,
                    "status": s.status.value,
                    "priority": s.priority.value,
                    "attempts": s.attempts,
                    "files_changed": s.files_changed,
                    "error_log": s.error_log,
                }
                for s in stories
            ],
            "iterations": [
                {
                    "iteration": it.iteration,
                    "story_id": it.story_id,
                    "success": it.success,
                    "duration_ms": it.duration_ms,
                    "files_changed": it.files_changed,
                    "error": it.error,
                    "token_usage": it.token_usage,
                }
                for it in iterations
            ],
            "token_summary": {
                "total": total_tokens,
            },
            "db_stats": stats,
        }

    def save(
        self,
        outcome: LoopOutcome,
        output_dir: str = ".quickagents/reports",
        formats: Optional[list[str]] = None,
    ) -> dict[str, Path]:
        """
        保存报告到文件

        Args:
            outcome: 循环结果
            output_dir: 输出目录
            formats: 输出格式列表，默认 ["markdown", "json"]

        Returns:
            保存的文件路径 dict
        """
        if formats is None:
            formats = ["markdown", "json"]

        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        saved = {}

        if "markdown" in formats:
            md_path = out / f"yugong_report_{timestamp}.md"
            md_path.write_text(
                self.generate_markdown(outcome),
                encoding="utf-8",
            )
            saved["markdown"] = md_path
            logger.info("Markdown 报告已保存: %s", md_path)

        if "json" in formats:
            json_path = out / f"yugong_report_{timestamp}.json"
            json_path.write_text(
                json.dumps(self.generate_json(outcome), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            saved["json"] = json_path
            logger.info("JSON 报告已保存: %s", json_path)

        return saved
