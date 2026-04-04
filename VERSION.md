# QuickAgents Version

> Version information file - for version detection and updates | 版本信息文件 - 用于版本检测和更新

---

## Current Version | 当前版本

| Property | Value |
|-----------|-------|
| Version | 2.8.3 |
| Git Tag | v2.8.3 |
| Release Date | 2026-04-05 |
| Minimum Compatible | 2.0.0 |
| Repository | https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM |
| PyPI Package | https://pypi.org/project/quickagents/ |
| Author | Coder-Beam |

---

## Installation | 安装

```bash
# Install from PyPI | 从PyPI安装
pip install quickagents

# Full installation (with Windows features) | 完整安装（包含Windows功能）
pip install quickagents[full]

# Verify installation | 验证安装
python -c "from quickagents import __version__; print(f'QuickAgents v{__version__}')"

# CLI commands | CLI命令
qka --help
qka stats
qka hooks install
```

---

## What's New (v2.8.3) | 本次更新

**Performance Optimization & Code Quality — 性能优化与代码质量**

---

### 1. SQLite Performance Optimization | SQLite性能优化

- **WAL Mode + Persistent Connections**: Thread-local persistent connections with PRAGMA tuning
  - `synchronous=NORMAL`, `cache_size=-8000`, `temp_store=MEMORY`
  - `mmap_size=67108864` (64MB), `busy_timeout=5000`
- **N+1 Query Elimination**: Batch SQL queries replace per-node loops
  - `query_edges_batch()`: 2N queries → 1 query
  - `get_nodes_batch()`: M queries → 1 query
- **Resource Cleanup**: `close()` + `__del__` for proper connection lifecycle

---

### 2. MarkdownSync Optimization | Markdown同步优化

- **Parallel Sync**: `sync_all()` uses `ThreadPoolExecutor` (3 workers)
- **Batch Query**: `sync_memory()` uses 1 `get_all_memories()` + Python grouping instead of 3 separate queries
- **Batch Feedback**: `sync_feedback()` uses 1 `get_feedbacks(limit=1000)` instead of 5 separate queries

---

### 3. Code Quality Gate | 代码质量门禁

- **mypy 0 errors**: 251 errors → 0 (Optional[] annotations + type: ignore)
- **ruff 0 errors**: All lint + format issues resolved, `line-length=120`
- **580 tests**: All passing, 0 failures

---

### 4. Knowledge Graph Fixes | 知识图谱修复

- **FTS5 Prefix Search**: Fixed prefix search for CJK text
- **Coverage Protection**: MarkdownSync overwrites only matching memory type sections

---

### Module Overview | 模块概览

| Module | Function | Status |
|--------|----------|--------|
| UnifiedDB | Unified database management | Stable |
| Session | Database session interface | Stable |
| ConnectionManager | Dynamic connection pool | Stable |
| TransactionManager | ACID transactions | Stable |
| QueryBuilder | Django-style query builder | Stable |
| MarkdownSync | Parallel sync to Markdown | Optimized |
| KnowledgeGraph | Knowledge graph + FTS5 | Optimized |
| DocumentPipeline | Document parsing pipeline | Stable |
| FileManager | Smart file read/write | Stable |
| LoopDetector | Pattern-based loop detection | Stable |
| Reminder | Event reminders | Stable |
| SkillEvolution | Skills self-evolution | Stable |
| Browser | Browser automation | Stable |

---

## Test Results | 测试结果

| Test Type | Pass Rate | Details |
|-----------|-----------|---------|
| Unit Tests | 100% | 580/580 passing |
| Code Quality | 100% | ruff 0 errors, mypy 0 errors |

**Test Command | 测试命令:**
```bash
pytest tests/ -v
# 580 passed
```

---

## Version History | 版本历史

### v2.8.2 (2026-04-05)
- FTS5 prefix search fix for KnowledgeGraph
- MarkdownSync overwrite protection
- CLI command rename `qa` → `qka` (finalized)
- PyPI release 2.8.2

### v2.8.1 (2026-04-04)
- CLI command rename from `qa` to `qka`
- SourceCodeParser inheritance fix
- Document module extraction documentation

### v2.8.0 (2026-04-01)
- Document Understanding module: 3-layer pipeline (parse → validate → extract)
- 7 document parsers: PDF, Word, Excel, XMind, FreeMind, OPML, Markdown
- Source code parser: Python ast + tree-sitter (optional)
- Three-level trace matching engine with bilingual synonym table
- `qka import` CLI command for batch document processing
- Knowledge Graph extension: 4 new NodeTypes, 4 new EdgeTypes
- Markdown export: trace matrix, coverage, diff reports
- Optional dependency groups: [document], [source-code], [ocr]
- 340 document tests, all passing

### v2.7.8 (2026-04-01)
- `qka uninstall` redesign: project-level only, no global side effects
- `qka export` command: clean export to Output/<version>/ with git commit binding
- 580 tests all passing

### v2.7.6 (2026-04-01)
- Core architecture upgrade: 6-phase enhancement
- `qka version` and `qka update` commands
- Performance benchmarks: 16,679 QPS read, 100% pool hit rate

### v2.7.5 (2026-04-01)
- ConnectionManager: dynamic connection pool, pre_ping, PRAGMA enhancements
- TransactionManager: exponential backoff retry, thread-local transactions
- Repository Layer: QueryBuilder, batch INSERT optimization
- Session: unified database session interface
- 568 tests passing

### v2.7.0 (2026-03-31)
- UnifiedDB V2 architecture: layered design with 7 modular files

### v2.4.0 (2026-03-29)
- Browser automation (Playwright required)

### v2.3.0 (2026-03-29)
- Unified self-evolution system, Git hooks integration

### v2.2.0 (2026-03-29)
- UnifiedDB architecture, SQLite primary storage + Markdown backup

### v2.0.0 (2026-03-22)
- Three-dimensional memory system, 17 agents, 24 skills

---

## Roadmap | 路线图

### v2.9.0 (Planned | 计划中)
- Multi-model routing with intelligent fallback
- Async database operations support
- Performance profiling dashboard

### v3.0.0 (Planned | 计划中)
- Plugin marketplace
- Custom skill creator
- Visual workflow builder

---

## Support | 支持

- **GitHub**: https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM
- **Issues**: https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/issues
- **PyPI**: https://pypi.org/project/quickagents/
- **Documentation**: https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/tree/main/Docs

---

## Remote Version Detection URL | 远程版本检测URL

```
https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/VERSION.md
```

---

## Update Commands | 更新命令

```bash
# Check for updates | 检查更新
/qa-update --check

# Update to latest | 更新到最新版本
/qa-update

# Show current version | 显示当前版本
/qa-update --version

# Manual update | 手动更新
pip install --upgrade quickagents
```

---

*QuickAgents v2.8.3 - Making AI agent development easier*

*QuickAgents v2.8.3 - 让AI代理开发更简单*
