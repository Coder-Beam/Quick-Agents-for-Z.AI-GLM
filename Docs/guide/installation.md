# QuickAgents Installation Guide

> Version: 2.6.8 | Updated: 2026-03-30 | Author: Coder-Beam

[中文](#quickagents-安装指南) | [English](#quickagents-installation-guide)

---

# QuickAgents Installation Guide

## Overview

QuickAgents consists of two parts:

| Component | Description | Installation |
|-----------|-------------|--------------|
| **Python Package** | Core functionality (UnifiedDB, KnowledgeGraph, CLI, etc.) | `pip install quickagents` |
| **OpenCode Config** | Agents, Skills, Plugin, Config files | Download from GitHub |

## Prerequisites

| Requirement | Minimum | Recommended | Check Command |
|-------------|---------|-------------|---------------|
| Python | 3.9 | 3.11+ | `python --version` |
| pip | 21.0 | Latest | `pip --version` |
| Git | 2.0 | Latest | `git --version` |
| OpenCode | 1.0+ | Latest | `opencode --version` |

## Quick Start (3 Steps)

### Step 1: Install Python Package

```bash
pip install quickagents
```

### Step 2: Download OpenCode Config

```bash
# In your project root directory
curl -fsSL https://codeload.github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/tar.gz/main | tar -xz --strip-components=1 Quick-Agents-for-Z.AI-GLM/.opencode
curl -fsSL https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/AGENTS.md -o AGENTS.md
curl -fsSL https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/opencode.json -o opencode.json
```

### Step 3: Verify Installation

```bash
# Check Python package
python -c "from quickagents import __version__; print(f'QuickAgents v{__version__}')"

# Check CLI
qa --help

# Check OpenCode config
ls .opencode/plugins/quickagents.ts
```

**Done!** Now you can start using QuickAgents:

```
启动QuickAgent
```

---

## Detailed Installation

### 1. Environment Check

**Windows:**
```bash
python --version
pip --version
```

**macOS/Linux:**
```bash
python3 --version
pip3 --version
```

**If Python not installed:**

<details>
<summary>Windows Installation</summary>

```powershell
# Option 1: Official Installer (Recommended)
# 1. Visit https://www.python.org/downloads/
# 2. Download Python 3.12.x
# 3. Check "Add Python to PATH" during installation

# Option 2: winget
winget install Python.Python.3.12

# Option 3: Scoop
scoop install python
```
</details>

<details>
<summary>macOS Installation</summary>

```bash
# Option 1: Homebrew (Recommended)
brew install python@3.12

# Option 2: Official Installer
# Visit https://www.python.org/downloads/macos/
```
</details>

<details>
<summary>Linux Installation</summary>

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install python3.12 python3-pip

# Fedora/RHEL
sudo dnf install python3.12 python3-pip

# Arch Linux
sudo pacman -S python python-pip
```
</details>

### 2. Install Python Package

```bash
# Basic installation
pip install quickagents

# With Windows features
pip install quickagents[windows]

# Full installation
pip install quickagents[full]

# Development mode
git clone https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM.git
cd Quick-Agents-for-Z.AI-GLM
pip install -e .
```

### 3. Download OpenCode Configuration

**Option A: Using curl (Recommended)**

```bash
# Create project directory
mkdir my-project && cd my-project

# Download .opencode directory
curl -fsSL https://codeload.github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/tar.gz/main | tar -xz --strip-components=1 Quick-Agents-for-Z.AI-GLM/.opencode

# Download required files
curl -fsSL https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/AGENTS.md -o AGENTS.md
curl -fsSL https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/opencode.json -o opencode.json

# Create Docs directory
mkdir -p Docs
touch Docs/MEMORY.md Docs/TASKS.md Docs/DESIGN.md Docs/INDEX.md
```

**Option B: Using Git Clone**

```bash
# Clone repository
git clone https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM.git temp-qa

# Copy to your project
cp -r temp-qa/.opencode ./
cp temp-qa/AGENTS.md ./
cp temp-qa/opencode.json ./
mkdir -p Docs
cp -r temp-qa/Docs/* Docs/

# Cleanup
rm -rf temp-qa
```

**Option C: Manual Download**

1. Visit https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM
2. Download ZIP
3. Extract `.opencode/`, `AGENTS.md`, `opencode.json` to your project

### 4. Configure Models

Create `.opencode/config/models.json`:

```json
{
  "primary": "glm-5",
  "categories": {
    "quick": "glm-5-flash",
    "planning": "glm-5",
    "coding": "glm-5"
  }
}
```

### 5. Initialize Database

```bash
# Initialize UnifiedDB
python -c "from quickagents import UnifiedDB; db = UnifiedDB(); print('Database initialized')"

# Install Git hooks (optional)
qa hooks install
```

### 6. Verify Installation

```bash
# 1. Check Python package
python -c "
from quickagents import __version__, UnifiedDB, KnowledgeGraph
print(f'QuickAgents v{__version__}')
db = UnifiedDB()
kg = KnowledgeGraph()
print('All modules imported successfully')
"

# 2. Check CLI
qa --help
qa stats

# 3. Check OpenCode config
test -f AGENTS.md && echo "✅ AGENTS.md"
test -f opencode.json && echo "✅ opencode.json"
test -d .opencode && echo "✅ .opencode/"
test -f .opencode/plugins/quickagents.ts && echo "✅ Plugin"
test -d .opencode/agents && echo "✅ Agents ($(ls .opencode/agents/*.md 2>/dev/null | wc -l) files)"
test -d .opencode/skills && echo "✅ Skills ($(ls -d .opencode/skills/*/ 2>/dev/null | wc -l) dirs)"
```

---

## CLI Commands Reference

```bash
# Database operations
qa stats                      # Show statistics
qa sync                       # Sync SQLite to Markdown
qa memory get <key>           # Get memory
qa memory set <key> <value>   # Set memory
qa memory search <query>      # Search memory

