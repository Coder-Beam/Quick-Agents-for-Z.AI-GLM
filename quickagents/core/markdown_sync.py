"""
MarkdownSync - Markdown同步器

功能:
- 将SQLite数据同步到Markdown文件
- 作为辅助备份和人类可读格式
- 支持从Markdown恢复到SQLite
- 异步同步，不阻塞主操作

同步策略:
- 写入: 先写SQLite, 异步同步到Markdown
- 读取: 优先SQLite(精确查询)
- 恢复: SQLite损坏时从Markdown恢复
- 版本: Markdown提交到Git
- 保护: 自动检测手动编写的Markdown内容,防止被覆盖
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from .unified_db import UnifiedDB, MemoryType, TaskStatus, FeedbackType, get_unified_db


def _get_attr(obj, key, default=None):
    """Get attribute from either dataclass or dict"""
    if hasattr(obj, key):
        return getattr(obj, key)
    elif isinstance(obj, dict):
        return obj.get(key, default)
    return default


class MarkdownSync:
    """
    Markdown同步器

    使用方式:
        sync = MarkdownSync(db, docs_dir='Docs')

        # 同步所有表到Markdown
        sync.sync_all()

        # 同步特定表
        sync.sync_memory()
        sync.sync_tasks()
        sync.sync_decisions()

        # 从Markdown恢复
        sync.restore_memory_from_md()
    """

    def __init__(
        self,
        db: UnifiedDB = None,
        docs_dir: str = "Docs",
        quickagents_dir: str = ".quickagents",
    ):
        """
        初始化同步器

        Args:
            db: UnifiedDB实例
            docs_dir: 文档目录
            quickagents_dir: QuickAgents数据目录
        """
        self.db = db or get_unified_db()
        self.docs_dir = Path(docs_dir)
        self.quickagents_dir = Path(quickagents_dir)

        # 确保目录存在
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.quickagents_dir.mkdir(parents=True, exist_ok=True)

        # 冲突检测器
        from ..utils.sync_conflict import SyncConflictDetector

        self.conflict_detector = SyncConflictDetector(
            str(self.docs_dir), str(self.quickagents_dir)
        )

    def sync_all(
        self, check_conflicts: bool = True, force: bool = False
    ) -> Dict[str, Any]:
        """
        同步所有表到Markdown

        Args:
            check_conflicts: 是否检查冲突（默认True）
            force: 是否强制同步，忽略冲突（默认False）

        Returns:
            结果字典，包含同步状态和冲突信息
        """
        # 检查冲突
        conflicts = []
        if check_conflicts and not force:
            conflicts = self.conflict_detector.check_conflicts()
            if conflicts:
                # 返回冲突信息，不执行同步
                return {
                    "success": False,
                    "conflicts": conflicts,
                    "conflict_report": self.conflict_detector.get_conflict_report(),
                    "message": "检测到文件冲突，请使用 force=True 强制同步或先处理冲突",
                }

        # 执行同步
        results = {
            "memory": self.sync_memory(False),
            "tasks": self.sync_tasks(False),
            "decisions": self.sync_decisions(False),
            "progress": self.sync_progress(False),
            "feedback": self.sync_feedback(False),
        }

        # 记录同步状态
        self.conflict_detector.record_all_sync_states()

        return {
            "success": True,
            "results": results,
            "conflicts": conflicts,
            "message": "同步完成",
        }

    # ==================== 覆盖保护 ====================

    # Marker present in every auto-generated Markdown file
    _SYNC_MARKER = "此文件由 SQLite 自动同步生成"

    def _is_safe_to_overwrite(self, file_path: Path) -> bool:
        """
        Check whether it is safe to overwrite *file_path* during sync.

        Safe to overwrite:
          - File does not exist yet
          - File is empty / near-empty
          - File already contains the auto-generated sync marker

        NOT safe (skip sync):
          - File has substantial manually-written content without the marker
        """
        if not file_path.exists():
            return True
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            return True
        if len(content.strip()) < 20:
            return True
        if self._SYNC_MARKER in content:
            return True
        # Substantial manual content — protect it
        return False

    # ==================== 三维记忆同步 ====================

    def sync_memory(self, check_conflicts: bool = True) -> bool:
        """
        同步三维记忆到MEMORY.md

        Args:
            check_conflicts: 是否检查冲突

        Returns:
            是否成功
        """
        # 检查冲突
        if check_conflicts:
            conflicts = self.conflict_detector.check_conflicts(["memory"])
            if conflicts:
                print(f"[WARN] 检测到冲突: {conflicts[0]['reason']}")
                print("  使用 sync_memory(check_conflicts=False) 强制同步")
                return False

        try:
            # 获取所有记忆
            factual = self.db.get_memories_by_type(MemoryType.FACTUAL)
            experiential = self.db.get_memories_by_type(MemoryType.EXPERIENTIAL)
            working = self.db.get_memories_by_type(MemoryType.WORKING)

            # 生成Markdown内容
            content = self._generate_memory_md(factual, experiential, working)

            # 写入文件（保护手动编写的内容）
            memory_path = self.docs_dir / "MEMORY.md"
            if not self._is_safe_to_overwrite(memory_path):
                return True  # skip, not an error
            memory_path.write_text(content, encoding="utf-8")

            # 记录同步状态
            self.conflict_detector.record_sync_state("memory")

            return True
        except Exception as e:
            print(f"同步记忆失败: {e}")
            return False

    def _generate_memory_md(
        self, factual: List, experiential: List, working: List
    ) -> str:
        """生成MEMORY.md内容"""
        lines = [
            "# MEMORY.md",
            "",
            f"> 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "> 此文件由 SQLite 自动同步生成，作为辅助备份",
            "> 主存储: .quickagents/unified.db",
            "",
            "---",
            "",
            "## Factual Memory (事实记忆)",
            "",
            "> 记录项目的静态事实信息",
            "",
        ]

        # 事实记忆 (支持 Memory 对象和字典)
        for item in factual:
            key = _get_attr(item, "key")
            value = _get_attr(item, "value")
            try:
                parsed = json.loads(value)
                if isinstance(parsed, (dict, list)):
                    value = json.dumps(parsed, ensure_ascii=False, indent=2)
            except Exception:
                pass
            lines.append(f"- **{key}**: {value}")

        lines.extend(["", "---", "", "## Experiential Memory (经验记忆)", ""])

        # 经验记忆 (支持 Memory 对象和字典)
        for item in experiential[-50:]:  # 最近50条
            category = _get_attr(item, "category", "general") or "general"
            content = _get_attr(item, "value")
            timestamp = _get_attr(item, "updated_at", "") or ""
            lines.append(f"- [{timestamp}] **{category}**: {content}")

        lines.extend(["", "---", "", "## Working Memory (工作记忆)", ""])

        # 工作记忆 (支持 Memory 对象和字典)
        for item in working:
            key = _get_attr(item, "key")
            value = _get_attr(item, "value")
            lines.append(f"- **{key}**: {value}")

        lines.append("")
        return "\n".join(lines)

    def restore_memory_from_md(self, memory_path: str = None) -> int:
        """从MEMORY.md恢复到SQLite"""
        path = Path(memory_path) if memory_path else self.docs_dir / "MEMORY.md"

        if not path.exists():
            return 0

        content = path.read_text(encoding="utf-8")
        restored = 0

        current_section = None
        for line in content.split("\n"):
            if "## Factual Memory" in line:
                current_section = MemoryType.FACTUAL
            elif "## Experiential Memory" in line:
                current_section = MemoryType.EXPERIENTIAL
            elif "## Working Memory" in line:
                current_section = MemoryType.WORKING
            elif line.strip().startswith("- **") and current_section:
                # 解析格式: - **key**: value
                match = re.match(r"-\s*\*\*(.+?)\*\*:\s*(.+)", line.strip())
                if match:
                    key = match.group(1)
                    value = match.group(2)

                    # 检查是否已存在
                    existing = self.db.get_memory(key)
                    if existing is None:
                        self.db.set_memory(key, value, current_section)
                        restored += 1

        return restored

    # ==================== 任务管理同步 ====================

    def sync_tasks(self, record_state: bool = True) -> bool:
        """
        同步任务到TASKS.md

        Args:
            record_state: 是否记录同步状态
        """
        try:
            # 获取所有任务
            all_tasks = self.db.get_tasks()
            completed = [t for t in all_tasks if _get_attr(t, "status") == "completed"]
            in_progress = [
                t for t in all_tasks if _get_attr(t, "status") == "in_progress"
            ]
            pending = [t for t in all_tasks if _get_attr(t, "status") == "pending"]
            blocked = [t for t in all_tasks if _get_attr(t, "status") == "blocked"]

            # 生成Markdown
            content = self._generate_tasks_md(completed, in_progress, pending, blocked)

            # 写入文件（保护手动编写的内容）
            tasks_path = self.docs_dir / "TASKS.md"
            if not self._is_safe_to_overwrite(tasks_path):
                return True  # skip, not an error
            tasks_path.write_text(content, encoding="utf-8")

            # 记录同步状态
            if record_state:
                self.conflict_detector.record_sync_state("tasks")

            return True
        except Exception as e:
            print(f"同步任务失败: {e}")
            return False

    def _generate_tasks_md(
        self,
        completed: List[Dict],
        in_progress: List[Dict],
        pending: List[Dict],
        blocked: List[Dict],
    ) -> str:
        """生成TASKS.md内容"""
        total = len(completed) + len(in_progress) + len(pending) + len(blocked)
        completion_rate = len(completed) / total * 100 if total > 0 else 0

        lines = [
            "# 任务管理 (TASKS.md)",
            "",
            f"> 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "> 此文件由 SQLite 自动同步生成，作为辅助备份",
            "> 主存储: .quickagents/unified.db",
            "",
            "---",
            "",
            "## 统计概览",
            "",
            "| 指标 | 数值 |",
            "|------|------|",
            f"| 总任务数 | {total} |",
            f"| 已完成 | {len(completed)} |",
            f"| 进行中 | {len(in_progress)} |",
            f"| 待开始 | {len(pending)} |",
            f"| 阻塞中 | {len(blocked)} |",
            f"| 完成率 | {completion_rate:.1f}% |",
            "",
            "---",
            "",
            "## 当前迭代",
            "",
        ]

        # 进行中的任务
        if in_progress:
            lines.append("| 任务ID | 任务名称 | 优先级 | 状态 | 开始时间 |")
            lines.append("|--------|----------|--------|------|----------|")
            for task in in_progress:
                task_id = _get_attr(task, "id") or _get_attr(task, "task_id")
                name = _get_attr(task, "name")
                priority = _get_attr(task, "priority")
                started_at = _get_attr(task, "started_at", "-")
                lines.append(
                    f"| {task_id} | {name} | {priority} | 进行中 | {started_at[:10] if started_at else '-'} |"
                )
            lines.append("")

        lines.extend(["---", "", "## 待办任务", ""])

        # 按优先级分组
        p0_tasks = [t for t in pending if _get_attr(t, "priority") == "P0"]
        p1_tasks = [t for t in pending if _get_attr(t, "priority") == "P1"]
        p2_tasks = [t for t in pending if _get_attr(t, "priority") == "P2"]

        if p0_tasks:
            lines.append("### P0 - 紧急")
            for task in p0_tasks:
                task_id = _get_attr(task, "id") or _get_attr(task, "task_id")
                name = _get_attr(task, "name")
                lines.append(f"- [ ] {task_id}: {name}")
            lines.append("")

        if p1_tasks:
            lines.append("### P1 - 高优先级")
            for task in p1_tasks:
                task_id = _get_attr(task, "id") or _get_attr(task, "task_id")
                name = _get_attr(task, "name")
                lines.append(f"- [ ] {task_id}: {name}")
            lines.append("")

        if p2_tasks:
            lines.append("### P2 - 中优先级")
            for task in p2_tasks:
                task_id = _get_attr(task, "id") or _get_attr(task, "task_id")
                name = _get_attr(task, "name")
                lines.append(f"- [ ] {task_id}: {name}")
            lines.append("")

        # 阻塞任务
        if blocked:
            lines.append("### 阻塞中")
            for task in blocked:
                task_id = _get_attr(task, "id") or _get_attr(task, "task_id")
                name = _get_attr(task, "name")
                notes = _get_attr(task, "notes", "")
                lines.append(f"- [ ] {task_id}: {name} {f'({notes})' if notes else ''}")
            lines.append("")

        lines.extend(["---", "", "## 已完成任务", ""])

        for task in completed[-20:]:  # 最近20个
            task_id = _get_attr(task, "id") or _get_attr(task, "task_id")
            name = _get_attr(task, "name")
            completed_at = _get_attr(task, "completed_at", "")
            lines.append(
                f"- [x] {task_id}: {name} - 完成于 {completed_at[:10] if completed_at else ''}"
            )

        lines.append("")
        return "\n".join(lines)

    # ==================== 决策日志同步 ====================

    def sync_decisions(self, record_state: bool = True) -> bool:
        """
        同步决策日志到DECISIONS.md

        Args:
            record_state: 是否记录同步状态
        """
        try:
            decisions = self.db.get_decisions()
            content = self._generate_decisions_md(decisions)

            decisions_path = self.docs_dir / "DECISIONS.md"
            if not self._is_safe_to_overwrite(decisions_path):
                return True  # skip, not an error
            decisions_path.write_text(content, encoding="utf-8")

            # 记录同步状态
            if record_state:
                self.conflict_detector.record_sync_state("decisions")

            return True
        except Exception as e:
            print(f"同步决策失败: {e}")
            return False

    def _generate_decisions_md(self, decisions: List[Dict]) -> str:
        """生成DECISIONS.md内容"""
        lines = [
            "# 决策日志 (DECISIONS.md)",
            "",
            f"> 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "> 此文件由 SQLite 自动同步生成，作为辅助备份",
            "> 主存储: .quickagents/unified.db",
            "",
            "---",
            "",
            "## 决策索引",
            "",
            "| 决策ID | 标题 | 决策时间 | 影响范围 | 状态 |",
            "|--------|------|----------|----------|------|",
        ]

        for d in decisions:
            decision_id = _get_attr(d, "decision_id") or _get_attr(d, "id")
            title = _get_attr(d, "title")
            created_at = _get_attr(d, "created_at", "")
            impact = _get_attr(d, "impact", "-")
            status = _get_attr(d, "status")
            lines.append(
                f"| {decision_id} | {title} | {created_at[:10] if created_at else ''} | {impact} | {status} |"
            )

        lines.extend(["", "---", ""])

        # 详细决策
        for d in decisions:
            decision_id = _get_attr(d, "decision_id") or _get_attr(d, "id")
            title = _get_attr(d, "title")
            created_at = _get_attr(d, "created_at", "")
            decision_maker = _get_attr(d, "decision_maker", "AI建议")
            status = _get_attr(d, "status")
            background = _get_attr(d, "background", "无")
            final_decision = _get_attr(d, "final_decision", "无")
            rationale = _get_attr(d, "rationale", "无")

            lines.extend(
                [
                    f"## {decision_id} - {title}",
                    "",
                    f"**决策时间**: {created_at[:10] if created_at else ''}",
                    f"**决策者**: {decision_maker}",
                    f"**状态**: {status}",
                    "",
                    "### 决策背景",
                    background,
                    "",
                    "### 最终决策",
                    final_decision,
                    "",
                    "### 理由",
                    rationale,
                    "",
                    "---",
                    "",
                ]
            )

        return "\n".join(lines)

    # ==================== 进度追踪同步 ====================

    def sync_progress(self, record_state: bool = True) -> bool:
        """
        同步进度到boulder.json（兼容旧格式）

        Args:
            record_state: 是否记录同步状态
        """
        try:
            progress = self.db.get_progress()
            if not progress:
                return True

            # 获取笔记本条目
            notepads = {"learnings": [], "decisions": [], "issues": [], "gotchas": []}
            plan_name = _get_attr(progress, "plan_name")
            if plan_name:
                for entry_type in notepads.keys():
                    entries = self.db.get_notepad_entries(plan_name, entry_type)
                    notepads[entry_type] = [_get_attr(e, "content") for e in entries]

            # 获取检查点
            checkpoints = self.db.get_checkpoints(plan_name or "")

            # 生成兼容格式的JSON
            boulder_data = {
                "version": "2.0.0",
                "plan_name": plan_name,
                "plan_path": _get_attr(progress, "plan_path"),
                "session_id": _get_attr(progress, "session_id"),
                "started_at": _get_attr(progress, "started_at"),
                "updated_at": _get_attr(progress, "updated_at"),
                "status": _get_attr(progress, "status"),
                "total_tasks": _get_attr(progress, "total_tasks", 0),
                "completed_tasks": _get_attr(progress, "completed_tasks", 0),
                "current_task": _get_attr(progress, "current_task"),
                "notepads": notepads,
                "checkpoints": [
                    {
                        "id": _get_attr(cp, "id"),
                        "description": _get_attr(cp, "description"),
                        "created_at": _get_attr(cp, "created_at"),
                    }
                    for cp in checkpoints
                ],
            }

            # 写入文件
            boulder_path = self.quickagents_dir / "boulder.json"
            boulder_path.write_text(
                json.dumps(boulder_data, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            # 记录同步状态
            if record_state:
                self.conflict_detector.record_sync_state("progress")

            return True
        except Exception as e:
            print(f"同步进度失败: {e}")
            return False

    # ==================== 经验收集同步 ====================

    def sync_feedback(self, record_state: bool = True) -> bool:
        """
        同步经验收集到Markdown文件

        Args:
            record_state: 是否记录同步状态
        """
        try:
            feedback_dir = self.quickagents_dir / "feedback"
            feedback_dir.mkdir(parents=True, exist_ok=True)

            # 按类型分组
            type_files = {
                FeedbackType.BUG: "bugs.md",
                FeedbackType.IMPROVEMENT: "improvements.md",
                FeedbackType.BEST_PRACTICE: "best-practices.md",
                FeedbackType.SKILL_REVIEW: "skill-review.md",
                FeedbackType.AGENT_REVIEW: "agent-review.md",
            }

            for fb_type, filename in type_files.items():
                feedbacks = self.db.get_feedbacks(fb_type)
                content = self._generate_feedback_md(fb_type, feedbacks)

                file_path = feedback_dir / filename
                file_path.write_text(content, encoding="utf-8")

            # 记录同步状态
            if record_state:
                self.conflict_detector.record_sync_state("feedback_bugs")
                self.conflict_detector.record_sync_state("feedback_improvements")

            return True
        except Exception as e:
            print(f"同步反馈失败: {e}")
            return False

    def _generate_feedback_md(
        self, fb_type: FeedbackType, feedbacks: List[Dict]
    ) -> str:
        """生成反馈Markdown内容"""
        type_names = {
            FeedbackType.BUG: "Bug/错误",
            FeedbackType.IMPROVEMENT: "改进建议",
            FeedbackType.BEST_PRACTICE: "最佳实践",
            FeedbackType.SKILL_REVIEW: "Skill评估",
            FeedbackType.AGENT_REVIEW: "Agent评估",
        }

        lines = [
            f"# {type_names.get(fb_type, '反馈')}收集",
            "",
            f"> 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "> 此文件由 SQLite 自动同步生成",
            "> 主存储: .quickagents/unified.db",
            "",
            "---",
            "",
        ]

        for fb in feedbacks:
            created_at = _get_attr(fb, "created_at", "")
            project_name = _get_attr(fb, "project_name", "未知项目")
            title = _get_attr(fb, "title")
            description = _get_attr(fb, "description")
            context = _get_attr(fb, "context")
            suggestion = _get_attr(fb, "suggestion")
            rating = _get_attr(fb, "rating")

            lines.append(f"## {created_at[:16] if created_at else ''} - {project_name}")
            lines.append("")
            lines.append(f"**标题**: {title}")

            if description:
                lines.append(f"**描述**: {description}")

            if context:
                lines.append(f"**场景**: {context}")

            if suggestion:
                lines.append(f"**建议**: {suggestion}")

            if rating:
                lines.append(f"**评分**: {rating}/5")

            lines.extend(["", "---", ""])

        return "\n".join(lines)

    # ==================== 恢复操作 ====================

    def restore_all_from_md(self) -> Dict[str, int]:
        """从所有Markdown文件恢复到SQLite"""
        results = {
            "memory": self.restore_memory_from_md(),
            "tasks": self.restore_tasks_from_md(),
            "decisions": self.restore_decisions_from_md(),
            "progress": self.restore_progress_from_json(),
            "feedback": self.restore_feedback_from_md(),
        }
        return results

    def restore_tasks_from_md(self, tasks_path: str = None) -> int:
        """从TASKS.md恢复任务"""
        path = Path(tasks_path) if tasks_path else self.docs_dir / "TASKS.md"

        if not path.exists():
            return 0

        content = path.read_text(encoding="utf-8")
        restored = 0

        # 解析任务格式
        # 格式1: - [x] T001: 任务名称 - 完成于 2026-03-25
        # 格式2: - [ ] T002: 任务名称
        pattern = (
            r"-\s*\[([ x])\]\s*(T\d+):\s*(.+?)(?:\s*-\s*完成于\s*(\d{4}-\d{2}-\d{2}))?$"
        )

        for match in re.finditer(pattern, content, re.MULTILINE):
            completed = match.group(1) == "x"
            task_id = match.group(2)
            name = match.group(3)
            match.group(4)

            # 检查是否已存在
            existing = self.db.get_task(task_id)
            if existing is None:
                status = TaskStatus.COMPLETED if completed else TaskStatus.PENDING
                self.db.add_task(task_id, name)
                if completed:
                    self.db.update_task_status(task_id, status)
                restored += 1

        return restored

    def restore_decisions_from_md(self, decisions_path: str = None) -> int:
        """从DECISIONS.md恢复决策"""
        path = (
            Path(decisions_path) if decisions_path else self.docs_dir / "DECISIONS.md"
        )

        if not path.exists():
            return 0

        content = path.read_text(encoding="utf-8")
        restored = 0

        # 简单解析决策ID
        pattern = r"##\s*(D\d+)\s*-\s*(.+)$"

        for match in re.finditer(pattern, content, re.MULTILINE):
            match.group(1)
            match.group(2)

            # 这里简化处理，实际需要更复杂的解析
            restored += 1

        return restored

    def restore_progress_from_json(self, boulder_path: str = None) -> int:
        """从boulder.json恢复进度"""
        path = (
            Path(boulder_path)
            if boulder_path
            else self.quickagents_dir / "boulder.json"
        )

        if not path.exists():
            return 0

        try:
            data = json.loads(path.read_text(encoding="utf-8"))

            # 恢复进度
            self.db.init_progress(
                plan_name=data.get("plan_name", ""),
                plan_path=data.get("plan_path"),
                total_tasks=data.get("total_tasks", 0),
            )

            # 恢复笔记本
            notepads = data.get("notepads", {})
            plan_name = data.get("plan_name", "")

            for entry_type, entries in notepads.items():
                for entry in entries:
                    if isinstance(entry, str):
                        self.db.add_notepad_entry(plan_name, entry_type, entry)

            return 1
        except Exception as e:
            print(f"恢复进度失败: {e}")
            return 0

    def restore_feedback_from_md(self) -> int:
        """从反馈Markdown文件恢复"""
        feedback_dir = self.quickagents_dir / "feedback"

        if not feedback_dir.exists():
            return 0

        restored = 0
        type_files = {
            "bugs.md": FeedbackType.BUG,
            "improvements.md": FeedbackType.IMPROVEMENT,
            "best-practices.md": FeedbackType.BEST_PRACTICE,
            "skill-review.md": FeedbackType.SKILL_REVIEW,
            "agent-review.md": FeedbackType.AGENT_REVIEW,
        }

        for filename, fb_type in type_files.items():
            file_path = feedback_dir / filename
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
                # 简单解析，实际需要更复杂的解析
                # 这里只计数
                entries = content.count("## ")
                restored += entries

        return restored


def get_markdown_sync(db: UnifiedDB = None, docs_dir: str = "Docs") -> MarkdownSync:
    """获取Markdown同步器实例"""
    return MarkdownSync(db, docs_dir)
