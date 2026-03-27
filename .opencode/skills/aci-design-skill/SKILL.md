# ACI Design Skill

> **来源**: SWE-agent 论文 - Agent-Computer Interface 设计原则
> **优先级**: P2 - 中期可实施
> **版本**: v1.0 | **创建日期**: 2026-03-27

---

## 概述

ACI (Agent-Computer Interface) 设计技能，基于 SWE-agent 论文的四大设计原则，优化 AI 代理与计算机系统的交互接口，提升操作效率和可靠性。

---

## 四大设计原则

### 1. 简化命令空间 (Simplified Command Space)

**核心理念**: 统一、明确、无歧义的命令体系

```yaml
命令规范:
  前缀统一:
    - /add-skill    # 添加技能
    - /list-skills  # 列出技能
    - /remove-skill # 移除技能
    - /update-skill # 更新技能
  
  命名规则:
    - 每个操作有且只有一个命令
    - 命令名称语义明确
    - 使用 kebab-case 格式
    - 避免缩写，使用完整单词

  参数规范:
    - 必填参数在前，可选参数在后
    - 使用 --flag 表示布尔选项
    - 使用 --flag=value 表示值选项
```

**实施检查清单**:

- [ ] 所有命令使用统一前缀
- [ ] 命令名称无歧义
- [ ] 每个功能只有一个入口命令
- [ ] 参数顺序符合直觉
- [ ] 提供命令补全提示

### 2. 严格格式化输出 (Strict Output Formatting)

**核心理念**: 类型化、结构化、可解析的输出格式

```yaml
输出类型前缀:
  FILE:     "文件内容输出"
  DIR:      "目录列表输出"
  ERROR:    "错误信息输出"
  INFO:     "一般信息输出"
  SUCCESS:  "成功确认输出"
  WARNING:  "警告提示输出"
  DATA:     "数据结构输出"

格式规范:
  行格式: "[TYPE] content"
  示例:
    - "[FILE] src/index.ts:42: export function main()"
    - "[DIR] src/components/"
    - "[ERROR] File not found: config.yaml"
    - "[INFO] Processing 5 files..."
    - "[SUCCESS] Build completed in 2.3s"
```

**输出模板**:

```
# 文件读取输出
[FILE] {filepath}:{line_number}: {content}

# 目录列表输出
[DIR] {path}/
  ├── {item1}
  ├── {item2}
  └── {item3}

# 错误输出
[ERROR] {error_type}: {message}
  Context: {context}
  Suggestion: {actionable_suggestion}

# 操作结果输出
[SUCCESS] {operation} completed
  Duration: {time}s
  Affected: {count} items
```

### 3. 增强反馈机制 (Enhanced Feedback Mechanism)

**核心理念**: 精确、有上下文、可操作的错误反馈

```yaml
错误反馈三要素:
  1. 精确原因:
     - 明确指出错误类型
     - 定位具体位置
     - 解释为什么失败

  2. 相关上下文:
     - 显示错误周围的代码/配置
     - 列出相关依赖
     - 提供环境信息

  3. 可操作建议:
     - 具体的修复步骤
     - 替代方案
     - 参考文档链接

反馈模板:
  "[ERROR] {operation} failed"
  "  Reason: {precise_reason}"
  "  Location: {file}:{line}"
  "  Context: {surrounding_context}"
  "  Suggestion: {actionable_fix}"
  "  Reference: {doc_link}"
```

**错误类型分类**:

| 错误类型 | 前缀 | 示例 |
|---------|------|------|
| 文件错误 | FILE_ERROR | 文件不存在/权限不足 |
| 语法错误 | SYNTAX_ERROR | 解析失败/格式错误 |
| 依赖错误 | DEPENDENCY_ERROR | 缺少依赖/版本冲突 |
| 网络错误 | NETWORK_ERROR | 连接失败/超时 |
| 验证错误 | VALIDATION_ERROR | 输入不合法 |
| 系统错误 | SYSTEM_ERROR | 资源不足/权限问题 |

### 4. 文件操作优化 (Optimized File Operations)

**核心理念**: 窗口化、精确引用、高效编辑

```yaml
文件读取优化:
  窗口化显示:
    - 默认显示上下文窗口（前后各5行）
    - 支持指定行范围
    - 长文件自动截断提示

  行号引用:
    - 所有输出包含行号
    - 格式: "filepath:line_number"
    - 支持范围引用: "filepath:10-20"

  精确范围编辑:
    - 基于行号的精确编辑
    - 支持多行块替换
    - 保留原有缩进

文件编辑规范:
  读取模式:
    - 小文件（<100行）: 完整读取
    - 中文件（100-1000行）: 窗口化读取
    - 大文件（>1000行）: 按需加载

  编辑模式:
    - 精确定位: 使用行号定位
    - 最小变更: 只修改必要内容
    - 验证确认: 编辑前预览变更
```

