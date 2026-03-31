---
name: background-agents
description: 后台代理执行系统 - 并行任务处理与结果整合
version: 1.0.0
---

# Background Agents Skill

> QuickAgents 的并行任务处理系统
> 系统化任务编排与协调

---

## 核心概念

### 什么是 Background Agents？

**Background Agents** 允许在后台运行子任务，主线程继续工作，当后台任务完成时自动整合结果。

**核心优势**：
- 🚀 **并行执行**：多个任务同时运行
- ⏱️ **时间节省**：主线程不阻塞
- 🔄 **智能整合**：结果就绪时自动合并
- 📊 **状态追踪**：实时监控后台任务状态

---

## 使用场景

### 场景1：代码库探索

**问题**：需要查找多个模式的代码

**传统方式**：
```typescript
// 串行执行 - 耗时
const auth = await search("auth");
const user = await search("user");
const order = await search("order");
```

**后台方式**：
```typescript
// 并行执行 - 高效
task({
  subagent_type: "explore",
  run_in_background: true,
  prompt: "查找所有认证相关代码"
});

task({
  subagent_type: "explore", 
  run_in_background: true,
  prompt: "查找所有用户相关代码"
});

task({
  subagent_type: "explore",
  run_in_background: true,
  prompt: "查找所有订单相关代码"
});

// 主线程继续工作
// 后台结果就绪时自动整合
```

### 场景2：多模型协作

**问题**：需要不同模型同时分析不同方面

**解决方案**：
```typescript
// Gemini 分析前端
task({
  category: "visual-engineering",
  run_in_background: true,
  prompt: "分析UI组件的响应式设计"
});

// GPT 分析后端
task({
  category: "ultrabrain",
  run_in_background: true,
  prompt: "分析API架构的可扩展性"
});

// GLM 分析安全
task({
  category: "debugging",
  run_in_background: true,
  prompt: "分析潜在的安全漏洞"
});

// 继续主要工作
// 三个分析完成后自动汇总
```

### 场景3：长时间运行的任务

**问题**：某些任务耗时较长

**解决方案**：
```typescript
// 启动长时间任务
const taskId = task({
  subagent_type: "librarian",
  run_in_background: true,
  prompt: "分析整个代码库的架构模式并生成报告"
});

// 继续其他工作
implementNewFeature();

// 需要结果时检查
const result = background_output(taskId);
if (result.status === "completed") {
  useResult(result.data);
}
```

---

## 核心功能

### 1. 启动后台任务

**基本语法**：
```typescript
task({
  subagent_type: "agent-name",  // 或使用 category
  run_in_background: true,      // 启用后台模式
  prompt: "任务描述"
});
```

**返回值**：
```typescript
{
  task_id: "bg_abc123",  // 任务ID
  status: "running",     // 状态
  started_at: "2026-03-25T15:00:00Z"
}
```

### 2. 检查任务状态

**方式1：自动通知**
- 任务完成时系统自动通知
- 不需要主动轮询

**方式2：主动查询**
```typescript
const result = background_output("bg_abc123");
// result.status: "running" | "completed" | "failed"
```

### 3. 获取任务结果

```typescript
const result = background_output("bg_abc123");

if (result.status === "completed") {
  console.log("任务完成:", result.data);
  console.log("学习点:", result.learnings);
} else if (result.status === "failed") {
  console.error("任务失败:", result.error);
}
```

### 4. 取消后台任务

```typescript
background_cancel("bg_abc123");
```

---

## 并发控制

### 默认配置

```json
{
  "max_background_tasks": 3,     // 最多3个并发任务
  "timeout_seconds": 300,         // 5分钟超时
  "retry_on_failure": true        // 失败时重试
}
```

### 自定义配置

在 `.opencode/config/background-config.json` 中：

```json
{
  "max_background_tasks": 5,
  "timeout_seconds": 600,
  "retry_on_failure": true,
  "retry_count": 3,
  "priority_levels": ["high", "medium", "low"],
  "queue_strategy": "fifo"  // 先进先出
}
```

