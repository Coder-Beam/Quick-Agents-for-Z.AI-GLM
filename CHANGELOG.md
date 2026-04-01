# Changelog

All notable changes to QuickAgents will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.7.8] - 2026-04-01

### Added - Project Isolation & Clean Export

#### qa uninstall — Project-Level Isolation (Redesign)
- **Strict Project Scope**: Only cleans files within the current project directory
- **No Global Side Effects**: Never touches pip package, `~/.quickagents/`, or other projects
- **Cleanup Targets**: `.quickagents/`, `.opencode/`, `AGENTS.md`, `VERSION.md`, `quickagents.json`, qa-related git hooks
- **New `--keep-opencode` Flag**: Preserve `.opencode/` directory when desired
- **Safety Banner**: Clear warning that only current project is affected, pip package untouched

#### qa export — Clean Project Export
- **Clean Export to `Output/<version>/`**: Copies project files excluding all QuickAgents runtime artifacts
- **Git Commit Binding**: Requires clean git working tree (all changes committed) before export
- **Commit Hash Traceability**: `export-manifest.json` records full git commit hash
- **Automatic Version Detection**: Reads from `pyproject.toml` → `package.json` → `VERSION.md` → git tag
- **`.gitignore` Injection**: `--inject-gitignore` adds QA exclusion rules to `.gitignore`
- **Exclusion Preview**: `--list-excludes` displays all exclusion patterns
- **Dry-Run Mode**: `--dry-run` previews included/excluded files without executing

#### Export Exclusion Patterns
- **Runtime Directories**: `.quickagents/`, `.opencode/`, `.pytest_cache/`, `__pycache__/`
- **Config Files**: `AGENTS.md`, `VERSION.md`, `quickagents.json`, `opencode.json`
- **QA-Generated Docs**: `Docs/MEMORY.md`, `Docs/TASKS.md`, `Docs/DECISIONS.md`, `Docs/INDEX.md`, `Docs/features/`, `Docs/modules/`
- **Generic Excludes**: `node_modules/`, `.git/`, `dist/`, `*.egg-info`, `*.pyc`, `.env`

### Changed
- **`qa uninstall` Complete Redesign**: Removed all global operations (no pip uninstall, no `~/.quickagents/` deletion)
- **Removed `--keep-config` Flag**: Replaced by `--keep-opencode` (was misleading — "config" implied global)
- **Uninstall Confirmation**: Prompt now reads "确认卸载当前项目中的 QuickAgents 文件?" instead of generic "确认卸载?"
- **Uninstall Completion Message**: Now explicitly states "pip 包未被卸载，其他项目不受影响"

### Fixed
- Multi-project safety: Previous version would `pip uninstall quickagents` affecting ALL projects
- Global data deletion: Previous version would `rm -rf ~/.quickagents/` destroying shared data
- `UninstallCommand` tests updated to match project-level behavior (54 CLI tests passing)

### New Files
- `tests/benchmark_performance.py` — Performance benchmark suite (read 16,679 QPS, pool 100% hit rate, WAL controlled)

## [2.7.6] - 2026-04-01

### Added - CLI Commands & Version Alignment

#### qa version Command
- **Version Display**: Shows QuickAgents version and Python version
- **Module Integrity Check**: `qa version --check` verifies all 15 core modules and 5 key classes

#### qa update Command
- **PyPI Upgrade**: `qa update` installs latest version from PyPI
- **Targeted Upgrade**: `qa update --target 2.7.6` upgrades to specific version
- **GitHub Source**: `qa update --source github` installs from GitHub main branch
- **Dry-Run**: `qa update --dry-run` previews upgrade without executing

#### qa uninstall Command (Initial Version, superseded by 2.7.8)
- **Interactive Uninstall**: `qa uninstall` with confirmation prompt
- **Dry-Run**: `qa uninstall --dry-run` previews cleanup
- **Keep Flags**: `--keep-data`, `--keep-config` for selective cleanup
- **Force Mode**: `--force` skips confirmation

