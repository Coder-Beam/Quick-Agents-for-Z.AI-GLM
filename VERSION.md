# QuickAgents Version

> Version information file - for version detection and updates | 版本信息文件 - 用于版本检测和更新

---

## Current Version | 当前版本

| Property | Value |
|-----------|-------|
| Version | 2.6.8 |
| Git Tag | v2.6.8 |
| Release Date | 2026-03-30 |
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

## What's New (v2.6.8) | 本次更新

**Major Update - Complete Documentation, Pattern Detection & Bilingual Support**

**重大更新 - 完整文档、模式检测与双语支持**

---

### 1. Pattern-based LoopDetector | 基于模式的循环检测器

**Problem Solved | 解决的问题:**
- Previous: Simple threshold (3 identical calls in 60s)
- Previous: 之前：简单阈值（60秒内3次相同调用）
- Now: Intelligent pattern detection
- Now: 现在：智能模式检测

**Detection Patterns | 检测模式:**

| Pattern | Definition | Example | Threshold |
|---------|------------|---------|-----------|
| **Stuck** | Same operation repeated | A→A→A | 3 times |
| **Oscillation** | Two operations alternating | A→B→A→B | 2 cycles |

**Allowed Patterns | 允许的模式:**
- A→B→C (normal exploration, different operations)
- A→B→C（正常探索，不同操作）
- read(file1)→read(file2)→read(file3) (different parameters)
- read(file1)→read(file2)→read(file3)（不同参数）

**Implementation | 实现:**
```python
from quickagents import LoopDetector

detector = LoopDetector()

# Record tool calls
detector.record_tool_call('read', {'file': 'a.py'})
detector.record_tool_call('read', {'file': 'a.py'})
detector.record_tool_call('read', {'file': 'a.py'})

# Check if looping
if detector.is_looping():
    patterns = detector.get_loop_patterns()
    # patterns: [{'type': 'stuck', 'tool': 'read', 'count': 3}]
```

**Token Savings | Token节省:** 100% (local processing)

---

### 2. Python Environment Detection | Python环境检测

**Step 0 in Startup Flow | 启动流程Step 0:**

```
启动QuickAgent
    ↓
Step 0: Python环境检测
    ├─ 检测 python --version / python3 --version
    ├─ 检测 pip --version / pip3 --version
    └─ 检测 Python版本 >= 3.9
        ├─ 通过 → 继续流程
        └─ 失败 → 显示安装引导
```

**Version Requirements | 版本要求:**

| Component | Minimum | Recommended | Reason |
|-----------|---------|-------------|--------|
| Python | 3.9 | 3.11+ | Uses match syntax |
| pip | 21.0 | Latest | Dependency resolution |

**Platform-specific Guides | 各平台安装指南:**

<details>
<summary>Windows</summary>

```powershell
# Option 1 - Official Installer (Recommended)
# 1. Visit https://www.python.org/downloads/
# 2. Download Python 3.12.x
# 3. Check "Add Python to PATH" during installation

# Option 2 - Scoop
scoop install python

# Option 3 - winget
winget install Python.Python.3.12
```
</details>

<details>
<summary>macOS</summary>

```bash
# Option 1 - Homebrew (Recommended)
brew install python@3.12

# Option 2 - Official Installer
# Visit https://www.python.org/downloads/macos/
```
</details>

<details>
<summary>Linux</summary>

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install python3.12 python3-pip

# Fedora/RHEL
sudo dnf install python3.12 python3-pip

# Arch Linux
sudo pacman -S python python-pip
```
</details>

---

### 3. Bilingual Documentation | 双语文档

**Complete Chinese and English Support | 完整的中英文支持:**

| Document | Chinese | English |
|----------|---------|---------|
| README.md | ✅ | ✅ |
| CHANGELOG.md | ✅ | ✅ |
| Installation Guide | ✅ | ✅ |
| API Documentation | ✅ | ✅ |

**README.md Structure | README.md结构:**
- Project Overview | 项目概述
- Core Features | 核心功能
- Installation | 安装
- CLI Commands | CLI命令
- Architecture | 架构
- Module Description | 模块说明
- Testing | 测试
- Documentation | 文档
- Contributing | 贡献
- License | 许可证

---

### 4. Comprehensive API Documentation | 完整的API文档

**Location | 位置:** `Docs/api/index.md`

**Coverage | 覆盖范围:**

| Module | Functions/Classes | Status |
|--------|-------------------|--------|
| UnifiedDB | 15+ methods | ✅ Documented |
| SkillEvolution | 10+ methods | ✅ Documented |
| MarkdownSync | 8+ methods | ✅ Documented |
| FileManager | 6+ methods | ✅ Documented |
| LoopDetector | 5+ methods | ✅ Documented |
| Reminder | 4+ methods | ✅ Documented |
| KnowledgeGraph | 20+ methods | ✅ Documented |
| TDDWorkflow | 8+ methods | ✅ Documented |
| GitCommit | 6+ methods | ✅ Documented |
| FeedbackCollector | 6+ methods | ✅ Documented |
| Browser | 10+ methods | ✅ Documented |
| CLI Tools | 30+ commands | ✅ Documented |

**Example API Documentation | API文档示例:**

```python
# UnifiedDB - Memory Operations
from quickagents import UnifiedDB, MemoryType

db = UnifiedDB('.quickagents/unified.db')

# Set memory
db.set_memory(
    key: str,
    value: Any,
    memory_type: MemoryType,
    category: Optional[str] = None,
    ttl: Optional[int] = None
) -> None

# Get memory
db.get_memory(key: str) -> Optional[Any]

# Search memory
db.search_memory(
    query: str,
    memory_type: Optional[MemoryType] = None,
    limit: int = 10
) -> List[Dict]
```

---

### 5. Author Unification | 作者统一

**Before | 之前:** Mixed (QuickAgents Team, Coder-Beam)

**After | 之后:** Unified to **Coder-Beam**

**Files Updated | 已更新文件:**

| File | Field | Value |
|------|-------|-------|
| pyproject.toml | authors | Coder-Beam |
| quickagents/__init__.py | __author__ | Coder-Beam |
| .opencode/plugins/package.json | author | Coder-Beam |
| README.md | Author | Coder-Beam |
| VERSION.md | Author | Coder-Beam |

---

### 6. Bug Fixes | Bug修复

| Bug | File | Fix |
|-----|------|-----|
| Glob null pointer | `.opencode/plugins/quickagents.ts` | Added null check for pattern parameter |
| Duplicate code | `.opencode/plugins/quickagents.ts` | Removed duplicate glob interception logic |
| Package.json formatting | `.opencode/plugins/package.json` | Fixed repository field indentation |
| Version inconsistency | Multiple files | Unified to 2.6.8 |

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
| Unit Tests | 100% | 254/254 passing |
| Integration Tests | 100% | All passing |
| Code Quality | 100% | All syntax checks pass |

**Test Command | 测试命令:**
```bash
pytest tests/ -v
# 254 passed in 9.58s
```

---

## Version History | 版本历史

### v2.6.8 (2026-03-30)
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

## Roadmap | 路线图

### v2.7.0 (Planned | 计划中)
- Multi-model routing enhancement
- Performance optimizations
- Additional language support

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

*QuickAgents v2.6.8 - Making AI agent development easier*

*QuickAgents v2.6.8 - 让AI代理开发更简单*
