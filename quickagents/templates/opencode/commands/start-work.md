# Start-Work Command

> 跨会话工作恢复命令 - 从计划开始或恢复执行
> 触发词：`/start-work [plan-name]`

---

## 命令概述

**start-work** 是一个强大的工作启动命令，支持：
- 🆕 开始新任务（从计划文件）
- 🔄 恢复中断的任务（跨会话）
- 📊 显示当前进度
- 🎯 自动切换到 Orchestrator agent

---

## 使用方式

### 方式1：开始新任务

```bash
/start-work auth-system
```

**行为**：
1. 查找 `.quickagents/plans/auth-system.md`
2. 创建新的 boulder.json 追踪
3. 切换到 Orchestrator agent
4. 开始执行任务

### 方式2：恢复工作（无参数）

```bash
/start-work
```

**行为**：
1. 读取 `boulder.json`
2. 计算当前进度
3. 注入续接提示
4. 从中断处继续

### 方式3：查看进度

```bash
/start-work --status
```

**输出**：
```
📊 当前进度

计划：用户认证系统重构
状态：进行中
进度：3/8 任务完成 (37.5%)
当前：T004 - 实现JWT认证

剩余任务：
- T004: 实现JWT认证
- T005: 添加Token刷新
- T006: 编写测试
- T007: 更新文档
- T008: 部署验证
```

---

## 执行流程

### 新任务流程

```
┌─────────────────────────────────────────────────┐
│          start-work 新任务流程                   │
├─────────────────────────────────────────────────┤
│                                                  │
│  1. 检查计划文件                                 │
│     └─ .quickagents/plans/{plan-name}.md        │
│       ├─ 存在 → 继续                             │
│       └─ 不存在 → 错误提示                       │
│                                                  │
│  2. 初始化 boulder.json                         │
│     ├─ 解析计划文件                             │
│     ├─ 提取任务列表                             │
│     ├─ 设置 active_plan                         │
│     └─ 初始化 notepad                           │
│                                                  │
│  3. 切换到 Orchestrator                         │
│     └─ 自动激活 orchestrator agent              │
│                                                  │
│  4. 开始执行                                     │
│     ├─ 读取计划                                 │
│     ├─ 创建 Todo 列表                           │
│     └─ 开始第一个任务                           │
│                                                  │
└─────────────────────────────────────────────────┘
```

### 恢复工作流程

```
┌─────────────────────────────────────────────────┐
│          start-work 恢复流程                     │
├─────────────────────────────────────────────────┤
│                                                  │
│  1. 检查 boulder.json                           │
│     ├─ 存在 → 读取进度                          │
│     └─ 不存在 → 提示创建计划                    │
│                                                  │
│  2. 计算进度                                     │
│     ├─ 读取 completed_tasks                     │
│     ├─ 读取 total_tasks                         │
│     └─ 计算百分比                               │
│                                                  │
│  3. 注入续接提示                                 │
│     ├─ 显示已完成任务                           │
│     ├─ 显示当前任务                             │
│     ├─ 显示剩余任务                             │
│     └─ 显示已学习模式                           │
│                                                  │
│  4. 切换到 Orchestrator                         │
│     └─ 自动激活 orchestrator agent              │
│                                                  │
│  5. 继续执行                                     │
│     ├─ 从 current_task 继续                     │
│     ├─ 加载智慧积累                             │
│     └─ 继续执行任务                             │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## 续接提示示例

### 基本格式

```markdown
📍 继续工作：{计划名称}

## 进度概览
- **状态**：进行中
- **进度**：3/8 任务完成 (37.5%)
- **当前任务**：T004 - 实现JWT认证
- **已用时间**：2小时30分钟

## 已完成任务
- ✅ T001: 分析现有认证代码
- ✅ T002: 设计新架构
- ✅ T003: 准备开发环境

## 剩余任务
- 🔄 T004: 实现JWT认证 ← 当前
- ⏳ T005: 添加Token刷新
- ⏳ T006: 编写测试
- ⏳ T007: 更新文档
- ⏳ T008: 部署验证

## 智慧积累
### 学习点
- 使用JWT替代Session提高可扩展性
- Token需要刷新机制保证安全
- RS256算法比HS256更安全

### 决策记录
- D001: 采用JWT认证（理由：无状态、可扩展）
- D002: Token有效期1小时（理由：平衡安全和体验）

### 遇到的问题
- Token过期时间配置需要与前端协调

### 踩坑记录
- Windows路径使用正斜杠避免转义问题

## 下一步
继续执行 T004：实现JWT认证
```

---

## 命令选项

### 基本选项

```bash
# 开始新任务
/start-work <plan-name>

# 恢复工作
/start-work

# 查看进度
/start-work --status

# 查看详细信息
/start-work --verbose

# 查看历史记录
/start-work --history
```

### 高级选项

```bash
# 从检查点恢复
/start-work --checkpoint=<checkpoint-id>

# 跳过已完成的任务
/start-work --skip-completed

# 重置进度（危险）
/start-work --reset

# 指定agent
/start-work --agent=orchestrator
```

---

## 与其他组件的协作

### 1. 与 Orchestrator 协作

**start-work 触发 Orchestrator**：
```bash
/start-work auth-system

