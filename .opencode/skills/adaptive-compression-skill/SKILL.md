# Adaptive Compression Skill

> **来源**: OpenDev 论文 (arXiv:2603.05344v2)
> **核心目标**: 峰值上下文消耗减少54%，通过自适应压缩策略优化上下文管理
> **适用场景**: 长会话、复杂任务、上下文压力较大时

---

## 一、核心概念

### 1.1 自适应压缩原则

```
压缩策略 = f(上下文压力, 内容类型, 保护文件)
```

**三大核心原则**:
1. **渐进式压缩**: 随着上下文压力增加，逐步提升压缩强度
2. **保护关键内容**: MEMORY.md、TASKS.md等核心文件优先保护
3. **保留推理链**: 压缩时保留关键决策和推理步骤

### 1.2 压缩阈值策略

| 压力阈值 | 策略 | 操作 | 效果 |
|----------|------|------|------|
| 70% | 警告日志 | 记录警告，建议压缩 | 预警阶段 |
| 80% | 观察掩码 | 掩码旧的工具观察结果 | 减少10-15% |
| 85% | 快速修剪 | 修剪大体积工具输出 | 减少20-30% |
| 90% | 激进掩码 | 大幅减少历史上下文 | 减少40-50% |
| 99% | 完整LLM压缩 | 调用LLM生成摘要 | 减少60-70% |

---

## 二、核心常量配置

```python
# 压缩阈值
COMPRESSION_THRESHOLDS = {
    "warning": 0.70,           # 警告日志
    "mask_observations": 0.80, # 掩码旧观察
    "prune_outputs": 0.85,     # 修剪工具输出
    "aggressive_mask": 0.90,   # 激进掩码
    "llm_compression": 0.99    # 完整LLM压缩
}

# 工具输出阈值
TOOL_OUTPUT_OFFLOAD_THRESHOLD = 8000  # chars - 超过此长度考虑修剪
MAX_TOOL_RESULT_SUMMARY = 300         # tokens - 摘要最大长度

# 保护文件列表（永不压缩）
PROTECTED_FILES = [
    "Docs/MEMORY.md",
    "Docs/TASKS.md", 
    "Docs/DESIGN.md",
    "AGENTS.md",
    ".opencode/memory/MEMORY.md"
]

# 保留的最近操作数
MAX_RECENT_OPERATIONS = 10
```

---

## 三、压缩策略实现

### 3.1 自适应压缩主流程

```python
def adaptive_compact(messages: list, current_tokens: int, max_tokens: int):
    """
    自适应压缩策略主入口
    
    Args:
        messages: 当前对话消息列表
        current_tokens: 当前token数
        max_tokens: 最大token数
    
    Returns:
        压缩后的消息列表
    """
    pressure = current_tokens / max_tokens
    
    if pressure > COMPRESSION_THRESHOLDS["llm_compression"]:
        return llm_summarize(messages, protected=PROTECTED_FILES)
    
    elif pressure > COMPRESSION_THRESHOLDS["aggressive_mask"]:
        return aggressive_mask(messages, keep_recent=MAX_RECENT_OPERATIONS)
    
    elif pressure > COMPRESSION_THRESHOLDS["prune_outputs"]:
        return prune_tool_outputs(messages, threshold=TOOL_OUTPUT_OFFLOAD_THRESHOLD)
    
    elif pressure > COMPRESSION_THRESHOLDS["mask_observations"]:
        return mask_old_observations(messages)
    
    elif pressure > COMPRESSION_THRESHOLDS["warning"]:
        log_warning(f"Context pressure at {pressure:.1%}, consider compression")
        return messages
    
    return messages
```

### 3.2 观察掩码策略

```python
def mask_old_observations(messages: list) -> list:
    """
    掩码旧的工具观察结果
    
    保留策略:
    - 保留最近5次工具调用的完整结果
    - 更旧的观察替换为简短摘要
    """
    masked = []
    tool_call_count = 0
    
    for msg in reversed(messages):
        if is_tool_result(msg):
            tool_call_count += 1
            if tool_call_count <= 5:
                masked.insert(0, msg)  # 保留完整
            else:
                summary = summarize_tool_result(msg, max_tokens=50)
                masked.insert(0, summary)  # 替换为摘要
        else:
            masked.insert(0, msg)
    
    return masked
```

### 3.3 工具输出修剪策略

```python
def prune_tool_outputs(messages: list, threshold: int = 8000) -> list:
    """
    修剪大体积工具输出
    
    修剪规则:
    - 超过threshold字符的输出截断为threshold
    - 保留开头和结尾，中间用[...truncated...]标记
    - 文件内容保留行号引用
    """
    pruned = []
    
    for msg in messages:
        if is_tool_result(msg) and len(msg.get("content", "")) > threshold:
            content = msg["content"]
            head = content[:threshold // 2]
            tail = content[-threshold // 4:]
            msg["content"] = f"{head}\n\n[...{len(content) - threshold} chars truncated...]\n\n{tail}"
        
        pruned.append(msg)
    
    return pruned
```

### 3.4 激进掩码策略

```python
def aggressive_mask(messages: list, keep_recent: int = 10) -> list:
    """
    激进掩码策略 - 大幅减少历史上下文
    
    保留策略:
    - 最近keep_recent条消息完整保留
    - 用户消息全部保留
    - 系统消息全部保留
    - 工具结果仅保留摘要
    - AI响应压缩为关键点
    """
    masked = []
    recent_count = 0
    
    for msg in reversed(messages):
        recent_count += 1
        
        if recent_count <= keep_recent:
            masked.insert(0, msg)  # 完整保留
        elif msg["role"] in ["user", "system"]:
            masked.insert(0, msg)  # 用户/系统消息保留
        elif is_tool_result(msg):
            summary = summarize_tool_result(msg, max_tokens=30)
            masked.insert(0, summary)
        elif msg["role"] == "assistant":
            # AI响应压缩为关键点
            keypoints = extract_keypoints(msg["content"], max_points=3)
            masked.insert(0, {"role": "assistant", "content": keypoints})
    
    return masked
```

