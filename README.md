# QuickAgents

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/Version-2.7.0-green.svg)](https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM)
[![OpenCode Compatible](https://img.shields.io/badge/OpenCode-Compatible-blue.svg)](https://opencode.ai)

**AI Agent Enhancement Toolkit with Self-Evolution** | **AI代理增强工具包，支持自我进化**

[中文文档](#quickagents-中文) | [English](#quickagents-english)

---

# QuickAgents (中文)

## 📖 项目简介

QuickAgents是一个强大的AI代理增强工具包，通过本地处理最大化效率，最小化Token消耗。支持自我进化、记忆管理、知识图谱、TDD工作流等核心功能。

### 🎯 核心目标

- **最大化本地处理**：减少API调用，节省Token消耗60-100%
- **自我进化系统**：自动收集经验，持续优化Skills
- **统一数据管理**：SQLite主存储 + Markdown辅助备份
- **跨会话记忆**：三维记忆系统，支持项目上下文保持

## ✨ 核心功能

### 1. 统一数据库系统 (UnifiedDB V2)

**V2 架构**：分层设计，模块化，可测试

```
┌─────────────────────────────────────────────────────────────┐
│                    UnifiedDB V2 Architecture                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │              UnifiedDB (Facade)                      │   │
│   │  - set_memory() / get_memory() / search_memory()    │   │
│   │  - add_task() / update_task_status()                │   │
│   │  - init_progress() / update_progress()              │   │
│   │  - add_feedback() / get_feedbacks()                 │   │
│   └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│   ┌──────────────────────┴──────────────────────────┐       │
│   │              Repository Layer                    │       │
│   ├─────────────────────────────────────────────────┤       │
│   │  MemoryRepo │ TaskRepo │ ProgressRepo │ FeedbackRepo │  │
│   └─────────────────────────────────────────────────┘       │
│                          │                                  │
│   ┌──────────────────────┴──────────────────────────┐       │
│   │              Core Components                     │       │
│   ├─────────────────────────────────────────────────┤       │
│   │  ConnectionManager │ TransactionManager │ MigrationManager │
│   └─────────────────────────────────────────────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**V2 特性**：
- **ConnectionManager**: 连接池、WAL模式、线程安全
- **TransactionManager**: ACID事务、嵌套SAVEPOINT
- **MigrationManager**: Schema版本管理、校验和验证
- **Repository层**: CRUD操作封装、类型安全

```python
from quickagents import UnifiedDB, MemoryType, TaskStatus

db = UnifiedDB('.quickagents/unified.db')

# 设置记忆
db.set_memory('project.name', 'MyProject', MemoryType.FACTUAL)
db.set_memory('current.task', '实现认证', MemoryType.WORKING)

# 获取记忆
name = db.get_memory('project.name')

# 任务管理
db.add_task('T001', '实现认证', 'P0')
db.update_task_status('T001', TaskStatus.COMPLETED)
```

### 2. 自我进化系统 (SkillEvolution)

```python
from quickagents import get_evolution

evolution = get_evolution()

# 任务完成时自动触发
evolution.on_task_complete({
    'task_id': 'T001',
    'task_name': '实现认证',
    'skills_used': ['tdd-workflow-skill'],
    'success': True
})

# Git提交时自动触发
evolution.on_git_commit()

# 检查定期优化
if evolution.check_periodic_trigger():
    evolution.run_periodic_optimization()
```

### 3. 知识图谱系统 (KnowledgeGraph)

```python
from quickagents import KnowledgeGraph, NodeType, EdgeType

kg = KnowledgeGraph()

# 创建节点
node = kg.create_node(
    node_type=NodeType.REQUIREMENT,
    title='用户认证需求',
    content='实现JWT认证'
)

# 创建边
kg.create_edge(
    source_id=node.id,
    target_id='T001',
    edge_type=EdgeType.TRACES_TO
)

# 搜索
results = kg.search('认证')

# 需求追踪
trace = kg.trace_requirement(node.id)
```

### 4. 浏览器自动化 (Browser)

```python
from quickagents import Browser

browser = Browser()
page = browser.new_page()

# 获取控制台日志
logs = page.get_console_logs()

# 获取网络请求
requests = page.get_network_requests()

# 执行JavaScript
result = page.evaluate('document.title')

browser.close()
```

## 🚀 安装

### 一句话安装（推荐）

直接告诉你的LLM代理工具（如OpenCode、Claude等）：

```
请按照 https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/Docs/guide/installation.md 中的指引安装QuickAgents
```

代理会自动完成所有安装步骤。

### 手动安装

```bash
pip install quickagents
```

### 完整安装（包含Windows功能）

```bash
pip install quickagents[full]
```

### 开发模式

```bash
git clone https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM.git
cd Quick-Agents-for-Z.AI-GLM
pip install -e .
```

## 📋 CLI命令

```bash
# 统计信息
qa stats

# 同步到Markdown
qa sync

# 记忆操作
qa memory get <key>
qa memory set <key> <value>
qa memory search <query>

# 任务操作
qa tasks list
qa tasks add <id> <name> --priority P0
qa tasks status <id> <status>

# 进度查看
qa progress

# 进化系统
qa evolution status
qa evolution optimize

# Git钩子
qa hooks install
qa hooks status

# 知识图谱
qa kg create-node --type requirement --title "需求标题"
qa kg search <query>
qa kg trace <node-id>

# 模型配置（ZhipuAI GLM Coding Plan）
qa models show                    # 查看当前配置
qa models list                    # 列出可用模型
qa models check-updates           # 检查GLM更新
qa models upgrade --dry-run       # 预览升级
qa models upgrade --force         # 执行升级
qa models strategy coding-plan    # 切换到Coding Plan
qa models lock GLM-5              # 锁定单一模型
qa models unlock                  # 解除锁定
```

## 🏗️ 架构

```
.quickagents/
├── unified.db           # SQLite主存储
│   ├── memory           # 三维记忆
│   ├── progress         # 进度追踪
│   ├── feedback         # 经验收集
│   ├── tasks            # 任务管理
│   ├── decisions        # 决策日志
│   └── knowledge_*      # 知识图谱
│
Docs/                    # Markdown辅助备份
├── MEMORY.md           # 项目记忆
├── TASKS.md            # 任务管理
└── DECISIONS.md        # 决策日志
```

### 三维记忆系统

| 记忆类型 | 用途 | 示例 |
|---------|------|------|
| Factual | 静态事实信息 | 项目名称、技术栈、架构决策 |
| Experiential | 动态经验信息 | 踩坑记录、最佳实践、用户反馈 |
| Working | 当前工作状态 | 当前任务、进度、阻塞点 |

## 📦 模块说明

| 模块 | 功能 | Token节省 |
|------|------|-----------|
| UnifiedDB | 统一数据库管理 | 60%+ |
| MarkdownSync | 自动同步到Markdown | 100% |
| FileManager | 智能文件读写（哈希检测） | 90%+ |
| LoopDetector | 循环检测 | 100% |
| Reminder | 事件提醒 | 100% |
| SkillEvolution | Skills自我进化 | 0 |
| KnowledgeGraph | 知识图谱 | 80%+ |
| Browser | 浏览器自动化 | 50%+ |
| Encoding | 统一UTF-8编码（跨平台） | 0 |

## 🧪 测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/knowledge_graph/

# 覆盖率报告
pytest --cov=quickagents tests/
```

## 📚 文档

- [API文档](https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/tree/main/Docs/api)
- [架构设计](https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/tree/main/Docs)
- [使用指南](https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/tree/main/Docs/guides)

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

# QuickAgents (English)

## 📖 Overview

QuickAgents is a powerful AI agent enhancement toolkit that maximizes efficiency through local processing and minimizes token consumption by 60-100%. It features self-evolution, memory management, knowledge graphs, TDD workflows, and more.

### 🎯 Core Goals

- **Maximize Local Processing**: Reduce API calls, save 60-100% tokens
- **Self-Evolution System**: Automatically collect experiences, continuously optimize skills
- **Unified Data Management**: SQLite primary storage + Markdown backup
- **Cross-Session Memory**: Three-dimensional memory system for project context preservation

## ✨ Core Features

### 1. Unified Database System (UnifiedDB)

```python
from quickagents import UnifiedDB, MemoryType, TaskStatus

db = UnifiedDB('.quickagents/unified.db')

# Set memory
db.set_memory('project.name', 'MyProject', MemoryType.FACTUAL)
db.set_memory('current.task', 'Implement Auth', MemoryType.WORKING)

# Get memory
name = db.get_memory('project.name')

# Task management
db.add_task('T001', 'Implement Auth', 'P0')
db.update_task_status('T001', TaskStatus.COMPLETED)
```

### 2. Self-Evolution System (SkillEvolution)

```python
from quickagents import get_evolution

evolution = get_evolution()

# Trigger on task completion
evolution.on_task_complete({
    'task_id': 'T001',
    'task_name': 'Implement Auth',
    'skills_used': ['tdd-workflow-skill'],
    'success': True
})

# Trigger on git commit
evolution.on_git_commit()

# Check periodic optimization
if evolution.check_periodic_trigger():
    evolution.run_periodic_optimization()
```

### 3. Knowledge Graph System (KnowledgeGraph)

```python
from quickagents import KnowledgeGraph, NodeType, EdgeType

kg = KnowledgeGraph()

# Create node
node = kg.create_node(
    node_type=NodeType.REQUIREMENT,
    title='User Authentication',
    content='Implement JWT authentication'
)

# Create edge
kg.create_edge(
    source_id=node.id,
    target_id='T001',
    edge_type=EdgeType.TRACES_TO
)

# Search
results = kg.search('authentication')

# Trace requirement
trace = kg.trace_requirement(node.id)
```

### 4. Browser Automation (Browser)

```python
from quickagents import Browser

browser = Browser()
page = browser.new_page()

# Get console logs
logs = page.get_console_logs()

# Get network requests
requests = page.get_network_requests()

# Execute JavaScript
result = page.evaluate('document.title')

browser.close()
```

## 🚀 Installation

### One-Line Install (Recommended)

Tell your LLM agent tool (e.g., OpenCode, Claude):

```
Follow the instructions at https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/Docs/guide/installation.md to install QuickAgents
```

The agent will automatically complete all installation steps.

### Manual Installation

```bash
pip install quickagents
```

### Full Installation (with Windows features)

```bash
pip install quickagents[full]
```

### Development Mode

```bash
git clone https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM.git
cd Quick-Agents-for-Z.AI-GLM
pip install -e .
```

## 📋 CLI Commands

```bash
# Statistics
qa stats

# Sync to Markdown
qa sync

# Memory operations
qa memory get <key>
qa memory set <key> <value>
qa memory search <query>

# Task operations
qa tasks list
qa tasks add <id> <name> --priority P0
qa tasks status <id> <status>

# Progress view
qa progress

# Evolution system
qa evolution status
qa evolution optimize

# Git hooks
qa hooks install
qa hooks status

# Knowledge graph
qa kg create-node --type requirement --title "Requirement Title"
qa kg search <query>
qa kg trace <node-id>

# Model configuration (ZhipuAI GLM Coding Plan)
qa models show                    # View current config
qa models list                    # List available models
qa models check-updates           # Check GLM updates
qa models upgrade --dry-run       # Preview upgrade
qa models upgrade --force         # Execute upgrade
qa models strategy coding-plan    # Switch to Coding Plan
qa models lock GLM-5              # Lock single model
qa models unlock                  # Unlock
```

## 🏗️ Architecture

```
.quickagents/
├── unified.db           # SQLite primary storage
│   ├── memory           # Three-dimensional memory
│   ├── progress         # Progress tracking
│   ├── feedback         # Experience collection
│   ├── tasks            # Task management
│   ├── decisions        # Decision log
│   └── knowledge_*      # Knowledge graph
│
Docs/                    # Markdown backup
├── MEMORY.md           # Project memory
├── TASKS.md            # Task management
└── DECISIONS.md        # Decision log
```

### Three-Dimensional Memory System

| Memory Type | Purpose | Example |
|-------------|---------|---------|
| Factual | Static factual information | Project name, tech stack, architecture decisions |
| Experiential | Dynamic experiential information | Pitfalls, best practices, user feedback |
| Working | Current working state | Current task, progress, blockers |

## 📦 Module Description

| Module | Function | Token Savings |
|--------|----------|---------------|
| UnifiedDB | Unified database management | 60%+ |
| MarkdownSync | Auto-sync to Markdown | 100% |
| FileManager | Smart file read/write (hash detection) | 90%+ |
| LoopDetector | Loop detection | 100% |
| Reminder | Event reminders | 100% |
| SkillEvolution | Skills self-evolution | 0 |
| KnowledgeGraph | Knowledge graph | 80%+ |
| Browser | Browser automation | 50%+ |
| Encoding | Unified UTF-8 encoding (cross-platform) | 0 |

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific tests
pytest tests/knowledge_graph/

# Coverage report
pytest --cov=quickagents tests/
```

## 📚 Documentation

- [API Documentation](https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/tree/main/Docs/api)
- [Architecture Design](https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/tree/main/Docs)
- [User Guide](https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/tree/main/Docs/guides)

## 🤝 Contributing

Contributions are welcome! Please check [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📊 Project Stats

- **Version**: 2.7.0
- **Python Support**: 3.8+
- **Test Coverage**: 254 tests passing
- **License**: MIT
- **Author**: Coder-Beam

## 🔗 Links

- **GitHub**: https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM
- **PyPI**: https://pypi.org/project/quickagents/
- **Documentation**: https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/tree/main/Docs

---

Made with ❤️ by Coder-Beam
