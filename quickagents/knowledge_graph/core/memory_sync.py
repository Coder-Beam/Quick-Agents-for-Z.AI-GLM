"""
Memory Sync - Minimal Unit

Syncs high-importance knowledge nodes to MEMORY.md.
"""

from pathlib import Path
from typing import List
from datetime import datetime

from ..types import NodeType, KnowledgeNode
from .node_manager import NodeManager


class MemorySync:
    """
    Memory Sync - Minimal Unit for syncing knowledge to MEMORY.md.

    Filters high-importance nodes and formats them for human-readable documentation.
    """

    SYNC_TYPES = {NodeType.REQUIREMENT, NodeType.DECISION, NodeType.FACT}
    MIN_IMPORTANCE = 0.7
    MIN_CONFIDENCE = 0.8

    def __init__(self, node_manager: NodeManager):
        """
        Initialize MemorySync.

        Args:
            node_manager: NodeManager instance for accessing nodes
        """
        self._node_manager = node_manager

    def sync_to_memory(self, memory_path: str = "Docs/MEMORY.md") -> int:
        """
        Sync high-importance nodes to MEMORY.md.

        Args:
            memory_path: Path to MEMORY.md file

        Returns:
            Number of nodes synced, 0 on error
        """
        try:
            # Get all nodes from storage
            nodes = self._node_manager.list_nodes(limit=1000)

            # Filter candidates
            candidates = self.filter_sync_candidates(nodes)

            if not candidates:
                # Create empty file
                self._write_memory_file(memory_path, [])
                return 0

            # Format and write
            self._write_memory_file(memory_path, candidates)
            return len(candidates)

        except (PermissionError, OSError, ValueError):
            return 0

    def filter_sync_candidates(self, nodes: List[KnowledgeNode]) -> List[KnowledgeNode]:
        """
        Filter nodes that should be synced.

        Criteria:
        - importance >= 0.7
        - node_type in [REQUIREMENT, DECISION, FACT]
        - confidence >= 0.8

        Args:
            nodes: List of nodes to filter

        Returns:
            Filtered list of nodes meeting all criteria
        """
        if not nodes:
            return []

        candidates = []
        for node in nodes:
            if (
                node.importance >= self.MIN_IMPORTANCE
                and node.node_type in self.SYNC_TYPES
                and node.confidence >= self.MIN_CONFIDENCE
            ):
                candidates.append(node)

        return candidates

    def format_for_memory(self, node: KnowledgeNode) -> str:
        """
        Format node for MEMORY.md.

        Format:
        ```markdown
        ### {node_type}: {title}

        {content}

        **Tags:** {tags}
        **Confidence:** {confidence}
        **Source:** {source_uri}
        ---
        ```

        Args:
            node: KnowledgeNode to format

        Returns:
            Formatted markdown string
        """
        lines = [
            f"### {node.node_type.name}: {node.title}",
            "",
            node.content,
            "",
            f"**Tags:** {', '.join(node.tags)}",
            f"**Confidence:** {node.confidence}",
            f"**Source:** {node.source_uri or 'N/A'}",
        ]

        # Add metadata if present
        if node.metadata:
            lines.append("**Metadata:**")
            for key, value in node.metadata.items():
                lines.append(f"  - {key}: {value}")

        lines.append("---")

        return "\n".join(lines)

    def _write_memory_file(self, memory_path: str, nodes: List[KnowledgeNode]) -> None:
        """将高重要度节点追加到 MEMORY.md 的 KG Sync section（不破坏现有内容）"""
        path = Path(memory_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # 如果文件不存在，创建新文件
        if not path.exists():
            header = "# Project Memory\n\nAuto-synced by QuickAgents Knowledge Graph.\n\n"
            path.write_text(header, encoding="utf-8")

        # 读取现有内容
        existing = path.read_text(encoding="utf-8")

        # 查找 KG Sync section 的边界
        section_marker = "## Knowledge Graph Sync"
        if section_marker in existing:
            # 截断到 section_marker 之前
            content_before = existing[: existing.index(section_marker)]
        else:
            content_before = existing.rstrip() + "\n\n"

        # 构建 KG section
        kg_section = f"{section_marker}\n> 自动同步: {datetime.now().isoformat()}\n\n"
        for node in nodes:
            kg_section += f"### {node.title}\n"
            kg_section += f"- 类型: {node.node_type.value if hasattr(node.node_type, 'value') else node.node_type}\n"
            kg_section += f"- 重要度: {node.importance:.1f}\n"
            if node.content:
                kg_section += f"- 内容: {node.content[:200]}\n"
            kg_section += "\n"

        path.write_text(content_before + kg_section, encoding="utf-8")
