# QuickAgents 正确实施方案

> 回归本质：Agent + Skill + Python脚本（可选），仅限OpenCode环境

---

## 一、QuickAgents 本质定义

### 1.1 核心定位

```
┌─────────────────────────────────────────────────────────┐
│         QuickAgents 是什么？                             │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  QuickAgents = Agent配置 + Skill配置 + Python脚本       │
│                                                          │
│  运行环境：                                               │
│  • OpenCode CLI                                         │
│  • OpenCode Desktop                                     │
│                                                          │
│  技术栈：                                                 │
│  • Agent配置：.md文件（.opencode/agents/）              │
│  • Skill配置：.md文件（.opencode/skills/）              │
│  • 执行脚本：Python脚本（可选）                          │
│                                                          │
│  不是什么：                                               │
│  ❌ 独立应用程序                                         │
│  ❌ API服务                                              │
│  ❌ 需要Docker部署                                       │
│  ❌ 需要云服务                                           │
│  ❌ 需要数据库                                           │
│  ❌ 需要Web服务器                                        │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 1.2 用户使用流程

```
┌─────────────────────────────────────────────────────────┐
│         用户如何使用QuickAgents                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  方式1：复制到新项目（最简单）                            │
│  ┌────────────────────────────────────────┐             │
│  │ 1. 复制整个QuickAgents仓库              │             │
│  │    git clone https://github.com/...    │             │
│  │                                         │             │
│  │ 2. 在OpenCode中打开项目目录             │             │
│  │    cd quickagents                      │             │
│  │    opencode .                          │             │
│  │                                         │             │
│  │ 3. 发送命令触发                         │             │
│  │    "初始化新项目"                       │             │
│  └────────────────────────────────────────┘             │
│                                                          │
│  方式2：作为模板使用                                      │
│  ┌────────────────────────────────────────┐             │
│  │ 1. GitHub Template方式                  │             │
│  │    使用此仓库作为模板创建新仓库          │             │
│  │                                         │             │
│  │ 2. 在OpenCode中打开                     │             │
│  │                                         │             │
│  │ 3. 开始对话                             │             │
│  │    "我想创建一个[项目描述]"             │             │
│  └────────────────────────────────────────┘             │
│                                                          │
│  方式3：仅使用AGENTS.md                                   │
│  ┌────────────────────────────────────────┐             │
│  │ 1. 复制AGENTS.md到项目根目录            │             │
│  │                                         │             │
│  │ 2. 在OpenCode中打开项目                 │             │
│  │                                         │             │
│  │ 3. 发送触发词                           │             │
│  │    "启动AGENTS.MD"                      │             │
│  └────────────────────────────────────────┘             │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 二、核心组件

### 2.1 Agents（代理配置）

位置：`.opencode/agents/`

#### 主要Agent列表

| Agent名称 | 文件 | 功能 | 模式 |
|----------|------|------|------|
| **yinglong-init** | yinglong-init.md | 项目初始化主代理 | primary |
| **boyi-consult** | boyi-consult.md | 需求分析代理 | subagent |
| **chisongzi-advise** | chisongzi-advise.md | 技术栈推荐代理 | subagent |
| **document-generator** | document-generator.md | 文档生成代理 | subagent |

### 2.2 Skills（技能配置）

位置：`.opencode/skills/`

#### 主要Skill列表

| Skill名称 | 目录 | 功能 |
|----------|------|------|
| **inquiry-skill** | inquiry-skill/ | 智能问答技能 |
| **memory-skill** | memory-skill/ | 记忆管理技能 |
| **template-skill** | template-skill/ | 模板生成技能 |
| **validation-skill** | validation-skill/ | 配置验证技能 |

### 2.3 Scripts（执行脚本）

位置：`.opencode/scripts/`（可选）

#### Python脚本列表

| 脚本名称 | 功能 |
|---------|------|
| generate_structure.py | 生成项目目录结构 |
| validate_config.py | 验证配置完整性 |
| sync_memory.py | 同步记忆文件 |

---

## 三、实施计划

### 阶段1：Agent配置开发（1周）

**任务**：
- [ ] 创建yinglong-init.md
- [ ] 创建boyi-consult.md
- [ ] 创建chisongzi-advise.md
- [ ] 创建document-generator.md

**交付物**：
- 4个Agent配置文件
- Agent使用文档

### 阶段2：Skill配置开发（1周）

**任务**：
- [ ] 开发inquiry-skill
- [ ] 开发memory-skill
- [ ] 开发template-skill
- [ ] 开发validation-skill

**交付物**：
- 4个Skill配置目录
- Skill使用文档

### 阶段3：Python脚本开发（可选，1周）

**任务**：
- [ ] 编写generate_structure.py
- [ ] 编写validate_config.py
- [ ] 编写sync_memory.py

**交付物**：
- 3个Python脚本
- 脚本使用文档

