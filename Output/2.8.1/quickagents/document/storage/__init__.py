"""
Storage layer for document analysis results.

Components:
- KnowledgeSaver: Save DocumentResult/SourceCodeResult to Knowledge Graph
- MarkdownExporter: Export analysis results to Markdown
- ResultCache: In-memory cache for intermediate results
"""

from .knowledge_saver import KnowledgeSaver
from .markdown_exporter import MarkdownExporter
from .result_cache import ResultCache

__all__ = [
    "KnowledgeSaver",
    "MarkdownExporter",
    "ResultCache",
]
