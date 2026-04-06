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
"""

import hashlib
import json
import logging
import os
import sqlite3
import time
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
        """生成唯一文章ID"""
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

    枀久化架构:
    - SQLite 为主存储（experience_entries + compiled_articles + FTS5）
    - Markdown 为辅助备份（.quickagents/compiled/）
    - 查询优先从 SQLite FTS5 读取

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
            prompt = compiler.generate_compile_prompt()

        # 查询编译后的知识（优先走 SQLite FTS5）
        article = compiler.query('tdd-patterns')

    CLI:
        qka experience status      # 查看状态
        qka experience compile     # 触发编译
        qka experience query <topic> # 查询编译后的知识
    """

    # 配置
    COMPILE_TASK_THRESHOLD = 10
    COMPILE_DAYS_THRESHOLD = 7
    COMPILED_DIR = ".quickagents/compiled"
    INDEX_FILE = "_index.md"
    SOURCES_FILE = "_sources.md"

    # 覆盖度阈值
    COVERAGE_HIGH_THRESHOLD = 5
    COVERAGE_MEDIUM_THRESHOLD = 2

    def __init__(self, db_path: str = ".quickagents/unified.db"):
        self._db_path = db_path
        self._buffer: List[ExperienceEntry] = []
        self._compiled_dir = Path(self.COMPILED_DIR)
        self._ensure_dirs()
        self._init_db()

    # ====================================================================
    # 数据库初始化
    # ====================================================================

    def _ensure_dirs(self):
        """确保目录存在"""
        self._compiled_dir.mkdir(parents=True, exist_ok=True)
        (self._compiled_dir / "patterns").mkdir(exist_ok=True)

    def _init_db(self):
        """初始化数据库（创建表 + 执行迁移）"""
        conn = sqlite3.connect(self._db_path)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA foreign_keys=ON")
            self._ensure_tables(conn)
            conn.commit()
        finally:
            conn.close()

    def _ensure_tables(self, conn: sqlite3.Connection):
        """确保所有表存在"""
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

    def _get_conn(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    # ====================================================================
    # 积累经验 → SQLite 持久化
    # ====================================================================

    def accumulate(self, task_result: Dict) -> None:
        """
        积累任务经验到 SQLite（持久化，进程崩溃不丢失）

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
        source_hash = hashlib.md5(content.encode("utf-8")).hexdigest()[:8]
        full_hash = f"{source}:{source_hash}"

        # 写入内存缓冲
        entry = ExperienceEntry(
            source=source,
            category=category,
            content=content,
            source_hash=full_hash,
        )
        self._buffer.append(entry)

        # 写入 SQLite（持久化）
        try:
            conn = self._get_conn()
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO experience_entries (source, category, content, source_hash, is_compiled) VALUES (?, ?, ?, ?, 0)",
                    (source, category, content, full_hash),
                )
                conn.commit()
            finally:
                conn.close()
        except Exception as e:
            logger.warning("经验写入SQLite失败（仍在缓冲区）: %s", e)

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
        """
        检查是否需要编译

        优先检查 SQLite 中未编译的经验数量（跨进程安全）
        """
        try:
            conn = self._get_conn()
            try:
                cursor = conn.execute("SELECT COUNT(*) FROM experience_entries WHERE is_compiled = 0")
                uncompiled_count = cursor.fetchone()[0]
            finally:
                conn.close()
        except Exception:
            uncompiled_count = len(self._buffer)

        # 条件1: 未编译经验达到阈值
        if uncompiled_count >= self.COMPILE_TASK_THRESHOLD:
            return True

        # 条件2: 距上次编译超过阈值天数
        last_compile = self._get_last_compile_time()
        if last_compile is None:
            return uncompiled_count > 0

        days_since = (datetime.now() - last_compile).days
        return days_since >= self.COMPILE_DAYS_THRESHOLD and uncompiled_count > 0

    def _get_last_compile_time(self) -> Optional[datetime]:
        """获取上次编译时间（优先从 SQLite）"""
        # 优先从 SQLite 查询
        try:
            conn = self._get_conn()
            try:
                cursor = conn.execute("SELECT MAX(updated_at) FROM compiled_articles")
                row = cursor.fetchone()
                if row and row[0]:
                    return datetime.fromisoformat(row[0])
            finally:
                conn.close()
        except Exception:
            pass

        # 回退到文件检查
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
        1. 读取未编译经验（优先从SQLite）
        2. 提取模式、实体、关系
        3. 创建/更新结构化文章
        4. 维护索引和源映射
        5. 添加覆盖度标记
        """
        if not self.should_compile():
            return "[Experience] 无未编译经验"

        # 从 SQLite 读取未编译经验
        entries = self._load_uncompiled_entries()

        if not entries:
            return "[Experience] 无未编译经验"

        # 按分类分组
        grouped = self._group_entries(entries)

        # 读取已有文章索引（从 SQLite）
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

            # 去重
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

        # 已有文章信息
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
        """从 SQLite 加载未编译经验"""
        try:
            conn = self._get_conn()
            try:
                cursor = conn.execute(
                    "SELECT id, source, category, content, source_hash, created_at "
                    "FROM experience_entries WHERE is_compiled = 0 "
                    "ORDER BY created_at ASC LIMIT 100"
                )
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            finally:
                conn.close()
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
        """按分类分组经验"""
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
        """
        保存编译后的文章到 SQLite + FTS5

        Args:
            article: 编译后的文章
        """
        import uuid as _uuid

        article_id = article.article_id or str(_uuid.uuid4())
        now = datetime.now().isoformat()

        try:
            conn = self._get_conn()
            try:
                # 检查是否已存在（按标题去重）
                cursor = conn.execute(
                    "SELECT article_id FROM compiled_articles WHERE title = ?",
                    (article.title,),
                )
                existing = cursor.fetchone()

                if existing:
                    # 更新已有文章
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
                    # 更新 FTS5
                    conn.execute(
                        "INSERT INTO compiled_articles_fts(rowid, title, summary, body, tags) VALUES ((SELECT rowid FROM compiled_articles WHERE article_id = ?), ?, ?, ?, ?)",
                        (existing[0], article.title, article.summary, article.body, json.dumps(article.tags)),
                    )
                    article_id = existing[0]
                else:
                    # 新建文章
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
                    # 写入 FTS5
                    conn.execute(
                        "INSERT INTO compiled_articles_fts(title, summary, body, tags) VALUES (?, ?, ?, ?)",
                        (article.title, article.summary, article.body, json.dumps(article.tags)),
                    )

                # 标记原始经验为已编译
                conn.execute(
                    "UPDATE experience_entries SET is_compiled = 1 WHERE category = ? AND is_compiled = 0",
                    (self._infer_category({"skill": article.tags[0] if article.tags else ""}),),
                )
                conn.commit()

                # 同步到 Markdown 备份
                self._sync_article_to_md(article)

            finally:
                conn.close()
        except Exception as e:
            logger.error("保存编译文章失败: %s", e)
            raise

    def save_compile_result(self, articles: List[CompiledArticle]) -> CompileResult:
        """
        批量保存编译结果

        Args:
            articles: 编译后的文章列表

        Returns:
            CompileResult: 编译统计
        """
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
        """
        解析 LLM 编译输出为 CompiledArticle 列表

        期望格式:
            COMPILE_RESULT
            ARTICLE_START|title|summary|coverage
            ARTICLE_BODY|...
            ARTICLE_END
            COMPILE_RESULT_END
        """
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
                # 保存前一篇
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
        """从 SQLite 加载编译索引"""
        try:
            conn = self._get_conn()
            try:
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
            finally:
                conn.close()
        except Exception as e:
            logger.warning("从SQLite加载索引失败: %s", e)
            return self._load_index_from_md()

    def _load_index_from_md(self) -> Dict[str, Dict]:
        """从 Markdown 文件加载索引（回退方案）"""
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
        """
        查询编译后的知识（SQLite FTS5 优先，Markdown 回退）

        Args:
            topic: 查询主题

        Returns:
            文章内容（Markdown格式），如果找不到返回None
        """
        topic_lower = topic.lower()

        # 优先从 SQLite FTS5 搜索
        try:
            conn = self._get_conn()
            try:
                # FTS5 全文搜索
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
                    # 拼接结果为 Markdown
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
            finally:
                conn.close()
        except Exception as e:
            logger.warning("SQLite FTS5查询失败，回退到文件: %s", e)

        # 回退: 从 Markdown 文件读取
        return self._query_from_md(topic_lower)

    def _query_from_md(self, topic_lower: str) -> Optional[str]:
        """从 Markdown 文件查询（回退方案）"""
        index = self._load_index_from_md()

        # 精确匹配
        for title, info in index.items():
            if topic_lower in title.lower():
                article_path = self._compiled_dir / "patterns" / f"{self._title_to_filename(title)}.md"
                if article_path.exists():
                    return article_path.read_text(encoding="utf-8")

        # 模糊匹配
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
        """将编译后的文章同步到 Markdown 文件（辅助备份）"""
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

        # 更新索引文件
        self._sync_md_index()

    def _sync_md_index(self) -> None:
        """同步 Markdown 索引文件"""
        try:
            conn = self._get_conn()
            try:
                cursor = conn.execute(
                    "SELECT title, summary, coverage, updated_at FROM compiled_articles ORDER BY title"
                )
                rows = cursor.fetchall()
            finally:
                conn.close()
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
        """知识库健康检查"""
        issues = []

        try:
            conn = self._get_conn()
            try:
                # 检查未编译经验数
                cursor = conn.execute("SELECT COUNT(*) FROM experience_entries WHERE is_compiled = 0")
                uncompiled = cursor.fetchone()[0]
                if uncompiled > 0:
                    issues.append(f"[INFO] {uncompiled} 条未编译经验")

                # 检查低覆盖度文章
                cursor = conn.execute("SELECT title FROM compiled_articles WHERE coverage = 'low'")
                for row in cursor.fetchall():
                    issues.append(f"[SUGGEST] 低覆盖度文章需要补充: {row[0]}")

                # 检查 SQLite 与 Markdown 一致性
                cursor = conn.execute("SELECT COUNT(*) FROM compiled_articles")
                db_count = cursor.fetchone()[0]
                md_count = len(list((self._compiled_dir / "patterns").glob("*.md")))
                if db_count != md_count:
                    issues.append(f"[WARN] SQLite({db_count}) 与 Markdown({md_count}) 文章数不一致")

                # 检查 FTS5 完整性
                cursor = conn.execute("SELECT COUNT(*) FROM compiled_articles_fts")
                fts_count = cursor.fetchone()[0]
                if fts_count != db_count:
                    issues.append(f"[WARN] FTS5({fts_count}) 与文章表({db_count}) 记录数不一致")

                if not issues:
                    issues.append("[OK] 知识库健康检查通过")
            finally:
                conn.close()
        except Exception as e:
            issues.append(f"[ERROR] 健康检查失败: {e}")

        return issues

    # ====================================================================
    # 状态与统计
    # ====================================================================

    def get_stats(self) -> Dict:
        """获取编译器统计"""
        try:
            conn = self._get_conn()
            try:
                cursor = conn.execute("SELECT COUNT(*) FROM experience_entries")
                total_entries = cursor.fetchone()[0]
                cursor = conn.execute("SELECT COUNT(*) FROM experience_entries WHERE is_compiled = 0")
                uncompiled = cursor.fetchone()[0]
                cursor = conn.execute("SELECT COUNT(*) FROM compiled_articles")
                compiled_count = cursor.fetchone()[0]
            finally:
                conn.close()
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
        """清空缓冲区（编译成功后调用）"""
        self._buffer.clear()

    def reset(self):
        """完全重置编译器"""
        self._buffer.clear()
