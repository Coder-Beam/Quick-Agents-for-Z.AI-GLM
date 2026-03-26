# QuickAgents Agent 使用指南

> 本指南详细介绍17个专业代理的使用方法、协作关系和最佳实践

**[中文](#中文)** | **[English](#english)**

---

# 中文

## 目录

- [快速导航](#快速导航)
- [Agent分类概览](#agent分类概览)
- [Agent调用方式](#agent调用方式)
- [核心代理详解](#核心代理详解)
- [质量代理详解](#质量代理详解)
- [工具代理详解](#工具代理详解)
- [规划代理详解](#规划代理详解)
- [Agent协作关系图](#agent协作关系图)
- [使用场景推荐](#使用场景推荐)
- [最佳实践](#最佳实践)

---

## 快速导航

| 使用场景 | 推荐代理 | 调用方式 |
|----------|---------|---------|
| **首次使用/项目初始化** | yinglong-init | `启动QuickAgent` |
| **日常开发对话** | fenghou-orchestrate | 直接对话 |
| **制定计划(Plan Mode)** | boyi-consult + fenghou-plan | `@boyi-consult` 或 `@fenghou-plan` |
| **实际开发执行** | fenghou-orchestrate | `@fenghou-orchestrate` 或 `/ultrawork` |
| **代码审查** | jianming-review | `@jianming-review` |
| **测试执行** | lishou-test | `@lishou-test` |
| **安全审计** | mengzhang-security | `@mengzhang-security` |
| **性能分析** | hengge-perf | `@hengge-perf` |
| **调试问题** | kuafu-debug | `@kuafu-debug` |
| **代码重构** | gonggu-refactor | `@gonggu-refactor` |
| **依赖管理** | huodi-deps | `@huodi-deps` |
| **CI/CD管理** | hengge-cicd | `@hengge-cicd` |
| **文档编写** | cangjie-doc | `@cangjie-doc` |
| **Skill管理** | huodi-skill | `@huodi-skill` |
| **技术推荐** | chisongzi-advise | `@chisongzi-advise` |

---

## Agent分类概览

### 🏆 核心代理（6个）

| 代理 | 中文名称 | 核心职责 |
|------|---------|---------|
| yinglong-init | 应龙初始化 | 项目初始化、配置引导 |
| boyi-consult | 伯益顾问 | 需求分析、可行性评估 |
| chisongzi-advise | 赤松子顾问 | 技术栈推荐、方案选型 |
| cangjie-doc | 仓颉文档 | 文档管理、知识创作 |
| huodi-skill | 祝融技能 | Skill管理、工具创造 |
| fenghou-orchestrate | 风后调度 | 主调度器、任务协调 |

### 🔍 质量代理（4个）

| 代理 | 中文名称 | 核心职责 |
|------|---------|---------|
| jianming-review | 简明审查 | 代码审查、质量保证 |
| lishou-test | 力寿测试 | 测试执行、质量验证 |
| mengzhang-security | 孟章安全 | 安全审计、漏洞检测 |
| hengge-perf | 横革性能 | 性能分析、优化建议 |

### 🛠️ 工具代理（4个）

| 代理 | 中文名称 | 核心职责 |
|------|---------|---------|
| kuafu-debug | 夸父调试 | 问题追踪、调试分析 |
| gonggu-refactor | 共工重构 | 代码重构、架构改进 |
| huodi-deps | 祝融依赖 | 依赖管理、版本控制 |
| hengge-cicd | 横革流水 | CI/CD管理、流程自动化 |

### 📋 规划代理（3个）

| 代理 | 中文名称 | 核心职责 |
|------|---------|---------|
| fenghou-plan | 风后规划 | 战略规划、任务分解 |
| boyi-consult | 伯益顾问 | 需求分析（兼任） |
| jianming-review | 简明审查 | 计划审查（兼任） |

---

## Agent调用方式

### 1. 触发词自动调用

```
启动QuickAgent
```

自动调用 `yinglong-init` 代理进行项目初始化。

### 2. @提及直接调用

```
@jianming-review 请审查这个文件
```

直接调用指定代理执行任务。

### 3. AI智能调度

直接描述任务，AI会自动选择合适的代理：

```
帮我测试这个模块
```

系统会自动调度 `lishou-test` 代理。

### 4. 命令触发

```
/ultrawork 实现用户认证功能
```

使用命令触发高效执行模式。

---

## 核心代理详解

### yinglong-init（应龙初始化）

**身份**：项目初始化代理 - 象征创世与起源

**核心能力**：
- 项目类型检测（新项目/现有项目）
- 配置文件检查与引导
- 7层需求澄清问询
- 文档结构创建
- 标准代理创建

**使用场景**：
- 新项目启动
- 现有项目接入QuickAgents
- 配置文件初始化

**调用方式**：
```
启动QuickAgent
```

**首次配置引导**：

如果检测到配置文件为空，系统会弹出交互式询问卡：

```markdown
## 🔧 首次配置向导

### 1. 模型配置

**Q1**: 您主要使用哪个AI模型？
- [ ] GLM-5（推荐，默认）
- [ ] GLM-5-Flash（快速响应）
- [ ] GPT-4o（需自行配置API Key）
- [ ] 其他（请手动配置）

**Q2**: 是否需要多模型协同？
- [ ] 否，仅使用单一模型
- [ ] 是，需要智能路由和fallback

### 2. LSP配置

**Q3**: 您的主要开发语言？（可多选）
- [ ] TypeScript/JavaScript
- [ ] Python
- [ ] Rust
- [ ] Go
- [ ] Java
- [ ] C/C++
```

---

### boyi-consult（伯益顾问）

**身份**：需求分析与顾问代理 - 深度分析需求、评估可行性

**核心能力**：
- 需求深度分析
- 可行性评估
- 风险识别
- 方案建议

**使用场景**：
- 复杂需求分析
- 技术方案评估
- 项目可行性研究

**调用方式**：
```
@boyi-consult 请分析这个需求的可行性
```

---

### chisongzi-advise（赤松子顾问）

**身份**：技术栈推荐代理 - 跨领域技术指引与方案推荐

**核心能力**：
- 技术栈选型
- 架构方案推荐
- 技术债务评估
- 最佳实践建议

**使用场景**：
- 新项目技术选型
- 架构升级建议
- 技术栈优化

**调用方式**：
```
@chisongzi-advise 推荐一个适合电商项目的技术栈
```

---

### cangjie-doc（仓颉文档）

**身份**：文档管理代理 - 文字创作与文档管理的象征

**核心能力**：
- 文档生成
- 文档更新
- 知识库维护
- API文档编写

**使用场景**：
- 自动生成文档
- 更新README
- 编写API文档

**调用方式**：
```
@cangjie-doc 为这个模块生成文档
```

---

### huodi-skill（祝融技能）

**身份**：Skill管理代理 - 工具/Skill的创造与管理

**核心能力**：
- Skill创建
- Skill更新
- Skill验证
- Skill集成

**使用场景**：
- 创建新的Skill
- 更新现有Skill
- Skill问题排查

**调用方式**：
```
@huodi-skill 创建一个新的代码格式化Skill
```

---

### fenghou-orchestrate（风后调度）

**身份**：主调度器 - 执行层协调器，负责系统化任务编排和协调

**核心能力**：
- 任务分类
- 代理调度
- 执行协调
- 结果整合

**使用场景**：
- 复杂任务执行
- 多代理协作
- 工作流编排

**调用方式**：
```
@fenghou-orchestrate 实现用户认证功能
```

或直接描述任务，系统会自动调度。

---

## 质量代理详解

### jianming-review（简明审查）

**身份**：质量审查代理 - 审查计划质量、审查代码实现、确保标准合规

**核心能力**：
- 代码审查
- 计划审查
- 标准合规检查
- 质量报告生成

**使用场景**：
- 代码合并前审查
- 计划质量评估
- 代码规范检查

**调用方式**：
```
@jianming-review 审查这个Pull Request
```

---

### lishou-test（力寿测试）

**身份**：测试执行代理 - 算数始祖，负责计量计算与测试执行

**核心能力**：
- 单元测试执行
- 集成测试执行
- 测试覆盖率分析
- 测试报告生成

**使用场景**：
- 运行测试套件
- 测试覆盖率检查
- 测试失败分析

**调用方式**：
```
@lishou-test 运行所有测试并生成覆盖率报告
```

---

### mengzhang-security（孟章安全）

**身份**：安全审计代理 - 青龙七宿之首，守护象征，负责安全防护

**核心能力**：
- 安全漏洞检测
- 依赖安全检查
- 代码安全审计
- 安全报告生成

**使用场景**：
- 安全审计
- 漏洞扫描
- 依赖安全检查

**调用方式**：
```
@mengzhang-security 进行安全审计
```

---

### hengge-perf（横革性能）

**身份**：性能分析代理 - 大禹治水功臣，擅长执行落地与性能优化

**核心能力**：
- 性能瓶颈分析
- 性能优化建议
- 资源使用监控
- 性能报告生成

**使用场景**：
- 性能问题排查
- 性能优化
- 资源使用分析

**调用方式**：
```
@hengge-perf 分析这个模块的性能瓶颈
```

---

## 工具代理详解

### kuafu-debug（夸父调试）

**身份**：调试代理 - 追逐太阳的巨人，代表探索追踪与问题调试

**核心能力**：
- 问题追踪
- 错误分析
- 调试建议
- 日志分析

**使用场景**：
- Bug调试
- 错误追踪
- 问题定位

**调用方式**：
```
@kuafu-debug 帮我调试这个问题
```

---

### gonggu-refactor（共工重构）

**身份**：重构代理 - 舟船发明者，工具创造者，负责代码重构与改进

**核心能力**：
- 代码重构
- 架构改进
- 代码简化
- 技术债务清理

**使用场景**：
- 代码重构
- 架构优化
- 代码清理

**调用方式**：
```
@gonggu-refactor 重构这个模块
```

---

### huodi-deps（祝融依赖）

**身份**：依赖管理代理 - 工具创造者，负责依赖工具管理

**核心能力**：
- 依赖更新
- 版本管理
- 依赖冲突解决
- 依赖安全检查

**使用场景**：
- 依赖更新
- 版本升级
- 依赖问题解决

**调用方式**：
```
@huodi-deps 检查并更新所有依赖
```

---

### hengge-cicd（横革流水）

**身份**：CI/CD管理代理 - 大禹治水功臣，擅长流程执行与落地实施

**核心能力**：
- CI/CD配置
- 流程自动化
- 部署管理
- 环境配置

**使用场景**：
- CI/CD配置
- 部署自动化
- 流程优化

**调用方式**：
```
@hengge-cicd 配置GitHub Actions
```

---

## 规划代理详解

### fenghou-plan（风后规划）

**身份**：规划器代理 - 先知之神，象征远见和智慧

**核心能力**：
- 战略规划
- 任务分解
- 里程碑定义
- 风险评估

**使用场景**：
- 项目规划
- 任务分解
- 计划制定

**调用方式**：
```
@fenghou-plan 制定一个三个月的开发计划
```

---

## Agent协作关系图

```
┌─────────────────────────────────────────────────────────────────┐
│                    QuickAgents Agent 协作图                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  【入口】                                                         │
│    └─ 触发词："启动QuickAgent"                                   │
│          ↓                                                       │
│    ┌──────────────────────────────────────┐                     │
│    │  yinglong-init（项目初始化）          │                     │
│    │  ├─ 检测项目类型                      │                     │
│    │  ├─ 检查配置文件                      │                     │
│    │  └─ 启动需求问询                      │                     │
│    └──────────────┬───────────────────────┘                     │
│                   ↓                                              │
│    ┌──────────────────────────────────────┐                     │
│    │  boyi-consult（需求分析）             │                     │
│    │  └─ 深度分析、可行性评估              │                     │
│    └──────────────┬───────────────────────┘                     │
│                   ↓                                              │
│    ┌──────────────────────────────────────┐                     │
│    │  chisongzi-advise（技术推荐）         │                     │
│    │  └─ 技术栈选型、架构建议              │                     │
│    └──────────────┬───────────────────────┘                     │
│                   ↓                                              │
│    ┌──────────────────────────────────────┐                     │
│    │  fenghou-plan（规划）                 │                     │
│    │  └─ 任务分解、里程碑定义              │                     │
│    └──────────────┬───────────────────────┘                     │
│                   ↓                                              │
│    ┌──────────────────────────────────────┐                     │
│    │  fenghou-orchestrate（主调度）        │                     │
│    │  ├─ 任务分类                          │                     │
│    │  └─ 代理调度                          │                     │
│    └──────────────┬───────────────────────┘                     │
│                   │                                              │
│     ┌─────────────┼─────────────┐                               │
│     ↓             ↓             ↓                               │
│  ┌────────┐  ┌────────┐  ┌────────┐                            │
│  │执行阶段│  │质量阶段│  │工具阶段│                            │
│  ├────────┤  ├────────┤  ├────────┤                            │
│  │gonggu  │  │jianming│  │kuafu   │                            │
│  │huodi   │  │lishou  │  │hengge  │                            │
│  │hengge  │  │mengzhan│  │        │                            │
│  └────────┘  └────────┘  └────────┘                            │
│                   │                                              │
│                   ↓                                              │
│    ┌──────────────────────────────────────┐                     │
│    │  cangjie-doc（文档管理）              │                     │
│    │  └─ 文档生成、知识库维护              │                     │
│    └──────────────────────────────────────┘                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 使用场景推荐

### 场景1：新项目启动

```
1. 用户：启动QuickAgent
   → yinglong-init 自动启动

2. 回答配置询问（首次使用）
   → 配置 models.json 和 lsp-config.json

3. 回答需求问询（7层）
   → boyi-consult 进行需求分析

4. 确认技术方案
   → chisongzi-advise 推荐技术栈

5. 开始执行
   → fenghou-orchestrate 调度执行
```

### 场景2：日常开发

```
1. 用户：帮我实现用户登录功能
   → fenghou-orchestrate 自动调度

2. 质量检查
   → jianming-review 代码审查
   → lishou-test 运行测试

3. 提交代码
   → git-commit-skill 自动提交
```

### 场景3：问题调试

```
1. 用户：@kuafu-debug 这个测试失败了
   → kuafu-debug 分析问题

2. 定位原因
   → kuafu-debug 提供调试建议

3. 修复问题
   → gonggu-refactor 或直接修复
```

---

## 最佳实践

### 1. 选择合适的代理

- **简单任务**：直接描述，让AI自动调度
- **复杂任务**：使用 `@代理名` 明确指定
- **跨会话恢复**：使用 `/start-work`

### 2. 充分利用问询

- 不要跳过需求问询环节
- 详细回答每个问题
- 及时提出疑问

### 3. 定期检查质量

- 代码完成后使用 `@jianming-review`
- 测试覆盖率达标后再提交
- 定期进行安全审计

### 4. 保持文档同步

- 使用 `@cangjie-doc` 自动生成文档
- 每次提交前检查文档更新
- 保持 MEMORY.md 的时效性

---

*版本: 2.0.1 | 更新时间: 2026-03-26*

---

# English

## Table of Contents

- [Quick Navigation](#quick-navigation-en)
- [Agent Categories Overview](#agent-categories-overview-en)
- [Agent Invocation Methods](#agent-invocation-methods-en)
- [Core Agents](#core-agents-en)
- [Quality Agents](#quality-agents-en)
- [Tool Agents](#tool-agents-en)
- [Planning Agents](#planning-agents-en)
- [Agent Collaboration Diagram](#agent-collaboration-diagram-en)
- [Usage Scenario Recommendations](#usage-scenario-recommendations-en)
- [Best Practices](#best-practices-en)

---

## Quick Navigation (EN)

| Scenario | Recommended Agent | Invocation |
|----------|------------------|------------|
| **First Use/Project Init** | yinglong-init | `启动QuickAgent` |
| **Daily Development** | fenghou-orchestrate | Direct conversation |
| **Planning (Plan Mode)** | boyi-consult + fenghou-plan | `@boyi-consult` or `@fenghou-plan` |
| **Development Execution** | fenghou-orchestrate | `@fenghou-orchestrate` or `/ultrawork` |
| **Code Review** | jianming-review | `@jianming-review` |
| **Testing** | lishou-test | `@lishou-test` |
| **Security Audit** | mengzhang-security | `@mengzhang-security` |
| **Performance Analysis** | hengge-perf | `@hengge-perf` |
| **Debugging** | kuafu-debug | `@kuafu-debug` |
| **Refactoring** | gonggu-refactor | `@gonggu-refactor` |
| **Dependency Management** | huodi-deps | `@huodi-deps` |
| **CI/CD Management** | hengge-cicd | `@hengge-cicd` |
| **Documentation** | cangjie-doc | `@cangjie-doc` |
| **Skill Management** | huodi-skill | `@huodi-skill` |
| **Tech Recommendation** | chisongzi-advise | `@chisongzi-advise` |

---

## Agent Categories Overview (EN)

### 🏆 Core Agents (6)

| Agent | Role | Core Responsibility |
|-------|------|---------------------|
| yinglong-init | Project Initialization | Project init, config guidance |
| boyi-consult | Consultant | Requirements analysis, feasibility |
| chisongzi-advise | Tech Advisor | Tech stack recommendation |
| cangjie-doc | Documentation | Doc management, knowledge creation |
| huodi-skill | Skill Manager | Skill management, tool creation |
| fenghou-orchestrate | Orchestrator | Main scheduler, task coordination |

### 🔍 Quality Agents (4)

| Agent | Role | Core Responsibility |
|-------|------|---------------------|
| jianming-review | Code Reviewer | Code review, quality assurance |
| lishou-test | Test Runner | Test execution, quality verification |
| mengzhang-security | Security Auditor | Security audit, vulnerability detection |
| hengge-perf | Performance Analyst | Performance analysis, optimization |

### 🛠️ Tool Agents (4)

| Agent | Role | Core Responsibility |
|-------|------|---------------------|
| kuafu-debug | Debugger | Issue tracking, debugging |
| gonggu-refactor | Refactorer | Code refactoring, architecture improvement |
| huodi-deps | Dependency Manager | Dependency management, version control |
| hengge-cicd | CI/CD Manager | CI/CD management, process automation |

### 📋 Planning Agents (3)

| Agent | Role | Core Responsibility |
|-------|------|---------------------|
| fenghou-plan | Planner | Strategic planning, task breakdown |
| boyi-consult | Consultant | Requirements analysis (dual role) |
| jianming-review | Reviewer | Plan review (dual role) |

---

## Agent Invocation Methods (EN)

### 1. Trigger Word Auto-Invocation

```
启动QuickAgent
```

Automatically invokes `yinglong-init` agent for project initialization.

### 2. @Mention Direct Invocation

```
@jianming-review Please review this file
```

Directly invokes the specified agent for a task.

### 3. AI Smart Dispatch

Simply describe the task, AI will automatically select the appropriate agent:

```
Help me test this module
```

The system will automatically dispatch `lishou-test` agent.

### 4. Command Trigger

```
/ultrawork Implement user authentication
```

Use command to trigger efficient execution mode.

---

## Core Agents (EN)

### yinglong-init

**Identity**: Project Initialization Agent - Symbolizing creation and origin

**Core Capabilities**:
- Project type detection (new/existing)
- Configuration file checking and guidance
- 7-layer requirements inquiry
- Document structure creation
- Standard agent creation

**Usage Scenarios**:
- New project startup
- Existing project QuickAgents integration
- Configuration file initialization

**Invocation**:
```
启动QuickAgent
```

---

### boyi-consult

**Identity**: Requirements Analysis & Consulting Agent

**Core Capabilities**:
- Deep requirements analysis
- Feasibility assessment
- Risk identification
- Solution recommendations

**Invocation**:
```
@boyi-consult Please analyze the feasibility of this requirement
```

---

### chisongzi-advise

**Identity**: Tech Stack Recommendation Agent

**Core Capabilities**:
- Tech stack selection
- Architecture recommendation
- Technical debt assessment
- Best practices advice

**Invocation**:
```
@chisongzi-advise Recommend a tech stack for an e-commerce project
```

---

### cangjie-doc

**Identity**: Documentation Management Agent

**Core Capabilities**:
- Document generation
- Document updates
- Knowledge base maintenance
- API documentation

**Invocation**:
```
@cangjie-doc Generate documentation for this module
```

---

### huodi-skill

**Identity**: Skill Management Agent

**Core Capabilities**:
- Skill creation
- Skill updates
- Skill verification
- Skill integration

**Invocation**:
```
@huodi-skill Create a new code formatting skill
```

---

### fenghou-orchestrate

**Identity**: Main Orchestrator - Execution layer coordinator

**Core Capabilities**:
- Task classification
- Agent dispatching
- Execution coordination
- Result integration

**Invocation**:
```
@fenghou-orchestrate Implement user authentication
```

Or simply describe the task, the system will dispatch automatically.

---

## Quality Agents (EN)

### jianming-review

**Identity**: Code Review Agent

**Core Capabilities**:
- Code review
- Plan review
- Standards compliance
- Quality report generation

**Invocation**:
```
@jianming-review Review this Pull Request
```

---

### lishou-test

**Identity**: Test Execution Agent

**Core Capabilities**:
- Unit test execution
- Integration test execution
- Test coverage analysis
- Test report generation

**Invocation**:
```
@lishou-test Run all tests and generate coverage report
```

---

### mengzhang-security

**Identity**: Security Audit Agent

**Core Capabilities**:
- Security vulnerability detection
- Dependency security check
- Code security audit
- Security report generation

**Invocation**:
```
@mengzhang-security Conduct security audit
```

---

### hengge-perf

**Identity**: Performance Analysis Agent

**Core Capabilities**:
- Performance bottleneck analysis
- Performance optimization
- Resource usage monitoring
- Performance report generation

**Invocation**:
```
@hengge-perf Analyze performance bottlenecks in this module
```

---

## Tool Agents (EN)

### kuafu-debug

**Identity**: Debugging Agent

**Core Capabilities**:
- Issue tracking
- Error analysis
- Debugging suggestions
- Log analysis

**Invocation**:
```
@kuafu-debug Help me debug this issue
```

---

### gonggu-refactor

**Identity**: Refactoring Agent

**Core Capabilities**:
- Code refactoring
- Architecture improvement
- Code simplification
- Technical debt cleanup

**Invocation**:
```
@gonggu-refactor Refactor this module
```

---

### huodi-deps

**Identity**: Dependency Management Agent

**Core Capabilities**:
- Dependency updates
- Version management
- Dependency conflict resolution
- Dependency security check

**Invocation**:
```
@huodi-deps Check and update all dependencies
```

---

### hengge-cicd

**Identity**: CI/CD Management Agent

**Core Capabilities**:
- CI/CD configuration
- Process automation
- Deployment management
- Environment configuration

**Invocation**:
```
@hengge-cicd Configure GitHub Actions
```

---

## Planning Agents (EN)

### fenghou-plan

**Identity**: Planner Agent

**Core Capabilities**:
- Strategic planning
- Task breakdown
- Milestone definition
- Risk assessment

**Invocation**:
```
@fenghou-plan Create a three-month development plan
```

---

## Agent Collaboration Diagram (EN)

```
┌─────────────────────────────────────────────────────────────────┐
│                    QuickAgents Agent Collaboration              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  【Entry】                                                       │
│    └─ Trigger: "启动QuickAgent"                                  │
│          ↓                                                       │
│    ┌──────────────────────────────────────┐                     │
│    │  yinglong-init (Project Init)        │                     │
│    │  ├─ Detect project type              │                     │
│    │  ├─ Check config files               │                     │
│    │  └─ Start requirements inquiry       │                     │
│    └──────────────┬───────────────────────┘                     │
│                   ↓                                              │
│    ┌──────────────────────────────────────┐                     │
│    │  boyi-consult (Requirements)         │                     │
│    │  └─ Deep analysis, feasibility       │                     │
│    └──────────────┬───────────────────────┘                     │
│                   ↓                                              │
│    ┌──────────────────────────────────────┐                     │
│    │  chisongzi-advise (Tech Rec)         │                     │
│    │  └─ Tech stack, architecture         │                     │
│    └──────────────┬───────────────────────┘                     │
│                   ↓                                              │
│    ┌──────────────────────────────────────┐                     │
│    │  fenghou-plan (Planning)             │                     │
│    │  └─ Task breakdown, milestones       │                     │
│    └──────────────┬───────────────────────┘                     │
│                   ↓                                              │
│    ┌──────────────────────────────────────┐                     │
│    │  fenghou-orchestrate (Orchestrator)  │                     │
│    │  ├─ Task classification              │                     │
│    │  └─ Agent dispatching                │                     │
│    └──────────────┬───────────────────────┘                     │
│                   │                                              │
│     ┌─────────────┼─────────────┐                               │
│     ↓             ↓             ↓                               │
│  ┌────────┐  ┌────────┐  ┌────────┐                            │
│  │Execute │  │Quality │  │ Tools  │                            │
│  ├────────┤  ├────────┤  ├────────┤                            │
│  │gonggu  │  │jianming│  │kuafu   │                            │
│  │huodi   │  │lishou  │  │hengge  │                            │
│  │hengge  │  │mengzhan│  │        │                            │
│  └────────┘  └────────┘  └────────┘                            │
│                   │                                              │
│                   ↓                                              │
│    ┌──────────────────────────────────────┐                     │
│    │  cangjie-doc (Documentation)         │                     │
│    │  └─ Doc generation, knowledge base   │                     │
│    └──────────────────────────────────────┘                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Usage Scenario Recommendations (EN)

### Scenario 1: New Project Startup

```
1. User: 启动QuickAgent
   → yinglong-init auto-starts

2. Answer config questions (first use)
   → Configure models.json and lsp-config.json

3. Answer requirements inquiry (7 layers)
   → boyi-consult analyzes requirements

4. Confirm tech solution
   → chisongzi-advise recommends tech stack

5. Start execution
   → fenghou-orchestrate dispatches execution
```

### Scenario 2: Daily Development

```
1. User: Help me implement user login
   → fenghou-orchestrate auto-dispatches

2. Quality check
   → jianming-review code review
   → lishou-test runs tests

3. Commit code
   → git-commit-skill auto-commits
```

### Scenario 3: Debugging Issues

```
1. User: @kuafu-debug This test is failing
   → kuafu-debug analyzes the issue

2. Identify cause
   → kuafu-debug provides debugging suggestions

3. Fix the issue
   → gonggu-refactor or direct fix
```

---

## Best Practices (EN)

### 1. Choose the Right Agent

- **Simple tasks**: Describe directly, let AI auto-dispatch
- **Complex tasks**: Use `@agent-name` to specify
- **Cross-session recovery**: Use `/start-work`

### 2. Leverage Inquiries Fully

- Don't skip requirements inquiry
- Answer each question in detail
- Raise questions promptly

### 3. Regular Quality Checks

- Use `@jianming-review` after code completion
- Submit only after test coverage meets requirements
- Conduct regular security audits

### 4. Keep Documentation Synced

- Use `@cangjie-doc` to auto-generate docs
- Check doc updates before each commit
- Maintain MEMORY.md timeliness

---

*Version: 2.0.1 | Last Updated: 2026-03-26*
