# UltraWork Command

> 超高效工作命令 - "Just do it" 模式
> 触发词：`ulw` 或 `ultrawork`

---

## 命令概述

**UltraWork** 是一个强大的工作模式，当你想"直接干，不要废话"时使用。

**核心特点**：
- 🚀 **最大性能**：并行执行、后台任务、自动探索
- 🧠 **智能判断**：自动识别任务复杂度并选择策略
- 🔍 **自动探索**：无需提供详细上下文，agent 会自己研究
- ⚡ **快速迭代**：边做边学，快速调整

---

## 使用方式

### 方式1：关键词触发

直接在消息中使用 `ulw` 或 `ultrawork`：

```
ulw 实现用户登录功能
ulw 修复这个测试失败
ulw 重构认证模块
```

### 方式2：命令调用

```bash
/ulw 实现用户登录功能
/ultrawork 修复这个测试失败
```

---

## 智能模式选择

UltraWork 会根据任务复杂度自动选择策略：

### 简单任务（Simple）
**特征**：单文件修改、简单修复、快速调整

**行为**：
- 直接执行
- 不创建计划
- 快速完成

**示例**：
```
ulw 修复这个拼写错误
ulw 添加缺失的分号
ulw 重命名这个变量
```

### 中等任务（Medium）
**特征**：多文件修改、需要探索、有依赖关系

**行为**：
- 快速探索代码库
- 识别相关文件
- 串行执行
- 简单验证

**示例**：
```
ulw 实现用户登录功能
ulw 添加输入验证
ulw 重构这个组件
```

### 复杂任务（Complex）
**特征**：架构级变更、多模块协调、需要深度思考

**行为**：
- 深度探索代码库
- 并行后台任务
- 系统化执行
- 完整验证

**示例**：
```
ulw 重构认证系统
ulw 迁移到新数据库
ulw 实现微服务架构
```

---

## 执行流程

### 标准流程

```
┌─────────────────────────────────────────────────┐
│          UltraWork 执行流程                       │
├─────────────────────────────────────────────────┤
│                                                  │
│  1. 任务分析                                      │
│     ├─ 识别任务类型（简单/中等/复杂）             │
│     ├─ 提取关键信息                               │
│     └─ 选择执行策略                               │
│                                                  │
│  2. 代码库探索（自动）                            │
│     ├─ 搜索相关文件                               │
│     ├─ 识别现有模式                               │
│     └─ 理解依赖关系                               │
│                                                  │
│  3. 并行执行（可选）                              │
│     ├─ 启动后台探索任务                           │
│     ├─ 继续主要工作                               │
│     └─ 整合后台结果                               │
│                                                  │
│  4. 迭代执行                                      │
│     ├─ 执行任务                                   │
│     ├─ 验证结果                                   │
│     ├─ 调整策略                                   │
│     └─ 继续下一步                                 │
│                                                  │
│  5. 完成验证                                      │
│     ├─ 运行测试                                   │
│     ├─ 代码检查                                   │
│     ├─ 更新文档                                   │
│     └─ Git 提交                                   │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## 后台任务支持

### 自动后台探索

对于复杂任务，UltraWork 会自动启动后台探索：

```typescript
// 示例：启动后台探索
task(
  subagent_type="explore",
  run_in_background=true,
  prompt="查找所有认证相关代码"
)

// 主线程继续工作
// 后台结果就绪时自动整合
```

### 并发控制

**默认并发数**：3个后台任务
**可配置**：在 `config/ultrawork.json` 中调整

```json
{
  "max_background_tasks": 3,
  "timeout_seconds": 300,
  "auto_explore": true
}
```

---

## Category 自动映射

UltraWork 会自动将任务映射到合适的 Category：

| 任务类型 | Category | 说明 |
|---------|----------|------|
| UI/前端 | `visual-engineering` | 使用 Gemini 3.1 Pro |
| 架构设计 | `ultrabrain` | 使用 GPT-5.4 深度推理 |
| 快速修复 | `quick` | 使用 GPT-5.4 Mini |
| 深度重构 | `deep` | 使用 GPT-5.3 Codex |
| 文档编写 | `writing` | 使用 Gemini 3 Flash |

**自动识别规则**：
```python
def detect_category(task_description):
    if "UI" in task or "前端" in task:
        return "visual-engineering"
    elif "架构" in task or "设计" in task:
        return "ultrabrain"
    elif "修复" in task or "改" in task:
        return "quick"
    elif "重构" in task or "迁移" in task:
        return "deep"
    else:
        return "unspecified-high"
```

---

## 与其他工具的集成

### 与 Orchestrator 集成

如果存在 Prometheus 计划：
```bash
# 使用现有计划
ulw 继续
ulw 继续
```

如果没有计划：
```bash
# 自动探索并执行
ulw 实现用户认证
```

### 与 Todo Enforcer 集成

UltraWork 模式下，Todo Enforcer 仍然生效：
- 自动创建 Todo
- 强制完成所有项
- 不会中途停止

### 与 Skills 集成

自动加载相关 Skills：
```bash
# 自动加载 git-master skill
ulw 提交这些更改

