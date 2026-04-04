"""Tests for knowledge graph types."""

import pytest
from quickagents.knowledge_graph.types import NodeType, EdgeType


class TestNodeType:
    """Tests for NodeType enum."""
    
    def test_node_type_values(self):
        """Test all node type values exist."""
        assert NodeType.REQUIREMENT.value == "requirement"
        assert NodeType.DECISION.value == "decision"
        assert NodeType.INSIGHT.value == "insight"
        assert NodeType.FACT.value == "fact"
        assert NodeType.CONCEPT.value == "concept"
        assert NodeType.SOURCE.value == "source"
        assert NodeType.DOCUMENT.value == "document"
        assert NodeType.SECTION.value == "section"
        assert NodeType.MODULE.value == "module"
        assert NodeType.FUNCTION.value == "function"
    
    def test_node_type_count(self):
        """Test total number of node types."""
        assert len(NodeType) == 10
    
    def test_node_type_from_string(self):
        """Test creating NodeType from string."""
        assert NodeType("requirement") == NodeType.REQUIREMENT
        with pytest.raises(ValueError):
            NodeType("invalid")


class TestEdgeType:
    """Tests for EdgeType enum."""
    
    def test_edge_type_values(self):
        """Test all edge type values exist."""
        assert EdgeType.DEPENDS_ON.value == "depends_on"
        assert EdgeType.IS_SUBCLASS_OF.value == "is_subclass_of"
        assert EdgeType.CITES.value == "cites"
        assert EdgeType.LINKS_TO.value == "links_to"
        assert EdgeType.EVOLVES_FROM.value == "evolves_from"
        assert EdgeType.MAPS_TO.value == "maps_to"
        assert EdgeType.AFFECTS.value == "affects"
        assert EdgeType.CONTRADICTS.value == "contradicts"
        assert EdgeType.SUPPORTS.value == "supports"
        assert EdgeType.RELATED_TO.value == "related_to"
        assert EdgeType.INDIRECTLY_RELATED_TO.value == "indirectly_related_to"
        assert EdgeType.CONTAINS.value == "contains"
        assert EdgeType.IMPLEMENTS.value == "implements"
        assert EdgeType.CALLS.value == "calls"
        assert EdgeType.EXTRACTED_FROM.value == "extracted_from"
    
    def test_edge_type_count(self):
        """Test total number of edge types."""
        assert len(EdgeType) == 15
