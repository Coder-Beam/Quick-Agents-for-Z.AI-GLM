"""
PDF Parser - Layer 1 document parsing for PDF files.

Uses PyMuPDF (fitz) for text extraction, structure detection,
table extraction, and image extraction.
Falls back to pdfplumber for table extraction when needed.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from . import BaseParser
from .utils import find_parent_id, build_structure_tree_stack
from ..models import (
    DocumentResult,
    DocumentSection,
    DocumentTable,
    DocumentImage,
)

logger = logging.getLogger(__name__)


class PDFParser(BaseParser):
    """PDF document parser using PyMuPDF + pdfplumber"""

    SUPPORTED_FORMATS = ["pdf"]
    REQUIRES_DEPENDENCIES = ["fitz", "pdfplumber"]
    PARSER_NAME = "pdf"

    def __init__(self):
        super().__init__()
        self._fitz = None
        self._pdfplumber = None
        if self._deps_available:
            import fitz
            import pdfplumber

            self._fitz = fitz
            self._pdfplumber = pdfplumber

    def parse(self, file_path: Path) -> DocumentResult:
        """Parse a PDF file and return DocumentResult"""
        if not self._deps_available:
            raise ImportError(
                "PDF parsing requires [document] dependencies. "
                "Install with: pip install quickagents[document]"
            )

        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        logger.info(f"Parsing PDF: {file_path}")
        metadata = self._extract_metadata(file_path)

        doc = self._fitz.open(str(file_path))
        try:
            pdf_metadata = self._extract_pdf_metadata(doc)
            title = pdf_metadata.get("title") or file_path.stem

            raw_text = self._extract_text_all_pages(doc)
            paragraphs = self._extract_paragraphs(doc)
            sections = self._detect_sections(doc)
            tables = self._extract_tables(file_path, doc)
            images = self._extract_images(doc)
            structure_tree = build_structure_tree_stack(sections)

            return DocumentResult(
                source_file=str(file_path),
                source_format="pdf",
                title=title,
                sections=sections,
                paragraphs=paragraphs,
                tables=tables,
                images=images,
                formulas=[],
                structure_tree=structure_tree,
                metadata={**metadata, **pdf_metadata, "page_count": len(doc)},
                raw_text=raw_text,
                errors=[],
            )
        finally:
            doc.close()

    def _extract_pdf_metadata(self, doc) -> Dict[str, Any]:
        """Extract PDF metadata"""
        meta = doc.metadata or {}
        return {
            "title": meta.get("title", ""),
            "author": meta.get("author", ""),
            "subject": meta.get("subject", ""),
            "creator": meta.get("creator", ""),
            "producer": meta.get("producer", ""),
            "creation_date": meta.get("creationDate", ""),
            "mod_date": meta.get("modDate", ""),
        }

    def _extract_text_all_pages(self, doc) -> str:
        """Extract all text from PDF"""
        parts = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            if text.strip():
                parts.append(text)
        return "\n\n".join(parts)

    def _extract_paragraphs(self, doc) -> List[str]:
        """Extract paragraphs from PDF"""
        paragraphs = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            for block in text.split("\n\n"):
                block = block.strip()
                if block and len(block) > 10:
                    paragraphs.append(block)
        return paragraphs

    def _detect_sections(self, doc) -> List[DocumentSection]:
        """
        Detect section structure by analyzing font sizes and numbering patterns.
        Larger fonts indicate higher-level headings.
        """
        section_counter = 0
        sections: List[DocumentSection] = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    line_text = ""
                    line_size = 0.0
                    for span in line.get("spans", []):
                        line_text += span.get("text", "")
                        if span.get("text", "").strip():
                            line_size = span.get("size", 0.0)

                    line_text = line_text.strip()
                    if not line_text:
                        continue

                    level = self._infer_heading_level(line_text, line_size, doc)
                    if level is not None:
                        section_counter += 1
                        sid = f"S{section_counter:03d}"
                        parent_id = find_parent_id(sections, level)
                        sections.append(
                            DocumentSection(
                                section_id=sid,
                                title=line_text,
                                level=level,
                                page_number=page_num + 1,
                                parent_id=parent_id,
                            )
                        )

        self._populate_section_content(sections, doc)
        return sections

    def _infer_heading_level(self, text: str, font_size: float, doc) -> Optional[int]:
        """
        Infer heading level from font size and numbering pattern.
        Returns None if not a heading.
        """
        import re

        numbered = re.match(r"^(\d+(?:\.\d+)*)\s+(.+)$", text)
        if numbered:
            depth = len(numbered.group(1).split("."))
            if depth <= 6:
                return depth

        if text.isupper() and len(text) > 3 and len(text) <= 80:
            return 1

        body_size = self._get_body_font_size(doc)
        if body_size and font_size > body_size * 1.2:
            ratio = font_size / body_size
            if ratio >= 1.8:
                return 1
            elif ratio >= 1.4:
                return 2
            else:
                return 3

        return None

    def _get_body_font_size(self, doc) -> Optional[float]:
        """Get the most common (body) font size in the document"""
        size_counts: Dict[float, int] = {}
        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if text:
                            size = round(span.get("size", 0.0), 1)
                            if size > 0:
                                size_counts[size] = size_counts.get(size, 0) + len(text)
        if not size_counts:
            return None
        return max(size_counts, key=size_counts.get)  # type: ignore[arg-type]

    def _populate_section_content(self, sections: List[DocumentSection], doc) -> None:
        """Fill section content from page text"""
        if not sections:
            return
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            for sec in sections:
                if sec.page_number == page_num + 1:
                    idx = text.find(sec.title)
                    if idx >= 0:
                        after = text[idx + len(sec.title) :].strip()
                        next_heading_pos = self._find_next_heading(
                            after, sections, page_num + 1
                        )
                        if next_heading_pos > 0:
                            after = after[:next_heading_pos].strip()
                        if len(after) > 500:
                            after = after[:500]
                        sec.content = after

    def _find_next_heading(
        self, text: str, sections: List[DocumentSection], page: int
    ) -> int:
        """Find position of next heading in text"""
        for sec in sections:
            if sec.page_number >= page:
                pos = text.find(sec.title)
                if pos > 0:
                    return pos
        return -1

    def _extract_tables(self, file_path: Path, doc) -> List[DocumentTable]:
        """
        Extract tables using PyMuPDF first, fallback to pdfplumber.
        """
        tables = self._extract_tables_fitz(doc)
        if not tables:
            tables = self._extract_tables_pdfplumber(file_path)
        return tables

    def _extract_tables_fitz(self, doc) -> List[DocumentTable]:
        """Extract tables using PyMuPDF"""
        tables: List[DocumentTable] = []
        table_counter = 0
        for page_num in range(len(doc)):
            page = doc[page_num]
            try:
                page_tables = page.find_tables()
            except Exception:
                continue
            for tab in page_tables:
                table_counter += 1
                rows = tab.extract()
                if not rows or len(rows) < 2:
                    continue
                headers = [str(c).strip() if c else "" for c in rows[0]]
                data_rows = []
                for row in rows[1:]:
                    data_rows.append([str(c).strip() if c else "" for c in row])
                tables.append(
                    DocumentTable(
                        table_id=f"T{table_counter:03d}",
                        page_number=page_num + 1,
                        headers=headers,
                        rows=data_rows,
                    )
                )
        return tables

    def _extract_tables_pdfplumber(self, file_path: Path) -> List[DocumentTable]:
        """Extract tables using pdfplumber as fallback"""
        if self._pdfplumber is None:
            return []
        tables: List[DocumentTable] = []
        table_counter = 0
        try:
            with self._pdfplumber.open(str(file_path)) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    for tab in page.extract_tables():
                        table_counter += 1
                        if not tab or len(tab) < 2:
                            continue
                        headers = [str(c).strip() if c else "" for c in tab[0]]
                        data_rows = []
                        for row in tab[1:]:
                            data_rows.append([str(c).strip() if c else "" for c in row])
                        tables.append(
                            DocumentTable(
                                table_id=f"T{table_counter:03d}",
                                page_number=page_num + 1,
                                headers=headers,
                                rows=data_rows,
                            )
                        )
        except Exception as e:
            logger.warning(f"pdfplumber table extraction failed: {e}")
        return tables

    def _extract_images(self, doc) -> List[DocumentImage]:
        """Extract image metadata from PDF"""
        images: List[DocumentImage] = []
        img_counter = 0
        seen_xrefs = set()

        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images(full=True)
            for img_info in image_list:
                xref = img_info[0]
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)
                img_counter += 1

                img_type = "unknown"

                try:
                    base_image = doc.extract_image(xref)
                    img_ext = base_image.get("ext", "unknown")
                    img_type = img_ext
                except Exception:
                    pass

                width = img_info[2] if len(img_info) > 2 else 0
                height = img_info[3] if len(img_info) > 3 else 0

                images.append(
                    DocumentImage(
                        image_id=f"IMG{img_counter:03d}",
                        image_type=img_type,
                        page_number=page_num + 1,
                        description=f"Image {img_counter} ({width}x{height})",
                    )
                )
        return images
