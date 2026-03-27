---
name: event-reminder-skill
description: 事件驱动提醒机制 - 对抗指令遗忘，保持长期目标一致性
version: 1.0.0
created_at: 2026-03-27
source: OpenDev论文 (arXiv:2603.05344v2)
---

# Event Reminder Skill - 事件驱动提醒机制

## 核心理念

来自OpenDev论文：**事件驱动系统提醒** 对抗指令遗忘 (Instruction Fade-out)。

```
问题: 长对话中，初始指令逐渐被稀释，导致Agent偏离目标

解决: 在关键节点重新注入约束，保持长期目标一致性

效果: 显著提升任务完成率和行为一致性
```

## 提醒触发点定义

### 1. 工具调用次数触发

```yaml
TOOL_CALL_REMINDERS:
  threshold: 5
  message: |
    📋 进度检查提醒
    
    已执行 {count} 次工具调用。
    请确认：
    - 当前任务目标是否明确？
    - TodoWrite是否需要更新？
    - 是否需要向用户确认方向？
```

### 2. 上下文压力触发

```yaml
CONTEXT_PRESSURE_REMINDERS:
  thresholds:
    0.70:
      level: warning
      message: "⚠️ 上下文使用率达到70%，考虑压缩策略"
    0.85:
      level: alert
      message: |
        🔴 上下文使用率达到85%
        
        建议操作：
        1. 使用 compress 压缩历史对话
        2. 将中间结果保存到文件
        3. 保护关键文件：MEMORY.md, TASKS.md
    0.95:
      level: critical
      message: |
        🚨 上下文即将溢出
        
        立即执行：
        1. 压缩非必要上下文
        2. 持久化当前状态
        3. 总结已完成工作
```

### 3. 任务切换触发

```yaml
TASK_SWITCH_REMINDERS:
  trigger: new_task_started
  message: |
    🔄 任务切换提醒
    
    开始新任务前，请确认：
    - [ ] 上一任务已提交Git
    - [ ] 文档已更新 (MEMORY.md, TASKS.md)
    - [ ] 测试已通过
    - [ ] 新任务已添加到TodoWrite
```

### 4. Git操作触发

```yaml
GIT_OPERATION_REMINDERS:
  pre_commit:
    message: |
      ✅ 提交前检查清单
      
      - [ ] 所有测试通过
      - [ ] 代码静态检查通过
      - [ ] 类型检查通过
      - [ ] 文档已更新
      - [ ] Commit message符合规范
      
      格式: <type>(<scope>): <subject>
      
  post_commit:
    message: |
      📝 提交完成
      
      下一步：
      1. 生成跨会话衔接提示词
      2. 更新MEMORY.md
      3. 检查是否需要推送
```

### 5. 长时间运行触发

```yaml
LONG_RUNNING_REMINDERS:
  thresholds:
    10_minutes:
      message: "⏰ 已运行10分钟，检查是否需要向用户同步进度"
    30_minutes:
      message: |
        ⏰ 已运行30分钟
        
        建议：
        1. 向用户汇报当前进度
        2. 评估是否需要分阶段完成
        3. 检查是否有阻塞问题
```

### 6. 错误模式触发

```yaml
ERROR_PATTERN_REMINDERS:
  repeated_errors: 3
  message: |
    ❌ 检测到重复错误模式
    
    已连续失败 {count} 次。
    建议：
    1. 暂停并分析根本原因
    2. 考虑使用 @debugger 代理
    3. 向用户报告问题
```

## 核心常量

```python
REMINDER_CONFIG = {
    "MAX_NUDGE_ATTEMPTS": 3,        # 最大提醒次数
    "TOOL_CALL_THRESHOLD": 5,       # 工具调用阈值
    "ERROR_THRESHOLD": 3,           # 错误阈值
    "LONG_RUNNING_MINUTES": [10, 30],  # 长时间运行阈值
    "CONTEXT_THRESHOLDS": [0.70, 0.85, 0.95]  # 上下文阈值
}
```

## 实现逻辑

### 提醒检测函数

```python
def should_trigger_reminder(context: dict) -> tuple[bool, str]:
    """检查是否需要触发提醒"""
    
    # 1. 工具调用检查
    if context["tool_calls"] >= REMINDER_CONFIG["TOOL_CALL_THRESHOLD"]:
        if context["tool_calls"] % REMINDER_CONFIG["TOOL_CALL_THRESHOLD"] == 0:
            return True, format_reminder("tool_call", count=context["tool_calls"])
    
    # 2. 上下文压力检查
    pressure = context["tokens"] / context["max_tokens"]
    for threshold in REMINDER_CONFIG["CONTEXT_THRESHOLDS"]:
        if pressure >= threshold and not context.get(f"reminded_{threshold}"):
            return True, format_reminder("context_pressure", level=threshold)
    
    # 3. 错误模式检查
    if context["consecutive_errors"] >= REMINDER_CONFIG["ERROR_THRESHOLD"]:
        return True, format_reminder("error_pattern", count=context["consecutive_errors"])
    
    # 4. 长时间运行检查
    elapsed = time.time() - context["start_time"]
    for minutes in REMINDER_CONFIG["LONG_RUNNING_MINUTES"]:
        if elapsed >= minutes * 60 and not context.get(f"reminded_{minutes}m"):
            return True, format_reminder("long_running", minutes=minutes)
    
    return False, ""
```

### 提醒注入函数

```python
def inject_reminder(messages: list, reminder: str, position: str = "append"):
    """注入提醒到消息列表"""
    reminder_message = {
        "role": "user",
        "content": f"[系统提醒]\n{reminder}"
    }
    
    if position == "append":
        messages.append(reminder_message)
    elif position == "prepend":
        messages.insert(-1, reminder_message)  # 在最后一条user消息前
    
    return messages
```

## 与QuickAgents集成

### AGENTS.md 集成

```markdown
## 事件驱动提醒机制

以下情况将自动触发提醒：

1. **工具调用次数** - 每5次工具调用检查进度
2. **上下文压力** - 70%/85%/95%三个阈值
3. **任务切换** - 新任务开始前检查
4. **Git操作** - 提交前后检查
5. **长时间运行** - 10分钟/30分钟
6. **错误模式** - 连续3次失败

提醒是约束治理的重要组成部分，帮助保持目标一致性。
```

### yinglong-init.md 集成

```markdown
## 提醒配置

启用事件驱动提醒：
- tool_call_threshold: 5
- context_thresholds: [0.70, 0.85, 0.95]
- error_threshold: 3
- long_running_minutes: [10, 30]
```

## 最佳实践

### 1. 避免提醒疲劳

```
- 同类型提醒设置冷却期
- 优先级排序，关键提醒优先
- 用户可选择关闭非关键提醒
```

### 2. 提醒内容设计

```
- 明确具体，可操作
- 提供上下文信息
- 给出建议行动
```

### 3. 提醒时机

```
- 在决策点前提醒
- 在潜在问题发生前提醒
- 在关键操作后确认
```

## 参考资源

- OpenDev论文: arXiv:2603.05344v2
- 核心概念: Event-Driven Reminders, Instruction Fade-out
- 相关概念: Constraint Governance, Nudge Mechanism
