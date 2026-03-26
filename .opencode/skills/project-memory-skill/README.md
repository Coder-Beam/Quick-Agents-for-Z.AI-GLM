# Project Memory Skill

## 概述

Project Memory Skill 是一个用于管理项目三维记忆系统的技能，基于论文《Memory in the Age of AI Agents》设计。

## 核心能力

### 1. 记忆管理

- **Factual Memory（事实记忆）**：管理项目静态事实信息
- **Experiential Memory（经验记忆）**：管理项目动态经验信息
- **Working Memory（工作记忆）**：管理当前活跃工作状态

### 2. 记忆操作

- **Formation（形成）**：在关键节点自动记录记忆
- **Retrieval（检索）**：智能检索相关记忆
- **Evolution（演化）**：整合和更新记忆

## 使用场景

### 场景1：项目初始化

当用户执行「启动AGENTS.MD」时，自动创建项目级MEMORY.md文件。

### 场景2：任务完成

当任务完成时，自动更新Working Memory和Experiential Memory。

### 场景3：跨会话衔接

在新会话开始时，读取MEMORY.md恢复上下文。

## 文件结构

```
project-memory-skill/
├── README.md           # 本文件
└── references/
    └── memory-template.md  # 记忆文件模板
```

## 记忆格式

### YAML Front Matter

```yaml
---
memory_type: project | feature | module
created_at: 2026-03-22T10:00:00Z
updated_at: 2026-03-22T15:30:00Z
version: 1.0.0
tags: [tag1, tag2, tag3]
related_files: [file1.md, file2.md]
---
```

### 记忆分类

| 类型 | 内容 | 更新时机 |
|------|------|----------|
| Factual | 项目元信息、技术决策、业务规则、约束条件 | 项目初始化、决策确认 |
| Experiential | 操作历史、经验总结、用户反馈、迭代记录 | 任务完成、变更发生 |
| Working | 当前状态、活跃上下文、临时变量、待决策项 | 实时更新 |

## 触发规则

### 自动触发

1. **Git提交时**：自动记录本次提交的关键信息
2. **任务完成时**：自动更新Working Memory状态
3. **决策确认时**：自动记录到Factual Memory

### 手动触发

用户可以通过以下方式手动触发：
- 「记录记忆：[内容]」
- 「更新记忆：[类型] [内容]」

## 检索规则

### 智能检索

AI根据当前上下文自动检索相关记忆：
1. 关键词匹配
2. 标签匹配
3. 时间范围过滤
4. 相关度排序

### 检索命令

- 「检索记忆：[关键词]」
- 「查看历史：[时间范围]」
- 「获取上下文」

## 注意事项

1. **永不删除**：所有记忆永久保留
2. **智能整合**：定期整合重复/过期记忆
3. **同步更新**：跨层级变更需同步更新

---

*版本: 1.0.0 | 创建时间: 2026-03-22*
