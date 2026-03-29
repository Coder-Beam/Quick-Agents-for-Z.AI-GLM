# QuickAgents Version

> 版本信息文件 - 用于版本检测和更新

---

## 当前版本

| 属性 | 值 |
|------|-----|
| 版本号 | 2.3.0 |
| Git标签 | v2.3.0 |
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
qa evolution status
qa hooks install
```

---

## 本次更新 (v2.3.0)

**重大更新 - 统一自我进化系统**

### 新增功能

#### SkillEvolution - 统一的Skills自我进化系统

自动触发、统一存储、经验闭环：

| 触发类型 | 触发条件 | 自动操作 |
|----------|----------|----------|
| TASK_COMPLETE | 任务完成 | 记录Skills使用、分析失败原因 |
| GIT_COMMIT | Git提交 | 分析提交内容、检测改进点 |
| PERIODIC | 10任务/7天 | 执行Skills优化、更新统计 |
| ERROR_DETECTED | 错误检测 | 记录错误、建议修复方案 |

#### GitHooks - Git钩子集成

```bash
qa hooks install    # 安装钩子
qa hooks status     # 查看状态
```

#### 新增CLI命令

```bash
qa evolution status      # 进化系统状态
qa evolution stats [skill] # Skills使用统计
qa evolution optimize    # 执行定期优化
qa evolution history <skill> # 查看进化历史
qa hooks install         # 安装Git钩子
```

### 架构改进

- **统一存储**: 所有进化数据存入UnifiedDB
- **Python API**: 0 Token消耗，本地处理
- **自动闭环**: 收集 -> 分析 -> 改进 -> 验证

### Skills本地化状态 (90%)

| Skill | 状态 | 模块 |
|-------|------|------|
| skill-evolution | ✅ 100% | SkillEvolution (新增) |
| git-hooks | ✅ 100% | GitHooks (新增) |
| doom-loop-skill | ✅ 100% | LoopDetector |
| project-memory-skill | ✅ 100% | MemoryManager + CacheDB |
| feedback-collector-skill | ✅ 100% | FeedbackCollector |
| tdd-workflow-skill | ✅ 100% | TDDWorkflow |
| git-commit-skill | ✅ 100% | GitCommit |

### 删除的内容

- `skills/self-improving-agent/hooks/openclaw/handler.ts` - TypeScript Hook已删除
- 项目现在100% Python化

---

## 历史版本

### v2.2.0 (2026-03-29)
- UnifiedDB统一存储架构
- SQLite主存储 + Markdown辅助备份
- Token节省60%+

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
