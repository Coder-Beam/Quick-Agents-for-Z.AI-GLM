---
name: category-system
description: Category系统 - 语义化任务分类与智能模型选择
version: 1.0.0
---

# Category System Skill

> 基于 Oh-My-OpenAgent 的 Category 系统设计
> QuickAgents 的智能任务分类与模型路由

---

## 核心概念

### 什么是 Category？

**Category 是语义化的任务分类**，它描述"这是什么类型的工作"，而不是"使用哪个模型"。

**核心理念**：
- 🎯 **意图驱动**：根据任务意图选择最佳配置
- 🤖 **智能路由**：自动选择最适合的模型
- 🔄 **动态调整**：根据任务复杂度调整参数
- 🎨 **可扩展**：支持自定义 Category

### Category vs Model

**传统方式（不推荐）**：
```typescript
// ❌ 直接指定模型 - 产生分布偏差
task({ agent: "gpt-5.4", prompt: "..." });
task({ agent: "glm-5", prompt: "..." });
```

**Category 方式（推荐）**：
```typescript
// ✅ 语义化分类 - 意图清晰
task({ category: "visual-engineering", prompt: "..." });
task({ category: "ultrabrain", prompt: "..." });
task({ category: "quick", prompt: "..." });
```

---

## 内置 Categories

### 1. visual-engineering

**用途**：前端开发、UI/UX设计、样式、动画

**模型**：Gemini 2.0 Flash Exp
**温度**：0.7
**特点**：注重视觉效果和用户体验

**适用场景**：
- ✅ 前端组件开发
- ✅ UI/UX设计
- ✅ 样式调整
- ✅ 动画实现
- ✅ 响应式布局

**使用示例**：
```typescript
task({
  category: "visual-engineering",
  prompt: "创建一个响应式的登录表单组件"
});
```

### 2. ultrabrain

**用途**：深度逻辑推理、复杂架构决策

**模型**：GLM-5
**温度**：0.1
**特点**：深度思考，长期规划

**适用场景**：
- ✅ 系统架构设计
- ✅ 技术选型决策
- ✅ 复杂问题分析
- ✅ 性能优化策略
- ✅ 安全架构设计

**使用示例**：
```typescript
task({
  category: "ultrabrain",
  prompt: "设计微服务架构，支持百万级用户并发"
});
```

### 3. deep

**用途**：深入研究型任务、复杂重构

**模型**：GLM-5
**温度**：0.2
**特点**：行动前深入研究

**适用场景**：
- ✅ 代码库深度分析
- ✅ 复杂重构
- ✅ 遗留系统理解
- ✅ 跨模块协调
- ✅ 技术债务清理

**使用示例**：
```typescript
task({
  category: "deep",
  prompt: "重构认证系统，保持向后兼容"
});
```

### 4. artistry

**用途**：创造性任务、创新想法

**模型**：Gemini 2.0 Flash Exp
**温度**：0.9
**特点**：大胆创新，打破常规

**适用场景**：
- ✅ 创新功能设计
- ✅ 实验性开发
- ✅ 创意问题解决
- ✅ 新框架探索

**使用示例**：
```typescript
task({
  category: "artistry",
  prompt: "设计一个独特的数据可视化方案"
});
```

### 5. quick

**用途**：简单任务、快速修复

**模型**：GLM-4 Flash
**温度**：0.3
**特点**：快速、高效、直接

**适用场景**：
- ✅ 拼写错误修复
- ✅ 简单重构
- ✅ 配置调整
- ✅ 文档更新
- ✅ 小bug修复

**使用示例**：
```typescript
task({
  category: "quick",
  prompt: "修复 LoginButton.tsx 中的拼写错误"
});
```

### 6. writing

**用途**：文档编写、技术写作

**模型**：Gemini 2.0 Flash Exp
**温度**：0.5
**特点**：清晰、准确、易读

**适用场景**：
- ✅ API文档
- ✅ 用户指南
- ✅ README编写
- ✅ 技术博客
- ✅ 代码注释

**使用示例**：
```typescript
task({
  category: "writing",
  prompt: "编写 API 使用文档"
});
```

### 7. testing

**用途**：测试编写、测试策略

**模型**：GLM-5
**温度**：0.1
**特点**：全面、可靠、注重覆盖

**适用场景**：
- ✅ 单元测试
- ✅ 集成测试
- ✅ E2E测试
- ✅ 测试策略设计

**使用示例**：
```typescript
task({
  category: "testing",
  prompt: "为用户服务编写单元测试"
});
```

### 8. debugging

**用途**：调试、问题诊断

**模型**：GLM-5
**温度**：0.1
**特点**：系统化诊断、根因分析

**适用场景**：
- ✅ Bug诊断
- ✅ 性能问题分析
- ✅ 错误追踪
- ✅ 日志分析

