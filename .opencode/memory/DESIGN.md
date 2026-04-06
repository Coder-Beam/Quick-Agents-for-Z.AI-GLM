# 设计文档 (DESIGN.md)

> QuickAgents v2.9.0 系统设计文档
> 产品化改造进行中 → v2.10.0

---

## 1. 背景与目标

### 1.1 项目背景

QuickAgents 是一个 AI 代理增强工具包（Python 包），通过本地处理最大化效率、最小化 LLM Token 消耗。它为 AI 编码代理（如 OpenCode、Claude Code）提供持久化记忆、知识图谱、文档理解、循环检测、自我进化等核心能力，所有计算在本地完成（0 Token）。

### 1.2 业务目标

| 目标 | 指标 | 目标值 |
|------|------|--------|
| Token 节省 | 减少不必要的 API 调用 | 60-100% |
| 跨会话连续性 | 项目上下文保持 | 100% 可恢复 |
| 代码质量 | mypy/ruff 错误 | 0 |
| 测试覆盖 | 自动化测试通过率 | 100% (907+ tests) |
| 自主循环 | YuGong 全自动执行 | 需求→完整项目 |

### 1.3 技术目标

| 目标 | 说明 |
|------|------|
| 性能 | SQLite WAL 模式、批量查询、并行同步 |
| 可扩展性 | 分层架构（Facade → Session → Repository → Core） |
| 可维护性 | 模块化设计，每个模块职责单一 |
| 跨平台 | Windows/macOS/Linux 统一 UTF-8 编码 |

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         QuickAgents v2.9.0                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │                    CLI Layer (qka)                           │     │
│  │  stats / sync / memory / tasks / evolution / hooks / tdd    │     │
│  │  yugong start / resume / report / config                    │     │
│  └─────────────────────────────────────────────────────────────┘     │
│                              │                                       │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │                 Python API (Facade)                          │     │
│  │  UnifiedDB │ KnowledgeGraph │ SkillEvolution │ Browser      │     │
│  │  YuGongLoop │ AgentExecutor │ ReportGenerator              │     │
│  └─────────────────────────────────────────────────────────────┘     │
│                              │                                       │
│  ┌──────────────┬──────────────┬──────────────┬────────────────┐     │
│  │    Core      │  YuGong      │  Knowledge   │  Document      │     │
│  │  Layer       │  Engine      │  Graph       │  Pipeline      │     │
│  ├──────────────┼──────────────┼──────────────┼────────────────┤     │
│  │ Session      │ YuGongLoop   │ KG Facade    │ Pipeline       │     │
│  │ ConnMgr      │ AgentExec    │ Searcher     │ 7 Parsers      │     │
│  │ TxMgr        │ LLMClient    │ Storage      │ Extractors     │     │
│  │ MigrationMgr │ ToolExec     │ FTS5 Index   │ Matching       │     │
│  │ Repos        │ YuGongDB     │ Types        │ Validators     │     │
│  │ MarkdownSync │ ReportGen    │              │                │     │
│  └──────────────┴──────────────┴──────────────┴────────────────┘     │
│                              │                                       │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │                  Storage Layer                               │     │
│  │  SQLite (WAL mode) ──sync──> Markdown (.md files)           │     │
│  └─────────────────────────────────────────────────────────────┘     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 模块划分

| 模块名称 | 职责 | 依赖模块 |
|----------|------|----------|
| `core/` | 数据库核心（连接、事务、迁移、仓库、同步） | sqlite3 |
| `knowledge_graph/` | 知识图谱（节点、边、搜索、FTS5） | core/ |
| `document/` | 文档管道（解析、匹配、验证、提取） | knowledge_graph/ |
| `browser/` | 浏览器自动化（Playwright） | playwright |
| `cli/` | CLI 工具（qka 命令行） | core/, knowledge_graph/ |
| `skills/` | TDD/Git/反馈等技能模块 | core/ |
| `yugong/` | 愚公自主循环引擎（LLM客户端、Agent、工具执行） | httpx |
| `utils/` | 编码、编辑器、同步冲突 | - |
| `yugong/` | 愚公自主循环引擎（需求→项目全自动） | llm_client, tool_executor, db |
| `audit/` | 审计问责（CodeAudit + QualityGate + Accountability） | core/ |

