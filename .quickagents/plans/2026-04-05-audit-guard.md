# AuditGuard 实施计划

> 生成时间: 2026-04-05
> 规划者: 风后-规划
> 版本: 1.0.0

## 元信息

| 属性 | 值 |
|------|-----|
| 计划ID | audit-guard-v1 |
| 创建时间 | 2026-04-05 |
| 预计工期 | 5 个 Phase |
| 优先级 | P0 |

---

## 1. 背景与目标

### 1.1 项目背景

用户在使用 QuickAgents 进行全自动编程开发时，AI 代理持续产出代码，但缺乏有效的实时监控和质量保障机制。存在以下风险：

- **DarkCode 风险**：AI 产出的代码未被记录、审查，用户不知道写了什么、为什么这么写
- **质量盲区**：代码变更后缺少即时质量验证，问题积累到后期才发现
- **学习断层**：问题修复经验未被系统化收集，同类问题重复出现

### 1.2 业务目标

| 目标 | 指标 | 目标值 |
|------|------|--------|
| 代码可追溯 | 每次文件变更100%记录 | 100% audit log coverage |
| 质量门禁 | 功能完成后自动质量检查 | ruff 0 + mypy 0 + pytest 100% |
| 问责闭环 | 问题→归因→学习→修复→验证 | 每个问题都有完整生命周期 |
| 学习积累 | 修复经验自动记录到记忆系统 | Experiential Memory 覆盖 |

### 1.3 技术目标

| 目标 | 说明 |
|------|------|
| 0 Token 消耗 | 所有审计/测试/问责逻辑本地执行 |
| 可配置 | 用户通过 `audit_config.json` 自定义触发规则和测试命令 |
| 不阻塞 | 质量门禁异步执行，不阻塞 AI 代理开发流程 |
| 可扩展 | 支持自定义检查器和报告器 |

---

## 2. 现状分析

### 2.1 已有基础（可复用）

| 模块 | 位置 | 可复用度 |
|------|------|----------|
| `GitCommit.run_pre_commit_checks()` | `skills/git_commit.py` | 90% — 已有 lint/test/typecheck 逻辑 |
| `TDDWorkflow` | `skills/tdd_workflow.py` | 80% — 已有 RED/GREEN/REFACTOR + coverage |
| `FeedbackCollector` | `skills/feedback_collector.py` | 70% — 已有经验记录 + 去重 |
| `UnifiedDB` | `core/unified_db.py` | 100% — 存储审计日志和问责记录 |
| `MarkdownSync` | `core/markdown_sync.py` | 90% — 同步审计报告到 Markdown |
| `LoopDetector` | `core/loop_detector.py` | 30% — 检测修复循环（问责闭环） |
| `ConnectionManager` | `core/connection_manager.py` | 100% — 数据库连接 |
| `SkillEvolution` | `core/evolution.py` | 80% — 记录修复经验到进化系统 |

### 2.2 缺失能力

| 能力 | 说明 |
|------|------|
| **CodeAudit** | 无实时文件变更追踪和 diff 记录 |
| **QualityGate** | 无功能级全量质量门禁（仅 GitCommit 有基础版） |
| **Accountability** | 无问题归因、问责记录、修复经验闭环 |
| **AuditConfig** | 无配置文件支持用户自定义审计规则 |
| **AuditReport** | 无 Markdown 审计报告生成 |

---

## 3. 实施方案

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AuditGuard Module                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐   │
│  │                    AuditGuard (Facade)                        │   │
│  │  audit_file_change() / run_quality_gate() / run_accountability│   │
│  └──────────────────────────┬────────────────────────────────────┘   │
│                              │                                       │
│  ┌───────────────┬──────────┼──────────┬───────────────┐            │
│  │               │          │          │               │            │
│  ▼               ▼          ▼          ▼               ▼            │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌──────────┐     │
│ │CodeAudit│ │Quality  │ │Account- │ │Audit     │ │Audit     │     │
│ │Tracker  │ │Gate     │ │ability  │ │Config    │ │Reporter  │     │
│ │         │ │         │ │Engine   │ │          │ │          │     │
│ │diff记录 │ │ruff     │ │问题归因 │ │JSON配置  │ │MD报告    │     │
│ │变更追踪 │ │mypy     │ │学习提取 │ │触发规则  │ │统计面板  │     │
│ │会话关联 │ │pytest   │ │修复闭环 │ │自定义cmd │ │趋势分析  │     │
│ └────┬────┘ │coverage │ └────┬────┘ └──────────┘ └──────────┘     │
│      │      └────┬────┘      │                                    │
│      │           │           │                                    │
│      ▼           ▼           ▼                                    │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │                 UnifiedDB (Storage)                        │     │
│  │  audit_log 表 │ audit_issues 表 │ audit_lessons 表          │     │
│  └───────────────────────────────────────────────────────────┘     │
│                              │                                       │
│                              ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │                 Existing Modules (复用)                     │     │
│  │  GitCommit │ TDDWorkflow │ FeedbackCollector │ Evolution   │     │
│  └───────────────────────────────────────────────────────────┘     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 目录结构

