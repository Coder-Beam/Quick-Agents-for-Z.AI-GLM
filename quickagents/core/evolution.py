"""
SkillEvolution - 统一的Skills自我进化系统

核心功能:
- 自动触发: 任务完成、Git提交、定期优化
- 统一存储: 所有进化记录存入UnifiedDB
- 经验闭环: 收集 -> 分析 -> 改进 -> 验证

架构 (v2.3.0):
- SQLite主存储: unified.db/skill_evolution表
- Markdown辅助备份: ~/.quickagents/evolution/*.md
- Python API调用，0 Token消耗
"""

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

from .unified_db import UnifiedDB, FeedbackType
from ..utils.encoding import write_file_utf8

logger = logging.getLogger(__name__)


class EvolutionTrigger(Enum):
    """进化触发类型"""

    TASK_COMPLETE = "task_complete"  # 任务完成
    GIT_COMMIT = "git_commit"  # Git提交
    PERIODIC = "periodic"  # 定期优化
    MANUAL = "manual"  # 手动触发
    ERROR_DETECTED = "error_detected"  # 错误检测


class SkillEvolution:
    """
    统一的Skills自我进化系统

    使用方式:
        from quickagents import UnifiedDB, SkillEvolution

        db = UnifiedDB('.quickagents/unified.db')
        evolution = SkillEvolution(db)

        # 任务完成时自动触发
        evolution.on_task_complete(task_info)

        # Git提交时自动触发
        evolution.on_git_commit(commit_info)

        # 检查是否需要定期优化
        if evolution.check_periodic_trigger():
            evolution.run_periodic_optimization()
    """

    # 定期优化阈值
    PERIODIC_TASK_THRESHOLD = 10  # 每10个任务
    PERIODIC_DAYS_THRESHOLD = 7  # 或每7天

    def __init__(self, db: UnifiedDB, project_name: Optional[str] = None):
        """
        初始化进化系统

        Args:
            db: UnifiedDB实例
            project_name: 项目名称
        """
        self.db = db
        self.project_name = project_name or os.path.basename(os.getcwd())
        self._init_evolution_table()

    def _init_evolution_table(self) -> None:
        """初始化skill_evolution表"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()

            # Skills进化记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS skill_evolution (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_name TEXT NOT NULL,
                    version TEXT DEFAULT '1.0.0',
                    trigger_type TEXT NOT NULL,
                    change_type TEXT NOT NULL,
                    description TEXT,
                    details TEXT,
                    rating INTEGER,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_evolution_skill ON skill_evolution(skill_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_evolution_trigger ON skill_evolution(trigger_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_evolution_status ON skill_evolution(status)")

            # Skills使用统计表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS skill_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_name TEXT NOT NULL,
                    task_id TEXT,
                    success INTEGER DEFAULT 1,
                    duration_ms INTEGER,
                    error_message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_skill ON skill_usage(skill_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_created ON skill_usage(created_at)")

            # 进化配置表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS evolution_config (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

    # ==================== 自动触发点 ====================

    def on_task_complete(self, task_info: Dict) -> Dict:
        """
        任务完成时自动触发

        Args:
            task_info: 任务信息 {
                'task_id': str,
                'task_name': str,
                'skills_used': List[str],
                'success': bool,
                'duration_ms': int,
                'error': str (optional)
            }

        Returns:
            进化分析结果
        """
        result = {  # type: ignore[var-annotated]
            "trigger": EvolutionTrigger.TASK_COMPLETE.value,
            "task_id": task_info.get("task_id"),
            "skills_analyzed": [],
            "feedback_added": [],
            "improvements_found": [],
        }

        # 1. 记录Skills使用情况
        for skill_name in task_info.get("skills_used", []):
            self._record_skill_usage(
                skill_name=skill_name,
                task_id=task_info.get("task_id"),
                success=task_info.get("success", True),
                duration_ms=task_info.get("duration_ms"),
                error_message=task_info.get("error"),
            )
            result["skills_analyzed"].append(skill_name)  # type: ignore[union-attr]

        # 2. 分析失败原因
        if not task_info.get("success", True):
            improvement = self._analyze_failure(task_info)
            if improvement:
                result["improvements_found"].append(improvement)  # type: ignore[union-attr]

        # 3. 检查是否有可复用的模式
        patterns = self._extract_patterns(task_info)
        if patterns:
            for pattern in patterns:
                self.db.add_feedback(
                    FeedbackType.BEST_PRACTICE,  # type: ignore[arg-type]
                    title=f"发现可复用模式: {pattern['name']}",
                    description=pattern["description"],
                    project_name=self.project_name,
                    metadata={
                        "context": pattern["context"],
                        "tags": ["auto-detected", "pattern"],
                    },
                )
                result["feedback_added"].append(pattern["name"])  # type: ignore[union-attr]

        # 4. 更新任务计数
        self._increment_task_count()

        # 5. 检查是否触发定期优化
        if self.check_periodic_trigger():
            result["periodic_optimization_due"] = True

        # 6. 积累经验到编译器
        try:
            from .experience_compiler import ExperienceCompiler

            compiler = ExperienceCompiler(str(self.db.db_path))
            compiler.accumulate(
                {
                    "task_id": task_info.get("task_id", "unknown"),
                    "skill": ", ".join(task_info.get("skills_used", [])),
                    "success": task_info.get("success", True),
                    "duration_ms": task_info.get("duration_ms", 0),
                    "observations": task_info.get("error") or task_info.get("task_name", ""),
                    "category": "evolution",
                }
            )
        except Exception as e:
            logger.debug("经验编译器积累失败（非致命）: %s", e)

        # 7. 检查是否需要自动编译经验
        compile_result = None
        try:
            from .experience_compiler import ExperienceCompiler

            compiler = ExperienceCompiler(str(self.db.db_path))
            if compiler.should_compile():
                result["experience_compile_due"] = True
                compile_result = {
                    "uncompiled_count": compiler.get_stats().get("uncompiled_entries", 0),
                    "status": "ready",
                }
        except Exception as e:
            logger.debug("经验编译检查失败: %s", e)

        return result

    def on_git_commit(self, commit_info: Optional[Dict] = None) -> Dict:
        """
        Git提交时自动触发

        Args:
            commit_info: 提交信息 {
                'hash': str,
                'message': str,
                'files_changed': List[str],
                'author': str
            } (可选，不提供则自动获取)

        Returns:
            进化分析结果
        """
        if commit_info is None:
            commit_info = self._get_last_commit_info()

        if not commit_info:
            return {
                "trigger": EvolutionTrigger.GIT_COMMIT.value,
                "status": "no_commits",
            }

        result = {  # type: ignore[var-annotated]
            "trigger": EvolutionTrigger.GIT_COMMIT.value,
            "commit_hash": commit_info.get("hash"),
            "improvements_found": [],
        }

        # 1. 分析提交内容
        analysis = self._analyze_commit(commit_info)

        # 2. 检测是否有改进点
        if analysis.get("improvements"):
            for imp in analysis["improvements"]:
                self.db.add_feedback(
                    FeedbackType.IMPROVEMENT,  # type: ignore[arg-type]
                    title=imp["title"],
                    description=imp.get("description", imp["title"]),
                    project_name=self.project_name,
                    metadata={
                        "context": f"Commit: {commit_info.get('hash', '')[:8]}",
                        "category": imp.get("category", "pattern"),
                        "files": imp.get("files", []),
                        "tags": [
                            "git-commit",
                            "auto-detected",
                            imp.get("type", "unknown"),
                        ],
                        "suggestion": imp.get("suggestion", ""),
                        "avoidance": "",
                    },
                )
                result["improvements_found"].append(imp["title"])  # type: ignore[union-attr]

        # 3. 检测是否有Bug修复
        if "fix" in commit_info.get("message", "").lower():
            # 尝试从 files_changed 提取修复范围
            files_changed = commit_info.get("files_changed", [])
            fix_scope = ", ".join(sorted(set(f.split("/")[0] for f in files_changed if "/" in f))[:3])
            self.db.add_feedback(
                FeedbackType.BUG,  # type: ignore[arg-type]
                title=f"Bug修复: {commit_info.get('message', '')[:80]}",
                description=commit_info.get("message", ""),
                project_name=self.project_name,
                metadata={
                    "context": f"Commit: {commit_info.get('hash', '')}",
                    "category": "fix",
                    "files": files_changed,
                    "tags": ["git-commit", "bug-fix"],
                    "suggestion": f"已修复，涉及模块: {fix_scope or '未知'}",
                    "avoidance": "同类问题可参考此修复方案",
                },
            )

        return result

    def on_error_detected(self, error_info: Dict) -> Dict:
        """
        错误检测时自动触发

        Args:
            error_info: 错误信息 {
                'error_type': str,
                'error_message': str,
                'context': str,
                'skill_involved': str (optional)
            }

        Returns:
            进化分析结果
        """
        result = {
            "trigger": EvolutionTrigger.ERROR_DETECTED.value,
            "error_type": error_info.get("error_type"),
            "logged": False,
        }

        # 记录错误
        self.db.add_feedback(
            FeedbackType.BUG,  # type: ignore[arg-type]
            title=f"[{error_info.get('error_type', 'Unknown')}] {error_info.get('error_message', '')[:100]}",
            description=error_info.get("error_message", ""),
            project_name=self.project_name,
            metadata={
                "context": error_info.get("context", ""),
                "suggestion": self._suggest_fix(error_info),
                "tags": ["error", "auto-detected"],
            },
        )
        result["logged"] = True

        # 如果涉及特定Skill，记录使用失败
        if error_info.get("skill_involved"):
            self._record_skill_usage(
                skill_name=error_info["skill_involved"],
                success=False,
                error_message=error_info.get("error_message"),
            )
            result["skill_recorded"] = error_info["skill_involved"]

        return result

    # ==================== 定期优化 ====================

    def check_periodic_trigger(self) -> bool:
        """
        检查是否触发定期优化

        触发条件:
        - 任务数达到阈值 (10个)
        - 或时间达到阈值 (7天)
        """
        # 检查任务计数
        task_count = self._get_task_count()
        if task_count >= self.PERIODIC_TASK_THRESHOLD:
            return True

        # 检查上次优化时间
        last_optimization = self._get_last_optimization_time()
        if last_optimization:
            days_since = (datetime.now() - last_optimization).days
            if days_since >= self.PERIODIC_DAYS_THRESHOLD:
                return True
        else:
            # 从未优化过，检查是否有足够数据
            if task_count >= 5:
                return True

        return False

    def run_periodic_optimization(self) -> Dict:
        """
        执行定期优化

        Returns:
            优化结果
        """
        result = {
            "trigger": EvolutionTrigger.PERIODIC.value,
            "skills_reviewed": [],
            "improvements_suggested": [],
            "skills_to_update": [],
        }

        # 1. 获取所有Skills使用统计
        stats = self._get_skill_statistics()

        # 2. 分析每个Skill的表现
        for skill_name, stat in stats.items():
            review = self._review_skill(skill_name, stat)
            result["skills_reviewed"].append(  # type: ignore[attr-defined]
                {
                    "skill_name": skill_name,
                    "success_rate": stat.get("success_rate", 0),
                    "usage_count": stat.get("count", 0),
                    "recommendation": review.get("recommendation"),
                }
            )

            # 识别需要改进的Skills
            if stat.get("success_rate", 1) < 0.8:
                result["skills_to_update"].append(skill_name)  # type: ignore[attr-defined]
                self._add_evolution_record(
                    skill_name=skill_name,
                    trigger_type=EvolutionTrigger.PERIODIC.value,
                    change_type="improvement_needed",
                    description=f"成功率低于80%: {stat.get('success_rate', 0):.1%}",
                    details=stat,
                )

        # 3. 更新优化时间
        self._update_last_optimization_time()
        result["optimization_time"] = datetime.now().isoformat()

        # 4. 重置任务计数
        self._reset_task_count()

        # 自动编译经验（如果达到阈值）
        try:
            from .experience_compiler import ExperienceCompiler

            compiler = ExperienceCompiler(str(self.db.db_path))
            if compiler.should_compile():
                prompt = compiler.generate_compile_prompt()
                if prompt and not prompt.startswith("[Experience]"):
                    stats = compiler.get_stats()
                    uncompiled = stats.get("uncompiled_entries", 0)
                    if uncompiled > 0:
                        self._auto_compile_experiences(compiler)
                        self._add_evolution_record(
                            skill_name="experience_compiler",
                            trigger_type=EvolutionTrigger.PERIODIC.value,
                            change_type="auto_compile",
                            description=f"自动编译 {uncompiled} 条经验",
                        )
        except Exception as e:
            logger.debug("自动编译失败: %s", e)

        return result

    # ==================== Skill管理 ====================

    def record_skill_creation(self, skill_name: str, reason: str, expected_use: Optional[str] = None) -> Dict:
        """记录Skill创建"""
        record_id = self._add_evolution_record(
            skill_name=skill_name,
            trigger_type=EvolutionTrigger.MANUAL.value,
            change_type="created",
            description=reason,
            details={"expected_use": expected_use},
        )
        return {
            "skill_name": skill_name,
            "change_type": "creation",
            "id": record_id,
            "details": {"expected_use": expected_use},
        }

    def record_skill_update(self, skill_name: str, version: str, changes: List[str], reason: str) -> Dict:
        """记录Skill更新"""
        record_id = self._add_evolution_record(
            skill_name=skill_name,
            trigger_type=EvolutionTrigger.MANUAL.value,
            change_type="updated",
            description=reason,
            details={"version": version, "changes": changes},
        )
        return {
            "skill_name": skill_name,
            "change_type": "update",
            "id": record_id,
            "version": version,
            "changes": changes,
        }

    def record_skill_archive(self, skill_name: str, reason: str) -> Dict:
        """记录Skill归档"""
        record_id = self._add_evolution_record(
            skill_name=skill_name,
            trigger_type=EvolutionTrigger.MANUAL.value,
            change_type="archived",
            description=reason,
        )
        return {
            "skill_name": skill_name,
            "change_type": "archive",
            "id": record_id,
            "reason": reason,
        }

    def get_skill_history(self, skill_name: str) -> List[Dict]:
        """获取Skill进化历史"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM skill_evolution
                WHERE skill_name = ?
                ORDER BY created_at DESC
            """,
                (skill_name,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_skill_stats(self, skill_name: str) -> Dict:
        """获取Skill使用统计"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()

            # 总使用次数
            cursor.execute(
                """
                SELECT COUNT(*) as count FROM skill_usage WHERE skill_name = ?
            """,
                (skill_name,),
            )
            total = cursor.fetchone()["count"]

            # 成功次数
            cursor.execute(
                """
                SELECT COUNT(*) as count FROM skill_usage
                WHERE skill_name = ? AND success = 1
            """,
                (skill_name,),
            )
            success = cursor.fetchone()["count"]

            # 平均耗时
            cursor.execute(
                """
                SELECT AVG(duration_ms) as avg_duration FROM skill_usage
                WHERE skill_name = ? AND duration_ms IS NOT NULL
            """,
                (skill_name,),
            )
            avg_duration = cursor.fetchone()["avg_duration"]

            # 最近错误
            cursor.execute(
                """
                SELECT error_message, created_at FROM skill_usage
                WHERE skill_name = ? AND success = 0
                ORDER BY created_at DESC LIMIT 5
            """,
                (skill_name,),
            )
            recent_errors = [dict(row) for row in cursor.fetchall()]

            return {
                "skill_name": skill_name,
                "usage_count": total,
                "success_count": success,
                "failure_count": total - success,
                "success_rate": success / total if total > 0 else 0,
                "avg_duration_ms": avg_duration,
                "recent_errors": recent_errors,
            }

    def get_all_skills_stats(self) -> Dict[str, Dict]:
        """获取所有Skills统计"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT skill_name,
                       COUNT(*) as count,
                       SUM(success) as success_count,
                       AVG(duration_ms) as avg_duration
                FROM skill_usage
                GROUP BY skill_name
            """)

            stats = {}
            for row in cursor.fetchall():
                skill_name = row["skill_name"]
                count = row["count"]
                success_count = row["success_count"] or 0
                stats[skill_name] = {
                    "count": count,
                    "success_count": success_count,
                    "failure_count": count - success_count,
                    "success_rate": success_count / count if count > 0 else 0,
                    "avg_duration_ms": row["avg_duration"],
                }

            return stats

    # ==================== 批量优化与历史模式分析 (v2.11.0) ====================

    def batch_analyze_skills(self, batch_size: int = 50) -> Dict:
        """
        批量分析Skills使用记录，一次性处理多个记录 (MCE论文: batch-level 13.6x faster)

        Args:
            batch_size: 单批处理的记录数

        Returns:
            批量分析结果
        """
        with self.db._get_connection() as conn:
            cursor = conn.cursor()

            # 获取最近的usage记录
            cursor.execute(
                """
                SELECT skill_name, success, duration_ms, error_message, created_at
                FROM skill_usage
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (batch_size,),
            )
            rows = [dict(row) for row in cursor.fetchall()]

        if not rows:
            return {"batch_size": 0, "analysis": {}, "patterns": []}

        # 按skill分组批量计算
        skill_data = {}  # type: Dict[str, Dict]
        for row in rows:
            name = row["skill_name"]
            if name not in skill_data:
                skill_data[name] = {"total": 0, "success": 0, "durations": [], "errors": []}
            skill_data[name]["total"] += 1
            if row["success"]:
                skill_data[name]["success"] += 1
            if row["duration_ms"]:
                skill_data[name]["durations"].append(row["duration_ms"])
            if row["error_message"]:
                skill_data[name]["errors"].append(row["error_message"])

        # 批量分析每个skill
        analysis = {}
        for name, data in skill_data.items():
            success_rate = data["success"] / data["total"] if data["total"] > 0 else 0
            avg_duration = sum(data["durations"]) / len(data["durations"]) if data["durations"] else 0

            # 性能分级
            if success_rate >= 0.9 and avg_duration < 5000:
                grade = "A"
            elif success_rate >= 0.8:
                grade = "B"
            elif success_rate >= 0.6:
                grade = "C"
            else:
                grade = "D"

            # 检测退化趋势 (最近5次vs全部)
            recent = rows[: min(5, len(rows))]
            recent_success = sum(1 for r in recent if r["skill_name"] == name and r["success"])
            recent_total = sum(1 for r in recent if r["skill_name"] == name)
            recent_rate = recent_success / recent_total if recent_total > 0 else success_rate
            degrading = recent_rate < success_rate - 0.1

            analysis[name] = {
                "grade": grade,
                "success_rate": round(success_rate, 3),
                "avg_duration_ms": round(avg_duration, 1),
                "usage_count": data["total"],
                "unique_errors": len(set(data["errors"])),
                "degrading": degrading,
            }

        # 检测跨skill模式
        patterns = self._detect_batch_patterns(skill_data)

        return {
            "batch_size": len(rows),
            "skills_analyzed": len(skill_data),
            "analysis": analysis,
            "patterns": patterns,
        }

    def analyze_history_patterns(self, lookback_days: int = 30) -> Dict:
        """
        分析历史模式，发现重复出现的问题和成功模式

        Args:
            lookback_days: 回看天数

        Returns:
            历史模式分析结果
        """
        from datetime import timedelta

        cutoff = (datetime.now() - timedelta(days=lookback_days)).isoformat()

        with self.db._get_connection() as conn:
            cursor = conn.cursor()

            # 获取历史进化记录
            cursor.execute(
                """
                SELECT skill_name, trigger_type, change_type, description, details, created_at
                FROM skill_evolution
                WHERE created_at >= ?
                ORDER BY created_at DESC
            """,
                (cutoff,),
            )
            evolution_rows = [dict(row) for row in cursor.fetchall()]

            # 获取历史使用记录
            cursor.execute(
                """
                SELECT skill_name, success, duration_ms, error_message, created_at
                FROM skill_usage
                WHERE created_at >= ?
                ORDER BY created_at ASC
            """,
                (cutoff,),
            )
            usage_rows = [dict(row) for row in cursor.fetchall()]

        # 1. 重复错误模式
        error_patterns = {}  # type: Dict[str, int]
        for row in usage_rows:
            if not row["success"] and row["error_message"]:
                # 简化错误消息以归类
                err_key = row["error_message"][:80]
                error_patterns[err_key] = error_patterns.get(err_key, 0) + 1

        recurring_errors = [
            {"error": k, "count": v} for k, v in sorted(error_patterns.items(), key=lambda x: -x[1]) if v >= 2
        ]

        # 2. Skill使用趋势 (按周聚合)
        weekly_trend = {}  # type: Dict[str, Dict[str, int]]
        for row in usage_rows:
            # 按周分组 (使用ISO week)
            try:
                dt = datetime.fromisoformat(row["created_at"])
                week_key = dt.strftime("%Y-W%W")
            except (ValueError, TypeError):
                week_key = "unknown"

            if week_key not in weekly_trend:
                weekly_trend[week_key] = {"total": 0, "success": 0}

            weekly_trend[week_key]["total"] += 1
            if row["success"]:
                weekly_trend[week_key]["success"] += 1

        # 3. 高频Skill组合 (成功任务中经常一起出现的skills)
        skill_co_occurrence = {}  # type: Dict[str, int]
        for row in evolution_rows:
            details_str = row.get("details", "")
            if details_str and row["change_type"] in ("pattern_extracted", "skills_combination"):
                try:
                    details = json.loads(details_str) if isinstance(details_str, str) else details_str
                    skills = details.get("skills_used", [])
                    if len(skills) >= 2:
                        key = " + ".join(sorted(skills))
                        skill_co_occurrence[key] = skill_co_occurrence.get(key, 0) + 1
                except (json.JSONDecodeError, TypeError):
                    pass

        top_combos = sorted(skill_co_occurrence.items(), key=lambda x: -x[1])[:5]

        # 4. 性能退化检测
        degraded_skills = []
        for row in evolution_rows:
            if row["change_type"] == "improvement_needed":
                degraded_skills.append(
                    {"skill": row["skill_name"], "description": row["description"], "date": row["created_at"]}
                )

        return {
            "lookback_days": lookback_days,
            "total_records": len(evolution_rows) + len(usage_rows),
            "recurring_errors": recurring_errors[:10],
            "weekly_trend": dict(sorted(weekly_trend.items())),
            "top_skill_combos": [{"combo": k, "count": v} for k, v in top_combos],
            "degraded_skills": degraded_skills[-5:],
            "summary": {
                "unique_errors": len(error_patterns),
                "recurring_error_count": len(recurring_errors),
                "weeks_analyzed": len(weekly_trend),
                "skill_combos_found": len(skill_co_occurrence),
            },
        }

    def _detect_batch_patterns(self, skill_data: Dict[str, Dict]) -> List[Dict]:
        """检测批量数据中的跨skill模式"""
        patterns = []

        # 1. 多个skill同时退化
        degraded = [
            name for name, data in skill_data.items() if data["total"] >= 3 and data["success"] / data["total"] < 0.7
        ]
        if len(degraded) >= 2:
            patterns.append(
                {
                    "type": "multi_skill_degradation",
                    "description": f"多个skill成功率低于70%: {', '.join(degraded)}",
                    "affected_skills": degraded,
                    "severity": "high",
                }
            )

        # 2. 所有skill都成功的模式 (最佳实践)
        all_good = [
            name for name, data in skill_data.items() if data["total"] >= 2 and data["success"] == data["total"]
        ]
        if len(all_good) >= 3:
            patterns.append(
                {
                    "type": "all_success_pattern",
                    "description": f"这些skill在本批次全部成功: {', '.join(all_good[:5])}",
                    "skills": all_good[:5],
                    "severity": "info",
                }
            )

        # 3. 慢skill检测 (平均耗时>10秒)
        slow_skills = [
            {
                "name": name,
                "avg_ms": sum(data["durations"]) / len(data["durations"]) if data["durations"] else 0,
            }
            for name, data in skill_data.items()
            if data["durations"] and sum(data["durations"]) / len(data["durations"]) > 10000
        ]
        if slow_skills:
            patterns.append(
                {
                    "type": "slow_skills",
                    "description": f"慢skill (avg>10s): {', '.join(s['name'] for s in slow_skills)}",
                    "details": slow_skills,
                    "severity": "medium",
                }
            )

        return patterns

    # ==================== 内部方法 ====================

    def _add_evolution_record(
        self,
        skill_name: str,
        trigger_type: str,
        change_type: str,
        description: str,
        details: Optional[Dict] = None,
        rating: Optional[int] = None,
    ) -> int:
        """添加进化记录"""
        details_str = json.dumps(details, ensure_ascii=False) if details else None

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO skill_evolution
                (skill_name, trigger_type, change_type, description, details, rating)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    skill_name,
                    trigger_type,
                    change_type,
                    description,
                    details_str,
                    rating,
                ),
            )

            return cursor.lastrowid

    def _record_skill_usage(
        self,
        skill_name: str,
        task_id: Optional[str] = None,
        success: bool = True,
        duration_ms: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """记录Skill使用"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO skill_usage
                (skill_name, task_id, success, duration_ms, error_message)
                VALUES (?, ?, ?, ?, ?)
            """,
                (skill_name, task_id, 1 if success else 0, duration_ms, error_message),
            )

    def _analyze_failure(self, task_info: Dict) -> Optional[Dict]:
        """分析失败原因"""
        error = task_info.get("error", "")
        skills_used = task_info.get("skills_used", [])

        if not error:
            return None

        # 记录改进建议
        self.db.add_feedback(
            FeedbackType.IMPROVEMENT,  # type: ignore[arg-type]
            title=f"任务失败分析: {task_info.get('task_name', '')}",
            description=f"错误: {error}",
            project_name=self.project_name,
            metadata={
                "context": f"Skills使用: {', '.join(skills_used)}",
                "suggestion": "检查相关Skills的错误处理逻辑",
                "tags": ["failure-analysis", "auto-detected"],
            },
        )

        return {
            "task_id": task_info.get("task_id"),
            "error": error,
            "skills_involved": skills_used,
        }

    def _extract_patterns(self, task_info: Dict) -> List[Dict]:
        """提取可复用模式与经验"""
        patterns = []
        skills_used = task_info.get("skills_used", [])
        success = task_info.get("success", True)
        task_name = task_info.get("task_name", "")
        duration_ms = task_info.get("duration_ms", 0)

        # ===== 1. Skills组合模式 =====
        if success and len(skills_used) >= 2:
            patterns.append(
                {
                    "name": f"Skills组合: {' + '.join(skills_used[:3])}",
                    "description": f"成功使用 {len(skills_used)} 个Skills完成: {task_name}",
                    "context": f"任务: {task_name}, 耗时: {duration_ms}ms",
                    "category": "pattern",
                }
            )

        # ===== 2. 效率异常检测 =====
        if duration_ms > 30000:  # 超过30秒
            patterns.append(
                {
                    "name": f"慢任务警告: {task_name}",
                    "description": f"任务耗时 {duration_ms}ms ({duration_ms / 1000:.1f}s)，超过30秒阈值",
                    "context": f"Skills: {', '.join(skills_used)}",
                    "category": "pitfall",
                    "suggestion": "考虑拆分任务或优化性能瓶颈",
                }
            )

        # ===== 3. 失败经验提取 =====
        if not success:
            error = task_info.get("error", "")
            if error:
                patterns.append(
                    {
                        "name": f"失败经验: {task_name}",
                        "description": f"错误: {error[:200]}",
                        "context": f"Skills: {', '.join(skills_used)}",
                        "category": "pitfall",
                        "suggestion": "检查相关Skills的错误处理逻辑",
                        "avoidance": f"避免重复触发: {', '.join(skills_used)}",
                    }
                )

        # ===== 4. 单Skill高频使用检测 =====
        if success and len(skills_used) == 1:
            patterns.append(
                {
                    "name": f"高频Skill: {skills_used[0]}",
                    "description": f"单独使用 {skills_used[0]} 完成任务",
                    "context": f"任务: {task_name}",
                    "category": "pattern",
                }
            )

        return patterns

    def _analyze_commit(self, commit_info: Dict) -> Dict:
        """分析提交内容

        覆盖所有 conventional commit 类型 + files_changed 模式分析
        """
        message = commit_info.get("message", "").lower()
        files_changed = commit_info.get("files_changed", [])

        improvements = []

        # ===== 1. Conventional commit 类型分析 =====
        commit_type_map = {
            "feat": {
                "title": "新功能开发",
                "category": "pattern",
            },
            "fix": {
                "title": "Bug修复",
                "category": "fix",
            },
            "refactor": {
                "title": "代码重构",
                "category": "pattern",
            },
            "perf": {
                "title": "性能优化",
                "category": "pattern",
            },
            "docs": {
                "title": "文档更新",
                "category": "pattern",
            },
            "test": {
                "title": "测试补充",
                "category": "pattern",
            },
            "style": {
                "title": "代码格式调整",
                "category": "pattern",
            },
            "chore": {
                "title": "构建/工具变更",
                "category": "pattern",
            },
            "ci": {
                "title": "CI配置变更",
                "category": "pattern",
            },
        }

        for type_key, type_info in commit_type_map.items():
            if type_key + "(" in message or type_key + ":" in message or message.startswith(type_key):
                improvements.append(
                    {
                        "title": type_info["title"],
                        "description": f"提交信息: {commit_info.get('message', '')}",
                        "type": type_key,
                        "category": type_info["category"],
                    }
                )
                break  # 一个提交只匹配一个类型

        # ===== 2. files_changed 模式分析 =====
        if files_changed:
            # 2a. 模块热点分析
            dir_counts = {}  # type: ignore[var-annotated]
            for f in files_changed:
                parts = f.split("/")
                if len(parts) > 1:
                    module = parts[0]
                    dir_counts[module] = dir_counts.get(module, 0) + 1

            hot_modules = [m for m, c in sorted(dir_counts.items(), key=lambda x: -x[1]) if c >= 2]
            if hot_modules:
                improvements.append(
                    {
                        "title": f"高频变更模块: {', '.join(hot_modules)}",
                        "description": (
                            f"本次提交中 {hot_modules[0]} 模块有"
                            f" {dir_counts[hot_modules[0]]} 个文件变更，是系统核心热点"
                        ),
                        "type": "module_hotspot",
                        "category": "architecture",
                        "files": hot_modules,  # type: ignore[dict-item]
                    }
                )

            # 2b. 配置文件变更检测
            config_extensions = (
                ".json",
                ".yaml",
                ".yml",
                ".toml",
                ".ini",
                ".cfg",
                ".env",
            )
            config_files = [f for f in files_changed if any(f.endswith(ext) for ext in config_extensions)]
            if config_files:
                improvements.append(
                    {
                        "title": "配置文件变更",
                        "description": f"变更的配置文件: {', '.join(config_files)}，可能影响运行时行为",
                        "type": "config_change",
                        "category": "pitfall",
                        "files": config_files,  # type: ignore[dict-item]
                    }
                )

            # 2c. 测试覆盖检测
            src_files = [f for f in files_changed if f.startswith("src/") and not f.startswith("src/test")]
            test_files = [f for f in files_changed if "test" in f.lower()]
            if src_files and not test_files:
                improvements.append(
                    {
                        "title": "源码变更缺少对应测试",
                        "description": f"修改了源码但未更新测试: {', '.join(src_files[:3])}",
                        "type": "missing_test",
                        "category": "pitfall",
                        "files": src_files,  # type: ignore[dict-item]
                        "suggestion": f"建议为 {src_files[0]} 添加对应的测试文件",
                    }
                )

            # 2e. 大规模变更检测
            if len(files_changed) >= 5:
                improvements.append(
                    {
                        "title": "大规模变更",
                        "description": f"本次提交涉及 {len(files_changed)} 个文件，属于大规模变更",
                        "type": "large_change",
                        "category": "architecture",
                        "suggestion": "大规模变更建议拆分为多个原子提交",
                    }
                )

        return {"improvements": improvements}

    def _suggest_fix(self, error_info: Dict) -> str:
        """
        基于项目历史经验的修复建议

        检索链路:
        1. 从 experience_compiler 查询编译后的经验文章
        2. 从 feedback 表搜索同类型错误的修复记录 (category='fix')
        3. 有匹配 → 返回历史解决方案
        4. 无匹配 → 返回通用建议
        """
        error_type = error_info.get("error_type", "")

        # 0. 查询经验编译器的编译文章
        try:
            from .experience_compiler import ExperienceCompiler

            compiler = ExperienceCompiler(str(self.db.db_path))
            compiled = compiler.query(error_type)
            if compiled:
                return compiled[:500]
        except Exception:
            pass

        # 1. 从项目历史经验中检索
        try:
            feedbacks = self.db.get_feedbacks(limit=50)
            for fb in feedbacks:
                meta = fb.metadata if hasattr(fb, "metadata") else {}
                if isinstance(meta, str):
                    import json

                    meta = json.loads(meta) if meta else {}

                if meta.get("category") == "fix" and error_type in str(meta.get("tags", [])):
                    suggestion = meta.get("suggestion", "")
                    if suggestion:
                        return suggestion

                # 也匹配 description 中的错误类型
                desc = fb.description if hasattr(fb, "description") else ""
                if desc and error_type in desc:
                    suggestion = meta.get("suggestion", "")
                    if suggestion:
                        return suggestion
        except Exception as e:
            logger.debug("Failed to query error suggestions: %s", e)

        # 2. 通用映射（fallback）
        suggestions = {
            "ImportError": "检查模块是否正确安装，确认 package 在 PYTHONPATH 中",
            "ModuleNotFoundError": "检查模块名称拼写，执行 pip install 安装缺失依赖",
            "FileNotFoundError": "检查文件路径是否正确，确认文件存在",
            "PermissionError": "检查文件/目录权限，尝试 chmod 或以管理员身份运行",
            "TimeoutError": "考虑增加超时时间或优化操作性能",
            "ValueError": "检查输入参数的有效性和取值范围",
            "TypeError": "检查参数类型是否正确，确认接口签名未变更",
            "KeyError": "检查字典键名是否正确，确认数据结构未变更",
            "AttributeError": "检查对象属性是否存在，确认类定义未变更",
            "IndexError": "检查索引是否越界,确认列表长度",
            "RuntimeError": "检查运行时状态，确认前置条件已满足",
        }

        return suggestions.get(error_type, f"请检查 {error_type} 的详情并尝试修复")

    def _review_skill(self, skill_name: str, stat: Dict) -> Dict:
        """评估Skill"""
        success_rate = stat.get("success_rate", 1)

        if success_rate >= 0.9:
            recommendation = "excellent"
        elif success_rate >= 0.8:
            recommendation = "good"
        elif success_rate >= 0.6:
            recommendation = "needs_improvement"
        else:
            recommendation = "critical"

        return {
            "skill_name": skill_name,
            "recommendation": recommendation,
            "details": stat,
        }

    def _get_last_commit_info(self) -> Optional[Dict]:
        """获取最后一次Git提交信息"""
        try:
            # 获取提交hash
            result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return None
            commit_hash = result.stdout.strip()

            # 获取提交信息
            result = subprocess.run(
                ["git", "log", "-1", "--pretty=%s"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            message = result.stdout.strip() if result.returncode == 0 else ""

            # 获取修改的文件
            result = subprocess.run(
                [
                    "git",
                    "diff-tree",
                    "--no-commit-id",
                    "--name-only",
                    "-r",
                    commit_hash,
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            files = result.stdout.strip().split("\n") if result.returncode == 0 else []

            return {
                "hash": commit_hash,
                "message": message,
                "files_changed": [f for f in files if f],
            }
        except Exception:
            return None

    def _get_task_count(self) -> int:
        """获取自上次优化以来的任务计数"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT value FROM evolution_config WHERE key = 'task_count'
            """)
            row = cursor.fetchone()
            return int(row["value"]) if row else 0

    def _increment_task_count(self) -> int:
        """增加任务计数"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO evolution_config (key, value, updated_at)
                VALUES ('task_count', '1', ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = CAST(value AS INTEGER) + 1,
                    updated_at = excluded.updated_at
            """,
                (datetime.now().isoformat(),),
            )

            cursor.execute("SELECT value FROM evolution_config WHERE key = 'task_count'")
            return int(cursor.fetchone()["value"])

    def _reset_task_count(self) -> None:
        """重置任务计数"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE evolution_config SET value = '0', updated_at = ?
                WHERE key = 'task_count'
            """,
                (datetime.now().isoformat(),),
            )

    def _get_last_optimization_time(self) -> Optional[datetime]:
        """获取上次优化时间"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT value FROM evolution_config WHERE key = 'last_optimization'
            """)
            row = cursor.fetchone()
            if row:
                try:
                    return datetime.fromisoformat(row["value"])
                except ValueError:
                    return None
            return None

    def _update_last_optimization_time(self) -> None:
        """更新上次优化时间"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO evolution_config (key, value, updated_at)
                VALUES ('last_optimization', ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
            """,
                (datetime.now().isoformat(), datetime.now().isoformat()),
            )

    def _set_last_optimization_time(self, dt: datetime) -> None:
        """Set last optimization time (for testing)"""
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO evolution_config (key, value, updated_at)
                VALUES ('last_optimization', ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at
            """,
                (dt.isoformat(), dt.isoformat()),
            )

    def _get_skill_statistics(self) -> Dict[str, Dict]:
        """获取所有Skills统计"""
        return self.get_all_skills_stats()

    def modify_skill(self, skill_name: str, modifications: Dict) -> bool:
        """自动修改 Skill 文件"""
        skill_path = os.path.join(".opencode", "skills", skill_name, "SKILL.md")
        if not os.path.exists(skill_path):
            skill_path = os.path.join("skills", skill_name, "SKILL.md")
        if not os.path.exists(skill_path):
            return False

        try:
            with open(skill_path, "r", encoding="utf-8") as f:
                content = f.read()

            for key, value in modifications.items():
                if key == "add_guideline":
                    content += f"\n- {value}\n"
                elif key == "update_threshold":
                    import re

                    content = re.sub(rf"({value['param']}:\s*)\d+", rf"\g<1>{value['new_value']}", content)

            backup_path = skill_path + ".bak"
            with open(backup_path, "w", encoding="utf-8") as f:
                pass

            with open(skill_path, "w", encoding="utf-8") as f:
                f.write(content)

            self._add_evolution_record(
                skill_name=skill_name,
                trigger_type=EvolutionTrigger.PERIODIC.value,
                change_type="skill_modified",
                description=f"自动修改: {list(modifications.keys())}",
            )
            return True
        except Exception as e:
            logger.warning("修改Skill失败 %s: %s", skill_name, e)
            return False

    def inject_context(self, context_type: str, data: Dict) -> None:
        """将进化洞察注入到项目上下文"""
        try:
            ctx_dir = os.path.join(".quickagents", "context")
            os.makedirs(ctx_dir, exist_ok=True)

            ctx_file = os.path.join(ctx_dir, f"{context_type}_insights.json")
            with open(ctx_file, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "type": context_type,
                        "data": data,
                        "injected_at": datetime.now().isoformat(),
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )

            self._add_evolution_record(
                skill_name="context_injector",
                trigger_type=EvolutionTrigger.PERIODIC.value,
                change_type="context_injected",
                description=f"注入 {context_type} 上下文",
            )
        except Exception as e:
            logger.debug("上下文注入失败: %s", e)

    def verify_evolution(self, skill_name: str) -> Dict:
        """验证进化效果"""
        stats = self.get_skill_stats(skill_name)

        with self.db._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT success FROM skill_usage 
                WHERE skill_name = ? ORDER BY created_at DESC LIMIT 20
            """,
                (skill_name,),
            )
            recent = [row[0] for row in cursor.fetchall()]

        if len(recent) < 5:
            return {"verdict": "insufficient_data", "samples": len(recent)}

        recent_rate = sum(recent[:10]) / min(len(recent[:10]), 10) if recent[:10] else 0
        older_rate = sum(recent[10:]) / min(len(recent[10:]), 10) if recent[10:] else recent_rate

        improved = recent_rate >= older_rate

        result = {
            "skill": skill_name,
            "recent_success_rate": recent_rate,
            "baseline_success_rate": older_rate,
            "improved": improved,
            "verdict": "positive" if improved else "negative",
        }

        if not improved:
            result["rollback_recommended"] = True
            self._add_evolution_record(
                skill_name=skill_name,
                trigger_type=EvolutionTrigger.PERIODIC.value,
                change_type="rollback_recommended",
                description=f"成功率下降: {recent_rate:.1%} < {older_rate:.1%}",
            )

        return result

    # ==================== 同步到Markdown ====================

    def _auto_compile_experiences(self, compiler) -> None:
        """基于规则的即时编译（不需要LLM）"""
        try:
            from .experience_compiler import CompiledArticle

            stats = compiler.get_stats()
            categories = stats.get("categories", [])

            for category in categories:
                results = compiler.query(category)
                if not results:
                    continue

                article = CompiledArticle(
                    title=f"经验总结: {category}",
                    summary=f"基于 {category} 类别经验的自动编译",
                    body=f"## {category} 经验总结\n\n{results[:2000]}",
                    tags=["auto-compiled", category],
                    sources=[],
                    coverage="auto",
                )
                compiler.save_compiled_article(article)
        except Exception as e:
            logger.debug("规则编译失败: %s", e)

    def sync_to_markdown(self, output_dir: Optional[str] = None) -> Dict:
        """
        同步进化记录到Markdown

        Args:
            output_dir: 输出目录，默认 ~/.quickagents/evolution/
        """
        if output_dir is None:
            output_dir = Path.home() / ".quickagents" / "evolution"  # type: ignore[assignment]
        else:
            output_dir = Path(output_dir)  # type: ignore[assignment]

        output_dir.mkdir(parents=True, exist_ok=True)  # type: ignore[union-attr]

        result = {"skills_synced": 0, "files_created": []}

        # 获取所有有记录的Skills
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT skill_name FROM skill_evolution")
            skills = [row["skill_name"] for row in cursor.fetchall()]

        # 为每个Skill生成Markdown文件
        for skill_name in skills:
            history = self.get_skill_history(skill_name)
            stats = self.get_skill_stats(skill_name)

            md_content = self._generate_skill_md(skill_name, history, stats)

            file_path = output_dir / f"{skill_name}.md"  # type: ignore[operator]
            write_file_utf8(str(file_path), md_content)

            result["files_created"].append(str(file_path))  # type: ignore[attr-defined]
            result["skills_synced"] += 1  # type: ignore[operator]

        # 生成统计汇总文件
        all_stats = self.get_all_skills_stats()
        if all_stats:
            stats_content = self._generate_stats_md(all_stats)
            stats_file = output_dir / "skill_stats.md"  # type: ignore[operator]
            write_file_utf8(str(stats_file), stats_content)
            result["files_created"].append(str(stats_file))  # type: ignore[attr-defined]

        return result

    def _generate_skill_md(self, skill_name: str, history: List[Dict], stats: Dict) -> str:
        """生成Skill的Markdown文档"""
        # Handle None values with proper defaults
        avg_duration = stats.get("avg_duration_ms") or 0
        success_rate = stats.get("success_rate") or 0

        lines = [
            f"# {skill_name} 进化记录",
            "",
            "## 统计信息",
            "",
            f"- 总使用次数: {stats.get('usage_count', 0)}",
            f"- 成功次数: {stats.get('success_count', 0)}",
            f"- 失败次数: {stats.get('failure_count', 0)}",
            f"- 成功率: {success_rate:.1%}",
            f"- 平均耗时: {avg_duration:.0f}ms",
            "",
            "## 进化历史",
            "",
        ]

        for entry in history:
            lines.append(f"### {entry['created_at'][:10]} - {entry['change_type']}")
            lines.append(f"- 触发: {entry['trigger_type']}")
            lines.append(f"- 描述: {entry['description']}")
            if entry.get("details"):
                lines.append(f"- 详情: {entry['details']}")
            lines.append("")

        return "\n".join(lines)

    def _generate_stats_md(self, all_stats: Dict[str, Dict]) -> str:
        """生成统计汇总Markdown文档"""
        lines = [
            "# Skills 统计汇总",
            "",
            "## 概览",
            "",
            f"- 总Skills数: {len(all_stats)}",
            "",
        ]

        if all_stats:
            lines.append("## 详细统计")
            lines.append("")

            for skill_name, stats in sorted(all_stats.items()):
                success_rate = stats.get("success_rate", 0)
                lines.extend(
                    [
                        f"### {skill_name}",
                        "",
                        f"- 使用次数: {stats.get('count', 0)}",
                        f"- 成功次数: {stats.get('success_count', 0)}",
                        f"- 失败次数: {stats.get('failure_count', 0)}",
                        f"- 成功率: {success_rate:.1%}",
                        f"- 平均耗时: {stats.get('avg_duration_ms', 0):.0f}ms",
                        "",
                    ]
                )

        return "\n".join(lines)


# 全局实例
_global_evolution: Optional[SkillEvolution] = None


def get_evolution(db_path: str = ".quickagents/unified.db", project_name: Optional[str] = None) -> SkillEvolution:
    """获取全局进化系统实例"""
    global _global_evolution
    if _global_evolution is None:
        from .unified_db import get_unified_db

        db = get_unified_db(db_path)
        _global_evolution = SkillEvolution(db, project_name)
    return _global_evolution


def reset_evolution() -> None:
    """重置全局进化系统实例（主要用于测试）"""
    global _global_evolution
    _global_evolution = None
    from .unified_db import reset_global_db

    reset_global_db()
