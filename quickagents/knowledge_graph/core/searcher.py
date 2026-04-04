"""
Knowledge Searcher - Minimal Unit

Searches knowledge nodes using FTS5 full-text search.
"""

import time
from typing import List, Optional, Dict, Any

from ..types import NodeType, KnowledgeNode, SearchResult
from ..interfaces import GraphStorageInterface


class KnowledgeSearcher:
    """
    Knowledge Searcher - Minimal Unit for searching knowledge nodes.

    Uses FTS5 full-text search via storage layer.
    """

    def __init__(self, storage: GraphStorageInterface):
        """
        Initialize KnowledgeSearcher.

        Args:
            storage: GraphStorageInterface implementation
        """
        self._storage = storage

    def search(
        self,
        query: str,
        node_types: List[NodeType] = None,
        filters: Dict[str, Any] = None,
        sort_by: str = "relevance",
        limit: int = 20,
        offset: int = 0,
        expand_relations: bool = False,
        relation_depth: int = 1,
    ) -> SearchResult:
        """
        Unified search method.

        Uses FTS5 full-text index for efficient search.
        Falls back to Python-side filtering when needed.
        """
        start_time = time.time()
        filters = filters or {}

        try:
            node_type_val = None
            if node_types and len(node_types) == 1:
                node_type_val = node_types[0].value

            # FTS already handles LIMIT/OFFSET, no re-slicing needed
            matched_nodes = self._storage.search_fts(
                query=query,
                node_type=node_type_val,
                limit=limit,
                offset=offset,
            )

            if node_types and len(node_types) > 1:
                type_set = set(node_types)
                matched_nodes = [n for n in matched_nodes if n.node_type in type_set]

            # Filter by direct attributes (project_name, feature_id are
            # columns on the node, not inside metadata)
            for key in ["project_name", "feature_id"]:
                if key in filters:
                    matched_nodes = [
                        n
                        for n in matched_nodes
                        if getattr(n, key, None) == filters[key]
                    ]

            # Get total count from FTS (without pagination)
            total = self._storage.count_fts(
                query=query,
                node_type=node_type_val,
            )
        except Exception:
            matched_nodes = self._fallback_search(
                query, node_types, filters, limit, offset
            )
            total = len(matched_nodes)

        if sort_by == "importance":
            matched_nodes.sort(key=lambda n: n.importance, reverse=True)
        elif sort_by == "created_at":
            matched_nodes.sort(key=lambda n: n.created_at or 0, reverse=True)

        related_nodes = []
        if expand_relations and matched_nodes:
            related_nodes = self._expand_relations(matched_nodes, relation_depth)

        query_time_ms = (time.time() - start_time) * 1000

        return SearchResult(
            nodes=matched_nodes,
            total=total,
            has_more=(offset + limit) < total,
            query_time_ms=query_time_ms,
            related_nodes=related_nodes,
        )

    def search_by_tags(self, tags: List[str], limit: int = 100) -> List[KnowledgeNode]:
        """
        Search by tags.

        Args:
            tags: List of tags to search for
            limit: Maximum number of results

        Returns:
            List of matching KnowledgeNode objects
        """
        all_nodes = self._storage.query_nodes({}, limit=1000, offset=0)

        tags_lower = [t.lower() for t in tags]
        matched_nodes = []

        for node in all_nodes:
            node_tags_lower = [t.lower() for t in node.tags]
            if any(tag in node_tags_lower for tag in tags_lower):
                matched_nodes.append(node)

        return matched_nodes[:limit]

    def search_by_date_range(
        self, start_date: str, end_date: str, node_type: NodeType = None
    ) -> List[KnowledgeNode]:
        """
        Search by date range.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format (None for open-ended)
            node_type: Optional NodeType to filter by

        Returns:
            List of matching KnowledgeNode objects

        Raises:
            ValueError: If date format is invalid
        """
        from datetime import datetime

        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Invalid start_date format: {start_date}. Expected YYYY-MM-DD"
            ) from e

        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Invalid end_date format: {end_date}. Expected YYYY-MM-DD"
            ) from e

        db_filters = {}
        if node_type:
            db_filters["node_type"] = node_type.value

        all_nodes = self._storage.query_nodes(db_filters, limit=1000, offset=0)

        matched_nodes = []
        for node in all_nodes:
            if node.created_at is None:
                continue

            node_date = node.created_at

            if start_dt and node_date < start_dt:
                continue

            if end_dt and node_date > end_dt.replace(hour=23, minute=59, second=59):
                continue

            matched_nodes.append(node)

        return matched_nodes

    def _fallback_search(
        self,
        query: str,
        node_types: Optional[List[NodeType]],
        filters: Optional[Dict],
        limit: int,
        offset: int,
    ) -> List:
        """Fallback Python-side search when FTS5 is unavailable."""
        db_filters = {}
        if node_types and len(node_types) == 1:
            db_filters["node_type"] = node_types[0].value
        if filters:
            for key in ["project_name", "feature_id"]:
                if key in filters:
                    db_filters[key] = filters[key]

        all_nodes = self._storage.query_nodes(db_filters, limit=1000, offset=0)
        query_lower = query.lower()
        matched = []
        for node in all_nodes:
            if (
                query_lower in node.title.lower()
                or query_lower in node.content.lower()
                or any(query_lower in tag.lower() for tag in node.tags)
            ):
                if node_types and len(node_types) > 1:
                    if node.node_type not in node_types:
                        continue
                matched.append(node)
        return matched[offset : offset + limit]

    def _expand_relations(
        self, nodes: List[KnowledgeNode], depth: int
    ) -> List[KnowledgeNode]:
        """
        Expand relations for given nodes.

        Args:
            nodes: List of nodes to expand relations for
            depth: Depth of expansion

        Returns:
            List of related KnowledgeNode objects
        """
        if depth <= 0:
            return []

        related_ids = set()
        for node in nodes:
            edges = self._storage.query_edges({"source_node_id": node.id}, limit=100)
            for edge in edges:
                related_ids.add(edge.target_node_id)

            edges = self._storage.query_edges({"target_node_id": node.id}, limit=100)
            for edge in edges:
                related_ids.add(edge.source_node_id)

        # Do NOT exclude matched nodes from related_nodes.
        # related_nodes shows the full relationship neighborhood,
        # even if some nodes also appear in the search results.

        related_nodes = []
        for node_id in related_ids:
            node = self._storage.get_node(node_id)
            if node:
                related_nodes.append(node)

        return related_nodes
