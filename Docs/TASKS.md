# 任务管理 (TASKS.md)

> 更新时间: 2026-04-05

---

## 统计概览

| 指标 | 数值 |
|------|------|
| 总任务数 | 9 |
| 已完成 | 9 |
| 进行中 | 0 |
| 阻塞中 | 0 |
| 完成率 | 100.0% |

---

## 当前迭代

**迭代目标**: 修复经验收集系统三大断点，使 SkillEvolution 系统真正产出有效经验

**关联决策**: D001 - 经验收集系统三大断点修复方案

| 任务ID | 任务名称 | 优先级 | 状态 | 文件 |
|--------|----------|--------|------|------|
| T001 | get_connection() 自动提交 | P0 | ✅ 已完成 | connection_manager.py |
| T002 | Skills层触发适配器 | P0 | ✅ 已完成 | skills/_evolution_trigger.py |
| T003 | GitCommit 接入触发 | P0 | ✅ 已完成 | skills/git_commit.py |
| T004 | TDDWorkflow 接入触发 | P0 | ✅ 已完成 | skills/tdd_workflow.py |
| T005 | _analyze_commit() 扩展 | P1 | ✅ 已完成 | core/evolution.py |
| T006 | _suggest_fix() 增强 | P1 | ✅ 已完成 | core/evolution.py |
| T007 | 经验数据模型 + _extract_patterns() 增强 | P1 | ✅ 已完成 | core/evolution.py |
| T008 | Hook脚本增强 files_changed | P2 | ✅ 已完成 | core/git_hooks.py |
| T009 | 全量验证 | P0 | ✅ 已完成 | - |

## 当前迭代

**迭代目标**: 修复经验收集系统三大断点，使 SkillEvolution 系统真正产出有效经验

**关联决策**: D001 - 经验收集系统三大断点修复方案

| 任务ID | 任务名称 | 优先级 | 状态 | 文件 | 依赖 |
|--------|----------|--------|------|------|------|
| T001 | get_connection() 自动提交 | P0 | 待开始 | connection_manager.py | 无 |
| T002 | Skills层触发适配器 | P0 | 待开始 | 新增 skills/_evolution_trigger.py | 无 |
| T003 | GitCommit 接入触发 | P0 | 待开始 | skills/git_commit.py | T002 |
| T004 | TDDWorkflow 接入触发 | P0 | 待开始 | skills/tdd_workflow.py | T002 |
| T005 | _analyze_commit() 扩展 | P1 | 待开始 | core/evolution.py | T001 |
| T006 | _suggest_fix() 增强 | P1 | 待开始 | core/evolution.py | T001 |
| T007 | 经验数据模型 + _extract_patterns() 增强 | P1 | 待开始 | core/evolution.py | T001 |
| T008 | Hook脚本增强 files_changed | P2 | 待开始 | core/git_hooks.py | 无 |
| T009 | 全量验证 + 文档更新 | P0 | 待开始 | - | T001-T008 |

---

## 待办任务

### P0 - 紧急

- [ ] T001: 修改 get_connection() 上下文管理器，正常退出时自动 conn.commit()
- [ ] T002: 新增 skills/_evolution_trigger.py 触发适配器（懒加载+错误隔离）
- [ ] T003: GitCommit.commit() 成功后接入 trigger_git_commit()
- [ ] T004: TDDWorkflow._run_tests() 完成后接入 trigger_task_complete()
- [ ] T009: 全量验证所有修复效果 + 更新文档

### P1 - 高优先级

- [ ] T005: _analyze_commit() 扩展 — 覆盖所有 conventional commit 类型 + files_changed 分析
- [ ] T006: _suggest_fix() 增强 — 项目历史经验检索 + fallback 通用映射
- [ ] T007: 经验数据模型 + _extract_patterns() 增强

### P2 - 中优先级

- [ ] T008: post-commit hook 脚本增强 FILES_CHANGED 采集

---

## 已完成任务

---