```
quickagents/audit/
├── __init__.py              # 公共 API 导出
├── audit_guard.py           # AuditGuard 门面类 (~200 lines)
├── code_audit.py            # CodeAuditTracker — 变更追踪 (~250 lines)
├── quality_gate.py          # QualityGate — 质量门禁 (~300 lines)
├── accountability.py        # AccountabilityEngine — 问责引擎 (~250 lines)
├── audit_config.py          # AuditConfig — 配置管理 (~150 lines)
├── audit_reporter.py        # AuditReporter — 报告生成 (~200 lines)
├── models.py                # 数据模型 (~100 lines)
└── migrations/              # 数据库迁移
    └── 001_audit_tables.sql
```

### 3.3 数据库表设计

```sql
-- 审计日志（反 DarkCode 核心）
CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,           -- 会话ID
    task_id TEXT,                       -- 关联任务ID
    file_path TEXT NOT NULL,            -- 变更文件路径
    change_type TEXT NOT NULL,          -- CREATE / MODIFY / DELETE
    diff_content TEXT,                  -- unified diff
    lines_added INTEGER DEFAULT 0,
    lines_removed INTEGER DEFAULT 0,
    tool_name TEXT,                     -- write / edit
    quality_status TEXT DEFAULT 'PENDING', -- PENDING / PASSED / FAILED
    created_at TEXT NOT NULL
);

-- 问责记录
CREATE TABLE IF NOT EXISTS audit_issues (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    task_id TEXT,
    issue_type TEXT NOT NULL,           -- lint / type / test / perf / regression
    severity TEXT NOT NULL,             -- P0 / P1 / P2
    file_path TEXT,
    check_name TEXT,                    -- ruff / mypy / pytest / coverage
    error_message TEXT NOT NULL,
    root_cause TEXT,                    -- 归因分析
    status TEXT DEFAULT 'OPEN',         -- OPEN / FIXING / RESOLVED / WONTFIX
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    fix_strategy TEXT,                  -- 修复策略
    fix_commit TEXT                     -- 修复提交 hash
);

-- 学习经验
CREATE TABLE IF NOT EXISTS audit_lessons (
    id TEXT PRIMARY KEY,
    issue_id TEXT REFERENCES audit_issues(id),
    lesson_type TEXT NOT NULL,          -- pitfall / pattern / best_practice
    category TEXT,                      -- code-style / type-safety / testing / performance
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    trigger_pattern TEXT,               -- 触发模式（用于未来自动匹配）
    prevention_tip TEXT,                -- 预防建议
    created_at TEXT NOT NULL
);
```

### 3.4 关键决策

| 决策ID | 决策内容 | 理由 |
|--------|----------|------|
| D001 | 使用 UnifiedDB SQLite 而非独立数据库 | 统一存储、统一查询、减少维护成本 |
| D002 | 质量门禁分为原子级（commit 触发）和全量级（task 完成触发） | 匹配用户确认的混合触发模式 |
| D003 | E2E/集成测试仅触发+收集，不负责环境搭建 | 用户预定义命令，降低 QuickAgents 复杂度 |
| D004 | 问责默认仅记录，可配置自动反馈给 AI 代理 | 双模式，用户控制 |
| D005 | 新建 `quickagents/audit/` 模块而非扩展 `skills/` | 独立模块边界清晰，职责分离 |

---

## 4. 任务分解

### Phase 1: 基础设施 + CodeAudit（变更追踪）

预计工时: 6-8h

- [ ] **T101**: 创建 `quickagents/audit/` 模块目录结构
- [ ] **T102**: 实现 `models.py` — 数据模型 (AuditLog, AuditIssue, AuditLesson dataclasses)
- [ ] **T103**: 实现 `audit_config.py` — AuditConfig 配置管理
  - 读取 `audit_config.json`，提供默认配置
  - 配置项: lint_command, typecheck_command, test_command, e2e_command, integration_command
  - 配置项: ignore_patterns, severity_threshold, auto_feedback_enabled
