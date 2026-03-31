# Changelog

All notable changes to QuickAgents will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
