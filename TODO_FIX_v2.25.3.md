# QuickAgents v2.25.3 全量修复清单

> 生成时间: 2026-04-07
> 基于全架构审计结果，按优先级排列

## P0 — 必须修复（运行时崩溃/数据丢失）

### P0-1: CLI audit status/run 运行时崩溃 ✅ 已修复
- **文件**: `quickagents/cli/main.py`
- **问题1**: 第679行 `tracker['today_changes']` KeyError — `get_stats()` 只返回 `total_changes/total_sessions/total_files`
- **问题2**: 第703/714行 `report.passed` AttributeError — `GateReport` 属性是 `all_passed`，不是 `passed`
- **问题3**: 第732行 `get_changes_by_session()` 方法不存在 — 应使用 `get_changes(session_id=...)`
- **问题4**: `on_git_commit()`/`on_task_complete()` 可返回 `None`（质量门禁禁用时），需 null check
- **修复**: 已在本次会话中完成

### P0-2: decisions 表不存在导致 get_decisions() 永远返回空
- **文件**: `quickagents/core/migration_manager.py`, `quickagents/core/unified_db.py`
- **问题**: `unified_db.py:465-494` 的 `get_decisions()` 查询 `FROM decisions` 表，但 migration 中从未创建此表
- **影响**: `MarkdownSync.sync_decisions()` 总是生成空 DECISIONS.md
- **修复方案**:
  1. 在 `migration_manager.py` 中添加 `migration_005` (add_decisions_table)
  2. 表结构: `decisions(id, title, decision, context, status, created_at, updated_at)`
  3. 在 `unified_db.py` 中添加 `add_decision()` / `update_decision()` 方法

### P0-3: 愚公循环运行时全部状态仅在内存中（YuGongDB 存而不用）
- **文件**: `quickagents/yugong/autonomous_loop.py`
- **问题**: `YuGongLoop._run_loop()` 85行循环体中零 DB 调用。`YuGongDB` 定义了 7 个表（stories/iterations/progress/context/state/checkpoints/logs）但主循环从不使用
- **影响**: 进程崩溃 = 全部状态永久丢失。TaskOrchestrator(dict)、ProgressLogger(list)、SafetyGuard(实例变量) 全部纯内存
- **修复方案**:
  1. `YuGongLoop.__init__()` 接受可选 `db_path` 参数，创建 `YuGongDB` 实例
  2. `_run_loop()` 每次迭代结束后调用 `db.save_state()` + `db.save_story()` + `db.save_iteration()`
  3. 每 N 次迭代调用 `db.save_checkpoint()`

---

## P1 — 应该修复（架构脱节/数据不一致）

### P1-1: CLI memory 使用错误后端
- **文件**: `quickagents/cli/main.py:177-205`
- **问题**: `cmd_memory` 用 `MemoryManager`（纯文件系统，直接写 Docs/MEMORY.md）而非 `UnifiedDB`（SQLite）
- **影响**: `qka memory set foo bar` 写 Markdown，但 `qka sync` 从 SQLite 覆盖 Markdown，导致 CLI 写入的内容丢失
- **修复**: `cmd_memory` 改用 `UnifiedDB(db_path).set_memory()` / `get_memory()` / `search_memory()`

### P1-2: SkillEvolution 不调用 ExperienceCompiler.accumulate()
- **文件**: `quickagents/core/evolution.py`
- **问题**: `on_task_complete()` 收集经验数据写 `feedback` 表，但从不调用 `ExperienceCompiler.accumulate()` 将经验送入编译管道
- **影响**: 经验编译器无数据源，除非手动通过 CLI 传入 JSON 文件
- **修复**: 在 `on_task_complete()` 末尾添加 `ExperienceCompiler(db_path).accumulate(task_info)` 调用

### P1-3: 进化系统 CLI stats bug
- **文件**: `quickagents/cli/main.py:562`
- **问题**: `stats['total_usage']` 但 `get_skill_stats()` 返回 `stats['usage_count']`
- **修复**: 改为 `stats.get('usage_count', 0)`