# 系统自动切换到 Orchestrator
# Orchestrator 读取计划并执行
```

### 2. 与 boulder.json 协作

**start-work 读写 boulder.json**：
```bash
# 读取进度
const progress = readBoulder();

# 更新进度
updateBoulder({
  current_task: "T004",
  status: "in_progress"
});
```

### 3. 与 Todo Enforcer 协作

**start-work 创建 Todo，Enforcer 强制完成**：
```bash
/start-work auth-system

# Orchestrator 创建 Todo
- [ ] T001: 分析代码
- [ ] T002: 设计架构
- [ ] T003: 实现功能

# Todo Enforcer 确保全部完成
```

---

## 实际案例

### 案例1：新项目启动

**步骤1：创建计划**
```bash
# 使用 Prometheus 创建计划
@fenghou-plan 规划用户认证系统

# 计划保存到
.quickagents/plans/auth-system.md
```

**步骤2：开始工作**
```bash
/start-work auth-system
```

**系统响应**：
```
🚀 开始新任务：用户认证系统重构

计划文件：.quickagents/plans/auth-system.md
任务数量：8个
预计时间：4小时

切换到 Orchestrator agent...
开始执行任务...
```

### 案例2：跨天恢复

**Day 1 - 下午5点**：
```bash
/start-work auth-system

# 执行了3个任务
✅ T001: 分析代码
✅ T002: 设计架构
🔄 T003: 实现功能（进行中）

# 下班，会话结束
```

**Day 2 - 上午9点（新会话）**：
```bash
/start-work
```

**系统响应**：
```
📍 继续工作：用户认证系统重构

进度：3/8 任务完成 (37.5%)
当前：T003 - 实现功能

已学习：
- 使用依赖注入解耦模块
- 接口优先设计模式

继续执行 T003...
```

### 案例3：检查点恢复

**发现问题需要回滚**：
```bash
# 查看检查点
/start-work --history

检查点列表：
- cp-003: 完成T005 (最新)
- cp-002: 完成T004
- cp-001: 完成T001-T003

# 回滚到检查点
/start-work --checkpoint=cp-002
```

**系统响应**：
```
⏪ 回滚到检查点：cp-002

已回滚任务：
- T005: 添加Token刷新 → 待执行
- T004: 实现JWT认证 → 已完成

当前任务：T005
继续执行...
```

---

## 错误处理

### 错误1：计划文件不存在

```bash
/start-work non-existent-plan
```

**错误信息**：
```
❌ 错误：计划文件不存在

找不到：.quickagents/plans/non-existent-plan.md

建议：
1. 检查计划名称是否正确
2. 使用 @fenghou-plan 创建新计划
3. 查看现有计划：ls .quickagents/plans/
```

### 错误2：boulder.json 损坏

```bash
/start-work
```

**错误信息**：
```
❌ 错误：进度文件损坏

.quickagents/boulder.json 格式不正确

建议：
1. 从检查点恢复：/start-work --checkpoint=<id>
2. 从Git恢复：git checkout .quickagents/boulder.json
3. 重新开始：/start-work --reset
```

### 错误3：没有活跃计划

```bash
/start-work
```

**错误信息**：
```
ℹ️ 提示：没有活跃的计划

当前没有进行中的任务。

建议：
1. 开始新任务：/start-work <plan-name>
2. 查看可用计划：ls .quickagents/plans/
```

---

## 配置选项

### 基础配置

```json
{
  "start_work": {
    "enabled": true,
    "auto_resume": true,           // 自动恢复
    "show_progress": true,         // 显示进度
    "switch_agent": true           // 自动切换agent
  }
}
```

### 高级配置

```json
{
  "start_work": {
    "enabled": true,
    "auto_resume": true,
    "show_progress": true,
    "switch_agent": true,
    
    "default_agent": "orchestrator",
    "max_recovery_attempts": 3,
    
    "progress_display": {
      "show_completed": true,
      "show_remaining": true,
      "show_learnings": true,
      "show_decisions": true,
      "max_learnings_shown": 5
    },
    
    "checkpoint": {
      "auto_create": true,
      "on_task_complete": true,
      "max_checkpoints": 10
    }
  }
}
```

---

## 最佳实践

### 1. 定期提交进度

```bash
# 每天结束前提交
git add .quickagents/
git commit -m "progress: 保存今日进度"
```

### 2. 使用检查点

```bash
# 完成重要任务后创建检查点
/start-work --checkpoint=create

# 需要时回滚
/start-work --checkpoint=<id>
```

### 3. 清晰的计划命名

```bash
# ❌ 不好
/start-work plan1

# ✅ 好
/start-work user-auth-refactor
/start-work payment-integration
/start-work performance-optimization
```

### 4. 查看进度再继续

```bash
# 先查看进度
/start-work --status

# 再继续工作
/start-work
```

---

## 相关命令

- `/stop-continuation` - 停止所有继续机制
- `/handoff` - 生成跨会话交接文档
- `/ulw` - UltraWork 模式

---

## 相关文档

- [Orchestrator Agent](../agents/orchestrator.md)
- [Boulder Tracking Skill](../skills/boulder-tracking-skill/SKILL.md)
- [Todo Continuation Enforcer](../hooks/todo-continuation-enforcer.md)

---

*基于 Oh-My-OpenAgent start-work 命令*
*适配 QuickAgents 跨会话恢复*
*版本: v1.0.0*
*创建时间: 2026-03-25*
