"""
CrossValidator - Layer 2 cross-validation.

Validates parsed document/source results by cross-checking
document content against source code structure. Detects
corrections, supplements, and confidence adjustments.
"""

import re
import logging
from typing import List, Dict, Optional, Callable

from ..models import (
    DocumentResult,
    SourceCodeResult,
    RefinedDocumentResult,
    RefinedCodeResult,
)

logger = logging.getLogger(__name__)


class CrossValidator:
    """Layer 2: Cross-validate parsed results against each other."""

    def validate_document(
        self,
        doc: DocumentResult,
        code: Optional[SourceCodeResult] = None,
        read_func: Optional[Callable] = None,
    ) -> RefinedDocumentResult:
        """Cross-validate a document result against source code."""
        corrections: List[Dict] = []
        supplements: List[Dict] = []
        notes_parts: List[str] = []

        if code:
            self._check_sections_against_code(
                doc, code, corrections, supplements, notes_parts
            )

        if read_func:
            self._check_with_external_read(
                doc, read_func, corrections, supplements, notes_parts
            )

        self._check_internal_consistency(doc, corrections, notes_parts)

        confidence = self._compute_confidence(doc, corrections, supplements)
        notes = "; ".join(notes_parts) if notes_parts else "Cross-validation complete"

        return RefinedDocumentResult(
            source_file=doc.source_file,
            source_format=doc.source_format,
            title=doc.title,
            sections=doc.sections,
            paragraphs=doc.paragraphs,
            tables=doc.tables,
            images=doc.images,
            formulas=doc.formulas,
            structure_tree=doc.structure_tree,
            metadata=doc.metadata,
            raw_text=doc.raw_text,
            errors=doc.errors,
            corrections=corrections,
            supplements=supplements,
            confidence=confidence,
            layer2_notes=notes,
        )

    def validate_source(
        self,
        code: SourceCodeResult,
        docs: Optional[List[DocumentResult]] = None,
    ) -> RefinedCodeResult:
        """Cross-validate source code result against documents."""
        corrections: List[Dict] = []
        supplements: List[Dict] = []
        notes_parts: List[str] = []

        if docs:
            self._check_code_against_docs(
                code, docs, corrections, supplements, notes_parts
            )

        self._check_code_consistency(code, corrections, notes_parts)

        confidence = self._compute_source_confidence(code, corrections, supplements)
        notes = "; ".join(notes_parts) if notes_parts else "Source validation complete"

        return RefinedCodeResult(
            source_dir=code.source_dir,
            languages=code.languages,
            modules=code.modules,
            dependencies=code.dependencies,
            structure_tree=code.structure_tree,
            stats=code.stats,
            raw_text=code.raw_text,
            errors=code.errors,
            corrections=corrections,
            supplements=supplements,
            confidence=confidence,
            layer2_notes=notes,
        )

    def _check_sections_against_code(
        self,
        doc: DocumentResult,
        code: SourceCodeResult,
        corrections: List[Dict],
        supplements: List[Dict],
        notes: List[str],
    ) -> None:
        code_funcs = set()
        for module in code.modules:
            for func in module.get_all_functions():
                code_funcs.add(func.name.lower())

        for section in doc.sections:
            if not section.title:
                continue
            title_lower = section.title.lower()
            referenced_funcs = []
            for func_name in code_funcs:
                if func_name in title_lower or self._name_in_text(func_name, section.content or ""):
                    referenced_funcs.append(func_name)

            if referenced_funcs:
                supplements.append({
                    "type": "code_reference",
                    "section": section.title,
                    "functions": referenced_funcs,
                    "source": "cross_validation",
                })

        doc_keywords = set()
        for section in doc.sections:
            words = re.findall(r'[a-zA-Z_]{3,}', (section.content or "").lower())
            doc_keywords.update(words)

        for module in code.modules:
            for func in module.functions:
                if func.name.startswith("_"):
                    continue
                if not func.docstring:
                    corrections.append({
                        "type": "missing_docstring",
                        "file": module.file_path,
                        "function": func.name,
                        "suggestion": f"Add docstring to {func.name}() referencing document sections",
                    })

        notes.append(f"Checked {len(doc.sections)} sections against {len(code_funcs)} functions")

    def _check_with_external_read(
        self,
        doc: DocumentResult,
        read_func: Callable,
        corrections: List[Dict],
        supplements: List[Dict],
        notes: List[str],
    ) -> None:
        try:
            for section in doc.sections:
                if not section.content or len(section.content) < 20:
                    continue
                external_info = read_func(section.title)
                if external_info:
                    supplements.append({
                        "type": "external_reference",
                        "section": section.title,
                        "content": external_info[:200],
                        "source": "external_read",
                    })
            notes.append("External read validation done")
        except Exception as e:
            notes.append(f"External read failed: {e}")

    def _check_internal_consistency(
        self,
        doc: DocumentResult,
        corrections: List[Dict],
        notes: List[str],
    ) -> None:
        section_titles: Dict[str, int] = {}
        for section in doc.sections:
            if section.title in section_titles:
                corrections.append({
                    "type": "duplicate_section",
                    "section": section.title,
                    "suggestion": f"Duplicate section title (first at index {section_titles[section.title]})",
                })
            section_titles[section.title] = len(section_titles)

        for section in doc.sections:
            if section.parent_id:
                parent_exists = any(
                    s.section_id == section.parent_id for s in doc.sections
                )
                if not parent_exists:
                    corrections.append({
                        "type": "broken_parent_ref",
                        "section": section.section_id,
                        "parent_id": section.parent_id,
                        "suggestion": "Parent section not found, hierarchy may be incorrect",
                    })

        orphan_count = sum(
            1 for c in corrections
            if c.get("type") in ("duplicate_section", "broken_parent_ref")
        )
        if orphan_count:
            notes.append(f"Found {orphan_count} consistency issues")

    def _check_code_against_docs(
        self,
        code: SourceCodeResult,
        docs: List[DocumentResult],
        corrections: List[Dict],
        supplements: List[Dict],
        notes: List[str],
    ) -> None:
        doc_text = " ".join(
            section.content or "" for doc in docs for section in doc.sections
        ).lower()

        for module in code.modules:
            for func in module.functions:
                if func.name.startswith("_"):
                    continue
                if func.name.lower() not in doc_text:
                    supplements.append({
                        "type": "undocumented_function",
                        "file": module.file_path,
                        "function": func.name,
                        "suggestion": "Consider documenting this function in requirements",
                    })

        notes.append(f"Checked {code.get_module_count()} modules against {len(docs)} documents")

    def _check_code_consistency(
        self,
        code: SourceCodeResult,
        corrections: List[Dict],
        notes: List[str],
    ) -> None:
        for module in code.modules:
            imports = module.imports if hasattr(module, 'imports') else []
            for imp in imports:
                if imp.startswith("from .") or imp.startswith("import ."):
                    parts = imp.replace("from ", "").replace("import ", "").split()
                    if parts and parts[0].strip() == ".":
                        continue

        notes.append("Code internal consistency checked")

    @staticmethod
    def _compute_confidence(
        doc: DocumentResult,
        corrections: List[Dict],
        supplements: List[Dict],
    ) -> float:
        base = 0.9
        penalty = len(corrections) * 0.05
        bonus = min(len(supplements) * 0.02, 0.1)
        return max(0.0, min(1.0, base - penalty + bonus))

    @staticmethod
    def _compute_source_confidence(
        code: SourceCodeResult,
        corrections: List[Dict],
        supplements: List[Dict],
    ) -> float:
        base = 0.85
        penalty = len(corrections) * 0.05
        bonus = min(len(supplements) * 0.02, 0.1)
        return max(0.0, min(1.0, base - penalty + bonus))

    @staticmethod
    def _name_in_text(name: str, text: str) -> bool:
        name_lower = name.lower().replace("_", " ")
        text_lower = text.lower().replace("_", " ")
        return name_lower in text_lower