### 资源限制

**内存限制**：
- 每个后台任务最多使用 512MB
- 超过限制自动终止

**CPU限制**：
- 后台任务优先级低于主线程
- 不会阻塞用户交互

---

## 任务队列

### 队列机制

```
┌─────────────────────────────────────────────────┐
│            后台任务队列                           │
├─────────────────────────────────────────────────┤
│                                                  │
│  新任务 ──→ [队列] ──→ 执行槽位 ──→ 完成        │
│             │           │                        │
│             │           ├─ 槽位1: Running        │
│             │           ├─ 槽位2: Running        │
│             │           └─ 槽位3: Running        │
│             │                                    │
│             └─ 等待中: Task4, Task5, Task6      │
│                                                  │
└─────────────────────────────────────────────────┘
```

### 优先级队列

```typescript
// 高优先级任务
task({
  subagent_type: "explore",
  run_in_background: true,
  priority: "high",
  prompt: "紧急：查找生产环境的Bug"
});

// 普通优先级任务
      task({
        subagent_type: "cangjie-doc",
        run_in_background: true,
        prompt: "为模块生成文档"
      });

// 低优先级任务
task({
  subagent_type: "explore",
  run_in_background: true,
  priority: "low",
  prompt: "优化建议收集"
});
```

---

## 结果整合

### 自动整合

**智能合并**：
- 后台任务完成时自动通知主线程
- 主线程可以立即使用结果
- 无需手动轮询

**整合策略**：
```typescript
// 策略1：追加（默认）
result.integrate("append");  // 结果追加到上下文

// 策略2：合并
result.integrate("merge");   // 相同结构的结果合并

// 策略3：覆盖
result.integrate("replace"); // 新结果覆盖旧结果
```

### 手动整合

```typescript
// 收集所有后台任务结果
const results = background_list();

// 筛选完成的任务
const completed = results.filter(r => r.status === "completed");

// 合并结果
const mergedData = mergeResults(completed.map(r => r.data));
```

---

## 最佳实践

### 1. 合理设置并发数

```typescript
// ❌ 不好 - 过多并发
for (let i = 0; i < 20; i++) {
  task({ run_in_background: true, ... });
}

// ✅ 好 - 适度并发（最多3个）
const tasks = items.slice(0, 3).map(item =>
  task({ run_in_background: true, ... })
);
```

### 2. 任务粒度控制

```typescript
// ❌ 不好 - 任务过大
task({
  run_in_background: true,
  prompt: "分析整个代码库并生成完整报告"
});

// ✅ 好 - 任务适中
task({
  run_in_background: true,
  prompt: "分析 src/auth/ 目录的认证模式"
});
```

### 3. 错误处理

```typescript
const result = background_output("bg_abc123");

if (result.status === "failed") {
  // 记录错误
  logError(result.error);
  
  // 根据情况重试
  if (result.retryable) {
    background_retry("bg_abc123");
  } else {
    // 降级处理
    useFallbackSolution();
  }
}
```

### 4. 超时设置

```typescript
// 长时间任务设置更长超时
task({
  run_in_background: true,
  timeout_seconds: 600,  // 10分钟
  prompt: "深度分析大型代码库"
});

// 快速任务设置较短超时
task({
  run_in_background: true,
  timeout_seconds: 60,   // 1分钟
  prompt: "快速搜索特定模式"
});
```

---

## 实际案例

### 案例1：重构前的代码库分析

**任务**：重构认证系统前，需要全面了解现有代码

**使用后台任务**：
```typescript
// 并行启动多个探索任务
task({
  subagent_type: "explore",
  run_in_background: true,
  prompt: "查找所有认证相关文件和依赖"
});

task({
  subagent_type: "explore",
  run_in_background: true,
  prompt: "查找所有使用认证的API端点"
});

task({
  subagent_type: "explore",
  run_in_background: true,
  prompt: "查找所有认证相关的测试"
});

// 主线程：阅读现有文档
const docs = readDocs();

// 等待后台任务完成
const results = await Promise.all([
  background_output("bg_001"),
  background_output("bg_002"),
  background_output("bg_003")
]);

// 整合所有信息
const analysis = integrateResults(docs, ...results);
```