- [ ] **T104**: 添加数据库迁移 — `migrations/001_audit_tables.sql`
  - 在 MigrationManager 中注册迁移
- [ ] **T105**: 实现 `code_audit.py` — CodeAuditTracker
  - `record_change(file_path, change_type, diff, tool_name, session_id, task_id)` → 写入 audit_log
  - `get_changes(session_id, task_id, file_path)` → 查询变更记录
  - `get_session_summary(session_id)` → 会话变更摘要
  - `get_file_history(file_path, limit)` → 文件变更历史
- [ ] **T106**: 实现 `audit_reporter.py` — AuditReporter (基础版)
  - `generate_session_report(session_id)` → Markdown 报告
  - `generate_file_report(file_path)` → 文件审计报告
- [ ] **T107**: 编写 Phase 1 测试
  - test_models, test_audit_config, test_code_audit_tracker, test_audit_reporter
- [ ] **T108**: Phase 1 原子提交

### Phase 2: QualityGate（质量门禁）

预计工时: 4-6h

- [ ] **T201**: 实现 `quality_gate.py` — QualityGate
  - `run_atomic_checks(file_paths)` → ruff + mypy + pytest（仅变更文件）
    - 复用 `GitCommit._run_lint()` / `_run_typecheck()` / `_run_tests()` 逻辑
    - 支持增量检查：仅检查变更的文件
  - `run_full_checks()` → 全量 ruff + mypy + pytest + coverage
  - `run_e2e_checks()` → 执行用户配置的 e2e_command
  - `run_integration_checks()` → 执行用户配置的 integration_command
  - 结果写入 audit_log.quality_status
- [ ] **T202**: QualityGate 结果模型
  - QualityResult dataclass: check_name, passed, output, duration_ms, file_paths
  - GateReport dataclass: all_passed, checks: List[QualityResult], timestamp
- [ ] **T203**: 混合触发集成
  - Git commit 触发 → `run_atomic_checks(staged_files)`
  - Task completion 触发 → `run_full_checks()` + `run_integration_checks()` + `run_e2e_checks()`
- [ ] **T204**: 编写 Phase 2 测试
  - test_quality_gate（mock subprocess）
  - test_trigger_modes（atomic vs full）
- [ ] **T205**: Phase 2 原子提交

### Phase 3: Accountability（问责闭环）

预计工时: 6-8h

- [ ] **T301**: 实现 `accountability.py` — AccountabilityEngine
  - `analyze_failure(gate_report)` → 从 QualityGate 失败结果中提取问题
    - 分类: lint_error / type_error / test_failure / coverage_gap / e2e_failure
    - 归因: 解析错误消息，定位根因文件和行号
    - 分级: P0（测试失败/类型错误）/ P1（lint 错误）/ P2（覆盖率不足）
  - `record_issue(issue)` → 写入 audit_issues 表
  - `resolve_issue(issue_id, fix_strategy, fix_commit)` → 更新状态
  - `extract_lesson(issue)` → 提取学习经验 → 写入 audit_lessons + Experiential Memory
- [ ] **T302**: 问题自动归因
  - ruff 错误 → 解析文件:行号:错误码
  - mypy 错误 → 解析文件:行号:类型不匹配
  - pytest 失败 → 解析 FAILED 文件::test_name + AssertionError
  - coverage 不足 → 解析未覆盖文件列表
- [ ] **T303**: 学习经验提取
  - 提取模式: `trigger_pattern`（错误码/类型签名/函数名）
  - 预防建议: 基于问题类型生成通用预防策略
  - 写入 Experiential Memory: `db.set_memory(key, lesson, MemoryType.EXPERIENTIAL)`
  - 写入 SkillEvolution: `evolution.on_task_complete(task_info)`
- [ ] **T304**: 修复闭环
  - 检测修复: 对比修复前后的 QualityGate 结果
  - 记录修复经验: 将修复策略写入 audit_lessons
  - 循环检测: 如果同一问题反复出现，使用 LoopDetector 检测
- [ ] **T305**: 自动反馈模式（可配置）
  - 当 `auto_feedback_enabled=True` 时：
  - 生成反馈消息: 问题摘要 + 根因 + 建议修复策略
  - 写入 Working Memory: `db.set_memory('audit.feedback', feedback_msg, MemoryType.WORKING)`
  - AI 代理在下次工具调用前读取 Working Memory 获取反馈
- [ ] **T306**: 编写 Phase 3 测试
  - test_accountability_engine
  - test_lesson_extraction
  - test_auto_feedback
