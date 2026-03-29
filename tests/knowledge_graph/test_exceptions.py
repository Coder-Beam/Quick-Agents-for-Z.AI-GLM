"""Tests for knowledge graph exceptions."""

import pytest
from quickagents.knowledge_graph.exceptions import (
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


class TestExceptions:
    """Tests for all custom exceptions."""
    
    def test_base_exception(self):
        """Test base exception is Exception subclass."""
        assert issubclass(KnowledgeGraphError, Exception)
    
    def test_node_not_found_error(self):
        """Test NodeNotFoundError with node_id."""
        error = NodeNotFoundError("kn_001")
        assert error.node_id == "kn_001"
        assert "kn_001" in str(error)
    
    def test_edge_not_found_error(self):
        """Test EdgeNotFoundError with edge_id."""
        error = EdgeNotFoundError("ke_001")
        assert error.edge_id == "ke_001"
        assert "ke_001" in str(error)
    
    def test_duplicate_node_error(self):
        """Test DuplicateNodeError with title and existing_id."""
        error = DuplicateNodeError("Test Title", "kn_existing")
        assert error.title == "Test Title"
        assert error.existing_id == "kn_existing"
    
    def test_duplicate_edge_error(self):
        """Test DuplicateEdgeError with source, target, type."""
        error = DuplicateEdgeError("kn_1", "kn_2", "depends_on")
        assert error.source_id == "kn_1"
        assert error.target_id == "kn_2"
        assert error.edge_type == "depends_on"
    
    def test_invalid_node_type_error(self):
        """Test InvalidNodeTypeError."""
        error = InvalidNodeTypeError("invalid_type")
        assert error.node_type == "invalid_type"
    
    def test_invalid_edge_type_error(self):
        """Test InvalidEdgeTypeError."""
        error = InvalidEdgeTypeError("invalid_edge")
        assert error.edge_type == "invalid_edge"
    
    def test_circular_dependency_error(self):
        """Test CircularDependencyError with path."""
        error = CircularDependencyError(["A", "B", "C", "A"])
        assert error.path == ["A", "B", "C", "A"]
        assert "A" in str(error)
    
    def test_extraction_error(self):
        """Test ExtractionError with source and reason."""
        error = ExtractionError("test.pdf", "File not found")
        assert error.source == "test.pdf"
        assert error.reason == "File not found"
    
    def test_sync_error(self):
        """Test SyncError with target and reason."""
        error = SyncError("MEMORY.md", "Permission denied")
        assert error.target == "MEMORY.md"
        assert error.reason == "Permission denied"
