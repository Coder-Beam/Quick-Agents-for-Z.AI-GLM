# Document Understanding Module — 完整提取与跨项目复用方案

> **版本**: v2.8.0 | **源项目**: QuickAgents | **许可证**: MIT
> **作者**: Coder-Beam | **适用**: Python 3.9+

---

## 一、模块概述

### 1.1 功能定位

Document Understanding Module 是一个**三层文档理解与需求追溯引擎**，能够：

1. **解析** 8 种文档格式（PDF / Word / Excel / XMind / FreeMind / OPML / Markdown / 源代码）
2. **交叉引用** 文档需求与源代码实现，生成需求追溯矩阵
3. **交叉验证** 解析结果的一致性与完整性
4. **提取知识** 从文档中提取需求、决策、事实、技术栈等结构化知识
5. **导出报告** 生成 Markdown 格式的追溯矩阵、覆盖率报告、差异报告

### 1.2 核心架构

```
┌──────────────────────────────────────────────────────────────────────┐
│                    三层处理流水线 (Three-Layer Pipeline)               │
│                                                                      │
│  Layer 1: 本地解析                                                    │
│  ├── 7 个文档解析器 (PDF/Word/Excel/XMind/FreeMind/OPML/Markdown)    │
│  └── 1 个源码解析器 (Python AST + Tree-sitter + Regex Fallback)      │
│       ↓ DocumentResult / SourceCodeResult                            │
│                                                                      │
│  Layer 1.5: 联合分析 (交叉引用)                                       │
│  ├── L1 约定匹配 (REQ-ID / Feature-tag / Section-number)             │
│  ├── L2 关键词匹配 (双语同义词表 + 中文二元语法)                      │
│  └── L3 语义匹配 (LLM / Jaccard + 同义词启发式)                      │
│       ↓ CrossReferenceResult (Trace Matrix + Coverage + Diff)        │
│                                                                      │
│  Layer 2: 交叉验证                                                    │
│  ├── 文档 vs 源码一致性检查                                           │
│  ├── 内部一致性检查 (空内容 / 孤立章节 / 重复表格)                    │
│  └── 外部读取校验 (可选)                                              │
│       ↓ RefinedDocumentResult (corrections + supplements)            │
│                                                                      │
│  Layer 3: 深度分析 (知识提取)                                          │
│  ├── 需求提取 (功能性 / 非功能性 / 约束)                              │
│  ├── 决策提取 (技术选型 / 架构决策)                                   │
│  ├── 事实提取 (技术栈 / 数据模型 / 业务规则)                          │
│  └── LLM 深度提取 (可选)                                              │
│       ↓ KnowledgeExtractionResult                                    │
│                                                                      │
│  Storage Layer:                                                      │
│  ├── KnowledgeSaver → Knowledge Graph (节点 + 边)                    │
│  ├── MarkdownExporter → Markdown 报告                                │
│  └── ResultCache → 内存缓存 (TTL + 哈希验证)                         │
│                                                                      │
│  Review Flow:                                                        │
│  └── ReviewSession → 用户确认/拒绝/修改分析结果                       │
└──────────────────────────────────────────────────────────────────────┘
```

### 1.3 代码规模

| 组件 | 文件数 | 代码行数(约) | 职责 |
|------|--------|-------------|------|
| `models.py` | 1 | 1114 | 全部数据模型 |
| `parsers/` | 9 | ~2600 | 文档+源码解析 |
| `matching/` | 7 | ~2100 | 三级匹配引擎 |
| `storage/` | 3 | ~540 | 知识图谱+导出+缓存 |
| `validators/` | 4 | ~1300 | 交叉验证+知识提取 |
| `pipeline.py` | 1 | ~270 | 流水线控制器 |
| **总计** | **25** | **~7900** | — |

---

## 二、目录结构与文件清单

