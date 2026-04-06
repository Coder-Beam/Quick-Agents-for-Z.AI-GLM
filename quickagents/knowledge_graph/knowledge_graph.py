"""
Knowledge Graph Manager - Facade Pattern

Combines all minimal units, provides unified interface.
Single entry point for all knowledge graph operations.
"""

from typing import Optional, List, Dict, Any

from .types import NodeType, EdgeType, KnowledgeNode, KnowledgeEdge, SearchResult
from .storage.sqlite_storage import SQLiteGraphStorage
from .core.node_manager import NodeManager
from .core.edge_manager import EdgeManager
from .core.extractor import KnowledgeExtractor
from .core.discovery import RelationDiscovery
from .core.searcher import KnowledgeSearcher
from .core.memory_sync import MemorySync


class KnowledgeGraph:
    """
    Knowledge Graph Manager - Facade Pattern

    Combines all minimal units, provides unified interface.
    Single entry point for all knowledge graph operations.
    """

    def __init__(self, db_path: str = ".quickagents/unified.db"):
        """
        Initialize KnowledgeGraph with all sub-components.

        Creates SQLiteGraphStorage, initializes schema, and
        wires up all 6 core component instances.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.storage = SQLiteGraphStorage(db_path)
        self.storage.initialize({})

        self.nodes = NodeManager(self.storage)
        self.edges = EdgeManager(self.storage)
        self.extractor = KnowledgeExtractor(self.nodes)
        self.discovery = RelationDiscovery(self.storage, self.edges)
        self.searcher = KnowledgeSearcher(self.storage)
        self.sync = MemorySync(self.nodes)

    def create_node(self, node_type: NodeType, title: str, content: str, **kwargs) -> KnowledgeNode:
        """Create a knowledge node."""
        return self.nodes.create_node(node_type, title, content, **kwargs)

    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Get a node by ID."""
        return self.nodes.get_node(node_id)

    def update_node(self, node_id: str, **kwargs) -> KnowledgeNode:
        """Update a node."""
        return self.nodes.update_node(node_id, **kwargs)

    def delete_node(self, node_id: str, cascade: bool = True) -> bool:
        """Delete a node."""
        return self.nodes.delete_node(node_id, cascade=cascade)

    def list_nodes(
        self, node_type: Optional[NodeType] = None, limit: int = 100, offset: int = 0
    ) -> List[KnowledgeNode]:
        """List nodes with optional filter."""
        return self.nodes.list_nodes(node_type=node_type, limit=limit, offset=offset)

    def create_edge(self, source_id: str, target_id: str, edge_type: EdgeType, **kwargs) -> KnowledgeEdge:
        """Create an edge between nodes."""
        return self.edges.create_edge(source_id, target_id, edge_type, **kwargs)

    def get_edge(self, edge_id: str) -> Optional[KnowledgeEdge]:
        """Get an edge by ID."""
        return self.edges.get_edge(edge_id)

    def delete_edge(self, edge_id: str) -> bool:
        """Delete an edge."""
        return self.edges.delete_edge(edge_id)

    def get_outgoing_edges(self, node_id: str, edge_type: Optional[EdgeType] = None) -> List[KnowledgeEdge]:
        """Get outgoing edges for a node."""
        return self.edges.get_outgoing_edges(node_id, edge_type=edge_type)

    def get_incoming_edges(self, node_id: str, edge_type: Optional[EdgeType] = None) -> List[KnowledgeEdge]:
        """Get incoming edges for a node."""
        return self.edges.get_incoming_edges(node_id, edge_type=edge_type)

    def search(self, query: str, **kwargs) -> SearchResult:
        """Search knowledge nodes."""
        return self.searcher.search(query, **kwargs)

    def search_by_tags(self, tags: List[str], limit: int = 100) -> List[KnowledgeNode]:
        """Search by tags."""
        return self.searcher.search_by_tags(tags, limit=limit)

    def discover(self, node_id: str, strategies: Optional[List[str]] = None) -> List[KnowledgeEdge]:
        """
        Discover relations using specified strategies.

        Args:
            node_id: Node ID to discover relations for
            strategies: List of strategy names ('direct', 'semantic', 'structural', 'transitive')
                        Default: ['direct', 'semantic']

        Returns:
            List of discovered KnowledgeEdge objects
        """
        strategies = strategies or ["direct", "semantic"]
        discovered = []

        if "direct" in strategies:
            discovered.extend(self.discovery.discover_direct_relations(node_id))

        if "semantic" in strategies:
            discovered.extend(self.discovery.discover_semantic_relations(node_id))

        if "structural" in strategies:
            discovered.extend(self.discovery.discover_structural_relations(node_id))

        if "transitive" in strategies:
            discovered.extend(self.discovery.discover_transitive_relations(node_id))

        # 自动持久化发现的关系
        persisted = []
        for edge in discovered:
            try:
                # 跳过已存在的边（按 source+target+type 去重）
                existing = self.edges.get_outgoing_edges(edge.source_id)
                already_exists = (
                    any(e.target_id == edge.target_id and str(e.edge_type) == str(edge.edge_type) for e in existing)
                    if existing
                    else False
                )
                if not already_exists:
                    self.edges.create_edge(edge)
                    persisted.append(edge)
            except Exception:
                persisted.append(edge)  # 保留未持久化的

        return persisted if persisted else discovered

    def find_path(self, from_node: str, to_node: str, max_depth: int = 5) -> Optional[List[str]]:
        """Find path between two nodes."""
        return self.discovery.find_path(from_node, to_node, max_depth=max_depth)

    def trace_requirement(self, node_id: str, max_depth: int = 3) -> Dict[str, Any]:
        """Trace requirement chain."""
        return self.discovery.trace_requirement(node_id, max_depth=max_depth)

    def extract_from_text(self, text: str, **kwargs) -> List[KnowledgeNode]:
        """Extract knowledge from text."""
        return self.extractor.extract_from_text(text, **kwargs)

    def import_from_file(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Import knowledge from file."""
        return self.extractor.import_from_file(file_path, **kwargs)

    def sync_to_memory(self, memory_path: str = "Docs/MEMORY.md") -> int:
        """Sync high-importance nodes to MEMORY.md."""
        return self.sync.sync_to_memory(memory_path=memory_path)

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics."""
        return self.storage.get_stats()

    def show_relations(self, node_id: str, direction: str = "both") -> Dict[str, List[KnowledgeEdge]]:
        """
        Show all relations for a node.

        Args:
            node_id: Node ID
            direction: 'in', 'out', or 'both'

        Returns:
            Dict with 'incoming' and/or 'outgoing' edge lists
        """
        result = {}

        if direction in ("out", "both"):
            result["outgoing"] = self.edges.get_outgoing_edges(node_id)

        if direction in ("in", "both"):
            result["incoming"] = self.edges.get_incoming_edges(node_id)

        return result

    def close(self) -> None:
        """Close underlying storage connections."""
        if hasattr(self.storage, "close"):
            self.storage.close()
