# v2.8.0 实施方案：文档理解 + 源码分析 + 知识导入系统

> 生成时间: 2026-04-01
> 规划者: 风后-规划
> 版本: 1.0.0
> 状态: ✅ 已确认

## 元信息

| 属性 | 值 |
|------|-----|
| 计划ID | PLAN-2026-0401-DOC-UNDERSTANDING |
| 创建时间 | 2026-04-01 |
| 预计工期 | 12-14 天（串行） |
| 优先级 | P0 - 紧急 |
| 当前版本 | v2.7.9 |
| 目标版本 | v2.8.0 |

---

## 决策记录

| 编号 | 决策项 | 决策结论 |
|------|--------|----------|
| D01 | 三层架构顺序 | 本地解析 -> 代理交叉验证 -> LLM 深度分析（用户审批后） |
| D02 | 存储内容 | 存分析结果，不存原始文档 |
| D03 | 文档入口 | `PALs/` 目录，用户必须放入 |
| D04 | 源码入口 | `PALs/SourceReference/`，不限目录结构 |
| D05 | 理解深度 | 深层（完整解析->结构化存储->知识图谱自动构建） |
| D06 | 处理模式 | CLI + API 两者都要 |
| D07 | Excel 特殊需求 | 理解公式计算逻辑、理解图表、需求矩阵/功能列表 |
| D08 | 脑图格式 | XMind + FreeMind + OPML + Markdown 大纲，全部支持 |
| D09 | 格式优先级 | PDF > 脑图 > Word > Excel |
| D10 | 库优先原则 | 优先第三方库，无则自研 |
| D11 | OCR 选型 | PaddleOCR（唯一选择），Umi-OCR 是桌面应用不符合架构 |
| D12 | 降级策略 | 不要降级，未安装则提示必须安装 |
| D13 | 联合触发方式 | 场景B：`qa import PALs/ --with-source` 一次性处理 |
| D14 | 追踪粒度 | 全粒度（文件->函数->行级），默认函数级，用户可调整 |
| D15 | 匹配方式 | 混合：结构化约定 -> 关键词匹配 -> LLM 语义理解 |
| D16 | 输出形式 | 追踪矩阵表格(MD) + 差异报告（仅差距和多余） |
| D17 | 差异处理 | 标注差异 + 生成修正建议（可选以代码或文档为准） |
| D18 | 版本号 | v2.8.0 |

---

## 1. 目录结构

```
项目根目录/
|
+-- PALs/                                    # 用户待理解文件入口
|   +-- requirements.pdf                     # 需求文档
|   +-- architecture.xmind                   # 架构脑图
|   +-- spec.docx                            # 功能规格
|   +-- data-matrix.xlsx                     # 需求矩阵
|   +-- outline.mm                           # FreeMind 脑图
|   +-- outline.opml                         # OPML 大纲
|   +-- outline.md                           # Markdown 大纲
|   |
|   +-- SourceReference/                     # 源码入口（任意目录结构）
|       +-- main.py
|       +-- app/
|       |   +-- __init__.py
|       |   +-- server.py
|       +-- auth/
|       |   +-- __init__.py
|       |   +-- jwt_handler.py               # # REQ-001 实现
|       |   +-- rbac.py                      # # REQ-002 实现
|       +-- models/
|       |   +-- user.py
|       +-- lib/
|       +-- tests/
|       +-- utils.js
|       +-- UserService.java
|       +-- config.yaml
|
+-- Docs/PALs/                               # 分析结果输出
|   +-- requirements.pdf.analysis.md         # 文档分析结果
|   +-- architecture.xmind.analysis.md
|   +-- SourceReference/                     # 源码分析结果
|   |   +-- _overview.md                     # 源码整体概述
|   |   +-- auth_jwt_handler_py.analysis.md  # 单文件分析
|   |   +-- ...
|   +-- _trace_matrix.md                     # 追踪矩阵
|   +-- _diff_report.md                      # 差异报告
|   +-- _cross_ref.md                        # 交叉引用摘要
|
+-- .quickagents/unified.db                  # 记忆 + 知识图谱
+-- ...
```

---

## 2. 三层管道架构

### 2.1 整体流程