```
document/
├── __init__.py                    # 公开 API 导出
├── models.py                      # 全部数据模型 (1114 行)
├── pipeline.py                    # DocumentPipeline 三层控制器
│
├── parsers/                       # Layer 1: 解析器
│   ├── __init__.py                # BaseParser + ParserRegistry + 依赖检查
│   ├── utils.py                   # 共享: find_parent_id, build_structure_tree_stack, build_tree_by_parent_id
│   ├── pdf_parser.py              # PyMuPDF + pdfplumber 备选
│   ├── word_parser.py             # python-docx
│   ├── excel_parser.py            # openpyxl + 公式 + 需求矩阵检测
│   ├── xmind_parser.py            # XMind 脑图
│   ├── freemind_parser.py         # FreeMind (.mm)
│   ├── opml_parser.py             # OPML 大纲
│   ├── markdown_parser.py         # Markdown
│   └── source_code_parser.py      # Python ast + tree-sitter + regex 备选
│
├── matching/                      # Layer 1.5: 联合分析
│   ├── __init__.py                # 公开 API
│   ├── synonym_table.py           # 45+ 双语同义词对 (中↔英)
│   ├── convention_matcher.py      # L1: 结构化约定匹配
│   ├── keyword_matcher.py         # L2: 同义词+关键词匹配
│   ├── semantic_matcher.py        # L3: LLM / 启发式语义匹配
│   ├── diff_analyzer.py           # 差异检测 (gap/extra/inconsistency)
│   ├── fix_suggester.py           # 修正建议 (以文档为准/以代码为准)
│   ├── granularity.py             # 粒度调整 (合并/拆分/增删追踪条目)
│   └── trace_engine.py            # 三级匹配引擎协调器
│
├── storage/                       # Storage Layer
│   ├── __init__.py                # 公开 API
│   ├── knowledge_saver.py         # DocumentResult/SourceCodeResult → Knowledge Graph
│   ├── markdown_exporter.py       # 追溯矩阵/覆盖率/差异/摘要 → Markdown
│   └── result_cache.py            # 内存缓存 (TTL + 哈希验证 + 淘汰)
│
├── validators/                    # Layer 2+3: 验证与提取
│   ├── __init__.py                # 公开 API
│   ├── cross_validator.py         # Layer 2: 交叉验证
│   ├── knowledge_extractor.py     # Layer 3: 知识提取
│   ├── layer_diff.py              # 三层 Diff + 合并
│   └── review_flow.py             # 用户审查确认流程
│
├── extractors/                    # (预留) 自定义提取器
│   └── __init__.py
│
├── ocr/                           # (预留) OCR 支持
│   └── __init__.py
│
└── tests/                         # 340 个测试
    ├── test_phase1.py             # 13 tests (架构+数据模型)
    ├── test_pdf_parser.py         # 29 tests
    ├── test_mindmap_parsers.py    # 57 tests (XMind+FreeMind+OPML+MD)
    ├── test_word_parser.py        # 30 tests
    ├── test_excel_parser.py       # 49 tests
    ├── test_source_code_parser.py # 46 tests
    ├── test_matching.py           # 41 tests
    ├── test_storage.py            # 37 tests
    ├── test_pipeline_integration.py # 38 tests
    └── fixtures/                  # 测试样本文件
        ├── test_sample.pdf
        ├── test_sample.docx
        ├── test_sample.xlsx
        ├── test_sample.xmind
        ├── test_sample.mm
        ├── test_sample.opml
        ├── test_sample.md
        └── source_sample/
            ├── auth.py
            ├── utils.py
            ├── config.json
            └── service/login.js
```

---

## 三、依赖关系

### 3.1 核心依赖 (必须)

| 包 | 用途 | 安装命令 |
|----|------|---------|
| Python >= 3.9 | 运行时 | — |

### 3.2 文档解析依赖 (可选, 按需安装)

| 包 | 版本 | 用途 | pip 安装 |
|----|------|------|---------|
| PyMuPDF | latest | PDF 解析 (fitz) | `pip install PyMuPDF` |
| pdfplumber | latest | PDF 表格提取备选 | `pip install pdfplumber` |
| python-docx | latest | Word (.docx) 解析 | `pip install python-docx` |
| openpyxl | latest | Excel (.xlsx) 解析 | `pip install openpyxl` |
| xmind | latest | XMind 脑图解析 | `pip install xmind` |
| tree-sitter | >= 0.23.0 | 多语言源码解析 | `pip install tree-sitter>=0.23.0` |

### 3.3 一键安装