### 3.5 LLM压缩策略

```python
def llm_summarize(messages: list, protected: list = None) -> list:
    """
    完整LLM压缩 - 调用LLM生成摘要
    
    这是最后的手段，仅在上下文压力达到99%时触发
    
    保护机制:
    - protected列表中的文件内容永不压缩
    - 保留最近3轮完整对话
    - 历史对话生成结构化摘要
    """
    protected = protected or PROTECTED_FILES
    
    # 1. 提取受保护内容
    protected_content = extract_protected(messages, protected)
    
    # 2. 分离最近对话
    recent, history = split_recent_history(messages, keep_turns=3)
    
    # 3. 生成历史摘要
    history_summary = generate_summary(history)
    
    # 4. 重组消息
    return [
        {"role": "system", "content": "以下为历史对话摘要:\n" + history_summary},
        *protected_content,
        *recent
    ]
```

---

## 四、保护文件机制

### 4.1 保护文件识别

```python
def is_protected_content(message: dict, protected_files: list) -> bool:
    """判断消息是否包含受保护文件内容"""
    content = message.get("content", "")
    
    for protected_path in protected_files:
        if protected_path in content:
            return True
    
    return False

def extract_protected(messages: list, protected_files: list) -> list:
    """提取并保护指定文件的内容"""
    protected = []
    
    for msg in messages:
        if is_protected_content(msg, protected_files):
            protected.append(msg)
    
    return protected
```

### 4.2 保护文件优先级

| 优先级 | 文件 | 理由 |
|--------|------|------|
| P0 | Docs/MEMORY.md | 项目记忆核心 |
| P0 | Docs/TASKS.md | 任务状态追踪 |
| P0 | AGENTS.md | 开发规范 |
| P1 | Docs/DESIGN.md | 设计文档 |
| P1 | .opencode/memory/* | OpenCode记忆 |

---

## 五、压缩触发时机

### 5.1 自动触发

| 触发条件 | 动作 |
|----------|------|
| 工具调用后检测到压力>70% | 执行对应策略 |
| 任务切换前 | 检查压力，必要时压缩 |
| 长时间运行(30分钟) | 执行压缩检查 |

### 5.2 手动触发

```bash
# 用户命令触发压缩
/compress-now [strategy=auto|mask|prune|aggressive|llm]

# 查看压缩统计
/compression-stats
```

---

## 六、压缩效果监控

### 6.1 监控指标

```yaml
metrics:
  - original_tokens: 原始token数
  - compressed_tokens: 压缩后token数
  - compression_ratio: 压缩率
  - strategy_used: 使用的策略
  - protected_files_count: 保护的文件数
  - processing_time: 处理耗时
```

### 6.2 效果报告

```markdown
## 压缩报告

- **触发时间**: 2026-03-27 10:30:00
- **压力阈值**: 85%
- **使用策略**: prune_outputs
- **原始token**: 45000
- **压缩后token**: 31500
- **压缩率**: 30%
- **保护文件**: 3个
- **处理耗时**: 1.2s
```

---

## 七、与现有系统集成

### 7.1 与DCP插件整合

```
DCP (Dynamic Context Preservation)
    ↓
作为llm_compression(99%)的后备方案
    ↓
当达到99%阈值时优先使用DCP
    ↓
DCP不可用时回退到基础LLM压缩
```

### 7.2 与event-reminder-skill集成

```python
# 在event-reminder-skill中添加压缩提醒
COMPRESSION_REMINDERS = {
    "70%": "上下文使用率达到70%，建议执行压缩",
    "85%": "上下文压力较高，已自动执行快速修剪",
    "95%": "上下文压力严重，建议使用/compress-now aggressive"
}
```

### 7.3 与lazy-discovery-skill协同

```
懒加载减少初始上下文
    ↓
推迟压缩触发时间
    ↓
减少压缩频率
    ↓
提升整体效率
```

---

## 八、最佳实践

### 8.1 压缩策略选择指南

| 场景 | 推荐策略 | 理由 |
|------|----------|------|
| 日常开发 | auto | 自动平衡效率与保留 |
| 代码审查 | mask | 保留关键文件引用 |
| 长会话 | aggressive | 最大化压缩效果 |
| 关键决策 | llm | 确保摘要质量 |

### 8.2 压缩避免场景

以下情况应避免压缩:
- 正在编辑的文件内容
- 未完成的测试结果
- 最近的错误信息
- 用户明确要求保留的内容

---

## 九、故障排除

### 9.1 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 压缩后丢失关键信息 | 保护文件未配置 | 更新PROTECTED_FILES |
| 压缩效果不佳 | 阈值设置过高 | 调整COMPRESSION_THRESHOLDS |
| LLM压缩失败 | API限制 | 回退到aggressive_mask |

### 9.2 调试命令

```bash
# 查看当前保护文件列表
/compression-protected

# 测试压缩效果(不实际执行)
/compression-dry-run [strategy]

# 查看压缩历史
/compression-history
```

---

## 十、参考资源

| 资源 | 链接 |
|------|------|
| OpenDev论文 | arXiv:2603.05344v2 |
| DCP插件 | 内置 |
| event-reminder-skill | .opencode/skills/event-reminder-skill/ |

---

*Skill版本: v1.0 | 创建日期: 2026-03-27 | 来源: OpenDev论文*
