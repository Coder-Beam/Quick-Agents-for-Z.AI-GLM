# QuickAgents 用户指南

> AI代理项目初始化系统 - 快速启动指南

---

## 目录

1. [快速开始](#快速开始)
2. [核心概念](#核心概念)
3. [使用流程](#使用流程)
4. [代理系统](#代理系统)
5. [技能系统](#技能系统)
6. [高级功能](#高级功能)
7. [最佳实践](#最佳实践)
8. [故障排查](#故障排查)

---

## 快速开始

### 系统要求

- **OpenCode CLI/Desktop**: v1.0+
- **Node.js**: v16+ (可选，用于某些技能)
- **Git**: v2.0+

### 安装

```bash
# 克隆仓库
git clone https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM.git
cd Quick-Agents-for-Z.AI-GLM

# 复制到你的项目
cp -r .opencode /path/to/your/project/
cp AGENTS.md /path/to/your/project/
```

### 第一个项目

在OpenCode中发送：

```
启动QuickAgent
```

系统将自动：
1. 检测项目类型（新项目/现有项目）
2. 启动需求澄清流程
3. 创建项目文档
4. 生成任务清单

---

## 核心概念

### 三维记忆系统

QuickAgents采用基于论文《Memory in the Age of AI Agents》的三维记忆系统：

| 记忆类型 | 功能 | 示例 |
|---------|------|------|
| **Factual Memory** | 静态事实 | 项目名称、技术栈、约束条件 |
| **Experiential Memory** | 动态经验 | 操作历史、踩坑记录、最佳实践 |
| **Working Memory** | 当前状态 | 当前任务、进度、阻塞点 |

**跨会话恢复**：
```bash
# 使用start-work命令恢复工作
/start-work

# 或发送跨会话衔接提示词
📍 跨会话衔接提示词...
```

### Boulder进度追踪

基于Oh-My-OpenAgent的跨会话进度管理：

```json
{
  "session_id": "abc123",
  "completed_tasks": 41,
  "total_tasks": 44,
  "current_task": "T015",
  "notepad": {
    "learnings": [...],
    "decisions": [...],
    "questions": [...],
    "pitfalls": [...]
  }
}
```

### Category系统

语义化任务分类，根据"做什么"自动选择配置：

| Category | 用途 | 默认模型 |
|----------|------|---------|
| `visual-engineering` | UI开发、前端设计 | Gemini 2.0 Flash |
| `ultrabrain` | 深度推理、复杂分析 | GPT-5.4 |
| `quick` | 快速响应、简单任务 | GLM-5 Flash |
| `planning` | 计划制定、需求分析 | GLM-5 |

---

## 使用流程

### 新项目初始化

1. **触发初始化**：
   ```
   启动QuickAgent
   ```

2. **需求澄清**（12轮递进式询问）：
   - L1: 业务本质
   - L2: 用户画像
   - L3: 核心流程
   - L4: 功能清单
   - L5: 数据模型
   - L6: 技术栈
   - L7: 交付标准
   - L8-L12: 深度细节

3. **项目创建**：
   - 生成`Docs/`目录结构
   - 创建`MEMORY.md`、`TASKS.md`等文档
   - 初始化`.opencode/`配置

### 现有项目分析

1. **触发分析**：
   ```
   启动QuickAgent
   ```

2. **系统自动检测**：
   - 读取`package.json`/`Cargo.toml`等
   - 分析目录结构
   - 识别技术栈

3. **询问意图**：
   - 继续开发
   - 重新开始
   - 功能增强

### 跨会话工作恢复

```bash
# 方法1：使用start-work命令
/start-work

# 方法2：使用跨会话衔接提示词
📍 跨会话衔接提示词
## 当前进度
- 已完成：xxx
- 进度：xx%
...
```

---

## 代理系统

### 核心代理（6个）

#### @yinglong-init
项目初始化专家，负责：
- 项目类型检测
- 需求收集与澄清
- 文档结构创建

**使用示例**：
```
@yinglong-init 初始化一个Vue3+TypeScript项目
```

#### @boyi-consult
需求分析专家，负责：
- 12轮需求澄清
- 需求文档生成
- 可行性评估

**使用示例**：
```
@boyi-consult 分析用户管理模块的需求
```

#### @chisongzi-advise
技术栈推荐专家，负责：
- 技术选型建议
- 架构设计评估
- 最佳实践推荐

**使用示例**：
```
@chisongzi-advise 推荐一个实时聊天系统的技术栈
```

#### @cangjie-doc
文档管理专家，负责：
- 文档创建与更新
- 文档同步
- 知识图谱维护

**使用示例**：
```
@cangjie-doc 更新API文档
```

#### @huodi-skill
技能管理专家，负责：
- 技能搜索与评估
- 技能安装与配置
- 技能优化建议

**使用示例**：
```
@huodi-skill 推荐一个代码格式化的技能
```

#### @fenghou-orchestrate
主调度器，负责：
- 任务分解
- 代理协调
- 进度追踪

**使用示例**：
```
@fenghou-orchestrate 完成用户认证功能的开发
```

### 质量代理（4个）

#### @jianming-review
代码审查，确保：
- 代码质量
- 最佳实践
- 安全漏洞

#### @lishou-test
测试执行，负责：
- 单元测试
- 集成测试
- E2E测试

#### @mengzhang-security
安全审计，检查：
- 安全漏洞
- 权限问题
- 敏感信息泄露

#### @hengge-perf
性能分析，识别：
- 性能瓶颈
- 内存泄漏
- 优化建议

### 工具代理（4个）

#### @kuafu-debug
调试代理，帮助：
- 问题诊断
- Bug修复
- 日志分析

#### @gonggu-gonggu-refactor
重构代理，负责：
- 代码重构
- 架构优化
- 技术债务清理

#### @huodi-deps
依赖管理，处理：
- 依赖安装
- 版本升级
- 冲突解决

#### @hengge-cicd
CI/CD管理，负责：
- 流水线配置
- 自动化部署
- 环境管理

---

## 技能系统

### 核心技能（14个）

#### inquiry-skill
互动询问卡，实现12轮需求澄清。

#### project-memory-skill
三维记忆系统，管理项目知识。

#### tdd-workflow-skill
TDD工作流，实现RED-GREEN-REFACTOR循环。

#### git-commit-skill
Git提交规范，自动生成符合规范的提交信息。

#### code-review-skill
代码审查，两阶段审查方法论。

#### category-system-skill
Category系统，语义化任务分类。

#### background-agents-skill
后台代理，并行执行任务。

#### boulder-tracking-skill
Boulder进度追踪，跨会话恢复。

#### skill-integration-skill
技能整合，向导式技能添加。

#### multi-model-skill
多模型协同，智能路由和fallback。

#### lsp-ast-skill
LSP/AST集成，智能诊断和重构。

#### ultrawork-command
超高效工作命令，一键完成复杂任务。

#### start-work-command
工作恢复命令，跨会话衔接。

#### todo-continuation-enforcer
Todo强制完成，确保任务不中断。

### 技能使用示例

#### 1. 需求澄清
```
启动QuickAgent
# 系统自动使用inquiry-skill进行12轮询问
```

#### 2. TDD开发
```
# 在编写任何功能代码前，先编写测试
@jianming-review 检查这个模块的测试覆盖率
```

#### 3. Git提交
```
# 完成任务后自动触发git-commit-skill
# 自动生成符合规范的提交信息
```

#### 4. 多模型协同
```
# 系统自动根据任务类型选择模型
@fenghou-orchestrate 分析这个复杂的分布式系统设计
# 自动使用ultrabrain category → GPT-5.4深度推理
```

---

## 高级功能

### ultrawork命令

一键完成复杂任务：

```bash
/ultrawork 实现用户认证功能
```

系统将：
1. 分解任务为子任务
2. 并行执行可并行部分
3. 串行执行依赖部分
4. 自动协调多个代理
5. 追踪进度并报告

### Background Agents

后台并行执行：

```json
{
  "background_tasks": [
    {
      "id": "task-1",
      "agent": "lishou-test",
      "command": "运行单元测试",
      "status": "running"
    },
    {
      "id": "task-2",
      "agent": "jianming-review",
      "command": "审查代码质量",
      "status": "pending"
    }
  ],
  "max_concurrent": 5
}
```

### Prometheus规划系统

三方协作规划：

| 代理 | 角色 | 职责 |
|------|------|------|
| **Prometheus** | 规划器 | 访谈式需求收集、计划生成 |
| **Metis** | 顾问 | 可行性分析、专业建议 |
| **Momus** | 审查员 | 质量审查、标准合规 |

**使用示例**：
```
@fenghou-plan 为这个电商系统制定开发计划
```

### LSP/AST集成

智能代码诊断和重构：

**支持的LSP**：
- TypeScript (typescript-language-server)
- Python (pyright)
- Rust (rust-analyzer)
- Go (gopls)
- Java (jdtls)
- C++ (clangd)

**AST搜索**：
```bash
# 搜索所有函数定义
/ast-search "function $NAME($PARAMS) { $BODY }"

# 重写代码模式
/ast-rewrite "var $VAR = $VALUE" → "const $VAR = $VALUE"
```

### 多模型协同

智能模型路由：

```json
{
  "categories": {
    "visual-engineering": {
      "primary": "gemini-2.0-flash",
      "fallback": ["gpt-5.4", "glm-5"]
    },
    "ultrabrain": {
      "primary": "gpt-5.4",
      "fallback": ["glm-5-plus", "gemini-2.0-flash"]
    },
    "quick": {
      "primary": "glm-5-flash",
      "fallback": ["gpt-4o-mini"]
    }
  }
}
```

---

## 最佳实践

### 1. 需求澄清

- **完整参与12轮询问**：不要跳过任何轮次
- **提供具体答案**：避免模糊表述
- **主动补充细节**：如果AI遗漏，主动补充

### 2. 任务执行

- **严格串行**：一个任务完成后再开始下一个
- **立即提交**：完成任务后立即提交Git
- **同步文档**：提交前更新MEMORY.md

### 3. 测试驱动

- **先写测试**：在编写功能代码前先写测试
- **保持覆盖率**：核心代码100%，非核心≥80%
- **持续测试**：每次提交前运行测试

### 4. 代码质量

- **遵循规范**：参考AGENTS.md的代码风格
- **使用代理**：用@jianming-review审查代码
- **解决债务**：及时修复技术债务

### 5. 跨会话管理

- **使用start-work**：每次会话开始时恢复工作
- **更新boulder.json**：定期保存进度
- **记录智慧**：在notepad中记录学习点

---

## 故障排查

### 问题1：代理无法启动

**症状**：发送`@agent-name`无响应

**解决方案**：
1. 检查`.opencode/agents/`目录是否存在对应代理
2. 检查代理配置文件格式是否正确
3. 重启OpenCode CLI/Desktop

### 问题2：技能加载失败

**症状**：提示"Skill not found"

**解决方案**：
1. 检查`.opencode/skills/`目录结构
2. 验证`SKILL.md`文件格式
3. 检查`registry.json`配置

### 问题3：跨会话恢复失败

**症状**：无法恢复之前的工作进度

**解决方案**：
1. 检查`.quickagents/boulder.json`是否存在
2. 验证session_id是否正确
3. 使用完整的跨会话衔接提示词

### 问题4：多模型协同异常

**症状**：模型切换失败或响应异常

**解决方案**：
1. 检查`.opencode/config/models.json`配置
2. 验证API密钥是否有效
3. 检查网络连接和API配额

### 问题5：LSP诊断不准确

**症状**：LSP提供的诊断信息不正确

**解决方案**：
1. 检查`.opencode/config/lsp-config.json`配置
2. 确保LSP服务器已正确安装
3. 重启LSP服务器

---

## 附录

### 常用命令速查

| 命令 | 用途 |
|------|------|
| `/start-work` | 恢复工作 |
| `/ultrawork <task>` | 超高效执行任务 |
| `@agent-name` | 调用特定代理 |
| `启动QuickAgent` | 初始化项目 |

### 配置文件位置

| 文件 | 位置 |
|------|------|
| 代理配置 | `.opencode/agents/*.md` |
| 命令配置 | `.opencode/commands/*.md` |
| 技能配置 | `.opencode/skills/*/SKILL.md` |
| Category配置 | `.opencode/config/categories.json` |
| 模型配置 | `.opencode/config/models.json` |
| 进度追踪 | `.quickagents/boulder.json` |

### 获取帮助

- **GitHub Issues**: https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/issues
- **文档**: `Docs/`目录
- **知识图谱**: `Docs/INDEX.md`

---

*文档版本: v1.0 | 更新时间: 2026-03-25*