- [ ] **T307**: Phase 3 原子提交

### Phase 4: AuditGuard 门面 + CLI 命令

预计工时: 4-6h

- [ ] **T401**: 实现 `audit_guard.py` — AuditGuard 门面类
  - `__init__(project_root, config_path)` → 初始化所有子模块
  - `on_file_change(file_path, change_type, diff, tool_name)` → CodeAudit 追踪
  - `on_git_commit(staged_files)` → 原子 QualityGate
  - `on_task_complete(task_id)` → 全量 QualityGate + Accountability
  - `get_audit_summary()` → 审计摘要
  - `close()` → 资源清理
- [ ] **T402**: 添加 CLI 命令
  - `qka audit status` — 审计系统状态
  - `qka audit run [--type atomic|full|e2e]` — 手动触发审计
  - `qka audit log [--session ID] [--file PATH]` — 查看审计日志
  - `qka audit issues [--status OPEN|RESOLVED]` — 查看问责记录
  - `qka audit lessons [--category CAT]` — 查看学习经验
  - `qka audit report [--format md|json]` — 生成审计报告
  - `qka audit init` — 初始化审计配置文件
- [ ] **T403**: 注册 `__init__.py` 公共 API
  - `from quickagents import AuditGuard, AuditConfig`
- [ ] **T404**: 编写 Phase 4 测试
  - test_audit_guard_facade
  - test_cli_audit_commands
- [ ] **T405**: Phase 4 原子提交

### Phase 5: 集成测试 + 文档 + 发布

预计工时: 4-6h

- [ ] **T501**: 端到端集成测试
  - 模拟完整流程: file_change → git_commit → task_complete → quality_gate → accountability → lesson
  - 验证 Markdown 报告生成
  - 验证 Experiential Memory 写入
- [ ] **T502**: 更新文档
  - README.md 添加 AuditGuard 章节
  - CHANGELOG.md 添加版本条目
  - Docs/API_REFERENCE.md 添加审计 API
  - Docs/DESIGN.md 更新架构图
- [ ] **T503**: 版本升级 + PyPI 发布
  - `pyproject.toml` → 2.9.0
  - `__init__.py` → 2.9.0
  - Git tag → v2.9.0
  - PyPI upload
- [ ] **T504**: Phase 5 原子提交

---

## 5. 风险评估

### 5.1 技术风险

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| 审计日志膨胀（大量文件变更） | 中 | 中 | 添加 TTL 配置 + 定期归档策略 |
| QualityGate 执行耗时影响体验 | 中 | 高 | 异步执行 + 进度条 + 可配置超时 |
| 问责自动归因不准确 | 中 | 中 | 分级告警 + 人工确认机制 |
| 用户未配置测试命令 | 高 | 低 | 自动检测 + 合理默认值 + skip 机制 |
| 与现有 GitCommit/TDDWorkflow 功能重叠 | 低 | 中 | 复用而非重写，明确边界 |

### 5.2 资源风险

| 风险 | 应对措施 |
|------|----------|
| 工时超预期 | 每个 Phase 独立可用，可分批发布 |
| 测试覆盖不足 | 每个 Phase 包含独立测试套件 |

---

## 6. 里程碑

| 里程碑 | 目标 | 预计完成 |
|--------|------|----------|
| M1 | Phase 1 完成: CodeAudit 可追踪文件变更 | Phase 1 结束 |
| M2 | Phase 2 完成: QualityGate 可执行质量检查 | Phase 2 结束 |
| M3 | Phase 3 完成: Accountability 问责闭环可用 | Phase 3 结束 |
| M4 | Phase 4 完成: CLI 命令可用，门面类集成 | Phase 4 结束 |
| M5 | Phase 5 完成: 集成测试通过，v2.9.0 发布 | Phase 5 结束 |

---

## 7. 验收标准

### 7.1 功能验收

- [ ] 每次文件 write/edit 操作自动记录 diff 到 audit_log
- [ ] `qka audit run --type atomic` 在 < 30s 内完成 ruff + mypy + pytest
- [ ] `qka audit run --type full` 执行全量检查 + 覆盖率 + E2E
- [ ] 质量门禁失败时自动创建 audit_issues 记录
- [ ] 修复后自动提取学习经验写入 Experiential Memory
- [ ] `auto_feedback_enabled=True` 时自动反馈写入 Working Memory

### 7.2 质量验收

- [ ] ruff check: 0 errors
- [ ] mypy: 0 errors
- [ ] pytest: 所有新增测试 100% 通过
- [ ] 代码覆盖率 ≥ 80%

