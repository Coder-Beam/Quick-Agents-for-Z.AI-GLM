# QuickAgents 模型配置指南

> 版本: 2.6.8 | 更新时间: 2026-03-30

---

## 概述

QuickAgents 采用**中心化模型配置**系统，所有Agent的模型配置统一管理在 `.opencode/config/models.json` 中。

### 优势

1. **统一管理** - 所有模型配置在一个文件中
2. **灵活切换** - 可快速切换模型提供商和版本
3. **锁定单一模型** - 可强制所有Agent使用同一模型
4. **版本升级** - 模型升级只需修改一处

---

## 配置文件结构

### .opencode/config/models.json

```json
{
  "version": "2.6.8",
  "default": {
    "primary": "glm-5",
    "fallback": null
  },
  "providers": {
    "zhipuai": {
      "models": {
        "glm-5": "zhipuai-coding-plan/glm-5",
        "glm-5-flash": "zhipuai/glm-5-flash"
      }
    },
    "anthropic": {
      "models": {
        "claude-sonnet-4-5": "anthropic/claude-sonnet-4-5",
        "claude-3-opus": "anthropic/claude-3-opus"
      }
    }
  },
  "categories": {
    "planning": "glm-5",
    "coding": "glm-5",
    "consulting": "glm-5",
    "orchestration": "glm-5",
    "debug": "claude-sonnet-4-5",
    "review": "claude-3-opus",
    "testing": "claude-sonnet-4-5",
    "security": "claude-sonnet-4-5",
    "refactor": "claude-sonnet-4-5",
    "docs": "glm-5",
    "skill": "glm-5",
    "deps": "glm-5",
    "perf": "glm-5",
    "cicd": "glm-5"
  },
  "agentMapping": {
    "yinglong-init": "planning",
    "cangjie-doc": "docs",
    "fenghou-orchestrate": "orchestration",
    "fenghou-plan": "planning",
    "huodi-skill": "skill",
    "huodi-deps": "deps",
    "kuafu-debug": "debug",
    "lishou-test": "testing",
    "jianming-review": "review",
    "mengzhang-security": "security",
    "gonggu-refactor": "refactor",
    "boyi-consult": "consulting",
    "chisongzi-advise": "consulting",
    "hengge-perf": "perf",
    "hengge-cicd": "cicd"
  },
  "agentOverrides": {}
}
```

---

## 使用场景

### 场景1：锁定单一大模型

如果你想所有Agent都使用同一个模型（如GLM-5）：

```json
{
  "default": {
    "primary": "glm-5",
    "fallback": null
  },
  "categories": {
    "planning": "glm-5",
    "coding": "glm-5",
    "consulting": "glm-5",
    "orchestration": "glm-5",
    "debug": "glm-5",
    "review": "glm-5",
    "testing": "glm-5",
    "security": "glm-5",
    "refactor": "glm-5",
    "docs": "glm-5",
    "skill": "glm-5",
    "deps": "glm-5",
    "perf": "glm-5",
    "cicd": "glm-5"
  }
}
```

### 场景2：混合使用多模型

根据任务类型使用不同模型：

```json
{
  "categories": {
    "planning": "glm-5",           // 规划任务用GLM-5
    "debug": "claude-sonnet-4-5",  // 调试任务用Claude
    "review": "claude-3-opus"      // 审查任务用Claude Opus
  }
}
```

### 场景3：覆盖特定Agent

如果只想改变某个特定Agent的模型：

```json
{
  "agentOverrides": {
    "kuafu-debug": "claude-3-opus",
    "jianming-review": "glm-5"
  }
}
```

### 场景4：添加新模型

当新版本发布时（如GLM-5.1）：

```json
{
  "providers": {
    "zhipuai": {
      "models": {
        "glm-5": "zhipuai-coding-plan/glm-5",
        "glm-5.1": "zhipuai-coding-plan/glm-5.1",
        "glm-5.2": "zhipuai-coding-plan/glm-5.2"
      }
    }
  },
  "categories": {
    "planning": "glm-5.2",  // 升级到最新版本
    "coding": "glm-5.1"     // 保守升级
  }
}
```

---

## 配置优先级

```
agentOverrides > categories > default
```

示例：
```json
{
  "default": { "primary": "glm-4" },
  "categories": { "debug": "glm-5" },
  "agentOverrides": { "kuafu-debug": "claude-sonnet-4-5" }
}
```

对于 `kuafu-debug` Agent：
1. 检查 `agentOverrides.kuafu-debug` → `claude-sonnet-4-5` ✅
2. 不存在则检查 `categories.debug` → `glm-5`
3. 都不存在则使用 `default.primary` → `glm-4`

---

## CLI 命令

### 查看当前配置

```bash
qa models list
qa models show
```

### 锁定单一模型

```bash
# 所有Agent使用GLM-5
qa models lock glm-5

# 所有Agent使用Claude
qa models lock claude-sonnet-4-5
```

### 升级模型版本

```bash
# 升级所有GLM-5到GLM-5.1
qa models upgrade glm-5 glm-5.1

# 升级特定类别
qa models upgrade --category debug claude-sonnet-4-5 claude-3-opus
```

### 覆盖Agent模型

```bash
# 为特定Agent设置模型
qa models override kuafu-debug claude-3-opus

# 清除覆盖
qa models override --clear kuafu-debug
```

---

## Agent 配置文件兼容

### 旧方式（仍然支持）

Agent配置文件中的 `model` 字段仍然有效，但优先级最低：

```yaml
---
name: kuafu-debug
model: anthropic/claude-sonnet-4-5  # 优先级最低
---
```

### 推荐方式

新版本推荐移除Agent配置中的 `model` 字段，使用中心化配置：

```yaml
---
name: kuafu-debug
# model 字段留空或删除，使用 models.json 配置
---
```

---

## 模型标识格式

| 提供商 | 格式 | 示例 |
|--------|------|------|
| ZhipuAI | `zhipuai-coding-plan/{model}` | `zhipuai-coding-plan/glm-5` |
| ZhipuAI (通用) | `zhipuai/{model}` | `zhipuai/glm-5-flash` |
| Anthropic | `anthropic/{model}` | `anthropic/claude-sonnet-4-5` |
| OpenAI | `openai/{model}` | `openai/gpt-4` |

---

## 故障排查

### 问题1：模型未找到

**错误**: `Model 'glm-5' not found`

**解决**: 检查 `providers` 配置中是否包含该模型

### 问题2：配置不生效

**检查步骤**:
1. 确认 `.opencode/config/models.json` 存在
2. 检查JSON格式是否正确
3. 运行 `qa models show` 查看当前配置

### 问题3：Agent仍使用旧模型

**原因**: Agent配置文件中的 `model` 字段优先级更高

**解决**: 
- 删除Agent配置文件中的 `model` 字段
- 或使用 `qa models override` 强制覆盖

---

## 版本升级指南

### 从 v2.6.7 升级到 v2.6.8

1. **自动迁移**: 升级时自动创建 `models.json`
2. **手动迁移**: 
   ```bash
   qa models init
   ```

### 从 v2.x 升级到 v3.0

1. 检查所有Agent配置文件
2. 移除 `model` 字段
3. 使用中心化配置

---

## 最佳实践

1. **生产环境**: 使用 `qa models lock` 锁定稳定版本
2. **开发环境**: 使用混合配置测试不同模型
3. **版本升级**: 先在 `agentOverrides` 中测试新模型
4. **备份配置**: 修改前备份 `models.json`

---

*版本: 2.6.8 | 适用于 QuickAgents v2.6.8+*
