# QuickAgents

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/Version-2.25.5-green.svg)](https://pypi.org/project/quickagents/)
[![OpenCode Compatible](https://img.shields.io/badge/OpenCode-Compatible-blue.svg)](https://opencode.ai)
[![GLM Optimized](https://img.shields.io/badge/GLM-Coding_Plan-orange.svg)](https://bigmodel.cn)

专为 **OpenCode** 和 **智谱 GLM 大模型 (Coding Plan)** 深度优化的 AI Agent 增强工具包。通过本地处理最大化效率，Token 消耗节省 60-100%。

---

## 安装

### 方式一：一行命令安装（推荐）

**macOS / Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/scripts/install.sh | bash
```

**Windows PowerShell:**
```powershell
iwr -useb https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/scripts/install.ps1 | iex
```

### 方式二：pip 安装 + 项目初始化

```bash
pip install quickagents
qka init
```

### 方式三：让 AI 代理自动安装（零操作）

把这句话发给你的 AI 代理（OpenCode / Claude Code / ChatGPT）：

```
请按照 https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/Docs/guide/installation.md 中的指引安装 QuickAgents
```

### 初始化参数

```bash
qka init                        # 交互式初始化
qka init --force                # 覆盖现有文件
qka init --dry-run              # 预览不执行
qka init --minimal              # 最小安装（仅核心文件）
qka init --with-ui-ux           # 含 ui-ux-pro-max 技能（Web/Mobile 项目）
qka init --with-browser         # 含 browser-devtools 技能
qka init --update-config        # 仅更新配置，保留数据
```

### 完整安装（所有可选依赖）

```bash
pip install quickagents[full]
```

### 开发模式

```bash
git clone https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM.git
cd Quick-Agents-for-Z.AI-GLM
pip install -e .
```

### 验证安装

```bash
python -c "from quickagents import __version__; print(f'QuickAgents v{__version__}')"
qka version
qka version --check      # 检查所有模块完整性
```

---

## QuickAgents 是什么？

QuickAgents 是一个 Python 包，为 AI 编码代理（特别是 OpenCode + 智谱 GLM Coding Plan）提供**本地化的增强能力**。核心理念：**能用本地 Python 处理的，绝不浪费 LLM Token**。

**核心能力一览：**

| 能力 | 说明 |
|------|------|
| 三维记忆系统 | Factual / Experiential / Working 三类记忆，SQLite 存储，跨会话持久化 |
| 知识图谱 | 需求追踪、实体关系、FTS5 全文搜索 |
| 愚公循环 (YuGong) | 自主开发循环，需求解析 → LLM 执行 → 质量检查 → 自动提交，循环直到完成 |
| Karpathy 经验编译器 | 分散经验 → LLM 编译 → 结构化知识文章，81x 压缩，84% Token 节省 |
| 文档理解管道 | PDF / Word / Excel / XMind / FreeMind / OPML / Markdown / 源码解析 |
| 自我进化系统 | 自动收集 Skills 使用经验，持续优化 |
| 审计问责 (AuditGuard) | 代码变更追踪、质量门禁、问题归因、学习经验提取 |
| 浏览器自动化 | Playwright + Lightpanda/Chromium，控制台日志、网络请求、性能指标 |
| TDD 工作流 | Red → Green → Refactor 本地化执行 |
| 循环检测 | Doom-Loop 防护，防止 Agent 陷入重复调用死循环 |
| 上下文压缩 | 渐进式压缩策略，70%/80%/85%/90%/99% 分级响应 |
| 并行执行器 | 最多 3 并发的只读任务并行处理 |
| Git 钩子 | 自动触发进化分析、提交前质量检查 |

---

## 与 oh-my-openagent (omo) 的对比

| 维度 | **QuickAgents** | **oh-my-openagent (omo)** |
|------|----------------|--------------------------|
| **定位** | Python 本地化工具包，Token 节省优先 | OpenCode 插件（TypeScript），多模型编排优先 |
| **核心语言** | Python（pip install） | TypeScript（OpenCode 插件生态） |
| **Token 策略** | 本地处理优先，SQLite 缓存，哈希检测，经验编译 | 多模型路由，按任务类别分派模型 |
| **模型支持** | 深度优化智谱 GLM Coding Plan，也支持 OpenAI | Claude / Kimi / GLM / GPT / Gemini 多模型混编 |
| **记忆系统** | 三维记忆（Factual/Experiential/Working）+ SQLite + Markdown 双存储 | 依赖 Agent 会话上下文 |
| **自主循环** | 愚公循环（YuGong）— 需求到完成全自动，熔断器 + 退出检测 + 质量门禁 | Ralph Loop — 不停止直到完成 |
| **经验编译** | Karpathy 模式，383 文件 → 13 文章，81x 压缩 | 无对应功能 |
| **知识图谱** | 完整 KnowledgeGraph + FTS5 搜索 + 需求追踪 | 无对应功能 |
| **文档理解** | PDF/Word/Excel/XMind/FreeMind/OPML/源码三层解析管道 | 无对应功能 |
| **审计问责** | AuditGuard — 代码变更追踪 + 质量门禁 + 学习提取 | 无对应功能 |
| **浏览器自动化** | Playwright + Lightpanda（轻量）+ Chromium 回退 | Playwright（内置 MCP） |
| **安装方式** | `pip install quickagents` + `qka init` | OpenCode 插件，JSON 配置 |
| **CLI 工具** | `qka` 命令行，30+ 子命令 | 依赖 OpenCode slash 命令 |
| **运行时依赖** | 极少：仅 psutil + httpx（核心功能零外部依赖） | 需要 Node.js / Bun 运行时 |

**简单总结：** omo 擅长多模型编排和 Agent 协调；QuickAgents 擅长本地化处理、Token 节省、记忆持久化和知识管理。两者可以互补使用。

---

## 功能模块详解

### 1. 统一数据库 (UnifiedDB V2)

分层架构：Facade → Session → Repository → Core Components，Django 风格 QueryBuilder。

```python
from quickagents import UnifiedDB, MemoryType, TaskStatus

db = UnifiedDB('.quickagents/unified.db')

# 三维记忆
db.set_memory('project.name', 'MyProject', MemoryType.FACTUAL)
db.set_memory('current.task', '实现认证', MemoryType.WORKING)
db.set_memory('lesson.001', '避免过度工程', MemoryType.EXPERIENTIAL, category='pitfalls')

# 任务管理
db.add_task('T001', '实现认证', 'P0')
db.update_task_status('T001', TaskStatus.COMPLETED)

# 进度追踪
db.init_progress('auth-system', total_tasks=8)
```

**性能数据：**
- N+1 查询消除：2N+M → 2（常量）
- 同步并行化：ThreadPoolExecutor 3 workers
- mypy 0 errors / ruff 0 errors

### 2. 愚公循环 (YuGong Loop)

全自动开发循环：从需求文件到完整项目。

```
需求解析 → 15步标准迭代循环：
  Phase 1: safety_check → get_next_story → build_prompt
  Phase 2: execute_agent → parse_output
  Phase 3: quality_checks → extract_learnings → update_story
  Phase 4: auto_commit → regression → exit_check → persist → sync → metrics
```

```python
from quickagents.yugong import YuGongLoop, YuGongConfig

# 三种模式：默认 / 保守 / 激进
config = YuGongConfig.conservative()   # 更严格安全限制
config = YuGongConfig.aggressive()     # 更高执行效率

loop = YuGongLoop(config=config, agent_fn=my_agent)
outcome = loop.start(parsed_requirement)
```

**安全机制：**
- 熔断器：连续无进展 / 相同错误次数阈值 + 冷却时间
- API 5 小时限制预警
- 退出检测：最少迭代次数 + 完成信号阈值
- 质量检查：typecheck / lint / tests / coverage / 安全扫描

```bash
qka yugong start requirement.json              # 启动循环
qka yugong start req.json --mode conservative   # 保守模式
qka yugong start req.json --provider openai     # 使用 OpenAI
qka yugong status                               # 查看状态
qka yugong resume                               # 从断点恢复
qka yugong report                               # 生成报告（Markdown + JSON）
qka yugong parse requirement.json               # 解析需求文件
qka yugong config default                       # 查看配置
```

### 3. Karpathy 经验编译器 (ExperienceCompiler)

基于 Andrej Karpathy 的 LLM Knowledge Base 模式：分散经验 → LLM 编译一次 → 结构化知识文章 → 后续直接查询。

```
任务完成 → accumulate(task_result) → 缓冲区 → 达到阈值 → compile() → 增量编译
                                                                         ↓
                                                            .quickagents/compiled/
                                                              _index.md
                                                              _sources.md
                                                              patterns/
                                                                tdd-patterns.md
                                                                debugging-tricks.md
```

**实测数据：** 383 文件 → 13 文章，81x 压缩，84% Token 节省。

```bash
qka experience stats          # 编译器统计
qka experience compile <path> # 编译指定路径
qka experience query <keyword> # 查询编译后的知识
qka experience lint           # 检查问题
qka experience clear          # 清空缓冲区
```

### 4. 知识图谱 (KnowledgeGraph)

```python
from quickagents import KnowledgeGraph, NodeType, EdgeType

kg = KnowledgeGraph()

node = kg.create_node(node_type=NodeType.REQUIREMENT, title='用户认证', content='JWT')
kg.create_edge(source_id=node.id, target_id='T001', edge_type=EdgeType.MAPS_TO)

results = kg.search('认证')
trace = kg.trace_requirement(node.id)
relations = kg.discover_relations(node.id)
```

### 5. 文档理解管道 (DocumentPipeline)

三层解析架构：

| 层 | 功能 | 说明 |
|----|------|------|
| Layer 1 | 本地解析 | PDF / Word / Excel / XMind / FreeMind / OPML / Markdown / 源码 |
| Layer 1.5 | 联合分析 | 文档 ↔ 源码追踪匹配引擎 |
| Layer 2 | 交叉验证 | 检查文档与源码一致性 |
| Layer 3 | 深度分析 | LLM 知识提取（需求 / 决策 / 事实） |

```bash
qka import PALs/                          # 导入文档目录
qka import PALs/ --with-source            # 同时导入源码
qka import PALs/ --dry-run                # 预览
qka import PALs/ --output Docs/PALs       # 指定输出目录
```

**支持的格式：**
- 文档：PDF (PyMuPDF + pdfplumber)、Word (python-docx)、Excel (openpyxl)、XMind
- 脑图：FreeMind (.mm)、OPML
- 源码：Python / JavaScript / TypeScript / Java / Go / Rust / C / C++ (tree-sitter)

### 6. 审计问责 (AuditGuard)

全自动代码质量保障：

| 组件 | 功能 |
|------|------|
| CodeAuditTracker | 实时文件变更追踪 |
| QualityGate | 原子级 / 全量级分层质量门禁 |
| AccountabilityEngine | 问题归因、修复闭环、学习经验提取 |
| AuditReporter | Markdown / JSON 报告生成 |

```bash
qka audit status                         # 审计系统状态
qka audit run --type atomic              # 原子级检查（每次提交）
qka audit run --type full                # 全量级检查（任务完成时）
qka audit log                            # 查看审计日志
qka audit issues --status OPEN           # 查看问题
qka audit lessons --category security    # 查看学习经验
qka audit report --format md             # 生成报告
qka audit init                           # 初始化配置
```

### 7. 浏览器自动化 (Browser)

```python
from quickagents import Browser

browser = Browser()                # 默认 Lightpanda（轻量）
browser = Browser(fallback_to_chromium=True)  # 回退到 Chromium

page = browser.open('https://example.com')
logs = page.get_console_logs()
requests = page.get_network_requests()
metrics = page.get_performance_metrics()
title = page.evaluate('document.title')
browser.close()
```

安装：`pip install quickagents[browser]` → `playwright install chromium`

### 8. 其他核心模块

| 模块 | 说明 | Token 节省 |
|------|------|-----------|
| FileManager | 哈希检测文件变化，缓存未变文件 | 90%+ |
| LoopDetector | V3 循环检测（stuck/oscillation 三级升级） | 100% |
| Reminder | 工具调用计数、长时间运行提醒、上下文压力响应 | 100% |
| ContextCompressor | 70%/80%/85%/90%/99% 分级渐进压缩 | 54%+ |
| ParallelExecutor | asyncio.gather + ThreadPool，最多 3 并发 | 间接 |
| MCPBridge | 只读桥接 OpenCode MCP 配置，发现可用工具 | 0 |
| SkillAuditor | Skill 描述质量审计 | 0 |
| MarkdownSync | SQLite → Markdown 双向同步，并行优化 | 100% |
| GitHooks | post-commit 自动触发进化分析 | 0 |
| Encoding | 统一 UTF-8 编码，Windows/Linux/macOS 一致 | 0 |

---

## CLI 命令完整列表

所有命令通过 `qka` 调用，`qka --help` 查看帮助。

### 项目初始化

| 命令 | 说明 |
|------|------|
| `qka init` | 初始化 QuickAgents 到当前项目 |
| `qka init --force` | 覆盖现有文件 |
| `qka init --dry-run` | 预览将安装的文件 |
| `qka init --minimal` | 最小安装 |
| `qka init --with-ui-ux` | 含 ui-ux-pro-max 技能 |
| `qka init --with-browser` | 含 browser-devtools 技能 |

### 记忆与数据库

| 命令 | 说明 |
|------|------|
| `qka stats` | 数据库统计信息 |
| `qka sync` | 同步 SQLite → Markdown |
| `qka sync memory` | 仅同步记忆 |
| `qka sync tasks` | 仅同步任务 |
| `qka sync --force` | 强制同步，忽略冲突 |
| `qka memory get <key>` | 获取记忆值 |
| `qka memory set <key> <value>` | 设置记忆值 |
| `qka memory search <keyword>` | 搜索记忆 |

### 任务管理

| 命令 | 说明 |
|------|------|
| `qka progress` | 查看当前进度 |

### 愚公循环 (YuGong)

| 命令 | 说明 |
|------|------|
| `qka yugong start <file>` | 启动自主开发循环 |
| `qka yugong start <file> --mode conservative` | 保守模式 |
| `qka yugong start <file> --mode aggressive` | 激进模式 |
| `qka yugong start <file> --provider openai` | 使用 OpenAI |
| `qka yugong start <file> --dry-run` | 预览 |
| `qka yugong status` | 查看循环状态 |
| `qka yugong resume` | 从断点恢复 |
| `qka yugong parse <file>` | 解析需求文件 |
| `qka yugong config <mode>` | 查看/切换配置模式 |
| `qka yugong report` | 生成执行报告 |

### 自我进化系统

| 命令 | 说明 |
|------|------|
| `qka evolution status` | 进化系统状态 |
| `qka evolution stats [skill]` | Skills 使用统计 |
| `qka evolution optimize` | 执行定期优化 |
| `qka evolution history <skill>` | Skill 进化历史 |
| `qka evolution sync` | 同步到 Markdown |

### 审计问责

| 命令 | 说明 |
|------|------|
| `qka audit status` | 审计系统状态 |
| `qka audit run --type atomic` | 原子级检查 |
| `qka audit run --type full` | 全量级检查 |
| `qka audit log` | 审计日志 |
| `qka audit issues` | 查看问题 |
| `qka audit lessons` | 学习经验 |
| `qka audit report --format md` | 生成报告 |
| `qka audit init` | 初始化配置 |

### TDD 工作流

| 命令 | 说明 |
|------|------|
| `qka tdd red <test_file>` | RED 阶段（测试应失败） |
| `qka tdd green <test_file>` | GREEN 阶段（测试应通过） |
| `qka tdd refactor <test_file>` | REFACTOR 阶段 |
| `qka tdd coverage` | 查看覆盖率 |
| `qka tdd stats` | TDD 统计 |

### 经验编译

| 命令 | 说明 |
|------|------|
| `qka experience stats` | 编译器统计 |
| `qka experience compile <path>` | 编译指定路径 |
| `qka experience query <keyword>` | 查询知识 |
| `qka experience lint` | 检查问题 |
| `qka experience clear` | 清空缓冲区 |

### 上下文压缩

| 命令 | 说明 |
|------|------|
| `qka compress stats` | 压缩器统计 |
| `qka compress check --usage 85` | 检查并建议压缩策略 |
| `qka compress reset` | 重置压缩器 |

### Skill 审计

| 命令 | 说明 |
|------|------|
| `qka skill audit <path>` | 审计 Skill 文件/目录 |
| `qka skill lint --content "..."` | 检查 Skill 内容 |

### Git 集成

| 命令 | 说明 |
|------|------|
| `qka hooks install` | 安装 Git 钩子 |
| `qka hooks uninstall` | 卸载 Git 钩子 |
| `qka hooks status` | 钩子状态 |
| `qka git status` | Git 状态 |
| `qka git check` | Pre-commit 检查 |
| `qka git commit <type> <scope> <subject>` | 格式化提交 |
| `qka git push` | 推送到远程 |

### 文档导入

| 命令 | 说明 |
|------|------|
| `qka import PALs/` | 导入文档目录 |
| `qka import PALs/ --with-source` | 同时导入源码 |
| `qka import PALs/ --dry-run` | 预览 |
| `qka import PALs/ --output <dir>` | 指定输出目录 |

### 反馈收集

| 命令 | 说明 |
|------|------|
| `qka feedback bug <desc>` | 记录 Bug |
| `qka feedback improve <desc>` | 记录改进建议 |
| `qka feedback best <desc>` | 记录最佳实践 |
| `qka feedback view [--type <t>]` | 查看反馈 |
| `qka feedback stats` | 反馈统计 |

### 模型配置（智谱 GLM Coding Plan）

| 命令 | 说明 |
|------|------|
| `qka models show` | 查看当前模型配置 |
| `qka models list` | 列出可用模型 |
| `qka models check-updates` | 检查 GLM 版本更新 |
| `qka models upgrade --dry-run` | 预览升级 |
| `qka models upgrade --force` | 执行升级 |
| `qka models strategy coding-plan` | 切换到 Coding Plan 策略 |
| `qka models lock <model>` | 锁定单一模型 |
| `qka models unlock` | 解除锁定 |

### 文件操作

| 命令 | 说明 |
|------|------|
| `qka read <file>` | 智能读取（哈希检测缓存） |
| `qka write <file> <content>` | 写入文件 |
| `qka edit <file> <old> <new>` | 编辑文件 |
| `qka hash <file>` | 获取文件哈希 |

### 缓存与检测

| 命令 | 说明 |
|------|------|
| `qka cache stats` | 缓存统计 |
| `qka cache clear` | 清空缓存 |
| `qka cache list` | 列出缓存文件 |
| `qka loop check` | 检查循环模式 |
| `qka loop reset` | 重置循环检测 |
| `qka loop stats` | 循环检测统计 |
| `qka reminder check` | 检查提醒 |
| `qka reminder stats` | 提醒统计 |

### 版本与升级

| 命令 | 说明 |
|------|------|
| `qka version` | 查看版本 |
| `qka version --check` | 检查所有模块完整性 |
| `qka update` | 从 PyPI 升级 |
| `qka update --target 2.11.0` | 升级到指定版本 |
| `qka update --source github` | 从 GitHub 源码安装 |
| `qka update --dry-run` | 仅预览 |

### 导出

| 命令 | 说明 |
|------|------|
| `qka export` | 导出干净项目文件到 Output/ |
| `qka export --version 1.0` | 指定版本号 |
| `qka export --dry-run` | 预览导出 |
| `qka export --list-excludes` | 列出排除规则 |
| `qka export --inject-gitignore` | 注入排除规则到 .gitignore |

### 卸载

| 命令 | 说明 |
|------|------|
| `qka uninstall` | 交互式卸载（项目级） |
| `qka uninstall --dry-run` | 预览卸载内容 |
| `qka uninstall --keep-data` | 保留 .quickagents/ |
| `qka uninstall --keep-opencode` | 保留 .opencode/ |
| `qka uninstall --force` | 跳过确认 |

---

## Python API 速查

```python
# 核心导入
from quickagents import (
    # 数据库
    UnifiedDB, MemoryType, TaskStatus, FeedbackType,
    # 进化
    SkillEvolution, get_evolution,
    # 知识图谱
    KnowledgeGraph, NodeType, EdgeType,
    # 工具
    FileManager, LoopDetector, Reminder,
    MarkdownSync, GitHooks, CacheDB,
    # v2.11.0 新增
    SkillAuditor, ContextCompressor, ExperienceCompiler,
    ParallelExecutor, MCPBridge,
    # 浏览器（需 pip install quickagents[browser]）
    Browser,
    # 审计
    AuditGuard, AuditConfig,
    # 记忆辅助
    update_memory, update_memories, add_experiential_memory,
    # 愚公循环
    YuGongLoop, YuGongConfig,
)

# 快速使用
db = UnifiedDB('.quickagents/unified.db')
db.set_memory('key', 'value', MemoryType.FACTUAL)
db.get_memory('key')

evolution = get_evolution()
evolution.on_task_complete({'task_id': 'T001', 'success': True})

kg = KnowledgeGraph()
node = kg.create_node(NodeType.REQUIREMENT, title='需求', content='描述')
results = kg.search('关键词')
```

---

## 可选依赖

| 安装命令 | 功能 |
|----------|------|
| `pip install quickagents[browser]` | 浏览器自动化（Playwright） |
| `pip install quickagents[document]` | 文档解析（PDF/Word/Excel/XMind） |
| `pip install quickagents[source-code]` | 多语言源码解析（tree-sitter） |
| `pip install quickagents[ocr]` | OCR 识别（PaddleOCR） |
| `pip install quickagents[windows]` | Windows 特定功能（pywin32/WMI） |
| `pip install quickagents[full]` | 完整安装（以上全部） |

核心功能零外部依赖，仅需 `psutil` + `httpx`。

---

## 项目结构

```
quickagents/
├── __init__.py              # 统一入口，全部公开 API
├── cli/                     # CLI 命令（qka）
│   ├── main.py              # 命令行入口 + 30+ 子命令
│   ├── init_cmd.py          # qka init 初始化
│   └── qa.py                # 旧入口兼容
├── core/                    # 核心模块
│   ├── unified_db.py        # 统一数据库 (Facade)
│   ├── session.py           # 会话层
│   ├── connection_manager.py # 连接池管理
│   ├── transaction_manager.py # 事务管理
│   ├── migration_manager.py # 数据库迁移
│   ├── repositories/        # Repository 层 + QueryBuilder
│   ├── markdown_sync.py     # SQLite ↔ Markdown 同步
│   ├── file_manager.py      # 智能文件管理（哈希缓存）
│   ├── memory.py            # 记忆管理器
│   ├── loop_detector.py     # Doom-Loop 检测器
│   ├── reminder.py          # 事件提醒系统
│   ├── evolution.py         # 自我进化引擎
│   ├── git_hooks.py         # Git 钩子管理
│   ├── cache_db.py          # 缓存数据库
│   ├── context_compressor.py # 上下文压缩器
│   ├── experience_compiler.py # 经验编译器（Karpathy 模式）
│   ├── parallel_executor.py # 并行任务执行器
│   ├── mcp_bridge.py        # MCP 配置桥接
│   └── skill_auditor.py     # Skill 质量审计
├── knowledge_graph/         # 知识图谱
│   ├── knowledge_graph.py   # 核心图操作
│   ├── types.py             # 节点/边类型定义
│   ├── storage/             # SQLite WAL 存储
│   └── core/                # FTS5 搜索引擎
├── document/                # 文档理解管道
│   ├── pipeline.py          # 三层处理管道
│   ├── parsers/             # PDF/Word/Excel/XMind/FreeMind/OPML/MD/源码解析器
│   ├── matching/            # 追踪匹配引擎
│   ├── validators/          # 交叉验证 + 评审流
│   ├── storage/             # Markdown 导出 + 知识保存
│   └── extractors/          # 知识提取器
├── yugong/                  # 愚公循环
│   ├── autonomous_loop.py   # 15步自主循环引擎
│   ├── config.py            # 配置（默认/保守/激进）
│   ├── models.py            # 数据模型
│   ├── safety_guard.py      # 安全熔断器
│   ├── exit_detector.py     # 退出检测器
│   ├── task_orchestrator.py # 任务编排器
│   ├── agent_executor.py    # Agent 执行器
│   ├── tool_executor.py     # 工具执行器
│   ├── llm_client.py        # LLM 客户端（httpx）
│   ├── requirement_parser.py # 需求解析器
│   ├── context_injector.py  # 上下文注入
│   ├── progress_logger.py   # 进度日志
│   ├── report_generator.py  # 报告生成器
│   └── db.py                # 持久化存储
├── audit/                   # 审计问责
│   ├── audit_guard.py       # 门面类
│   ├── code_audit.py        # 代码变更追踪
│   ├── quality_gate.py      # 质量门禁
│   ├── accountability.py    # 问责引擎
│   ├── audit_reporter.py    # 报告生成
│   └── models.py            # 数据模型
├── browser/                 # 浏览器自动化
│   ├── browser.py           # Browser/Page 封装
│   └── installer.py         # Lightpanda/Chromium 安装
├── skills/                  # Skills 本地化
│   ├── feedback_collector.py
│   ├── tdd_workflow.py
│   ├── git_commit.py
│   ├── category_router.py
│   ├── model_router.py
│   └── project_detector.py
├── utils/                   # 工具模块
│   ├── memory_helper.py     # 记忆辅助函数
│   ├── smart_editor.py      # 智能编辑
│   ├── encoding.py          # UTF-8 编码
│   ├── hash_cache.py        # 哈希缓存
│   ├── script_helper.py     # Windows 脚本替代
│   └── sync_conflict.py     # 同步冲突检测
└── templates/               # 项目模板（qka init 使用）
    ├── AGENTS.md
    ├── opencode.json
    ├── opencode/             # OpenCode 配置模板
    ├── docs/                 # 文档模板
    └── skills-optional/      # 可选 Skills
```

---

## 测试

```bash
pytest tests/
pytest tests/knowledge_graph/          # 特定模块
pytest --cov=quickagents tests/        # 覆盖率
```

---

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件。

---

## 更新日志

### v2.25.5 (2026-04-07) — 全架构验证通过 + 测试修复

**ConnectionManager 统一验证：**
- 确认所有 3 个模块（ExperienceCompiler / YuGongDB / SQLiteGraphStorage）100% 使用 ConnectionManager
- 生产代码中零 `sqlite3.connect` 调用（仅 `:memory:` 路径保留）
- 所有模块共享连接池、线程安全、WAL 模式

**测试修复（6 个 → 0 个失败）：**
- CLI memory 测试：改为 mock `UnifiedDB`（`MemoryManager` 已移除）
- KG memory_sync 测试：UTF-8 编码 + 匹配实际输出格式
- Migration 测试：避免与内置 migration_004 版本冲突

**最终验证：**
- **991 tests passed, 0 failures**
- All imports OK
- Version 2.25.5

### v2.25.4 (2026-04-07) — 全架构A级修复 + 自我进化闭环

**统一架构（零自建连接）:**
- 知识图谱 `discover()` 修复属性名bug + `create_edge()` 签名修正
- 知识图谱新增 `knowledge_node_tags` 关联表 + SQL JOIN 高效查询
- 知识图谱 discovery 全部改为 SQL WHERE/FTS5 查询（零 Python 全表扫描）
- `DocPipeline.save()` dispatch bug 修复（`hasattr` → `isinstance`）
- Evolution Markdown sync `total_usage` → `usage_count` 修复
- `restore_feedback_from_md()` 自动发现 `.quickagents/feedback/` 目录

**自动编译闭环:**
- `on_task_complete()` 自动检查 `should_compile()` 并设标志
- `run_periodic_optimization()` 自动触发编译流程
- 新增 `_auto_compile_experiences()` 基于规则的即时编译

**真正自我进化（5阶段闭环）:**
- Act: `modify_skill()` 自动修改 Skill 文件
- Act: `inject_context()` 注入进化洞察到项目上下文
- Act: `adjust_parameters()` 自动调整进化参数
- Verify: `verify_evolution()` 成功率对比验证 + 回滚建议
- 语义分析: Evolution 查询 ExperienceCompiler 编译文章

**跨模块集成（互操作性矩阵全✅）:**
- 愚公循环完成 → 自动触发 `Evolution.on_task_complete()`
- AuditGuard 提取 lessons → 自动流入 Evolution feedback
- Evolution `_suggest_fix()` → 同时查询 feedback + compiled_articles
- Git 钩子 Windows 兼容（`sys.executable` + `.bat` wrapper + 日志文件）
- Git 钩子同时触发 Evolution + AuditGuard

### v2.25.3 (2026-04-07) — 架构完整性修复

**P0 紧急修复（运行时崩溃）:**
- 修复 `qka audit status` 崩溃（KeyError: `today_changes`）
- 修复 `qka audit run` 崩溃（AttributeError: `report.passed` → `report.all_passed`）
- 修复 `qka audit log` 崩溃（`get_changes_by_session()` 不存在）
- 添加 decisions 表 migration_005 + `add_decision()` 方法
- 愚公循环 `YuGongLoop` 接入 `YuGongDB` 持久化（每次迭代 + 最终保存）

**P1 架构修复（数据一致性）:**
- CLI `qka memory` 改用 `UnifiedDB`（SQLite）替代 `MemoryManager`（纯文件）
- `SkillEvolution.on_task_complete()` 自动调用 `ExperienceCompiler.accumulate()`
- 修复进化系统 CLI `stats['total_usage']` → `stats['usage_count']`
- `DocumentPipeline.save()` 接入 `KnowledgeSaver` 写入 SQLite
- 知识图谱 `discover()` 结果自动持久化到 SQLite
- 知识图谱 `sync_to_memory()` 改为追加模式，不破坏主记忆系统
- 新增 `qka knowledge` CLI 命令（status/search/discover）

**P2 改善（恢复路径修复）:**
- `restore_decisions_from_md()` 真正解析并插入 SQLite
- `restore_feedback_from_md()` 真正解析并插入 SQLite
- `restore_progress_from_json()` 移除对不存在方法的调用
- 新增 `qka tasks` 和 `qka progress` CLI 命令

### v2.11.0 (2026-04-05) — 研究驱动增强

- 新增 MCPBridge（OpenCode MCP 工具发现）
- 新增 ParallelExecutor（并发任务执行）
- 新增 CJK 感知记忆搜索
- 新增 SkillEvolution 批量分析

---

## 链接

- **GitHub**: https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM
- **PyPI**: https://pypi.org/project/quickagents/
- **智谱 GLM**: https://bigmodel.cn
- **OpenCode**: https://opencode.ai

---

*Made by Coder-Beam*
