"""
ExperienceCompiler - 经验编译器（Karpathy LLM Knowledge Base模式）

核心思路:
- 分散的任务经验 → LLM编译一次 → 结构化知识文章 → 后续直接查询编译后的文章
- 增量编译（哈希检测变化，只处理新增经验）
- 覆盖度标记（告诉LLM何时信任vs查原始数据）
- 阈值触发（默认每10条经验或7天触发编译）

数据流:
  任务完成 → accumulate(task_result) → SQLite experience_entries 表
                                                ↓ 达到阈值
                                         compile() → 增量编译
                                                ↓
                                    SQLite compiled_articles 表 (+ FTS5 索引)
                                    Markdown 同步备份 → .quickagents/compiled/

基于:
- llm-wiki-compiler (Karpathy模式): 383文件→13文章, 81x压缩, 84% Token节省
- arXiv:2601.21557 MCE: 批量级优化13.6x效率提升
- QuickAgents SkillEvolution: 已有进化系统增强

连接管理:
- 通过 ConnectionManager 管理数据库连接（连接池、线程安全、WAL）
- 表结构由 MigrationManager 004_experience_tables 迁移创建
- 支持 db_path（向后兼容）或 ConnectionManager（共享连接池）
"""

import hashlib
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)


def _get_connection_manager(conn_mgr_or_path: Union[str, "ConnectionManager"]) -> "ConnectionManager":
    from .connection_manager import ConnectionManager

    if isinstance(conn_mgr_or_path, ConnectionManager):
        return conn_mgr_or_path
    return ConnectionManager(str(conn_mgr_or_path))


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

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "category": self.category,
            "content": self.content,
            "timestamp": self.timestamp,
            "source_hash": self.source_hash,
        }


