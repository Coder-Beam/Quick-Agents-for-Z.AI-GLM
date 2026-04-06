# QuickAgents v2.25.4 全架构A级修复清单

> 生成时间: 2026-04-07
> 目标: 所有模块达到 A 级评价，统一架构，真正自我进化

## 核心约束
- 所有模块必须统一使用 UnifiedDB 的 ConnectionManager，绝不接受自建连接
- 知识图谱 tag/discovery 必须SQL层面高效实现
- 编译必须自动执行，无需手动触发
- 自我进化必须真正闭环：Collect→Analyze→Compile→Act→Verify
- Git 钩子必须兼容 Windows（主要使用场景）
- 互操作性矩阵必须全部 ✅

---

## Wave 1: 统一架构 + 关键 Bug 修复

### W1-1: ExperienceCompiler 统一到 ConnectionManager（当前自建 sqlite3.connect）
- **文件**: `quickagents/core/experience_compiler.py`
- **目标**: 改为接收 ConnectionManager 或 db_path，通过 ConnectionManager 访问
- **评级目标**: A

### W1-2: YuGongDB 统一到 ConnectionManager（当前自建 sqlite3.connect）
- **文件**: `quickagents/yugong/db.py`
- **目标**: 改为接收 ConnectionManager 或 db_path，通过 ConnectionManager 访问
- **评级目标**: A

### W1-3: KnowledgeGraph 存储层统一到 ConnectionManager（当前自建线程局部连接）
- **文件**: `quickagents/knowledge_graph/storage/sqlite_storage.py`
- **目标**: 改为接收 ConnectionManager，复用 UnifiedDB 的连接池
- **评级目标**: A

### W1-4: 知识图谱 discover() 属性名 bug + create_edge 签名不匹配
- **文件**: `quickagents/knowledge_graph/knowledge_graph.py:131-139`
- **问题**: `edge.source_id` 应为 `edge.source_node_id`；`create_edge(edge)` 应传参数
- **评级目标**: A

### W1-5: DocPipeline dispatch bug（hasattr 检查不存在的属性）
- **文件**: `quickagents/document/pipeline.py:155-158`
- **问题**: `hasattr(result, "document_id")` 永远 False；应改 isinstance 检查
- **补充**: 还需调用 `save_traces()` 保存交叉引用
- **评级目标**: A

### W1-6: Evolution Markdown sync key bug
- **文件**: `quickagents/core/evolution.py:1347`
- **问题**: `stats.get('total_usage', 0)` 应为 `stats.get('usage_count', 0)`
- **评级目标**: A

### W1-7: restore_all_from_md() 路径不匹配
- **文件**: `quickagents/core/markdown_sync.py`
- **问题**: feedback restore 默认 `Docs/feedback.md`，但 sync 写到 `.quickagents/feedback/*.md`
- **修复**: restore 自动扫描 `.quickagents/feedback/` 目录下所有 .md 文件
- **评级目标**: A

### W1-8: 知识图谱 tag 搜索效率优化
- **文件**: `quickagents/knowledge_graph/storage/sqlite_storage.py`, `searcher.py`
- **问题**: `search_by_tags()` 加载1000节点到Python过滤
- **方案**: 添加 `knowledge_node_tags(node_id, tag)` 关联表 + SQL JOIN 查询
- **需添加 migration_006**
- **评级目标**: A

### W1-9: 知识图谱 discovery 效率优化
- **文件**: `quickagents/knowledge_graph/core/discovery.py`
- **问题**: 3个方法都 `query_nodes(limit=1000)` 全表扫描
- **方案**: 使用 SQL JOIN + WHERE 直接在数据库层面发现关系
- **评级目标**: A

---

## Wave 2: 自动编译 + 真正自我进化

### W2-1: 经验编译自动触发
- **文件**: `quickagents/core/evolution.py`
- **目标**: `on_task_complete()` 检查 `should_compile()`，设置 `experience_compile_due` 标志
- **目标**: `run_periodic_optimization()` 自动触发编译流程
- **评级目标**: A

### W2-2: 自我进化 — 语义分析替代字符串匹配
- **文件**: `quickagents/core/evolution.py`
- **问题**: `_extract_patterns()` 和 `_analyze_commit()` 使用 if/else 硬编码
- **方案**: 基于 embedding 相似度的模式匹配（使用经验编译器的 FTS5 作为近似语义搜索）
- **评级目标**: A

### W2-3: 自我进化 — Act 行动层实现
- **文件**: `quickagents/core/evolution.py` + 新文件
- **目标**: 
  1. `modify_skill()` — 自动更新 SKILL.md 文件的参数/提示词
  2. `inject_context()` — 将进化洞察注入到 session 上下文
  3. `adjust_parameters()` — 自动调整进化阈值/编译阈值
- **评级目标**: A

### W2-4: 自我进化 — Verify 验证层实现
- **文件**: `quickagents/core/evolution.py`
- **目标**: 
  1. 修改前后对比验证（修改skill后运行测试检查成功率变化）
  2. 回滚机制（修改导致下降时自动回滚）
  3. 效果报告生成
- **评级目标**: A

---

## Wave 3: 跨模块集成 + Git 钩子

### W3-1: YuGongLoop → Evolution 集成
- **文件**: `quickagents/yugong/autonomous_loop.py`
- **目标**: 循环完成时自动调用 `evolution.on_task_complete()`
- **评级目标**: A

### W3-2: AuditGuard → Evolution 集成
- **文件**: `quickagents/audit/audit_guard.py`
- **目标**: 提取的 lessons 自动流入 Evolution 的 feedback 系统
- **评级目标**: A

### W3-3: Evolution 查询经验编译器
- **文件**: `quickagents/core/evolution.py`
- **目标**: `_suggest_fix()` 同时查询 experience_entries 和 compiled_articles
- **评级目标**: A

### W3-4: Git 钩子 Windows 兼容
- **文件**: `quickagents/core/git_hooks.py`
- **目标**: 
  1. 使用 `sys.executable` 替代硬编码 `python3`
  2. 生成 `.bat`/`.cmd` wrapper 用于 Windows
  3. 错误写入日志文件而非 `2>/dev/null`
  4. 同时触发 Evolution + AuditGuard
- **评级目标**: A

### W3-5: 清理死代码 + dead imports
- **文件**: `quickagents/cli/main.py:97`, `quickagents/core/markdown_sync.py:803-825`
- **目标**: 删除未使用的 MemoryManager import、restore_progress 死代码
- **评级目标**: A

---

## Wave 4: 版本发布

### W4-1: 版本号 → 2.25.4 + 更新文档
### W4-2: Git commit + tag v2.25.4

---

## 验收标准

- [ ] 所有模块统一使用 ConnectionManager（零自建连接）
- [ ] 知识图谱 tag 搜索和 discovery 走 SQL 查询（不加载全表）
- [ ] 经验编译自动触发（无需手动）
- [ ] 自我进化 5 阶段闭环：Collect→Analyze→Compile→Act→Verify
- [ ] DocPipeline dispatch 正确分发到 KnowledgeSaver
- [ ] restore 路径匹配（自动发现 .quickagents/feedback/ 下的文件）
- [ ] Git 钩子 Windows 原生兼容
- [ ] 互操作性矩阵全部 ✅
- [ ] CLI 30+ 命令全部可用
