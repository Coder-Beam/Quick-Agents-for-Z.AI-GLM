"""
Knowledge Graph Exceptions

Custom exceptions for knowledge graph operations.
"""

from typing import List


class KnowledgeGraphError(Exception):
    """Base exception for knowledge graph operations."""
    pass


class NodeNotFoundError(KnowledgeGraphError):
    """Raised when a node is not found."""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        super().__init__(f"Node not found: {node_id}")


class EdgeNotFoundError(KnowledgeGraphError):
    """Raised when an edge is not found."""
    
    def __init__(self, edge_id: str):
        self.edge_id = edge_id
        super().__init__(f"Edge not found: {edge_id}")


class DuplicateNodeError(KnowledgeGraphError):
    """Raised when attempting to create a duplicate node."""
    
    def __init__(self, title: str, existing_id: str):
        self.title = title
        self.existing_id = existing_id
        super().__init__(f"Duplicate node with similar title: {title} (existing: {existing_id})")


class DuplicateEdgeError(KnowledgeGraphError):
    """Raised when attempting to create a duplicate edge."""
    
    def __init__(self, source_id: str, target_id: str, edge_type: str):
        self.source_id = source_id
        self.target_id = target_id
        self.edge_type = edge_type
        super().__init__(f"Edge already exists: {source_id} -> {target_id} ({edge_type})")


class InvalidNodeTypeError(KnowledgeGraphError):
    """Raised when an invalid node type is provided."""
    
    def __init__(self, node_type: str):
        self.node_type = node_type
        super().__init__(f"Invalid node type: {node_type}")


class InvalidEdgeTypeError(KnowledgeGraphError):
    """Raised when an invalid edge type is provided."""
    
    def __init__(self, edge_type: str):
        self.edge_type = edge_type
        super().__init__(f"Invalid edge type: {edge_type}")


class CircularDependencyError(KnowledgeGraphError):
    """Raised when a circular dependency is detected."""
    
    def __init__(self, path: List[str]):
        self.path = path
        super().__init__(f"Circular dependency detected: {' -> '.join(path)}")


class DatabaseIntegrityError(KnowledgeGraphError):
    """Raised when database integrity is violated."""
    pass


class ExtractionError(KnowledgeGraphError):
    """Raised when knowledge extraction fails."""
    
    def __init__(self, source: str, reason: str):
        self.source = source
        self.reason = reason
        super().__init__(f"Failed to extract knowledge from {source}: {reason}")


class SyncError(KnowledgeGraphError):
    """Raised when synchronization fails."""
    
    def __init__(self, target: str, reason: str):
        self.target = target
        self.reason = reason
        super().__init__(f"Failed to sync to {target}: {reason}")
