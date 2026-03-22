# Project Memory Skill

## 描述

此技能用于管理项目的三维记忆系统（基于《Memory in the Age of AI Agents》论文设计），支持Factual/Experiential/Working三类记忆的创建、更新、检索和整合。

## 使用时机

在以下场景中主动使用此技能：

1. **项目初始化时**：创建项目级MEMORY.md文件
2. **任务完成时**：更新Working Memory和Experiential Memory
3. **决策确认时**：记录到Factual Memory
4. **Git提交时**：自动记录提交信息到记忆
5. **跨会话开始时**：读取MEMORY.md恢复上下文
6. **用户请求时**：检索或更新记忆

## 记忆类型

### Factual Memory（事实记忆）

记录项目静态事实：
- 项目元信息：名称、路径、技术栈、依赖、目录结构
- 技术决策：架构选型、技术方案、API设计、数据库设计
- 业务规则：业务逻辑、计算规则、验证规则
- 约束条件：技术约束、业务约束、时间约束、资源约束

### Experiential Memory（经验记忆）

记录项目动态经验：
- 操作历史：已完成任务、操作记录、变更历史
- 经验总结：踩坑记录、最佳实践、教训总结
- 用户反馈：用户意见、需求调整、验收反馈
- 迭代记录：版本迭代、功能演进、问题修复

### Working Memory（工作记忆）

记录当前活跃状态：
- 当前状态：当前任务、进度百分比、阻塞点
- 活跃上下文：相关文件、依赖关系、前置条件
- 临时变量：待处理事项、临时决策、缓存数据
- 待决策项：需要用户确认的问题、待选方案

## 记忆文件格式

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

## 操作指令

### 创建记忆

当需要创建新的记忆文件时：
1. 确定记忆层级（project/feature/module）
2. 使用标准模板创建MEMORY.md
3. 填充YAML Front Matter元数据
4. 初始化三类记忆结构

### 更新记忆

当需要更新记忆时：
1. 识别更新类型（Factual/Experiential/Working）
2. 追加新记忆内容
3. 更新updated_at时间戳
4. 添加相关标签

### 检索记忆

当需要检索记忆时：
1. 根据关键词匹配
2. 根据标签过滤
3. 根据时间范围筛选
4. 按相关度排序返回

### 整合记忆

定期执行记忆整合：
1. 识别重复记忆
2. 合并相似内容
3. 保留完整历史
4. 永不删除任何记忆

## 注意事项

1. **永不删除**：所有记忆永久保留，仅做整合
2. **实时更新**：Working Memory需要实时更新
3. **跨层级同步**：功能/模块级变更需同步更新项目级记忆
4. **Git提交触发**：每次Git提交后自动记录

## 相关文件

- `Docs/MEMORY.md` - 项目级记忆文件
- `Docs/features/{name}/MEMORY.md` - 功能级记忆文件
- `Docs/modules/{name}/MEMORY.md` - 模块级记忆文件
