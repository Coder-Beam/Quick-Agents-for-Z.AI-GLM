"""
FreeMind Parser - Layer 1 parser for FreeMind mind map files (.mm).

FreeMind files are XML documents with a specific schema.
Uses xml.etree.ElementTree for parsing.
"""

from pathlib import Path
from typing import List
import logging
import xml.etree.ElementTree as ET

from . import BaseParser
from .utils import build_tree_by_parent_id
from ..models import DocumentResult, DocumentSection

logger = logging.getLogger(__name__)


class FreeMindParser(BaseParser):
    """FreeMind .mm mind map parser"""

    SUPPORTED_FORMATS = ["mm"]
    REQUIRES_DEPENDENCIES = []
    PARSER_NAME = "freemind"

    def parse(self, file_path: Path) -> DocumentResult:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"FreeMind file not found: {file_path}")

        logger.info(f"Parsing FreeMind: {file_path}")
        metadata = self._extract_metadata(file_path)

        tree = ET.parse(str(file_path))
        root_elem = tree.getroot()

        sections: List[DocumentSection] = []
        all_text: List[str] = []
        counter = [0]

        root_node = root_elem.find(".//node")
        if root_node is None:
            root_node = root_elem

        root_text = root_node.get("TEXT", root_node.get("text", ""))
        if root_text:
            counter[0] += 1
            root_section = DocumentSection(
                section_id=f"S{counter[0]:03d}",
                title=root_text,
                level=1,
                page_number=1,
            )
            sections.append(root_section)
            all_text.append(root_text)
            self._walk_nodes(
                root_node, sections, all_text,
                root_section.section_id, 2, counter
            )

        structure_tree = build_tree_by_parent_id(sections)
        raw_text = "\n".join(all_text)

        return DocumentResult(
            source_file=str(file_path),
            source_format="mm",
            title=root_text or file_path.stem,
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

    def _walk_nodes(
        self,
        parent_elem,
        sections: List[DocumentSection],
        text_parts: List[str],
        parent_id: str,
        level: int,
        counter: list,
    ) -> None:
        """Recursively walk FreeMind XML nodes"""
        for node in parent_elem.findall("node"):
            text = node.get("TEXT", node.get("text", ""))
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

            richcontent = node.find(".//richcontent")
            if richcontent is not None:
                content = self._extract_richcontent(richcontent)
                if content:
                    sec.content = content

            self._walk_nodes(
                node, sections, text_parts,
                sec.section_id, level + 1, counter
            )

    def _extract_richcontent(self, elem: ET.Element) -> str:
        """Extract text content from richcontent HTML"""
        parts = []
        for p in elem.iter("p"):
            text = "".join(p.itertext()).strip()
            if text:
                parts.append(text)
        return "\n".join(parts)
