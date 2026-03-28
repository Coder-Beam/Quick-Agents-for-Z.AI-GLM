# Feedback Collector Skill 设计文档

> **版本**: v1.0.0  
> **创建日期**: 2026-03-28  
> **状态**: 简化设计

---

## 一、核心目标

在使用QuickAgents的过程中，自动收集经验到本地全局目录，为QuickAgents升级提供指导。

---

## 二、存储结构

```
~/.quickagents/feedback/
├── bugs.md           # Bug/错误
├── improvements.md   # 改进建议
├── best-practices.md # 最佳实践
├── skill-review.md   # Skill评估
└── agent-review.md   # Agent评估
```

---

## 三、文件格式

每个文件采用简单格式：

```markdown
# [类型] 收集

---

## 2026-03-28 10:30 - my-project

**描述**: 懒加载工具未正确加载grep工具

**场景**: 代码审查任务中，grep工具未被自动加载

**建议**: 优化lazy-discovery-skill的工具分类逻辑

---

## 2026-03-28 14:20 - my-project

**描述**: ...

**场景**: ...

**建议**: ...

---
```

---

## 四、触发机制

| 触发点 | 说明 |
|--------|------|
| 任务完成 | 分析本次任务，记录有价值的经验 |
| Git提交 | 分析本次提交，记录改进点 |
| 手动触发 | `/feedback <类型> <描述>` |

**去重逻辑**：同一小时内，相同类型+相似描述的经验只保留一条（AI判断相似度）。

---

## 五、命令

| 命令 | 功能 |
|------|------|
| `/feedback bug <描述>` | 记录Bug |
| `/feedback improve <描述>` | 记录改进建议 |
| `/feedback best <描述>` | 记录最佳实践 |
| `/feedback skill <skill名> <评价>` | 评估Skill |
| `/feedback agent <agent名> <评价>` | 评估Agent |
| `/feedback view [类型]` | 查看收集的经验 |

---

## 六、收集内容

AI在触发时自动提取：

1. **Bug**: 问题描述 + 复现场景 + 影响范围
2. **改进建议**: 现状 + 期望 + 建议
3. **最佳实践**: 场景 + 做法 + 效果
4. **Skill评估**: Skill名 + 使用效果 + 改进点
5. **Agent评估**: Agent名 + 协作效果 + 改进点

---

## 七、与QuickAgents集成

1. 创建 `feedback-collector-skill`
2. 在 `event-reminder-skill` 中添加触发点
3. 在 `AGENTS.md` 中添加简单说明

---

## 八、实现步骤

1. 创建 skill 目录和 SKILL.md
2. 实现触发检测
3. 实现简单写入逻辑
4. 实现手动命令

---

*简化版设计 | 2026-03-28*
