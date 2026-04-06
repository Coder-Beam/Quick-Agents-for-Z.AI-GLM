# 任务管理 (TASKS.md)

> 更新时间: 2026-04-06
> 版本: v2.9.0 → v2.10.0 产品化改造
> 产品化方案: Docs/enhancement-analysis/quickagents-productization-plan.md

---

## 统计概览

| 指标 | 数值 |
|------|------|
| 总任务数 | 19 |
| 已完成 | 0 |
| 进行中 | 0 |
| 待开始 | 19 |
| 阻塞中 | 0 |
| 完成率 | 0.0% |

---

## 决策记录 (已确认)

| # | 决策 | 结果 |
|---|------|------|
| D1 | 概念存根Skills处理方式 | **A: 删除** (18个SKILL.md已删除,未提交) |
| D2 | 版本号 | **A: v2.10.0** 渐进式 |
| D3 | report_generator输出格式 | **B: Markdown+JSON** 双格式 |
| D4 | CLI默认LLM Provider | **A: ZhipuAI** |
| D5 | 是否提交YuGong到git | **A: 先提交** |

---

## 当前迭代 — Phase 0: 提交清理 + 状态恢复

### P0 - 紧急 (立即执行)

| 任务ID | 任务名称 | 优先级 | 状态 | 说明 |
|--------|----------|--------|------|------|
| T001 | 提交上一会话未提交的变更 | P0 | 待开始 | 18个SKILL.md删除 + report_generator.py + yugong/__init__.py + Docs同步 |
| T002 | 清理残留的空Skills目录 | P0 | 待开始 | 删除SKILL.md后留下的空目录 |

---

## Phase 1: CRITICAL修复 + CLI集成 (Week 1)

### P0 - CRITICAL Bug修复

| 任务ID | 任务名称 | 优先级 | 状态 | 说明 |
|--------|----------|--------|------|------|
| T003 | 修复C2: autonomous_loop.py agent_fn=None假成功 | P0 | 待开始 | 将success=True改为False并输出明确错误信息 |
| T004 | 修复C1: CLI qka yugong start接入真实Agent | P0 | 待开始 | 替换[WARN]为真实AgentExecutor调用链 |
| T005 | 修复C3: AgentExecutor连接到CLI默认配置 | P0 | 待开始 | LLMConfig.from_env(provider="zhipuai") → 默认链路 |

### P1 - CLI增强

| 任务ID | 任务名称 | 优先级 | 状态 | 说明 |
|--------|----------|--------|------|------|
| T006 | 新增CLI子命令 qka yugong report | P1 | 待开始 | 从YuGongDB生成报告(D3:双格式) |
| T007 | 新增CLI子命令 qka yugong resume | P1 | 待开始 | 从DB恢复状态继续循环 |
| T008 | 新增CLI子命令 qka yugong config | P1 | 待开始 | 初始化/查看配置 |
| T009 | 修复test_phase5_integration.py的8个import失败 | P1 | 待开始 | 导入路径问题 |

---

## Phase 2: Skills产品化 + 目录治理 (Week 2)

### P1 - Skills治理

| 任务ID | 任务名称 | 优先级 | 状态 | 说明 |
|--------|----------|--------|------|------|
| T010 | 更新registry.json对齐实际Skills | P1 | 待开始 | 当前7个→需对齐到实际保留的9个 |
| T011 | 清理EVOLUTION.md | P1 | 待开始 | 移除已删除Skills的记录 |
| T012 | 清理Skills空目录(验证) | P1 | 待开始 | 确保所有已删除Skills目录完全清理 |

### P2 - 新建可执行Python模块

| 任务ID | 任务名称 | 优先级 | 状态 | 说明 |
|--------|----------|--------|------|------|
| T013 | 新建 project_detector.py | P2 | 待开始 | 本地项目类型检测(文件模式匹配,0 Token) |
| T014 | 新建 category_router.py | P2 | 待开始 | 任务分类→模型路由(关键词匹配,0 Token) |
| T015 | 新建 model_router.py | P2 | 待开始 | 多模型路由+fallback |

---

## Phase 3: 质量保障 + 发布准备 (Week 3)

### P2 - 质量修复

| 任务ID | 任务名称 | 优先级 | 状态 | 说明 |
|--------|----------|--------|------|------|
| T016 | 修复MEDIUM问题(静默异常) | P2 | 待开始 | safety_guard.py, cli/main.py等处的静默吞异常 |
| T017 | 修复AGENTS.md中EdgeType.TRACES_TO引用 | P2 | 待开始 | 该枚举值不存在 |

### P1 - 发布准备

| 任务ID | 任务名称 | 优先级 | 状态 | 说明 |
|--------|----------|--------|------|------|
| T018 | 版本更新 v2.10.0 | P1 | 待开始 | pyproject.toml, VERSION.md, __init__.py |
| T019 | 文档更新 + CHANGELOG + README | P1 | 待开始 | 发布文档，记录所有变更 |

---

## 已完成任务

> (暂无 — Phase 1-4 已完成的工作属于前期版本迭代，见 Git 提交历史)

---

## 里程碑

| 里程碑 | 目标 | 截止日期 | 状态 |
|--------|------|----------|------|
| M0 | 提交清理 + 状态恢复 | 2026-04-06 | 待开始 |
| M1 | Phase 1完成: CRITICAL修复 + CLI集成 | 2026-04-09 | 待开始 |
| M2 | Phase 2完成: Skills治理 + 新模块 | 2026-04-13 | 待开始 |
| M3 | Phase 3完成: 质量保障 + v2.10.0发布 | 2026-04-16 | 待开始 |

---

## 关键文件索引

### 需要修改的文件

| 文件 | 任务 | 说明 |
|------|------|------|
| `quickagents/yugong/autonomous_loop.py` | T003 | 修复C2逻辑bug |
| `quickagents/cli/main.py` | T004, T005, T006, T007, T008 | CLI命令修复与增强 |
| `quickagents/yugong/report_generator.py` | T006 | 已创建,CLI集成时使用 |
| `quickagents/yugong/__init__.py` | T003 | 已更新导出ReportGenerator |
| `tests/yugong/test_phase5_integration.py` | T009 | 修复import失败 |
| `.opencode/skills/registry.json` | T010 | 更新Skills注册表 |
| `.opencode/skills/EVOLUTION.md` | T011 | 清理进化记录 |
| `AGENTS.md` | T017 | 修正EdgeType引用 |

### 方案文档

| 文档 | 说明 |
|------|------|
| `Docs/enhancement-analysis/quickagents-productization-plan.md` | 产品化方案 v1.0 (完整) |
| `Docs/enhancement-analysis/yugong-loop-design.md` | YuGong技术设计文档 (70KB) |
| `Docs/enhancement-analysis/IMPLEMENTATION_PLAN.md` | 实施计划 |

---

*最后更新: 2026-04-06 | 基于 v2.9.0 产品化改造方案*
