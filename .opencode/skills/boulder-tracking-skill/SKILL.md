---
name: boulder-tracking
description: Boulder进度追踪系统 - 跨会话进度管理与恢复
version: 2.0.0
architecture: SQLite主存储 + JSON/Markdown辅助备份
---

# Boulder Tracking Skill

> 基于 Oh-My-OpenAgent 的 Boulder 进度追踪
> QuickAgents 的跨会话进度管理系统

---

## 架构 (v2.0.0+)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Boulder进度追踪架构                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   AI代理 ──► .quickagents/unified.db ◄── 主存储 (SQLite)           │
│              │         progress表                                   │
│              │         notepads表                                   │
│              │         checkpoints表                                │
│              │                                                      │
│              ▼ (自动同步)                                           │
│       .quickagents/boulder.json ◄── 兼容旧格式                      │
│              │                                                      │
│              ▼                                                      │
│       Docs/TASKS.md ◄── 人类可读备份                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 存储位置

| 数据类型 | SQLite表 | 备份文件 |
|----------|----------|----------|
| 进度状态 | progress | boulder.json |
| 笔记本 | notepads | - |
| 检查点 | checkpoints | - |
| 任务 | tasks | Docs/TASKS.md |

---

## 核心概念

### 什么是 Boulder？

**Boulder** 是一个跨会话进度追踪系统，以希腊神话中的西西弗斯（Sisyphus）推石上山命名。

**核心功能**：
- 📊 **进度追踪**：记录任务完成状态
- 🔄 **跨会话恢复**：新会话自动恢复进度
- 📝 **智慧积累**：保存学习点和决策记录
- 🎯 **检查点**：定期保存关键状态

### 为什么需要 Boulder？

**问题**：
- 会话结束后上下文丢失
- 需要重新解释任务背景
- 无法追踪长期项目进度

**解决方案**：
- 使用 boulder.json 保存进度
- 新会话自动读取并恢复
- 智慧积累持续传递

---

## 文件结构

### Boulder 系统文件

```
.quickagents/
├── boulder.json              # 进度追踪主文件
├── boulder-schema.json       # JSON Schema
│
├── plans/                    # 计划文件目录
│   ├── auth-system.md
│   └── user-refactor.md
│
├── notepads/                 # 笔记本目录
│   └── {plan-name}/
│       ├── learnings.md      # 学习点
│       ├── decisions.md      # 决策记录
│       ├── issues.md         # 遇到的问题
│       └── gotchas.md        # 踩坑记录
│
└── logs/                     # 日志目录
    ├── orchestrator.log
    └── boulder.log
```

---

## boulder.json 结构

### 基本结构

```json
{
  "version": "1.0.0",
  "active_plan": ".quickagents/plans/auth-system.md",
  "session_ids": ["session-001", "session-002"],
  "started_at": "2026-03-25T10:00:00Z",
  "updated_at": "2026-03-25T15:30:00Z",
  "plan_name": "用户认证系统重构",
  "total_tasks": 8,
  "completed_tasks": 3,
  "current_task": "T004",
  "status": "in_progress",
  "tasks": [...],
  "notepads": {...},
  "checkpoints": [...]
}
```

### 状态字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | string | idle, in_progress, paused, completed, failed |
| `total_tasks` | number | 总任务数 |
| `completed_tasks` | number | 已完成任务数 |
| `current_task` | string | 当前任务ID |

### 任务结构

```json
{
  "id": "T001",
  "name": "分析现有认证代码",
  "status": "completed",
  "started_at": "2026-03-25T10:00:00Z",
  "completed_at": "2026-03-25T10:30:00Z",
  "priority": "P0",
  "dependencies": [],
  "assigned_to": "orchestrator",
  "notes": "发现3个需要重构的模块"
}
```

### 笔记本结构

```json
{
  "learnings": [
    "使用JWT替代Session",
    "添加Token刷新机制"
  ],
  "decisions": [
    {
      "id": "D001",
      "content": "采用JWT认证",
      "rationale": "无状态、可扩展",
      "made_at": "2026-03-25T10:15:00Z"
    }
  ],
  "issues": [
    "Token过期时间配置不明确"
  ],
  "gotchas": [
    "Windows路径需要使用正斜杠"
  ],
  "commands": [
    "npm run test",
    "npm run lint"
  ]
}
```

