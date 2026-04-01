"""
XMind Parser - Layer 1 parser for XMind mind map files (.xmind).

XMind files are ZIP archives containing JSON/XML content.
Uses the xmind library for structured parsing.
"""

from pathlib import Path
from typing import List, Dict, Any
import logging

from . import BaseParser
from .utils import build_tree_by_parent_id
from ..models import DocumentResult, DocumentSection

logger = logging.getLogger(__name__)


class XMindParser(BaseParser):
    """XMind mind map parser"""

    SUPPORTED_FORMATS = ["xmind"]
    REQUIRES_DEPENDENCIES = ["xmind"]
    PARSER_NAME = "xmind"

    def __init__(self):
        super().__init__()
        self._xmind = None
        if self._deps_available:
            import xmind
            self._xmind = xmind

    def parse(self, file_path: Path) -> DocumentResult:
        if not self._deps_available:
            raise ImportError(
                "XMind parsing requires the xmind library. "
                "Install with: pip install XMind"
            )

        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"XMind file not found: {file_path}")

        logger.info(f"Parsing XMind: {file_path}")
        metadata = self._extract_metadata(file_path)

        wb = self._xmind.load(str(file_path))
        sections: List[DocumentSection] = []
        all_text_parts: List[str] = []
        counter = [0]

        for sheet in wb.getSheets():
            sheet_title = sheet.getTitle() or "Untitled Sheet"
            counter[0] += 1
            sheet_section = DocumentSection(
                section_id=f"S{counter[0]:03d}",
                title=sheet_title,
                level=1,
                page_number=1,
            )
            sections.append(sheet_section)

            root = sheet.getRootTopic()
            if root is None:
                continue

            root_title = root.getTitle()
            if root_title:
                counter[0] += 1
                root_section = DocumentSection(
                    section_id=f"S{counter[0]:03d}",
                    title=root_title,
                    level=2,
                    page_number=1,
                    parent_id=sheet_section.section_id,
                )
                sections.append(root_section)
                all_text_parts.append(root_title)
                self._walk_topics(
                    root, sections, all_text_parts,
                    root_section.section_id, 3, counter
                )

        structure_tree = build_tree_by_parent_id(sections)
        raw_text = "\n".join(all_text_parts)

        return DocumentResult(
            source_file=str(file_path),
            source_format="xmind",
            title=file_path.stem,
            sections=sections,
            paragraphs=[],
            tables=[],
            images=[],
            formulas=[],
            structure_tree=structure_tree,
            metadata=metadata,
            raw_text=raw_text,
            errors=[],
        )

    def _walk_topics(
        self,
        topic,
        sections: List[DocumentSection],
        text_parts: List[str],
        parent_id: str,
        level: int,
        counter: list,
    ) -> None:
        """Recursively walk topic tree"""
        children = topic.getSubTopics() or []
        for child in children:
            title = child.getTitle()
            if not title:
                continue
            counter[0] += 1
            sec = DocumentSection(
                section_id=f"S{counter[0]:03d}",
                title=title,
                level=level,
                page_number=1,
                parent_id=parent_id,
            )
            sections.append(sec)
            text_parts.append("  " * (level - 1) + title)

            notes = child.getNotes()
            if notes:
                note_text = self._extract_notes(notes)
                if note_text:
                    sec.content = note_text
                    text_parts.append(note_text)

            self._walk_topics(
                child, sections, text_parts,
                sec.section_id, level + 1, counter
            )

    def _extract_notes(self, notes) -> str:
        """Extract plain text from notes"""
        if isinstance(notes, str):
            return notes
        if hasattr(notes, "getTextContent"):
            return notes.getTextContent() or ""
        if hasattr(notes, "plain"):
            return notes.plain or ""
        return ""