### 2.3 技术选型

| 层级 | 技术选择 | 选择理由 |
|------|----------|----------|
| 语言 | Python 3.9+ | AI 生态兼容、SQLite 内置 |
| 主存储 | SQLite (WAL mode) | 零部署、高性能本地数据库 |
| 辅助存储 | Markdown | 人类可读、Git 版本控制 |
| 文档解析 | PyMuPDF + python-docx + openpyxl | 行业标准库 |
| 知识搜索 | FTS5 | SQLite 内置全文搜索 |
| 浏览器 | Playwright | 跨浏览器自动化标准 |
| 代码分析 | ast + tree-sitter (optional) | Python 内置 + 多语言支持 |

---

## 3. 数据模型

### 3.1 核心实体关系

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Memory  │     │   Task   │     │ Progress │     │ Feedback │
│          │     │          │     │          │     │          │
│ key (PK) │     │ id (PK)  │     │ project  │     │ id (PK)  │
│ value    │     │ name     │     │ total    │     │ type     │
│ type     │     │ priority │     │ current  │     │ title    │
│ category │     │ status   │     │ completed│     │ desc     │
│ created  │     │ assignee │     │          │     │ created  │
│ updated  │     │          │     │          │     │          │
└──────────┘     └──────────┘     └──────────┘     └──────────┘

┌──────────┐     ┌──────────┐
│  KGNode  │────<│  KGEdge  │
│          │     │          │
│ id (PK)  │     │ id (PK)  │
│ type     │     │ source   │
│ title    │     │ target   │
│ content  │     │ type     │
│ metadata │     │ weight   │
└──────────┘     └──────────┘
```

### 3.2 SQLite 表结构

| 表名 | 功能 | 核心字段 |
|------|------|----------|
| `memory` | 三维记忆 | key, value, memory_type, category |
| `tasks` | 任务管理 | id, name, priority, status |
| `progress` | 进度追踪 | project_id, total_tasks, completed_tasks |
| `feedback` | 经验收集 | id, type, title, description |
| `decisions` | 决策日志 | id, title, decision, alternatives |
| `kg_nodes` | 知识节点 | id, node_type, title, content |
| `kg_edges` | 知识关系 | id, source_id, target_id, edge_type |
| `file_cache` | 文件缓存 | path, hash, content |
| `operation_history` | 操作历史 | id, operation, timestamp |

### 3.3 存储方案

| 数据类型 | 存储方式 | 说明 |
|----------|----------|------|
| 结构化数据 | SQLite (unified.db) | 主存储，高性能查询 |
| 全文索引 | SQLite FTS5 | 知识图谱搜索 |
| 人类可读备份 | Markdown | MEMORY.md, TASKS.md, DECISIONS.md |
| 文件缓存 | SQLite (cache.db) | 哈希检测，避免重复读取 |

---

## 4. API 设计

### 4.1 Python API (核心入口)

```python
from quickagents import UnifiedDB, MemoryType, TaskStatus, KnowledgeGraph

# UnifiedDB — 统一数据库
db = UnifiedDB('.quickagents/unified.db')
db.set_memory('key', 'value', MemoryType.FACTUAL)
db.get_memory('key')
db.search_memory('query')
db.add_task('T001', '任务名', 'P0')
db.get_all_memories()  # v2.8.3 批量获取

# KnowledgeGraph — 知识图谱
kg = KnowledgeGraph()
kg.create_node(node_type, title, content)
kg.create_edge(source_id, target_id, edge_type)
kg.search('query')
kg.close()  # v2.8.3 资源清理

