"""
Relation Discovery - Minimal Unit

Discovers relations between knowledge nodes through various methods:
- Direct relations (reference matching, links, shared tags)
- Semantic relations (content similarity)
- Structural relations (same feature/project, temporal proximity)
- Transitive relations (path-based)
"""

import re
from typing import List, Optional, Dict, Any, Set
from collections import deque

from ..types import EdgeType, KnowledgeEdge
from ..interfaces import GraphStorageInterface
from .edge_manager import EdgeManager


class RelationDiscovery:
    """
    Relation Discovery - Minimal Unit for discovering relations between nodes.
    """

    NODE_ID_PATTERN = re.compile(r"kn_[a-z]+_[a-z0-9_]+")
    MARKDOWN_LINK_PATTERN = re.compile(r"\[.*?\]\((kn_[a-z]+_[a-z0-9_]+)\)")

    def __init__(self, storage: GraphStorageInterface, edge_manager: EdgeManager):
        """
        Initialize RelationDiscovery.

        Args:
            storage: GraphStorageInterface implementation
            edge_manager: EdgeManager for creating discovered edges
        """
        self._storage = storage
        self._edge_manager = edge_manager

    def discover_direct_relations(self, node_id: str) -> List[KnowledgeEdge]:
        """
        Discover direct relations by reference matching.

        Looks for:
        - Node ID references in content (e.g., "kn_xxx")
        - Markdown links to nodes
        - Shared tags with other nodes

        Args:
            node_id: Node ID to discover relations for

        Returns:
            List of discovered KnowledgeEdge objects
        """
        node = self._storage.get_node(node_id)
        if not node:
            return []

        discovered = []
        referenced_ids = set()

        if node.content:
            for match in self.NODE_ID_PATTERN.finditer(node.content):
                referenced_ids.add(match.group())

            for match in self.MARKDOWN_LINK_PATTERN.finditer(node.content):
                referenced_ids.add(match.group(1))

        for ref_id in referenced_ids:
            if ref_id != node_id:
                target = self._storage.get_node(ref_id)
                if target:
                    edge = KnowledgeEdge(
                        id=f"ke_rel_{node_id}_{ref_id}",
                        source_node_id=node_id,
                        target_node_id=ref_id,
                        edge_type=EdgeType.RELATED_TO,
                        weight=0.8,
                        metadata={"discovery_method": "direct_reference"},
                    )
                    discovered.append(edge)

        if node.tags:
            for other in self._storage.query_nodes_by_tags(node.tags, limit=500):
                if other.id == node_id:
                    continue
                if other.tags:
                    shared_tags = set(node.tags) & set(other.tags)
                    if shared_tags:
                        edge = KnowledgeEdge(
                            id=f"ke_rel_{node_id}_{other.id}",
                            source_node_id=node_id,
                            target_node_id=other.id,
                            edge_type=EdgeType.RELATED_TO,
                            weight=len(shared_tags) / max(len(node.tags), len(other.tags)),
                            metadata={
                                "discovery_method": "shared_tags",
                                "shared_tags": list(shared_tags),
                            },
                        )
                        discovered.append(edge)

        return discovered

    def discover_semantic_relations(self, node_id: str, threshold: float = 0.7) -> List[KnowledgeEdge]:
        """
        Discover semantic relations by content similarity.

        Uses FTS5 search to find candidate nodes, then computes Jaccard
        similarity to filter below threshold.

        Args:
            node_id: Node ID to discover relations for
            threshold: Minimum similarity threshold (0.0-1.0)

        Returns:
            List of discovered KnowledgeEdge objects
        """
        node = self._storage.get_node(node_id)
        if not node:
            return []

        if not node.content or not node.content.strip():
            return []

        node_words = set(self._tokenize(node.content))
        if not node_words:
            return []

        discovered = []

        source_text = (node.title + " " + node.content)[:200]
        content_tokens = list(set(self._tokenize(source_text)))

        search_results = []
        for keyword in content_tokens[:6]:
            try:
                hits = self._storage.search_fts(keyword, limit=20)
                seen = {n.id for n in search_results}
                for n in hits:
                    if n.id not in seen:
                        search_results.append(n)
                        seen.add(n.id)
            except Exception:
                continue

        for other in search_results:
            if other.id == node_id:
                continue

            if not other.content or not other.content.strip():
                continue

            other_words = set(self._tokenize(other.content))
            if not other_words:
                continue

            similarity = self._jaccard_similarity(node_words, other_words)

            if similarity >= threshold:
                edge = KnowledgeEdge(
                    id=f"ke_rel_{node_id}_{other.id}",
                    source_node_id=node_id,
                    target_node_id=other.id,
                    edge_type=EdgeType.RELATED_TO,
                    weight=similarity,
                    metadata={"discovery_method": "semantic", "similarity": similarity},
                )
                discovered.append(edge)

        return discovered

    def discover_structural_relations(self, node_id: str) -> List[KnowledgeEdge]:
        """
        Discover structural relations (same feature/project, temporal proximity).

        Uses targeted SQL queries instead of loading all nodes.

        Args:
            node_id: Node ID to discover relations for

        Returns:
            List of discovered KnowledgeEdge objects
        """
        node = self._storage.get_node(node_id)
        if not node:
            return []

        discovered = []
        seen_ids = set()

        if node.feature_id:
            for other in self._storage.query_nodes({"feature_id": node.feature_id}, limit=100):
                if other.id != node_id and other.id not in seen_ids:
                    seen_ids.add(other.id)
                    discovered.append(
                        KnowledgeEdge(
                            id=f"ke_rel_{node_id}_{other.id}",
                            source_node_id=node_id,
                            target_node_id=other.id,
                            edge_type=EdgeType.RELATED_TO,
                            weight=0.9,
                            metadata={"discovery_method": "structural", "reason": "same_feature"},
                        )
                    )

        if node.project_name:
            for other in self._storage.query_nodes({"project_name": node.project_name}, limit=100):
                if other.id != node_id and other.id not in seen_ids:
                    seen_ids.add(other.id)
                    discovered.append(
                        KnowledgeEdge(
                            id=f"ke_rel_{node_id}_{other.id}",
                            source_node_id=node_id,
                            target_node_id=other.id,
                            edge_type=EdgeType.RELATED_TO,
                            weight=0.7,
                            metadata={"discovery_method": "structural", "reason": "same_project"},
                        )
                    )

        if node.created_at and not node.project_name and not node.feature_id:
            time_bound = 3600
            for other in self._storage.query_nodes({}, limit=200):
                if other.id == node_id or other.id in seen_ids:
                    continue
                if other.created_at and not other.project_name and not other.feature_id:
                    time_diff = abs((node.created_at - other.created_at).total_seconds())
                    if time_diff < time_bound:
                        seen_ids.add(other.id)
                        discovered.append(
                            KnowledgeEdge(
                                id=f"ke_rel_{node_id}_{other.id}",
                                source_node_id=node_id,
                                target_node_id=other.id,
                                edge_type=EdgeType.RELATED_TO,
                                weight=0.5,
                                metadata={"discovery_method": "structural", "reason": "temporal_proximity"},
                            )
                        )

        return discovered

    def discover_transitive_relations(self, node_id: str, max_depth: int = 3) -> List[KnowledgeEdge]:
        """
        Discover transitive relations (A→B, B→C implies A→C).

        Args:
            node_id: Node ID to discover relations for
            max_depth: Maximum traversal depth

        Returns:
            List of discovered KnowledgeEdge objects
        """
        node = self._storage.get_node(node_id)
        if not node:
            return []

        discovered = []
        visited = set()
        queue = deque([(node_id, 0)])
        reachable = set()

        while queue:
            current_id, depth = queue.popleft()

            if current_id in visited:
                continue

            visited.add(current_id)

            if depth >= max_depth:
                continue

            outgoing = self._edge_manager.get_outgoing_edges(current_id)

            for edge in outgoing:
                target_id = edge.target_node_id
                if target_id not in visited:
                    queue.append((target_id, depth + 1))
                    if target_id != node_id:
                        reachable.add(target_id)

        for target_id in reachable:
            direct_edge = self._edge_manager.get_outgoing_edges(node_id)
            has_direct = any(e.target_node_id == target_id for e in direct_edge)

            if not has_direct:
                edge = KnowledgeEdge(
                    id=f"ke_ind_{node_id}_{target_id}",
                    source_node_id=node_id,
                    target_node_id=target_id,
                    edge_type=EdgeType.INDIRECTLY_RELATED_TO,
                    weight=0.5,
                    metadata={"discovery_method": "transitive"},
                )
                discovered.append(edge)

        return discovered

    def find_path(self, from_node: str, to_node: str, max_depth: int = 5) -> Optional[List[str]]:
        """
        Find shortest path between nodes using BFS.

        Args:
            from_node: Starting node ID
            to_node: Target node ID
            max_depth: Maximum search depth

        Returns:
            List of node IDs forming the path, or None if no path found
        """
        if from_node == to_node:
            return [from_node]

        source = self._storage.get_node(from_node)
        target = self._storage.get_node(to_node)

        if not source or not target:
            return None

        visited = {from_node}
        queue = deque([(from_node, [from_node])])

        while queue:
            current_id, path = queue.popleft()

            if len(path) > max_depth:
                continue

            outgoing = self._edge_manager.get_outgoing_edges(current_id)

            for edge in outgoing:
                next_id = edge.target_node_id

                if next_id == to_node:
                    return path + [next_id]

                if next_id not in visited:
                    visited.add(next_id)
                    queue.append((next_id, path + [next_id]))

        return None

    def trace_requirement(self, node_id: str, max_depth: int = 3) -> Dict[str, Any]:
        """
        Trace requirement chain following DEPENDS_ON and MAPS_TO edges.

        Args:
            node_id: Requirement node ID to trace
            max_depth: Maximum traversal depth

        Returns:
            Dictionary with node_id, chains, and related nodes
        """
        node = self._storage.get_node(node_id)
        if not node:
            return {
                "node_id": node_id,
                "chains": [],
                "related": [],
                "error": "Node not found",
            }

        chains = []
        related = []
        visited = set()

        def trace(current_id: str, path: List[str], depth: int):
            if depth > max_depth or current_id in visited:
                return

            visited.add(current_id)

            edges = self._edge_manager.get_outgoing_edges(current_id)

            for edge in edges:
                if edge.edge_type in (EdgeType.DEPENDS_ON, EdgeType.MAPS_TO):
                    target_id = edge.target_node_id
                    new_path = path + [target_id]

                    if edge.edge_type == EdgeType.MAPS_TO:
                        chains.append(
                            {
                                "type": "maps_to",
                                "path": new_path,
                                "target_id": target_id,
                            }
                        )
                    else:
                        chains.append(
                            {
                                "type": "depends_on",
                                "path": new_path,
                                "target_id": target_id,
                            }
                        )

                    related.append({"node_id": target_id, "relation": edge.edge_type.value})

                    trace(target_id, new_path, depth + 1)

        trace(node_id, [node_id], 0)

        return {"node_id": node_id, "chains": chains, "related": related}

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words.

        Args:
            text: Text to tokenize

        Returns:
            List of lowercase words
        """
        words = re.findall(r"\b\w+\b", text.lower())
        return [w for w in words if len(w) > 1]

    def _jaccard_similarity(self, set1: Set[str], set2: Set[str]) -> float:
        """
        Calculate Jaccard similarity between two sets.

        Args:
            set1: First set
            set2: Second set

        Returns:
            Jaccard similarity (0.0-1.0)
        """
        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0
