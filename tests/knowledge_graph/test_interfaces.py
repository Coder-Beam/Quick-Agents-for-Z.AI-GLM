"""Tests for knowledge graph interfaces."""

import pytest
from abc import ABC
from quickagents.knowledge_graph.interfaces import GraphStorageInterface, VectorSearchInterface


class TestGraphStorageInterface:
    """Tests for GraphStorageInterface."""
    
    def test_is_abstract(self):
        """Test that GraphStorageInterface is abstract."""
        assert issubclass(GraphStorageInterface, ABC)
    
    def test_has_required_methods(self):
        """Test interface has all required abstract methods."""
        methods = [
            'initialize',
            'create_node',
            'get_node',
            'update_node',
            'delete_node',
            'create_edge',
            'get_edge',
            'delete_edge',
            'query_nodes',
            'query_edges',
            'find_path',
            'get_stats',
        ]
        for method in methods:
            assert hasattr(GraphStorageInterface, method)


class TestVectorSearchInterface:
    """Tests for VectorSearchInterface."""
    
    def test_is_abstract(self):
        """Test that VectorSearchInterface is abstract."""
        assert issubclass(VectorSearchInterface, ABC)
    
    def test_has_required_methods(self):
        """Test interface has all required abstract methods."""
        methods = [
            'initialize',
            'index_node',
            'remove_node',
            'search',
            'get_embedding',
        ]
        for method in methods:
            assert hasattr(VectorSearchInterface, method)
