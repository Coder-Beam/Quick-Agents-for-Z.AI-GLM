# -*- coding: utf-8 -*-
"""
Document Pipeline - Three-layer processing architecture.

This module implements the core pipeline that orchestrates:
document parsing, source code analysis, cross-referencing, and knowledge extraction.

Architecture:
    Layer 1: Local parsing (PDF/Word/Excel/Mindmap/Source)
    Layer 1.5: Joint analysis (trace matching engine)
    Layer 2: Cross-validation (OpenCode Read)
    Layer 3: Deep analysis (LLM knowledge extraction)

Usage:
    from quickagents.document import DocumentPipeline
    from quickagents.document.models import (
        DocumentResult,
        SourceCodeResult
        CrossReferenceResult
    )

    from pathlib import Path
    from typing import Optional, List, Dict, Any
    import logging
    from datetime import datetime
    import hashlib

    from .parsers import ParserRegistry, BaseParser
    from .matching import TraceMatchEngine
    from .storage import KnowledgeSaver, TraceSaver, MarkdownExporter
    from .validators import CrossValidator
    from quickagents.core.unified_db import UnifiedDB, MemoryType
    from quickagents.knowledge_graph import KnowledgeGraph

logger = logging.getLogger(__name__)


class DocumentPipeline:
    """
    Document Pipeline - Three-layer processing architecture.

    Orchestrates document parsing, source code analysis, cross-referencing,
    and knowledge extraction.

    Attributes:
        project_root (Path): Project root directory
        db (UnifiedDB): UnifiedDB instance
        kg (KnowledgeGraph): KnowledgeGraph instance
    """

    def __init__(self, project_root: str = "."):
        """Initialize the pipeline."""
        self.project_root = Path(project_root)
        db_path = self.project_root / ".quickagents" / "unified.db"
        self.db = UnifiedDB(db_path)
        self.kg = KnowledgeGraph(db)

        # Initialize parser registry
        self.registry = ParserRegistry()
        self._initialized = False

        logger.info("DocumentPipeline initialized")

    def parse(self, file_path: Path) -> DocumentResult:
        """Parse document (Layer 1)"""
        parser = self.registry.get_parser(file_path.suffix.lower())
        if parser is None:
            raise ValueError(f"Unsupported file format: {file_path}")
        logger.info(f"Parsing {file_path} with {parser.__class__.__name__}")
        return parser.parse(file_path)

    
    def parse_source(self, source_dir: Path) -> SourceCodeResult:
        """Parse source directory (Layer 1)"""
        parser = self.registry.get_source_parser(source_dir)
        if parser is None:
            raise ValueError(f"Unsupported source format: {source_dir}")
        logger.info(f"Parsing source directory {source_dir} with {parser.__class__.__name__}")
        return parser.parse(source_dir)
    
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
    
    def cross_reference(self, doc_results: List[DocumentResult],
                       code_result: SourceCodeResult) -> CrossReferenceResult:
        """Joint analysis - Layer 1.5"""
        engine = TraceMatchEngine()
        return engine.match(doc_results, code_result)
    
    def cross_validate(self, doc_result: DocumentResult,
                       code_result: SourceCodeResult) -> "RefinedDocumentResult":
        """Cross validation - Layer 2"""
        validator = CrossValidator()
        return validator.validate(doc_result, code_result)
    
    def extract_knowledge(self, doc_result: DocumentResult,
                          code_result: SourceCodeResult) -> Dict:
        """Deep analysis - Layer 3"""
        # TODO: Implement LLM knowledge extraction
        pass
    
    def save(self, result: Any, storage_type: str = "auto") -> None:
        """Save result to storage layer"""
        if storage_type == "auto":
            # Auto select storage type
            if isinstance(result, (DocumentResult, SourceCodeResult)):
                storage_type = "memory"
            elif isinstance(result, CrossReferenceResult):
                storage_type = "kg"
        
        if storage_type == "memory":
            # Save to memory system
            self._sync_memory(result)
        elif storage_type == "kg":
            # Save to knowledge graph
            self._sync_knowledge(result)
        elif storage_type == "file":
            # Save to file system
            file_path = self._get_output_path(result, file_prefix="")
            if file_path:
                Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    content = self._serialize_result(result)
                    f.write(file_path)
                    logger.info(f"Saved {storage_type} to {file_path}")
    
    def import_all(self, pals_dir: str, with_source: bool = False,
                   layers: Optional[List[int]] = None) -> Dict:
        """
        Import all documents and source code (optional)
        
        Args:
            pals_dir: PALs directory path
            with_source: Whether include source code (default: False)
            layers: Execution layers (default: [1, 2, 3])
        
        Returns:
            Import results
        """
        # Validate input
        self._validate_input(pals_dir, with_source)
        
        # Check dependencies
        self._check_all_dependencies(pals_dir)
        
        # Scan files
        doc_files, source_files = self._scan_files(pals_dir, with_source)
        
        # Parse documents
        doc_results = []
        for file_path in doc_files:
            try:
                result = self.parse(file_path)
                doc_results.append(result)
                logger.info(f"Parsed {file_path}")
            except Exception as e:
                logger.error(f"Failed to parse {file_path}: {e}")
        
        # Parse source code
        code_result = None
        if with_source and source_files:
            try:
                code_result = self.parse_source(Path(pals_dir) / "SourceReference")
                logger.info(f"Parsed {len(code_result.modules)} source modules")
            except Exception as e:
                logger.error(f"Failed to parse source directory: {e}")
        
        # Joint analysis
        cross_ref = None
        if with_source and doc_results and code_result:
            cross_ref = self.cross_reference(doc_results, code_result)
            logger.info("Cross-reference analysis complete")
        
        # Save results
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
        
        pals_path = Path(pals_dir)
        if not pals_path.exists():
            raise ValueError(f"PALs directory not found: {pals_dir}")
        
        for file_path in pals_path.rglob("*"):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                # Distinguish documents and source code
                if ext in ("pdf", "docx", "doc", "xlsx", "xls", "xmind", "mm", "opml", "md"):
                    doc_files.append(file_path)
                elif with_source and ext in ("py", "js", "ts", "java", "go", "rs", "c", "cpp"):
                    source_files.append(file_path)
                elif ext in ("json", "yaml", "toml"):
                    # Config files as documents
                    doc_files.append(file_path)
        
        # Separate SourceReference directory
        if with_source:
            source_ref_dir = pals_path / "SourceReference"
            if source_ref_dir.exists():
                for file_path in source_ref_dir.rglob("*"):
                    if file_path.is_file():
                        ext = file_path.suffix.lower()
                        if ext in ("py", "js", "ts", "java", "go", "rs", "c", "cpp"):
                            source_files.append(file_path)
        
        return doc_files, source_files
    
    def _get_source_dir(self, pals_dir: Path, with_source: bool) -> Optional[Path]:
        """Get source directory path"""
        if with_source:
            source_dir = pals_dir / "SourceReference"
            if source_dir.exists():
                return source_dir
        return None
    
    def _validate_input(self, pals_dir: str, with_source: bool) -> None:
        """Validate input"""
        pals_path = Path(pals_dir)
        if not pals_path.exists():
            raise ValueError(f"PALs directory not found: {pals_dir}")
    
    def _check_all_dependencies(self, pals_dir: str) -> None:
        """Check all dependencies"""
        # TODO: Implement actual dependency checking
        pass
    
    def _sync_memory(self, result: Any) -> None:
        """Sync result to memory system"""
        # TODO: Implement memory sync
        pass
    
    def _sync_knowledge(self, result: Any) -> None:
        """Sync result to knowledge graph"""
        # TODO: Implement knowledge graph sync
        pass
    
    def _save_all_results(self, doc_results: List, code_result: Any, cross_ref: Any) -> None:
        """Save all results"""
        # Save document results
        for result in doc_results:
            self.save(result, storage_type="file")
        
        # Save source code results
        if code_result:
            self.save(code_result, storage_type="file")
        
        # Save cross-reference results
        if cross_ref:
            self.save(cross_ref, storage_type="kg")
    
    def _serialize_result(self, result: Any) -> str:
        """Serialize result to JSON"""
        import json
        return json.dumps(result.to_dict(), ensure_ascii=False, default=str)
    
    def _get_output_path(self, source_file: str, output_dir: Path) -> Path:
        """Generate output file path"""
        source_path = Path(source_file)
        output_file = output_dir / f"{source_path.stem}.analysis.md"
        return output_file
    
    def ensure_pals_dir(self, pals_dir: str) -> Path:
        """Ensure PALs directory exists, create if not exists"""
        pals_path = Path(pals_dir)
        if not pals_path.exists():
            logger.warning(f"PALs directory not found: {pals_dir}, creating...")
            pals_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created PALs directory: {pals_dir}")
        return pals_path
    
    def get_pals_dir(self) -> Path:
        """Get PALs directory path"""
        return self.project_root / "PALs"
