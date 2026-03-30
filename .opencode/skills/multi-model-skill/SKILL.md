---
name: multi-model-skill
description: |
  Multi-model collaboration skill providing intelligent model routing,
  automatic fallback, load balancing, and cost optimization.
license: MIT
allowed-tools:
  - read
  - skill
dependencies:
  - project-memory-skill
metadata:
  category: optimization
  priority: medium
  version: 1.0.0
---

# Multi-Model Skill

## 概述

多模型协同技能，提供智能模型路由、自动Fallback、负载均衡和成本优化功能。

## 核心能力

### 1. 智能模型路由

根据任务特征自动选择最合适的模型：

```
任务类型 → 模型Profile
├─ code-generation → primary (GLM-5)
├─ code-review → reasoning (GPT-4o)
├─ documentation → creative (Claude-3-Opus)
├─ quick-fix → fast (GLM-4-Flash)
└─ image-analysis → vision (Gemini-1.5-Pro)
```

### 2. 自动Fallback机制

当首选模型不可用时，自动切换到备选模型：

```
Fallback Chain:
- default: [primary, reasoning, fast]
- critical: [reasoning, primary, creative]
- fast_path: [fast, primary]
- vision_path: [vision, creative, primary]
```

### 3. 负载均衡

采用加权轮询策略，确保API调用分布均匀：

```json
{
  "zhipu": 50,
  "openai": 30,
  "anthropic": 15,
  "google": 5
}
```

### 4. 成本优化

智能控制API成本，优先使用性价比高的模型：

```json
{
  "primary": $0.01/task,
  "reasoning": $0.10/task,
  "creative": $0.05/task,
  "fast": $0.005/task,
  "vision": $0.05/task
}
```

## 使用方式

### 基础路由

```markdown
<!-- 使用默认路由 -->
@primary 请分析这段代码的性能瓶颈

<!-- 显式指定模型Profile -->
@reasoning 设计一个高可用的微服务架构
@creative 编写一份用户友好的API文档
@fast 快速格式化这段代码
@vision 分析这个架构图的组件关系
```

### 任务类型路由

```markdown
<!-- 自动识别任务类型 -->
请生成用户认证模块的代码  → 自动使用 primary
审查这个PR的代码质量      → 自动使用 reasoning
为这个API编写文档         → 自动使用 creative
```

### Category路由

```markdown
<!-- 基于Category自动路由 -->
/ultrabrain 分析系统瓶颈  → reasoning模型
/quick 快速修复这个bug    → fast模型
```

## 配置说明

### 模型Profile定义

在 `.opencode/config/models.json` 中定义：

```json
{
  "model_profiles": {
    "primary": {
      "model": "glm-5",
      "provider": "zhipu",
      "temperature": 0.1,
      "max_tokens": 4096,
      "use_case": ["general", "coding", "planning"]
    }
  }
}
```

### Fallback配置

```json
{
  "fallback_chain": {
    "default": ["primary", "reasoning", "fast"],
    "critical": ["reasoning", "primary", "creative"]
  }
}
```

### 负载均衡配置

```json
{
  "load_balancing": {
    "strategy": "weighted_round_robin",
    "weights": {
      "zhipu": 50,
      "openai": 30
    },
    "health_check": {
      "interval_seconds": 60,
      "failure_threshold": 3
    }
  }
}
```

## 工作流程

### 路由决策流程

```
1. 分析任务特征
   ├─ 任务类型 (code/review/doc/...)
   ├─ Category (ultrabrain/quick/...)
   └─ 复杂度 (simple/medium/complex)

2. 查询路由规则
   └─ task_type_mapping / category_mapping

3. 选择模型Profile
   └─ primary / reasoning / creative / fast / vision

4. 获取Provider配置
   └─ provider / model / temperature / max_tokens

5. 执行请求
   ├─ 成功 → 返回结果
   └─ 失败 → 触发Fallback

6. Fallback处理
   └─ 按fallback_chain依次尝试

7. 负载均衡
   └─ 加权轮询选择Provider实例

8. 成本优化
   └─ 检查cost_limits，必要时降级
```

### 错误处理流程

```
请求失败
├─ 网络错误 → 重试 (最多3次，指数退避)
├─ 超时 → Fallback到下一个模型
├─ Rate Limit → 等待后重试或Fallback
├─ 模型不可用 → Fallback
└─ 成本超限 → 降级到更便宜的模型
```

## 监控指标

### 性能指标

- **请求延迟**: P50/P95/P99延迟
- **成功率**: 按Provider和模型统计
- **Fallback率**: 触发Fallback的请求比例
- **成本统计**: 按任务类型和模型统计

### 健康检查

```json
{
  "providers": {
    "zhipu": {
      "status": "healthy",
      "latency_p95": 1200,
      "success_rate": 0.99,
      "circuit_breaker": "closed"
    }
  }
}
```

## 最佳实践

### 1. 合理配置Fallback链

```json
// 推荐：根据任务重要性配置
"critical": ["reasoning", "primary", "creative"],
"default": ["primary", "reasoning", "fast"]
```

### 2. 启用成本优化

```json
{
  "cost_optimization": {
    "enabled": true,
    "max_cost_per_task": 1.00,
    "prefer_cheaper": true
  }
}
```

### 3. 配置合理的超时

```json
{
  "error_handling": {
    "timeout": {
      "connection_ms": 5000,
      "request_ms": 60000
    }
  }
}
```

### 4. 启用熔断器

```json
{
  "error_handling": {
    "circuit_breaker": {
      "enabled": true,
      "failure_threshold": 5,
      "reset_timeout_ms": 60000
    }
  }
}
```

## 与其他Skill集成

### 与Category系统集成

```markdown
Category → 模型Profile
- ultrabrain → reasoning
- visual-engineering → vision
- quick → fast
```

### 与Orchestrator集成

```markdown
orchestrator根据子任务类型，自动调用multi-model-skill进行路由
```

### 与Background Agents集成

```markdown
后台任务自动使用fast Profile，降低成本
```

## 故障排查

### 问题1：Fallback过于频繁

**可能原因**:
- 首选模型不稳定
- 超时配置过短
- Rate Limit限制

**解决方案**:
- 增加超时时间
- 调整Rate Limit
- 优化Fallback链

### 问题2：成本超预算

**可能原因**:
- 过多使用高成本模型
- 未启用成本优化

**解决方案**:
- 启用 `cost_optimization.enabled`
- 调整 `max_cost_per_task`
- 增加fast模型使用权重

### 问题3：响应延迟高

**可能原因**:
- Provider网络问题
- 模型处理慢
- 未启用负载均衡

**解决方案**:
- 启用负载均衡
- 优化健康检查间隔
- 考虑使用更快的模型

## 扩展指南

### 添加新Provider

1. 在 `models.json` 的 `providers` 中添加配置
2. 配置 `rate_limit` 和 `priority`
3. 在 `load_balancing.weights` 中设置权重
4. 测试连接和Fallback

### 添加新Profile

1. 在 `model_profiles` 中定义新Profile
2. 配置 `model`、`provider`、`temperature`
3. 在 `routing_rules` 中添加映射规则
4. 在 `fallback_chain` 中添加到相应链

---

*版本: 1.0.0 | 创建时间: 2026-03-25*