```
qa import PALs/ --with-source（一条命令，一次性处理）

扫描阶段: PALs 目录结构分析
  +-- 识别文件类型（按扩展名）
  +-- 区分: 文档 vs 源码 vs 配置
  +-- 检测依赖库是否安装
  |   +-- [document] PyMuPDF, python-docx...
  |   +-- [source] tree-sitter...
  |   +-- [ocr] paddleocr...
  |   +-- 未安装 -> 报错退出 + 安装提示
  +-- 生成处理计划（文件列表 + 预估时间）

第1层: 本地解析（QuickAgents Python）
  文档管道:
    PDF -> PyMuPDF + pdfplumber(表格) + PaddleOCR(扫描件)
    DOCX -> python-docx
    XLSX -> openpyxl (公式解析 + 图表数据提取)
    XMind -> xmind库
    .mm -> xml.etree
    .opml -> xml.etree
    .md -> heading解析
    输出: DocumentResult

  源码管道:
    .py  -> ast 模块
    .js  -> tree-sitter
    .ts  -> tree-sitter
    .java-> tree-sitter
    .go  -> tree-sitter
    .rs  -> tree-sitter
    .c   -> tree-sitter
    .cpp -> tree-sitter
    配置 -> json/toml/yaml
    目录结构 -> pathlib扫描
    输出: SourceCodeResult

第1.5层: 联合分析 -- 三级匹配引擎
  第1级: 结构化约定匹配（精确，置信度 1.0）
    +-- 代码注释中的需求ID: # REQ-001, // TODO-002
    +-- 文档中的编号: "REQ-001 用户认证"
    +-- 配置文件中的引用: feature_flag: "AUTH_LOGIN"

  第2级: 关键词匹配（中精度，置信度 0.7-0.9）
    +-- 文档术语 vs 代码命名: "用户认证" <-> auth/authentication
    +-- 功能描述 vs 函数签名: "密码验证" <-> validate_password()
    +-- 业务概念 vs 数据模型: "订单" <-> Order, order_list
    +-- 同义词表扩充: 登录<->login<->signin, 导出<->export<->download

  第3级: LLM 语义匹配（高精度，置信度标注）
    +-- 仅处理第1+2级未匹配的需求（减少LLM调用）
    +-- 需求描述 -> 与每个未匹配代码模块的语义相似度
    +-- 置信度 >= 0.6 才建立追踪关系

  输出: CrossReferenceResult
    +-- trace_matrix: 追踪矩阵（全粒度: 文件级/函数级/行级）
    +-- diff_report: 差异报告（gap + extra + inconsistency）
    +-- fix_suggestions: 修正建议（以代码为准/以文档为准）

第2层: 代理交叉验证 (OpenCode Read 工具)
  +-- 用 Read 重新读取原文档（PDF/DOCX 等支持的格式）
  +-- 用 Read 重新读取源码文件
  +-- LLM 对比第1层输出 vs Read 输出
  +-- 纠正: 错字/漏字/OCR错误/结构偏差/解析遗漏
  +-- 补充: 上下文理解/遣词造句/隐含含义
  +-- 验证追踪矩阵: 抽样检查追踪关系的正确性
  输出: RefinedDocumentResult + RefinedCodeResult

用户审查确认
  展示内容:
    +-- 追踪矩阵表格 (Markdown)
    +-- 差异报告（gap + extra + inconsistency）
    +-- 修正建议（以代码为准 / 以文档为准）
    +-- 覆盖率统计
    +-- 用户可调整追踪粒度（细化/粗化/删除/新增）
  用户操作:
    +-- 确认 -> 进入第3层或直接存储
    +-- 修改追踪关系 -> 更新后继续
    +-- 选择修正建议基准 -> 以代码为准/以文档为准
    +-- 跳过第3层 -> 直接存储当前结果

第3层: LLM 深度分析（用户审批后）
  +-- 需求提取: 自动识别功能/非功能需求
  +-- 决策识别: 技术选型/方案决策
  +-- 事实提取: 业务规则/约束条件
  +-- 概念建模: 核心概念 + 关系
  +-- 代码质量: 潜在问题/改进建议
  +-- 需求-代码追踪: 最终确认 MAPS_TO 关系
  +-- 交叉对比: 第2层 vs 第3层 结果去重合并

存储层
  +-- 记忆系统 (UnifiedDB)
  +-- 知识图谱 (10 种 NodeType + 15 种 EdgeType)
  +-- FTS5 全文检索
  +-- Markdown 同步: Docs/PALs/
```

---

## 3. 第三方库选型

### 3.1 文档解析

| 格式 | 选型库 | 版本 | 能力覆盖 | 许可证 |
|------|--------|------|----------|--------|
| PDF | PyMuPDF (fitz) | >=1.24.0 | 文本提取、表格检测、图片提取、布局分析 | AGPL-3.0 |
| PDF表格 | pdfplumber | >=0.11.0 | 精细表格提取、线框检测 | MIT |
| Word | python-docx | >=1.1.0 | 段落、标题、表格、图片、样式、列表 | MIT |
| Excel | openpyxl | >=3.1.0 | 单元格读写、公式、图表数据、条件格式 | MIT |
| XMind | XMind (PyPI) | >=1.2.0 | XMind 解析为 dict/JSON | MIT |
| FreeMind | 标准库 xml.etree | 内置 | MM 格式是标准XML | 无依赖 |
| OPML | 标准库 xml.etree | 内置 | OPML 标准解析 | 无依赖 |
| Markdown | 自研解析器 | -- | heading 层级 -> 树结构 | -- |

### 3.2 OCR

| 选型 | 理由 |
|------|------|
| PaddleOCR >=3.4.0 | 唯一选择。Python 库，PP-OCRv5 + PP-StructureV3，Apache 2.0 |
| PaddlePaddle >=3.0.0 | PaddleOCR 的框架依赖 |

Umi-OCR 排除理由：桌面应用(.exe)，不是 Python 库，无法 import，只能 HTTP 调用。

### 3.3 源码解析

