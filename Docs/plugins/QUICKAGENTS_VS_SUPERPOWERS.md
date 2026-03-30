# QuickAgents vs Superpowers 功能对比

> 决策建议：**只用QuickAgents即可**

---

## 一、功能对比

| 功能 | Superpowers | QuickAgents | 建议 |
|------|-------------|-------------|------|
| **TDD** | tdd-workflow | tdd-workflow-skill | ✅ QuickAgents覆盖 |
| **代码审查** | code-review | code-review-skill | ✅ QuickAgents覆盖 |
| **头脑风暴** | brainstorming | brainstorming | ✅ QuickAgents覆盖 |
| **调试** | systematic-debugging | - ❌ 需要Superpowers |
| **计划编写** | writing-plans | - ❌ 需要Superpowers |
| **并行代理** | dispatching-parallel-agents | - ❌ 需要Superpowers |

---

## 二、QuickAgents独有功能

| 功能 | 说明 |
|------|------|
| si-hybrid-skill | 阶段-迭代混合模型（核心方法论） |
| project-memory-skill | 三维记忆系统 |
| inquiry-skill | 7层询问模型 |
| git-commit-skill | Git提交规范 |
| category-system | 语义化任务分类 |
| event-reminder-skill | 事件驱动提醒 |
| doom-loop-skill | 循环检测 |
| skill-integration-skill | Skill整合 |
| feedback-collector-skill | 经验收集 |
| browser-devtools-skill | 浏览器自动化 |
| update-skill | 版本更新 |
| background-agents | 后台代理 |
| boulder-tracking | 进度追踪 |

---

## 三、Superpowers独有功能

| 功能 | 说明 | 是否必要？ |
|------|------|-----------|
| systematic-debugging | 系统化调试 | ⚠️ 可选 |
| writing-plans | 计划编写 | ⚠️ 可选 |
| dispatching-parallel-agents | 并行代理 | ⚠️ 可选 |
| executing-plans | 计划执行 | ⚠️ 可选 |
| receiving-code-review | 接收代码审查 | ⚠️ 可选 |
| requesting-code-review | 请求代码审查 | ⚠️ 可选 |
| using-git-worktrees | Git Worktree | ⚠️ 可选 |
| verification-before-completion | 完成前验证 | ⚠️ 可选 |

---

## 四、决策建议

### 推荐方案：只用QuickAgents

**原因**：
1. ✅ 核心功能已覆盖（TDD、代码审查、头脑风暴）
2. ✅ 独有QuickAgents方法论（SI-Hybrid、7层询问、三维记忆）
3. ✅ 与插件深度集成（LoopDetector、LocalExecutor）
4. ❌ Superpowers的功能是"可选增强"，非必需

### 配置更新

```json
// opencode.json
{
  "plugin": [
    "@coder-beam/quickagents"
  ]
}
```

**移除Superpowers**，QuickAgents已包含所有必需功能。

---

## 五、特殊情况

如果需要以下功能，可临时启用Superpowers：
- 复杂调试场景（systematic-debugging）
- 大规模重构（dispatching-parallel-agents）
- Git Worktree隔离（using-git-worktrees）

---

*决策：只用QuickAgents，Superpowers作为可选补充*
