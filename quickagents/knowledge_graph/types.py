"""
Knowledge Graph Types

Defines core types: NodeType, EdgeType, KnowledgeNode, KnowledgeEdge, SearchResult.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


class NodeType(Enum):
    """Knowledge node types."""
    REQUIREMENT = "requirement"
    DECISION = "decision"
    INSIGHT = "insight"
    FACT = "fact"
    CONCEPT = "concept"
    SOURCE = "source"
    DOCUMENT = "document"
    SECTION = "section"
    MODULE = "module"
    FUNCTION = "function"


class EdgeType(Enum):
    """Knowledge edge types."""
    DEPENDS_ON = "depends_on"
    IS_SUBCLASS_OF = "is_subclass_of"
    CITES = "cites"
    LINKS_TO = "links_to"
    EVOLVES_FROM = "evolves_from"
    MAPS_TO = "maps_to"
    AFFECTS = "affects"
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"
    RELATED_TO = "related_to"
    INDIRECTLY_RELATED_TO = "indirectly_related_to"
    CONTAINS = "contains"
    IMPLEMENTS = "implements"
    CALLS = "calls"
    EXTRACTED_FROM = "extracted_from"


@dataclass
class KnowledgeNode:
    """Knowledge node data class."""
    id: str
    node_type: NodeType
    title: str
    content: str
    source_type: Optional[str] = None
    source_uri: Optional[str] = None
    confidence: float = 1.0
    importance: float = 0.5
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    project_name: Optional[str] = None
    feature_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed_at: Optional[datetime] = None


@dataclass
class KnowledgeEdge:
    """Knowledge edge data class."""
    id: str
    source_node_id: str
    target_node_id: str
    edge_type: EdgeType
    weight: float = 1.0
    evidence: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class SearchResult:
    """Search result data class."""
    nodes: List[KnowledgeNode]
    total: int
    has_more: bool
    query_time_ms: float
    related_nodes: List[KnowledgeNode] = field(default_factory=list)
