# Todo Continuation Enforcer Hook

> 强制Todo完成机制 - 确保Agent不会中途停止
> 基于 Oh-My-OpenAgent 的 Todo Enforcer 设计

---

## Hook 概述

**触发时机**：Event + Message
**触发条件**：Agent 响应时存在未完成的 Todo
**行为**：注入继续提示，强制 Agent 完成所有 Todo

---

## 核心理念

### 为什么需要 Todo Enforcer？

**问题**：
- Agent 可能在完成部分任务后停止
- 用户需要手动提醒继续
- 工作流程被打断

**解决方案**：
- 自动检测未完成的 Todo
- 注入系统提醒，强制继续
- 直到所有 Todo 标记为完成

### "推石上山"（Sisyphus）精神

就像希腊神话中的西西弗斯，不断推石上山，永不停止。Todo Enforcer 确保 Agent 也会持续工作，直到所有任务完成。

---

## 工作机制

### 检测流程

```
┌─────────────────────────────────────────────────┐
│          Todo Enforcer 检测流程                  │
├─────────────────────────────────────────────────┤
│                                                  │
│  1. Agent 响应完成                               │
│       ↓                                          │
│  2. 检查 TodoWrite 工具使用                      │
│       ↓                                          │
│  3. 分析 Todo 列表                               │
│       ├─ 所有 Todo 都完成？                      │
│       │   └─ YES → 允许响应                      │
│       │   └─ NO  → 注入提醒                      │
│       ↓                                          │
│  4. 注入系统提醒                                 │
│       ↓                                          │
│  5. Agent 继续工作                               │
│       ↓                                          │
│  [循环直到所有 Todo 完成]                        │
│                                                  │
└─────────────────────────────────────────────────┘
```

### 系统提醒格式

```markdown
[SYSTEM REMINDER - TODO CONTINUATION]

你有未完成的待办事项！在响应前必须完成所有待办：

- [ ] 实现用户服务 ← 当前进行中
- [ ] 添加验证逻辑
- [ ] 编写测试用例

**重要**：在所有待办事项标记为完成前，不要响应！
```

---

## 配置选项

### 基础配置

```json
{
  "todo_continuation_enforcer": {
    "enabled": true,
    "max_reminders": 10,        // 最多提醒10次
    "reminder_interval": 1,      // 每次响应后提醒
    "strict_mode": true          // 严格模式：不允许跳过
  }
}
```

### 高级配置

```json
{
  "todo_continuation_enforcer": {
    "enabled": true,
    "max_reminders": 10,
    "reminder_interval": 1,
    "strict_mode": true,
    
    "excluded_agents": [
      "oracle",           // Oracle agent 只读，不强制
      "librarian",        // Librarian agent 可能不需要 Todo
      "explore"           // Explore agent 快速探索
    ],
    
    "reminder_template": "custom_template.md",
    
    "break_conditions": {
      "user_intervention": true,   // 用户干预时停止
      "error_state": true,         // 错误状态时停止
      "timeout_minutes": 30        // 超时停止
    }
  }
}
```

---

## 使用示例

### 示例1：基本任务执行

**Agent 创建 Todo**：
```markdown
## 当前任务
- [ ] 读取配置文件
- [ ] 解析配置项
- [ ] 验证配置有效性
- [ ] 应用配置
```

**第一次响应**：
```
我已读取配置文件，开始解析...
```

**系统检测**：
- 4个 Todo，0个完成
- 注入提醒

**系统提醒**：
```markdown
[SYSTEM REMINDER - TODO CONTINUATION]

你有未完成的待办事项！在响应前必须完成所有待办：

- [ ] 读取配置文件 ← 当前进行中
- [ ] 解析配置项
- [ ] 验证配置有效性
- [ ] 应用配置

**重要**：在所有待办事项标记为完成前，不要响应！
```

**Agent 继续工作**：
```markdown
✅ 读取配置文件完成
✅ 解析配置项完成
✅ 验证配置有效性完成
✅ 应用配置完成

## 当前任务
- [x] 读取配置文件
- [x] 解析配置项
- [x] 验证配置有效性
- [x] 应用配置

所有任务已完成！
```

**系统检测**：
- 4个 Todo，4个完成
- 允许响应

### 示例2：长时间任务

**Agent 创建 Todo**：
```markdown
## 重构任务
- [ ] 分析现有代码
- [ ] 设计新架构
- [ ] 实现重构
- [ ] 运行测试
- [ ] 更新文档
```

**多次循环**：
1. 完成分析 → 系统提醒 → 继续设计
2. 完成设计 → 系统提醒 → 继续实现
3. 完成实现 → 系统提醒 → 继续测试
4. 完成测试 → 系统提醒 → 继续文档
5. 完成文档 → 所有完成 → 允许响应

---

## 与其他机制的配合

### 1. 与 Orchestrator 配合

**Orchestrator 使用 Todo 驱动**：
```markdown
## 执行计划
- [ ] T001: 任务1
- [ ] T002: 任务2
- [ ] T003: 任务3
```

**Todo Enforcer 确保**：
- Orchestrator 不会在 T001 后停止
- 必须完成所有任务才能响应