### 7.3 集成验收

- [ ] AuditGuard 与 UnifiedDB 无缝集成
- [ ] CLI 命令 `qka audit *` 全部可用
- [ ] Markdown 报告正确生成
- [ ] 不影响现有 GitCommit / TDDWorkflow 功能

---

## 8. 配置文件模板

### audit_config.json（默认）

```json
{
    "version": "1.0.0",
    
    "code_audit": {
        "enabled": true,
        "ignore_patterns": [
            "**/.git/**",
            "**/__pycache__/**",
            "**/node_modules/**",
            "**/.quickagents/**"
        ],
        "max_diff_lines": 500,
        "track_tool_calls": ["write", "edit"]
    },
    
    "quality_gate": {
        "enabled": true,
        "atomic_checks": {
            "lint_command": "auto",
            "typecheck_command": "auto",
            "test_command": "auto",
            "timeout_seconds": 30
        },
        "full_checks": {
            "coverage_threshold": 80,
            "timeout_seconds": 120
        },
        "e2e_command": null,
        "integration_command": null
    },
    
    "accountability": {
        "enabled": true,
        "auto_feedback_enabled": false,
        "severity_threshold": "P2",
        "auto_resolve_on_fix": true,
        "lesson_extraction": true
    },
    
    "reporting": {
        "output_dir": ".quickagents/audit_reports",
        "format": "markdown",
        "auto_report_on_task_complete": true
    }
}
```

---

## 9. CLI 命令一览

```bash
# 初始化审计配置
qka audit init                    # 生成 audit_config.json

# 查看状态
qka audit status                  # 审计系统状态
qka audit log                     # 查看审计日志
qka audit log --session abc123    # 按会话过滤
qka audit log --file src/main.py  # 按文件过滤
qka audit log --limit 20          # 限制条数

# 手动触发
qka audit run                     # 全量检查
qka audit run --type atomic       # 原子检查（仅变更文件）
qka audit run --type full         # 全量检查
qka audit run --type e2e          # E2E 测试

# 问责管理
qka audit issues                  # 所有问题
qka audit issues --status OPEN    # 未解决问题
qka audit issues --severity P0    # 紧急问题

# 学习经验
qka audit lessons                 # 所有学习经验
qka audit lessons --category testing  # 按类别过滤

# 报告
qka audit report                  # 生成 Markdown 审计报告
qka audit report --format json    # JSON 格式
```

---

## 10. Python API 一览

```python
from quickagents import AuditGuard, AuditConfig

# 初始化
guard = AuditGuard(project_root='.', config_path='audit_config.json')

# 文件变更追踪（由插件或 AI 代理调用）
guard.on_file_change(
    file_path='src/auth.py',
    change_type='MODIFY',
    diff=unified_diff,
    tool_name='edit',
    session_id='sess-001',
    task_id='T001'
)

# Git commit 触发（原子检查）
result = guard.on_git_commit(staged_files=['src/auth.py', 'tests/test_auth.py'])
# result: GateReport(all_passed=True, checks=[...])

# Task 完成触发（全量检查 + 问责）
result = guard.on_task_complete(task_id='T001')
# result: {
#     'quality': GateReport,
#     'issues': [AuditIssue],
#     'lessons': [AuditLesson],
#     'feedback': str  # auto_feedback 生成的反馈消息
# }

# 查询
summary = guard.get_audit_summary()
# summary: {total_changes, total_issues, pass_rate, top_error_categories}

# 清理
guard.close()
```

---

## 11. 附录

### 11.1 与现有模块的关系

```
AuditGuard (新模块)
    │
    ├── 复用 GitCommit._run_lint/typecheck/tests()  → QualityGate
    ├── 复用 TDDWorkflow._run_tests/coverage()       → QualityGate
    ├── 复用 UnifiedDB                                → 存储审计数据
    ├── 复用 FeedbackCollector                        → 学习经验收集
    ├── 复用 SkillEvolution                           → 进化系统
    ├── 复用 LoopDetector                             → 修复循环检测
    └── 复用 MarkdownSync                             → 审计报告同步
```

### 11.2 版本规划

| 版本 | 内容 |
|------|------|
| v2.9.0 | AuditGuard 完整功能（Phase 1-5） |

### 11.3 参考文档

- [AGENTS.md](../AGENTS.md) - 开发规范
- [CHANGELOG.md](../CHANGELOG.md) - 变更日志
- [Docs/DESIGN.md](DESIGN.md) - 系统设计文档

---

*计划版本: 1.0.0 | 创建时间: 2026-04-05*
