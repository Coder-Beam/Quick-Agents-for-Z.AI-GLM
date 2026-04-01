"""
Data models for document understanding.

Based on v2.8.0 implementation plan:
- DocumentResult: 第1层文档解析输出
- SourceCodeResult: 第1层源码分析输出
- CrossReferenceResult: 第1.5层联合分析输出
- RefinedDocumentResult/RefinedCodeResult: 第2层交叉验证输出
- KnowledgeExtractionResult: 第3层深度分析输出
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Enum
from datetime import datetime


import hashlib


# ============== 文档解析结果 ==============

@dataclass
class DocumentSection:
    """文档章节"""
    section_id: str
    title: str
    level: int                    # 层级深度 (1=H1, 2=H2, ...)
    content: str = ""               # 该章节下的文本内容
    page_number: int
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    
    def add_child(self, child_id: str) -> None:
        """添加子章节"""
        self.children_ids.append(child_id)
    
    def get_full_path(self) -> str:
        """获取完整路径（如 "1.1.2.3"）"""
        parts = [self.title]
        current = self
        while current.parent_id:
            parts.insert(0, current.title)
            current = self._find_section(current.parent_id)
        return ".".join(reversed(parts))
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "section_id": self.section_id,
            "title": self.title,
            "level": self.level,
            "content": self.content,
            "page_number": self.page_number,
            "parent_id": self.parent_id,
            "children_ids": self.children_ids,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "DocumentSection":
        """从字典创建"""
        return cls(
            section_id=data["section_id"],
            title=data["title"],
            level=data["level"],
            content=data["content"],
            page_number=data["page_number"],
            parent_id=data.get("parent_id"),
            children_ids=data.get("children_ids", []),
        )
    
    def __repr__(self) -> str:
        return f"DocumentSection(id={self.section_id}, title='{self.title}', level={self.level})"


    
    def __eq__(self, other) -> bool:
        if not isinstance(other, DocumentSection):
            return False
        return self.section_id == other.section_id
    
    def __hash__(self) -> int:
        return hash((self.section_id, self.title, self.content))


@dataclass
class DocumentTable:
    """文档表格"""
    table_id: str
    caption: Optional[str] = None
    headers: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)
    section_id: Optional[str] = None
    page_number: int
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "table_id": self.table_id,
            "caption": self.caption,
            "headers": self.headers,
            "rows": self.rows,
            "section_id": self.section_id,
            "page_number": self.page_number,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "DocumentTable":
        """从字典创建"""
        return cls(
            table_id=data["table_id"],
            caption=data.get("caption"),
            headers=data.get("headers", []),
            rows=data.get("rows", []),
            section_id=data.get("section_id"),
            page_number=data["page_number"],
        )
    
    def get_row_count(self) -> int:
        """获取行数（不含表头）"""
        return len(self.rows)
    
    def get_column_count(self) -> int:
        """获取列数"""
        return len(self.headers)
    
    def to_markdown(self) -> str:
        """转换为 Markdown 表格"""
        if not self.headers:
            return ""
        lines = ["| " + " | ".join(self.headers) + " |"]
        for row in self.rows:
            lines.append("| " + " | ".join(row) + " |")
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return f"DocumentTable(id={self.table_id}, rows={len(self.rows)})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, DocumentTable):
            return False
        return self.table_id == other.table_id
    
    def __hash__(self) -> int:
        return hash((self.table_id, tuple(self.rows)))


@dataclass
class DocumentImage:
    """文档图片"""
    image_id: str
    caption: Optional[str] = None
    image_type: str              # png/jpeg/svg等
    description: Optional[str] = None
    section_id: Optional[str] = None
    page_number: int
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "image_id": self.image_id,
            "caption": self.caption,
            "image_type": self.image_type,
            "description": self.description,
            "section_id": self.section_id,
            "page_number": self.page_number,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "DocumentImage":
        """从字典创建"""
        return cls(
            image_id=data["image_id"],
            caption=data.get("caption"),
            image_type=data["image_type"],
            description=data.get("description"),
            section_id=data.get("section_id"),
            page_number=data["page_number"],
        )
    
    def __repr__(self) -> str:
        return f"DocumentImage(id={self.image_id}, type={self.image_type})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, DocumentImage):
            return False
        return self.image_id == other.image_id
    
    def __hash__(self) -> int:
        return hash((self.image_id, self.image_type))


@dataclass
class DocumentFormula:
    """Excel公式 / 计算逻辑"""
    formula_id: str
    cell_ref: Optional[str] = None
    formula_text: str
    description: str = ""          # 公式含义的自然语言描述
    dependencies: List[str] = field(default_factory=list)
    sheet_name: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "formula_id": self.formula_id,
            "cell_ref": self.cell_ref,
            "formula_text": self.formula_text,
            "description": self.description,
            "dependencies": self.dependencies,
            "sheet_name": self.sheet_name,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "DocumentFormula":
        """从字典创建"""
        return cls(
            formula_id=data["formula_id"],
            cell_ref=data.get("cell_ref"),
            formula_text=data["formula_text"],
            description=data["description"],
            dependencies=data.get("dependencies", []),
            sheet_name=data.get("sheet_name"),
        )
    
    def __repr__(self) -> str:
        return f"DocumentFormula(id={self.formula_id}, cell={self.cell_ref})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, DocumentFormula):
            return False
        return self.formula_id == other.formula_id
    
    def __hash__(self) -> int:
        return hash((self.formula_id, self.formula_text))


@dataclass
class DocumentResult:
    """第1层解析结果 -- 统一中间表示"""
    source_file: str
    source_format: str                # pdf/docx/xlsx/xmind/mm/opml/md
    title: Optional[str] = None
    sections: List[DocumentSection] = field(default_factory=list)
    paragraphs: List[str] = field(default_factory=list)
    tables: List[DocumentTable] = field(default_factory=list)
    images: List[DocumentImage] = field(default_factory=list)
    formulas: List[DocumentFormula] = field(default_factory=list)
    structure_tree: Dict = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_text: str = ""
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "source_file": self.source_file,
            "source_format": self.source_format,
            "title": self.title,
            "sections": [s.to_dict() for s in self.sections],
            "paragraphs": self.paragraphs,
            "tables": [t.to_dict() for t in self.tables],
            "images": [i.to_dict() for i in self.images],
            "formulas": [f.to_dict() for f in self.formulas],
            "structure_tree": self.structure_tree,
            "metadata": self.metadata,
            "raw_text": self.raw_text,
            "errors": self.errors,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "DocumentResult":
        """从字典创建"""
        return cls(
            source_file=data["source_file"],
            source_format=data["source_format"],
            title=data.get("title"),
            sections=[DocumentSection.from_dict(s) for s in data.get("sections", [])],
            paragraphs=data.get("paragraphs", []),
            tables=[DocumentTable.from_dict(t) for t in data.get("tables", [])],
            images=[DocumentImage.from_dict(i) for i in data.get("images", [])],
            formulas=[DocumentFormula.from_dict(f) for f in data.get("formulas", [])],
            structure_tree=data.get("structure_tree", {}),
            metadata=data.get("metadata", {}),
            raw_text=data.get("raw_text", ""),
            errors=data.get("errors", []),
        )
    
    def get_hash(self) -> str:
        """计算内容哈希"""
        content = self.raw_text + str(len(self.sections)) + str(len(self.tables))
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def has_errors(self) -> bool:
        """检查是否有错误"""
        return len(self.errors) > 0
    
    def get_section_count(self) -> int:
        """获取章节数"""
        return len(self.sections)
    
    def get_table_count(self) -> int:
        """获取表格数"""
        return len(self.tables)
    
    def get_image_count(self) -> int:
        """获取图片数"""
        return len(self.images)
    
    def find_section_by_title(self, title: str) -> Optional[DocumentSection]:
        """按标题查找章节"""
        for section in self.sections:
            if section.title == title:
                return section
        return None
    
    def find_sections_by_level(self, level: int) -> List[DocumentSection]:
        """按层级查找章节"""
        return [s for s in self.sections if s.level == level]
    
    def get_all_text(self) -> str:
        """获取所有文本内容"""
        parts = [self.raw_text]
        for section in self.sections:
            parts.append(f"\n## {section.title}\n{section.content}")
        return "\n\n".join(parts)
    
    def __repr__(self) -> str:
        return (f"DocumentResult(file={self.source_file}, "
                f"sections={len(self.sections)}, tables={len(self.tables)})")
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, DocumentResult):
            return False
        return self.source_file == other.source_file
    
    def __hash__(self) -> int:
        return hash((self.source_file, self.get_hash()))


# ============== 源码解析结果 ==============
@dataclass
class CodeFunction:
    """代码函数/方法"""
    func_id: str
    name: str
    signature: str
    docstring: Optional[str] = None
    parameters: List[Dict] = field(default_factory=list)
    return_type: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    calls: List[str] = field(default_factory=list)
    start_line: int
    end_line: int
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "func_id": self.func_id,
            "name": self.name,
            "signature": self.signature,
            "docstring": self.docstring,
            "parameters": self.parameters,
            "return_type": self.return_type,
            "decorators": self.decorators,
            "calls": self.calls,
            "start_line": self.start_line,
            "end_line": self.end_line,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "CodeFunction":
        """从字典创建"""
        return cls(
            func_id=data["func_id"],
            name=data["name"],
            signature=data["signature"],
            docstring=data.get("docstring"),
            parameters=data.get("parameters", []),
            return_type=data.get("return_type"),
            decorators=data.get("decorators", []),
            calls=data.get("calls", []),
            start_line=data["start_line"],
            end_line=data["end_line"],
        )
    
    def get_loc(self) -> int:
        """获取代码行数"""
        return self.end_line - self.start_line + 1
    
    def __repr__(self) -> str:
        return f"CodeFunction(id={self.func_id}, name={self.name}, lines={self.start_line}-{self.end_line})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, CodeFunction):
            return False
        return self.func_id == other.func_id
    
    def __hash__(self) -> int:
        return hash((self.func_id, self.name, self.start_line, self.end_line))


@dataclass
class CodeClass:
    """代码类"""
    class_id: str
    name: str
    docstring: Optional[str] = None
    bases: List[str] = field(default_factory=list)
    methods: List[CodeFunction] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "class_id": self.class_id,
            "name": self.name,
            "docstring": self.docstring,
            "bases": self.bases,
            "methods": [m.to_dict() for m in self.methods],
            "attributes": self.attributes,
            "decorators": self.decorators,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "CodeClass":
        """从字典创建"""
        return cls(
            class_id=data["class_id"],
            name=data["name"],
            docstring=data.get("docstring"),
            bases=data.get("bases", []),
            methods=[CodeFunction.from_dict(m) for m in data.get("methods", [])],
            attributes=data.get("attributes", []),
            decorators=data.get("decorators", []),
        )
    
    def get_method_count(self) -> int:
        """获取方法数"""
        return len(self.methods)
    
    def find_method_by_name(self, name: str) -> Optional[CodeFunction]:
        """按名称查找方法"""
        for method in self.methods:
            if method.name == name:
                return method
        return None
    
    def __repr__(self) -> str:
        return f"CodeClass(id={self.class_id}, name={self.name}, methods={len(self.methods)})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, CodeClass):
            return False
        return self.class_id == other.class_id
    
    def __hash__(self) -> int:
        return hash((self.class_id, self.name))


@dataclass
class CodeModule:
    """代码模块/文件"""
    module_id: str
    file_path: str
    language: str
    module_docstring: Optional[str] = None
    imports: List[str] = field(default_factory=list)
    classes: List[CodeClass] = field(default_factory=list)
    functions: List[CodeFunction] = field(default_factory=list)
    variables: List[str] = field(default_factory=list)
    loc: int                     # 代码行数
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "module_id": self.module_id,
            "file_path": self.file_path,
            "language": self.language,
            "module_docstring": self.module_docstring,
            "imports": self.imports,
            "classes": [c.to_dict() for c in self.classes],
            "functions": [f.to_dict() for f in self.functions],
            "variables": self.variables,
            "loc": self.loc,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "CodeModule":
        """从字典创建"""
        return cls(
            module_id=data["module_id"],
            file_path=data["file_path"],
            language=data["language"],
            module_docstring=data.get("module_docstring"),
            imports=data.get("imports", []),
            classes=[CodeClass.from_dict(c) for c in data.get("classes", [])],
            functions=[CodeFunction.from_dict(f) for f in data.get("functions", [])],
            variables=data.get("variables", []),
            loc=data["loc"],
        )
    
    def get_function_count(self) -> int:
        """获取函数数"""
        return len(self.functions)
    
    def get_class_count(self) -> int:
        """获取类数"""
        return len(self.classes)
    
    def find_function_by_name(self, name: str) -> Optional[CodeFunction]:
        """按名称查找函数"""
        for func in self.functions:
            if func.name == name:
                return func
        return None
    
    def find_class_by_name(self, name: str) -> Optional[CodeClass]:
        """按名称查找类"""
        for cls in self.classes:
            if cls.name == name:
                return cls
        return None
    
    def get_all_functions(self) -> List[CodeFunction]:
        """获取所有函数（包括类方法）"""
        funcs = list(self.functions)
        for cls in self.classes:
            funcs.extend(cls.methods)
        return funcs
    
    def __repr__(self) -> str:
        return (f"CodeModule(id={self.module_id}, path={self.file_path}, "
                f"funcs={len(self.functions)}, classes={len(self.classes)})")
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, CodeModule):
            return False
        return self.module_id == other.module_id
    
    def __hash__(self) -> int:
        return hash((self.module_id, self.file_path))


@dataclass
class CodeDependency:
    """模块间依赖"""
    source_module: str
    target_module: str
    dep_type: str              # import/inheritance/call
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "source_module": self.source_module,
            "target_module": self.target_module,
            "dep_type": self.dep_type,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "CodeDependency":
        """从字典创建"""
        return cls(
            source_module=data["source_module"],
            target_module=data["target_module"],
            dep_type=data["dep_type"],
        )
    
    def __repr__(self) -> str:
        return f"CodeDependency({self.source_module} -> {self.target_module})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, CodeDependency):
            return False
        return (self.source_module == other.source_module 
                and self.target_module == other.target_module)
    
    def __hash__(self) -> int:
        return hash((self.source_module, self.target_module, self.dep_type))


@dataclass
class SourceCodeResult:
    """源码分析结果"""
    source_dir: str
    languages: List[str] = field(default_factory=list)
    modules: List[CodeModule] = field(default_factory=list)
    dependencies: List[CodeDependency] = field(default_factory=list)
    structure_tree: Dict = field(default_factory=dict)
    stats: Dict[str, Any] = field(default_factory=dict)
    raw_text: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "source_dir": self.source_dir,
            "languages": self.languages,
            "modules": [m.to_dict() for m in self.modules],
            "dependencies": [d.to_dict() for d in self.dependencies],
            "structure_tree": self.structure_tree,
            "stats": self.stats,
            "raw_text": self.raw_text,
            "errors": self.errors,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SourceCodeResult":
        """从字典创建"""
        return cls(
            source_dir=data["source_dir"],
            languages=data.get("languages", []),
            modules=[CodeModule.from_dict(m) for m in data.get("modules", [])],
            dependencies=[CodeDependency.from_dict(d) for d in data.get("dependencies", [])],
            structure_tree=data.get("structure_tree", {}),
            stats=data.get("stats", {}),
            raw_text=data.get("raw_text", {}),
            errors=data.get("errors", []),
        )
    
    def get_module_count(self) -> int:
        """获取模块数"""
        return len(self.modules)
    
    def get_total_loc(self) -> int:
        """获取总代码行数"""
        return sum(m.loc for m in self.modules)
    
    def get_all_functions(self) -> List[CodeFunction]:
        """获取所有函数"""
        funcs = []
        for module in self.modules:
            funcs.extend(module.functions)
            for cls in module.classes:
                funcs.extend(cls.methods)
        return funcs
    
    def get_all_classes(self) -> List[CodeClass]:
        """获取所有类"""
        classes = []
        for module in self.modules:
            classes.extend(module.classes)
        return classes
    
    def find_module_by_path(self, file_path: str) -> Optional[CodeModule]:
        """按路径查找模块"""
        for module in self.modules:
            if module.file_path == file_path:
                return module
        return None
    
    def has_errors(self) -> bool:
        """检查是否有错误"""
        return len(self.errors) > 0
    
    def __repr__(self) -> str:
        return (f"SourceCodeResult(dir={self.source_dir}, "
                f"modules={len(self.modules)}, langs={self.languages})")
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, SourceCodeResult):
            return False
        return self.source_dir == other.source_dir
    
    def __hash__(self) -> int:
        return hash((self.source_dir, tuple(self.languages)))


# ============== 联合分析结果 ==============
class TraceType(Enum):
    """追踪类型"""
    CONVENTION = "convention"     # 结构化约定匹配
    KEYWORD = "keyword"           # 关键词匹配
    SEMANTIC = "semantic"         # LLM语义匹配


class TraceStatus(Enum):
    """追踪状态"""
    COVERED = "covered"          # 已覆盖
    PARTIAL = "partial"          # 部分覆盖
    UNCOVERED = "uncovered"      # 未覆盖
    EXTRA = "extra"              # 无文档对应


@dataclass
class TraceEntry:
    """需求-代码追踪条目"""
    trace_id: str
    requirement: Optional[str] = None
    req_node_id: Optional[str] = None
    req_source: Optional[str] = None       # 来源文档+章节
    implementation: Optional[str] = None
    impl_node_id: Optional[str] = None
    impl_file: Optional[str] = None
    impl_function: Optional[str] = None
    impl_lines: Optional[str] = None       # "L15-42"
    trace_type: str = ""
    confidence: float = 0.0
    status: str = ""
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "trace_id": self.trace_id,
            "requirement": self.requirement,
            "req_node_id": self.req_node_id,
            "req_source": self.req_source,
            "implementation": self.implementation,
            "impl_node_id": self.impl_node_id,
            "impl_file": self.impl_file,
            "impl_function": self.impl_function,
            "impl_lines": self.impl_lines,
            "trace_type": self.trace_type,
            "confidence": self.confidence,
            "status": self.status,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "TraceEntry":
        """从字典创建"""
        return cls(
            trace_id=data["trace_id"],
            requirement=data.get("requirement"),
            req_node_id=data.get("req_node_id"),
            req_source=data.get("req_source"),
            implementation=data.get("implementation"),
            impl_node_id=data.get("impl_node_id"),
            impl_file=data.get("impl_file"),
            impl_function=data.get("impl_function"),
            impl_lines=data.get("impl_lines"),
            trace_type=data.get("trace_type", ""),
            confidence=data.get("confidence", 0.0),
            status=data.get("status", ""),
        )
    
    def __repr__(self) -> str:
        return f"TraceEntry(id={self.trace_id}, status={self.status}, conf={self.confidence:.2f})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, TraceEntry):
            return False
        return self.trace_id == other.trace_id
    
    def __hash__(self) -> int:
        return hash(self.trace_id)


@dataclass
class DiffEntry:
    """差异条目"""
    diff_id: str
    diff_type: str                   # gap/extra/inconsistency
    description: str = ""
    req_side: Optional[str] = None          # 需求侧描述
    code_side: Optional[str] = None         # 代码侧描述
    suggestion_by_code: Optional[str] = None # 以代码为准的修正建议
    suggestion_by_doc: Optional[str] = None  # 以文档为准的修正建议
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "diff_id": self.diff_id,
            "diff_type": self.diff_type,
            "description": self.description,
            "req_side": self.req_side,
            "code_side": self.code_side,
            "suggestion_by_code": self.suggestion_by_code,
            "suggestion_by_doc": self.suggestion_by_doc,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "DiffEntry":
        """从字典创建"""
        return cls(
            diff_id=data["diff_id"],
            diff_type=data["diff_type"],
            description=data.get("description", ""),
            req_side=data.get("req_side"),
            code_side=data.get("code_side"),
            suggestion_by_code=data.get("suggestion_by_code"),
            suggestion_by_doc=data.get("suggestion_by_doc"),
        )
    
    def __repr__(self) -> str:
        return f"DiffEntry(id={self.diff_id}, type={self.diff_type})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, DiffEntry):
            return False
        return self.diff_id == other.diff_id
    
    def __hash__(self) -> int:
        return hash((self.diff_id, self.diff_type))


@dataclass
class CrossReferenceResult:
    """文档 <-> 源码交叉引用结果"""
    trace_matrix: List[TraceEntry] = field(default_factory=list)
    diff_report: List[DiffEntry] = field(default_factory=list)
    coverage_report: Dict = field(default_factory=dict)
    unmatched_reqs: List[str] = field(default_factory=list)
    unmatched_code: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "trace_matrix": [t.to_dict() for t in self.trace_matrix],
            "diff_report": [d.to_dict() for d in self.diff_report],
            "coverage_report": self.coverage_report,
            "unmatched_reqs": self.unmatched_reqs,
            "unmatched_code": self.unmatched_code,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "CrossReferenceResult":
        """从字典创建"""
        return cls(
            trace_matrix=[TraceEntry.from_dict(t) for t in data.get("trace_matrix", [])],
            diff_report=[DiffEntry.from_dict(d) for d in data.get("diff_report", [])],
            coverage_report=data.get("coverage_report", {}),
            unmatched_reqs=data.get("unmatched_reqs", []),
            unmatched_code=data.get("unmatched_code", []),
        )
    
    def get_coverage_rate(self) -> float:
        """获取覆盖率"""
        return self.coverage_report.get("rate", 0.0)
    
    def get_covered_count(self) -> int:
        """获取已覆盖数"""
        return self.coverage_report.get("covered", 0)
    
    def get_uncovered_count(self) -> int:
        """获取未覆盖数"""
        return self.coverage_report.get("uncovered", 0)
    
    def has_diffs(self) -> bool:
        """检查是否有差异"""
        return len(self.diff_report) > 0
    
    def __repr__(self) -> str:
        return (f"CrossReferenceResult(traces={len(self.trace_matrix)}, "
                f"diffs={len(self.diff_report)}, coverage={self.get_coverage_rate():.1%})")
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, CrossReferenceResult):
            return False
        return self.trace_matrix == other.trace_matrix
    
    def __hash__(self) -> int:
        return hash((tuple(self.trace_matrix), tuple(self.diff_report)))


# ============== 第2层交叉验证结果 ==============
@dataclass
class RefinedDocumentResult(DocumentResult):
    """第2层交叉验证后的精炼文档结果"""
    corrections: List[Dict] = field(default_factory=list)
    supplements: List[Dict] = field(default_factory=list)
    confidence: float = 0.0
    layer2_notes: str = ""
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            "corrections": self.corrections,
            "supplements": self.supplements,
            "confidence": self.confidence,
            "layer2_notes": self.layer2_notes,
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict) -> "RefinedDocumentResult":
        """从字典创建"""
        base = DocumentResult.from_dict(data)
        return cls(
            source_file=base.source_file,
            source_format=base.source_format,
            title=base.title,
            sections=base.sections,
            paragraphs=base.paragraphs,
            tables=base.tables,
            images=base.images,
            formulas=base.formulas,
            structure_tree=base.structure_tree,
            metadata=base.metadata,
            raw_text=base.raw_text,
            errors=base.errors,
            corrections=data.get("corrections", []),
            supplements=data.get("supplements", []),
            confidence=data.get("confidence", 0.0),
            layer2_notes=data.get("layer2_notes", ""),
        )
    
    def __repr__(self) -> str:
        return f"RefinedDocumentResult(file={self.source_file}, conf={self.confidence:.2f})"


@dataclass
class RefinedCodeResult(SourceCodeResult):
    """第2层交叉验证后的精炼源码结果"""
    corrections: List[Dict] = field(default_factory=list)
    supplements: List[Dict] = field(default_factory=list)
    confidence: float = 0.0
    layer2_notes: str = ""
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            "corrections": self.corrections,
            "supplements": self.supplements,
            "confidence": self.confidence,
            "layer2_notes": self.layer2_notes,
        })
        return base_dict
    
    @classmethod
    def from_dict(cls, data: Dict) -> "RefinedCodeResult":
        """从字典创建"""
        base = SourceCodeResult.from_dict(data)
        return cls(
            source_dir=base.source_dir,
            languages=base.languages,
            modules=base.modules,
            dependencies=base.dependencies,
            structure_tree=base.structure_tree,
            stats=base.stats,
            raw_text=base.raw_text,
            errors=base.errors,
            corrections=data.get("corrections", []),
            supplements=data.get("supplements", []),
            confidence=data.get("confidence", 0.0),
            layer2_notes=data.get("layer2_notes", ""),
        )
    
    def __repr__(self) -> str:
        return f"RefinedCodeResult(dir={self.source_dir}, conf={self.confidence:.2f})"


# ============== 第3层深度分析结果 ==============
@dataclass
class ExtractedRequirement:
    """提取的需求"""
    req_id: str
    title: str = ""
    description: str = ""
    req_type: str = ""            # functional/non-functional/constraint
    priority: Optional[str] = None   # high/medium/low
    source_section: str = ""
    confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "req_id": self.req_id,
            "title": self.title,
            "description": self.description,
            "req_type": self.req_type,
            "priority": self.priority,
            "source_section": self.source_section,
            "confidence": self.confidence,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ExtractedRequirement":
        """从字典创建"""
        return cls(
            req_id=data["req_id"],
            title=data.get("title", ""),
            description=data.get("description", ""),
            req_type=data.get("req_type", ""),
            priority=data.get("priority"),
            source_section=data.get("source_section", ""),
            confidence=data.get("confidence", 0.0),
        )
    
    def __repr__(self) -> str:
        return f"ExtractedRequirement(id={self.req_id}, title={self.title[:30]}...)"


@dataclass
class ExtractedDecision:
    """提取的决策"""
    decision_id: str
    title: str = ""
    description: str = ""
    rationale: Optional[str] = None
    alternatives: List[str] = field(default_factory=list)
    source_section: str = ""
    confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "decision_id": self.decision_id,
            "title": self.title,
            "description": self.description,
            "rationale": self.rationale,
            "alternatives": self.alternatives,
            "source_section": self.source_section,
            "confidence": self.confidence,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ExtractedDecision":
        """从字典创建"""
        return cls(
            decision_id=data["decision_id"],
            title=data.get("title", ""),
            description=data.get("description", ""),
            rationale=data.get("rationale"),
            alternatives=data.get("alternatives", []),
            source_section=data.get("source_section", ""),
            confidence=data.get("confidence", 0.0),
        )
    
    def __repr__(self) -> str:
        return f"ExtractedDecision(id={self.decision_id}, title={self.title[:30]}...)"


@dataclass
class ExtractedFact:
    """提取的事实"""
    fact_id: str
    content: str = ""
    category: str = ""
    source_section: str = ""
    confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "fact_id": self.fact_id,
            "content": self.content,
            "category": self.category,
            "source_section": self.source_section,
            "confidence": self.confidence,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ExtractedFact":
        """从字典创建"""
        return cls(
            fact_id=data["fact_id"],
            content=data.get("content", ""),
            category=data.get("category", ""),
            source_section=data.get("source_section", ""),
            confidence=data.get("confidence", 0.0),
        )
    
    def __repr__(self) -> str:
        return f"ExtractedFact(id={self.fact_id}, category={self.category})"


@dataclass
class KnowledgeExtractionResult:
    """第3层深度分析结果"""
    requirements: List[ExtractedRequirement] = field(default_factory=list)
    decisions: List[ExtractedDecision] = field(default_factory=list)
    facts: List[ExtractedFact] = field(default_factory=list)
    concepts: List[Dict] = field(default_factory=list)
    relationships: List[Dict] = field(default_factory=list)
    summary: str = ""
    layer3_notes: str = ""
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "requirements": [r.to_dict() for r in self.requirements],
            "decisions": [d.to_dict() for d in self.decisions],
            "facts": [f.to_dict() for f in self.facts],
            "concepts": self.concepts,
            "relationships": self.relationships,
            "summary": self.summary,
            "layer3_notes": self.layer3_notes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "KnowledgeExtractionResult":
        """从字典创建"""
        return cls(
            requirements=[ExtractedRequirement.from_dict(r) for r in data.get("requirements", [])],
            decisions=[ExtractedDecision.from_dict(d) for d in data.get("decisions", [])],
            facts=[ExtractedFact.from_dict(f) for f in data.get("facts", [])],
            concepts=data.get("concepts", []),
            relationships=data.get("relationships", []),
            summary=data.get("summary", ""),
            layer3_notes=data.get("layer3_notes", ""),
        )
    
    def get_requirement_count(self) -> int:
        """获取需求数"""
        return len(self.requirements)
    
    def get_decision_count(self) -> int:
        """获取决策数"""
        return len(self.decisions)
    
    def get_fact_count(self) -> int:
        """获取事实数"""
        return len(self.facts)
    
    def __repr__(self) -> str:
        return (f"KnowledgeExtractionResult(reqs={len(self.requirements)}, "
                f"decisions={len(self.decisions)}, facts={len(self.facts)})")


# ============== 工具函数 ==============
def generate_id(prefix: str = "") -> str:
    """生成唯一ID"""
    import uuid
    if prefix:
        return f"{prefix}-{uuid.uuid4().hex[:8]}"
    return uuid.uuid4().hex