---

## 使用流程

### 1. 开始新任务

**使用 /start-work 命令**：
```bash
/start-work auth-system
```

**系统行为**：
1. 检查 `.quickagents/plans/auth-system.md` 是否存在
2. 创建或更新 `boulder.json`
3. 切换到 Orchestrator agent
4. 开始执行任务

### 2. 执行任务

**Orchestrator 自动**：
1. 读取计划文件
2. 创建 Todo 列表
3. 系统化执行
4. 更新 boulder.json
5. 积累智慧到 notepad

### 3. 跨会话恢复

**新会话开始**：
```bash
/start-work
```

**系统行为**：
1. 读取 `boulder.json`
2. 计算进度（3/8任务完成）
3. 注入续接提示
4. 从 T004 继续

**续接提示示例**：
```markdown
## 继续工作：用户认证系统重构

**进度**：3/8 任务完成 (37.5%)
**当前任务**：T004 - 实现JWT认证
**剩余任务**：T004, T005, T006, T007, T008

**已学习模式**：
- 使用JWT替代Session
- Token需要刷新机制

**遇到的问题**：
- Token过期时间配置不明确

**下一步**：继续执行 T004
```

---

## API 接口

### 读取进度

```typescript
// 读取 boulder.json
const boulder = readBoulder();

console.log(`进度: ${boulder.completed_tasks}/${boulder.total_tasks}`);
console.log(`当前任务: ${boulder.current_task}`);
```

### 更新任务状态

```typescript
// 标记任务开始
updateTask("T004", {
  status: "in_progress",
  started_at: new Date().toISOString()
});

// 标记任务完成
updateTask("T004", {
  status: "completed",
  completed_at: new Date().toISOString(),
  notes: "JWT认证已实现"
});
```

### 添加学习点

```typescript
// 添加学习点
addLearning("使用RS256算法签名JWT");

// 添加决策
addDecision({
  id: "D002",
  content: "Token有效期设置为1小时",
  rationale: "平衡安全性和用户体验"
});

// 添加问题
addIssue("刷新Token的并发处理需要考虑");
```

### 创建检查点

```typescript
// 创建检查点
createCheckpoint({
  description: "完成基础认证功能",
  tasks_completed: ["T001", "T002", "T003", "T004"]
});
```

### 回滚到检查点

```typescript
// 回滚到检查点
rollbackToCheckpoint("checkpoint-001");
```

---

## 最佳实践

### 1. 定期创建检查点

```typescript
// 每完成一个重要任务后
if (isMajorTask(task)) {
  createCheckpoint({
    description: `完成 ${task.name}`,
    tasks_completed: getCompletedTasks()
  });
}
```

### 2. 详细记录学习点

```typescript
// ❌ 不好
addLearning("修复了bug");

// ✅ 好
addLearning("认证中间件需要在路由之前注册，否则Token验证不会生效");
```

### 3. 记录决策理由

```typescript
// ❌ 不好
addDecision({
  content: "使用Redis缓存"
});

// ✅ 好
addDecision({
  content: "使用Redis缓存用户会话",
  rationale: "支持分布式部署、自动过期、高性能读写"
});
```

### 4. 及时更新进度

```typescript
// 任务开始时
updateTask(taskId, { status: "in_progress" });

// 任务完成时
updateTask(taskId, { 
  status: "completed",
  completed_at: new Date().toISOString()
});

// 遇到阻塞时
updateTask(taskId, { 
  status: "blocked",
  notes: "等待API文档更新"
});
```

---

## 跨会话示例

### 场景：大型重构项目

**Day 1 - Session 1**：
```bash
# 开始工作
/start-work user-service-refactor

# Orchestrator 执行
- [x] T001: 分析现有代码
- [x] T002: 设计新架构
- [ ] T003: 实现核心模块 ← 进行中
```

**进度保存**：
```json
{
  "completed_tasks": 2,
  "current_task": "T003",
  "status": "in_progress"
}
```