| 选型 | 版本 | 理由 |
|------|------|------|
| 标准库 ast | 内置 | Python 零依赖 AST 解析，100% 覆盖 Python 语法 |
| tree-sitter | >=0.22.0 | 50+ 语言统一 AST 接口 |
| tree-sitter-python | >=0.23.0 | Python 语法（与 ast 互补） |
| tree-sitter-javascript | >=0.23.0 | JavaScript 语法 |
| tree-sitter-typescript | >=0.23.0 | TypeScript 语法 |
| tree-sitter-java | >=0.23.0 | Java 语法 |
| tree-sitter-go | >=0.23.0 | Go 语法 |
| tree-sitter-rust | >=0.23.0 | Rust 语法 |
| tree-sitter-c | >=0.23.0 | C 语法 |
| tree-sitter-cpp | >=0.23.0 | C++ 语法 |

---

## 4. 依赖管理

### 4.1 pyproject.toml 配置

```toml
[project.optional-dependencies]
# 文档解析（PDF/Word/Excel/脑图）
document = [
    "PyMuPDF>=1.24.0",
    "pdfplumber>=0.11.0",
    "python-docx>=1.1.0",
    "openpyxl>=3.1.0",
    "XMind>=1.2.0",
]
# OCR 扫描件识别
ocr = [
    "paddlepaddle>=3.0.0",
    "paddleocr>=3.4.0",
]
# 源码分析
source = [
    "tree-sitter>=0.22.0",
    "tree-sitter-python>=0.23.0",
    "tree-sitter-javascript>=0.23.0",
    "tree-sitter-typescript>=0.23.0",
    "tree-sitter-java>=0.23.0",
    "tree-sitter-go>=0.23.0",
    "tree-sitter-rust>=0.23.0",
    "tree-sitter-c>=0.23.0",
    "tree-sitter-cpp>=0.23.0",
]
# 完整安装
all = [
    "quickagents[document,ocr,source]",
]
```

### 4.2 安装命令

```bash
pip install quickagents[all]                # 完整安装（推荐）
pip install quickagents[document]            # 仅文档
pip install quickagents[document,ocr]        # 文档 + OCR
pip install quickagents[source]              # 仅源码
```

### 4.3 未安装时的错误提示

```
[ERROR] 处理 PDF 文件需要 [document] 依赖组
        请执行: pip install quickagents[document]

[ERROR] 检测到扫描件 PDF，需要 OCR 能力
        请执行: pip install quickagents[ocr]

[ERROR] 分析源码需要 [source] 依赖组
        请执行: pip install quickagents[source]

[ERROR] 完整导入需要 [document,source] 依赖组
        请执行: pip install quickagents[all]
```

---

## 5. 数据模型

### 5.1 DocumentResult（第1层文档输出）

```python
@dataclass
class DocumentSection:
    """文档章节"""
    section_id: str
    title: str
    level: int                # 层级深度 (1=H1, 2=H2, ...)
    content: str              # 该章节下的文本内容
    page_number: int
    parent_id: Optional[str]
    children_ids: List[str]

@dataclass
class DocumentTable:
    """文档表格"""
    table_id: str
    caption: Optional[str]
    headers: List[str]
    rows: List[List[str]]
    section_id: Optional[str]
    page_number: int

@dataclass
class DocumentImage:
    """文档图片"""
    image_id: str
    caption: Optional[str]
    image_type: str
    description: Optional[str]
    section_id: Optional[str]
    page_number: int

@dataclass
class DocumentFormula:
    """Excel公式 / 计算逻辑"""
    formula_id: str
    cell_ref: Optional[str]
    formula_text: str
    description: str          # 公式含义的自然语言描述
    dependencies: List[str]
    sheet_name: Optional[str]

@dataclass
class DocumentResult:
    """第1层解析结果 -- 统一中间表示"""
    source_file: str
    source_format: str        # pdf/docx/xlsx/xmind/mm/opml/md
    title: Optional[str]
    sections: List[DocumentSection]
    paragraphs: List[str]
    tables: List[DocumentTable]
    images: List[DocumentImage]
    formulas: List[DocumentFormula]
    structure_tree: Dict
    metadata: Dict[str, Any]
    raw_text: str
    errors: List[str]
```

### 5.2 SourceCodeResult（第1层源码输出）

```python
@dataclass
class CodeModule:
    """代码模块/文件"""
    module_id: str
    file_path: str
    language: str
    module_docstring: Optional[str]
    imports: List[str]
    classes: List[CodeClass]
    functions: List[CodeFunction]
    variables: List[str]
    loc: int

@dataclass
class CodeClass:
    """代码类"""
    class_id: str
    name: str
    docstring: Optional[str]
    bases: List[str]
    methods: List[CodeFunction]
    attributes: List[str]
    decorators: List[str]

@dataclass
class CodeFunction:
    """代码函数/方法"""
    func_id: str
    name: str
    signature: str
    docstring: Optional[str]
    parameters: List[Dict]
    return_type: Optional[str]
    decorators: List[str]
    calls: List[str]
    start_line: int
    end_line: int

@dataclass
class CodeDependency:
    """模块间依赖"""
    source_module: str
    target_module: str
    dep_type: str             # import/inheritance/call

@dataclass
class SourceCodeResult:
    """源码分析结果"""
    source_dir: str
    languages: List[str]
    modules: List[CodeModule]
    dependencies: List[CodeDependency]
    structure_tree: Dict
    stats: Dict[str, Any]
    raw_text: Dict[str, str]  # {file_path: source_code}
    errors: List[str]
```

