# QuickAgents Version

> Version information file - for version detection and updates | 版本信息文件 - 用于版本检测和更新

---

## Current Version | 当前版本

| Property | Value |
|-----------|-------|
| Version | 2.7.6 |
| Git Tag | v2.7.6 |
| Release Date | 2026-04-01 |
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
qa --help
qa stats
qa hooks install
```

---

## What's New (v2.7.6) | 本次更新

**Core Architecture Upgrade — 6-Phase Enhancement, 568 Tests**

**核心架构升级 — 6阶段增强，568个测试**

---

### 1. Dynamic Connection Pool | 动态连接池

**Problem Solved | 解决的问题:**
- Fixed-size pool wastes resources when idle
- No validation for stale connections
- 固定连接池空闲时浪费资源
- 无过期连接验证

**Solution | 解决方案:**
- `PoolConfig(min_size, max_size)` — dynamic scaling
- `pre_ping=True` — validate before reuse
- PRAGMA tuning: `mmap_size=256MB`, `temp_store=MEMORY`
- Pool metrics: `hit_rate`, `avg_wait_ms`, `evicted_count`
- WAL auto-checkpoint: interval + threshold based

```python
from quickagents.core import ConnectionManager, PoolConfig

config = PoolConfig(min_size=2, max_size=10, pre_ping=True)
mgr = ConnectionManager('.quickagents/unified.db', pool_config=config)
metrics = mgr.get_pool_metrics()
```

---

### 2. Exponential Backoff Retry | 指数退避重试

- `RetryConfig(max_retries=5, backoff_base_ms=2000)`
- Thread-local transactions — independent depth per thread
- Read-only transaction separation
- 指数退避消除 `database is locked` 错误

---

### 3. Django-style QueryBuilder | Django风格查询构建器

```python
from quickagents.core import QueryBuilder

results = (
    QueryBuilder('memory')
    .filter(memory_type='factual')
    .filter(importance_score__gte=0.7)
    .exclude(category='internal')
    .order_by('-importance_score')
    .limit(10)
    .build()
)
```

- Immutable cloning, parameterized queries
- Batch INSERT optimization (5-10x faster)
- 不可变克隆，参数化查询，批量插入优化

---

### 4. External Migration Files | 外部迁移文件

- Load SQL from `migrations/` directory
- `MigrationResult` tracking with duration_ms
- Enhanced logging per migration
- 从 `migrations/` 目录加载SQL，增强日志

---

### 5. Session Interface Unification | Session接口统一

```python
session = db.session

with session.query() as conn:          # Read-only
    rows = conn.execute("SELECT ...").fetchall()

with session.transaction() as conn:    # Read-write
    conn.execute("INSERT INTO ...")

