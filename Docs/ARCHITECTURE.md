# QuickAgents 系统架构

> 本文档详细介绍QuickAgents的系统架构、设计理念和核心组件

---

## 目录

- [概述](#概述)
- [设计理念](#设计理念)
- [核心组件](#核心组件)
- [目录结构](#目录结构)
- [配置系统](#配置系统)
- [数据流](#数据流)
- [代理系统](#代理系统)
- [技能系统](#技能系统)
- [记忆系统](#记忆系统)

---

## 概述

QuickAgents是一个完整的AI代理增强工具包（Python 包），通过本地处理最大化效率、最小化 Token 消耗。核心能力包括：

- **统一数据库 (UnifiedDB V2)**: 分层架构，SQLite 主存储 + Markdown 辅助备份
- **知识图谱 (KnowledgeGraph)**: 节点+边+FTS5 全文搜索，WAL 模式优化
- **文档管道 (DocumentPipeline)**: 三层管道（解析→验证→提取），支持 7 种格式
- **17个专业代理**: 覆盖项目初始化、开发、测试、部署全流程
- **22个专项技能**: 提供记忆管理、进度追踪、代码分析等核心能力
- **三维记忆系统**: 基于《Memory in the Age of AI Agents》论文的 Factual/Experiential/Working 记忆架构
- **580 测试**: 100% 通过率，mypy/ruff 0 错误

---

## 设计理念

### 1. 零假设原则

绝对不脑补、不假设任何未被用户明确确认的需求细节、业务场景、约束条件与成功标准。

### 2. 需求本质优先

永远先追问「为什么做」，再讨论「做什么」，最后才谈「怎么做」。

### 3. 全链路风险前置

对任何需求与方案，第一时间识别技术风险、业务风险、合规风险、运维风险、成本风险。

### 4. 绝不替用户决策

只提供专业的技术方案、风险评估与备选方案，绝对不替用户做任何业务决策。

### 5. 三维记忆驱动

基于论文《Memory in the Age of AI Agents》设计，支持跨会话状态恢复和知识积累。

---

## 核心组件

```
┌─────────────────────────────────────────────────────────────────┐
│                        QuickAgents 系统                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Agents    │  │   Skills    │  │  Commands   │              │
│  │   17个代理   │  │   12个技能   │  │   6个命令   │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         └────────────────┼────────────────┘                      │
│                          │                                       │
│                          ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Orchestration Layer                     │  │
│  │                  (fenghou-orchestrate)                     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                          │                                       │
│                          ▼                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Memory    │  │   Config    │  │   Hooks     │              │
│  │   记忆系统   │  │   配置系统   │  │   钩子系统   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 目录结构

```
QuickAgents/
├── AGENTS.md                    # 开发规范（核心文件）
│
├── .opencode/                   # OpenCode配置目录
│   │
│   ├── agents/                  # 代理配置（17个）
│   │   ├── README.md
│   │   ├── yinglong-init.md     # 项目初始化
│   │   ├── boyi-consult.md      # 需求分析
│   │   ├── chisongzi-advise.md  # 技术推荐
│   │   ├── cangjie-doc.md       # 文档管理
│   │   ├── huodi-skill.md       # Skill管理
│   │   ├── fenghou-orchestrate.md # 主调度器
│   │   ├── fenghou-plan.md      # 规划器
│   │   ├── jianming-review.md   # 代码审查
│   │   ├── lishou-test.md       # 测试执行
│   │   ├── mengzhang-security.md # 安全审计
│   │   ├── hengge-perf.md       # 性能分析
│   │   ├── kuafu-debug.md       # 调试代理
│   │   ├── gonggu-refactor.md   # 重构代理
│   │   ├── huodi-deps.md        # 依赖管理
│   │   └── hengge-cicd.md       # CI/CD管理
│   │
│   ├── skills/                  # 技能配置（12个）
│   │   ├── EVOLUTION.md         # 技能进化记录
│   │   ├── registry.json        # 技能注册表
│   │   ├── project-memory-skill/
│   │   ├── boulder-tracking-skill/
│   │   ├── category-system-skill/
│   │   ├── inquiry-skill/
│   │   ├── tdd-workflow-skill/
│   │   ├── code-review-skill/
│   │   ├── git-commit-skill/
│   │   ├── multi-model-skill/
│   │   ├── lsp-ast-skill/
│   │   ├── project-detector-skill/
│   │   ├── background-agents-skill/
│   │   └── skill-integration-skill/
│   │
│   ├── commands/                # 命令配置（6个）
│   │   ├── README.md
│   │   ├── start-work.md
│   │   ├── ultrawork.md
│   │   ├── run-workflow.md
│   │   ├── enable-coordination.md
│   │   └── disable-coordination.md
│   │
│   ├── hooks/                   # 钩子配置
│   │   ├── README.md
│   │   └── todo-continuation-enforcer.md
│   │
│   ├── config/                  # 配置文件
│   │   ├── quickagents.json     # QuickAgents配置
│   │   ├── categories.json      # 任务分类配置
│   │   └── lsp-config.json      # LSP配置
│   │
│   ├── memory/                  # 项目记忆（与Docs/同步）
│   │   ├── MEMORY.md
│   │   ├── TASKS.md
│   │   ├── DESIGN.md
│   │   ├── INDEX.md
│   │   └── DECISIONS.md
│   │
│   └── plugins/                 # 插件目录
│       └── README.md
│
├── Docs/                        # 项目文档
│   ├── README.md                # 文档导航
│   ├── AGENT_GUIDE.md           # Agent使用指南
│   ├── USER_GUIDE.md            # 用户指南
│   ├── ARCHITECTURE.md          # 架构文档
│   ├── API_REFERENCE.md         # API参考
│   ├── EXAMPLES.md              # 使用示例
│   ├── MEMORY.md                # 项目记忆
│   ├── TASKS.md                 # 任务管理
│   ├── DESIGN.md                # 设计文档
│   ├── INDEX.md                 # 知识图谱
│   ├── DECISIONS.md             # 决策日志
│   ├── guide/
│   │   └── installation.md      # 安装指南
│   └── en/                      # 英文文档
│       ├── AGENT_GUIDE.md
│       ├── USER_GUIDE.md
│       ├── ARCHITECTURE.md
│       └── guide/
│           └── installation.md
│
├── .quickagents/                # QuickAgents数据
│   └── boulder.json             # 进度追踪数据
│
└── packages/                    # NPM包
    └── quickagents-cli/         # CLI工具
```

---

## 配置系统

### quickagents.json

主配置文件，控制QuickAgents的核心行为：

```json
{
  "version": "2.1.1",
  "triggerWords": [
    "启动QuickAgent",
    "启动QuickAgents",
    "启动QA",
    "Start QA"
  ],
  "agents": {
    "enabled": true,
    "autoCreate": true
  },
  "skills": {
    "enabled": true,
    "autoEvolve": true
  },
  "memory": {
    "type": "three-dimensional",
    "sync": true
  }
}
```

### categories.json

任务分类配置，用于智能模型选择：

```json
{
  "version": "2.1.1",
  "categories": {
    "quick": {
      "description": "快速任务",
      "model": "flash",
      "maxTokens": 4000
    },
    "planning": {
      "description": "规划任务",
      "model": "pro",
      "maxTokens": 16000
    },
    "coding": {
      "description": "编码任务",
      "model": "pro",
      "maxTokens": 8000
    }
  }
}
```

### lsp-config.json

LSP服务器配置，支持多语言：

```json
{
  "version": "2.1.1",
  "languages": ["typescript", "python", "rust"],
  "ast-grep": true,
  "servers": {
    "typescript": {
      "command": "typescript-language-server",
      "args": ["--stdio"]
    }
  }
}
```

---

## 数据流

### 初始化流程

```
用户触发词 → yinglong-init → 检查环境
                ↓
           读取配置 → 检查首次使用
                ↓
           首次配置向导（models.json, lsp-config.json）
                ↓
           7层需求问询（inquiry-skill）
                ↓
           创建目录结构 → 初始化文档
                ↓
           创建标准代理（编程项目）
                ↓
           开始执行第一个任务
```

### 任务执行流程

```
用户任务 → fenghou-orchestrate → 分类（category-system-skill）
                ↓
           选择模型（multi-model-skill）
                ↓
           调度代理 → 执行任务
                ↓
           记录记忆（project-memory-skill）
                ↓
           更新进度（boulder-tracking-skill）
                ↓
           Git提交（git-commit-skill）
```

### 跨会话恢复流程

```
/start-work → 读取MEMORY.md → 读取boulder.json
                ↓
           恢复上下文 → 显示进度
                ↓
           继续执行 → 更新状态
```

---

## 代理系统

### 代理分类

| 分类 | 代理 | 职责 |
|------|------|------|
| **核心** | yinglong-init | 项目初始化 |
| | boyi-consult | 需求分析与顾问 |
| | chisongzi-advise | 技术栈推荐 |
| | cangjie-doc | 文档管理 |
| | huodi-skill | Skill管理 |
| | fenghou-orchestrate | 主调度器 |
| **质量** | jianming-review | 代码审查 |
| | lishou-test | 测试执行 |
| | mengzhang-security | 安全审计 |
| | hengge-perf | 性能分析 |
| **工具** | kuafu-debug | 调试代理 |
| | gonggu-refactor | 重构代理 |
| | huodi-deps | 依赖管理 |
| | hengge-cicd | CI/CD管理 |
| **规划** | fenghou-plan | 规划器 |

### 代理协作关系

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户请求                                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  fenghou-orchestrate                            │
│                      (主调度器)                                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   规划阶段     │   │   执行阶段     │   │   质量阶段     │
├───────────────┤   ├───────────────┤   ├───────────────┤
│ fenghou-plan  │   │ gonggu-refactor│   │ jianming-review│
│ boyi-consult  │   │ huodi-deps    │   │ lishou-test   │
│               │   │ hengge-cicd   │   │ mengzhang-security│
└───────────────┘   └───────────────┘   │ hengge-perf   │
                                        └───────────────┘
```

---

## 技能系统

### 技能分类

| 分类 | 技能 | 用途 |
|------|------|------|
| **核心** | project-memory-skill | 三维记忆管理 |
| | boulder-tracking-skill | 跨会话进度追踪 |
| | category-system-skill | 语义化任务分类 |
| **开发** | inquiry-skill | 7层需求问询 |
| | tdd-workflow-skill | 测试驱动开发 |
| | code-review-skill | 代码质量审查 |
| | git-commit-skill | Git提交标准化 |
| **工具** | multi-model-skill | 多模型支持 |
| | lsp-ast-skill | LSP/AST代码分析 |
| | project-detector-skill | 项目类型检测 |
| | background-agents-skill | 并行代理执行 |
| | skill-integration-skill | Skill整合管理 |

### 技能进化机制

```
任务完成 → 分析使用情况 → 识别改进空间
                ↓
           记录优化建议到MEMORY.md
                ↓
           每10任务或每周 → 执行优化
                ↓
           综合评估（统计+反馈+自评）
                ↓
           更新技能 → 记录到EVOLUTION.md
```

---

## 记忆系统

### 三维记忆架构

基于论文《Memory in the Age of AI Agents》设计：

```
┌─────────────────────────────────────────────────────────────────┐
│                      Memory System                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Factual Memory  │  │Experiential Mem │  │ Working Memory  │  │
│  │    (事实记忆)    │  │   (经验记忆)     │  │   (工作记忆)    │  │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────┤  │
│  │ • 项目元信息     │  │ • 操作历史       │  │ • 当前任务      │  │
│  │ • 技术决策       │  │ • 经验总结       │  │ • 活跃上下文    │  │
│  │ • 业务规则       │  │ • 用户反馈       │  │ • 待决策项      │  │
│  │ • 约束条件       │  │ • 迭代记录       │  │ • 临时变量      │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                  │
│  Formation ──────────► Retrieval ──────────► Evolution          │
│  (形成触发)            (智能检索)           (智能整合)            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 记忆存储

记忆存储在 `MEMORY.md` 文件中，采用混合格式：

```yaml
---
# YAML Front Matter - 元数据区
memory_type: project | feature | module
created_at: 2026-03-27T10:00:00Z
updated_at: 2026-03-27T15:30:00Z
version: 2.1.1
tags: [tag1, tag2, tag3]
---

# Markdown主体 - 内容区
```

---

## Python 包架构 (v2.8.3)

### 核心包结构

```
quickagents/
├── __init__.py                  # 公共 API 导出
├── core/                        # 核心模块
│   ├── unified_db.py            # UnifiedDB 门面类 (737 lines)
│   ├── session.py               # Session 统一接口 (190 lines)
│   ├── connection_manager.py    # 动态连接池 (640 lines)
│   ├── transaction_manager.py   # ACID 事务 (364 lines)
│   ├── migration_manager.py     # 迁移管理 (500 lines)
│   ├── markdown_sync.py         # Markdown 同步 (并行+批量)
│   ├── evolution.py             # SkillEvolution 自我进化
│   ├── file_manager.py          # FileManager 文件管理
│   ├── loop_detector.py         # LoopDetector 循环检测
│   ├── reminder.py              # Reminder 事件提醒
│   ├── cache_db.py              # 缓存数据库
│   ├── git_hooks.py             # Git 钩子
│   ├── memory.py                # 记忆辅助函数
│   └── repositories/            # Repository 层
│       ├── query_builder.py     # Django 风格查询构建器 (463 lines)
│       ├── base.py              # BaseRepository
│       ├── memory_repo.py       # MemoryRepository (528 lines)
│       ├── task_repo.py         # TaskRepository (457 lines)
│       ├── progress_repo.py     # ProgressRepository (271 lines)
│       └── feedback_repo.py     # FeedbackRepository (274 lines)
│
├── knowledge_graph/             # 知识图谱模块
│   ├── knowledge_graph.py       # KG 门面类
│   ├── interfaces.py            # 接口定义 (含批量方法默认实现)
│   ├── types.py                 # NodeType, EdgeType 枚举
│   ├── exceptions.py            # KG 异常
│   ├── core/
│   │   └── searcher.py          # FTS5 搜索 + 批量关系扩展
│   └── storage/
│       └── sqlite_storage.py    # WAL + 线程本地持久连接 + 批量查询
│
├── document/                    # 文档管道模块
│   ├── pipeline.py              # 三层管道编排
│   ├── models.py                # 数据模型
│   ├── parsers/                 # 7 个解析器 (PDF/Word/Excel/XMind/FreeMind/OPML/MD)
│   ├── extractors/              # 知识提取器
│   ├── matching/                # 三级追踪匹配
│   ├── validators/              # 交叉验证
│   ├── storage/                 # 文档存储
│   └── ocr/                     # OCR 支持 (可选)
│
├── browser/                     # 浏览器自动化 (Playwright)
├── cli/                         # CLI 工具 (qka 命令)
├── skills/                      # TDD/Git/反馈等技能模块
└── utils/                       # 编码/编辑器/同步冲突
```

### UnifiedDB V2 分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                 UnifiedDB (Facade) — 统一入口                │
│  set_memory / get_memory / search_memory / get_all_memories │
│  add_task / update_task_status / init_progress / add_feedback│
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                 Session Layer (v2.8.3)                       │
│  query() / transaction() / read_only() / execute()          │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                 Repository Layer                             │
│  MemoryRepo │ TaskRepo │ ProgressRepo │ FeedbackRepo         │
│  QueryBuilder (Django-style chainable API)                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                 Core Components                              │
│  ConnectionManager │ TransactionManager │ MigrationManager   │
│  (动态连接池/pre_ping/PRAGMA增强/WAL Checkpoint)              │
└─────────────────────────────────────────────────────────────┘
```

### v2.8.3 性能优化

#### SQLite WAL 模式 + 持久连接

```python
# quickagents/knowledge_graph/storage/sqlite_storage.py
# 线程本地持久连接，避免每次操作新建连接
PRAGMA journal_mode=WAL        # 读写并发
PRAGMA synchronous=NORMAL      # 平衡性能与安全
PRAGMA cache_size=-8000        # 8MB 页面缓存
PRAGMA temp_store=MEMORY       # 临时表在内存
PRAGMA mmap_size=67108864      # 64MB 内存映射
PRAGMA busy_timeout=5000       # 5秒锁等待
```

#### N+1 查询消除

```python
# 优化前: _expand_relations() 对 N 个节点执行 2N+M 次查询
# 优化后: 2 次批量 SQL 查询
def _expand_relations(self, nodes):
    node_ids = [n.id for n in nodes]
    all_edges = self.storage.query_edges_batch(node_ids)  # 1 query
    edge_node_ids = set(e.source for e in all_edges) | set(e.target for e in all_edges)
    related_nodes = self.storage.get_nodes_batch(edge_node_ids)  # 1 query
    return self._build_relations(nodes, all_edges, related_nodes)
```

#### MarkdownSync 并行同步

```python
# v2.8.3: ThreadPoolExecutor 并行化
def sync_all(self):
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(self.sync_memory),
            executor.submit(self.sync_tasks),
            executor.submit(self.sync_feedback),
        ]
        for f in futures:
            f.result()
```

### 性能基准 (v2.8.3)

| 指标 | 值 |
|------|-----|
| 单次读取 QPS | 16,679 ops/sec |
| 批量写入 QPS | 5,200–7,096 ops/sec |
| 连接池命中率 | 100% |
| 连接获取时间 | 0.005–0.006 ms |
| WAL 增长 | 0 KB (auto-checkpoint) |

---

## 扩展性

### 添加新代理

1. 在 `.opencode/agents/` 创建 `agent-name.md`
2. 添加YAML前置配置
3. 在 `INDEX.md` 中添加索引

### 添加新技能

1. 在 `.opencode/skills/` 创建 `skill-name/` 目录
2. 创建 `SKILL.md` 技能说明文档
3. 在 `registry.json` 中注册

### 添加新命令

1. 在 `.opencode/commands/` 创建 `command-name.md`
2. 定义命令行为和参数
3. 更新文档

---

*版本: 2.8.3 | 更新时间: 2026-04-05*
