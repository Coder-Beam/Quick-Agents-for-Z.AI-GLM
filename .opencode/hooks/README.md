# QuickAgents Hooks System

> 自动化钩子系统 - 提供工具执行、Git提交、会话生命周期等自动化能力

---

## 目录结构

```
.opencode/hooks/
├── hooks.json              # 钩子配置文件
├── README.md               # 本文档
│
├── pre-tool/               # 工具执行前钩子
│   ├── secret-detector.sh  # 敏感信息检测
│   └── file-protector.sh   # 文件保护
│
├── post-tool/              # 工具执行后钩子
│   ├── auto-formatter.sh   # 自动格式化
│   └── type-checker.sh     # 类型检查
│
├── pre-commit/             # Git提交前钩子
│   ├── test-runner.sh      # 测试运行
│   └── lint-check.sh       # 代码检查
│
├── session/                # 会话生命周期钩子
│   ├── env-check.sh        # 环境检查
│   └── metrics-logger.sh   # 指标记录
│
├── task/                   # 任务生命周期钩子
│   ├── task-validator.sh   # 任务验证
│   └── task-completer.sh   # 任务完成处理
│
└── notification/           # 通知钩子
    └── desktop-notify.sh   # 桌面通知
```

---

## 钩子类型

### 1. pre-tool（工具执行前）

| 钩子名称 | 功能 | 优先级 |
|----------|------|--------|
| secret-detector | 检测敏感信息（API密钥、密码等） | 100 |
| file-protector | 保护关键文件不被意外修改 | 90 |

### 2. post-tool（工具执行后）

| 钩子名称 | 功能 | 优先级 |
|----------|------|--------|
| auto-formatter | 自动格式化代码 | 50 |
| type-checker | TypeScript类型检查 | 40 |

### 3. pre-commit（Git提交前）

| 钩子名称 | 功能 | 优先级 |
|----------|------|--------|
| test-runner | 运行相关测试 | 100 |
| lint-check | ESLint/Prettier检查 | 90 |

### 4. session（会话生命周期）

| 钩子名称 | 触发时机 | 功能 |
|----------|----------|------|
| env-check | 会话开始 | 检查环境配置 |
| metrics-logger | 会话结束 | 记录会话指标 |

### 5. task（任务生命周期）

| 钩子名称 | 触发时机 | 功能 |
|----------|----------|------|
| task-validator | 任务开始前 | 验证任务可行性 |
| task-completer | 任务完成后 | 清理和记录 |

### 6. notification（通知）

| 钩子名称 | 事件 | 功能 |
|----------|------|------|
| desktop-notify | task_complete, error, review_required | 桌面通知 |

---

## 配置说明

### hooks.json 结构

```json
{
  "version": "1.0.0",
  "enabled": true,
  "hooks": {
    "pre-tool": {
      "enabled": true,
      "timeout": 30000,
      "hooks": [...]
    }
  },
  "globalSettings": {
    "logLevel": "info",
    "failFast": true,
    "parallel": false
  }
}
```

### 钩子配置属性

| 属性 | 类型 | 说明 |
|------|------|------|
| name | string | 钩子名称 |
| script | string | 脚本路径 |
| enabled | boolean | 是否启用 |
| priority | number | 优先级（越高越先执行） |
| timeout | number | 超时时间（毫秒） |
| triggers | array | 触发条件 |

---

## 使用方式

### 启用/禁用所有钩子

```bash
# 禁用
jq '.enabled = false' .opencode/hooks/hooks.json > tmp.json && mv tmp.json .opencode/hooks/hooks.json

# 启用
jq '.enabled = true' .opencode/hooks/hooks.json > tmp.json && mv tmp.json .opencode/hooks/hooks.json
```

### 启用/禁用特定钩子

```bash
# 禁用 pre-tool 的 secret-detector
jq '.hooks.pre-tool.hooks[0].enabled = false' .opencode/hooks/hooks.json > tmp.json && mv tmp.json .opencode/hooks/hooks.json
```

### 手动执行钩子

```bash
# 执行 pre-tool 钩子
./.opencode/hooks/pre-tool/secret-detector.sh
```

---

## 环境要求

- **Bash**: Git Bash (Windows) / Bash (Linux/macOS)
- **jq**: JSON 处理工具（可选，用于配置修改）
- **Node.js**: >= 18.0.0（用于某些钩子）

---

## 日志

钩子执行日志位于：`.opencode/logs/hooks.log`

---

## 最佳实践

1. **不要过度使用钩子**: 只启用必要的钩子，避免影响性能
2. **设置合理的超时**: 根据项目大小调整 timeout
3. **定期检查日志**: 监控钩子执行情况
4. **保护敏感文件**: 使用 file-protector 保护 .env 等文件

---

*版本: 1.0.0 | 更新时间: 2026-03-26*
