"""
Node Manager - Minimal Unit

Manages knowledge nodes with CRUD operations and ID generation.
"""

import time
import secrets
from typing import Optional, List, Dict, Any

from ..types import NodeType, KnowledgeNode
from ..exceptions import InvalidNodeTypeError, NodeNotFoundError
from ..interfaces import GraphStorageInterface


class NodeManager:
    """
    Node Manager - Minimal Unit for managing knowledge nodes.
    
    Provides CRUD operations with automatic ID generation.
    """
    
    TYPE_SHORTS = {
        NodeType.REQUIREMENT: "req",
        NodeType.DECISION: "dec",
        NodeType.INSIGHT: "ins",
        NodeType.FACT: "fct",
        NodeType.CONCEPT: "cpt",
        NodeType.SOURCE: "src",
    }
    
    def __init__(self, storage: GraphStorageInterface):
        """
        Initialize NodeManager.
        
        Args:
            storage: GraphStorageInterface implementation
        """
        self._storage = storage
    
    def create_node(
        self,
        node_type: NodeType,
        title: str,
        content: str,
        **kwargs
    ) -> KnowledgeNode:
        """
        Create single node with auto-generated ID.
        
        Args:
            node_type: Type of node (must be NodeType enum)
            title: Node title
            content: Node content
            **kwargs: Additional node properties
            
        Returns:
            Created KnowledgeNode
            
        Raises:
            InvalidNodeTypeError: If node_type is not a NodeType enum
        """
        if not isinstance(node_type, NodeType):
            raise InvalidNodeTypeError(str(node_type))
        
        node_id = self._generate_id(node_type)
        
        node = KnowledgeNode(
            id=node_id,
            node_type=node_type,
            title=title,
            content=content,
            source_type=kwargs.get('source_type'),
            source_uri=kwargs.get('source_uri'),
            confidence=kwargs.get('confidence', 1.0),
            importance=kwargs.get('importance', 0.5),
            tags=kwargs.get('tags', []),
            metadata=kwargs.get('metadata', {}),
            project_name=kwargs.get('project_name'),
            feature_id=kwargs.get('feature_id'),
        )
        
        return self._storage.create_node(node)
    
    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """
        Get single node by ID.
        
        Args:
            node_id: Node ID to retrieve
            
        Returns:
            KnowledgeNode if found, None otherwise
        """
        return self._storage.get_node(node_id)
    
    def update_node(self, node_id: str, **kwargs) -> KnowledgeNode:
        """
        Update single node.
        
        Args:
            node_id: Node ID to update
            **kwargs: Fields to update
            
        Returns:
            Updated KnowledgeNode
            
        Raises:
            NodeNotFoundError: If node doesn't exist
        """
        node = self._storage.get_node(node_id)
        if node is None:
            raise NodeNotFoundError(node_id)
        
        if not kwargs:
            return node
        
        return self._storage.update_node(node_id, kwargs)
    
    def delete_node(self, node_id: str, cascade: bool = True) -> bool:
        """
        Delete single node.
        
        Args:
            node_id: Node ID to delete
            cascade: Whether to cascade delete (default True)
            
        Returns:
            True if deleted, False if not found
        """
        return self._storage.delete_node(node_id, cascade=cascade)
    
    def list_nodes(
        self,
        node_type: NodeType = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[KnowledgeNode]:
        """
        List nodes with optional type filter.
        
        Args:
            node_type: Optional NodeType to filter by
            limit: Maximum number of nodes to return
            offset: Number of nodes to skip
            
        Returns:
            List of KnowledgeNode objects
        """
        filters = {}
        if node_type is not None:
            filters['node_type'] = node_type.value
        
        return self._storage.query_nodes(filters, limit=limit, offset=offset)
    
    def _generate_id(self, node_type: NodeType) -> str:
        """
        Generate unique node ID.
        
        Format: kn_{type_short}_{timestamp}_{random}
        
        Args:
            node_type: NodeType to generate ID for
            
        Returns:
            Unique node ID string
        """
        type_short = self.TYPE_SHORTS.get(node_type, "unk")
        timestamp = int(time.time() * 1000)
        random_hex = secrets.token_hex(4)
        
        return f"kn_{type_short}_{timestamp}_{random_hex}"
