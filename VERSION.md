# QuickAgents Version

> Version information file - for version detection and updates | 版本信息文件 - 用于版本检测和更新

---

## Current Version | 当前版本

| Property | Value |
|-----------|-------|
| Version | 2.8.1 |
| Git Tag | v2.8.1 |
| Release Date | 2026-04-04 |
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

## What's New (v2.8.1) | 本次更新

**Document Understanding & Source Code Analysis — 文档理解与源码分析**

**三层管道：本地解析 → 交叉验证 → 知识提取**

---

### 1. Document Pipeline | 文档管道

**Supported Formats | 支持格式:**
- PDF (PyMuPDF + pdfplumber)
- Word (.docx via python-docx)
- Excel (.xlsx via openpyxl, formulas + requirement matrix detection)
- XMind / FreeMind (.mm) / OPML / Markdown outlines
- Source code: Python (ast), JS/TS/Java/Go/Rust/C/C++ (tree-sitter)

```bash
# Import all documents from PALs/ directory
qka import PALs/

# Include source code analysis
qka import PALs/ --with-source

# Preview without processing
qka import PALs/ --dry-run
```

---

### 2. Three-Level Trace Matching | 三级追踪匹配

- **L1 Convention**: REQ-ID, feature tags, section numbers (confidence: 1.0)
- **L2 Keyword**: Synonym table (45+ bilingual pairs), Chinese bigram tokenization (confidence: 0.7-0.9)
- **L3 Semantic**: LLM or Jaccard+synonym heuristic matching (confidence: 0.6+)

Output: Trace matrix + diff report + fix suggestions

---

### 3. Knowledge Extraction | 知识提取

Automatic extraction from documents:
- Functional / non-functional requirements
- Technical decisions
- Business facts and constraints
- Tech-stack and concepts

---

### 4. Storage | 存储

- Knowledge Graph: 10+ NodeType, 15+ EdgeType
- FTS5 full-text search
- Markdown export: trace matrix, coverage, diff reports
- `Docs/PALs/` output directory

---

### 5. Optional Dependencies | 可选依赖

```bash
# Document parsing
pip install quickagents[document]

# Source code analysis
pip install quickagents[source-code]

# OCR (scanned PDFs)
pip install quickagents[ocr]

# Everything
pip install quickagents[full]
```

---

### Module Overview | 模块概览

| Module | Function | Status |
|--------|----------|--------|
| DocumentPipeline | Three-layer pipeline orchestration | New |
| Parsers (7) | PDF/Word/Excel/XMind/FreeMind/OPML/MD | New |
| SourceCodeParser | Python ast + tree-sitter | New |
| TraceMatchEngine | Three-level matching | New |
| CrossValidator | Layer 2 cross-validation | New |
| KnowledgeExtractor | Layer 3 extraction | New |
| KnowledgeSaver | KG node+edge persistence | New |
| MarkdownExporter | MD report generation | New |

---

## Test Results | 测试结果

| Test Type | Pass Rate | Details |
|-----------|-----------|---------|
| Unit Tests | 100% | 340/340 document tests passing |
| Integration Tests | 100% | All passing, 580+ total |
| Code Quality | 100% | All syntax checks pass |

**Test Command | 测试命令:**
```bash
pytest tests/ -v
# 580 passed in 23.24s
```

---

## Version History | 版本历史

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
- Git commit enforcement: export requires clean working tree
- `.gitignore` injection: `qka export --inject-gitignore`
- 580 tests all passing

### v2.7.6 (2026-04-01)
- Core architecture upgrade: 6-phase enhancement
- `qka uninstall` command (superseded by v2.7.8)

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

*QuickAgents v2.8.0 - Making AI agent development easier*

*QuickAgents v2.8.0 - 让AI代理开发更简单*