#### Documentation
- **Uninstall Guide**: `Docs/guides/UNINSTALL_GUIDE.md` — complete uninstall instructions for all versions
- **Performance Benchmarks**: `tests/benchmark_performance.py` with automated verification

### Changed
- **Version Alignment**: Unified all version references to 2.7.6 across VERSION.md, RELEASE_NOTES.md, README.md
- **Test Count**: 568 → 580 tests (12 new uninstall tests)

### Performance Benchmark Results (v2.7.6)
| Metric | Result |
|--------|--------|
| Single Read QPS | 16,679 ops/sec |
| Batch Write QPS | 5,200–7,096 ops/sec |
| Connection Pool Hit Rate | 100% |
| Connection Acquisition | 0.005–0.006 ms |
| WAL Growth | 0 KB (auto-checkpoint) |

## [2.7.5] - 2026-04-01

### Added - Core Architecture Upgrade (6 Phases)

#### Phase 1: ConnectionManager Enhancement
- **Dynamic Connection Pool**: `PoolConfig(min_size, max_size)` replaces fixed `pool_size`
- **pre_ping Validation**: `SELECT 1` check before reusing connections
- **PRAGMA Enhancements**: `mmap_size=256MB`, `temp_store=MEMORY`, `wal_autocheckpoint=1000`
- **Pool Metrics**: `PoolMetrics` dataclass tracking hit_rate, avg_wait_ms, created/reused/evicted counts
- **Idle Connection Eviction**: Configurable `idle_timeout` (default 300s)
- **WAL Auto-Checkpoint**: Interval-based (5min) + threshold-based (1000 ops), using independent connection

#### Phase 2: TransactionManager Enhancement
- **Exponential Backoff Retry**: `RetryConfig(max_retries=5, backoff_base_ms=2000, multiplier=2.0)`
- **Thread-Local Transactions**: `threading.local()` for per-thread depth/connection tracking
- **Independent Read-Only Depth**: Separate `read_depth` counter for `read_only()` transactions
- **Retryable Error Detection**: Configurable error message matching (database is locked/busy)

#### Phase 3: Repository Layer Enhancement
- **QueryBuilder**: Django-style chainable API (filter/exclude/order_by/limit/offset/only)
- **Immutable Cloning**: Each chained call returns new QueryBuilder instance
- **Parameterized Queries**: All queries use `?` placeholders, SQL-injection safe
- **Batch INSERT Optimization**: `add_batch()` with batched VALUES clauses (5-10x faster)
- **BaseRepository.query()**: Generic query method accepting QueryBuilder instances

#### Phase 4: MigrationManager Enhancement
- **External Migration Files**: `load_external_migrations()` from `migrations/` directory
- **MigrationResult Dataclass**: Track success/failure with duration_ms per migration
- **Enhanced Logging**: Per-migration timing and status reporting
- **Migration.source Field**: Distinguish 'builtin' vs 'external' migrations

#### Phase 5: Session Interface Unification
- **Session Class**: Unified database session interface (query/transaction/read_only/execute)
- **Public acquire()/release()**: ConnectionManager public API replacing _acquire()/_release()
- **UnifiedDB.session Property**: Single entry point for all database access
- **_get_connection() Delegation**: V1 compat layer delegates through Session

### Changed
- **ConnectionManager**: 254→640 lines (dynamic pool, metrics, WAL checkpoint)
- **TransactionManager**: 219→364 lines (retry, thread-local, read-only separation)
- **MigrationManager**: 405→500 lines (external files, result tracking)
- **BaseRepository**: Added `query()` method and batch VALUES optimization
- **UnifiedDB**: Added `session` property, `_get_connection()` delegates to Session
- **Test Coverage**: Expanded from 536 to 568 tests (32 new Phase 5 tests)

### Fixed
- `_get_connection()` missing auto-commit on exit — data loss prevention
- `sqlite_storage.py` `_get_connection()` missing commit/rollback handling
- WAL checkpoint using pool connections — now uses independent temporary connection
- Thread-local `getattr` without defaults — `AttributeError` prevention
- `QueryBuilder` missing from `core/__init__.py` exports
- `RetryConfig` missing from `core/__init__.py` exports
- `core/__init__.py` V1 backup import referencing moved `unified_db_v1_backup`

