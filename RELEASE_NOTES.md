# QuickAgents v2.6.8 Release Notes

> **Release Date**: 2026-03-30 | **Author**: Coder-Beam

[![Version](https://img.shields.io/badge/Version-2.6.8-green.svg)](https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/releases/tag/v2.6.8)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/Tests-254%20passing-brightgreen.svg)](https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM)

---

## 🎉 Overview

QuickAgents v2.6.8 is a **major documentation and quality release** that brings:

- ✅ **Pattern-based Loop Detection** - Intelligent stuck/oscillation detection
- ✅ **Python Environment Detection** - Automated Python 3.9+ verification
- ✅ **Complete Bilingual Documentation** - Full Chinese and English support
- ✅ **Comprehensive API Documentation** - All modules fully documented
- ✅ **Author Unification** - All files unified to Coder-Beam

---

## 🚀 Installation

### Quick Install

```bash
# Install from PyPI
pip install quickagents

# Verify installation
python -c "from quickagents import __version__; print(f'QuickAgents v{__version__}')"
```

### Full Installation (with Windows features)

```bash
pip install quickagents[full]
```

### Development Installation

```bash
git clone https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM.git
cd Quick-Agents-for-Z.AI-GLM
pip install -e .
```

---

## ✨ What's New

### 1. Pattern-based LoopDetector

**Before (v2.4.x):**
- Simple threshold: 3 identical calls in 60 seconds
- False positives on legitimate repeated operations
- No distinction between exploration and stuck patterns

**Now (v2.6.8):**
- **Stuck Pattern Detection**: A→A→A (3+ identical calls)
- **Oscillation Pattern Detection**: A→B→A→B (2+ cycles)
- **Intelligent Allowlist**: A→B→C (normal exploration allowed)

**Code Example:**
```python
from quickagents import LoopDetector

detector = LoopDetector()

# Record tool calls
detector.record_tool_call('read', {'file': 'auth.py'})
detector.record_tool_call('read', {'file': 'auth.py'})
detector.record_tool_call('read', {'file': 'auth.py'})

# Check if stuck
if detector.is_looping():
    patterns = detector.get_loop_patterns()
    print(f"Loop detected: {patterns}")
    # Output: [{'type': 'stuck', 'tool': 'read', 'count': 3}]
```

**Files Changed:**
- `.opencode/plugins/quickagents.ts` - New pattern detection logic
- `quickagents/core/loop_detector.py` - Enhanced detection

---

### 2. Python Environment Detection

**New Step 0 in Startup Flow:**

```
启动QuickAgent
    ↓
Step 0: Python环境检测（必需）
    ├─ 检测 python --version
    ├─ 检测 pip --version
    └─ 检测版本 >= 3.9
        ├─ 通过 → 继续流程
        └─ 失败 → 显示安装引导
```

**Platform-Specific Installation Guides:**

| Platform | Method | Command |
|----------|--------|---------|
| Windows | Official | Download from python.org |
| Windows | Scoop | `scoop install python` |
| Windows | winget | `winget install Python.Python.3.12` |
| macOS | Homebrew | `brew install python@3.12` |
| Linux (Ubuntu) | apt | `sudo apt install python3.12 python3-pip` |
| Linux (Fedora) | dnf | `sudo dnf install python3.12 python3-pip` |

**Files Changed:**
- `AGENTS.md` - Added Step 0: Python环境检测
- `.opencode/agents/yinglong-init.md` - Added Python detection flow
- `Docs/guide/installation.md` - Complete rewrite with Python detection

---

### 3. Complete Bilingual Documentation

**README.md:**
- Full Chinese and English versions
- Complete installation instructions
- All CLI commands documented
- Architecture diagrams
- Module descriptions

**CHANGELOG.md:**
- Version history from 1.0.0 to 2.6.8
- Upgrade guides
- Breaking changes documented

**API Documentation:**
- `Docs/api/index.md` - Complete API reference
- All modules: UnifiedDB, KnowledgeGraph, SkillEvolution, etc.
- Type definitions
- Usage examples

---

### 4. Author Unification

**Before:**
- `QuickAgents Team` in some files
- Inconsistent authorship

**Now:**
- All files unified to `Coder-Beam`
- Consistent branding

**Files Updated:**
| File | Before | After |
|------|--------|-------|
| `quickagents/__init__.py` | QuickAgents Team | Coder-Beam |
| `pyproject.toml` | QuickAgents Team | Coder-Beam |
| `README.md` | QuickAgents Team | Coder-Beam |
| `.opencode/skills/project-detector-skill/SKILL.md` | QuickAgents Team | Coder-Beam |

---

## 📊 Statistics

### Code Quality

| Metric | Status |
|--------|--------|
| Python Syntax | ✅ 100% passing |
| Type Hints | ✅ Complete |
| Docstrings | ✅ All modules |
| Code Style | ✅ PEP 8 compliant |

### Test Results

| Test Type | Count | Status |
|-----------|-------|--------|
| Unit Tests | 192 | ✅ Passing |
| Integration Tests | 42 | ✅ Passing |
| E2E Tests | 20 | ✅ Passing |
| **Total** | **254** | **✅ 100%** |

### Token Savings

| Scenario | Savings |
|----------|---------|
| File operations (cached) | 100% |
| File operations (uncached) | 60-80% |
| Search operations | 80-95% |
| Memory/Knowledge queries | 90-100% |
| **Average** | **60-80%** |

---

## 🐛 Bug Fixes

### Critical Fixes

1. **Glob Null Check Bug**
   - **Issue**: `LocalExecutor.glob()` crashed when pattern was undefined
   - **Fix**: Added null check before processing
   - **File**: `.opencode/plugins/quickagents.ts:418-423`

2. **Duplicate Code in Plugin**
   - **Issue**: Glob interception logic duplicated (lines 562-593)
   - **Fix**: Removed duplicate code block
   - **File**: `.opencode/plugins/quickagents.ts`

3. **Package.json Formatting**
   - **Issue**: Repository field had incorrect indentation
   - **Fix**: Corrected JSON formatting
   - **File**: `.opencode/plugins/package.json`

### Minor Fixes

- Fixed 24 SKILL.md files missing YAML front matter
- Fixed plugin version mismatch (2.2.0 → 2.6.8)
- Fixed installation guide referencing non-existent `qa init` command

---

## 📦 Package Contents

### Python Modules

```
quickagents/
├── __init__.py              # Main exports
├── cli/
│   ├── main.py              # CLI implementation
│   └── qa.py                # Entry point
├── core/
│   ├── unified_db.py        # Unified database
│   ├── evolution.py         # Skill evolution
│   ├── git_hooks.py         # Git integration
│   ├── markdown_sync.py     # Markdown sync
│   ├── file_manager.py      # File operations
│   ├── loop_detector.py     # Loop detection
│   ├── reminder.py          # Event reminders
│   ├── cache_db.py          # Caching
│   └── memory.py            # Memory management
├── knowledge_graph/
│   ├── knowledge_graph.py   # Knowledge graph facade
│   ├── types.py             # Type definitions
│   ├── interfaces.py        # Abstract interfaces
│   ├── exceptions.py        # Custom exceptions
│   ├── core/
│   │   ├── node_manager.py
│   │   ├── edge_manager.py
│   │   ├── searcher.py
│   │   ├── discovery.py
│   │   ├── extractor.py
│   │   └── memory_sync.py
│   └── storage/
│       └── sqlite_storage.py
├── skills/
│   ├── feedback_collector.py
│   ├── tdd_workflow.py
│   └── git_commit.py
├── browser/
│   ├── browser.py           # Browser automation
│   └── installer.py         # Dependency installer
└── utils/
    ├── hash_cache.py
    └── script_helper.py
```

### OpenCode Configuration

```
.opencode/
├── plugins/
│   ├── quickagents.ts       # Unified plugin
│   └── package.json
├── agents/                  # 15 agent configs
├── skills/                  # 24 skill configs
├── config/
│   ├── models.json
│   ├── lsp-config.json
│   ├── categories.json
│   └── quickagents.json
├── commands/
│   ├── start-work.md
│   └── ultrawork.md
└── memory/
    ├── MEMORY.md
    ├── TASKS.md
    └── DECISIONS.md
```

---

## 🔧 CLI Commands

### Database Operations

```bash
qa stats                      # Show statistics
qa sync                       # Sync SQLite to Markdown
qa memory get <key>           # Get memory value
qa memory set <key> <value>   # Set memory value
qa memory search <query>      # Search memory
```

### Task Management

```bash
qa tasks list                 # List all tasks
qa tasks add <id> <name>      # Add new task
qa tasks status <id> <status> # Update task status
qa progress                   # Show current progress
```

### Evolution System

```bash
qa evolution status           # Show evolution status
qa evolution stats [skill]    # Skill usage statistics
qa evolution optimize         # Run periodic optimization
qa evolution history <skill>  # View skill evolution
```

### Git Integration

```bash
qa hooks install              # Install Git hooks
qa hooks status               # Check hooks status
qa git status                 # Git status
qa git check                  # Pre-commit checks
```

### TDD Workflow

```bash
qa tdd red <test_file>        # RED phase
qa tdd green <test_file>      # GREEN phase
qa tdd refactor <test_file>   # REFACTOR phase
qa tdd coverage               # Check coverage
```

---

## 📚 Documentation

### User Documentation

| Document | Location | Description |
|----------|----------|-------------|
| README.md | `/` | Complete project overview |
| CHANGELOG.md | `/` | Version history |
| VERSION.md | `/` | Version information |
| Installation Guide | `Docs/guide/installation.md` | Installation instructions |

### API Documentation

| Document | Location | Description |
|----------|----------|-------------|
| API Reference | `Docs/api/index.md` | Complete API docs |
| Architecture | `Docs/ARCHITECTURE.md` | System architecture |
| Plugin Guide | `Docs/plugins/` | Plugin documentation |

### Skills Documentation

- 24 skill files in `.opencode/skills/`
- Each with complete YAML front matter
- Usage examples and configuration

---

## 🔄 Upgrade Guide

### From v2.4.x to v2.6.8

```bash
# 1. Update Python package
pip install --upgrade quickagents

# 2. Verify version
python -c "from quickagents import __version__; print(__version__)"
# Output: 2.6.8

# 3. No breaking changes in API
# All existing code continues to work
```

### From v2.x to v2.6.8

```bash
# 1. Backup database
cp -r .quickagents .quickagents.backup

# 2. Update package
pip install --upgrade quickagents

# 3. Update OpenCode config (optional)
curl -fsSL https://codeload.github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/tar.gz/main | tar -xz --strip-components=1 Quick-Agents-for-Z.AI-GLM/.opencode
```

---

## 🗺️ What's Next

### v2.7.0 (Planned)

- Multi-model routing enhancement
- Performance optimizations
- Additional language support (Japanese, Korean)

### v3.0.0 (Planned)

- Plugin marketplace
- Custom skill creator
- Visual workflow builder
- Cloud sync capabilities

---

## 🤝 Contributing

Contributions are welcome! Please see:

- **Contributing Guide**: [CONTRIBUTING.md](CONTRIBUTING.md)
- **Code of Conduct**: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- **Issue Tracker**: [GitHub Issues](https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/issues)

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

Special thanks to:

- OpenCode community
- All contributors and testers
- Projects that inspired QuickAgents:
  - [Oh-My-OpenAgent](https://github.com/anthropics/anthropic-quickstarts/tree/main/agents/oh-my-openagent)
  - OpenDev paper (arXiv:2603.05344v2)
  - VeRO paper (arXiv:2602.22480)
  - SWE-agent paper

---

## 📞 Support

- **GitHub**: https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM
- **Issues**: https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/issues
- **PyPI**: https://pypi.org/project/quickagents/
- **Documentation**: https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/tree/main/Docs

---

**Full Changelog**: https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/compare/v2.4.0...v2.6.8

---

*QuickAgents v2.6.8 - Making AI agent development easier*
*Released with ❤️ by Coder-Beam*
