# QuickAgents Version

> 版本信息文件 - 用于版本检测和更新

---

## 当前版本

| 属性 | 值 |
|------|-----|
| 版本号 | 2.2.0 |
| Git标签 | v2.2.0 |
| 发布日期 | 2026-03-29 |
| 最低兼容版本 | 2.0.0 |
| 仓库地址 | https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM |
| PyPI包 | https://pypi.org/project/quickagents/ |

---

## 安装方式

```bash
# 从PyPI安装
pip install quickagents

# 完整安装（包含Windows功能）
pip install quickagents[full]

# 使用CLI
qa --help
qa stats
qa cache stats
```

---

## 本次更新 (v2.2.0)

**重大更新 - Skills本地化 + Python包发布**

### 新增功能

#### quickagents Python包
完整的Python本地化包，Token节省90%+：

| 模块 | 功能 | Token节省 |
|------|------|-----------|
| FileManager | 智能文件读写（哈希检测） | 90%+ |
| CacheDB | SQLite缓存管理 | 100% |
| MemoryManager | 三维记忆管理 | 100% |
| LoopDetector | 循环检测 | 100% |
| Reminder | 事件提醒 | 100% |
| FeedbackCollector | 经验收集 | 100% |
| TDDWorkflow | TDD工作流 | 100% |
| GitCommit | Git提交管理 | 100% |
| ScriptHelper | Windows脚本替代 | 100% |

#### Skills本地化状态 (80%)

| Skill | 状态 | 模块 |
|-------|------|------|
| doom-loop-skill | ✅ 100% | LoopDetector |
| project-memory-skill | ✅ 100% | MemoryManager + CacheDB |
| lazy-discovery-skill | ✅ 100% | 内置工具分类 |
| event-reminder-skill | ✅ 100% | Reminder |
| feedback-collector-skill | ✅ 100% | FeedbackCollector |
| tdd-workflow-skill | ✅ 100% | TDDWorkflow |
| git-commit-skill | ✅ 100% | GitCommit |
| ui-ux-pro-max | ✅ 已有Python | search.py, core.py |
| inquiry-skill | ❌ 难以本地化 | 需要AI对话 |
| si-hybrid-skill | ❌ 难以本地化 | 方法论指导 |

### 变更内容
- **移除npm包**：统一使用PyPI发布
- **新增ScriptHelper**：替代.bat/.ps1/.vbs脚本
- **依赖配置**：psutil>=5.9.0 (核心), pywin32>=305 (Windows)

### 文档更新
- AGENTS.md 新增「二四、本地化Python包 (quickagents)」章节
- 新增 `Docs/guides/TOOL_ERROR_FIX_GUIDE.md` 工具错误修复指南

---

## 历史版本

### v2.1.1 (2026-03-28)
- `feedback-collector-skill` - 经验收集系统
- Skills本地化框架搭建

### v2.1.0 (2026-03-27)
- 基于OpenDev/VeRO/SWE-agent论文的6个新Skills
- 事件驱动提醒机制
- ACI设计原则

### v2.0.0 (2026-03-25)
- 三维记忆系统
- 17个专业代理
- 12个核心技能

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

*最后更新: 2026-03-29*