### New Files
- `quickagents/core/session.py` (190 lines) — Session unified interface
- `quickagents/core/repositories/query_builder.py` (463 lines) — Django-style query builder
- `tests/test_phase3_repo_upgrade.py` (48 tests) — Repository/QueryBuilder tests
- `tests/test_phase4_migration_upgrade.py` (26 tests) — MigrationManager tests
- `tests/test_phase5_session_unification.py` (32 tests) — Session tests

## [2.7.0] - 2026-03-31

### Added - UnifiedDB V2 Architecture

#### Core Components (Phase 1)
- **ConnectionManager**: Connection pool with WAL mode and thread safety (247 lines)
- **TransactionManager**: ACID transactions with nested SAVEPOINT support (219 lines)
- **MigrationManager**: Schema version management with checksum verification (405 lines)

#### Repository Layer (Phase 2)
- **BaseRepository**: Generic CRUD operations base class (422 lines)
- **Models**: Memory, Task, Progress, Feedback entities with dataclasses (282 lines)
- **MemoryRepository**: Factual/Experiential/Working memory operations (528 lines)
- **TaskRepository**: Task lifecycle management (457 lines)
- **ProgressRepository**: Project progress tracking (271 lines)
- **FeedbackRepository**: Experience collection (274 lines)

#### Unified API (Phase 3)
- **UnifiedDB Facade**: Single entry point for all database operations (737 lines)
- **V1 Compatibility Layer**: `_get_connection()` and `_execute_sql()` for backward compatibility

### Changed
- **Architecture**: Migrated from monolithic to layered architecture
  - V1: Single 841-line file → V2: 7 modular files (~3,500 lines total)
- **Test Coverage**: Expanded from 254 to 336 tests (100% pass rate)
- **Evolution Integration**: Fixed API mismatches between SkillEvolution and UnifiedDB V2
- **Knowledge Graph Integration**: Fixed Windows temp file handling for integration tests

### Fixed
- **Windows Temp Files**: Proper database connection cleanup with context managers
- **Global Instance Tests**: Added `reset_evolution()` for test isolation
- **API Compatibility**: All V1 API methods work correctly with V2 implementation

### Architecture Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                    UnifiedDB V2 Architecture                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │              UnifiedDB (Facade)                      │   │
│   │  - set_memory() / get_memory() / search_memory()    │   │
│   │  - add_task() / update_task_status()                │   │
│   │  - init_progress() / update_progress()              │   │
│   │  - add_feedback() / get_feedbacks()                 │   │
│   └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│   ┌──────────────────────┴──────────────────────────┐       │
│   │              Repository Layer                    │       │
│   ├─────────────────────────────────────────────────┤       │
│   │  MemoryRepo  │  TaskRepo  │  ProgressRepo  │ FeedbackRepo │
│   └─────────────────────────────────────────────────┘       │
│                          │                                  │
│   ┌──────────────────────┴──────────────────────────┐       │
│   │              Core Components                     │       │
│   ├─────────────────────────────────────────────────┤       │
│   │  ConnectionManager │ TransactionManager │ MigrationManager │
│   └─────────────────────────────────────────────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Test Results
| Test Suite | Total | Passed | Failed |
|------------|-------|--------|--------|
| V2 Phase 1-3 | 98 | 98 | 0 |
| Evolution | 34 | 34 | 0 |
| Knowledge Graph | 204 | 204 | 0 |
| **Total** | **336** | **336** | **0** |

## [2.6.8] - 2026-03-30

### Added
- **Bilingual Documentation**: Full Chinese and English documentation support
- **Comprehensive README**: Complete project documentation with examples
- **Pattern-based LoopDetector**: Replaced simple threshold with intelligent pattern detection
  - Stuck pattern detection (A→A→A)
  - Oscillation pattern detection (A→B→A→B)
- **Python Environment Detection**: Step 0 in startup flow checks Python >= 3.9
- **Installation Guidance**: Platform-specific Python installation instructions