### 5.3 CrossReferenceResult（第1.5层联合输出）

```python
@dataclass
class TraceEntry:
    """需求-代码追踪条目"""
    trace_id: str
    requirement: Optional[str]
    req_node_id: Optional[str]
    req_source: Optional[str]       # 来源文档+章节
    implementation: Optional[str]
    impl_node_id: Optional[str]
    impl_file: Optional[str]
    impl_function: Optional[str]
    impl_lines: Optional[str]       # "L15-42"
    trace_type: str                 # convention/keyword/semantic
    confidence: float
    status: str                     # covered/partial/uncovered/extra

@dataclass
class DiffEntry:
    """差异条目"""
    diff_id: str
    diff_type: str                   # gap/extra/inconsistency
    description: str
    req_side: Optional[str]          # 需求侧描述
    code_side: Optional[str]         # 代码侧描述
    suggestion_by_code: Optional[str] # 以代码为准的修正建议
    suggestion_by_doc: Optional[str]  # 以文档为准的修正建议

@dataclass
class CrossReferenceResult:
    """文档 <-> 源码交叉引用结果"""
    trace_matrix: List[TraceEntry]
    diff_report: List[DiffEntry]
    coverage_report: Dict            # {total, covered, partial, uncovered, extra, rate}
    unmatched_reqs: List[str]        # 完全未匹配的需求
    unmatched_code: List[str]        # 完全未匹配的代码模块
```

### 5.4 RefinedDocumentResult / RefinedCodeResult（第2层输出）

```python
@dataclass
class RefinedDocumentResult(DocumentResult):
    """第2层交叉验证后的精炼文档结果"""
    corrections: List[Dict]   # [{原文本, 纠正后, 理由}]
    supplements: List[Dict]   # [{类型, 内容, 来源}]
    confidence: float
    layer2_notes: str

@dataclass
class RefinedCodeResult(SourceCodeResult):
    """第2层交叉验证后的精炼源码结果"""
    corrections: List[Dict]
    supplements: List[Dict]
    confidence: float
    layer2_notes: str
```

### 5.5 KnowledgeExtractionResult（第3层输出）

```python
@dataclass
class ExtractedRequirement:
    """提取的需求"""
    req_id: str
    title: str
    description: str
    req_type: str             # functional/non-functional/constraint
    priority: Optional[str]   # high/medium/low
    source_section: str
    confidence: float

@dataclass
class ExtractedDecision:
    """提取的决策"""
    decision_id: str
    title: str
    description: str
    rationale: Optional[str]
    alternatives: List[str]
    source_section: str
    confidence: float

@dataclass
class ExtractedFact:
    """提取的事实"""
    fact_id: str
    content: str
    category: str
    source_section: str
    confidence: float

@dataclass
class KnowledgeExtractionResult:
    """第3层深度分析结果"""
    requirements: List[ExtractedRequirement]
    decisions: List[ExtractedDecision]
    facts: List[ExtractedFact]
    concepts: List[Dict]
    relationships: List[Dict]
    summary: str
    layer3_notes: str
```

---

## 6. 追踪矩阵设计

### 6.1 三级匹配引擎

```python
class TraceMatchEngine:
    """三级追踪匹配引擎"""

    def match(self, doc_result, code_result) -> CrossReferenceResult:
        """
        匹配流程:
        1. 结构化约定匹配 -> 精确匹配，置信度 1.0
        2. 关键词匹配 -> 中精度匹配，置信度 0.7-0.9
        3. LLM 语义匹配 -> 仅处理未匹配项，置信度 >= 0.6
        """

    def _match_by_convention(self, requirements, modules):
        """
        第1级: 结构化约定
        +-- 代码注释: # REQ-001, # FEATURE-AUTH, // TODO-002
        +-- 文档编号: "REQ-001 用户认证", "2.1 登录功能"
        +-- 函数命名: req_001_login(), feature_auth()
        +-- 配置标记: feature_flag: "AUTH_LOGIN"
        粒度: 函数级（可定位到具体函数/行）
        """

    def _match_by_keyword(self, requirements, modules, functions):
        """
        第2级: 关键词匹配
        +-- 直接匹配: "用户认证" <-> UserAuth, auth, authentication
        +-- 翻译匹配: "登录" <-> login, signin, sign_in
        +-- 缩写匹配: "RBAC" <-> rbac, role_based_access
        +-- 业务术语表: 用户自定义术语 <-> 代码命名
        +-- 同义词库: 内置中英文同义词对
        粒度: 函数级
        """

    def _match_by_semantic(self, unmatched_reqs, unmatched_funcs):
        """
        第3级: LLM 语义匹配
        仅处理第1+2级未匹配的剩余需求
        输入给 LLM: 需求文本 + 未匹配代码模块列表（名称+docstring+签名）
        LLM 输出: 匹配对 + 置信度 + 匹配理由
        过滤: 置信度 < 0.6 丢弃
        粒度: 文件级或函数级
        """
```

