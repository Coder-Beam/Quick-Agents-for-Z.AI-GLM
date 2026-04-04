# 决策日志 (DECISIONS.md)

> 更新时间: 2026-04-05

---

## 决策索引

| 决策ID | 标题 | 决策时间 | 影响范围 | 状态 |
|--------|------|----------|----------|------|
| D001 | 经验收集系统三大断点修复方案 | 2026-04-05 | evolution/skills/connection_manager | 已确认 |

---

## D001 - 经验收集系统三大断点修复方案

| 属性 | 值 |
|------|-----|
| 决策ID | D001 |
| 决策时间 | 2026-04-05 |
| 决策者 | 用户确认 + AI规划 |
| 影响范围 | 核心架构（进化系统、连接管理、Skills触发层） |
| 关联任务 | T001-T009 |

### 决策背景

QuickAgents v2.8.1 的经验收集系统（SkillEvolution）处于"空转"状态：
- `.quickagents/feedback/` 下 5 个 .md 文件仅文件头，无实际内容
- `unified.db` 中 feedback 仅 1 条、skill_usage/skill_evolution/memory 均 0 条
- 系统设计目标是为AI提供项目经验以减少重复理解成本，但实际未收集到任何有效经验

根因排查发现 3 个层级的断点，经与用户讨论确认修复方案如下。

### 断点 #1: 触发链路断裂

**问题**：`on_task_complete()` 和 `on_error_detected()` 是死代码，无调用者。`on_git_commit()` 仅靠 post-commit bash hook 触发，Windows 下可能失效。

**决策**：层次B + 层次C 组合

1. **层次B — Skills层内部自动触发**
   - 新增 `skills/_evolution_trigger.py` 薄适配层，统一处理懒加载 + 错误隔离
   - `GitCommit.commit()` 成功后自动调用 `trigger_git_commit()`
   - `TDDWorkflow._run_tests()` 完成后自动调用 `trigger_task_complete()`
   - `FeedbackCollector.add_feedback()` 添加后自动调用 `trigger_task_complete()`
   - 所有触发调用失败时静默吞掉异常，不影响主流程

2. **层次C — Windows Hook兼容**
   - 增强 post-commit hook 脚本，新增 `FILES_CHANGED` 采集
   - 直接覆盖安装，不考虑向后兼容旧hook

3. **循环依赖风险评估**：确认无循环依赖
   - `skills/ → _evolution_trigger → get_evolution → UnifiedDB → repositories`
   - 链路中没有回到 skills 的依赖
   - `get_evolution()` 内部自动创建数据库和表（CREATE TABLE IF NOT EXISTS，幂等安全）

### 断点 #2: conn.commit() 缺失

**问题**：`evolution.py` 中所有 12 处 `_get_connection()` 写操作均缺少 `conn.commit()`，数据写入后未持久化。

**决策**：选项B — 修改 `get_connection()` 为自动提交

- 在 `connection_manager.py` 的 `get_connection()` 上下文管理器中，正常退出时自动 `conn.commit()`
- 异常时保持 `conn.rollback()`

**副作用排查结论**（风险为零）：

| 检查项 | 结果 |
|--------|------|
| Repository层是否自己有 conn.commit()？ | 有（如 feedback_repo.py:189），重复commit是空操作 |
| 是否存在跨 with 块事务？ | 不存在，每个 with 块都是独立操作 |
| 只读操作（SELECT）commit 是否有开销？ | SQLite 无写操作时 commit 是空操作 |
| migration_manager 是否用同一个连接？ | 是，DDL自带隐式commit |

**不提供"不自动提交"选项**：YAGNI原则，当前不存在跨语句事务场景，真需要时再加。

### 断点 #3: 分析逻辑过于浅薄

**问题**：`_analyze_commit()` 仅检测 refactor/perf 两个关键词；`_extract_patterns()` 条件苛刻；`_suggest_fix()` 是6条静态映射。

**决策**：全面增强

1. **`_analyze_commit()` 扩展**
   - 覆盖所有 conventional commit 类型：feat/fix/docs/style/refactor/perf/test/chore
   - 新增 `files_changed` 分析维度：模块热点、文件关联、配置变更、新增文件、测试覆盖

2. **`_suggest_fix()` 增强**
   - 不跨项目检索，仅限当前项目
   - 从 feedback 表搜索同类型历史修复记录（category='fix'）
   - 有匹配 → 返回历史解决方案；无匹配 → 返回通用建议（保留现有映射作 fallback）

3. **经验数据模型**
   - metadata 新增字段：`category`（architecture/pitfall/pattern/fix/dependency）、`suggestion`、`avoidance`、`files`
   - 核心目标：让AI更懂项目、少走弯路、降低重复理解成本
   - 围绕"AI需要什么"而非"我们能收集什么"设计字段

4. **经验去重策略**：允许重复写入，检索时取最新一条
   - 理由：同一文件的经验可能随项目演进而变化，保留历史有追溯价值

### 实施计划

| 顺序 | 任务ID | 任务 | 文件 |
|------|--------|------|------|
| 1 | T001 | get_connection() 自动提交 | connection_manager.py |
| 2 | T002 | Skills层触发适配器 | 新增 skills/_evolution_trigger.py |
| 3 | T003 | GitCommit 接入触发 | skills/git_commit.py |
| 4 | T004 | TDDWorkflow 接入触发 | skills/tdd_workflow.py |
| 5 | T005 | _analyze_commit() 扩展 | core/evolution.py |
| 6 | T006 | _suggest_fix() 增强 | core/evolution.py |
| 7 | T007 | 经验数据模型 + _extract_patterns() 增强 | core/evolution.py |
| 8 | T008 | Hook脚本增强 files_changed | core/git_hooks.py |
| 9 | T009 | 全量验证 | - |

### 备选方案（未采纳）

| 方案 | 未采纳理由 |
|------|-----------|
| 断点#1 层次A：CLI层手动触发 | 每个命令需手动添加，容易遗漏，不覆盖Python API调用路径 |
| 断点#1 仅层次C：仅修Hook | 不解决 on_task_complete/on_error_detected 死代码问题 |
| 断点#2 选项A：evolution.py逐个加commit | 遗漏风险高，未来新增代码仍可能忘记commit |
| 断点#2 选项C：混合模式 | 过度设计，当前无跨语句事务需求 |

---

*版本: 1.0.0 | 创建时间: 2026-04-05*