### Changed
- **Unified Version**: All version numbers synchronized to 2.6.8
- **Plugin Architecture**: Updated to v2.6.8 with enhanced loop detection
- **Documentation Structure**: Reorganized for better GitHub presentation

### Fixed
- **Glob Bug**: Fixed null check in LocalExecutor.glob function
- **Duplicate Code**: Removed duplicate glob interception logic
- **Package.json Format**: Fixed repository field indentation

### Improved
- **Token Savings**: Estimated 60-100% reduction in various scenarios
- **Code Quality**: All Python syntax checks pass, 254 tests passing
- **Agent Configuration**: All 15 agent files validated
- **Skill Configuration**: All 24 skill files have valid YAML front matter

## [2.3.0] - 2026-03-26

### Added
- **SkillEvolution**: Unified self-evolution system with automatic triggers
- **GitHooks**: Automatic evolution analysis on git commits
- **KnowledgeGraph**: Complete knowledge graph implementation
  - Node types: REQUIREMENT, DECISION, FEATURE, etc.
  - Edge types: TRACES_TO, IMPLEMENTS, DEPENDS_ON, etc.
  - Search, trace, and discovery capabilities
- **Browser Automation**: Playwright-based browser automation
- **SQLite Primary Storage**: Unified database architecture

### Changed
- **Architecture Migration**: Moved from Markdown to SQLite as primary storage
- **Token Optimization**: 60%+ savings with SQLite queries
- **CLI Tools**: Enhanced with knowledge graph commands

### Fixed
- **Cross-session Memory**: SQLite ensures reliable context preservation
- **Query Performance**: Efficient indexed queries

## [2.2.0] - 2026-03-25

### Added
- **FileManager Cache**: Hash-based file caching (60-100% token savings)
- **LoopDetector**: Basic loop detection (3 identical calls in 60s)
- **LocalExecutor**: Local execution for qa/grep/glob commands
- **Unified Plugin**: Single @coder-beam/quickagents plugin

### Changed
- **Plugin Consolidation**: Merged Superpowers functionality into QuickAgents
- **Token Savings**: Massive reduction in file operation tokens

### Removed
- **Superpowers Dependency**: No longer needed, functionality integrated

## [2.1.0] - 2026-03-24

### Added
- **MarkdownSync**: Auto-sync SQLite to Markdown files
- **Reminder**: Event-driven reminders for long-running sessions
- **FeedbackCollector**: Automatic experience collection

### Changed
- **Storage Strategy**: Dual storage (SQLite + Markdown)

## [2.0.0] - 2026-03-22

### Added
- **Initial Release**: Core QuickAgents functionality
- **UnifiedDB**: Three-dimensional memory system
- **CLI Tools**: Basic command-line interface
- **Agent System**: 15 specialized agents
- **Skills System**: 24 skill modules

### Core Features
- Factual/Experiential/Working memory types
- Task management with priorities
- Progress tracking
- Decision logging
- Git integration

## [1.0.0] - 2026-03-20

### Added
- **Project Initialization**: Basic project setup
- **Documentation Generation**: Auto-generate AGENTS.md
- **Memory System**: Initial memory implementation

---

## Version Naming Convention

- **Major (X.0.0)**: Breaking changes, architecture overhaul
- **Minor (0.X.0)**: New features, significant improvements
- **Patch (0.0.X)**: Bug fixes, minor improvements

## Upgrade Guide

### From 2.3.0 to 2.6.8

1. Update package: `pip install --upgrade quickagents`
2. No breaking changes in API
3. New pattern-based loop detection is automatic
4. Python 3.9+ required (was 3.8+)

### From 2.2.0 to 2.3.0

1. Update package: `pip install --upgrade quickagents`
2. Run migration: `qa migrate` (if prompted)
3. Install Git hooks: `qa hooks install`

### From 2.x to 2.3.0

1. Backup data: `cp -r .quickagents .quickagents.backup`
2. Update package: `pip install --upgrade quickagents`
3. Initialize new structure: `qa init`
4. Restore data if needed

---

For more details, see the [GitHub Releases](https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/releases) page.