class CompiledArticle:
    """编译后的知识文章"""

    def __init__(
        self,
        title: str,
        summary: str,
        body: str,
        tags: List[str],
        sources: List[str],
        coverage: str = "medium",
        updated: Optional[str] = None,
        article_id: Optional[str] = None,
    ):
        self.title = title
        self.summary = summary
        self.body = body
        self.tags = tags
        self.sources = sources
        self.coverage = coverage
        self.updated = updated or datetime.now().isoformat()
        self.article_id = article_id or self._generate_id()

    def _generate_id(self) -> str:
        import uuid as _uuid

        return f"article-{_uuid.uuid4().hex[:12]}"

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "summary": self.summary,
            "body": self.body,
            "tags": json.dumps(self.tags, ensure_ascii=False),
            "sources": json.dumps(self.sources, ensure_ascii=False),
            "coverage": self.coverage,
            "updated": self.updated,
            "article_id": self.article_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CompiledArticle":
        return CompiledArticle(
            title=data["title"],
            summary=data.get("summary", ""),
            body=data.get("body", ""),
            tags=json.loads(data["tags"]) if isinstance(data.get("tags"), str) else data.get("tags", []),
            sources=json.loads(data["sources"]) if isinstance(data.get("sources"), str) else data.get("sources", []),
            coverage=data.get("coverage", "medium"),
            updated=data.get("updated"),
            article_id=data.get("article_id"),
        )


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
    - 增量编译：哈希检测变化
    - 覆盖度标记：告诉LLM何时信任

    持久化架构:
    - SQLite 为主存储（experience_entries + compiled_articles + FTS5）
    - 表由 MigrationManager 004 迁移自动创建
    - 连接由 ConnectionManager 统一管理
    - Markdown 为辅助备份（.quickagents/compiled/）

    使用方式:
        # 共享 ConnectionManager（推荐）
        compiler = ExperienceCompiler(conn_mgr)

        # 或传入 db_path（向后兼容，内部创建 ConnectionManager）
        compiler = ExperienceCompiler(db_path='.quickagents/unified.db')

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
            prompt = compiler.generate_compile_prompt()

        # 查询编译后的知识（优先走 SQLite FTS5）
        article = compiler.query('tdd-patterns')

    CLI:
        qka experience status      # 查看状态
        qka experience compile     # 触发编译
        qka experience query <topic> # 查询编译后的知识
    """

    COMPILE_TASK_THRESHOLD = 10
    COMPILE_DAYS_THRESHOLD = 7
    COMPILED_DIR = ".quickagents/compiled"
    INDEX_FILE = "_index.md"
    SOURCES_FILE = "_sources.md"

    COVERAGE_HIGH_THRESHOLD = 5
    COVERAGE_MEDIUM_THRESHOLD = 2

    def __init__(
        self,
        db_path: str = ".quickagents/unified.db",
        conn_mgr: Optional["ConnectionManager"] = None,
    ):
        self._conn_mgr = conn_mgr or _get_connection_manager(db_path)
        self._db_path = str(self._conn_mgr.db_path)
        self._buffer: List[ExperienceEntry] = []
        self._compiled_dir = Path(self.COMPILED_DIR)
        self._ensure_dirs()
        self._ensure_tables()

    def _ensure_dirs(self):
        self._compiled_dir.mkdir(parents=True, exist_ok=True)
        (self._compiled_dir / "patterns").mkdir(exist_ok=True)

    def _ensure_tables(self):
        with self._conn_mgr.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS experience_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    category TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source_hash TEXT NOT NULL,
                    is_compiled INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT (strftime('%s', 'now')),
                    UNIQUE(source_hash)
                );

                CREATE INDEX IF NOT EXISTS idx_exp_entry_category ON experience_entries(category);
                CREATE INDEX IF NOT EXISTS idx_exp_entry_compiled ON experience_entries(is_compiled);
                CREATE INDEX IF NOT EXISTS idx_exp_entry_time ON experience_entries(created_at);

                CREATE TABLE IF NOT EXISTS compiled_articles (
                    article_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    body TEXT NOT NULL,
                    tags TEXT DEFAULT '[]',
                    sources TEXT DEFAULT '[]',
                    coverage TEXT DEFAULT 'medium',
                    compiled_from TEXT DEFAULT '[]',
                    source_hash TEXT,
                    created_at TEXT DEFAULT (strftime('%s', 'now')),
                    updated_at TEXT DEFAULT (strftime('%s', 'now'))
                );

                CREATE INDEX IF NOT EXISTS idx_compiled_coverage ON compiled_articles(coverage);
                CREATE INDEX IF NOT EXISTS idx_compiled_updated ON compiled_articles(updated_at);

                CREATE VIRTUAL TABLE IF NOT EXISTS compiled_articles_fts USING fts5(
                    title,
                    summary,
                    body,
                    tags
                );
            """)

    # ====================================================================
    # 积累经验 → SQLite 持久化
    # ====================================================================

    def accumulate(self, task_result: Dict) -> None:
        source = task_result.get("task_id", "unknown")
        category = task_result.get("category", self._infer_category(task_result))
        content = self._serialize_experience(task_result)
        source_hash = hashlib.md5(content.encode("utf-8")).hexdigest()[:8]
        full_hash = f"{source}:{source_hash}"

        entry = ExperienceEntry(
            source=source,
            category=category,
            content=content,
            source_hash=full_hash,
        )
        self._buffer.append(entry)

        try:
            with self._conn_mgr.get_connection() as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO experience_entries (source, category, content, source_hash, is_compiled) VALUES (?, ?, ?, ?, 0)",
                    (source, category, content, full_hash),
                )
        except Exception as e:
            logger.warning("经验写入SQLite失败（仍在缓冲区）: %s", e)

        logger.debug(
            "积累经验: source=%s, category=%s, buffer=%d",
            source,
            category,
            len(self._buffer),
        )

    def _infer_category(self, task_result: Dict) -> str:
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
        try:
            with self._conn_mgr.get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM experience_entries WHERE is_compiled = 0")
                uncompiled_count = cursor.fetchone()[0]
        except Exception:
            uncompiled_count = len(self._buffer)

        if uncompiled_count >= self.COMPILE_TASK_THRESHOLD:
            return True

        last_compile = self._get_last_compile_time()
        if last_compile is None:
            return uncompiled_count > 0

        days_since = (datetime.now() - last_compile).days
        return days_since >= self.COMPILE_DAYS_THRESHOLD and uncompiled_count > 0

    def _get_last_compile_time(self) -> Optional[datetime]:
        try:
            with self._conn_mgr.get_connection() as conn:
                cursor = conn.execute("SELECT MAX(updated_at) FROM compiled_articles")
                row = cursor.fetchone()
                if row and row[0]:
                    return datetime.fromisoformat(row[0])
        except Exception:
            pass

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
        if not self.should_compile():
            return "[Experience] 无未编译经验"

        entries = self._load_uncompiled_entries()

        if not entries:
            return "[Experience] 无未编译经验"

        grouped = self._group_entries(entries)

        existing_articles = self._load_compiled_index()

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

        for category, cat_entries in grouped.items():
            prompt_parts.append(f"\n## 分类: {category}")
            prompt_parts.append(f"经验条目数: {len(cat_entries)}")

            seen = set()
            unique = []
            for e in cat_entries:
                key = e.get("source_hash") or e.get("source", "")
                if key not in seen:
                    seen.add(key)
                    unique.append(e)
            prompt_parts.append(f"去重后: {len(unique)}\n")

            for entry in unique[:20]:
                content = entry.get("content", "")
                ts = entry.get("created_at", "")[:10] if entry.get("created_at") else ""
                prompt_parts.append(f"- [{ts}] {content}")

        if existing_articles:
            prompt_parts.append("\n## 已有文章索引")
            for title, info in existing_articles.items():
                prompt_parts.append(f"- {title}: {info.get('summary', 'N/A')}")

        prompt_parts.append(
            "\n## 输出要求\n"
            "请输出编译结果，格式如下：\n\n"
            "```\n"
            "COMPILE_RESULT\n"
            "ARTICLE_START|title|summary|coverage\n"
            "ARTICLE_BODY|...\n"
            "ARTICLE_END\n"
            "ARTICLE_START|title2|summary2|coverage2\n"
            "ARTICLE_BODY|...\n"
            "ARTICLE_END\n"
            "COMPILE_RESULT_END\n"
            "```\n"
        )

        return "\n".join(prompt_parts)

    def _load_uncompiled_entries(self) -> List[Dict]:
        try:
            with self._conn_mgr.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT id, source, category, content, source_hash, created_at "
                    "FROM experience_entries WHERE is_compiled = 0 "
                    "ORDER BY created_at ASC LIMIT 100"
                )
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            logger.warning("从SQLite加载未编译经验失败: %s", e)
            return [
                {
                    "source": e.source,
                    "category": e.category,
                    "content": e.content,
                    "source_hash": e.source_hash,
                    "created_at": e.timestamp,
                }
                for e in self._buffer
            ]

    def _group_entries(self, entries: List[Dict]) -> Dict[str, List[Dict]]:
        grouped: Dict[str, List[Dict]] = {}
        for entry in entries:
            cat = entry.get("category", "general-patterns")
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(entry)
        return grouped

    # ====================================================================
    # 编译结果回写 → SQLite + FTS5
    # ====================================================================

    def save_compiled_article(self, article: CompiledArticle) -> None:
        import uuid as _uuid

        article_id = article.article_id or str(_uuid.uuid4())
        now = datetime.now().isoformat()

        try:
            with self._conn_mgr.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT article_id FROM compiled_articles WHERE title = ?",
                    (article.title,),
                )
                existing = cursor.fetchone()

                if existing:
                    conn.execute(
                        """UPDATE compiled_articles
                        SET summary = ?, body = ?, tags = ?, sources = ?,
                            coverage = ?, updated_at = ?
                        WHERE article_id = ?""",
                        (
                            article.summary,
                            article.body,
                            json.dumps(article.tags, ensure_ascii=False),
                            json.dumps(article.sources, ensure_ascii=False),
                            article.coverage,
                            now,
                            existing[0],
                        ),
                    )
                    conn.execute(
                        "INSERT INTO compiled_articles_fts(rowid, title, summary, body, tags) VALUES ((SELECT rowid FROM compiled_articles WHERE article_id = ?), ?, ?, ?, ?)",
                        (existing[0], article.title, article.summary, article.body, json.dumps(article.tags)),
                    )
                    article_id = existing[0]
                else:
                    source_hash = hashlib.md5((article.title + article.body).encode("utf-8")).hexdigest()[:8]
                    conn.execute(
                        """INSERT INTO compiled_articles
                        (article_id, title, summary, body, tags, sources, coverage, source_hash, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            article_id,
                            article.title,
                            article.summary,
                            article.body,
                            json.dumps(article.tags, ensure_ascii=False),
                            json.dumps(article.sources, ensure_ascii=False),
                            article.coverage,
                            source_hash,
                            now,
                            now,
                        ),
                    )
                    conn.execute(
                        "INSERT INTO compiled_articles_fts(title, summary, body, tags) VALUES (?, ?, ?, ?)",
                        (article.title, article.summary, article.body, json.dumps(article.tags)),
                    )

                conn.execute(
                    "UPDATE experience_entries SET is_compiled = 1 WHERE category = ? AND is_compiled = 0",
                    (self._infer_category({"skill": article.tags[0] if article.tags else ""}),),
                )

            self._sync_article_to_md(article)

        except Exception as e:
            logger.error("保存编译文章失败: %s", e)
            raise

    def save_compile_result(self, articles: List[CompiledArticle]) -> CompileResult:
        result = CompileResult()
        start = time.monotonic()

        for article in articles:
            try:
                self.save_compiled_article(article)
                result.experiences_processed += 1
            except Exception as e:
                logger.warning("保存文章失败 '%s': %s", article.title, e)
                result.experiences_skipped += 1

        result.duration_ms = (time.monotonic() - start) * 1000
        self._buffer.clear()
        return result

    def parse_compile_output(self, raw_output: str) -> List[CompiledArticle]:
        articles = []
        in_result = False
        current_title = None
        current_summary = None
        current_coverage = "medium"
        current_body_lines: List[str] = []

        for line in raw_output.split("\n"):
            stripped = line.strip()
            if stripped == "COMPILE_RESULT":
                in_result = True
                continue
            if stripped == "COMPILE_RESULT_END":
                in_result = False
                continue

            if not in_result:
                continue

            if stripped.startswith("ARTICLE_START|"):
                if current_title:
                    articles.append(
                        CompiledArticle(
                            title=current_title,
                            summary=current_summary or "",
                            body="\n".join(current_body_lines),
                            tags=[self._infer_category({"skill": current_title})],
                            sources=[],
                            coverage=current_coverage,
                        )
                    )
                parts = stripped[len("ARTICLE_START|") :].split("|")
                current_title = parts[0] if parts else "Untitled"
                current_summary = parts[1] if len(parts) > 1 else ""
                current_coverage = parts[2] if len(parts) > 2 else "medium"
                current_body_lines = []
                continue

            if stripped == "ARTICLE_END":
                if current_title:
                    articles.append(
                        CompiledArticle(
                            title=current_title,
                            summary=current_summary or "",
                            body="\n".join(current_body_lines),
                            tags=[self._infer_category({"skill": current_title})],
                            sources=[],
                            coverage=current_coverage,
                        )
                    )
                current_title = None
                current_body_lines = []
                continue

            current_body_lines.append(line)

        return articles

    # ====================================================================
    # SQLite 查询 → FTS5 优先
    # ====================================================================

    def _load_compiled_index(self) -> Dict[str, Dict]:
        try:
            with self._conn_mgr.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT title, summary, coverage, tags, updated_at FROM compiled_articles ORDER BY updated_at DESC"
                )
                index = {}
                for row in cursor.fetchall():
                    title = row[0]
                    index[title] = {
                        "summary": row[1],
                        "coverage": row[2],
                        "tags": json.loads(row[3]) if row[3] else [],
                        "updated": row[4],
                    }
                return index
        except Exception as e:
            logger.warning("从SQLite加载索引失败: %s", e)
            return self._load_index_from_md()

    def _load_index_from_md(self) -> Dict[str, Dict]:
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
            logger.warning("加载Markdown索引失败: %s", e)
            return {}

    # ====================================================================
    # 查询 → SQLite FTS5 优先
    # ====================================================================

    def query(self, topic: str) -> Optional[str]:
        topic_lower = topic.lower()

        try:
            with self._conn_mgr.get_connection() as conn:
                cursor = conn.execute(
                    """SELECT ca.title, ca.summary, ca.body, ca.tags, ca.coverage, ca.sources
                    FROM compiled_articles_fts fts
                    JOIN compiled_articles ca ON fts.rowid = ca.rowid
                    WHERE compiled_articles_fts MATCH ?
                    ORDER BY rank
                    LIMIT 5""",
                    (topic_lower,),
                )
                rows = cursor.fetchall()
                if rows:
                    parts = []
                    for row in rows:
                        title, summary, body, tags_json, coverage, sources_json = row
                        tags = json.loads(tags_json) if tags_json else []
                        parts.append(f"## {title}\n")
                        parts.append(f"> 覆盖度: {coverage}\n")
                        parts.append(f"> 标签: {', '.join(tags)}\n\n")
                        parts.append(f"### 摘要\n{summary}\n\n")
                        parts.append(body)
                        parts.append("\n---\n")
                    return "\n".join(parts)
        except Exception as e:
            logger.warning("SQLite FTS5查询失败，回退到文件: %s", e)

        return self._query_from_md(topic_lower)

    def _query_from_md(self, topic_lower: str) -> Optional[str]:
        index = self._load_index_from_md()

        for title, info in index.items():
            if topic_lower in title.lower():
                article_path = self._compiled_dir / "patterns" / f"{self._title_to_filename(title)}.md"
                if article_path.exists():
                    return article_path.read_text(encoding="utf-8")

        for title, info in index.items():
            summary = info.get("summary", "").lower()
            if topic_lower in summary:
                article_path = self._compiled_dir / "patterns" / f"{self._title_to_filename(title)}.md"
                if article_path.exists():
                    return article_path.read_text(encoding="utf-8")

        return None

    def _title_to_filename(self, title: str) -> str:
        return title.lower().replace(" ", "-").replace("/", "-")

    # ====================================================================
    # Markdown 同步备份
    # ====================================================================

    def _sync_article_to_md(self, article: CompiledArticle) -> None:
        patterns_dir = self._compiled_dir / "patterns"
        patterns_dir.mkdir(exist_ok=True)

        filename = self._title_to_filename(article.title)
        md_path = patterns_dir / f"{filename}.md"

        md_content = f"""# {article.title}

> 覆盖度: {article.coverage}
> 标签: {", ".join(article.tags)}
> 更新时间: {article.updated}

## 摘要

{article.summary}

## 正文

{article.body}

## 来源

{chr(10).join(f"- {s}" for s in article.sources)}
"""
        md_path.write_text(md_content, encoding="utf-8")

        self._sync_md_index()

    def _sync_md_index(self) -> None:
        try:
            with self._conn_mgr.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT title, summary, coverage, updated_at FROM compiled_articles ORDER BY title"
                )
                rows = cursor.fetchall()
        except Exception:
            return

        lines = [
            "# Knowledge Base Index\n",
            f"# 更新时间: {datetime.now().isoformat()}\n",
        ]
        for title, summary, coverage, updated in rows:
            lines.append(f"\n## {title}\n")
            lines.append(f"summary: {summary}\n")
            lines.append(f"coverage: {coverage}\n")
            lines.append(f"updated: {updated}\n")

        index_path = self._compiled_dir / self.INDEX_FILE
        index_path.write_text("\n".join(lines), encoding="utf-8")

    # ====================================================================
    # 健康检查
    # ====================================================================

    def lint(self) -> List[str]:
        issues = []

        try:
            with self._conn_mgr.get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM experience_entries WHERE is_compiled = 0")
                uncompiled = cursor.fetchone()[0]
                if uncompiled > 0:
                    issues.append(f"[INFO] {uncompiled} 条未编译经验")

                cursor = conn.execute("SELECT title FROM compiled_articles WHERE coverage = 'low'")
                for row in cursor.fetchall():
                    issues.append(f"[SUGGEST] 低覆盖度文章需要补充: {row[0]}")

                cursor = conn.execute("SELECT COUNT(*) FROM compiled_articles")
                db_count = cursor.fetchone()[0]
                md_count = len(list((self._compiled_dir / "patterns").glob("*.md")))
                if db_count != md_count:
                    issues.append(f"[WARN] SQLite({db_count}) 与 Markdown({md_count}) 文章数不一致")

                cursor = conn.execute("SELECT COUNT(*) FROM compiled_articles_fts")
                fts_count = cursor.fetchone()[0]
                if fts_count != db_count:
                    issues.append(f"[WARN] FTS5({fts_count}) 与文章表({db_count}) 记录数不一致")

                if not issues:
                    issues.append("[OK] 知识库健康检查通过")
        except Exception as e:
            issues.append(f"[ERROR] 健康检查失败: {e}")

        return issues

    # ====================================================================
    # 状态与统计
    # ====================================================================

    def get_stats(self) -> Dict:
        try:
            with self._conn_mgr.get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM experience_entries")
                total_entries = cursor.fetchone()[0]
                cursor = conn.execute("SELECT COUNT(*) FROM experience_entries WHERE is_compiled = 0")
                uncompiled = cursor.fetchone()[0]
                cursor = conn.execute("SELECT COUNT(*) FROM compiled_articles")
                compiled_count = cursor.fetchone()[0]
        except Exception:
            total_entries = len(self._buffer)
            uncompiled = len(self._buffer)
            compiled_count = 0

        return {
            "buffer_size": len(self._buffer),
            "total_entries": total_entries,
            "uncompiled_entries": uncompiled,
            "compiled_articles": compiled_count,
            "should_compile": self.should_compile(),
            "last_compile": str(self._get_last_compile_time()),
            "categories": list({e.category for e in self._buffer}),
            "compiled_dir": str(self._compiled_dir),
        }

    def clear_buffer(self):
        self._buffer.clear()

    def reset(self):
        self._buffer.clear()