# Task management
qa tasks list                 # List tasks
qa tasks add <id> <name>      # Add task

# Evolution system
qa evolution status           # Show evolution status
qa evolution optimize         # Run optimization

# Git hooks
qa hooks install              # Install Git hooks
qa hooks status               # Check hooks status

# Knowledge graph
qa kg search <query>          # Search knowledge graph
qa kg trace <node-id>         # Trace requirement

# TDD workflow
qa tdd red <test_file>        # Run RED phase
qa tdd green <test_file>      # Run GREEN phase
qa tdd refactor <test_file>   # Run REFACTOR phase
```

---

## Project Structure

After installation, your project should look like:

```
my-project/
├── AGENTS.md                 # AI agent instructions
├── opencode.json             # OpenCode config
├── .opencode/
│   ├── plugins/
│   │   ├── quickagents.ts    # Unified plugin
│   │   └── package.json
│   ├── agents/               # 15 agent configs
│   │   ├── yinglong-init.md
│   │   ├── boyi-consult.md
│   │   └── ...
│   ├── skills/               # 24 skill configs
│   │   ├── tdd-workflow-skill/
│   │   ├── code-review-skill/
│   │   └── ...
│   ├── config/
│   │   ├── models.json       # Model configuration
│   │   └── lsp-config.json   # LSP configuration
│   ├── commands/
│   │   ├── start-work.md
│   │   └── ultrawork.md
│   └── memory/
│       ├── MEMORY.md
│       └── TASKS.md
├── Docs/
│   ├── MEMORY.md
│   ├── TASKS.md
│   ├── DESIGN.md
│   └── INDEX.md
└── .quickagents/
    └── unified.db            # SQLite database
```

---

## Usage

### Start QuickAgents

In OpenCode, send one of these triggers:

```
启动QuickAgent
启动QuickAgents
启动QA
Start QA
```

### Common Workflows

**New Project:**
```
启动QuickAgent
# Follow the interactive prompts
```

**Continue Development:**
```
/start-work
# Resume from last session
```

**Code Review:**
```
@code-reviewer Review the authentication module
```

**TDD Development:**
```
@yinglong-init Implement user authentication with TDD
```

---

## Troubleshooting

### Python Not Found

```bash
# Windows: Check PATH
where python

# macOS/Linux: Check PATH
which python3

# If not found, reinstall Python with "Add to PATH" option
```

### pip Install Fails

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Use --user flag
pip install --user quickagents

# Clear cache
pip cache purge
pip install quickagents --no-cache-dir
```

### Plugin Not Loading

```bash
# Check plugin exists
ls .opencode/plugins/quickagents.ts

# Check opencode.json
cat opencode.json

# Should show:
# {"plugin": ["@coder-beam/quickagents"]}
```

### Database Errors

```bash
# Reset database
rm -rf .quickagents/
python -c "from quickagents import UnifiedDB; UnifiedDB()"
```

### CLI Not Found

```bash
# Check installation
pip show quickagents

# Reinstall
pip install --force-reinstall quickagents

# Check PATH
qa --help
```