**效果**：
- 传统方式：15分钟
- 后台方式：5分钟（节省66%时间）

### 案例2：多模型代码审查

**任务**：从多个角度审查代码质量

**使用后台任务**：
```typescript
// 安全审查（GPT-5.4）
task({
  category: "ultrabrain",
  run_in_background: true,
  load_skills: ["security-auditor"],
  prompt: "审查代码的安全漏洞"
});

// 性能审查（GLM-5）
task({
  category: "performance-analyzer",
  run_in_background: true,
  prompt: "审查代码的性能问题"
});

// 代码风格（Gemini）
task({
  category: "visual-engineering",
  run_in_background: true,
  prompt: "审查代码的可读性和风格"
});

// 主线程：继续开发
continueDevelopment();

// 收集审查结果
const reviews = collectBackgroundResults();
generateReviewReport(reviews);
```

### 案例3：文档生成

**任务**：为多个模块生成文档

**使用后台任务**：
```typescript
const modules = ["auth", "user", "order", "payment"];

// 并行生成文档
modules.forEach(module => {
  task({
    category: "writing",
    run_in_background: true,
    prompt: `为 ${module} 模块生成API文档`
  });
});

// 主线程：处理其他工作
updateProjectStructure();

// 收集生成的文档
const docs = collectBackgroundResults();
saveDocumentation(docs);
```

---

## 监控与调试

### 查看后台任务列表

```typescript
const tasks = background_list();

tasks.forEach(task => {
  console.log(`${task.id}: ${task.status} - ${task.prompt}`);
});
```

### 查看任务详情

```typescript
const task = background_info("bg_abc123");

console.log("状态:", task.status);
console.log("开始时间:", task.started_at);
console.log("运行时间:", task.elapsed_seconds);
console.log("资源使用:", task.resource_usage);
```

### 日志记录

**日志位置**：`.quickagents/logs/background-tasks.log`

**日志格式**：
```
[2026-03-25 15:00:00] [INFO] 启动后台任务: bg_abc123
[2026-03-25 15:00:01] [INFO] 任务类型: explore
[2026-03-25 15:00:05] [INFO] 任务进度: 50%
[2026-03-25 15:00:10] [INFO] 任务完成: bg_abc123
```

---

## 配置参考

### 完整配置

```json
{
  "background_agents": {
    "enabled": true,
    "max_background_tasks": 3,
    "timeout_seconds": 300,
    "retry_on_failure": true,
    "retry_count": 3,
    "priority_levels": ["high", "medium", "low"],
    "queue_strategy": "fifo",
    "resource_limits": {
      "memory_mb": 512,
      "cpu_percent": 50
    },
    "notification": {
      "on_complete": true,
      "on_failure": true,
      "on_timeout": true
    }
  }
}
```

---

## 常见问题

### Q1: 后台任务会阻塞主线程吗？

**A**: 不会。后台任务完全独立运行，不影响主线程。

### Q2: 最多可以同时运行多少个后台任务？

**A**: 默认3个，可在配置中调整（建议不超过5个）。

### Q3: 后台任务失败会怎样？

**A**: 
- 自动重试（可配置）
- 记录错误日志
- 通知主线程

### Q4: 如何知道后台任务完成了？

**A**: 
- 系统自动通知
- 主动查询状态
- 查看日志

### Q5: 后台任务可以相互调用吗？

**A**: 不可以。后台任务不能再启动新的后台任务（防止无限递归）。

---

## 相关文档

- [Orchestrator Agent](../../agents/orchestrator.md)
- [UltraWork 命令](../../commands/ultrawork.md)
- [Category 系统](../category-system-skill/SKILL.md)

---

*基于 Oh-My-OpenAgent Background Agents*
*适配 QuickAgents 并行执行系统*
*版本: v1.0.0*
*创建时间: 2026-03-25*
