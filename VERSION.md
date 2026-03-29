# QuickAgents Version

> 版本信息文件 - 用于版本检测和更新

---

## 当前版本

| 属性 | 值 |
|------|-----|
| 版本号 | 2.1.1 |
| Git标签 | v2.1.1 |
| 发布日期 | 2026-03-29 |
| 最低兼容版本 | 2.0.0 |
| 仓库地址 | https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM |
| PyPI包 | https://pypi.org/project/quickagents/ |

---

## 安装方式

```bash
# 从PyPI安装
pip install quickagents

# 使用CLI
qa --help
qa stats
qa cache stats
```

---

## 本次更新 (v2.1.1)

**新增功能**:
- `feedback-collector-skill` - 经验收集系统
- `quickagents` Python包 - 本地化Skills，Token节省90%+
  - FileManager: 哈希检测文件读写
  - CacheDB: SQLite缓存系统
  - MemoryManager: 三维记忆管理
  - LoopDetector: 循环检测
  - Reminder: 事件提醒
  - FeedbackCollector: 经验收集
  - TDDWorkflow: TDD工作流
  - GitCommit: Git提交管理

**更新内容**:
- Skills本地化: 8个Skills完全本地化
- 移除npm包，统一使用PyPI
- AGENTS.md 新增「二四、本地化Python包」章节

---

## 远程版本检测URL

```
https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/VERSION.md
```

---

## 更新命令

```bash
/qa-update              # 检测并更新
/qa-update --check      # 仅检测，不更新
/qa-update --version    # 显示当前版本
```

---

*最后更新: 2026-03-28*
