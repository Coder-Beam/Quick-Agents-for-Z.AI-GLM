# QuickAgents 用户指南

> 完整的用户使用指南，帮助您高效使用QuickAgents

---

## 目录

- [快速入门](#快速入门)
- [触发词](#触发词)
- [命令](#命令)
- [技能](#技能)
- [工作流程](#工作流程)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

---

## 快速入门

### 前置条件

- 已安装 OpenCode CLI 或桌面版
- 已安装 Git
- Node.js（可选，用于CLI工具）

### 首次设置

1. 使用以下方式之一安装QuickAgents：

```bash
# 方式1：CLI安装
npm install -g quickagents-cli
qa init

# 方式2：一句话提示词（推荐）
# 粘贴到AI代理中：
# Install and configure QuickAgents by following the instructions here:
# https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/Docs/guide/installation.md
```

2. 启动初始化：

```
启动QuickAgent
```

3. 回答配置问题（仅首次）

4. 完成需求问询（7层）

5. 开始开发！

---

## 触发词

QuickAgents响应以下触发词（大小写不敏感）：

| 触发词 | 说明 |
|--------|------|
| `启动QuickAgent` | 推荐，启动项目初始化 |
| `启动QuickAgents` | 兼容 |
| `启动QA` | 简短形式 |
| `Start QA` | 英文 |

### 触发后发生什么

1. 调用 **yinglong-init** 代理
2. 检测项目类型（新项目/现有项目）
3. 检查配置文件
4. 开始需求问询（如果是新项目）
5. 创建文档结构
6. 创建标准代理（编程项目）

---

## 命令

### /start-work

**用途**：跨会话恢复

**使用方法**：
```
/start-work
```

**功能**：
- 读取 MEMORY.md 恢复上下文
- 读取 boulder.json 恢复进度
- 显示当前状态
- 从中断处继续

**何时使用**：
- 开始新会话时
- 从中断中恢复
- 继续处理任务

---

### /ultrawork

**用途**：超高效任务执行

**使用方法**：
```
/ultrawork <任务描述>
```

**示例**：
```
/ultrawork 实现用户认证功能
/ultrawork 修复登录bug
/ultrawork 为UserService添加单元测试
```

**功能**：
- 分析任务复杂度
- 调度合适的代理
- 以最高效率执行
- 实时报告进度

---

### /run-workflow

**用途**：运行预定义工作流

**使用方法**：
```
/run-workflow <工作流名称>
```

**可用工作流**：
- `full-review` - 完整代码审查
- `deploy` - 部署工作流
- `test-all` - 运行所有测试

---

### /enable-coordination

**用途**：启用多代理协调

**使用方法**：
```
/enable-coordination
```

**功能**：
- 启用代理协调模式
- 允许多个代理协同工作
- 改善复杂任务处理

---

### /disable-coordination

**用途**：禁用多代理协调

**使用方法**：
```
/disable-coordination
```

**功能**：
- 禁用代理协调模式
- 返回单代理模式
- 适用于简单任务

---

## 技能

### 核心技能

| 技能 | 用途 | 自动触发 |
|------|------|----------|
| project-memory-skill | 三维记忆管理 | 是 |
| boulder-tracking-skill | 跨会话进度追踪 | 是 |
| category-system-skill | 语义化任务分类 | 是 |

### 开发技能

| 技能 | 用途 | 自动触发 |
|------|------|----------|
| inquiry-skill | 7层需求问询 | 初始化时 |
| tdd-workflow-skill | 测试驱动开发工作流 | 代码任务 |
| code-review-skill | 代码质量审查 | 审查时 |
| git-commit-skill | Git提交标准化 | 提交时 |

### 工具技能

| 技能 | 用途 | 自动触发 |
|------|------|----------|
| multi-model-skill | 多模型支持 | 是 |
| lsp-ast-skill | LSP/AST代码分析 | 代码任务 |
| project-detector-skill | 项目类型检测 | 初始化时 |
| background-agents-skill | 并行代理执行 | 复杂任务 |
| skill-integration-skill | Skill整合管理 | 手动 |

---

## 工作流程

### 新项目工作流

```
1. 触发：启动QuickAgent
   ↓
2. yinglong-init 启动
   ↓
3. 项目类型检测
   ↓
4. 配置检查
   ↓
5. 首次设置（如需要）
   ↓
6. 7层需求问询
   ↓
7. 技术栈推荐
   ↓
8. 任务分解
   ↓
9. 开始执行
```

### 日常开发工作流

```
1. 向AI描述任务
   ↓
2. fenghou-orchestrate 分类任务
   ↓
3. 调度合适的代理
   ↓
4. 执行任务
   ↓
5. 质量检查（审查、测试）
   ↓
6. Git提交
   ↓
7. 更新记忆
```

### 调试工作流

```
1. 报告问题：@kuafu-debug <问题>
   ↓
2. kuafu-debug 分析问题
   ↓
3. 识别根本原因
   ↓
4. 实现修复
   ↓
5. 测试验证修复
   ↓
6. 代码审查
   ↓
7. 提交更改
```

---

## 最佳实践

### 1. 始终使用触发词

始终使用 `启动QuickAgent` 进行初始化，确保行为一致。

### 2. 完成需求问询

不要跳过7层需求问询，详细回答每个问题：
- L1：业务本质
- L2：用户画像
- L3：核心流程
- L4：功能清单
- L5：数据模型
- L6：技术栈
- L7：交付标准

### 3. 利用代理专业化

为特定任务使用特定代理：
- `@jianming-review` 代码审查
- `@lishou-test` 测试执行
- `@mengzhang-security` 安全审计
- `@kuafu-debug` 问题调试

### 4. 使用跨会话恢复

开始新会话时：
```
/start-work
```

这会恢复你的上下文和进度。

### 5. 频繁提交

让 git-commit-skill 处理提交：
- 标准化提交信息
- 提交前检查
- 文档更新

### 6. 保持记忆更新

MEMORY.md 是项目的"大脑"，保持更新：
- 记录重要决策
- 记录经验教训
- 追踪当前状态

### 7. 复杂任务使用 /ultrawork

对于复杂的多步骤任务：
```
/ultrawork 实现完整的OAuth2用户认证系统
```

---

## 常见问题

### Q: 如何开始一个新项目？

**A**: 只需使用触发词：
```
启动QuickAgent
```
系统会引导你完成整个过程。

### Q: 关闭会话后如何继续工作？

**A**: 使用恢复命令：
```
/start-work
```

### Q: 如何调用特定代理？

**A**: 使用@提及：
```
@jianming-review 请审查这段代码
```

### Q: 如何更改模型配置？

**A**: 编辑 `.opencode/config/models.json` 或运行：
```
@huodi-skill 更新模型配置
```

### Q: 如果我没有Z.ai订阅怎么办？

**A**: 你可以在 `models.json` 中配置其他模型。QuickAgents支持：
- Claude模型
- GPT模型
- Gemini模型
- 本地模型

### Q: 如何添加新的LSP语言？

**A**: 编辑 `.opencode/config/lsp-config.json`：
```json
{
  "languages": ["typescript", "python"],
  "servers": {
    "python": {
      "command": "pyright-langserver",
      "args": ["--stdio"]
    }
  }
}
```

### Q: 如何创建自定义技能？

**A**: 使用技能管理代理：
```
@huodi-skill 创建一个新的代码格式化技能
```

### Q: /ultrawork 和普通任务有什么区别？

**A**: `/ultrawork` 优化用于：
- 复杂的多步骤任务
- 需要多个代理的任务
- 需要并行执行的任务

普通任务通过直接对话处理。

### Q: 如何查看我的进度？

**A**: 查看进度文件：
```bash
cat .quickagents/boulder.json
```

或询问AI：
```
当前进度如何？
```

### Q: 如何重置QuickAgents？

**A**: 删除配置并重新初始化：
```bash
rm -rf .opencode
rm -rf .quickagents
rm AGENTS.md
启动QuickAgent
```

---

## 快速参考卡

```
┌─────────────────────────────────────────────────────────────────┐
│                    QuickAgents 快速参考                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  触发词                                                          │
│  ─────────────────────────────────────────────────────────────  │
│  启动QuickAgent  启动QuickAgents  启动QA  Start QA               │
│                                                                  │
│  命令                                                            │
│  ─────────────────────────────────────────────────────────────  │
│  /start-work      - 跨会话恢复                                   │
│  /ultrawork       - 超高效执行                                   │
│  /run-workflow    - 运行预定义工作流                              │
│  /enable-coord    - 启用代理协调                                  │
│  /disable-coord   - 禁用代理协调                                  │
│                                                                  │
│  常用代理                                                        │
│  ─────────────────────────────────────────────────────────────  │
│  @jianming-review  - 代码审查                                    │
│  @lishou-test      - 测试执行                                    │
│  @kuafu-debug      - 问题调试                                    │
│  @cangjie-doc      - 文档编写                                    │
│                                                                  │
│  关键文件                                                        │
│  ─────────────────────────────────────────────────────────────  │
│  AGENTS.md                    - 开发规范                         │
│  .opencode/config/models.json - 模型配置                         │
│  Docs/MEMORY.md               - 项目记忆                         │
│  .quickagents/boulder.json    - 进度追踪                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

*版本: 2.0.1 | 更新时间: 2026-03-26*
