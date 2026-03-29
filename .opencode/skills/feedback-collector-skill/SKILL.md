---
name: feedback-collector-skill
description: |
  收集QuickAgents使用过程中的经验、改进方向、最佳实践。
  自动触发：任务完成、Git提交后分析。
  手动触发：/feedback <类型> <描述>
  
  Architecture (v2.3.0+):
  - SQLite主存储: unified.db/feedback表
  - 与SkillEvolution集成: 自动收集Skills使用经验
  - Markdown辅助备份: ~/.quickagents/feedback/*.md
license: MIT
allowed-tools:
  - read
  - write
  - edit
  - bash
metadata:
  category: feedback
  priority: medium
  version: 2.3.0
  localized: true
---

# Feedback Collector Skill

收集QuickAgents使用经验，为系统升级提供指导。

## 架构 (v2.3.0+)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    经验收集与自我进化架构                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   AI代理 ──► .quickagents/unified.db ◄── 主存储 (SQLite)           │
│              │         feedback表                                   │
│              │         skill_evolution表                            │
│              │                                                      │
│              ▼ (SkillEvolution自动收集)                             │
│       on_task_complete() ──► 自动记录Skills使用                    │
│       on_git_commit() ──► 自动分析提交内容                         │
│       check_periodic_trigger() ──► 定期优化检查                    │
│              │                                                      │
│              ▼ (自动同步)                                           │
│       ~/.quickagents/feedback/ ◄── Markdown备份                    │
│       ~/.quickagents/evolution/ ◄── Skills进化记录                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Python API (推荐)

```python
from quickagents import UnifiedDB, SkillEvolution, FeedbackType, MarkdownSync

db = UnifiedDB('.quickagents/unified.db')
evolution = SkillEvolution(db)

# 方式1: 使用SkillEvolution自动收集（推荐）
result = evolution.on_task_complete({
    'task_id': 'T001',
    'task_name': '实现认证',
    'skills_used': ['tdd-workflow-skill', 'git-commit-skill'],
    'success': True,
    'duration_ms': 45000
})

# 方式2: 手动添加反馈
db.add_feedback(
    FeedbackType.BUG,
    'lazy-discovery未正确加载',
    description='grep工具未加载',
    project_name='my-project'
)

# 方式3: Git提交自动分析
evolution.on_git_commit()

# 方式4: 定期优化
if evolution.check_periodic_trigger():
    result = evolution.run_periodic_optimization()

# 查询反馈
bugs = db.get_feedbacks(FeedbackType.BUG, limit=10)

# 同步到Markdown
sync = MarkdownSync(db)
sync.sync_feedback()
```

## 存储位置

```
~/.quickagents/feedback/
├── bugs.md           # Bug/错误
├── improvements.md   # 改进建议
├── best-practices.md # 最佳实践
├── skill-review.md   # Skill评估
└── agent-review.md   # Agent评估
```

## 经验类型

| 类型 | 文件 | 命令 |
|------|------|------|
| Bug/错误 | bugs.md | `/feedback bug` |
| 改进建议 | improvements.md | `/feedback improve` |
| 最佳实践 | best-practices.md | `/feedback best` |
| Skill评估 | skill-review.md | `/feedback skill` |
| Agent评估 | agent-review.md | `/feedback agent` |

---

## 触发机制

### 自动触发

1. **任务完成时** - 分析本次任务，提取经验
2. **Git提交后** - 分析变更，记录改进点

### 手动触发

```bash
/feedback bug <问题描述>
/feedback improve <改进建议>
/feedback best <最佳实践描述>
/feedback skill <skill名> <评价>
/feedback agent <agent名> <评价>
/feedback view [类型]     # 查看收集的经验
```

---

## 文件格式

每条记录采用简单格式：

```markdown
## YYYY-MM-DD HH:mm - <项目名>

**描述**: <核心内容>

**场景**: <触发场景/上下文>

**建议**: <可选的改进建议>

---
```

---

## 自动收集流程

### 任务完成触发

```
任务完成
    ↓
分析任务上下文
    ↓
提取经验点：
  - 遇到的问题 → bugs.md
  - 可优化的地方 → improvements.md
  - 有效的方法 → best-practices.md
  - Skill使用效果 → skill-review.md
  - Agent协作效果 → agent-review.md
    ↓
写入对应文件
```

### Git提交触发

```
Git提交完成
    ↓
分析提交内容
    ↓
提取改进点
    ↓
写入 improvements.md
```

---

## 去重逻辑

同一小时内，相同类型+相似描述的经验只保留一条（AI判断相似度）。

```
判断流程：
1. 提取新经验的描述关键词
2. 查找同类型文件中最近1小时的记录
3. AI判断描述是否相似（语义相似度 > 0.7）
4. 相似则跳过，不相似则新增
```

---

## 查看命令

```bash
/feedback view          # 查看所有类型统计
/feedback view bugs     # 查看Bug列表
/feedback view improve  # 查看改进建议
/feedback view best     # 查看最佳实践
/feedback view skill    # 查看Skill评估
/feedback view agent    # 查看Agent评估
```

---

## 初始化

首次使用时，自动创建目录和文件：

```bash
~/.quickagents/feedback/
├── bugs.md           # 初始为空，只有标题
├── improvements.md
├── best-practices.md
├── skill-review.md
└── agent-review.md
```

---

## 使用示例

### 手动记录Bug

```
用户: /feedback bug lazy-discovery-skill未正确加载grep工具

AI: 已记录到 ~/.quickagents/feedback/bugs.md
    项目: my-project
    时间: 2026-03-28 10:30
```

### 任务完成后自动收集

```
AI完成任务后:
1. 分析: 本次任务使用了 lazy-discovery-skill
2. 发现: 工具加载延迟约2秒，可优化
3. 记录: improvements.md - "lazy-discovery-skill加载延迟可优化"
```

---

## 与其他Skill集成

| Skill | 集成方式 |
|-------|----------|
| event-reminder-skill | 添加任务完成/Git提交触发点 |
| project-memory-skill | 可参考全局反馈到项目记忆 |

---

## 注意事项

1. **隐私保护**: 所有数据存储在用户本地，不上传
2. **存储管理**: 用户可手动删除旧记录
3. **格式一致**: 保持简单格式，便于阅读和搜索

---

*版本: 1.0.0 | 创建时间: 2026-03-28*
