# 示例命令配置

以下是几个常用命令的示例配置：

## 示例 1: 运行测试命令

### 文件名: test.md

```markdown
---
description: 运行测试套件
template: 运行完整的测试套件，包括单元测试和集成测试
重点关注：
1. 测试覆盖率
2. 失败的测试用例
3. 性能问题

如果测试失败，请：
- 分析失败原因
- 建议修复方案
- 不要直接修改代码，仅提供建议
agent: build
model: anthropic/claude-sonnet-4-5
---
```

### 调用方式

```
/test 运行完整的测试套件
/test 只运行用户相关的测试
```

---

## 示例 2: 代码审查命令

### 文件名: review.md

```markdown
---
description: 代码审查命令
template: 审查指定的代码文件，重点关注：
1. 代码质量和最佳实践
2. 潜在的 Bug 和边界情况
3. 性能影响
4. 安全考虑

提供具体的改进建议，但不要直接修改代码。
agent: build
model: anthropic/claude-sonnet-4-5
---
```

### 调用方式

```
/review src/utils/auth.ts
/review components/Button.vue
```

---

## 示例 3: 构建命令

### 文件名: build.md

```markdown
---
description: 构建项目
template: 执行项目构建流程，包括：
1. 清理之前的构建产物
2. 运行构建命令
3. 检查构建结果
4. 报告任何错误或警告

如果构建失败，请：
- 分析错误原因
- 提供修复建议
- 重点关注依赖问题和配置错误
agent: build
model: anthropic/claude-sonnet-4-5
---
```

### 调用方式

```
/build
/build --production
```

---

## 示例 4: 文档生成命令

### 文件名: docs.md

```markdown
---
description: 生成或更新文档
template: 为指定的代码或功能生成文档，包括：
1. 功能概述
2. API 说明
3. 使用示例
4. 注意事项

确保文档：
- 清晰易懂
- 包含实用的示例
- 遵循项目文档规范
agent: build
model: anthropic/claude-sonnet-4-5
---
```

### 调用方式

```
/docs utils/auth.ts
/docs src/components/UserProfile.vue
```

---

*这些是示例文件，实际使用时请根据项目需求创建自定义命令配置*
