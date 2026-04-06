# -*- coding: utf-8 -*-
"""
Document Pipeline - Three-layer processing architecture.

Architecture:
    Layer 1: Local parsing (PDF/Word/Excel/Mindmap/Source)
    Layer 1.5: Joint analysis (trace matching engine)
    Layer 2: Cross-validation (OpenCode Read)
    Layer 3: Deep analysis (LLM knowledge extraction)
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
import json

from .parsers import ParserRegistry
from .models import (
    DocumentResult,
    SourceCodeResult,
    CrossReferenceResult,
    RefinedDocumentResult,
    KnowledgeExtractionResult,
)

logger = logging.getLogger(__name__)


class DocumentPipeline:
    """
    Document Pipeline - Three-layer processing architecture.

    Orchestrates document parsing, source code analysis, cross-referencing,
    and knowledge extraction.
    """

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.registry = ParserRegistry()
        self._register_default_parsers()
        logger.info("DocumentPipeline initialized")

    def _register_default_parsers(self):
        """Register all available parsers."""
        import importlib

        _parser_specs = [
            ("pdf", ".parsers.pdf_parser.PDFParser"),
            ("docx", ".parsers.word_parser.WordParser"),
            ("xlsx", ".parsers.excel_parser.ExcelParser"),
            ("xls", ".parsers.excel_parser.ExcelParser"),
            ("xmind", ".parsers.xmind_parser.XMindParser"),
            ("mm", ".parsers.freemind_parser.FreeMindParser"),
            ("opml", ".parsers.opml_parser.OPMLParser"),
            ("md", ".parsers.markdown_parser.MarkdownParser"),
            ("source", ".parsers.source_code_parser.SourceCodeParser"),
        ]

        for fmt, qualname in _parser_specs:
            module_path, class_name = qualname.rsplit(".", 1)
            try:
                mod = importlib.import_module(module_path, package="quickagents.document")
                parser_cls = getattr(mod, class_name)
                if self.registry.has_parser(fmt):
                    continue
                parser = parser_cls()
                self.registry.register(fmt, parser)
            except Exception as e:
                logger.debug(f"Skipped parser for {fmt}: {e}")

    def parse(self, file_path: Path) -> DocumentResult:
        """Parse document (Layer 1)"""
        ext = file_path.suffix.lower().lstrip(".")
        parser = self.registry.get_parser(ext)
        if parser is None:
            raise ValueError(f"Unsupported file format: {file_path}")
        logger.info(f"Parsing {file_path} with {parser.__class__.__name__}")
        return parser.parse(file_path)

    def parse_source(self, source_dir: Path) -> SourceCodeResult:
        """Parse source directory (Layer 1)"""
        parser = self.registry.get_parser("source")
        if parser is None:
            raise ValueError("Source code parser not registered")
        logger.info(f"Parsing source directory {source_dir}")
        return parser.parse(source_dir)  # type: ignore[return-value]

    def parse_batch(self, file_paths: List[Path]) -> List[DocumentResult]:
        """Batch parse documents (Layer 1)"""
        results = []
        for file_path in file_paths:
            try:
                result = self.parse(file_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to parse {file_path}: {e}")
        return results

    def cross_reference(
        self,
        doc_results: List[DocumentResult],
        code_result: SourceCodeResult,
    ) -> CrossReferenceResult:
        """Joint analysis - Layer 1.5"""
        from .matching import TraceMatchEngine

        engine = TraceMatchEngine()
        return engine.match(doc_results, code_result)

    def cross_validate(
        self,
        doc_result: DocumentResult,
        code_result: Optional[SourceCodeResult] = None,
    ) -> RefinedDocumentResult:
        """Cross validation - Layer 2"""
        from .validators import CrossValidator

        validator = CrossValidator()
        return validator.validate_document(doc_result, code_result)

    def extract_knowledge(
        self,
        doc_results: List[DocumentResult],
        code_result: Optional[SourceCodeResult] = None,
    ) -> KnowledgeExtractionResult:
        """Deep analysis - Layer 3"""
        from .validators import KnowledgeExtractor

        extractor = KnowledgeExtractor()
        return extractor.extract(doc_results, code_result)

    def save(self, result: Any, storage_type: str = "auto") -> None:
        """Save result to storage layer"""
        if storage_type == "auto":
            if isinstance(result, (DocumentResult, SourceCodeResult)):
                storage_type = "file"
            elif isinstance(result, CrossReferenceResult):
                storage_type = "file"

        if storage_type == "file":
            output_path = self._get_output_path(result)
            if output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                content = self._serialize_result(result)
                output_path.write_text(content, encoding="utf-8")
                logger.info(f"Saved result to {output_path}")

            # 同步到知识图谱（如果可用）
            try:
                from ..knowledge_graph import KnowledgeGraph
                from .storage.knowledge_saver import KnowledgeSaver

                kg = KnowledgeGraph()
                saver = KnowledgeSaver(kg)
                if hasattr(result, "document_id"):
                    saver.save_document(result)
                elif hasattr(result, "source_id"):
                    saver.save_source(result)
            except Exception:
                pass  # KG 可选，失败不影响主流程

    def import_all(
        self,
        pals_dir: str,
        with_source: bool = False,
    ) -> Dict:
        """
        Import all documents and source code.

        Args:
            pals_dir: PALs directory path
            with_source: Whether include source code
        """

        pals_path = Path(pals_dir)
        if not pals_path.exists():
            raise ValueError(f"PALs directory not found: {pals_dir}")

        doc_files, source_files = self._scan_files(pals_dir, with_source)

        doc_results = []
        for file_path in doc_files:
            try:
                result = self.parse(file_path)
                doc_results.append(result)
                logger.info(f"Parsed {file_path}")
            except Exception as e:
                logger.error(f"Failed to parse {file_path}: {e}")

        code_result = None
        if with_source and source_files:
            source_dir = pals_path / "SourceReference"
            if source_dir.exists():
                try:
                    code_result = self.parse_source(source_dir)
                    logger.info(f"Parsed {len(code_result.modules)} source modules")
                except Exception as e:
                    logger.error(f"Failed to parse source directory: {e}")

        cross_ref = None
        if with_source and doc_results and code_result:
            cross_ref = self.cross_reference(doc_results, code_result)
            logger.info("Cross-reference analysis complete")

        self._save_all_results(doc_results, code_result, cross_ref)

        return {
            "documents": doc_results,
            "source": code_result,
            "cross_reference": cross_ref,
            "errors": [],
        }

    def _scan_files(self, pals_dir: str, with_source: bool) -> tuple:
        """Scan PALs directory for files"""
        doc_files = []
        source_files = []
        doc_exts = {
            ".pdf",
            ".docx",
            ".doc",
            ".xlsx",
            ".xls",
            ".xmind",
            ".mm",
            ".opml",
            ".md",
        }
        source_exts = {".py", ".js", ".ts", ".java", ".go", ".rs", ".c", ".cpp"}

        pals_path = Path(pals_dir)
        for file_path in pals_path.rglob("*"):
            if not file_path.is_file():
                continue
            ext = file_path.suffix.lower()
            if ext in doc_exts:
                doc_files.append(file_path)
            elif ext in source_exts:
                source_files.append(file_path)
            elif ext in (".json", ".yaml", ".toml"):
                doc_files.append(file_path)

        return doc_files, source_files

    def _save_all_results(
        self,
        doc_results: List,
        code_result: Any,
        cross_ref: Any,
    ) -> None:
        """Save all results"""
        for result in doc_results:
            self.save(result, storage_type="file")
        if code_result:
            self.save(code_result, storage_type="file")
        if cross_ref:
            self.save(cross_ref, storage_type="file")

    def _serialize_result(self, result: Any) -> str:
        """Serialize result to JSON"""
        return json.dumps(result.to_dict(), ensure_ascii=False, default=str)

    def _get_output_path(self, result: Any) -> Optional[Path]:
        """Generate output file path"""
        source_file = getattr(result, "source_file", None)
        if source_file is None:
            source_dir = getattr(result, "source_dir", None)
            if source_dir is None:
                return None
            stem = Path(source_dir).stem
        else:
            stem = Path(source_file).stem

        output_dir = self.project_root / "Docs" / "PALs"
        return output_dir / f"{stem}.analysis.md"

    def ensure_pals_dir(self, pals_dir: str) -> Path:
        """Ensure PALs directory exists"""
        pals_path = Path(pals_dir)
        if not pals_path.exists():
            logger.warning(f"PALs directory not found: {pals_dir}, creating...")
            pals_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created PALs directory: {pals_dir}")
        return pals_path

    def get_pals_dir(self) -> Path:
        """Get PALs directory path"""
        return self.project_root / "PALs"
