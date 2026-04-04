"""
Edge Manager - Minimal Unit

Manages knowledge edges with CRUD operations and ID generation.
"""

import time
import secrets
from typing import Optional, List

from ..types import EdgeType, KnowledgeEdge
from ..exceptions import InvalidEdgeTypeError
from ..interfaces import GraphStorageInterface


class EdgeManager:
    """
    Edge Manager - Minimal Unit for managing knowledge edges.

    Provides CRUD operations with automatic ID generation.
    """

    TYPE_SHORTS = {
        EdgeType.DEPENDS_ON: "dep",
        EdgeType.IS_SUBCLASS_OF: "sub",
        EdgeType.CITES: "cit",
        EdgeType.LINKS_TO: "lnk",
        EdgeType.EVOLVES_FROM: "evo",
        EdgeType.MAPS_TO: "map",
        EdgeType.AFFECTS: "aff",
        EdgeType.CONTRADICTS: "con",
        EdgeType.SUPPORTS: "sup",
        EdgeType.RELATED_TO: "rel",
        EdgeType.INDIRECTLY_RELATED_TO: "ind",
    }

    def __init__(self, storage: GraphStorageInterface):
        """
        Initialize EdgeManager.

        Args:
            storage: GraphStorageInterface implementation
        """
        self._storage = storage

    def create_edge(
        self, source_id: str, target_id: str, edge_type: EdgeType, **kwargs
    ) -> KnowledgeEdge:
        """
        Create single edge with auto-generated ID.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            edge_type: Type of edge (must be EdgeType enum)
            **kwargs: Additional edge properties (evidence, weight, confidence, metadata)

        Returns:
            Created KnowledgeEdge

        Raises:
            InvalidEdgeTypeError: If edge_type is not an EdgeType enum
            DuplicateEdgeError: If edge already exists (from storage)
            Exception: If source/target nodes don't exist (FK constraint)
        """
        if not isinstance(edge_type, EdgeType):
            raise InvalidEdgeTypeError(str(edge_type))

        edge_id = self._generate_id(edge_type)

        edge = KnowledgeEdge(
            id=edge_id,
            source_node_id=source_id,
            target_node_id=target_id,
            edge_type=edge_type,
            weight=kwargs.get("weight", 1.0),
            evidence=kwargs.get("evidence"),
            metadata=kwargs.get("metadata", {}),
            confidence=kwargs.get("confidence", 1.0),
        )

        return self._storage.create_edge(edge)

    def get_edge(self, edge_id: str) -> Optional[KnowledgeEdge]:
        """
        Get single edge by ID.

        Args:
            edge_id: Edge ID to retrieve

        Returns:
            KnowledgeEdge if found, None otherwise
        """
        return self._storage.get_edge(edge_id)

    def delete_edge(self, edge_id: str) -> bool:
        """
        Delete single edge.

        Args:
            edge_id: Edge ID to delete

        Returns:
            True if deleted, False if not found
        """
        return self._storage.delete_edge(edge_id)

    def get_outgoing_edges(
        self, node_id: str, edge_type: EdgeType = None
    ) -> List[KnowledgeEdge]:
        """
        Get edges where node is source.

        Args:
            node_id: Node ID to find outgoing edges for
            edge_type: Optional EdgeType to filter by

        Returns:
            List of KnowledgeEdge objects
        """
        filters = {"source_node_id": node_id}
        if edge_type is not None:
            filters["edge_type"] = edge_type.value

        return self._storage.query_edges(filters)

    def get_incoming_edges(
        self, node_id: str, edge_type: EdgeType = None
    ) -> List[KnowledgeEdge]:
        """
        Get edges where node is target.

        Args:
            node_id: Node ID to find incoming edges for
            edge_type: Optional EdgeType to filter by

        Returns:
            List of KnowledgeEdge objects
        """
        filters = {"target_node_id": node_id}
        if edge_type is not None:
            filters["edge_type"] = edge_type.value

        return self._storage.query_edges(filters)

    def _generate_id(self, edge_type: EdgeType) -> str:
        """
        Generate unique edge ID.

        Format: ke_{type_short}_{timestamp}_{random}

        Args:
            edge_type: EdgeType to generate ID for

        Returns:
            Unique edge ID string
        """
        type_short = self.TYPE_SHORTS.get(edge_type, "unk")
        timestamp = int(time.time() * 1000)
        random_hex = secrets.token_hex(4)

        return f"ke_{type_short}_{timestamp}_{random_hex}"