```bash
# 文档解析完整安装
pip install PyMuPDF pdfplumber python-docx openpyxl xmind

# 源码解析 (可选, 支持 JS/TS/Java/Go/Rust/C/C++)
pip install tree-sitter>=0.23.0

# 一键全部安装
pip install PyMuPDF pdfplumber python-docx openpyxl xmind tree-sitter>=0.23.0
```

### 3.4 依赖降级策略

模块采用**优雅降级**设计：

- **PDF**: PyMuPDF 优先 → pdfplumber 备选
- **源码**: Python `ast` 模块（内置，用于 .py）→ tree-sitter（可选，多语言）→ 正则表达式（兜底）
- **缺失依赖时不报错**：解析器注册时跳过，`check_dependencies()` 返回 False，并提供安装提示

---

## 四、数据模型详解

### 4.1 模型层次图

```
DocumentResult (Layer 1 输出)
├── DocumentSection[]      # 章节树 (带层级、父子关系)
├── DocumentTable[]        # 表格 (带表头、行数据、Markdown转换)
├── DocumentImage[]        # 图片
├── DocumentFormula[]      # 公式 (Excel公式，带单元格引用和依赖)
├── structure_tree: Dict   # 嵌套结构树
├── metadata: Dict         # 文件元数据 (大小、哈希、作者、时间)
├── raw_text: str          # 原始文本
└── errors: List[str]      # 解析错误

SourceCodeResult (Layer 1 输出)
├── CodeModule[]           # 模块/文件
│   ├── CodeClass[]        # 类
│   │   ├── CodeFunction[] # 方法
│   │   └── attributes[]   # 类属性
│   ├── CodeFunction[]     # 顶层函数
│   ├── imports[]          # 导入声明
│   └── variables[]        # 模块级变量
├── CodeDependency[]       # 模块间依赖 (import/inheritance/call)
├── structure_tree: Dict   # 目录结构树
├── stats: Dict            # 统计 (文件数、LOC、函数数、类数、语言分布)
└── raw_text: Dict[str,str]# 文件路径 → 源码内容

CrossReferenceResult (Layer 1.5 输出)
├── TraceEntry[]           # 追踪矩阵 (需求→实现)
├── DiffEntry[]            # 差异报告 (gap/extra/inconsistency)
├── coverage_report: Dict  # 覆盖率统计
├── unmatched_reqs[]       # 未匹配需求
└── unmatched_code[]       # 未匹配代码

RefinedDocumentResult extends DocumentResult (Layer 2 输出)
├── corrections[]          # 修正项
├── supplements[]          # 补充项
└── confidence: float      # 置信度

KnowledgeExtractionResult (Layer 3 输出)
├── ExtractedRequirement[] # 提取的需求 (functional/non-functional/constraint)
├── ExtractedDecision[]    # 提取的决策 (技术选型/架构决策)
├── ExtractedFact[]        # 提取的事实 (技术栈/数据模型/业务规则)
├── concepts[]             # 概念
└── relationships[]        # 关系
```

### 4.2 关键模型字段说明

#### DocumentSection

| 字段 | 类型 | 说明 |
|------|------|------|
| section_id | str | 唯一标识 (如 "S001") |
| title | str | 章节标题 |
| level | int | 层级深度 (1=H1, 2=H2, ...) |
| page_number | int | 所在页码 |
| content | str | 章节正文内容 |
| parent_id | Optional[str] | 父章节 ID |
| children_ids | List[str] | 子章节 ID 列表 |

#### TraceEntry

| 字段 | 类型 | 说明 |
|------|------|------|
| trace_id | str | 唯一标识 (如 "TRACE-K001") |
| requirement | Optional[str] | 需求描述 |
| req_source | Optional[str] | 需求来源 (文档+章节) |
| implementation | Optional[str] | 实现描述 |
| impl_file | Optional[str] | 实现文件路径 |
| impl_function | Optional[str] | 实现函数名 |
| impl_lines | Optional[str] | 行范围 (如 "L15-42") |
| trace_type | str | 匹配方式 (convention/keyword/semantic) |
| confidence | float | 置信度 (0.0-1.0) |
| status | str | 状态 (covered/partial/uncovered/extra) |

#### CodeFunction

