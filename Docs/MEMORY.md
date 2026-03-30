# MEMORY.md

> 更新时间: 2026-03-30 21:00
> 此文件由 SQLite 自动同步生成，作为辅助备份

---

## Factual Memory (事实记忆)

记录项目的静态事实信息

### 项目元信息

- **项目名称**: QuickAgents
- **项目路径**: D:\Projects\QuickAgents
- **技术栈**: Python 3.8+, TypeScript
- **版本**: 2.6.8
- **作者**: Coder-Beam
- **GitHub**: https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM

### 核心模块

- **UnifiedDB**: 统一数据库管理（SQLite主存储）
- **MarkdownSync**: 自动同步到Markdown（辅助备份）
- **FileManager**: 智能文件读写（哈希检测）
- **LoopDetector**: 循环检测
- **Reminder**: 事件提醒
- **SkillEvolution**: Skills自我进化
- **KnowledgeGraph**: 知识图谱
- **Browser**: 浏览器自动化
- **Encoding**: 统一UTF-8编码（跨平台）

### ZhipuAI GLM Coding Plan 集成

- **状态**: 已完成
- **完成时间**: 2026-03-30
- **模型配置**: `.opencode/config/models.json`
- **支持模型**: GLM-5.1, GLM-5, GLM-4.7, GLM-4.7-FlashX, GLM-4.5-Air
- **CLI命令**: `qa models show/list/check-updates/upgrade/strategy/lock/unlock`

### 统一UTF-8编码系统

- **状态**: 已完成
- **完成时间**: 2026-03-30
- **位置**: `quickagents/utils/encoding.py`
- **功能**: 
  - 统一UTF-8编码（无BOM）
  - 跨平台兼容（Windows/macOS/Linux）
  - 支持中文、英文、Emoji、日韩文
  - 自动处理BOM

---

## Experiential Memory (经验记忆)

记录项目的动态经验信息

### 最新进展

- **2026-03-30**: 完成ZhipuAI GLM Coding Plan集成
- **2026-03-30**: 创建统一UTF-8编码系统
- **2026-03-30**: 修复CLI命令bug
- **2026-03-30**: 更新文档（README.md, model-configuration.md）

### 最佳实践

- 使用 `read_file_utf8()` 和 `write_file_utf8()` 进行文件读写
- 使用 `qa models` 命令管理模型配置
- Coding Plan用户优先使用GLM-5

---

## Working Memory (工作记忆)



