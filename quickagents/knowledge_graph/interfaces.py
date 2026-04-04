"""
Knowledge Graph Interfaces

Abstract interfaces for pluggable storage and search backends.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from .types import KnowledgeNode, KnowledgeEdge


class GraphStorageInterface(ABC):
    """
    Abstract interface for graph storage backends.

    Implementations:
    - SQLiteGraphStorage (default)
    - Neo4jGraphStorage (future enterprise extension)
    """

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the storage backend."""
        pass

    @abstractmethod
    def create_node(self, node: KnowledgeNode) -> KnowledgeNode:
        """Create a node."""
        pass

    @abstractmethod
    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Get a node by ID."""
        pass

    @abstractmethod
    def update_node(self, node_id: str, updates: Dict[str, Any]) -> KnowledgeNode:
        """Update a node."""
        pass

    @abstractmethod
    def delete_node(self, node_id: str, cascade: bool = True) -> bool:
        """Delete a node."""
        pass

    @abstractmethod
    def create_edge(self, edge: KnowledgeEdge) -> KnowledgeEdge:
        """Create an edge."""
        pass

    @abstractmethod
    def get_edge(self, edge_id: str) -> Optional[KnowledgeEdge]:
        """Get an edge by ID."""
        pass

    @abstractmethod
    def delete_edge(self, edge_id: str) -> bool:
        """Delete an edge."""
        pass

    @abstractmethod
    def query_nodes(
        self, filters: Dict[str, Any], limit: int = 100, offset: int = 0
    ) -> List[KnowledgeNode]:
        """Query nodes with filters."""
        pass

    @abstractmethod
    def query_edges(
        self, filters: Dict[str, Any], limit: int = 100
    ) -> List[KnowledgeEdge]:
        """Query edges with filters."""
        pass

    @abstractmethod
    def find_path(
        self, from_node: str, to_node: str, max_depth: int = 5
    ) -> Optional[List[str]]:
        """Find path between two nodes."""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        pass


class VectorSearchInterface(ABC):
    """
    Abstract interface for vector search engines.

    Implementations:
    - SQLiteFTSSearch (default, uses FTS5)
    - ChromaDBVectorSearch (future enhanced extension)
    """

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the search engine."""
        pass

    @abstractmethod
    def index_node(self, node: KnowledgeNode) -> bool:
        """Index a node for search."""
        pass

    @abstractmethod
    def remove_node(self, node_id: str) -> bool:
        """Remove a node from the index."""
        pass

    @abstractmethod
    def search(
        self, query: str, top_k: int = 20, filters: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[str, float]]:
        """
        Search for nodes.

        Returns:
            List of (node_id, score) tuples.
        """
        pass

    @abstractmethod
    def get_embedding(self, node_id: str) -> Optional[List[float]]:
        """Get the embedding vector for a node."""
        pass