---

## Upgrade

```bash
# Upgrade Python package
pip install --upgrade quickagents

# Update OpenCode config
curl -fsSL https://codeload.github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/tar.gz/main | tar -xz --strip-components=1 Quick-Agents-for-Z.AI-GLM/.opencode
```

---

## Uninstall

```bash
# Remove Python package
pip uninstall quickagents

# Remove config files
rm -rf .opencode/ AGENTS.md opencode.json

# Remove database
rm -rf .quickagents/
```

---

## Support

- **GitHub**: https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM
- **Issues**: https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/issues
- **PyPI**: https://pypi.org/project/quickagents/

---

# QuickAgents 安装指南

## 概述

QuickAgents 由两部分组成：

| 组件 | 描述 | 安装方式 |
|------|------|----------|
| **Python包** | 核心功能（UnifiedDB、KnowledgeGraph、CLI等） | `pip install quickagents` |
| **OpenCode配置** | 代理、技能、插件、配置文件 | 从GitHub下载 |

## 前置要求

| 要求 | 最低版本 | 推荐版本 | 检查命令 |
|------|----------|----------|----------|
| Python | 3.9 | 3.11+ | `python --version` |
| pip | 21.0 | 最新 | `pip --version` |
| Git | 2.0 | 最新 | `git --version` |
| OpenCode | 1.0+ | 最新 | `opencode --version` |

## 快速安装（3步）

### 步骤1：安装Python包

```bash
pip install quickagents
```

### 步骤2：下载OpenCode配置

```bash
# 在项目根目录执行
curl -fsSL https://codeload.github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/tar.gz/main | tar -xz --strip-components=1 Quick-Agents-for-Z.AI-GLM/.opencode
curl -fsSL https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/AGENTS.md -o AGENTS.md
curl -fsSL https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/opencode.json -o opencode.json
```

### 步骤3：验证安装

```bash
# 检查Python包
python -c "from quickagents import __version__; print(f'QuickAgents v{__version__}')"

# 检查CLI
qa --help

# 检查OpenCode配置
ls .opencode/plugins/quickagents.ts
```

**完成！** 现在可以开始使用QuickAgents：

```
启动QuickAgent
```

---

## 详细安装步骤

### 1. 环境检测

**Windows:**
```bash
python --version
pip --version
```

**macOS/Linux:**
```bash
python3 --version
pip3 --version
```

**如果Python未安装：**

<details>
<summary>Windows安装</summary>

```powershell
# 方式1：官方安装包（推荐）
# 1. 访问 https://www.python.org/downloads/
# 2. 下载Python 3.12.x
# 3. 安装时勾选 "Add Python to PATH"

# 方式2：winget
winget install Python.Python.3.12

# 方式3：Scoop
scoop install python
```
</details>

<details>
<summary>macOS安装</summary>

```bash
# 方式1：Homebrew（推荐）
brew install python@3.12

# 方式2：官方安装包
# 访问 https://www.python.org/downloads/macos/
```
</details>

<details>
<summary>Linux安装</summary>

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install python3.12 python3-pip

# Fedora/RHEL
sudo dnf install python3.12 python3-pip

# Arch Linux
sudo pacman -S python python-pip
```
</details>

### 2. 安装Python包

```bash
# 基础安装
pip install quickagents

# 包含Windows功能
pip install quickagents[windows]

# 完整安装
pip install quickagents[full]

# 开发模式
git clone https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM.git
cd Quick-Agents-for-Z.AI-GLM
pip install -e .
```

### 3. 下载OpenCode配置

**方式A：使用curl（推荐）**

```bash
# 创建项目目录
mkdir my-project && cd my-project

# 下载.opencode目录
curl -fsSL https://codeload.github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/tar.gz/main | tar -xz --strip-components=1 Quick-Agents-for-Z.AI-GLM/.opencode

# 下载必要文件
curl -fsSL https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/AGENTS.md -o AGENTS.md
curl -fsSL https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/opencode.json -o opencode.json

# 创建Docs目录
mkdir -p Docs
touch Docs/MEMORY.md Docs/TASKS.md Docs/DESIGN.md Docs/INDEX.md
```

**方式B：使用Git克隆**

```bash
# 克隆仓库
git clone https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM.git temp-qa