### 2. 与 UltraWork 配合

**UltraWork 模式**：
```bash
ulw 实现用户认证系统
```

**Todo 自动创建 + 强制完成**：
1. UltraWork 创建 Todo
2. Todo Enforcer 强制完成
3. 直到所有任务完成

### 3. 与 boulder.json 配合

**跨会话恢复**：
```json
{
  "completed_tasks": ["T001", "T002"],
  "current_task": "T003",
  "remaining_tasks": ["T004", "T005"]
}
```

**Todo Enforcer**：
- 新会话读取 boulder.json
- 创建剩余 Todo
- 强制完成所有剩余任务

---

## 例外情况

### 1. 用户干预

**用户明确停止**：
```bash
/stop-continuation
```

**行为**：
- Todo Enforcer 停止提醒
- Agent 可以响应

### 2. 错误状态

**遇到无法恢复的错误**：
```markdown
[ERROR] 无法继续：缺少关键依赖

- [x] 安装依赖1
- [x] 安装依赖2
- [ ] 安装依赖3 ← 失败：网络错误
```

**行为**：
- 检测到错误状态
- 暂停强制机制
- 等待用户决策

### 3. 超时

**运行超过配置的时间**：
```json
{
  "timeout_minutes": 30
}
```

**行为**：
- 超过30分钟后停止提醒
- 生成超时报告
- 保存当前进度

### 4. 排除的 Agent

**某些 Agent 不需要强制**：
```json
{
  "excluded_agents": ["oracle", "librarian", "explore"]
}
```

**原因**：
- Oracle: 只读咨询，可能不需要 Todo
- Librarian: 文档查找，快速返回
- Explore: 快速探索，不需要完整流程

---

## 监控与调试

### 查看强制记录

```bash
cat .quickagents/logs/todo-enforcer.log
```

### 日志格式

```
[2026-03-25 15:00:00] [INFO] 检测到未完成的Todo: 3/5
[2026-03-25 15:00:00] [INFO] 注入提醒 #1
[2026-03-25 15:00:30] [INFO] Todo进度: 4/5
[2026-03-25 15:00:30] [INFO] 注入提醒 #2
[2026-03-25 15:01:00] [INFO] Todo进度: 5/5
[2026-03-25 15:01:00] [INFO] 所有Todo完成，允许响应
```

### 统计数据

```bash
# 查看强制次数
grep "注入提醒" .quickagents/logs/todo-enforcer.log | wc -l

# 查看完成率
grep "所有Todo完成" .quickagents/logs/todo-enforcer.log | wc -l
```

---

## 最佳实践

### 1. 合理创建 Todo

❌ **不好**：
```markdown
- [ ] 做所有事情
```

✅ **好**：
```markdown
- [ ] 读取配置文件
- [ ] 解析配置
- [ ] 验证配置
- [ ] 应用配置
```

### 2. 及时更新 Todo

```markdown
# 完成一项立即标记
- [x] 读取配置文件  ← 完成时立即标记
- [ ] 解析配置       ← 继续下一项
```

### 3. 遇到阻塞及时报告

```markdown
- [x] 读取配置文件
- [ ] 解析配置 ← 阻塞：配置格式错误
- [ ] 验证配置
- [ ] 应用配置

**问题**：配置文件格式不符合预期，需要用户确认如何处理
```

### 4. 使用优先级

```markdown
## P0 - 必须完成
- [ ] 核心功能实现

## P1 - 高优先级
- [ ] 测试编写

## P2 - 可选
- [ ] 文档完善
```

---

## 配置文件

### 完整配置示例

```json
{
  "todo_continuation_enforcer": {
    "enabled": true,
    "max_reminders": 10,
    "reminder_interval": 1,
    "strict_mode": true,
    "excluded_agents": [
      "oracle",
      "librarian", 
      "explore"
    ],
    "break_conditions": {
      "user_intervention": true,
      "error_state": true,
      "timeout_minutes": 30
    },
    "notification": {
      "sound": false,
      "desktop": false
    },
    "logging": {
      "enabled": true,
      "level": "info",
      "file": ".quickagents/logs/todo-enforcer.log"
    }
  }
}
```

---

## 常见问题

### Q1: 如果任务真的无法完成怎么办？

**A**: 
1. 标记为阻塞状态
2. 详细说明原因
3. 等待用户决策

### Q2: 可以跳过某些 Todo 吗？

**A**: 
- 严格模式下不可以
- 可以将 Todo 标记为"可选"或"待定"

### Q3: 最多会提醒多少次？

**A**: 默认10次，可在配置中调整。超过后停止提醒并生成报告。

### Q4: 如何临时禁用？

**A**: 
```bash
/stop-continuation
```

---

## 相关文档

- [Orchestrator Agent](../agents/orchestrator.md)
- [UltraWork 命令](../commands/ultrawork.md)
- [boulder.json 进度追踪](../../.quickagents/boulder.json)

---

*基于 Oh-My-OpenAgent Todo Continuation Enforcer*
*适配 QuickAgents 强制完成机制*
*版本: v1.0.0*
*创建时间: 2026-03-25*
