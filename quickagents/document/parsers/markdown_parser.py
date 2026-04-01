"""
Markdown Outline Parser - Layer 1 parser for Markdown outline files (.md).

Parses heading hierarchy into a tree structure.
"""

from pathlib import Path
from typing import List
import logging
import re

from . import BaseParser
from .utils import find_parent_id, build_structure_tree_stack
from ..models import DocumentResult, DocumentSection

logger = logging.getLogger(__name__)


class MarkdownParser(BaseParser):
    """Markdown outline parser"""

    SUPPORTED_FORMATS = ["md"]
    REQUIRES_DEPENDENCIES = []
    PARSER_NAME = "markdown"

    _HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")

    def parse(self, file_path: Path) -> DocumentResult:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {file_path}")

        logger.info(f"Parsing Markdown: {file_path}")
        metadata = self._extract_metadata(file_path)

        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()

        sections: List[DocumentSection] = []
        all_text: List[str] = []
        counter = [0]
        content_buffer: List[str] = []
        current_section_id: str = ""

        for line in lines:
            m = self._HEADING_RE.match(line)
            if m:
                if current_section_id and content_buffer:
                    for sec in sections:
                        if sec.section_id == current_section_id:
                            sec.content = "\n".join(content_buffer).strip()
                            break
                    content_buffer = []

                level = len(m.group(1))
                title = m.group(2).strip()
                counter[0] += 1
                parent_id = find_parent_id(sections, level)
                sec = DocumentSection(
                    section_id=f"S{counter[0]:03d}",
                    title=title,
                    level=level,
                    page_number=1,
                    parent_id=parent_id,
                )
                sections.append(sec)
                all_text.append(title)
                current_section_id = sec.section_id
            else:
                stripped = line.strip()
                if stripped:
                    content_buffer.append(stripped)
                    all_text.append(stripped)

        if current_section_id and content_buffer:
            for sec in sections:
                if sec.section_id == current_section_id:
                    sec.content = "\n".join(content_buffer).strip()
                    break

        title = file_path.stem
        if sections and sections[0].level == 1:
            title = sections[0].title

        structure_tree = build_structure_tree_stack(sections)
        raw_text = content

        paragraphs = [
            p.strip() for p in content.split("\n\n") if p.strip()
        ]

        return DocumentResult(
            source_file=str(file_path),
            source_format="md",
            title=title,
            sections=sections,
            paragraphs=paragraphs,
            tables=[],
            images=[],
            formulas=[],
            structure_tree=structure_tree,
            metadata=metadata,
            raw_text=raw_text,
            errors=[],
        )
