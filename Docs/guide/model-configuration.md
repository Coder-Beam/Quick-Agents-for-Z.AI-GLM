# QuickAgents 模型配置指南

> 版本: 2.7.0 | 更新时间: 2026-03-30
> 专为 ZhipuAI GLM Coding Plan 优化

---

## 概述

QuickAgents 采用**中心化模型配置**系统，专为 **ZhipuAI GLM Coding Plan** 优化，支持三种模型使用方案：

| 方案 | 描述 | 适用场景 |
|------|------|----------|
| **Coding Plan** | 使用智谱AI Coding Plan订阅套餐 | 编程开发、代码生成、架构设计（推荐） |
| **单一大模型** | 所有任务使用同一个模型 | 简单项目、新手用户、成本控制 |
| **混合大模型** | 不同任务类型使用不同模型 | 复杂项目、追求最优效果 |

---

## ZhipuAI GLM 模型系列

### Coding Plan 可用模型

| 模型 | 描述 | 上下文 | 能力 |
|------|------|--------|------|
| **GLM-5.1** | 最新旗舰，Coding Plan全量支持，思考模式增强 | 204K | Coding, Agent, Thinking, Function-Call, MCP |
| **GLM-5** | 旗舰基座，面向Agentic Engineering，Coding对齐Claude Opus 4.5 | 204K | Coding, Agent, Thinking, Function-Call, MCP |
| **GLM-4.7** | 旗舰版，面向Agentic Coding，Coding对齐Claude Sonnet 4.5 | 204K | Coding, Agent, Thinking, Function-Call, MCP |
| **GLM-4.7-FlashX** | 轻量高速版，适合简单任务和快速迭代 | 204K | Coding, Quick-Response |
| **GLM-4.5-Air** | 轻量版，适合简单任务和快速响应 | 128K | Quick-Response |

### 能力说明

| 能力 | 描述 |
|------|------|
| **Coding** | 代码生成、理解、调试能力 |
| **Agent** | 长程任务执行、工具调用、自主规划 |
| **Thinking** | 深度思考模式，复杂推理 |
| **Function-Call** | 函数调用能力 |
| **MCP** | Model Context Protocol 支持 |
| **Quick-Response** | 快速响应，低延迟 |

### Claude Code 模型映射

Coding Plan 提供 Anthropic 兼容接口，Claude Code 用户可无缝切换：

| Claude 模型 | 映射到 GLM | 说明 |
|-------------|-----------|------|
| Claude Opus | GLM-5 | 旗舰级能力对齐 |
| Claude Sonnet | GLM-4.7 | 平衡性能与速度 |
| Claude Haiku | GLM-4.5-Air | 快速响应 |

---

## 方案详解

### 方案A：Coding Plan（推荐）

**什么是Coding Plan？**

Coding Plan 是智谱AI专门为AI编码打造的订阅套餐：
- 针对编程场景深度优化
- 支持 Agentic Engineering 工作流
- Coding 能力对齐 Claude Opus 4.5 / Sonnet 4.5
- 支持 MCP (Model Context Protocol)
- 支持 Function Call 和 Thinking 模式

**API 端点**：
```
标准端点: https://open.bigmodel.cn/api/coding/paas/v4
Anthropic兼容: https://open.bigmodel.cn/api/anthropic
```

**环境变量配置**：
```bash
ANTHROPIC_BASE_URL=https://open.bigmodel.cn/api/anthropic
API_TIMEOUT_MS=3000000
CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
```

**配置示例**：
```json
{
  "strategy": "coding-plan",
  "default": {
    "primary": "GLM-5",
    "fallback": "GLM-4.7"
  },
  "providers": {
    "zhipuai-coding-plan": {
      "baseUrl": "https://open.bigmodel.cn/api/coding/paas/v4",
      "anthropicBaseUrl": "https://open.bigmodel.cn/api/anthropic"
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
  "lockModel": "GLM-5",
  "default": {
    "primary": "GLM-5",
    "fallback": null
  }
}
```

**CLI命令**：
```bash
# 锁定所有Agent使用GLM-5
qka models lock GLM-5
```

### 方案C：混合大模型

**适用场景**：
- 复杂项目，需要不同模型的专长
- 追求最优效果
- 成本与性能平衡

