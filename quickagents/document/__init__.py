"""
Document understanding module for QuickAgents.

This module provides document parsing, source code analysis,
cross-referencing, and knowledge extraction capabilities.

Architecture:
    - Layer 1: Local parsing (PDF/Word/Excel/MindMap/Source)
    - Layer 1.5: Joint analysis (trace matching engine)
    - Layer 2: Cross-validation (OpenCode Read)
    - Layer 3: Deep analysis (LLM knowledge extraction)

Usage:
    from quickagents.document import DocumentPipeline, DocumentResult, SourceCodeResult
    from quickagents.document.parsers import BaseParser, ParserRegistry
"""

__version__ = "0.1.0"
__author__ = "QuickAgents Team"

# 公开 API
from .pipeline import DocumentPipeline
from .models import (
    DocumentResult,
    DocumentSection,
    DocumentTable,
    DocumentImage,
    DocumentFormula,
    SourceCodeResult,
    CodeModule,
    CodeClass,
    CodeFunction,
    CodeDependency,
    CrossReferenceResult,
    TraceEntry,
    DiffEntry,
    RefinedDocumentResult,
    RefinedCodeResult,
    KnowledgeExtractionResult,
    ExtractedRequirement,
    ExtractedDecision,
    ExtractedFact,
)

# 解析器相关（延迟导入，避免强制依赖)
def get_parser_registry():
    """获取解析器注册表（延迟加载）"""
    from .parsers import ParserRegistry
    return ParserRegistry()

    
def get_supported_formats():
    """获取支持的文档格式"""
    return [
        "pdf", "docx", "xlsx", "xmind", "mm", "opml", "md",
        # 源码格式
        "py", "js", "ts", "java", "go", "rs", "c", "cpp"
    ]


def check_dependencies(format: str) -> bool:
    """
    检查处理指定格式所需的依赖是否已安装
    
    Args:
        format: 文档格式 (pdf/docx/xlsx/xmind等) 或源码格式 (py/js/ts等)
        
    Returns:
        True: 依赖已安装
        False: 依赖未安装
    """
    from .parsers import check_dependencies as _check_dependencies
    return _check_dependencies(format)