| 字段 | 类型 | 说明 |
|------|------|------|
| func_id | str | 唯一标识 |
| name | str | 函数名 |
| signature | str | 完整签名 |
| parameters | List[Dict] | 参数列表 (含类型) |
| return_type | Optional[str] | 返回类型 |
| docstring | Optional[str] | 文档字符串 |
| decorators | List[str] | 装饰器列表 |
| calls | List[str] | 调用的函数列表 |
| start_line / end_line | int | 起止行号 |

### 4.3 模型公共方法

所有模型均提供：
- `to_dict() -> Dict` — 序列化为字典
- `from_dict(data) -> Self` — 从字典反序列化
- `__repr__()` — 可读字符串表示
- `__eq__()` / `__hash__()` — 相等性与哈希

---

## 五、核心 API 使用指南

### 5.1 快速开始

```python
from pathlib import Path
from quickagents.document import DocumentPipeline

# 初始化流水线
pipeline = DocumentPipeline()

# ── 解析单个文档 ──
result = pipeline.parse(Path("requirements.docx"))
print(f"标题: {result.title}")
print(f"章节数: {len(result.sections)}")
print(f"表格数: {len(result.tables)}")

# ── 解析源代码目录 ──
code = pipeline.parse_source(Path("src/"))
print(f"模块数: {len(code.modules)}")
print(f"总LOC: {code.stats['total_loc']}")

# ── 交叉引用 (文档 ↔ 源码) ──
docs = [pipeline.parse(Path(f)) for f in ["req.docx", "design.pdf"]]
xref = pipeline.cross_reference(docs, code)
print(f"追踪条目: {len(xref.trace_matrix)}")
print(f"覆盖率: {xref.coverage_report['rate']:.1%}")

# ── 交叉验证 ──
validated = pipeline.cross_validate(docs[0], code)
print(f"置信度: {validated.confidence}")
print(f"修正项: {len(validated.corrections)}")

# ── 知识提取 ──
knowledge = pipeline.extract_knowledge(docs, code)
for req in knowledge.requirements:
    print(f"[{req.req_type}] {req.title}")

# ── 导出 Markdown 报告 ──
from quickagents.document.storage import MarkdownExporter
exporter = MarkdownExporter()
report = exporter.export_full_report(xref, docs, code)
Path("trace_report.md").write_text(report, encoding="utf-8")
```

### 5.2 批量导入

```python
# 一键导入整个 PALs/ 目录
result = pipeline.import_all("PALs/", with_source=True)
# 自动扫描所有文档 + 源码，执行三层流水线
```

### 5.3 CLI 命令

```bash
# 扫描 PALs/ 目录并执行完整分析
qka import --with-source --verbose

# 仅解析，不做验证
qka import --no-validate --dry-run

# 指定输出目录
qka import --output Docs/PALs/
```

### 5.4 依赖检查

```python
from quickagents.document import check_dependencies, get_supported_formats

# 检查格式依赖是否满足
if check_dependencies("pdf"):
    print("PDF 解析可用")

# 获取支持的所有格式
print(get_supported_formats())
# ['pdf', 'docx', 'xlsx', 'xmind', 'mm', 'opml', 'md', 'py', 'js', 'ts', ...]
```

### 5.5 自定义解析器

```python
from pathlib import Path
from typing import List
from quickagents.document.parsers import BaseParser, ParserRegistry
from quickagents.document.models import DocumentResult

class CSVParser(BaseParser):
    SUPPORTED_FORMATS = ["csv"]
    REQUIRES_DEPENDENCIES = ["csv"]  # csv 是内置模块
    PARSER_NAME = "csv"

    def parse(self, file_path: Path) -> DocumentResult:
        import csv
        # ... 解析逻辑 ...
        return DocumentResult(
            source_file=str(file_path),
            source_format="csv",
            title=file_path.stem,
            # ...
        )

# 注册自定义解析器
registry = ParserRegistry()
registry.register("csv", CSVParser())
```

### 5.6 自定义同义词表

```python
from quickagents.document.matching import SynonymTable

table = SynonymTable()

# 添加自定义术语
table.add_synonym("发票", "invoice")
table.add_synonym("发票", "receipt")

# 批量添加
table.add_custom_terms({
    "发票": ["invoice", "receipt", "billing"],
    "退款": ["refund", "return", "cancel"],
})

# 查询同义词
print(table.lookup("认证"))
# ['auth', 'authenticate', 'authentication', 'login', 'signin']

# 计算匹配分数
score = table.match_score("认证", "authenticate_user")
# 0.8 (部分匹配)
```

