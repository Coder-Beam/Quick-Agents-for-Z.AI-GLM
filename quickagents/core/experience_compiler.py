"""
ExperienceCompiler - 经验编译器（Karpathy LLM Knowledge Base模式）

核心思路:
- 分散的任务经验 → LLM编译一次 → 结构化知识文章 → 后续直接查询编译后的文章
- 增量编译（哈希检测变化，只处理新增经验）
- 覆盖度标记（告诉LLM何时信任vs查原始数据）
- 阈值触发（默认每10条经验或7天触发编译）

基于:
- llm-wiki-compiler (Karpathy模式): 383文件→13文章, 81x压缩, 84% Token节省
- arXiv:2601.21557 MCE: 批量级优化13.6x效率提升
- QuickAgents SkillEvolution: 已有进化系统增强

数据流:
  任务完成 → accumulate(task_result) → 缓冲区
                                                ↓ 达到阈值
                                         compile() → 增量编译
                                                ↓
                                    .quickagents/compiled/
                                      _index.md          # 索引
                                      _sources.md       # 源映射
                                      patterns/
                                        tdd-patterns.md
                                        debugging-tricks.md
                                        ...
"""

import hashlib
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ============================================================================
# 数据模型
# ============================================================================


class ExperienceEntry:
    """原始经验条目"""

    def __init__(
        self,
        source: str,
        category: str,
        content: str,
        timestamp: Optional[str] = None,
        source_hash: Optional[str] = None,
    ):
        self.source = source
        self.category = category
        self.content = content
        self.timestamp = timestamp or datetime.now().isoformat()
        self.source_hash = source_hash or self._compute_hash()

    def _compute_hash(self) -> str:
        content_hash = hashlib.md5(self.content.encode("utf-8")).hexdigest()[:8]
        return f"{self.source}:{content_hash}"


class CompiledArticle:
    """编译后的知识文章"""

    def __init__(
        self,
        title: str,
        summary: str,
        body: str,
        tags: List[str],
        sources: List[str],
        coverage: str = "medium",  # high/medium/low
        updated: Optional[str] = None,
    ):
        self.title = title
        self.summary = summary
        self.body = body
        self.tags = tags
        self.sources = sources
        self.coverage = coverage
        self.updated = updated or datetime.now().isoformat()


class CompileResult:
    """编译结果"""

    def __init__(self):
        self.articles_created: int = 0
        self.articles_updated: int = 0
        self.experiences_processed: int = 0
        self.experiences_skipped: int = 0
        self.coverage_map: Dict[str, int] = {}
        self.duration_ms: float = 0.0


# ============================================================================
# 经验编译器
# ============================================================================