**使用示例**：
```typescript
task({
  category: "debugging",
  prompt: "诊断登录接口超时问题"
});
```

---

## Category 自动检测

### 关键词映射

系统会根据任务描述中的关键词自动选择 Category：

| Category | 关键词 |
|----------|--------|
| visual-engineering | UI, ux, 界面, 前端, 样式, CSS, 动画, 布局, 响应式 |
| ultrabrain | 架构, 设计, 决策, 策略, 规划, 优化, 分析 |
| deep | 重构, 迁移, 研究, 分析, 理解, 深入, 技术债 |
| artistry | 创新, 创意, 实验, 新颖, 探索 |
| quick | 修复, fix, 改, 更新, 简单, 快速 |
| writing | 文档, readme, 说明, 指南, 注释 |
| testing | 测试, test, 单元测试, 集成测试 |
| debugging | 调试, debug, 问题, 错误, bug |

### 文件模式映射

根据文件路径/扩展名自动选择：

| Category | 文件模式 |
|----------|----------|
| visual-engineering | *.tsx, *.jsx, *.vue, *.css, */components/* |
| testing | *.test.ts, *.spec.js, */tests/* |
| writing | *.md, README*, */docs/* |

### 复杂度检测

根据任务复杂度自动调整：

**简单** → quick
- 1个文件，<50行代码
- 关键词：修复、改、简单

**中等** → unspecified-low / 对应领域
- 2-5个文件，<200行代码
- 关键词：实现、添加、创建

**复杂** → unspecified-high / deep
- 6+个文件，>200行代码
- 关键词：重构、迁移、架构

---

## Category + Skill 组合策略

### 策略1：设计师（UI实现）

**组合**：
- Category: `visual-engineering`
- Skills: `frontend-ui-ux`, `playwright`

**效果**：
- 实现美观的 UI
- 自动在浏览器中验证渲染效果

**使用**：
```typescript
task({
  category: "visual-engineering",
  load_skills: ["frontend-ui-ux", "playwright"],
  prompt: "创建一个响应式的仪表盘页面"
});
```

### 策略2：架构师（设计审查）

**组合**：
- Category: `ultrabrain`
- Skills: [] (纯推理)

**效果**：
- 深度架构分析
- 长期可维护性评估

**使用**：
```typescript
task({
  category: "ultrabrain",
  load_skills: [],
  prompt: "评估当前系统架构的可扩展性"
});
```

### 策略3：维护者（快速修复）

**组合**：
- Category: `quick`
- Skills: `git-master`

**效果**：
- 快速修复代码
- 自动生成规范提交

**使用**：
```typescript
task({
  category: "quick",
  load_skills: ["git-master"],
  prompt: "修复用户名验证逻辑"
});
```

### 策略4：测试专家

**组合**：
- Category: `testing`
- Skills: `tdd-workflow`

**效果**：
- 编写全面测试
- 遵循TDD最佳实践

**使用**：
```typescript
task({
  category: "testing",
  load_skills: ["tdd-workflow"],
  prompt: "为订单服务编写单元测试"
});
```

---

## 自定义 Category

### 创建自定义 Category

在 `.opencode/config/categories.json` 中添加：

```json
{
  "custom_categories": {
    "data-engineering": {
      "description": "数据处理、ETL、数据分析",
      "model": "glm-5",
      "temperature": 0.2,
      "prompt_append": "你是一位数据工程师。专注于数据管道设计、ETL流程和数据分析。",
      "use_cases": [
        "数据管道设计",
        "ETL开发",
        "数据分析",
        "报表生成"
      ]
    }
  }
}
```

### 使用自定义 Category

```typescript
task({
  category: "data-engineering",
  prompt: "设计用户行为分析的数据管道"
});
```

---

## 模型 Fallback 机制

### Fallback 链

每个 Category 都有 fallback 链，当主模型不可用时自动切换：

```json
{
  "model_fallback": {
    "visual-engineering": [
      "gemini-2.0-flash-exp",
      "glm-5",
      "glm-4-flash"
    ],
    "ultrabrain": [
      "glm-5",
      "gemini-2.0-flash-exp",
      "glm-4-flash"
    ]
  }
}
```

### Fallback 触发条件

1. **API 错误**：429、503、529 等
2. **密钥错误**：API key 缺失或无效
3. **超时**：响应超时
4. **主动重试**：`timeout_seconds > 0`

---

## 最佳实践

### 1. 明确任务意图

❌ **不好**：
```
ulw 修复这个
```

✅ **好**：
```
ulw 修复 LoginButton 组件的样式问题
```

### 2. 让系统自动选择

❌ **不好**：
```
使用 glm-5 来设计架构
```

✅ **好**：
```
设计系统架构  # 自动选择 ultrabrain
```

### 3. 组合 Skill 增强

```typescript
// 基础 Category
task({ category: "visual-engineering", prompt: "..." });

// Category + Skill 组合
task({
  category: "visual-engineering",
  load_skills: ["frontend-ui-ux"],
  prompt: "..."
});
```

### 4. 根据复杂度选择

**简单任务**：
```typescript
task({ category: "quick", prompt: "修复拼写错误" });
```

**复杂任务**：
```typescript
task({
  category: "deep",
  prompt: "重构认证系统为微服务架构"
});
```

---

## 实际案例

### 案例1：前端开发

**任务**：创建响应式登录表单

**自动检测**：
- 关键词：表单 → visual-engineering
- 文件：Login.tsx → visual-engineering

**执行**：
```typescript
task({
  category: "visual-engineering",
  load_skills: ["frontend-ui-ux"],
  prompt: "创建一个响应式的登录表单，支持邮箱和密码登录"
});
```

**结果**：
- 使用 Gemini 2.0 Flash Exp
- 温度 0.7
- 加载 frontend-ui-ux skill
- 生成美观的响应式表单

### 案例2：架构设计

**任务**：设计微服务架构

**自动检测**：
- 关键词：架构、设计 → ultrabrain
- 复杂度：高 → ultrabrain

**执行**：
```typescript
task({
  category: "ultrabrain",
  prompt: "设计支持百万级用户的微服务架构，包括认证、订单、支付服务"
});
```

**结果**：
- 使用 GLM-5
- 温度 0.1
- 启用深度思考（16k tokens）
- 生成详细架构设计

### 案例3：快速修复

**任务**：修复拼写错误

**自动检测**：
- 关键词：修复 → quick
- 复杂度：简单 → quick

**执行**：
```typescript
task({
  category: "quick",
  load_skills: ["git-master"],
  prompt: "修复 LoginButton.tsx 第 15 行的拼写错误"
});
```

**结果**：
- 使用 GLM-4 Flash
- 温度 0.3
- 快速修复
- 自动生成 Git 提交

---

## 调试与日志

### 查看 Category 选择日志

```bash
cat .quickagents/logs/category-selection.log
```

### 日志格式

```
[2026-03-25 15:30:00] [INFO] Category 自动检测
[2026-03-25 15:30:00] [INFO] 关键词匹配：架构 → ultrabrain
[2026-03-25 15:30:00] [INFO] 文件模式匹配：*.ts → 无
[2026-03-25 15:30:00] [INFO] 复杂度检测：高 → ultrabrain
[2026-03-25 15:30:00] [INFO] 最终选择：ultrabrain
[2026-03-25 15:30:00] [INFO] 模型：glm-5
[2026-03-25 15:30:00] [INFO] 温度：0.1
```

---

## 配置参考

### 完整配置示例

```json
{
  "categories": {
    "my-category": {
      "description": "类别描述",
      "model": "模型ID",
      "temperature": 0.5,
      "prompt_append": "额外提示词",
      "reasoning_effort": "medium",
      "thinking": {
        "type": "enabled",
        "budget_tokens": 8000
      },
      "use_cases": ["用例1", "用例2"]
    }
  },
  
  "mapping_rules": {
    "keywords": {
      "my-category": ["关键词1", "关键词2"]
    },
    "file_patterns": {
      "my-category": ["*.ext", "*/path/*"]
    }
  },
  
  "model_fallback": {
    "my-category": ["model1", "model2", "model3"]
  }
}
```

---

## 常见问题

### Q1: 如何知道选择了哪个 Category？

**A**: 查看日志：
```bash
cat .quickagents/logs/category-selection.log
```

### Q2: Category 和 Agent 有什么区别？

**A**:
- **Category**: 语义化任务分类 + 模型配置
- **Agent**: 完整的代理配置（包括工具权限、行为模式等）
- **关系**: Category 用于 task 委托，Agent 用于 @提及

### Q3: 可以同时使用多个 Category 吗？

**A**: 不可以。每个任务只能使用一个 Category。如果任务包含多个领域，选择最核心的一个。

### Q4: 如何禁用自动检测？

**A**: 显式指定 Category：
```typescript
task({
  category: "ultrabrain",  // 显式指定
  prompt: "..."
});
```

---

## 相关文档

- [UltraWork 命令](../commands/ultrawork.md)
- [Orchestrator Agent](../agents/orchestrator.md)
- [Oh-My-OpenAgent Category System](../../reference/oh-my-openagent-features.md)

---

*基于 Oh-My-OpenAgent Category System*
*适配 QuickAgents 智能判断系统*
*版本: v1.0.0*
*创建时间: 2026-03-25*