row = session.query_one("SELECT ...")  # Convenience
rows = session.query_all("SELECT ...")
session.execute("UPDATE ...")          # Auto-commit
```

- Single entry point for all database access
- All modules delegate through Session
- 所有模块通过 Session 统一访问数据库

---

### 6. Complete Command Reference | 完整命令参考

**CLI Commands (35+ subcommands):**
- `qa stats/sync/memory/tasks/progress/evolution/hooks/git/tdd/feedback/models/cache/loop/reminder`

**Slash Commands (30+ commands):**
- `/ultrawork` `/start-work` `/run-workflow` `/add-skill` `/list-skills` `/tdd-red/green/refactor` `/qa-update` `/feedback` `/debug` `/handoff`

**Upgrade Commands | 升级命令:**
- `/qa-update` — detect and update
- `/qa-update --check` — check only
- `/qa-update --rollback` — rollback
- `/qa-check-alignment` — version alignment check

---

## Module Overview | 模块概览

| Module | Function | Token Savings |
|--------|----------|---------------|
| UnifiedDB | Unified database management | 60%+ |
| MarkdownSync | Auto-sync to Markdown | 100% |
| FileManager | Smart file read/write (hash detection) | 90%+ |
| LoopDetector | Pattern-based loop detection | 100% |
| Reminder | Event reminders | 100% |
| SkillEvolution | Skills self-evolution | 0 |
| KnowledgeGraph | Knowledge graph | 80%+ |
| Browser | Browser automation | 50%+ |

---

## Test Results | 测试结果

| Test Type | Pass Rate | Details |
|-----------|-----------|---------|
| Unit Tests | 100% | 568/568 passing |
| Integration Tests | 100% | All passing |
| Code Quality | 100% | All syntax checks pass |

**Test Command | 测试命令:**
```bash
pytest tests/ -v
# 568 passed in 27.85s
```

---

## Version History | 版本历史

### v2.7.6 (2026-04-01)
- Core architecture upgrade: 6-phase enhancement
- Dynamic connection pool with pre_ping
- Exponential backoff retry
- Django-style QueryBuilder
- External migration files
- Session interface unification
- `qa version` and `qa update` CLI commands
- `qa uninstall` command with dry-run/keep-data/keep-config
- 580 tests passing (244 new)

### v2.7.5 (2026-04-01)
- Initial core architecture upgrade release (superseded by v2.7.6)

### v2.7.0 (2026-03-30)
- Pattern-based LoopDetector
- Python environment detection
- Bilingual documentation
- Complete API documentation
- Author unification

### v2.4.0 (2026-03-29)
- Browser automation (Playwright required)
- Lightpanda support

### v2.3.0 (2026-03-29)
- Unified self-evolution system
- Git hooks integration

### v2.2.0 (2026-03-29)
- UnifiedDB architecture
- SQLite primary storage + Markdown backup
- 60%+ token savings

### v2.1.1 (2026-03-28)
- feedback-collector-skill
- Experience collection system

### v2.1.0 (2026-03-27)
- 6 new skills based on OpenDev/VeRO/SWE-agent papers
- Event-driven reminders
- ACI design principles

### v2.0.0 (2026-03-22)
- Three-dimensional memory system
- 17 professional agents
- 24 core skills

---

## Agent Alignment Requirements | Agent对齐要求

> 每次版本更新时，所有Agent必须与当前版本的功能对齐

### v2.7.0 Agent更新要求

#### 必须包含的Python API

| Agent | 必须包含的API |
|-------|--------------|
| yinglong-init | Python环境检测、UnifiedDB初始化 |
| cangjie-doc | UnifiedDB、MarkdownSync、三向同步 |
| fenghou-orchestrate | UnifiedDB进度追踪、Todo驱动 |
| huodi-skill | SkillEvolution、使用统计 |
| kuafu-debug | SystematicDebugging、UnifiedDB记录 |
| lishou-test | TDD API、覆盖率检查 |
| jianming-review | SkillEvolution反馈、质量门禁 |
| mengzhang-security | 安全审计、UnifiedDB记录 |
| gonggu-refactor | UnifiedDB重构记录 |
| boyi-consult | KnowledgeGraph需求追踪 |
| fenghou-plan | UnifiedDB计划存储 |
| chisongzi-advise | 技术栈推荐、UnifiedDB |
| huodi-deps | 依赖管理、UnifiedDB |
| hengge-perf | 性能分析、UnifiedDB记录 |
| hengge-cicd | CI/CD管理、UnifiedDB |

#### 自动对齐检查

使用 `version-alignment-skill` 进行自动检查：

```bash
# 检查所有组件对齐状态
/qa-check-alignment

# 自动修复对齐问题
/qa-auto-align
```

#### 版本更新检查清单

当QuickAgents版本更新时：
1. [ ] 更新所有Agent的Python API使用说明
2. [ ] 更新相关Skill的功能集成
3. [ ] 更新AGENTS.md的API文档
4. [ ] 运行对齐检查确保一致性
5. [ ] 运行测试确保兼容性

---

## Roadmap | 路线图

### v2.8.0 (Planned | 计划中)
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

*QuickAgents v2.7.6 - Making AI agent development easier*

*QuickAgents v2.7.6 - 让AI代理开发更简单*