### 6.2 追踪矩阵输出格式

**Docs/PALs/_trace_matrix.md**:

```markdown
# 需求追踪矩阵

> 生成时间: 2026-04-01 14:30:00
> 文档源: PALs/ (3 个文档)
> 源码源: PALs/SourceReference/ (12 个文件)
> 匹配引擎: 结构化约定(5) + 关键词(8) + LLM语义(3)

## 追踪矩阵

| 需求ID | 需求描述 | 来源文档 | 实现模块 | 实现函数 | 行范围 | 匹配方式 | 置信度 | 状态 |
|--------|----------|----------|----------|----------|--------|----------|--------|------|
| REQ-001 | 用户通过JWT认证 | spec.pdf 2.1 | auth/jwt_handler.py | generate_token() | L15-42 | 结构化 | 1.00 | 已覆盖 |
| REQ-001 | 用户通过JWT认证 | spec.pdf 2.1 | auth/jwt_handler.py | verify_token() | L44-78 | 结构化 | 1.00 | 已覆盖 |
| REQ-002 | 基于角色的访问控制 | spec.pdf 2.2 | auth/rbac.py | check_permission() | L22-55 | 关键词 | 0.85 | 已覆盖 |
| REQ-003 | 密码强度校验 | spec.pdf 2.3 | -- | -- | -- | -- | -- | 未覆盖 |
| -- | Token刷新机制 | -- | auth/jwt_handler.py | refresh_token() | L80-105 | 关键词 | 0.75 | 无文档 |
| REQ-004 | 订单状态追踪 | spec.pdf 3.1 | models/order.py | Order.status | L30 | LLM | 0.65 | 部分覆盖 |

## 统计

| 指标 | 数值 |
|------|------|
| 总需求数 | 6 |
| 完全覆盖 | 2 (33%) |
| 部分覆盖 | 2 (33%) |
| 未覆盖 | 1 (17%) |
| 无文档对应 | 1 (17%) |
| 覆盖率 | 67% |
```

### 6.3 差异报告输出格式

**Docs/PALs/_diff_report.md**:

```markdown
# 差异报告

> 生成时间: 2026-04-01 14:30:00

## 未覆盖的需求（有需求无实现）

### REQ-003: 密码强度校验
- **来源**: spec.pdf 2.3
- **描述**: "用户密码必须包含大小写字母、数字和特殊字符，长度8-20位"
- **建议**: 需要在 auth/validator.py 中新增 validate_password_strength() 函数

## 无文档对应的实现（有实现无文档）

### auth/jwt_handler.py: refresh_token()
- **位置**: L80-105
- **分析**: 实现了 Token 自动刷新机制，但文档中无对应需求描述
- **建议**: 在 spec.pdf 中补充 Token 刷新策略章节，或将此功能标记为实现细节

## 文档与代码不一致

### REQ-004: 订单状态追踪
- **文档描述**: "订单状态包括：待支付、已支付、已发货、已完成、已取消"
- **代码实现**: models/order.py OrderStatus 枚举仅包含：PENDING, PAID, SHIPPED, CANCELLED
- **差异**: 缺少 COMPLETED 状态
- **修正建议**:
  - [以文档为准] 在 OrderStatus 枚举中补充 COMPLETED 状态
  - [以代码为准] 更新 spec.pdf 3.1 删除"已完成"状态描述
```

### 6.4 用户粒度调整机制

用户审查追踪矩阵时可以:

1. **粗化（合并）**: 多条 trace entry 合并，粒度从函数级变为模块级
2. **细化（拆分）**: 一条 trace entry 拆分为多条，粒度从函数级变为行级
3. **新增**: 手动建立追踪关系（即使代码还没写）
4. **删除**: 删除错误的追踪关系
5. **选择修正基准**: "REQ-004 以文档为准" -> 生成代码修改建议

---

## 7. 知识图谱扩展

### 7.1 新增节点类型

```python
class NodeType(Enum):
    # 现有 (6种)
    REQUIREMENT = "requirement"
    DECISION = "decision"
    INSIGHT = "insight"
    FACT = "fact"
    CONCEPT = "concept"
    SOURCE = "source"
    # 新增 (4种)
    DOCUMENT = "document"        # 文档元信息
    SECTION = "section"          # 文档章节
    MODULE = "module"            # 代码模块/文件
    FUNCTION = "function"        # 代码函数/方法
```

### 7.2 新增边类型

```python
class EdgeType(Enum):
    # 现有 (11种)
    DEPENDS_ON = "depends_on"
    IS_SUBCLASS_OF = "is_subclass_of"
    CITES = "cites"
    LINKS_TO = "links_to"
    EVOLVES_FROM = "evolves_from"
    MAPS_TO = "maps_to"
    AFFECTS = "affects"
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"
    RELATED_TO = "related_to"
    INDIRECTLY_RELATED_TO = "indirectly_related_to"
    # 新增 (4种)
    CONTAINS = "contains"              # 文档->章节, 模块->函数
    IMPLEMENTS = "implements"          # 函数->需求（MAPS_TO 的反向）
    CALLS = "calls"                    # 函数->函数调用
    EXTRACTED_FROM = "extracted_from"  # 知识节点->原始文档/源码
```