### 5.7 用户审查流程

```python
from quickagents.document.validators import ReviewFlow, ReviewStatus

session = ReviewSession()
session.phase = "trace_review"

# 添加审查项
session.add_item("T001", "trace", "REQ-001 ↔ auth.py:login()", confidence=0.95)
session.add_item("T002", "trace", "REQ-002 ↔ auth.py:rbac_check()", confidence=0.6)

# 自动接受高置信度项
session.accept_auto(min_confidence=0.9)

# 手动审查
item = session.get_item("T002")
item.accept("确认匹配")          # 或 item.reject() / item.modify("新内容")

# 获取结果
print(session.summary())
print(session.is_complete())
results = session.get_results()
```

### 5.8 结果缓存

```python
from quickagents.document.storage import ResultCache

cache = ResultCache(max_size=100, ttl_seconds=3600)

# 缓存结果
file_hash = cache.compute_hash("requirements.docx")
cache.put("req.docx", result, file_hash)

# 读取缓存 (文件未变化时命中)
cached = cache.get("req.docx", file_hash)
if cached:
    print("缓存命中")
```

---

## 六、各解析器详解

### 6.1 PDF 解析器 (`pdf_parser.py`)

**依赖**: PyMuPDF (fitz) + pdfplumber (备选)

**能力**:
- 文本提取 + 标题层级识别 (字体大小启发式)
- 页面分割 (每页独立处理)
- 哈希去重 (同一内容不重复输出)

**降级**: PyMuPDF 不可用时使用 pdfplumber

### 6.2 Word 解析器 (`word_parser.py`)

**依赖**: python-docx

**能力**:
- 章节树提取 (Heading 1-6 → level 1-6)
- 表格提取 (含表头、行数据、Markdown 转换)
- 段落文本提取
- 元数据提取 (作者、创建时间、修改时间)
- 图片检测 (含引用位置)

### 6.3 Excel 解析器 (`excel_parser.py`)

**依赖**: openpyxl

**能力**:
- 多 Sheet 解析 (每个 Sheet 为一个 Section)
- 表格提取 (含表头、行数据)
- **公式提取** — 识别 `=B2*C2`, `=SUM(D2:D4)` 等，解析公式类型和单元格依赖
- **需求矩阵检测** — 基于关键词评分 + REQ-ID 正则模式，自动识别含需求的 Sheet
- 文本段落检测 (非表格内容)

### 6.4 XMind 解析器 (`xmind_parser.py`)

**依赖**: xmind

**能力**:
- 多 Sheet 支持
- 递归展开主题树 (RootTopic → SubTopics)
- 标题层级映射 (depth → level)
- 备注/标签提取

### 6.5 FreeMind 解析器 (`freemind_parser.py`)

**依赖**: 无 (XML 标准库)

**能力**:
- XML 解析 `<map>` → `<node>` 递归
- 富文本节点提取 (`<richcontent>` 标签)
- 层级映射

### 6.6 OPML 解析器 (`opml_parser.py`)

**依赖**: 无 (XML 标准库)

**能力**:
- `<outline>` 递归解析
- `text` 属性提取
- 层级映射

### 6.7 Markdown 解析器 (`markdown_parser.py`)

**依赖**: 无 (正则表达式)

**能力**:
- `#` 标题层级识别 (H1-H6)
- 章节内容提取
- 父子关系构建

### 6.8 源码解析器 (`source_code_parser.py`)

**依赖**: Python `ast` (内置) + tree-sitter (可选)

**能力**:
- **Python (.py)**: `ast` 模块精确解析 — 类、函数、参数类型、返回类型、装饰器、调用关系、docstring、模块变量
- **JS/TS/Java/Go/Rust/C/C++**: tree-sitter (已安装时) → 正则表达式 (兜底)
- **JSON/YAML/TOML**: 配置文件解析
- **目录结构树**: 递归扫描文件树
- **依赖关系图**: 模块间 import/inheritance/call 依赖
- **统计**: 文件数、LOC、函数数、类数、语言分布