# 自动加载 frontend-ui-ux skill
ulw 优化登录页面UI
```

---

## 配置选项

### 基础配置

创建 `.opencode/config/ultrawork.json`：

```json
{
  "enabled": true,
  "max_background_tasks": 3,
  "auto_explore": true,
  "timeout_seconds": 300,
  "fallback_on_error": true,
  
  "category_mapping": {
    "ui": "visual-engineering",
    "frontend": "visual-engineering",
    "architecture": "ultrabrain",
    "design": "ultrabrain",
    "fix": "quick",
    "quick": "quick",
    "refactor": "deep",
    "migrate": "deep",
    "docs": "writing"
  },
  
  "complexity_detection": {
    "simple": {
      "file_count": 1,
      "keywords": ["修复", "fix", "改", "rename"]
    },
    "medium": {
      "file_count": 5,
      "keywords": ["实现", "implement", "添加", "add"]
    },
    "complex": {
      "file_count": 10,
      "keywords": ["重构", "refactor", "迁移", "migrate", "架构", "architecture"]
    }
  }
}
```

---

## 使用示例

### 示例1：简单任务

**输入**：
```
ulw 修复 LoginButton.tsx 中的拼写错误
```

**执行**：
1. 识别为简单任务
2. 直接读取文件
3. 修复错误
4. 保存文件
5. 完成

**输出**：
```
✅ 已修复 LoginButton.tsx 中的拼写错误
   - 第 15 行："Sucess" → "Success"
```

### 示例2：中等任务

**输入**：
```
ulw 实现用户登录功能
```

**执行**：
1. 识别为中等任务
2. 探索代码库（查找相关文件）
3. 识别现有模式
4. 创建 Todo
5. 实现登录逻辑
6. 添加测试
7. 验证
8. Git 提交

**输出**：
```
✅ 用户登录功能已完成

已创建：
- src/services/auth.ts
- src/components/LoginForm.tsx
- tests/auth.test.ts

测试结果：5/5 通过
Git 提交：feat(auth): 实现用户登录功能
```

### 示例3：复杂任务

**输入**：
```
ulw 重构认证系统为 JWT
```

**执行**：
1. 识别为复杂任务
2. 启动后台探索（查找所有认证相关代码）
3. 深度分析现有架构
4. 设计新架构
5. 并行实现多个模块
6. 系统化测试
7. 迁移数据
8. 更新文档
9. Git 提交

**输出**：
```
✅ 认证系统重构为 JWT 完成

后台探索任务：
- 查找认证代码：找到 23 个文件
- 识别依赖关系：完成
- 分析现有模式：完成

架构变更：
- Session → JWT
- 新增 Token 刷新机制
- 添加权限中间件

已修改文件：
- src/middleware/auth.ts
- src/services/auth.ts
- src/controllers/auth.ts
- ... (共 15 个文件)

测试结果：23/23 通过
文档已更新
Git 提交：refactor(auth): 重构为 JWT 认证
```

---

## 最佳实践

### 1. 清晰的任务描述

❌ **不好**：
```
ulw 修复这个
```

✅ **好**：
```
ulw 修复 LoginButton.tsx 中的点击事件未触发问题
```

### 2. 合理的期望

**UltraWork 适合**：
- 明确目标的任务
- 需要探索的任务
- 快速迭代

**UltraWork 不适合**：
- 需要用户频繁决策的任务
- 完全未定义的需求
- 需要多人协作的任务

### 3. 利用自动探索

```
# 让 agent 自己探索
ulw 优化这个模块的性能

# 不要过度提供上下文
# ❌ ulw 在 src/services/user.ts 第 50-100 行添加缓存，使用 Redis，注意并发...
# ✅ ulw 为用户服务添加缓存
```

---

## 调试与日志

### 查看执行日志

```bash
# 查看最近的 UltraWork 执行记录
cat .quickagents/logs/ultrawork.log
```

### 日志格式

```
[2026-03-25 15:30:00] [INFO] UltraWork 启动
[2026-03-25 15:30:01] [INFO] 任务类型：复杂
[2026-03-25 15:30:02] [INFO] 后台任务：启动 explore agent
[2026-03-25 15:30:05] [INFO] 探索完成：找到 23 个文件
[2026-03-25 15:30:10] [INFO] 执行中：重构认证模块
[2026-03-25 15:35:00] [INFO] 完成：测试通过 23/23
```

---

## 故障排除

### 问题1：任务卡住

**原因**：可能是探索时间过长或遇到错误

**解决**：
```bash
# 查看日志
cat .quickagents/logs/ultrawork.log

# 或停止当前任务
/stop-continuation
```

### 问题2：结果不符合预期

**原因**：任务描述不够清晰

**解决**：
```bash
# 提供更详细的描述
ulw 实现用户登录功能，使用 JWT，支持记住我
```

### 问题3：后台任务失败

**原因**：资源限制或超时

**解决**：
```json
// 调整配置
{
  "max_background_tasks": 2,
  "timeout_seconds": 600
}
```

---

## 与 /ulw-loop 的区别

| 特性 | ulw | /ulw-loop |
|------|-----|-----------|
| 执行次数 | 单次 | 循环执行直到完成 |
| 适用场景 | 单个任务 | 大型项目 |
| 自动继续 | 否 | 是 |
| 检测完成 | 否 | 检测 `<promise>DONE</promise>` |

**使用建议**：
- 单个任务：使用 `ulw`
- 大型项目：使用 `/ulw-loop`

---

## 相关命令

- `/ulw-loop` - UltraWork 循环模式
- `/start-work` - 从计划开始执行
- `/stop-continuation` - 停止所有继续机制
- `/handoff` - 生成跨会话交接文档

---

## 高级用法

### 组合使用

```bash
# 先规划再执行
@fenghou-plan 规划用户认证系统
/start-work auth-plan

# 或者直接 UltraWork
ulw 实现用户认证系统
```

### 与特定 Agent 协作

```bash
# 指定使用特定 agent
@oracle ulw 审查这段代码
@librarian ulw 查找这个功能的实现示例
```

---

*基于 Oh-My-OpenAgent UltraWork 模式*
*适配 QuickAgents 智能判断系统*
*版本: v1.0.0*
*创建时间: 2026-03-25*