### 7.3 知识图谱示例

```
DOCUMENT("requirements.pdf")
  +-- CONTAINS -> SECTION("2 用户认证")
  |    +-- CONTAINS -> SECTION("2.1 JWT认证")
  |    |    +-- EXTRACTED_FROM -> REQUIREMENT("REQ-001: 用户通过JWT认证")
  |    |         +-- MAPS_TO -> MODULE("auth/jwt_handler.py")
  |    |         |    +-- CONTAINS -> FUNCTION("generate_token()") [L15-42]
  |    |         |    |    +-- CALLS -> FUNCTION("create_access_token()")
  |    |         |    +-- CONTAINS -> FUNCTION("verify_token()") [L44-78]
  |    |         |         +-- CALLS -> FUNCTION("decode_jwt()")
  |    |         +-- MAPS_TO -> MODULE("auth/jwt_handler.py")
  |    +-- CONTAINS -> SECTION("2.2 权限控制")
  |         +-- EXTRACTED_FROM -> REQUIREMENT("REQ-002: 基于角色的访问控制")
  |              +-- MAPS_TO -> MODULE("auth/rbac.py")
  |                   +-- CONTAINS -> FUNCTION("check_permission()")
  +-- CONTAINS -> SECTION("3 数据模型")
       +-- EXTRACTED_FROM -> CONCEPT("订单")
            +-- RELATED_TO -> CONCEPT("用户")
            +-- MAPS_TO -> MODULE("models/order.py")
```

---

## 8. 模块架构

```
quickagents/
+-- document/                             # 新模块
|   +-- __init__.py                       # 公开 API (~30行)
|   +-- pipeline.py                       # 三层管道主控制器 (~400行)
|   +-- models.py                         # 数据模型 (~350行)
|   |
|   +-- parsers/                          # 第1层: 解析器
|   |   +-- __init__.py                   # 解析器注册表 + 工厂 (~60行)
|   |   +-- base.py                       # BaseParser 抽象类 (~60行)
|   |   +-- pdf_parser.py                 # PDF: PyMuPDF + pdfplumber + PaddleOCR (~300行)
|   |   +-- word_parser.py                # Word: python-docx (~200行)
|   |   +-- excel_parser.py               # Excel: openpyxl + 公式 + 图表 (~300行)
|   |   +-- xmind_parser.py               # XMind: xmind库 (~150行)
|   |   +-- freemind_parser.py            # FreeMind .mm: xml.etree (~120行)
|   |   +-- opml_parser.py                # OPML: xml.etree (~100行)
|   |   +-- markdown_parser.py            # Markdown 大纲 (~80行)
|   |   +-- source_code_parser.py         # 源码: ast + tree-sitter (~400行)
|   |
|   +-- matching/                         # 第1.5层: 联合分析
|   |   +-- __init__.py
|   |   +-- trace_engine.py               # 三级匹配引擎 (~350行)
|   |   +-- convention_matcher.py         # 第1级: 结构化约定 (~100行)
|   |   +-- keyword_matcher.py            # 第2级: 关键词匹配 (~150行)
|   |   +-- semantic_matcher.py           # 第3级: LLM语义匹配 (~150行)
|   |   +-- diff_analyzer.py              # 差异分析器 (~150行)
|   |   +-- fix_suggester.py              # 修正建议生成器 (~120行)
|   |   +-- synonym_table.py              # 中英文同义词库 (~80行)
|   |
|   +-- extractors/                       # 第3层: 知识提取
|   |   +-- __init__.py
|   |   +-- requirement_extractor.py      # 需求提取 (~200行)
|   |   +-- decision_extractor.py         # 决策提取 (~150行)
|   |   +-- fact_extractor.py             # 事实提取 (~150行)
|   |   +-- concept_extractor.py          # 概念建模 (~150行)
|   |
|   +-- storage/                          # 存储层
|   |   +-- __init__.py
|   |   +-- knowledge_saver.py            # 结果存入记忆+知识图谱 (~300行)
|   |   +-- trace_saver.py                # 追踪矩阵存入知识图谱 (~150行)
|   |   +-- result_cache.py               # 中间结果缓存 (~100行)
|   |   +-- markdown_exporter.py          # 分析结果导出为MD (~200行)
|   |
|   +-- validators/                       # 第2层: 交叉验证
|   |   +-- __init__.py
|   |   +-- cross_validator.py            # OpenCode Read 对比验证 (~200行)
|   |
|   +-- ocr/                              # OCR 集成
|   |   +-- __init__.py
|   |   +-- paddle_ocr_wrapper.py         # PaddleOCR 封装 (~150行)
|   |
|   +-- cli.py                            # qa import 命令 (~400行)
```

---

## 9. CLI 命令