**自动跳过**: `__pycache__`, `.git`, `node_modules`, `venv`, `dist`, `build` 等目录

---

## 七、匹配引擎详解

### 7.1 三级匹配架构

```
输入: DocumentResult[] + SourceCodeResult
        │
        ▼
┌─────────────────────┐
│ L1: ConventionMatcher │  精确匹配，confidence = 1.0
│ - REQ-ID 匹配        │  如 "REQ-001" → @REQ-001 注解
│ - Feature-tag 匹配   │  如 "[AUTH]" → AuthModule
│ - Section-number 匹配│  如 "1.2.3" → section_1_2_3
└──────────┬──────────┘
           │ 未匹配的需求+代码
           ▼
┌─────────────────────┐
│ L2: KeywordMatcher   │  中等匹配，confidence = 0.7-0.9
│ - 同义词匹配         │  中文需求术语 ↔ 英文代码命名
│ - 关键词提取         │  中英文混合文本分词
│ - 中文二元语法       │  "用户认证" → ["用户", "户认", "认证"]
└──────────┬──────────┘
           │ 仍未匹配的
           ▼
┌─────────────────────┐
│ L3: SemanticMatcher  │  模糊匹配，confidence >= 0.6
│ - LLM 语义匹配      │  (有 LLM 时) 理解语义相似度
│ - Jaccard + 同义词   │  (无 LLM 时) 启发式相似度
└──────────┬──────────┘
           │
           ▼
  CrossReferenceResult
  ├── TraceEntry[]        所有匹配条目
  ├── DiffEntry[]         差异 (gap/extra/inconsistency)
  ├── coverage_report     覆盖率统计
  ├── unmatched_reqs[]    未匹配需求
  └── unmatched_code[]    未匹配代码
```

### 7.2 双语同义词表 (45+ 术语对)

内置中英双语同义词映射，覆盖常见业务领域：

| 中文 | 英文同义词 |
|------|-----------|
| 用户 | user, account, member, customer |
| 认证 | auth, authenticate, login, signin |
| 密码 | password, passwd, pwd, credential |
| 订单 | order, purchase, transaction |
| 支付 | payment, pay, checkout, billing |
| 权限 | permission, auth, acl, access |
| ... | ... |

支持自定义扩展：`table.add_synonym("发票", "invoice")`

### 7.3 差异分析

| 差异类型 | 含义 | 修正建议 |
|----------|------|---------|
| `gap` | 有需求无实现 | 以文档为准：建议补充代码实现 |
| `extra` | 有实现无文档 | 以代码为准：建议补充文档 |
| `inconsistency` | 文档与代码不一致 | 双向修正建议 |

---

## 八、存储层详解

### 8.1 KnowledgeSaver

将解析结果写入 Knowledge Graph（知识图谱）：

```python
from quickagents.document.storage import KnowledgeSaver

saver = KnowledgeSaver(kg)  # kg 是 KnowledgeGraph 实例

# 保存文档 → 节点+边
doc_ids = saver.save_document(doc_result)

# 保存源码 → 节点+边
code_ids = saver.save_source(code_result)

# 保存追踪关系 → 边
saver.save_traces(cross_ref, doc_ids, code_ids)
```

**节点类型**: DOCUMENT, SECTION, MODULE, FUNCTION
**边类型**: CONTAINS, IMPLEMENTS, MAPS_TO

### 8.2 MarkdownExporter

生成 6 种 Markdown 报告：

| 方法 | 输出 |
|------|------|
| `export_trace_matrix()` | 需求追踪矩阵表 |
| `export_coverage_report()` | 覆盖率统计报告 |
| `export_diff_report()` | 差异报告 (含修正建议) |
| `export_full_report()` | 完整报告 (以上三者合并) |
| `export_document_summary()` | 单文档摘要 |
| `export_source_overview()` | 源码概览 |

### 8.3 ResultCache

内存级缓存，避免重复解析：

- **TTL 过期**: 默认 1 小时
- **哈希验证**: 文件内容变化时自动失效
- **LRU 淘汰**: 超过 max_size 时淘汰最旧条目

---

## 九、跨项目集成方案

### 9.1 方案 A: 直接安装 quickagents

