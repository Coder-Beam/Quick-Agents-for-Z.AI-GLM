---
name: lazy-discovery-skill
description: 工具懒加载系统 - 按需加载工具描述，减少初始上下文负担
version: 1.0.0
created_at: 2026-03-27
source: OpenDev论文 (arXiv:2603.05344v2)
---

# Lazy Discovery Skill - 工具懒加载系统

## 核心理念

来自OpenDev论文：**懒加载工具发现** 可减少初始上下文负担50%+。

```
传统方式:
启动时 → 加载所有工具描述 → 占用大量system prompt

懒加载方式:
启动时 → 加载核心工具 → 按需加载扩展工具 → 动态优化
```

## 工具分类体系

### L1 - 核心工具（始终加载）

这些工具是所有任务的基础，始终在上下文中：

```
CORE_TOOLS = [
    "bash",      # 执行命令
    "read",      # 读取文件
    "write",     # 写入文件
    "edit"       # 编辑文件
]
```

### L2 - 任务类型工具（按需加载）

根据任务类型动态加载：

```yaml
TASK_TYPE_TOOLS:
  code_review:
    - grep        # 内容搜索
    - glob        # 文件匹配
    - skill       # 技能调用
    
  ui_design:
    - skill       # ui-ux-pro-max
    - read
    - write
    
  testing:
    - bash
    - read
    - skill       # tdd-workflow
    
  deployment:
    - bash
    - write
    - edit
    
  documentation:
    - read
    - write
    - edit
    - glob
    
  debugging:
    - bash
    - grep
    - read
    - skill       # systematic-debugging
```

### L3 - 扩展工具（延迟加载）

仅在明确需要时加载：

```yaml
EXTENDED_TOOLS:
  - webfetch          # 网页获取
  - compress          # 上下文压缩
  - task              # 子任务派发
  - question          # 用户询问
```

## 使用方式

### 1. 任务分析阶段

当用户发起请求时，分析任务类型：

```python
def analyze_task_type(user_request: str) -> str:
    """分析任务类型"""
    keywords = {
        "code_review": ["审查", "review", "检查代码", "code quality"],
        "ui_design": ["设计", "UI", "界面", "landing page", "dashboard"],
        "testing": ["测试", "test", "TDD", "unit test"],
        "deployment": ["部署", "deploy", "CI/CD", "发布"],
        "documentation": ["文档", "doc", "README", "说明"],
        "debugging": ["调试", "debug", "修复", "fix", "错误"]
    }
    
    for task_type, words in keywords.items():
        if any(w in user_request for w in words):
            return task_type
    
    return "general"
```

### 2. 工具加载

```python
def get_tools_for_task(task_type: str) -> list:
    """获取任务所需工具"""
    tools = CORE_TOOLS.copy()
    
    if task_type in TASK_TYPE_TOOLS:
        tools.extend(TASK_TYPE_TOOLS[task_type])
    
    return list(set(tools))  # 去重
```

### 3. 动态扩展

```python
def extend_tools(current_tools: list, new_need: str) -> list:
    """动态扩展工具集"""
    if new_need == "web_search" and "webfetch" not in current_tools:
        current_tools.append("webfetch")
        log_tool_discovery("webfetch", reason="user needs web search")
    
    return current_tools
```

## 实施检查清单

- [ ] 启动时只加载CORE_TOOLS
- [ ] 任务分析时识别task_type
- [ ] 根据task_type加载L2工具
- [ ] 记录工具加载日志
- [ ] 支持运行时动态扩展

## Token节省估算

```
全量加载: ~5000 tokens (所有工具描述)
核心加载: ~1500 tokens (4个核心工具)
节省: ~3500 tokens (70%)
```

## 与QuickAgents集成

### yinglong-init.md 集成点

```markdown
## 工具懒加载配置

初始工具集:
- bash, read, write, edit

任务类型映射:
- 代码审查 → +grep, +glob
- UI设计 → +skill(ui-ux-pro-max)
- 测试 → +skill(tdd-workflow)
- 部署 → +bash扩展
```

### AGENTS.md 集成点

```markdown
## 工具使用原则

1. 优先使用已加载工具
2. 需要新工具时明确说明
3. 避免不必要的工具切换
```

## 参考资源

- OpenDev论文: arXiv:2603.05344v2
- 核心概念: Lazy Tool Discovery
- 性能提升: 初始上下文减少50%+
