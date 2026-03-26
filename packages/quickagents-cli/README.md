# QuickAgents CLI

> QuickAgents 命令行工具 - AI代理项目初始化系统

[![npm version](https://badge.fury.io/js/quickagents-cli.svg)](https://badge.fury.io/js/quickagents-cli)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 安装

```bash
# 使用 npm
npm install -g quickagents-cli

# 使用 pnpm
pnpm add -g quickagents-cli

# 使用 yarn
yarn global add quickagents-cli
```

## 快速开始

```bash
# 初始化项目
qa init

# 启动会话
qa start

# 查看状态
qa status
```

## 命令

### `qa init [options]`

在当前目录初始化 QuickAgents 项目。

**选项:**
- `-t, --template <name>` - 使用指定模板 (default/minimal/full)
- `-f, --force` - 强制覆盖现有文件
- `--skip-skills` - 跳过技能安装

### `qa start [options]`

启动 QuickAgents 会话。

**选项:**
- `-a, --agent <name>` - 指定初始代理
- `-t, --task <id>` - 恢复指定任务

### `qa status [options]`

显示项目状态。

**选项:**
- `-j, --json` - JSON 格式输出
- `-d, --detailed` - 显示详细信息

### `qa agent <action> [name]`

管理代理。

**操作:**
- `list` - 列出所有代理
- `show` - 显示代理详情
- `enable` - 启用代理
- `disable` - 禁用代理

**选项:**
- `-c, --category <cat>` - 按类别筛选

### `qa skill <action> [name]`

管理技能。

**操作:**
- `list` - 列出已安装技能
- `install` - 安装技能
- `remove` - 移除技能
- `update` - 更新技能

**选项:**
- `-r, --registry <url>` - 指定技能仓库

### `qa workflow <action> [name]`

管理工作流。

**操作:**
- `list` - 列出可用工作流
- `run` - 运行工作流
- `status` - 查看工作流状态

**选项:**
- `-t, --timeout <ms>` - 超时时间
- `--dry-run` - 模拟执行

### `qa config <action> [key] [value]`

管理配置。

**操作:**
- `get` - 获取配置值
- `set` - 设置配置值
- `list` - 列出所有配置
- `reset` - 重置配置

### `qa metrics [options]`

查看项目指标。

**选项:**
- `-p, --period <days>` - 统计周期（天），默认 7
- `-f, --format <type>` - 输出格式 (table/json)

## 项目结构

初始化后的项目结构：

```
your-project/
├── .opencode/
│   ├── agents/          # 代理配置
│   ├── skills/          # 技能配置
│   ├── commands/        # 自定义命令
│   ├── config/          # 配置文件
│   │   ├── models.json
│   │   └── coordination.json
│   ├── hooks/           # 钩子脚本
│   └── memory/          # 记忆文件
│
├── Docs/
│   ├── MEMORY.md        # 项目记忆
│   ├── TASKS.md         # 任务管理
│   ├── DESIGN.md        # 设计文档
│   └── INDEX.md         # 知识图谱
│
└── AGENTS.md            # 开发规范
```

## 模板

### Default (默认)
标准 QuickAgents 项目配置，包含核心代理和技能。

**包含代理:** yinglong-init, boyi-consult, chisongzi-advise, cangjie-doc

**包含技能:** project-memory-skill, inquiry-skill, tdd-workflow-skill

### Minimal (最小化)
最小化配置，仅包含核心代理。

**包含代理:** yinglong-init

**包含技能:** project-memory-skill

### Full (完整)
完整配置，包含所有代理和技能。

## 开发

```bash
# 克隆仓库
git clone https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM.git
cd Quick-Agents-for-Z.AI-GLM/packages/quickagents-cli

# 安装依赖
pnpm install

# 构建
pnpm build

# 测试
pnpm test
```

## 许可证

MIT License - 详见 [LICENSE](../../LICENSE) 文件

## 相关链接

- [QuickAgents 主项目](https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM)
- [问题反馈](https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/issues)
- [OpenCode](https://opencode.ai)