**Day 2 - Session 2（新会话）**：
```bash
# 恢复工作
/start-work

# 系统自动注入
"继续用户服务重构 - 已完成2/8任务，从T003继续"
```

**Orchestrator 继续**：
```markdown
## 继续执行

**上次进度**：T003 - 实现核心模块
**已学习**：
- 使用依赖注入解耦
- 接口优先设计

**继续执行**：T003...
```

**Day 3 - Session 3**：
```bash
/start-work

# 继续从T005开始（T003、T004已完成）
```

**Day 5 - Session 5**：
```bash
/start-work

# 所有任务完成
✅ 用户服务重构完成！
```

---

## 监控与调试

### 查看当前进度

```bash
# 查看boulder.json
cat .quickagents/boulder.json

# 或使用jq美化输出
cat .quickagents/boulder.json | jq '{
  plan: .plan_name,
  progress: "\(.completed_tasks)/\(.total_tasks)",
  status: .status,
  current: .current_task
}'
```

### 查看学习点

```bash
# 查看所有学习点
cat .quickagents/boulder.json | jq '.notepads.learnings'
```

### 查看决策记录

```bash
# 查看所有决策
cat .quickagents/boulder.json | jq '.notepads.decisions'
```

### 查看检查点

```bash
# 查看所有检查点
cat .quickagents/boulder.json | jq '.checkpoints'
```

### 重置进度

```bash
# ⚠️ 危险操作 - 重置所有进度
echo '{}' > .quickagents/boulder.json
```

---

## 配置选项

### 基础配置

```json
{
  "boulder": {
    "enabled": true,
    "auto_save": true,           // 自动保存
    "save_interval_seconds": 30,  // 保存间隔
    "max_checkpoints": 10,        // 最多保存10个检查点
    "auto_checkpoint": true,      // 自动创建检查点
    "checkpoint_interval_tasks": 3 // 每3个任务创建检查点
  }
}
```

### 高级配置

```json
{
  "boulder": {
    "enabled": true,
    "auto_save": true,
    "save_interval_seconds": 30,
    "max_checkpoints": 10,
    "auto_checkpoint": true,
    "checkpoint_interval_tasks": 3,
    
    "notepad": {
      "auto_extract_learnings": true,  // 自动提取学习点
      "max_learnings_per_task": 5,     // 每任务最多5个学习点
      "persist_to_files": true         // 保存到独立文件
    },
    
    "recovery": {
      "auto_resume": true,             // 自动恢复
      "show_progress_on_start": true,  // 启动时显示进度
      "max_recovery_attempts": 3       // 最多恢复尝试次数
    },
    
    "logging": {
      "enabled": true,
      "level": "info",
      "file": ".quickagents/logs/boulder.log"
    }
  }
}
```

---

## 常见问题

### Q1: boulder.json 文件损坏怎么办？

**A**: 
1. 从最近的检查点恢复
2. 或从 Git 历史恢复
3. 或重新初始化

### Q2: 如何在多个项目间切换？

**A**: 每个项目有独立的 `.quickagents/` 目录，互不影响。

### Q3: 检查点会占用很多空间吗？

**A**: 不会。默认最多保存10个检查点，旧检查点自动删除。

### Q4: 可以手动编辑 boulder.json 吗？

**A**: 可以，但要小心：
1. 保持 JSON 格式正确
2. 遵循 schema 定义
3. 建议通过 API 修改

### Q5: 如何备份进度？

**A**: 
```bash
# 备份整个 .quickagents 目录
cp -r .quickagents .quickagents.backup

# 或提交到Git
git add .quickagents/
git commit -m "backup: 保存进度"
```

---

## 相关文档

- [Orchestrator Agent](../../agents/orchestrator.md)
- [start-work 命令](../../commands/start-work.md)
- [Todo Continuation Enforcer](../../hooks/todo-continuation-enforcer.md)

---

*基于 Oh-My-OpenAgent Boulder System*
*适配 QuickAgents 跨会话管理*
*版本: v1.0.0*
*创建时间: 2026-03-25*