**文件操作模板**:

```yaml
# 读取文件（窗口化）
[FILE] {filepath}:{start}-{end}
  {line_1}
  {line_2}
  ...
  [TRUNCATED] {total_lines} lines total, showing {shown_lines}

# 编辑文件（精确范围）
[EDIT] {filepath}:{start}-{end}
  - {old_content}
  + {new_content}
  [CONFIRM] Apply this change? (y/n)

# 搜索结果（格式化）
[SEARCH] Pattern: "{pattern}" in {scope}
  {filepath}:{line}: {matched_content}
  Found {count} matches in {files} files
```

---

## 核心常量

```python
# 文件操作常量
FILE_WINDOW_SIZE = 10          # 上下文窗口大小
MAX_FILE_DISPLAY = 2000        # 最大显示行数
LARGE_FILE_THRESHOLD = 1000    # 大文件阈值

# 输出格式常量
MAX_LINE_LENGTH = 120          # 最大行宽
TRUNCATE_SUFFIX = "..."        # 截断后缀
INDENT_SIZE = 2                # 缩进大小

# 错误反馈常量
MAX_CONTEXT_LINES = 5          # 错误上下文行数
MAX_SUGGESTION_LENGTH = 200    # 建议最大长度
```

---

## 使用指南

### 1. 命令设计检查

当设计新命令时，使用以下检查清单：

```markdown
## 命令设计检查清单

- [ ] 命令是否使用统一前缀？
- [ ] 命令名称是否语义明确？
- [ ] 是否有其他命令提供相同功能？
- [ ] 参数顺序是否符合直觉？
- [ ] 是否提供了帮助信息？
- [ ] 是否支持命令补全？
```

### 2. 输出格式检查

当输出信息时，使用以下模板：

```markdown
## 输出格式检查清单

- [ ] 是否使用了类型前缀？
- [ ] 每行是否只有一个信息单元？
- [ ] 格式是否固定且可解析？
- [ ] 是否包含必要的上下文？
- [ ] 是否有明确的结束标记？
```

### 3. 错误反馈检查

当报告错误时，确保包含：

```markdown
## 错误反馈检查清单

- [ ] 是否指出了精确原因？
- [ ] 是否定位了具体位置？
- [ ] 是否提供了相关上下文？
- [ ] 是否给出了可操作建议？
- [ ] 是否提供了参考链接？
```

### 4. 文件操作检查

当操作文件时，遵循以下规范：

```markdown
## 文件操作检查清单

- [ ] 是否使用了窗口化显示？
- [ ] 是否包含行号引用？
- [ ] 是否使用精确范围编辑？
- [ ] 是否保留了原有缩进？
- [ ] 是否进行了编辑预览？
```

---

## 集成示例

### 示例1: 读取文件

```
# 输入
/read src/services/user.ts 42

# 输出
[FILE] src/services/user.ts:37-47
  37: /**
  38:  * 用户服务
  39:  */
  40: export class UserService {
  41:   private repository: IUserRepository;
  42: 
  43:   constructor(repository: IUserRepository) {
  44:     this.repository = repository;
  45:   }
  46: 
  47:   async findById(id: string): Promise<User | null> {

[INFO] Showing lines 37-47 of 150 total
```

### 示例2: 编辑文件

```
# 输入
/edit src/services/user.ts:44 "  constructor(repo: IUserRepository) {"

# 输出
[EDIT] src/services/user.ts:43-45
  - constructor(repository: IUserRepository) {
  + constructor(repo: IUserRepository) {
  [CONFIRM] Apply this change? (y/n)
```

### 示例3: 错误反馈

```
# 错误示例
[ERROR] FILE_ERROR: File not found
  Location: config/database.yaml:1
  Context: Loading database configuration
  Suggestion: Run 'npm run init-config' to create default config
  Reference: https://docs.example.com/config#database
```

### 示例4: 搜索结果

```
# 输入
/search "UserService" src/

# 输出
[SEARCH] Pattern: "UserService" in src/
  src/services/user.ts:40: export class UserService {
  src/services/user.ts:60: const userService = new UserService(repo);
  src/controllers/user.ts:15: import { UserService } from '../services/user';
  Found 3 matches in 2 files
```

---

## 与其他Skills的集成

### 与 lazy-discovery-skill 集成

- 命令描述按需加载
- 工具文档延迟加载

### 与 event-reminder-skill 集成

- 格式化提醒消息
- 结构化日志输出

### 与 doom-loop-skill 集成

- 检测到循环时输出结构化警告
- 提供可操作的解决方案

---

## 参考资料

- **SWE-agent 论文**: github.com/SWE-agent/SWE-agent
- **ACI 设计原则**: SWE-agent 论文 Section 3
- **OpenDev 论文**: arXiv:2603.05344v2

---

*创建日期: 2026-03-27*
*版本: v1.0*