**推荐映射**（基于 Coding Plan）：

| 任务类型 | 推荐模型 | 原因 |
|----------|----------|------|
| 规划 (planning) | GLM-5 | 需要深度思考和长程规划 |
| 编码 (coding) | GLM-5 | Coding能力对齐Claude Opus 4.5 |
| 调试 (debug) | GLM-5 | 调试需要深度分析 |
| 审查 (review) | GLM-5 | 审查需要深度理解 |
| 安全 (security) | GLM-5 | 安全审计需要深度分析 |
| 重构 (refactor) | GLM-5 | 重构需要强Coding能力 |
| 咨询 (consulting) | GLM-5 | 需要强推理和规划能力 |
| 编排 (orchestration) | GLM-5 | 需要Agent SOTA级长程执行 |
| 文档 (docs) | GLM-4.7 | 文档生成需要通用能力 |
| Skill管理 (skill) | GLM-4.7 | Skill管理需要通用能力 |
| 性能分析 (perf) | GLM-4.7 | 需要一定分析能力 |
| 测试 (testing) | GLM-4.7-FlashX | 重复性任务，轻量版效率更高 |
| 依赖管理 (deps) | GLM-4.7-FlashX | 简单任务，轻量版即可 |
| CI/CD (cicd) | GLM-4.7-FlashX | 标准化流程，轻量版效率更高 |

**配置示例**：
```json
{
  "strategy": "coding-plan",
  "default": {
    "primary": "GLM-5",
    "fallback": "GLM-4.7"
  },
  "categories": {
    "planning": "GLM-5",
    "coding": "GLM-5",
    "debug": "GLM-5",
    "review": "GLM-5",
    "security": "GLM-5",
    "refactor": "GLM-5",
    "consulting": "GLM-5",
    "orchestration": "GLM-5",
    "docs": "GLM-4.7",
    "skill": "GLM-4.7",
    "perf": "GLM-4.7",
    "testing": "GLM-4.7-FlashX",
    "deps": "GLM-4.7-FlashX",
    "cicd": "GLM-4.7-FlashX"
  }
}
```

---

## 配置文件结构

### .opencode/config/models.json

```json
{
  "$schema": "./models-schema.json",
  "version": "2.7.0",
  "description": "QuickAgents model configuration optimized for ZhipuAI GLM Coding Plan",
  
  "strategy": "coding-plan",
  "lockModel": null,
  
  "default": {
    "primary": "GLM-5",
    "fallback": "GLM-4.7"
  },
  
  "providers": {
    "zhipuai-coding-plan": {
      "displayName": "智谱AI Coding Plan",
      "description": "专为AI编码打造的订阅套餐，针对编程场景深度优化",
      "baseUrl": "https://open.bigmodel.cn/api/coding/paas/v4",
      "anthropicBaseUrl": "https://open.bigmodel.cn/api/anthropic",
      "models": {
        "GLM-5.1": { "id": "GLM-5.1", "reasoning": true, "recommended": true },
        "GLM-5": { "id": "GLM-5", "reasoning": true },
        "GLM-4.7": { "id": "GLM-4.7", "reasoning": true },
        "GLM-4.7-FlashX": { "id": "GLM-4.7-FlashX", "reasoning": false },
        "GLM-4.5-Air": { "id": "GLM-4.5-Air", "reasoning": false }
      },
      "defaultModel": "GLM-5"
    }
  },
  
  "categories": {
    "planning": "GLM-5",
    "coding": "GLM-5",
    "debug": "GLM-5",
    "review": "GLM-5",
    "security": "GLM-5",
    "refactor": "GLM-5",
    "consulting": "GLM-5",
    "orchestration": "GLM-5",
    "docs": "GLM-4.7",
    "skill": "GLM-4.7",
    "perf": "GLM-4.7",
    "testing": "GLM-4.7-FlashX",
    "deps": "GLM-4.7-FlashX",
    "cicd": "GLM-4.7-FlashX"
  },
  
  "agentMapping": {
    "yinglong-init": "planning",
    "fenghou-plan": "planning",
    "fenghou-orchestrate": "orchestration",
    "kuafu-debug": "debug",
    "jianming-review": "review",
    "mengzhang-security": "security",
    "gonggu-refactor": "refactor",
    "boyi-consult": "consulting",
    "chisongzi-advise": "consulting",
    "cangjie-doc": "docs",
    "huodi-skill": "skill",
    "hengge-perf": "perf",
    "lishou-test": "testing",
    "huodi-deps": "deps",
    "hengge-cicd": "cicd"
  },
  
  "agentOverrides": {},
  
  "codingPlanConfig": {
    "claudeCodeMapping": {
      "opus": "GLM-5",
      "sonnet": "GLM-4.7",
      "haiku": "GLM-4.5-Air"
    },
    "envVariables": {
      "ANTHROPIC_BASE_URL": "https://open.bigmodel.cn/api/anthropic",
      "API_TIMEOUT_MS": "3000000",
      "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"
    }
  },
  
  "versionUpgrade": {
    "autoDetect": true,
    "checkUrl": "https://docs.bigmodel.cn/llms.txt",
    "upgradePath": {
      "GLM-4": "GLM-4.7",
      "GLM-4.5": "GLM-4.7",
      "GLM-4.6": "GLM-4.7",
      "GLM-4.7": "GLM-5",
      "GLM-5": "GLM-5.1"
    },
    "notifications": true
  },
  
  "agentRecommendations": {
    "yinglong-init": {
      "model": "GLM-5",
      "reason": "项目初始化需要强规划能力和长程任务执行"
    }
  }
}
```

