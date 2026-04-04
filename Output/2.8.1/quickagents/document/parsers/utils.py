"""
Shared utility functions for document parsers.
"""

from typing import List, Dict, Any, Optional, Tuple

from ..models import DocumentSection


def find_parent_id(
    sections: List[DocumentSection], current_level: int
) -> Optional[str]:
    for sec in reversed(sections):
        if sec.level < current_level:
            return sec.section_id
    return None


def build_structure_tree_stack(sections: List[DocumentSection]) -> Dict:
    if not sections:
        return {}
    root: Dict[str, Any] = {"children": []}
    stack: List[Tuple[int, Dict]] = [(0, root)]

    for sec in sections:
        node: Dict[str, Any] = {
            "id": sec.section_id,
            "title": sec.title,
            "level": sec.level,
            "children": [],
        }
        while stack and stack[-1][0] >= sec.level:
            stack.pop()
        if stack:
            stack[-1][1]["children"].append(node)
        else:
            root["children"].append(node)
        stack.append((sec.level, node))

    return root


def build_tree_by_parent_id(sections: List[DocumentSection]) -> Dict:
    if not sections:
        return {}
    root: Dict[str, Any] = {"children": []}
    node_map: Dict[str, Dict] = {}

    for sec in sections:
        node: Dict[str, Any] = {
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
