# OpenCode 代理配置目录

此目录用于存放 OpenCode 代理的配置文件。

## 代理配置格式

代理可以通过 Markdown 文件配置，文件名即为代理名称。

### 基本结构

```markdown
---
description: 代理的简要描述
mode: subagent | primary
model: provider/model-id
tools:
  write: true
  bash: true
---

You are [代理类型] agent.

[具体的指令内容]
```

### 配置选项

| 选项 | 类型 | 说明 | 必需 |
|------|------|------|------|
| description | string | 代理功能及使用场景的简要描述 | ✅ |
| mode | string | 代理模式（primary/subagent） | ❌（默认all） |
| model | string | 使用的模型 | ❌ |
| temperature | number | 温度参数（0.0-1.0） | ❌ |
| tools | object | 工具访问权限配置 | ❌ |
| permission | object | 工具操作权限（ask/allow/deny） | ❌ |

### 代理模式

- **primary**: 主代理，可直接交互，使用 Tab 键切换
- **subagent**: 子代理，由主代理调用或通过 @ 提及调用

## 使用说明

1. 在此目录创建 `.md` 文件
2. 文件名即为代理名称（如 `review.md`）
3. 在配置文件中定义代理行为
4. OpenCode 会自动加载此目录下的代理

## 相关文档

- [OpenCode 代理文档](https://opencode.ai/docs/agents/)
- [OpenCode 配置文档](https://opencode.ai/docs/config/)
