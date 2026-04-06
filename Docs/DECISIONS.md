# 决策日志 (DECISIONS.md)

> 更新时间: 2026-04-06

---

## 决策索引

| 决策ID | 标题 | 决策时间 | 影响范围 | 状态 |
|--------|------|----------|----------|------|
| D001 | 概念存根Skills处理方式 | 2026-04-06 | Skills目录, .opencode/skills/ | ✅ 已确认 |
| D002 | 产品化版本号 | 2026-04-06 | pyproject.toml, VERSION.md | ✅ 已确认 |
| D003 | ReportGenerator输出格式 | 2026-04-06 | yugong/report_generator.py | ✅ 已实施 |
| D004 | CLI默认LLM Provider | 2026-04-06 | cli/main.py, yugong/llm_client.py | ✅ 已确认 |
| D005 | YuGong模块Git提交策略 | 2026-04-06 | Git仓库 | ✅ 已确认 |
| D006 | YuGong自主循环架构 | 2026-04-05 | quickagents/yugong/ (16个文件) | ✅ 已实施 |
| D007 | 双层架构：Python包+OpenCode插件 | 2026-03-25 | 整体架构 | ✅ 已实施 |
| D008 | SQLite为主存储+Markdown辅助 | 2026-03-25 | core/, Docs/ | ✅ 已实施 |

---

## D001 - 概念存根Skills处理方式

| 属性 | 值 |
|------|-----|
| 决策ID | D001 |
| 决策时间 | 2026-04-06 |
| 决策者 | 用户确认 |
| 影响范围 | .opencode/skills/ (28个目录→9个保留) |
| 关联任务 | T001, T002, T010, T011, T012 |

### 决策背景
28个Skill目录中18个是概念存根(纯SKILL.md文本)，无脚本、无代码引用。其中部分Skills的功能已有对应Python模块实现(如project-memory→UnifiedDB, feedback-collector→SkillEvolution)。

### 备选方案
1. **方案A: 删除** — 清除所有无实质内容的存根，保持目录干净
2. **方案B: 保留标记deprecated** — 保留但标记，占用目录空间

### 最终决策
**方案A: 删除**

### 执行状态
- 18个SKILL.md已删除(git unstaged)，待提交
- 空目录需清理
- registry.json需更新

### 保留的Skills (9个)
1. `ui-ux-pro-max` — 可执行型(BM25搜索+67种UI样式数据)
2. `glm-version-sync-skill` — 可执行型(版本同步脚本)
3. `browser-devtools-skill` — 引用真实Python模块(Browser)
4. `doom-loop-skill` — 引用LoopDetector
5. `event-reminder-skill` — 引用Reminder
6. `feedback-collector-skill` — 引用SkillEvolution
7. `project-memory-skill` — 引用UnifiedDB
8. `version-alignment-skill` — 引用多个核心模块
9. `yugong-loop-skill` — 引用LoopDetector+YuGong

---

## D002 - 产品化版本号

| 属性 | 值 |
|------|-----|
| 决策ID | D002 |
| 决策时间 | 2026-04-06 |
| 决策者 | 用户确认 |
| 影响范围 | pyproject.toml, VERSION.md, __init__.py |

### 最终决策
**v2.10.0** — 渐进式版本升级，不跳大版本号

### 理由
- 产品化改造主要是修复和增强，不涉及破坏性变更
- YuGong是新模块，不影响已有API
- 渐进式升级降低用户升级风险

---

## D003 - ReportGenerator输出格式

| 属性 | 值 |
|------|-----|
| 决策ID | D003 |
| 决策时间 | 2026-04-06 |
| 决策者 | 用户确认 |
| 影响范围 | yugong/report_generator.py |
| 关联任务 | T006 |

### 最终决策
**双格式: Markdown + JSON**

### 实施状态
✅ 已实施 — `ReportGenerator` 类支持 `generate_markdown()` + `generate_json()` + `save(formats=["markdown","json"])`

### 理由
- Markdown: 人类可读，方便直接查看
- JSON: 机器可解析，方便CI/CD集成和自动化处理

---

## D004 - CLI默认LLM Provider

| 属性 | 值 |
|------|-----|
| 决策ID | D004 |
| 决策时间 | 2026-04-06 |
| 决策者 | 用户确认 |
| 影响范围 | cli/main.py, yugong/llm_client.py |
| 关联任务 | T004, T005 |

### 最终决策
**ZhipuAI** 作为默认Provider

### 理由
- 项目使用GLM-5模型(204800 context window)
- ZhipuAI API Key环境变量: `ZHIPUAI_API_KEY`
- 兼容OpenAI API格式，切换成本低

### 优先级链
```
ZHIPUAI_API_KEY → zhipuai provider
OPENAI_API_KEY → openai provider (fallback)
```

---

## D005 - YuGong模块Git提交策略

| 属性 | 值 |
|------|-----|
| 决策ID | D005 |
| 决策时间 | 2026-04-06 |
| 决策者 | 用户确认 |
| 影响范围 | Git仓库 |

### 最终决策
**先提交** — 当前YuGong工作成果先提交到git

### 理由
- 已有222+ tests全部通过，具备提交条件
- 避免代码丢失风险
- 便于后续增量开发

---

## D006 - YuGong自主循环架构

| 属性 | 值 |
|------|-----|
| 决策ID | D006 |
| 决策时间 | 2026-04-05 |
| 决策者 | AI建议 + 用户确认 |
| 影响范围 | quickagents/yugong/ (16个文件, 222+ tests) |

### 最终决策
实现完整的自主开发循环模块

### 模块结构
```
yugong/
├── models.py           — 数据模型 (UserStory, LoopResult, LoopState)
├── config.py           — YuGongConfig
├── db.py               — YuGongDB SQLite持久化 (7张表)
├── llm_client.py       — LLMClient + LLMConfig (OpenAI兼容)
├── tool_executor.py    — ToolExecutor (7个内置工具)
├── agent_executor.py   — AgentExecutor (多轮对话+工具调用)
├── autonomous_loop.py  — YuGongLoop 核心引擎
├── requirement_parser.py — 需求解析 (JSON/MD/Text)
├── task_orchestrator.py  — 任务编排
├── safety_guard.py     — 安全守护
├── exit_detector.py    — 退出检测
├── context_injector.py — 上下文注入
├── progress_logger.py  — 进度日志
├── report_generator.py — 报告生成器 (D3双格式)
└── __init__.py         — 模块导出
```

---

## D007 - 双层架构

| 属性 | 值 |
|------|-----|
| 决策ID | D007 |
| 决策时间 | 2026-03-25 |
| 决策者 | 架构决策 |
| 影响范围 | 整体架构 |

### 最终决策
Python包(pip install) + OpenCode平台插件(TypeScript) 双层架构

---

## D008 - SQLite主存储+Markdown辅助

| 属性 | 值 |
|------|-----|
| 决策ID | D008 |
| 决策时间 | 2026-03-25 |
| 决策者 | 架构决策 |
| 影响范围 | core/, Docs/ |

### 最终决策
SQLite为主存储(WAL模式) + Markdown为辅助备份(Git版本控制)

---

*最后更新: 2026-04-06 | 产品化改造*