### P1-4: DocumentPipeline.save() 完全绕过 SQLite
- **文件**: `quickagents/document/pipeline.py`
- **问题**: `save()` 方法硬编码 `storage_type="file"`，只写平面文件。`KnowledgeSaver` 存在但 `DocumentPipeline` 从不调用
- **修复**: `save()` 中当 `KnowledgeGraph` 可用时，调用 `KnowledgeSaver` 写入 KG → SQLite

### P1-5: 知识图谱 discover() 结果不持久化
- **文件**: `quickagents/knowledge_graph/knowledge_graph.py:107-136`
- **问题**: 4 个 discovery 方法返回内存中的 `KnowledgeEdge`，调用方从不写回数据库
- **修复**: `discover()` 方法内部自动调用 `self.edges.create_edge()` 持久化发现的边

### P1-6: 知识图谱无 CLI 命令
- **文件**: `quickagents/cli/main.py`
- **问题**: 没有注册 `qka knowledge`/`qka kg` 子命令
- **修复**: 添加 `cmd_knowledge` 函数 + argparse 注册，支持 `search/create/status` 子命令

### P1-7: 知识图谱 sync_to_memory() 覆写 MEMORY.md
- **文件**: `quickagents/knowledge_graph/core/memory_sync.py:134-154`
- **问题**: 每次调用完全覆写文件，破坏主记忆系统内容
- **修复**: 改为追加模式或仅在 `## Knowledge Graph Sync` section 内更新

---

## P2 — 改善（非紧急但应修复）

### P2-1: MarkdownSync.restore_decisions_from_md() 是空壳
- **文件**: `quickagents/core/markdown_sync.py:725-745`
- **问题**: 解析了 `D001 - 标题` 但从不插入 SQLite，只计数
- **修复**: 解析后调用 `db._get_connection()` 执行 `INSERT INTO decisions`

### P2-2: MarkdownSync.restore_feedback_from_md() 是空壳
- **文件**: `quickagents/core/markdown_sync.py:778-803`
- **问题**: 只数 `## ` 标题数，不解析也不插入
- **修复**: 解析标题和内容，调用 `db.add_feedback()`

### P2-3: MarkdownSync.restore_progress_from_json() 调用不存在方法
- **文件**: `quickagents/core/markdown_sync.py:758-771`
- **问题**: 调用 `db.add_notepad_entry()`, `db.get_notepad_entries()`, `db.get_checkpoints()` 但这些方法不存在于 UnifiedDB
- **修复**: 移除不存在方法的调用，改用实际存在的 `db.init_progress()` + `db.update_progress()`

### P2-4: Git 钩子不兼容 Windows + 错误被静默吞掉
- **文件**: `quickagents/core/git_hooks.py`
- **问题**: 用 `#!/bin/bash` + `python3`，Windows 上可能无法执行；`2>/dev/null || true` 静默吞掉所有错误；不触发 AuditGuard
- **修复**: 添加 Windows batch 脚本支持；错误写入日志文件而非丢弃；添加 AuditGuard 调用

### P2-5: 缺失 CLI 命令 qka tasks 和 qka progress
- **文件**: `quickagents/cli/main.py`
- **问题**: AGENTS.md 文档了 `qka tasks list/add/status` 和 `qka progress`，但 argparse 中未注册
- **修复**: 添加 `cmd_tasks` 和 `cmd_progress` 函数 + argparse 注册

---

## 版本与发布

### VER-1: 版本号 → 2.25.3
- **文件**: `pyproject.toml:7` — `version = "2.11.0"` → `version = "2.25.3"`
- **文件**: `quickagents/__init__.py` — 更新 `__version__`

### VER-2: 更新 README.md
- 更新版本号、修复日志、架构改进说明

### GIT-1: Git commit + tag
- `git commit` 全部修复
- `git tag v2.25.3`

---

## 完成标准

- [ ] 所有 P0 项修复并通过测试
- [ ] 所有 P1 项修复并通过测试
- [ ] P2 项至少完成 3 个
- [ ] 版本号更新为 2.25.3
- [ ] README.md 更新
- [ ] Git commit + tag v2.25.3
