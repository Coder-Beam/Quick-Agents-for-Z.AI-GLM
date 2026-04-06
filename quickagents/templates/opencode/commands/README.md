# OpenCode 命令配置目录

此目录用于存放 OpenCode 自定义命令的配置文件。

## 命令配置格式

命令可以通过 Markdown 文件配置，文件名即为命令名称。

### 基本结构

```markdown
---
description: 命令的简要描述
template: 命令模板
agent: 使用哪个代理执行
model: 使用的模型
---

[可选的额外说明]
```

### 配置选项

| 选项 | 类型 | 说明 | 必需 |
|------|------|------|------|
| description | string | 命令的简要描述 | ✅ |
| template | string | 命令模板 | ✅ |
| agent | string | 执行命令的代理 | ❌ |
| model | string | 使用的模型 | ❌ |

## 使用说明

1. 在此目录创建 `.md` 文件
2. 文件名即为命令名称（如 `test.md`）
3. 在配置文件中定义命令行为
4. OpenCode 会自动加载此目录下的命令

## 模板变量

命令模板中可以使用以下变量：

- `$ARGUMENTS`: 命令参数
- `$FILE`: 当前文件
- `$PROJECT`: 项目根目录

## 相关文档

- [OpenCode 配置文档 - Commands](https://opencode.ai/docs/config/#commands)