# 复制到你的项目
cp -r temp-qa/.opencode ./
cp temp-qa/AGENTS.md ./
cp temp-qa/opencode.json ./
mkdir -p Docs
cp -r temp-qa/Docs/* Docs/

# 清理
rm -rf temp-qa
```

### 4. 配置模型

创建 `.opencode/config/models.json`:

```json
{
  "primary": "glm-5",
  "categories": {
    "quick": "glm-5-flash",
    "planning": "glm-5",
    "coding": "glm-5"
  }
}
```

### 5. 初始化数据库

```bash
# 初始化UnifiedDB
python -c "from quickagents import UnifiedDB; db = UnifiedDB(); print('数据库已初始化')"

# 安装Git钩子（可选）
qa hooks install
```

### 6. 验证安装

```bash
# 1. 检查Python包
python -c "
from quickagents import __version__, UnifiedDB, KnowledgeGraph
print(f'QuickAgents v{__version__}')
db = UnifiedDB()
kg = KnowledgeGraph()
print('所有模块导入成功')
"

# 2. 检查CLI
qa --help
qa stats

# 3. 检查OpenCode配置
test -f AGENTS.md && echo "✅ AGENTS.md"
test -f opencode.json && echo "✅ opencode.json"
test -d .opencode && echo "✅ .opencode/"
test -f .opencode/plugins/quickagents.ts && echo "✅ 插件"
test -d .opencode/agents && echo "✅ 代理 ($(ls .opencode/agents/*.md 2>/dev/null | wc -l) 个文件)"
test -d .opencode/skills && echo "✅ 技能 ($(ls -d .opencode/skills/*/ 2>/dev/null | wc -l) 个目录)"
```

---

## CLI命令参考

```bash
# 数据库操作
qa stats                      # 显示统计信息
qa sync                       # 同步SQLite到Markdown
qa memory get <key>           # 获取记忆
qa memory set <key> <value>   # 设置记忆
qa memory search <query>      # 搜索记忆

# 任务管理
qa tasks list                 # 列出任务
qa tasks add <id> <name>      # 添加任务

# 进化系统
qa evolution status           # 显示进化状态
qa evolution optimize         # 执行优化

# Git钩子
qa hooks install              # 安装Git钩子
qa hooks status               # 检查钩子状态

# 知识图谱
qa kg search <query>          # 搜索知识图谱
qa kg trace <node-id>         # 追踪需求

# TDD工作流
qa tdd red <test_file>        # 运行RED阶段
qa tdd green <test_file>      # 运行GREEN阶段
qa tdd refactor <test_file>   # 运行REFACTOR阶段
```

---

## 使用方法

### 启动QuickAgents

在OpenCode中发送以下触发词之一：

```
启动QuickAgent
启动QuickAgents
启动QA
Start QA
```

### 常用工作流

**新项目：**
```
启动QuickAgent
# 按照交互提示操作
```

**继续开发：**
```
/start-work
# 从上次会话恢复
```

**代码审查：**
```
@code-reviewer 审查认证模块
```

**TDD开发：**
```
@yinglong-init 使用TDD实现用户认证
```

---

## 故障排查

### 找不到Python

```bash
# Windows：检查PATH
where python

# macOS/Linux：检查PATH
which python3

# 如果找不到，重新安装Python并勾选"Add to PATH"
```

### pip安装失败

```bash
# 升级pip
python -m pip install --upgrade pip

# 使用--user标志
pip install --user quickagents

# 清除缓存
pip cache purge
pip install quickagents --no-cache-dir
```

### 插件未加载

```bash
# 检查插件是否存在
ls .opencode/plugins/quickagents.ts

# 检查opencode.json
cat opencode.json

# 应该显示：
# {"plugin": ["@coder-beam/quickagents"]}
```

### 数据库错误

```bash
# 重置数据库
rm -rf .quickagents/
python -c "from quickagents import UnifiedDB; UnifiedDB()"
```

### CLI未找到

```bash
# 检查安装
pip show quickagents

# 重新安装
pip install --force-reinstall quickagents

# 检查PATH
qa --help
```

---

## 升级

```bash
# 升级Python包
pip install --upgrade quickagents

# 更新OpenCode配置
curl -fsSL https://codeload.github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/tar.gz/main | tar -xz --strip-components=1 Quick-Agents-for-Z.AI-GLM/.opencode
```

---

## 卸载

```bash
# 移除Python包
pip uninstall quickagents

# 移除配置文件
rm -rf .opencode/ AGENTS.md opencode.json

# 移除数据库
rm -rf .quickagents/
```

---

## 支持

- **GitHub**: https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM
- **问题反馈**: https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/issues
- **PyPI**: https://pypi.org/project/quickagents/