---

## 模型版本自动升级

### 自动检测

QuickAgents 会自动检测智谱AI发布的新版本：
- 自动从 `https://docs.bigmodel.cn/llms.txt` 获取最新模型信息
- 检测到新版本时通知用户

### 升级路径

| 当前版本 | 升级到 |
|----------|--------|
| GLM-4 | GLM-4.7 |
| GLM-4.5 | GLM-4.7 |
| GLM-4.6 | GLM-4.7 |
| GLM-4.7 | GLM-5 |
| GLM-5 | GLM-5.1 |

### 升级命令

```bash
# 查看当前配置
qka models show

# 查看可用模型列表
qka models list

# 检查 GLM 更新
qka models check-updates

# 预览升级（推荐先执行）
qka models upgrade --dry-run

# 执行升级
qka models upgrade --force

# 升级到指定版本
qka models upgrade --to GLM-5.1 --force

# 切换策略
qka models strategy coding-plan --force
qka models strategy single-model --model GLM-5 --force

# 锁定/解锁模型
qka models lock GLM-5 --force
qka models unlock
```

### GLM 版本自动同步 Skill

QuickAgents 提供了 `glm-version-sync-skill` 用于自动检测 GLM 模型更新：

**功能**：
- 从 `https://docs.bigmodel.cn/llms.txt` 获取最新 GLM 模型信息
- 与当前 `models.json` 配置比较
- 自动备份配置文件
- 支持升级预览（dry-run）
- 支持回滚到上一个版本

**使用方式**：

```bash
# 检查更新
python .opencode/skills/glm-version-sync-skill/scripts/glm_version_sync.py check

# 查看当前状态
python .opencode/skills/glm-version-sync-skill/scripts/glm_version_sync.py status

# 预览升级（推荐先执行）
python .opencode/skills/glm-version-sync-skill/scripts/glm_version_sync.py upgrade --dry-run

# 执行升级
python .opencode/skills/glm-version-sync-skill/scripts/glm_version_sync.py upgrade

# 升级到指定版本
python .opencode/skills/glm-version-sync-skill/scripts/glm_version_sync.py upgrade GLM-5.1
```

### 升级路径配置

```json
{
  "versionUpgrade": {
    "autoDetect": true,
    "checkUrl": "https://docs.bigmodel.cn/llms.txt",
    "upgradePath": {
      "GLM-4": "GLM-4.7",
      "GLM-4.5": "GLM-4.7",
      "GLM-4.6": "GLM-4.7",
      "GLM-4.7": "GLM-5",
      "GLM-5": "GLM-5.1"
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
qka models show

# 列出所有可用模型
qka models list

# 查看特定Agent的模型
qka models show --agent kuafu-debug
```

### 方案切换

```bash
# 切换到Coding Plan方案（推荐）
qka models strategy coding-plan

# 切换到单一大模型方案
qka models strategy single-model --model GLM-5

# 切换到混合方案
qka models strategy hybrid
```