```bash
pip install quickagents[document]
```

优点：零配置，开箱即用
缺点：引入 quickagents 全部依赖

### 9.2 方案 B: 复制模块目录

将 `quickagents/document/` 整个目录复制到目标项目：

```
your_project/
└── document/              # 从 quickagents/document/ 复制
    ├── __init__.py
    ├── models.py
    ├── pipeline.py
    ├── parsers/
    ├── matching/
    ├── storage/
    └── validators/
```

需要修改导入路径：
- 所有 `from ..models import` → `from .models import`（如果在顶层）
- 或保持目录结构，在父级创建 `__init__.py`

**需要修改的文件清单**（导入路径调整）：

| 文件 | 原导入 | 改为 |
|------|--------|------|
| `parsers/__init__.py` | `from ..models import` | `from .models import` |
| `parsers/utils.py` | `from ..models import` | `from .models import` |
| `parsers/*.py` | `from ..models import` | `from .models import` |
| `matching/*.py` | `from ..models import` | `from .models import` |
| `storage/knowledge_saver.py` | `from ..models import` + `from quickagents.knowledge_graph...` | 需替换 KG 接口 |
| `validators/*.py` | `from ..models import` | `from .models import` |
| `pipeline.py` | `from .parsers import` + `from .matching import` + `from .validators import` | 保持不变 |

**KnowledgeSaver 的 Knowledge Graph 依赖**:

`knowledge_saver.py` 依赖 `quickagents.knowledge_graph.types` 中的 `NodeType` 和 `EdgeType`。如果目标项目没有 KG，有两个选择：

1. **不使用 KnowledgeSaver** — 只用 MarkdownExporter 导出报告
2. **实现简单适配器** — 只需实现 `create_node()` 和 `create_edge()` 方法

### 9.3 方案 C: 提取为独立 pip 包

将模块提取为独立包 `doc-understanding`：

```toml
# pyproject.toml
[project]
name = "doc-understanding"
version = "1.0.0"
requires-python = ">=3.9"
dependencies = []

[project.optional-dependencies]
document = ["PyMuPDF", "pdfplumber", "python-docx", "openpyxl", "xmind"]
source-code = ["tree-sitter>=0.23.0"]
all = ["PyMuPDF", "pdfplumber", "python-docx", "openpyxl", "xmind", "tree-sitter>=0.23.0"]
```

---

## 十、扩展开发指南

### 10.1 添加新文档格式解析器

```python
# 1. 创建 parsers/csv_parser.py
from pathlib import Path
from quickagents.document.parsers import BaseParser
from quickagents.document.models import DocumentResult, DocumentSection, DocumentTable

class CSVParser(BaseParser):
    SUPPORTED_FORMATS = ["csv"]
    REQUIRES_DEPENDENCIES = []  # csv 是内置模块
    PARSER_NAME = "csv"

    def parse(self, file_path: Path) -> DocumentResult:
        import csv
        sections = []
        tables = []

        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader, [])
            rows = list(reader)

        tables.append(DocumentTable(
            table_id="T001",
            page_number=1,
            headers=headers,
            rows=[row for row in rows],
        ))

        return DocumentResult(
            source_file=str(file_path),
            source_format="csv",
            title=file_path.stem,
            tables=tables,
            metadata=self._extract_metadata(file_path),
        )

# 2. 注册到 Pipeline
from quickagents.document import DocumentPipeline
pipeline = DocumentPipeline()
pipeline.registry.register("csv", CSVParser())

# 3. 使用
result = pipeline.parse(Path("data.csv"))
```

### 10.2 添加自定义匹配策略

```python
from quickagents.document.matching import TraceMatchEngine, SynonymTable

# 自定义同义词表
table = SynonymTable()
table.add_custom_terms({
    "发票": ["invoice", "receipt"],
    "退款": ["refund", "return"],
})

# 传入 LLM 函数用于语义匹配
def my_llm_func(prompt: str) -> str:
    # 调用你的 LLM
    return llm.generate(prompt)

engine = TraceMatchEngine(
    synonym_table=table,
    llm_func=my_llm_func,
)

result = engine.match(doc_results, code_result)
```

### 10.3 添加自定义知识提取

