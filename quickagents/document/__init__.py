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

__version__ = "2.10.0"
__author__ = "QuickAgents Team"

# 公开 API
from .pipeline import DocumentPipeline as DocumentPipeline
from .models import (
    DocumentResult as DocumentResult,
    DocumentSection as DocumentSection,
    DocumentTable as DocumentTable,
    DocumentImage as DocumentImage,
    DocumentFormula as DocumentFormula,
    SourceCodeResult as SourceCodeResult,
    CodeModule as CodeModule,
    CodeClass as CodeClass,
    CodeFunction as CodeFunction,
    CodeDependency as CodeDependency,
    CrossReferenceResult as CrossReferenceResult,
    TraceEntry as TraceEntry,
    DiffEntry as DiffEntry,
    RefinedDocumentResult as RefinedDocumentResult,
    RefinedCodeResult as RefinedCodeResult,
    KnowledgeExtractionResult as KnowledgeExtractionResult,
    ExtractedRequirement as ExtractedRequirement,
    ExtractedDecision as ExtractedDecision,
    ExtractedFact as ExtractedFact,
)


# 解析器相关（延迟导入，避免强制依赖)
def get_parser_registry():
    """获取解析器注册表（延迟加载）"""
    from .parsers import ParserRegistry

    return ParserRegistry()


def get_supported_formats():
    """获取支持的文档格式"""
    return [
        "pdf",
        "docx",
        "xlsx",
        "xmind",
        "mm",
        "opml",
        "md",
        # 源码格式
        "py",
        "js",
        "ts",
        "java",
        "go",
        "rs",
        "c",
        "cpp",
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
