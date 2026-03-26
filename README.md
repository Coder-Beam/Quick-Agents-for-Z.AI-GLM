# QuickAgents - AI Agent Project Initialization System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenCode Compatible](https://img.shields.io/badge/OpenCode-Compatible-blue.svg)](https://opencode.ai)
[![Version](https://img.shields.io/badge/Version-2.0.1-green.svg)](https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM)
[![npm](https://img.shields.io/badge/npm-quickagents--cli-red.svg)](https://www.npmjs.com/package/quickagents-cli)

**[中文](#quickagents---ai-代理项目初始化系统)** | **English**

> A complete AI agent project initialization system with out-of-the-box project setup, requirements clarification, multi-agent collaboration, and cross-session recovery capabilities.

---

## 🚀 One-Line Installation

### For Humans (Recommended)

Copy and paste this prompt into your AI agent (OpenCode CLI/Desktop, etc.):

```
Install and configure QuickAgents by following the instructions here:
https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/Docs/en/guide/installation.md
```

**Or use CLI for one-line installation:**

```bash
npm install -g quickagents-cli
qa init
```

### For LLM Agents

Fetch the installation guide and follow it:

```bash
curl -fsSL https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/Docs/en/guide/installation.md
```

---

## Core Features

### 🚀 Standardized Startup Process

**Trigger Words** (case-insensitive):
- `启动QuickAgent` (Recommended)
- `启动QuickAgents`
- `启动QA`
- `Start QA`

> 💡 **Tip**: `启动QuickAgent` is recommended for clarity and brevity.

### 🧠 Three-Dimensional Memory System

Based on the paper "Memory in the Age of AI Agents":

| Memory Type | Purpose | Examples |
|-------------|---------|----------|
| **Factual Memory** | Static facts | Project metadata, technical decisions, business rules |
| **Experiential Memory** | Dynamic experiences | Operation history, lessons learned, user feedback |
| **Working Memory** | Active state | Current task, active context, pending decisions |

### 🤖 17 Professional Agents

| Category | Agents |
|----------|--------|
| **Core** | yinglong-init, boyi-consult, chisongzi-advise, cangjie-doc, huodi-skill, fenghou-orchestrate |
| **Quality** | jianming-review, lishou-test, mengzhang-security, hengge-perf |
| **Tools** | kuafu-debug, gonggu-refactor, huodi-deps, hengge-cicd |
| **Planning** | fenghou-plan, boyi-consult, jianming-review |

### 📦 12 Specialized Skills

| Skill | Purpose |
|-------|---------|
| project-memory-skill | Three-dimensional memory management |
| boulder-tracking-skill | Cross-session progress tracking |
| category-system-skill | Semantic task classification |
| inquiry-skill | 7-layer requirements inquiry |
| tdd-workflow-skill | Test-driven development workflow |
| code-review-skill | Code quality review |
| git-commit-skill | Git commit standardization |
| multi-model-skill | Multi-model support |
| lsp-ast-skill | LSP/AST code analysis |
| project-detector-skill | Project type detection |
| background-agents-skill | Parallel agent execution |
| skill-integration-skill | Skill integration management |

### 📚 Complete Documentation System

- **Hybrid Structure**: Project-level + features/ + modules/
- **Bidirectional Sync**: Docs/ ↔ .opencode/memory/
- **Knowledge Graph**: INDEX.md provides complete document navigation

---

## Quick Start

### 1. Install QuickAgents

```bash
# Option 1: Use CLI
npm install -g quickagents-cli
qa init

# Option 2: Use one-line prompt (recommended)
# Paste into your AI agent:
# Install and configure QuickAgents by following the instructions here:
# https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/Docs/en/guide/installation.md
```

### 2. Start Initialization

In OpenCode or compatible AI coding agent, send:

```
启动QuickAgent
```

### 3. First-Time Configuration

On first use, the system will automatically guide you through:
- **models.json**: AI model configuration
- **lsp-config.json**: LSP server configuration

### 4. Answer Inquiry Cards

AI will collect requirements through interactive inquiry cards using the 7-layer model:

1. **L1 Business Essence**: Why? Core pain points?
2. **L2 User Profile**: Who uses? Use cases?
3. **L3 Core Flow**: Complete process? Exception handling?
4. **L4 Feature List**: What to build? Feature boundaries?
5. **L5 Data Model**: Data structures? Relationships?
6. **L6 Tech Stack**: Frameworks? Database? Deployment?
7. **L7 Delivery Standards**: Acceptance criteria? Timeline?

---

## Agent Usage Guide

### By Scenario

| Scenario | Recommended Approach | Description |
|----------|---------------------|-------------|
| **First Use** | `启动QuickAgent` | Auto-invokes yinglong-init |
| **Daily Development** | Direct conversation | AI intelligently dispatches fenghou-orchestrate |
| **Making Plans** | `@boyi-consult` or `@fenghou-plan` | Enter Plan Mode |
| **Actual Development** | `@fenghou-orchestrate` or `/ultrawork` | Efficient execution |

### Core Commands

| Command | Description |
|---------|-------------|
| `/start-work` | Cross-session recovery |
| `/ultrawork <task>` | Ultra-efficient task execution |
| `/run-workflow` | Run workflow |
| `/enable-coordination` | Enable agent coordination |
| `/disable-coordination` | Disable agent coordination |

> 📖 **Detailed Guide**: See [Docs/en/AGENT_GUIDE.md](Docs/en/AGENT_GUIDE.md) for complete agent usage and collaboration diagrams.

---

## Project Structure

```
your-project/
├── AGENTS.md              # Development specification
├── Docs/                  # Project documentation
│   ├── MEMORY.md          # Three-dimensional memory
│   ├── TASKS.md           # Task management
│   ├── DESIGN.md          # Design documents
│   ├── INDEX.md           # Knowledge graph
│   ├── AGENT_GUIDE.md     # Agent usage guide
│   ├── USER_GUIDE.md      # User guide
│   ├── ARCHITECTURE.md    # Architecture docs
│   ├── en/                # English documentation
│   └── guide/             # Installation guides
│       └── installation.md
│
├── .opencode/             # OpenCode configuration
│   ├── agents/            # 17 professional agents
│   ├── skills/            # 12 specialized skills
│   ├── commands/          # 6 core commands
│   ├── hooks/             # Automation hooks
│   ├── config/            # Configuration files
│   │   ├── quickagents.json
│   │   ├── categories.json
│   │   └── lsp-config.json
│   └── memory/            # Project memory
│
└── .quickagents/          # QuickAgents data
    └── boulder.json       # Progress tracking
```

---

## Documentation

| Document | Description | Language |
|----------|-------------|----------|
| [README.md](README.md) | Project overview | EN/CN |
| [AGENT_GUIDE.md](Docs/en/AGENT_GUIDE.md) | Agent usage guide | EN |
| [USER_GUIDE.md](Docs/en/USER_GUIDE.md) | User guide | EN |
| [ARCHITECTURE.md](Docs/en/ARCHITECTURE.md) | System architecture | EN |
| [Installation Guide](Docs/en/guide/installation.md) | Installation instructions | EN |
| [中文文档](Docs/README.md) | 中文文档索引 | CN |

---

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- Inspired by [oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent)
- Built for [OpenCode](https://opencode.ai)

---

*Version: 2.0.1 | Last Updated: 2026-03-26*

---

# QuickAgents - AI 代理项目初始化系统

**中文** | **[English](#quickagents---ai-agent-project-initialization-system)**

> 一套完整的AI代理项目初始化系统，提供开箱即用的项目初始化、需求澄清、多代理协作和跨会话恢复能力

---

## 🚀 一键安装

### For Humans（推荐）

复制以下提示词，粘贴到你的AI代理（OpenCode CLI/Desktop等）：

```
Install and configure QuickAgents by following the instructions here:
https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/Docs/guide/installation.md
```

**或者使用CLI一键安装**：

```bash
npm install -g quickagents-cli
qa init
```

### For LLM Agents

获取安装指南并执行：

```bash
curl -fsSL https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/Docs/guide/installation.md
```

---

## 核心特性

### 🚀 标准化启动流程

**触发词**（大小写不敏感）：
- 「启动QuickAgent」（推荐）
- 「启动QuickAgents」
- 「启动QA」
- 「Start QA」

> 💡 **提示**：推荐使用「启动QuickAgent」，简洁且语义明确

### 🧠 三维记忆系统

基于论文《Memory in the Age of AI Agents》设计：

| 记忆类型 | 用途 | 示例 |
|---------|------|------|
| **Factual Memory** | 事实记忆 | 项目元信息、技术决策、业务规则 |
| **Experiential Memory** | 经验记忆 | 操作历史、经验总结、用户反馈 |
| **Working Memory** | 工作记忆 | 当前状态、活跃上下文、待决策项 |

### 🤖 17个专业代理

| 分类 | 代理 |
|------|------|
| **核心** | yinglong-init, boyi-consult, chisongzi-advise, cangjie-doc, huodi-skill, fenghou-orchestrate |
| **质量** | jianming-review, lishou-test, mengzhang-security, hengge-perf |
| **工具** | kuafu-debug, gonggu-refactor, huodi-deps, hengge-cicd |
| **规划** | fenghou-plan, boyi-consult, jianming-review |

### 📦 12个专项技能

| 技能 | 用途 |
|------|------|
| project-memory-skill | 三维记忆管理 |
| boulder-tracking-skill | 跨会话进度追踪 |
| category-system-skill | 语义化任务分类 |
| inquiry-skill | 7层需求问询 |
| tdd-workflow-skill | 测试驱动开发工作流 |
| code-review-skill | 代码质量审查 |
| git-commit-skill | Git提交标准化 |
| multi-model-skill | 多模型支持 |
| lsp-ast-skill | LSP/AST代码分析 |
| project-detector-skill | 项目类型检测 |
| background-agents-skill | 并行代理执行 |
| skill-integration-skill | Skill整合管理 |

### 📚 完整文档体系

- **混合结构**：项目级 + features/ + modules/
- **双向同步**：Docs/ ↔ .opencode/memory/
- **知识图谱**：INDEX.md 提供完整的文档导航

---

## 快速开始

### 1. 安装QuickAgents

```bash
# 方式1：使用CLI
npm install -g quickagents-cli
qa init

# 方式2：使用一句话提示词（推荐）
# 粘贴到AI代理中：
# Install and configure QuickAgents by following the instructions here:
# https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/Docs/guide/installation.md
```

### 2. 启动初始化

在 OpenCode 或兼容的 AI 编码代理中，发送：

```
启动QuickAgent
```

### 3. 首次配置引导

首次使用时，系统会自动引导你完成：
- **models.json**：AI模型配置
- **lsp-config.json**：LSP服务器配置

### 4. 回答询问卡

AI 会通过互动询问卡收集需求，按照7层扩展模型逐层澄清：

1. **L1 业务本质**：为什么做？核心痛点？
2. **L2 用户画像**：谁使用？使用场景？
3. **L3 核心流程**：完整流程？异常处理？
4. **L4 功能清单**：做什么？功能边界？
5. **L5 数据模型**：数据结构？关系？
6. **L6 技术栈**：框架？数据库？部署？
7. **L7 交付标准**：验收标准？时间节点？

---

## Agent使用指南

### 按场景使用代理

| 场景 | 推荐方式 | 说明 |
|------|---------|------|
| **首次使用** | `启动QuickAgent` | 自动调用 yinglong-init |
| **日常开发** | 直接对话 | AI智能调度 fenghou-orchestrate |
| **制定计划** | `@boyi-consult` 或 `@fenghou-plan` | 进入Plan Mode |
| **实际开发** | `@fenghou-orchestrate` 或 `/ultrawork` | 高效执行 |

### 核心命令

| 命令 | 说明 |
|------|------|
| `/start-work` | 跨会话恢复 |
| `/ultrawork <任务>` | 超高效执行任务 |
| `/run-workflow` | 运行工作流 |
| `/enable-coordination` | 启用代理协调 |
| `/disable-coordination` | 禁用代理协调 |

> 📖 **详细指南**：查看 [Docs/AGENT_GUIDE.md](Docs/AGENT_GUIDE.md) 了解完整的Agent调用和合作关系图

---

## 项目结构

```
your-project/
├── AGENTS.md              # 开发规范
├── Docs/                  # 项目文档
│   ├── MEMORY.md          # 三维记忆
│   ├── TASKS.md           # 任务管理
│   ├── DESIGN.md          # 设计文档
│   ├── INDEX.md           # 知识图谱
│   ├── AGENT_GUIDE.md     # Agent使用指南
│   ├── USER_GUIDE.md      # 用户指南
│   ├── ARCHITECTURE.md    # 架构文档
│   ├── en/                # 英文文档
│   └── guide/             # 安装指南
│       └── installation.md
│
├── .opencode/             # OpenCode配置
│   ├── agents/            # 17个专业代理
│   ├── skills/            # 12个专项技能
│   ├── commands/          # 6个核心命令
│   ├── hooks/             # 自动化钩子
│   ├── config/            # 配置文件
│   │   ├── quickagents.json
│   │   ├── categories.json
│   │   └── lsp-config.json
│   └── memory/            # 项目记忆
│
└── .quickagents/          # QuickAgents数据
    └── boulder.json       # 进度追踪
```

---

## 文档导航

| 文档 | 描述 | 语言 |
|------|------|------|
| [README.md](README.md) | 项目概览 | CN/EN |
| [AGENT_GUIDE.md](Docs/AGENT_GUIDE.md) | Agent使用指南 | CN |
| [USER_GUIDE.md](Docs/USER_GUIDE.md) | 用户指南 | CN |
| [ARCHITECTURE.md](Docs/ARCHITECTURE.md) | 系统架构 | CN |
| [安装指南](Docs/guide/installation.md) | 安装说明 | CN |
| [English Docs](Docs/en/README.md) | English documentation | EN |

---

## 贡献指南

欢迎贡献！提交PR前请阅读贡献指南。

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

---

## 许可证

本项目采用 MIT 许可证 - 详情请查看 [LICENSE](LICENSE) 文件。

---

## 致谢

- 灵感来源于 [oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent)
- 为 [OpenCode](https://opencode.ai) 构建

---

*版本: 2.0.1 | 更新时间: 2026-03-26*
