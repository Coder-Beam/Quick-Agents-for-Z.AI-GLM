---
name: lsp-ast-skill
description: |
  LSP and AST-Grep integration skill for intelligent diagnostics,
  code pattern search, and automated refactoring.
license: MIT
allowed-tools:
  - read
  - write
  - edit
  - bash
dependencies:
  - code-review-skill
metadata:
  category: development
  priority: medium
  version: 1.0.0
---

# LSP + AST-Grep Skill

## 概述

LSP（Language Server Protocol）和AST-Grep集成技能，提供智能代码诊断、模式搜索和自动化重构能力。

## 核心能力

### 1. LSP诊断

利用LSP获取实时代码诊断：

```typescript
// 获取诊断信息
interface Diagnostic {
  file: string;
  line: number;
  column: number;
  severity: 'error' | 'warning' | 'info';
  message: string;
  source: string;
  code?: string;
}

// 支持的语言
- TypeScript/JavaScript
- Python
- Go
- Rust
- Java
- C#
```

### 2. AST模式搜索

使用AST-Grep进行代码模式搜索：

```bash
# 搜索console.log
ast-grep --pattern 'console.log($MSG)' --lang typescript

# 搜索特定函数调用
ast-grep --pattern 'fetch($URL)' --lang javascript

# 搜索React组件
ast-grep --pattern 'function $COMP() { $$ }' --lang typescript
```

### 3. AST重写

使用AST-Grep进行代码重写：

```bash
# 替换console.log为logger
ast-grep --pattern 'console.log($MSG)' \
         --rewrite 'logger.info($MSG)' \
         --lang typescript

# var转const
ast-grep --pattern 'var $VAR = $VALUE' \
         --rewrite 'const $VAR = $VALUE' \
         --lang javascript
```

### 4. LSP重构

利用LSP进行智能重构：

```typescript
// 重命名符号
lsp_rename(file: string, line: number, newName: string)

// 查找引用
lsp_find_references(file: string, line: number)

// 跳转定义
lsp_goto_definition(file: string, line: number)

// 获取类型信息
lsp_hover(file: string, line: number)
```

## 使用方式

### LSP诊断

```markdown
<!-- 获取文件诊断 -->
@lsp 诊断 src/auth/auth.service.ts

<!-- 获取项目所有诊断 -->
@lsp 诊断所有文件

<!-- 按严重程度过滤 -->
@lsp 只显示错误
@lsp 显示警告和错误
```

### AST搜索

```markdown
<!-- 搜索模式 -->
@ast 搜索 "console.log($MSG)"

<!-- 搜索并显示上下文 -->
@ast 搜索 "fetch($URL)" --context 3

<!-- 按语言搜索 -->
@ast 搜索 "def $FUNC($ARGS):" --lang python
```

### AST重写

```markdown
<!-- 预览重写 -->
@ast 重写预览 "var $VAR = $VAL" → "const $VAR = $VAL"

<!-- 执行重写 -->
@ast 重写 "console.log($MSG)" → "logger.info($MSG)"

<!-- 批量重写 -->
@ast 批量重写 --rules .quickagents/ast-rules/
```

### LSP重构

```markdown
<!-- 重命名 -->
@lsp 重命名 getUserById → fetchUserById

<!-- 查找引用 -->
@lsp 引用 formatDate

<!-- 跳转定义 -->
@lsp 定义 UserService
```

## 工作流程

### 诊断流程

```
1. 检测文件类型
2. 启动对应LSP服务器
3. 获取诊断信息
4. 过滤和排序
5. 生成诊断报告
```

### 搜索流程

```
1. 解析搜索模式
2. 检测目标语言
3. 构建AST模式
4. 遍历代码文件
5. 匹配和报告
```

### 重构流程

```
1. 解析重写规则
2. 预览变更
3. 用户确认
4. 执行重写
5. LSP验证
6. 运行测试
```

## 配置说明

### LSP服务器配置

在 `.opencode/config/lsp-config.json` 中配置：

```json
{
  "servers": {
    "typescript": {
      "command": "typescript-language-server",
      "args": ["--stdio"],
      "file_patterns": ["**/*.ts", "**/*.tsx"],
      "enabled": true
    }
  }
}
```

### AST规则配置

```json
{
  "ast_grep": {
    "rules_dir": ".quickagents/ast-rules",
    "default_rules": {
      "no-console-log": {
        "language": "typescript",
        "pattern": "console.log($MSG)",
        "message": "Avoid console.log",
        "severity": "warning"
      }
    }
  }
}
```

### 自定义规则

在 `.quickagents/ast-rules/` 目录下创建规则文件：

```yaml
# no-any-type.yaml
id: no-any-type
language: typescript
pattern: ": any"
message: "Avoid using 'any' type. Use a specific type instead."
severity: warning
note: |
  Using 'any' defeats TypeScript's type checking.
  Consider using 'unknown' or a specific type.
```