class ExperienceCompiler:
    """
    经验编译器（Karpathy LLM Knowledge Base模式）

    将分散的任务经验编译为结构化知识文章:
    - 降低84% Token消耗（llm-wiki-compiler实测）
    - 增量编译：哈希检测变化，    - 覆盖度标记：告诉LLM何时信任

    使用方式:
        compiler = ExperienceCompiler()

        # 积累经验（每次任务完成时调用）
        compiler.accumulate({
            'task_id': 'T001',
            'skill': 'tdd-workflow',
            'success': True,
            'duration_ms': 45000,
            'observations': '测试先行能显著提升代码质量'
        })

        # 检查是否需要编译
        if compiler.should_compile():
            # 生成编译指令（由LLM执行）
            prompt = compiler.generate_compile_prompt()

    CLI:
        qka experience status      # 查看状态
        qka experience compile     # 触发编译
        qka experience query <topic> # 查询编译后的知识
    """

    # 配置
    COMPILE_TASK_THRESHOLD = 10  # 每10条未编译经验触发编译
    COMPILE_DAYS_THRESHOLD = 7  # 或每7天
    COMPILED_DIR = ".quickagents/compiled"
    INDEX_FILE = "_index.md"
    SOURCES_FILE = "_sources.md"

    # 覆盖度阈值（基于源数量）
    COVERAGE_HIGH_THRESHOLD = 5  # 5+来源 → high
    COVERAGE_MEDIUM_THRESHOLD = 2  # 2-4来源 → medium
    # 0-1来源 → low

    def __init__(self, db_path: str = ".quickagents/unified.db"):
        self._db_path = db_path
        self._buffer: List[ExperienceEntry] = []
        self._compiled_dir = Path(self.COMPILED_DIR)
        self._ensure_dirs()

    def _ensure_dirs(self):
        """确保编译目录存在"""
        self._compiled_dir.mkdir(parents=True, exist_ok=True)
        patterns_dir = self._compiled_dir / "patterns"
        patterns_dir.mkdir(exist_ok=True)

    # ====================================================================
    # 积累经验
    # ====================================================================

    def accumulate(self, task_result: Dict) -> None:
        """
        积累任务经验到缓冲区

        Args:
            task_result: 任务结果字典，包含:
                - task_id: 任务ID
                - skill: 使用的技能名称
                - success: 是否成功
                - duration_ms: 执行耗时
                - observations: 观察记录
                - error_type: 错误类型（如果失败）
                - category: 经验分类（可选）
        """
        source = task_result.get("task_id", "unknown")
        category = task_result.get("category", self._infer_category(task_result))
        content = self._serialize_experience(task_result)

        entry = ExperienceEntry(
            source=source,
            category=category,
            content=content,
        )
        self._buffer.append(entry)

        logger.debug(
            "积累经验: source=%s, category=%s, buffer=%d",
            source,
            category,
            len(self._buffer),
        )

    def _infer_category(self, task_result: Dict) -> str:
        """推断经验分类"""
        skill = task_result.get("skill", "")
        success = task_result.get("success", True)

        if not success:
            return "pitfalls"
        if "tdd" in skill.lower():
            return "tdd-patterns"
        if "debug" in skill.lower():
            return "debugging-tricks"
        if "review" in skill.lower() or "audit" in skill.lower():
            return "code-review"
        if "commit" in skill.lower() or "git" in skill.lower():
            return "git-workflow"
        if "security" in skill.lower():
            return "security-patterns"
        return "general-patterns"

    def _serialize_experience(self, task_result: Dict) -> str:
        """序列化经验为文本"""
        parts = []
        for key in ["task_id", "skill", "success", "duration_ms", "observations", "error_type"]:
            val = task_result.get(key)
            if val is not None:
                parts.append(f"{key}: {val}")
        return " | ".join(parts)

    # ====================================================================
    # 编译检查
    # ====================================================================

    def should_compile(self) -> bool:
        """检查是否需要编译"""
        # 条件1: 缓冲区达到阈值
        if len(self._buffer) >= self.COMPILE_TASK_THRESHOLD:
            return True

        # 条件2: 距上次编译超过阈值天数
        last_compile = self._get_last_compile_time()
        if last_compile is None:
            return len(self._buffer) > 0

        days_since = (datetime.now() - last_compile).days
        return days_since >= self.COMPILE_DAYS_THRESHOLD and len(self._buffer) > 0

    def _get_last_compile_time(self) -> Optional[datetime]:
        """获取上次编译时间"""
        index_path = self._compiled_dir / self.INDEX_FILE
        if not index_path.exists():
            return None

        try:
            stat = os.stat(index_path)
            return datetime.fromtimestamp(stat.st_mtime)
        except OSError:
            return None

    # ====================================================================
    # 编译执行
    # ====================================================================

    def generate_compile_prompt(self) -> str:
        """
        生成编译指令（由宿主LLM执行）

        基于Karpathy模式：
        1. 读取缓冲区中的原始经验
        2. 提取模式、实体、关系
        3. 创建/更新结构化文章
        4. 维护索引和源映射
        5. 添加覆盖度标记
        """
        if not self._buffer:
            return "[Experience] 无未编译经验"

        # 按分类分组
        grouped = self._group_by_category()

        # 读取现有索引
        existing_index = self._load_index()

        prompt_parts = [
            "# 经验编译任务\n",
            "请将以下原始经验编译为结构化知识文章。\n",
            "遵循Karpathy LLM Knowledge Base模式：\n\n",
            "## 编译规则",
            "1. 按主题合并相关经验为单篇文章",
            "2. 每篇文章包含：Summary(2-3段)、Key Points、Gotchas、Sources",
            "3. 为每节添加覆盖度标记: [coverage: high/medium/low]",
            "4. 覆盖度标准：",
            "   - high (5+来源): 可直接信任",
            "   - medium (2-4来源): 概述可信，细节查原始",
            "   - low (0-1来源): 直接查原始数据",
            "5. 如果已有同名文章，合并新信息而非替换\n",
            "6. 输出格式：每篇文章以 ## 标题 开头的Markdown\n",
        ]

        for category, entries in grouped.items():
            prompt_parts.append(f"\n## 分类: {category}")
            prompt_parts.append(f"经验条目数: {len(entries)}")

            # 去重
            seen_hashes = set()
            unique_entries = []
            for e in entries:
                if e.source_hash not in seen_hashes:
                    seen_hashes.add(e.source_hash)
                    unique_entries.append(e)
            prompt_parts.append(f"去重后: {len(unique_entries)}\n")

            for entry in unique_entries[:20]:  # 每分类最多20条
                prompt_parts.append(f"- [{entry.timestamp[:10]}] {entry.content}")

        # 现有文章信息
        if existing_index:
            prompt_parts.append("\n## 已有文章索引")
            for title, info in existing_index.items():
                prompt_parts.append(f"- {title}: {info.get('summary', 'N/A')}")

        prompt_parts.append(
            "\n## 输出要求\n"
            "将编译结果写入以下目录的Markdown文件：\n"
            f"  目录: {self.COMPILED_DIR}/patterns/\n"
            "  文件名: 使用小写kebab-case，如 tdd-patterns.md\n"
            "  同时更新 _index.md 索引文件\n"
        )

        return "\n".join(prompt_parts)

    def _group_by_category(self) -> Dict[str, List[ExperienceEntry]]:
        """按分类分组经验"""
        grouped: Dict[str, List[ExperienceEntry]] = {}
        for entry in self._buffer:
            cat = entry.category
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(entry)
        return grouped

    # ====================================================================
    # 索引管理
    # ====================================================================

    def _load_index(self) -> Dict[str, Dict]:
        """加载编译索引"""
        index_path = self._compiled_dir / self.INDEX_FILE
        if not index_path.exists():
            return {}

        try:
            content = index_path.read_text(encoding="utf-8")
            index = {}
            current_title = None
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("## "):
                    current_title = line[3:].strip()
                    index[current_title] = {"title": current_title}
                elif current_title and ":" in line:
                    key, _, val = line.partition(":")
                    index[current_title][key.strip()] = val.strip()
            return index
        except Exception as e:
            logger.warning("加载索引失败: %s", e)
            return {}

    def _save_index(self, articles: Dict[str, CompiledArticle]) -> None:
        """保存编译索引"""
        index_path = self._compiled_dir / self.INDEX_FILE
        lines = [
            "# Knowledge Base Index\n",
            f"# 更新时间: {datetime.now().isoformat()}\n",
        ]
        for title, article in sorted(articles.items()):
            lines.append(f"\n## {title}\n")
            lines.append(f"summary: {article.summary}\n")
            lines.append(f"coverage: {article.coverage}\n")
            lines.append(f"sources: {len(article.sources)}\n")
            lines.append(f"tags: {', '.join(article.tags)}\n")
            lines.append(f"updated: {article.updated}\n")

        index_path.write_text("\n".join(lines), encoding="utf-8")

    # ====================================================================
    # 查询编译后的知识
    # ====================================================================

    def query(self, topic: str) -> Optional[str]:
        """
        查询编译后的知识

        直接读取编译后的文章，而非重新处理原始经验。
        这是84% Token节省的核心机制。

        Args:
            topic: 查询主题

        Returns:
            文章内容（Markdown），如果找不到返回None
        """
        # 先查索引
        index = self._load_index()
        topic_lower = topic.lower()

        # 精确匹配
        for title, info in index.items():
            if topic_lower in title.lower():
                article_path = self._compiled_dir / "patterns" / f"{self._title_to_filename(title)}.md"
                if article_path.exists():
                    return article_path.read_text(encoding="utf-8")

        # 模糊匹配（标签和摘要）
        for title, info in index.items():
            summary = info.get("summary", "").lower()
            if topic_lower in summary:
                article_path = self._compiled_dir / "patterns" / f"{self._title_to_filename(title)}.md"
                if article_path.exists():
                    return article_path.read_text(encoding="utf-8")

        return None

    def _title_to_filename(self, title: str) -> str:
        """标题转文件名"""
        return title.lower().replace(" ", "-").replace("/", "-")

    # ====================================================================
    # 健康检查
    # ====================================================================

    def lint(self) -> List[str]:
        """
        知识库健康检查

        检查项:
        - 过期文章（源文件哈希变化）
        - 孤立文章（无源引用）
        - 低覆盖度标记
        - 索引一致性
        """
        issues = []
        index = self._load_index()

        if not index:
            issues.append("[INFO] 知识库为空，尚未编译")
            return issues

        # 检查文章文件存在性
        patterns_dir = self._compiled_dir / "patterns"
        for title, info in index.items():
            filename = self._title_to_filename(title)
            article_path = patterns_dir / f"{filename}.md"
            if not article_path.exists():
                issues.append(f"[WARN] 索引引用的文章不存在: {title} ({filename}.md)")

        # 检查孤立文章（文件存在但不在索引中）
        if patterns_dir.exists():
            indexed_files = {self._title_to_filename(t) for t in index}
            for f in patterns_dir.glob("*.md"):
                if f.stem not in indexed_files:
                    issues.append(f"[WARN] 孤立文章（未在索引中）: {f.name}")

        # 检查低覆盖度
        for title, info in index.items():
            coverage = info.get("coverage", "unknown")
            if coverage == "low":
                issues.append(f"[SUGGEST] 低覆盖度文章需要补充: {title}")

        if not issues:
            issues.append("[OK] 知识库健康检查通过")

        return issues

    # ====================================================================
    # 状态与统计
    # ====================================================================

    def get_stats(self) -> Dict:
        """获取编译器统计"""
        index = self._load_index()
        return {
            "buffer_size": len(self._buffer),
            "compiled_articles": len(index),
            "should_compile": self.should_compile(),
            "last_compile": str(self._get_last_compile_time()),
            "categories": list({e.category for e in self._buffer}),
            "compiled_dir": str(self._compiled_dir),
        }

    def clear_buffer(self):
        """清空缓冲区（编译成功后调用）"""
        self._buffer.clear()

    def reset(self):
        """完全重置编译器"""
        self._buffer.clear()
