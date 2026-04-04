"""
Memory Sync - Minimal Unit

Syncs high-importance knowledge nodes to MEMORY.md.
"""

from pathlib import Path
from typing import List

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
        """
        Write nodes to MEMORY.md file.

        Args:
            memory_path: Path to write to
            nodes: Nodes to write
        """
        # Ensure parent directory exists
        path = Path(memory_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Build content
        content_parts = ["# Project Memory", "", "## Knowledge Graph Sync", ""]

        for node in nodes:
            content_parts.append(self.format_for_memory(node))
            content_parts.append("")

        # Write file
        path.write_text("\n".join(content_parts), encoding="utf-8")