# MarkdownSync — 同步
from quickagents import MarkdownSync
sync = MarkdownSync(db)
sync.sync_all()  # v2.8.3 并行同步
```

### 4.2 CLI API (qka 命令)

| 命令 | 功能 |
|------|------|
| `qka stats` | 数据库统计 |
| `qka sync` | 同步到 Markdown |
| `qka memory get/set/search` | 记忆操作 |
| `qka tasks list/add/status` | 任务管理 |
| `qka import PALs/` | 文档导入 |
| `qka yugong start <req>` | 启动愚公自主循环 |
| `qka yugong resume` | 从DB恢复继续执行 |
| `qka yugong report` | 生成执行报告(MD+JSON) |
| `qka yugong config` | 初始化/查看配置 |
| `qka evolution status/stats` | 进化系统 |
| `qka hooks install/status` | Git 钩子 |

---

## 5. 性能方案

### 5.1 性能目标

| 指标 | 目标值 | 实际值 (v2.8.3) |
|------|--------|-----------------|
| 单次读取 QPS | > 10,000 | 16,679 |
| 批量写入 QPS | > 5,000 | 5,200-7,096 |
| 连接池命中率 | > 95% | 100% |
| 知识图谱批量查询 | O(1) queries | 2 queries (fixed) |

### 5.2 优化策略

| 策略 | 说明 | 适用场景 |
|------|------|----------|
| WAL 模式 | 读写并发，无锁 | SQLite 全局 |
| 批量 SQL | 2N+M queries → 2 queries | KnowledgeGraph `_expand_relations` |
| 并行同步 | ThreadPoolExecutor (3 workers) | MarkdownSync `sync_all` |
| 批量读取 | 1 query + Python grouping | MarkdownSync `sync_memory` |
| 内存映射 | mmap_size=64MB | SQLite PRAGMA |
| 持久连接 | Thread-local 连接复用 | KnowledgeGraph Storage |

### 5.3 监控方案

| 监控类型 | 方式 | 指标 |
|----------|------|------|
| 连接池 | PoolMetrics dataclass | hit_rate, avg_wait_ms, created/reused/evicted |
| 性能基准 | tests/benchmark_performance.py | QPS, pool hit rate, WAL growth |
| 测试覆盖 | pytest --cov | 行覆盖率 |

---

## 6. 质量门禁

### 6.1 静态分析

| 工具 | 状态 | 说明 |
|------|------|------|
| ruff (E,W,F) | 0 errors | line-length=120 |
| mypy --ignore-missing-imports | 0 errors | Optional[] + type: ignore |

### 6.2 测试

| 测试类型 | 数量 | 通过率 |
|----------|------|--------|
| 全部测试 | 907 | 100% (242 yugong) |
| 文档模块 | 340 | 100% |
| 知识图谱 | 204 | 100% |
| YuGong模块 | 242 | 100% |

---

## 7. 风险分析

### 7.1 技术风险

| 风险 | 可能性 | 影响 | 应对措施 |
|------|--------|------|----------|
| SQLite 并发锁 | 低 | 中 | WAL 模式 + busy_timeout=5000 |
| 磁盘空间不足 | 低 | 高 | WAL auto-checkpoint (1000 ops) |
| 跨平台编码问题 | 中 | 中 | 统一 UTF-8 编码模块 |
| 依赖冲突 | 低 | 中 | 可选依赖组 [document]/[source-code] |

### 7.2 应对预案

| 预案名称 | 触发条件 | 处理步骤 |
|----------|----------|----------|
| SQLite 恢复 | 数据库损坏 | MarkdownSync.restore_all_from_md() |
| 连接泄漏 | 连接数异常增长 | close() + __del__ 双重保障 |
| 内存溢出 | 大文件缓存 | FileManager hash 检测 + TTL |

---

## 8. 附录

### 8.1 术语表

| 术语 | 定义 |
|------|------|
| UnifiedDB | 统一数据库门面类 |
| FTS5 | SQLite 全文搜索扩展 |
| WAL | Write-Ahead Logging，SQLite 并发模式 |
| KnowledgeGraph | 知识图谱，节点+边+FTS5搜索 |
| MarkdownSync | SQLite → Markdown 双向同步 |
| DocumentPipeline | 三层文档处理管道（解析→验证→提取） |

### 8.2 参考文档

- [AGENTS.md](../AGENTS.md) - 开发规范
- [ARCHITECTURE.md](./ARCHITECTURE.md) - 系统架构
- [API_REFERENCE.md](./API_REFERENCE.md) - API 参考
- [INDEX.md](./INDEX.md) - 知识图谱索引
- [CHANGELOG.md](../CHANGELOG.md) - 变更日志

---

*最后更新: 2026-04-06 | v2.9.0 (产品化改造中 → v2.10.0)*