```bash
# 完整导入（一条命令）
qa import PALs/ --with-source                # 文档 + 源码 + 联合分析
qa import PALs/ --with-source --layer 2      # 执行到第2层
qa import PALs/ --with-source --layer 3      # 全部3层（需用户确认）

# 仅文档导入
qa import PALs/requirements.pdf              # 单文件
qa import PALs/ --format pdf,xmind           # 指定格式
qa import PALs/                              # PALs下所有文档（不含SourceReference）

# 仅源码分析
qa import PALs/SourceReference/              # 全部源码
qa import PALs/SourceReference/auth/         # 指定子目录

# 查看结果
qa import list                               # 列出已导入文件
qa import show PALs/requirements.pdf         # 查看文档分析结果
qa import show PALs/SourceReference/auth/    # 查看源码分析结果
qa import trace                              # 查看追踪矩阵
qa import trace --format table               # 表格格式（默认）
qa import trace --coverage                   # 覆盖率统计
qa import diff                               # 查看差异报告
qa import diff --by code                     # 以代码为准的修正建议
qa import diff --by doc                      # 以文档为准的修正建议

# 管理
qa import status                             # 系统状态 + 依赖检查
qa import deps                               # 检查/安装依赖
qa import reprocess PALs/requirements.pdf    # 重新处理
qa import remove PALs/requirements.pdf       # 移除结果
```

---

## 10. Python API

```python
from quickagents.document import DocumentPipeline

pipeline = DocumentPipeline(project_root='.')

# 完整导入（场景B：一条命令）
result = pipeline.import_all(
    pals_dir='PALs/',
    with_source=True,
    layers=[1, 2],
)
print(result.cross_ref.trace_matrix)        # 追踪矩阵
print(result.cross_ref.coverage_report)     # 覆盖率报告
print(result.cross_ref.diff_report)         # 差异报告

# 仅文档分析
doc_result = pipeline.parse('PALs/requirements.pdf')
refined = pipeline.cross_validate(doc_result)
pipeline.save(refined)

# 仅源码分析
code_result = pipeline.parse_source('PALs/SourceReference/')
pipeline.save_code(code_result)

# 联合分析（已有分析结果时）
cross_ref = pipeline.cross_reference(
    doc_results=[...],
    code_result=code_result,
)
```

---

## 11. 任务分解

### Phase 1: 架构基础（1.5天）

| 任务 | 说明 | 预计行数 |
|------|------|----------|
| T001 | 创建 document/ 模块骨架 | 5个文件 |
| T002 | 定义数据模型 models.py | ~350行 |
| T003 | 实现 BaseParser 抽象类 + 解析器注册表 | ~120行 |
| T004 | 实现 DocumentPipeline 第1层框架 | ~150行 |
| T005 | PALs 目录检测与创建逻辑 | ~30行 |
| T006 | 依赖检测逻辑（检查可选依赖是否安装） | ~80行 |
| T007 | Phase 1 单元测试 | ~100行 |

### Phase 2: PDF 解析器（2天）最高优先级

| 任务 | 说明 | 预计行数 |
|------|------|----------|
| T008 | PDF 文本提取（PyMuPDF get_text + sort） | ~80行 |
| T009 | PDF 章节结构识别（字体大小+位置推断标题层级） | ~100行 |
| T010 | PDF 表格提取（PyMuPDF find_tables + pdfplumber 备选） | ~100行 |
| T011 | PDF 图片提取与描述 | ~60行 |
| T012 | PDF -> DocumentResult 完整转换 | ~50行 |
| T013 | PDF 解析器测试（含真实 PDF 文件测试） | ~150行 |

### Phase 3: 脑图解析器（1.5天）

| 任务 | 说明 | 预计行数 |
|------|------|----------|
| T014 | XMind 解析器（xmind库 -> 树结构 -> DocumentResult） | ~150行 |
| T015 | FreeMind .mm 解析器（xml.etree 解析） | ~120行 |
| T016 | OPML 解析器（xml.etree 解析） | ~100行 |
| T017 | Markdown 大纲解析器（heading -> 树结构） | ~80行 |
| T018 | 脑图解析器测试 | ~150行 |

### Phase 4: Word 解析器（1天）

| 任务 | 说明 | 预计行数 |
|------|------|----------|
| T019 | Word 文本+标题结构提取（python-docx） | ~80行 |
| T020 | Word 表格提取 | ~60行 |
| T021 | Word 图片提取 | ~50行 |
| T022 | Word 解析器测试 | ~100行 |

### Phase 5: Excel 解析器（1.5天）

| 任务 | 说明 | 预计行数 |
|------|------|----------|
| T023 | Excel 单元格数据读取（openpyxl） | ~80行 |
| T024 | Excel 公式解析 + 计算逻辑描述 | ~120行 |
| T025 | Excel 图表数据提取 | ~80行 |
| T026 | Excel 需求矩阵/功能列表结构识别 | ~80行 |
| T027 | Excel 解析器测试 | ~120行 |

### Phase 6: 源码解析器（2天）