```python
from quickagents.document.validators import KnowledgeExtractor

# 传入自定义 LLM 函数
extractor = KnowledgeExtractor(llm_func=my_llm_func)
knowledge = extractor.extract(doc_results, code_result)
```

### 10.4 添加自定义导出格式

```python
from quickagents.document.storage.markdown_exporter import MarkdownExporter

class HTMLExporter(MarkdownExporter):
    def export_trace_matrix(self, result, **kwargs) -> str:
        # 覆写为 HTML 表格输出
        rows = []
        for t in result.trace_matrix:
            rows.append(f"<tr><td>{t.trace_id}</td><td>{t.requirement}</td>...</tr>")
        return "<table>" + "".join(rows) + "</table>"
```

---

## 十一、测试体系

### 11.1 测试覆盖

| 测试文件 | 测试数 | 覆盖范围 |
|----------|--------|---------|
| test_phase1.py | 13 | 架构 + 数据模型 + BaseParser + ParserRegistry |
| test_pdf_parser.py | 29 | PDF 解析 + 标题识别 + 元数据 |
| test_mindmap_parsers.py | 57 | XMind + FreeMind + OPML + Markdown |
| test_word_parser.py | 30 | Word 解析 + 表格 + 章节 + 元数据 |
| test_excel_parser.py | 49 | Excel + 公式 + 需求矩阵 + 多Sheet |
| test_source_code_parser.py | 46 | 源码解析 + AST + 类型注解 + 类继承 |
| test_matching.py | 41 | 三级匹配 + 同义词 + 差异分析 + 粒度调整 |
| test_storage.py | 37 | KnowledgeSaver + MarkdownExporter + ResultCache |
| test_pipeline_integration.py | 38 | 完整三层流水线集成 |
| **总计** | **340** | — |

### 11.2 运行测试

```bash
# 运行全部测试
pytest quickagents/document/tests/ -v

# 运行单个模块测试
pytest quickagents/document/tests/test_pdf_parser.py -v

# 运行并显示覆盖率
pytest quickagents/document/tests/ --cov=quickagents.document -v
```

---

## 十二、关键设计决策

| 编号 | 决策 | 原因 |
|------|------|------|
| D01 | 三层架构: 本地解析 → Agent 验证 → LLM 深度分析 | 逐层增强，每层可独立使用 |
| D02 | 存储分析结果，不存储原始文档 | 减少存储开销，保留结构化信息 |
| D03 | 统一中间表示 (DocumentResult) | 不同格式解析后归一化为相同结构 |
| D04 | 解析器注册表 + 自动发现 | 可扩展，新增格式无需修改核心代码 |
| D05 | 优雅降级 + 依赖缺失提示 | 不强制依赖，按需安装 |
| D06 | 三级匹配 (约定→关键词→语义) | 从精确到模糊，最大化匹配率 |
| D07 | Excel 公式解析 + 需求矩阵检测 | Excel 常用于需求管理 |
| D08 | 中英双语同义词表 | 适配中文需求文档 ↔ 英文代码 |
| D09 | Python ast + tree-sitter + regex 三级解析 | Python 精确，多语言可选，兜底保障 |
| D10 | 优先使用第三方库而非自建 | 降低维护成本，提高可靠性 |

---

## 十三、已知限制

| 限制 | 原因 | 解决方案 |
|------|------|---------|
| FTS5 不支持中文分词 | SQLite FTS5 的 `unicode61` tokenizer 忽略中文字符 | 需自定义 jieba tokenizer |
| PDF 表格提取不完美 | PDF 格式自由，无标准表格结构 | 使用 pdfplumber 备选 |
| JS/TS 解析精度有限 (无 tree-sitter 时) | 正则表达式无法完全解析 | 安装 tree-sitter |
| 图片内容未 OCR | 需要 PaddleOCR | 安装 `[ocr]` 可选依赖 |
| KnowledgeSaver 依赖 KnowledgeGraph 模块 | 与 QuickAgents 知识图谱耦合 | 不使用 KG 时仅用 MarkdownExporter |

---

## 十四、版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v2.8.0 | 2026-04-02 | 初始完整版本：10 个阶段、62 个任务、340 个测试 |

---

*文档版本: v1.0 | 生成时间: 2026-04-02*
