---
name: update-skill
description: |
  QuickAgents版本检测和更新功能。
  命令: /qa-update
  功能: 检测新版本、下载更新、智能合并配置
license: MIT
allowed-tools:
  - read
  - write
  - edit
  - bash
  - webfetch
metadata:
  category: system
  priority: high
  version: 1.0.0
---

# Update Skill

QuickAgents版本检测和更新功能。

---

## 命令

| 命令 | 功能 |
|------|------|
| `/qa-update` | 检测并更新 |
| `/qa-update --check` | 仅检测，不更新 |
| `/qa-update --version` | 显示当前版本 |

---

## 版本检测

### 检测流程

```
1. 读取本地 .quickagents/VERSION.md
   - 不存在则视为首次安装

2. 获取远程 VERSION.md
   - URL: https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/VERSION.md

3. 对比版本号
   - 相同: 无需更新
   - 不同: 提示用户更新
```

### 版本号格式

```
主版本.次版本.修订号
例如: 2.1.1
```

---

## 更新流程

### 1. 检测新版本

```
/qa-update

AI: 正在检测新版本...
    当前版本: v2.1.0
    最新版本: v2.1.1
    
    发现新版本!
```

### 2. 显示更新日志

```
AI: v2.1.1 更新内容:
    
    新增功能:
    - feedback-collector-skill 经验收集系统
    
    更新内容:
    - Skills总数: 18 → 19
    
    是否更新? (y/n)
```

### 3. 备份配置

```
用户: y

AI: 正在备份配置...
    ✓ .opencode/config/ → .opencode/config.backup/20260328_103000/
    ✓ Docs/ → Docs.backup/20260328_103000/
```

### 4. 下载更新

```
AI: 正在下载更新...
    ✓ .opencode/agents/
    ✓ .opencode/skills/
    ✓ .opencode/commands/
    ✓ .opencode/hooks/
    ✓ AGENTS.md
    ✓ VERSION.md
```

### 5. 智能合并配置

```
AI: 正在合并配置...
    ✓ categories.json - 合并完成
    ✓ quickagents.json - 保留用户配置
    ! models.json - 不覆盖用户配置
    ! lsp-config.json - 不覆盖用户配置
```

### 6. 同步文档

```
AI: 正在同步文档...
    ✓ Docs/ ↔ .opencode/memory/
```

### 7. 更新完成

```
AI: ✓ 更新完成!
    
    版本: v2.1.1
    备份位置: .opencode/config.backup/20260328_103000/
    
    如需回滚: /qa-update --rollback
```

---

## 配置处理策略

### 需备份的目录

| 目录 | 处理方式 |
|------|----------|
| `.opencode/config/` | 备份 + 智能合并 |
| `Docs/` | 备份 + 覆盖更新 |

### 不更新的目录

| 目录 | 原因 |
|------|------|
| `.opencode/memory/` | 用户数据 |
| `.quickagents/` | 用户数据 |

### 智能合并规则

```yaml
categories.json:
  - 保留用户自定义分类
  - 新增官方分类
  - 冲突时用户优先

quickagents.json:
  - 保留用户配置值
  - 新增官方配置项
  - 冲突时提示用户

models.json:
  - 完全保留用户配置
  - 不覆盖

lsp-config.json:
  - 完全保留用户配置
  - 不覆盖
```

---

## 备份命名规则

```
.opencode/config.backup/YYYYMMDD_HHMMSS/
Docs.backup/YYYYMMDD_HHMMSS/
```

示例: `.opencode/config.backup/20260328_103000/`

---

## 错误处理

| 错误 | 处理 |
|------|------|
| 网络连接失败 | 提示检查网络，稍后重试 |
| VERSION.md损坏 | 重新下载 |
| 更新中断 | 提示从备份恢复 |
| 配置合并冲突 | 保留两份，提示用户处理 |

---

## 回滚功能

```bash
/qa-update --rollback
```

```
AI: 可用备份:
    1. 20260328_103000 (v2.1.0)
    2. 20260327_140000 (v2.0.1)
    
    选择要恢复的备份 (1/2/cancel):
```

---

## 首次安装

如果本地没有 `.quickagents/VERSION.md`:

```
AI: 检测到首次安装 QuickAgents
    正在初始化版本信息...
    ✓ 创建 .quickagents/VERSION.md
    ✓ 当前版本: v2.1.1
```

---

## 与其他Skill集成

| Skill | 集成方式 |
|-------|----------|
| yinglong-init | 启动时调用版本检测 |
| feedback-collector-skill | 更新后收集用户反馈 |

---

## 更新范围

### 全量更新文件

```
.opencode/agents/       # 所有代理
.opencode/skills/       # 所有技能
.opencode/commands/     # 所有命令
.opencode/hooks/        # 所有钩子
AGENTS.md               # 开发规范
VERSION.md              # 版本信息
```

### 智能合并文件

```
.opencode/config/categories.json
.opencode/config/quickagents.json
```

### 不更新文件

```
.opencode/config/models.json      # 用户模型配置
.opencode/config/lsp-config.json  # 用户LSP配置
.opencode/memory/                 # 项目记忆
.quickagents/                     # 用户数据
```

---

*版本: 1.0.0 | 创建时间: 2026-03-28*