### 阶段4：测试与文档（1周）

**任务**：
- [ ] 测试完整流程
- [ ] 编写用户指南
- [ ] 编写开发者文档
- [ ] 创建示例项目

**交付物**：
- 完整的用户文档
- 示例项目

---

## 四、技术规范

### 4.1 Agent配置规范

```yaml
---
description: Agent描述
mode: primary | subagent
model: 模型名称
temperature: 0.1-0.8
tools:
  write: true | false
  edit: true | false | ask
  bash: true | false | ask
permission:
  edit: allow | ask | deny
  bash:
    "python *": allow
    "*": ask
---

# Agent标题

## 角色定位
[Agent的角色描述]

## 核心能力
[Agent具备的核心能力]

## 工作流程
[Agent的工作流程]

## 使用示例
[使用示例]
```

### 4.2 Skill配置规范

```
skill-name/
├── skill.md          # Skill说明文档
├── templates/        # 模板文件（可选）
├── scripts/          # 脚本文件（可选）
└── references/       # 参考文档（可选）
```

### 4.3 Python脚本规范

- 使用Python 3.8+
- 仅使用标准库（除非必要）
- 提供清晰的命令行参数
- 包含完整的错误处理
- 输出格式化的结果

---

## 五、使用示例

### 示例1：快速初始化Web项目

```
用户在OpenCode中：
"初始化一个电商平台项目"

Agent响应：
📊 项目分析：
• 类型：Web应用（电商）
• 复杂度：中等
• 推荐技术栈：
  - 前端：React + TypeScript
  - 后端：Node.js + Express
  - 数据库：PostgreSQL
  - 缓存：Redis
• 预计时间：8-12周

需要确认的关键决策：
1. 使用React框架？[是/否]
2. 使用PostgreSQL数据库？[是/否]

用户：是

Agent：
✅ 正在生成项目配置...
✅ AGENTS.md 已生成
✅ Docs/ 目录已创建
✅ 开发代理已创建
✅ Skills已初始化

质量评分：92/100
可以开始开发了！
```

### 示例2：深度定制企业项目

```
用户在OpenCode中：
"启动AGENTS.MD --mode expert"

Agent：
好的，让我们深入了解您的项目。

[执行12轮深度问答]

Agent：
📊 完整分析报告已生成

✅ 详细文档：
  • AGENTS.md（完整版，30+页）
  • DESIGN.md（架构设计）
  • TASKS.md（任务拆解）
  • DECISIONS.md（决策记录）
  • 风险评估报告

✅ 开发环境：
  • 9个开发代理已创建
  • 完整的Skills体系
  • 测试配置
  • CI/CD配置

质量评分：96/100
```

---

## 六、目录结构

```
QuickAgents/
├── AGENTS.md                   # 主开发规范
├── README.md                   # 项目说明
│
├── .opencode/                  # OpenCode配置
│   ├── agents/                 # Agent配置
│   │   ├── yinglong-init.md
│   │   ├── boyi-consult.md
│   │   ├── chisongzi-advise.md
│   │   └── document-generator.md
│   │
│   ├── skills/                 # Skill配置
│   │   ├── inquiry-skill/
│   │   │   └── skill.md
│   │   ├── memory-skill/
│   │   │   └── skill.md
│   │   ├── template-skill/
│   │   │   └── skill.md
│   │   └── validation-skill/
│   │       └── skill.md
│   │
│   ├── scripts/                # Python脚本（可选）
│   │   ├── generate_structure.py
│   │   ├── validate_config.py
│   │   └── sync_memory.py
│   │
│   └── memory/                 # OpenCode记忆
│       ├── MEMORY.md
│       ├── TASKS.md
│       ├── DESIGN.md
│       ├── INDEX.md
│       └── DECISIONS.md
│
├── Docs/                       # 项目文档
│   ├── MEMORY.md
│   ├── TASKS.md
│   ├── DESIGN.md
│   ├── INDEX.md
│   └── DECISIONS.md
│
└── templates/                  # 项目模板
    ├── web-app/
    ├── api-service/
    └── cli-tool/
```

---

## 七、质量保证

### 7.1 测试清单

- [ ] Agent能被OpenCode正确识别和加载
- [ ] Skill能被Agent正确调用
- [ ] Python脚本能正常执行
- [ ] 完整流程端到端测试
- [ ] 不同项目类型测试

### 7.2 文档清单

- [ ] README.md（项目说明）
- [ ] GETTING_STARTED.md（快速开始）
- [ ] AGENTS_GUIDE.md（Agent开发指南）
- [ ] SKILLS_GUIDE.md（Skill开发指南）
- [ ] EXAMPLES.md（使用示例）

---

*文档版本: v2.0 | 创建时间: 2026-03-25*
*回归QuickAgents本质：Agent + Skill + Python脚本*