| 任务 | 说明 | 预计行数 |
|------|------|----------|
| T028 | SourceCodeResult + CrossReferenceResult 数据模型 | ~120行 |
| T029 | Python ast 解析器（模块/类/函数/依赖/docstring） | ~200行 |
| T030 | tree-sitter 多语言解析器（条件导入，未安装报错） | ~150行 |
| T031 | 目录结构扫描 + 语言检测 | ~60行 |
| T032 | 配置文件解析（json/yaml/toml） | ~50行 |
| T033 | 源码解析器测试 | ~150行 |

### Phase 7: 联合分析引擎（2天）

| 任务 | 说明 | 预计行数 |
|------|------|----------|
| T034 | TraceMatchEngine 框架 + TraceEntry 生成 | ~100行 |
| T035 | 第1级: 结构化约定匹配器 | ~100行 |
| T036 | 第2级: 关键词匹配器 + 同义词库 | ~150行 |
| T037 | 第3级: LLM 语义匹配器 | ~150行 |
| T038 | 差异分析器（gap/extra/inconsistency） | ~150行 |
| T039 | 修正建议生成器 | ~120行 |
| T040 | 用户粒度调整接口 | ~80行 |
| T041 | 联合分析测试 | ~150行 |

### Phase 8: 存储层 + 知识图谱扩展（1.5天）

| 任务 | 说明 | 预计行数 |
|------|------|----------|
| T042 | 扩展 NodeType: +DOCUMENT, SECTION, MODULE, FUNCTION | ~20行 |
| T043 | 扩展 EdgeType: +CONTAINS, IMPLEMENTS, CALLS, EXTRACTED_FROM | ~15行 |
| T044 | KnowledgeSaver -- 文档结果存入记忆+知识图谱 | ~80行 |
| T045 | KnowledgeSaver -- 源码结果存入记忆+知识图谱 | ~80行 |
| T046 | TraceSaver -- 追踪矩阵存入知识图谱 | ~100行 |
| T047 | MarkdownExporter -- 分析结果导出MD文件 | ~200行 |
| T048 | 修复 FTS5 -- KnowledgeSearcher 实际查询 FTS5 索引 | ~50行 |
| T049 | 为 memory 表增加 FTS5 全文检索 | ~40行 |
| T050 | 存储层测试 | ~150行 |

### Phase 9: 三层管道集成（1.5天）

| 任务 | 说明 | 预计行数 |
|------|------|----------|
| T051 | 第2层: CrossValidator (OpenCode Read 交叉验证) | ~200行 |
| T052 | 第3层: LLM 深度分析 + 知识提取提示词模板 | ~200行 |
| T053 | 知识提取器: 需求/决策/事实/概念提取 | ~300行 |
| T054 | 三层差异对比 + 合并逻辑 | ~100行 |
| T055 | 用户审查确认流程 | ~50行 |
| T056 | 管道集成测试 | ~100行 |

### Phase 10: CLI + 文档 + 发布（1天）

| 任务 | 说明 | 预计行数 |
|------|------|----------|
| T057 | qa import CLI 命令（含源码+联合分析） | ~400行 |
| T058 | 更新 pyproject.toml (optional-dependencies) | ~15行 |
| T059 | 文档: PALs + SourceReference 使用指南 | -- |
| T060 | CHANGELOG.md + VERSION.md 更新 | -- |
| T061 | 全量测试回归 (580+ 现有 + 新增) | -- |
| T062 | PyPI 发布 v2.8.0 | -- |

---

## 12. 总览

| 维度 | 数值 |
|------|------|
| Phase 数 | 10 |
| 任务数 | 62 |
| 新增代码 | ~5,710 行（不含测试） |
| 新增测试 | ~1,500 行 |
| 新增文件 | ~29 个 .py |
| 新增依赖 | 16 个（分3组: document/ocr/source，全部可选） |
| 新增 NodeType | 4 种 (DOCUMENT, SECTION, MODULE, FUNCTION) |
| 新增 EdgeType | 4 种 (CONTAINS, IMPLEMENTS, CALLS, EXTRACTED_FROM) |
| 优先级执行顺序 | Phase 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10 |
| 预计总时长 | 12-14 天（串行执行） |
| 当前版本 | v2.7.9 |
| 目标版本 | v2.8.0 |

---

## 13. 风险评估

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| PyMuPDF AGPL 许可证影响用户 | 低 | 中 | 已作为可选依赖，安装时提示 |
| PaddleOCR + PaddlePaddle 安装体积大 | 中 | 低 | 作为独立 [ocr] 可选组 |
| XMind库 (2019年) 不兼容新版 XMind Zen | 中 | 中 | 备选: 自研 ZIP+JSON 解析 |
| PDF 扫描件 OCR 需 GPU 加速 | 低 | 中 | CPU 模式可用但较慢，提示用户 |
| tree-sitter 语言包版本兼容 | 低 | 低 | 锁定 >=0.23.0 统一版本 |
| 大文档（100页）内存占用 | 低 | 中 | 逐页处理，流式存储 |
| Excel 图表理解能力有限 | 高 | 中 | 提取图表数据+元信息，图表视觉理解延后 |
| 第3级 LLM 语义匹配 API 成本 | 中 | 低 | 仅处理未匹配项，减少调用次数 |

---

*方案状态: 已确认 | 等待实施启动*