### 锁定单一模型

```bash
# 所有Agent使用GLM-5
qka models lock GLM-5

# 解除锁定
qka models unlock
```

### 升级模型

```bash
# 检查更新
qka models check-updates

# 升级指定模型
qka models upgrade GLM-5 GLM-5.1

# 升级特定类别
qka models upgrade --category debug GLM-5 GLM-5.1
```

### 覆盖Agent模型

```bash
# 为特定Agent设置模型
qka models override kuafu-debug GLM-5

# 清除覆盖
qka models override --clear kuafu-debug
```

---

## 配置优先级

```
agentOverrides > categories > default > Agent配置文件
```

示例：
```json
{
  "default": { "primary": "GLM-4.7" },
  "categories": { "debug": "GLM-5" },
  "agentOverrides": { "kuafu-debug": "GLM-5.1" }
}
```

对于 `kuafu-debug` Agent：
1. 检查 `agentOverrides.kuafu-debug` → `GLM-5.1` ✅

---

## 故障排查

### 问题1：模型未找到

**错误**: `Model 'GLM-5' not found`

**解决**: 检查 `providers` 配置中是否包含该模型

### 问题2：Coding Plan不可用

**检查**:
1. 确认已订阅 Coding Plan 套餐
2. 确认 API Key 有 Coding Plan 权限
3. 确认使用正确的 Base URL

### 问题3：配置不生效

**检查步骤**:
1. 确认 `.opencode/config/models.json` 存在
2. 检查JSON格式是否正确
3. 运行 `qka models show` 查看当前配置

### 问题4：Claude Code 兼容问题

**解决**:
1. 设置环境变量 `ANTHROPIC_BASE_URL=https://open.bigmodel.cn/api/anthropic`
2. 使用 Claude Code 模型映射：Opus→GLM-5, Sonnet→GLM-4.7, Haiku→GLM-4.5-Air

---

## Agent 模型推荐

基于 Coding Plan 的 Agent 模型推荐：

### 旗舰级任务（推荐 GLM-5）

| Agent | 任务类型 | 原因 |
|-------|----------|------|
| yinglong-init | 项目初始化 | 需要强规划能力和长程任务执行 |
| fenghou-orchestrate | 任务编排 | 需要 Agent SOTA 级长程执行能力 |
| fenghou-plan | 计划制定 | 需要深度思考和推理能力 |
| kuafu-debug | 调试 | Coding 能力对齐 Claude Opus 4.5 |
| jianming-review | 代码审查 | 需要深度理解和推理能力 |
| boyi-consult | 需求咨询 | 需要强推理和规划能力 |
| chisongzi-advise | 技术推荐 | 需要综合分析能力 |
| mengzhang-security | 安全审计 | 需要深度分析能力 |
| gonggu-refactor | 重构 | 需要强 Coding 能力 |

### 标准级任务（推荐 GLM-4.7）

| Agent | 任务类型 | 原因 |
|-------|----------|------|
| cangjie-doc | 文档生成 | 需要通用能力，4.7 已足够 |
| huodi-skill | Skill 管理 | 需要通用能力 |
| hengge-perf | 性能分析 | 需要一定分析能力 |

### 轻量级任务（推荐 GLM-4.7-FlashX）

| Agent | 任务类型 | 原因 |
|-------|----------|------|
| lishou-test | 测试执行 | 重复性任务，轻量版效率更高 |
| huodi-deps | 依赖管理 | 简单任务，轻量版即可 |
| hengge-cicd | CI/CD | 标准化流程，轻量版效率更高 |

---

## 最佳实践

1. **生产环境**: 使用 `qka models lock` 锁定稳定版本
2. **开发环境**: 使用 Coding Plan 方案获得最佳编程体验
3. **版本升级**: 先在 `agentOverrides` 中测试新模型
4. **备份配置**: 修改前备份 `models.json`
5. **Coding Plan**: 编程场景优先使用 Coding Plan
6. **成本优化**: 简单任务使用 FlashX 版本
7. **Claude Code**: 利用 Anthropic 兼容接口无缝切换

---

*版本: 2.7.0 | 适用于 QuickAgents v2.7.0+*
