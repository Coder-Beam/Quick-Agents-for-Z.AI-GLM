# QuickAgents 模型配置指南

> 版本: 2.6.8 | 更新时间: 2026-03-30

---

## 概述

QuickAgents 采用**中心化模型配置**系统，支持三种模型使用方案：

| 方案 | 描述 | 适用场景 |
|------|------|----------|
| **Coding Plan** | 使用智谱AI编程优化模型组合包 | 编程开发、代码生成、架构设计 |
| **单一大模型** | 所有任务使用同一个模型 | 简单项目、新手用户、成本控制 |
| **混合大模型** | 不同任务类型使用不同模型 | 复杂项目、追求最优效果 |

---

## 方案详解

### 方案A：Coding Plan（推荐）

**什么是Coding Plan？**

Coding Plan是智谱AI专门针对编程场景优化的模型组合包：
- 代码生成更精准
- 架构理解更深入
- Bug调试更高效
- 技术文档更专业

**模型标识格式**：
```
zhipuai-coding-plan/glm-5
```

**与普通版本的区别**：

| 特性 | Coding Plan | 普通版本 |
|------|-------------|----------|
| 代码生成质量 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 架构理解 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 调试能力 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 通用对话 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**配置示例**：
```json
{
  "strategy": "coding-plan",
  "providers": {
    "zhipuai": {
      "plans": {
        "coding-plan": {
          "prefix": "zhipuai-coding-plan",
          "models": {
            "glm-5": "zhipuai-coding-plan/glm-5"
          }
        }
      }
    }
  }
}
```

### 方案B：单一大模型

**适用场景**：
- 刚接触AI编程的新手
- 项目简单，不需要复杂模型
- 控制API成本

**配置示例**：
```json
{
  "strategy": "single-model",
  "lockModel": "glm-5",
  "default": {
    "primary": "glm-5",
    "fallback": null
  }
}
```

**CLI命令**：
```bash
# 锁定所有Agent使用GLM-5
qa models lock glm-5
```

### 方案C：混合大模型

**适用场景**：
- 复杂项目，需要不同模型的专长
- 追求最优效果
- 拥有多个API Key

**推荐映射**：

| 任务类型 | 推荐模型 | 原因 |
|----------|----------|------|
| 规划 (planning) | GLM-5 | 中文理解强，逻辑清晰 |
| 编码 (coding) | GLM-5 Coding Plan | 代码生成精准 |
| 调试 (debug) | Claude Sonnet | 调试能力强 |
| 审查 (review) | Claude Opus | 审查细致全面 |
| 测试 (testing) | GLM-5-Flash | 快速生成测试用例 |
| 文档 (docs) | GLM-5 | 中文文档流畅 |

**配置示例**：
```json
{
  "strategy": "hybrid",
  "default": {
    "primary": "glm-5",
    "fallback": "claude-sonnet-4-5"
  },
  "categories": {
    "planning": "glm-5",
    "coding": "glm-5",
    "debug": "claude-sonnet-4-5",
    "review": "claude-3-opus",
    "testing": "glm-5-flash",
    "docs": "glm-5"
  }
}
```

---

## 配置文件结构

### .opencode/config/models.json

```json
{
  "$schema": "./models-schema.json",
  "version": "2.6.8",
  "strategy": "coding-plan",
  "lockModel": null,
  "default": {
    "primary": "glm-5",
    "fallback": null
  },
  "providers": {
    "zhipuai": {
      "displayName": "智谱AI (ZhipuAI)",
      "plans": {
        "coding-plan": {
          "name": "Coding Plan",
          "prefix": "zhipuai-coding-plan",
          "models": {
            "glm-5": "zhipuai-coding-plan/glm-5"
          }
        },
        "standard": {
          "name": "标准版",
          "prefix": "zhipuai",
          "models": {
            "glm-5": "zhipuai/glm-5",
            "glm-5-flash": "zhipuai/glm-5-flash"
          }
        }
      }
    },
    "anthropic": {
      "displayName": "Anthropic",
      "models": {
        "claude-sonnet-4-5": "anthropic/claude-sonnet-4-5",
        "claude-3-opus": "anthropic/claude-3-opus"
      }
    }
  },
  "categories": {
    "planning": "glm-5",
    "coding": "glm-5",
    "debug": "glm-5",
    "review": "glm-5",
    "testing": "glm-5-flash",
    "docs": "glm-5"
  },
  "agentMapping": {
    "yinglong-init": "planning",
    "cangjie-doc": "docs",
    "kuafu-debug": "debug",
    "jianming-review": "review",
    "lishou-test": "testing"
  },
  "agentOverrides": {},
  "versionUpgrade": {
    "autoDetect": true,
    "upgradePath": {
      "glm-4": "glm-5",
      "glm-5": "glm-5.1"
    }
  }
}
```

---

## 模型版本自动升级

### 自动检测

QuickAgents会自动检测智谱AI发布的新版本：
- GLM-5 → GLM-5.1
- GLM-5.1 → GLM-5.2

### 升级命令

```bash
# 查看可用升级
qa models check-updates

# 升级所有GLM-5到GLM-5.1
qa models upgrade glm-5 glm-5.1

# 升级Coding Plan版本
qa models upgrade --plan coding-plan glm-5 glm-5.1

# 自动升级到最新版本
qa models upgrade --auto
```

### 升级路径配置

```json
{
  "versionUpgrade": {
    "autoDetect": true,
    "upgradePath": {
      "glm-4": "glm-5",
      "glm-5": "glm-5.1",
      "glm-5.1": "glm-5.2",
      "claude-3-opus": "claude-sonnet-4-5"
    },
    "notifications": true
  }
}
```

---

## CLI 命令参考

### 查看配置

```bash
# 查看当前配置
qa models show

# 列出所有可用模型
qa models list

# 查看特定Agent的模型
qa models show --agent kuafu-debug
```

### 方案切换

```bash
# 切换到Coding Plan方案
qa models strategy coding-plan

# 切换到单一大模型方案
qa models strategy single-model --model glm-5

# 切换到混合方案
qa models strategy hybrid
```

### 锁定单一模型

```bash
# 所有Agent使用GLM-5
qa models lock glm-5

# 解除锁定
qa models unlock
```

### 升级模型

```bash
# 检查更新
qa models check-updates

# 升级指定模型
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

## 配置优先级

```
agentOverrides > categories > default > Agent配置文件
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

---

## 故障排查

### 问题1：模型未找到

**错误**: `Model 'glm-5' not found`

**解决**: 检查 `providers` 配置中是否包含该模型

### 问题2：Coding Plan不可用

**检查**:
1. 确认使用 `zhipuai-coding-plan/` 前缀
2. 确认API Key有Coding Plan权限

### 问题3：配置不生效

**检查步骤**:
1. 确认 `.opencode/config/models.json` 存在
2. 检查JSON格式是否正确
3. 运行 `qa models show` 查看当前配置

---

## 最佳实践

1. **生产环境**: 使用 `qa models lock` 锁定稳定版本
2. **开发环境**: 使用混合配置测试不同模型
3. **版本升级**: 先在 `agentOverrides` 中测试新模型
4. **备份配置**: 修改前备份 `models.json`
5. **Coding Plan**: 编程场景优先使用Coding Plan

---

*版本: 2.6.8 | 适用于 QuickAgents v2.6.8+*
