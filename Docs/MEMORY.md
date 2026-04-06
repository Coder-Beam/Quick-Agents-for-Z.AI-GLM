# MEMORY.md

> 更新时间: 2026-04-06 11:55

> 此文件由 SQLite 自动同步生成，作为辅助备份
> 主存储: .quickagents/unified.db

---

## Factual Memory (事实记忆)

> 记录项目的静态事实信息

- **project.name**: QuickAgents
- **project.version**: 2.9.0
- **project.path**: D:/Projects/QuickAgents
- **project.description**: AI代理增强工具包 - 本地Python包 + OpenCode平台插件
- **project.tech_stack**: Python 3.9+, SQLite (WAL), FTS5, Playwright, httpx, Click
- **project.python_modules**: core, skills, yugong, audit, knowledge_graph, document, browser, cli, utils
- **project.current_stage**: 产品化改造中 - Phase 1 未完成
- **project.test_status**: 907 tests (242 yugong + 665 others), 8 integration failures
- **project.last_commit**: 5726701 feat(yugong): 真实Agent执行器 + CLI集成 + 修复3个CRITICAL bug
- **project.target_version**: v2.10.0 (D2决策)
- **project.default_llm_provider**: ZhipuAI (D4决策)
- **decision.D1**: 概念存根Skills处理方式=删除 (用户确认A)
- **decision.D2**: 版本号=v2.10.0渐进式 (用户确认A)
- **decision.D3**: report_generator输出格式=Markdown+JSON双格式 (用户确认B)
- **decision.D4**: CLI默认LLM Provider=ZhipuAI (用户确认A)
- **decision.D5**: 是否提交YuGong到git=是先提交 (用户确认A)
- **skills.remaining**: browser-devtools, doom-loop, event-reminder, feedback-collector, glm-version-sync, project-memory, ui-ux-pro-max, version-alignment, yugong-loop-skill + EVOLUTION.md + registry.json
- **skills.deleted**: aci-design, adaptive-compression, background-agents, boulder-tracking, category-system, code-review, git-commit, inquiry, lazy-discovery, lsp-ast, multi-model, project-detector, si-hybrid, skill-integration, systematic-debugging, tdd-workflow, update, vero-evaluation (18个SKILL.md已删除, 目录可能残留)

---

## Experiential Memory (经验记忆)

- [1775447707.677343] **pitfalls**: 上一会话崩溃：在执行D1删除概念存根Skills时崩溃，18个SKILL.md已删除但未提交
- [1775447707.6774867] **pitfalls**: 概念存根删除已部分完成：18个SKILL.md已从git删除(unstaged)，但目录可能仍存在
- [1775447707.6775842] **pitfalls**: registry.json仅注册7个Skills，与实际28个目录严重不一致，需在Skills治理时同步更新
- [1775447707.6776798] **pitfalls**: test_phase5_integration.py有8个import失败，已知问题待修复

---

## Working Memory (工作记忆)

- **current.phase**: 产品化改造 Phase 1 - CRITICAL修复与CLI集成
- **current.critical_status**: C1:CLI未接入真实Agent; C2:agent_fn=None假成功(已修复未提交?); C3:AgentExecutor未连接CLI默认配置
- **current.uncommitted_changes**: 18个SKILL.md已删除(unstaged) + report_generator.py新增(untracked) + yugong/__init__.py修改 + Docs文件更新
- **current.next_action**: 提交D1删除+report_generator → 修复C1/C2/C3 → CLI子命令增强 → Skills目录治理
- **current.blockers**: 无阻塞项，5个决策点已全部确认
