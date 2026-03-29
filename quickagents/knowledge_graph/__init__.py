"""Knowledge Graph module for QuickAgents."""

from .types import NodeType, EdgeType, KnowledgeNode, KnowledgeEdge, SearchResult
from .exceptions import (
    KnowledgeGraphError,
    NodeNotFoundError,
    EdgeNotFoundError,
    DuplicateNodeError,
    DuplicateEdgeError,
    InvalidNodeTypeError,
    InvalidEdgeTypeError,
    CircularDependencyError,
    DatabaseIntegrityError,
    ExtractionError,
    SyncError,
)

# Note: KnowledgeGraph will be added in Part 3
# from .knowledge_graph import KnowledgeGraph

__all__ = [
    'NodeType',
    'EdgeType',
    'KnowledgeNode',
    'KnowledgeEdge',
    'SearchResult',
    # Exceptions
    'KnowledgeGraphError',
    'NodeNotFoundError',
    'EdgeNotFoundError',
    'DuplicateNodeError',
    'DuplicateEdgeError',
    'InvalidNodeTypeError',
    'InvalidEdgeTypeError',
    'CircularDependencyError',
    'DatabaseIntegrityError',
    'ExtractionError',
    'SyncError',
    # 'KnowledgeGraph',  # Will be added in Part 3
]
