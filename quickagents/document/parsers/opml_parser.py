"""
OPML Parser - Layer 1 parser for OPML outline files (.opml).

OPML (Outline Processor Markup Language) is an XML format for outlines.
Uses xml.etree.ElementTree for parsing.
"""

from pathlib import Path
from typing import List, Dict, Any
import logging
import xml.etree.ElementTree as ET

from . import BaseParser
from .utils import build_tree_by_parent_id
from ..models import DocumentResult, DocumentSection

logger = logging.getLogger(__name__)


class OPMLParser(BaseParser):
    """OPML outline parser"""

    SUPPORTED_FORMATS = ["opml"]
    REQUIRES_DEPENDENCIES = []
    PARSER_NAME = "opml"

    def parse(self, file_path: Path) -> DocumentResult:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"OPML file not found: {file_path}")

        logger.info(f"Parsing OPML: {file_path}")
        metadata = self._extract_metadata(file_path)

        tree = ET.parse(str(file_path))
        root_elem = tree.getroot()

        title = ""
        head = root_elem.find("head")
        if head is not None:
            title_elem = head.find("title")
            if title_elem is not None and title_elem.text:
                title = title_elem.text

        body = root_elem.find("body")
        if body is None:
            body = root_elem

        sections: List[DocumentSection] = []
        all_text: List[str] = []
        counter = [0]

        for outline in body.findall("outline"):
            text = outline.get("text", outline.get("title", ""))
            if not text:
                continue
            counter[0] += 1
            sec = DocumentSection(
                section_id=f"S{counter[0]:03d}",
                title=text,
                level=1,
                page_number=1,
            )
            sections.append(sec)
            all_text.append(text)

            note = outline.get("_note", "")
            if note:
                sec.content = note

            self._walk_outlines(
                outline, sections, all_text,
                sec.section_id, 2, counter
            )

        structure_tree = build_tree_by_parent_id(sections)
        raw_text = "\n".join(all_text)

        return DocumentResult(
            source_file=str(file_path),
            source_format="opml",
            title=title or file_path.stem,
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

    def _walk_outlines(
        self,
        parent: ET.Element,
        sections: List[DocumentSection],
        text_parts: List[str],
        parent_id: str,
        level: int,
        counter: list,
    ) -> None:
        """Recursively walk OPML outline elements"""
        for outline in parent.findall("outline"):
            text = outline.get("text", outline.get("title", ""))
            if not text:
                continue
            counter[0] += 1
            sec = DocumentSection(
                section_id=f"S{counter[0]:03d}",
                title=text,
                level=level,
                page_number=1,
                parent_id=parent_id,
            )
            sections.append(sec)
            text_parts.append("  " * (level - 1) + text)

            note = outline.get("_note", "")
            if note:
                sec.content = note

            self._walk_outlines(
                outline, sections, text_parts,
                sec.section_id, level + 1, counter
            )

    def _build_tree(self, sections: List[DocumentSection]) -> Dict:
        if not sections:
            return {}
        root: Dict[str, Any] = {"children": []}
        node_map: Dict[str, Dict] = {}
        for sec in sections:
            node = {
                "id": sec.section_id,
                "title": sec.title,
                "level": sec.level,
                "children": [],
            }
            node_map[sec.section_id] = node
            if sec.parent_id and sec.parent_id in node_map:
                node_map[sec.parent_id]["children"].append(node)
            else:
                root["children"].append(node)
        return root