## 与其他Skill集成

### 与Code Review集成

```markdown
code-review-skill自动使用LSP诊断和AST模式检测
```

### 与Refactor集成

```markdown
refactor代理使用LSP重命名和AST重写进行重构
```

### 与Test Runner集成

```markdown
test-runner使用AST检测测试文件和测试用例
```

## 命令参考

### LSP命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `@lsp 诊断` | 获取文件诊断 | `@lsp 诊断 src/index.ts` |
| `@lsp 重命名` | 重命名符号 | `@lsp 重命名 oldName → newName` |
| `@lsp 引用` | 查找引用 | `@lsp 引用 formatDate` |
| `@lsp 定义` | 跳转定义 | `@lsp 定义 UserService` |
| `@lsp 类型` | 获取类型信息 | `@lsp 类型 line:45` |

### AST命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `@ast 搜索` | 搜索模式 | `@ast 搜索 "console.log($MSG)"` |
| `@ast 重写` | 执行重写 | `@ast 重写 "var → const"` |
| `@ast 预览` | 预览变更 | `@ast 预览 "old → new"` |
| `@ast 规则` | 应用规则 | `@ast 规则 no-console-log` |
| `@ast 语言` | 列出支持语言 | `@ast 语言` |

## 输出格式

### 诊断报告

```markdown
# LSP诊断报告

## 文件: src/auth/auth.service.ts

### 错误 (2)
1. Line 45, Col 12: Cannot find name 'userPassword'
2. Line 78, Col 5: Type 'string' is not assignable to type 'number'

### 警告 (3)
1. Line 23, Col 10: 'password' is declared but never used
2. Line 56, Col 8: Missing return type on function
3. Line 89, Col 1: Unused import 'bcrypt'

### 信息 (1)
1. Line 12, Col 5: Variable 'config' is declared but never used

## 统计
- 总问题数: 6
- 错误: 2
- 警告: 3
- 信息: 1
```

### 搜索结果

```markdown
# AST搜索结果

## 模式: console.log($MSG)
## 语言: typescript
## 匹配数: 5

### src/utils/logger.ts:12
```typescript
console.log('Debug info:', data)
```

### src/services/user.ts:45
```typescript
console.log('User created:', user.id)
```

### src/controllers/auth.ts:78
```typescript
console.log('Auth attempt:', email)
```
```

### 重写预览

```markdown
# AST重写预览

## 规则: var → const
## 影响文件: 3
## 变更数: 7

### src/index.ts
```diff
- var config = require('./config')
+ const config = require('./config')

- var port = 3000
+ const port = 3000
```

### src/utils/helper.ts
```diff
- var helper = {
+ const helper = {
```

## 是否执行此重写? (y/n)
```

## 最佳实践

### 1. LSP使用

- 定期检查诊断
- 优先修复错误
- 关注警告信息
- 利用自动修复

### 2. AST搜索

- 使用具体模式
- 限制搜索范围
- 结合文件类型过滤
- 保存常用模式

### 3. AST重写

- 先预览后执行
- 小批量操作
- 执行后运行测试
- 提交前检查

### 4. 性能优化

- 限制文件大小
- 使用缓存
- 并行处理
- 增量更新

## 故障排查

### 问题1：LSP服务器无法启动

**可能原因**:
- 语言服务器未安装
- 配置路径错误
- 端口冲突

**解决方案**:
```bash
# 安装语言服务器
npm install -g typescript-language-server

# 检查配置
cat .opencode/config/lsp-config.json
```

### 问题2：AST搜索无结果

**可能原因**:
- 模式语法错误
- 语言不匹配
- 文件被排除

**解决方案**:
```bash
# 测试模式
ast-grep --pattern 'console.log($MSG)' --lang typescript test.ts

# 检查语言
ast-grep --lang list
```

### 问题3：重写导致错误

**可能原因**:
- 重写规则不正确
- 上下文考虑不足
- 类型不匹配

**解决方案**:
- 使用预览模式
- 小范围测试
- 运行类型检查
- 运行测试

## 扩展指南

### 添加新语言支持

1. 安装对应语言服务器
2. 在lsp-config.json中添加配置
3. 测试连接
4. 在ast_grep.languages中添加语言

### 创建自定义规则

1. 在.quickagents/ast-rules/创建YAML文件
2. 定义id、pattern、message
3. 测试规则
4. 添加到配置

### 集成到CI/CD

```yaml
# .github/workflows/lint.yml
- name: AST Check
  run: |
    ast-grep --config .quickagents/ast-rules/ --json > ast-report.json
    if [ $(jq 'length' ast-report.json) -gt 0 ]; then
      echo "AST violations found"
      exit 1
    fi
```

---

*版本: 1.0.0 | 创建时间: 2026-03-25*
