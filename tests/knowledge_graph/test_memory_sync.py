"""
Tests for MemorySync - Knowledge synchronization to MEMORY.md
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from quickagents.knowledge_graph.types import NodeType, KnowledgeNode
from quickagents.knowledge_graph.core.node_manager import NodeManager
from quickagents.knowledge_graph.core.memory_sync import MemorySync


class TestSyncToMemory:
    """Tests for sync_to_memory method."""

    @pytest.fixture
    def node_manager(self):
        """Create NodeManager with mock storage."""
        mock_storage = Mock()
        return NodeManager(mock_storage)

    @pytest.fixture
    def memory_sync(self, node_manager):
        """Create MemorySync instance."""
        return MemorySync(node_manager)

    @pytest.fixture
    def sample_nodes(self):
        """Create sample high-importance nodes."""
        return [
            KnowledgeNode(
                id="kn_req_001",
                node_type=NodeType.REQUIREMENT,
                title="User Authentication",
                content="System must support OAuth 2.0 authentication",
                importance=0.9,
                confidence=0.95,
                tags=["auth", "security"],
                source_uri="docs/requirements.md",
            ),
            KnowledgeNode(
                id="kn_dec_002",
                node_type=NodeType.DECISION,
                title="Use PostgreSQL",
                content="PostgreSQL chosen as primary database",
                importance=0.85,
                confidence=0.9,
                tags=["database", "architecture"],
                source_uri="docs/adr/001-db-choice.md",
            ),
            KnowledgeNode(
                id="kn_fct_003",
                node_type=NodeType.FACT,
                title="API Rate Limit",
                content="API rate limit is 1000 requests per minute",
                importance=0.75,
                confidence=0.95,
                tags=["api", "limits"],
                source_uri="config/api.yaml",
            ),
        ]

    def test_basic(self, memory_sync, node_manager, sample_nodes):
        """Test basic sync to memory file."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            memory_path = os.path.join(tmpdir, "MEMORY.md")

            # Mock query_nodes to return sample nodes
            node_manager._storage.query_nodes = Mock(return_value=sample_nodes)

            result = memory_sync.sync_to_memory(memory_path)

            assert result == 3
            assert os.path.exists(memory_path)

            content = Path(memory_path).read_text(encoding="utf-8")
            # sync_to_memory uses its own format (not format_for_memory)
            assert "User Authentication" in content
            assert "Use PostgreSQL" in content
            assert "API Rate Limit" in content

    def test_no_candidates(self, memory_sync, node_manager):
        """Test sync when no candidates match criteria."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            memory_path = os.path.join(tmpdir, "MEMORY.md")

            # Mock query_nodes to return empty list
            node_manager._storage.query_nodes = Mock(return_value=[])

            result = memory_sync.sync_to_memory(memory_path)

            assert result == 0
            assert os.path.exists(memory_path)

    def test_file_not_found(self, memory_sync, node_manager, sample_nodes):
        """Test sync when path is invalid (contains null byte)."""
        node_manager._storage.query_nodes = Mock(return_value=sample_nodes)

        # Use invalid path (null byte is not allowed in paths)
        result = memory_sync.sync_to_memory("/invalid\x00path/MEMORY.md")

        assert result == 0

    def test_permission_denied(self, memory_sync, node_manager, sample_nodes):
        """Test sync when permission denied."""
        node_manager._storage.query_nodes = Mock(return_value=sample_nodes)

        # Mock Path.write_text to raise PermissionError
        with patch.object(Path, "write_text", side_effect=PermissionError("Permission denied")):
            result = memory_sync.sync_to_memory("/root/MEMORY.md")
            assert result == 0


class TestFilterSyncCandidates:
    """Tests for filter_sync_candidates method."""

    @pytest.fixture
    def node_manager(self):
        """Create NodeManager with mock storage."""
        mock_storage = Mock()
        return NodeManager(mock_storage)

    @pytest.fixture
    def memory_sync(self, node_manager):
        """Create MemorySync instance."""
        return MemorySync(node_manager)

    def test_by_importance(self, memory_sync):
        """Test filtering by importance >= 0.7."""
        nodes = [
            KnowledgeNode(
                id="kn_001",
                node_type=NodeType.REQUIREMENT,
                title="High",
                content="High importance",
                importance=0.9,
                confidence=0.9,
            ),
            KnowledgeNode(
                id="kn_002",
                node_type=NodeType.REQUIREMENT,
                title="Low",
                content="Low importance",
                importance=0.3,
                confidence=0.9,
            ),
            KnowledgeNode(
                id="kn_003",
                node_type=NodeType.DECISION,
                title="Medium",
                content="Medium importance",
                importance=0.7,
                confidence=0.9,
            ),
        ]

        result = memory_sync.filter_sync_candidates(nodes)

        assert len(result) == 2
        titles = [n.title for n in result]
        assert "High" in titles
        assert "Medium" in titles
        assert "Low" not in titles

    def test_by_type(self, memory_sync):
        """Test filtering by node_type in [REQUIREMENT, DECISION, FACT]."""
        nodes = [
            KnowledgeNode(
                id="kn_001",
                node_type=NodeType.REQUIREMENT,
                title="Req",
                content="Requirement",
                importance=0.8,
                confidence=0.9,
            ),
            KnowledgeNode(
                id="kn_002",
                node_type=NodeType.INSIGHT,
                title="Insight",
                content="Insight",
                importance=0.9,
                confidence=0.9,
            ),
            KnowledgeNode(
                id="kn_003",
                node_type=NodeType.CONCEPT,
                title="Concept",
                content="Concept",
                importance=0.9,
                confidence=0.9,
            ),
            KnowledgeNode(
                id="kn_004",
                node_type=NodeType.DECISION,
                title="Decision",
                content="Decision",
                importance=0.8,
                confidence=0.9,
            ),
            KnowledgeNode(
                id="kn_005", node_type=NodeType.FACT, title="Fact", content="Fact", importance=0.8, confidence=0.9
            ),
        ]

        result = memory_sync.filter_sync_candidates(nodes)

        assert len(result) == 3
        types = [n.node_type for n in result]
        assert NodeType.REQUIREMENT in types
        assert NodeType.DECISION in types
        assert NodeType.FACT in types
        assert NodeType.INSIGHT not in types
        assert NodeType.CONCEPT not in types

    def test_combined_criteria(self, memory_sync):
        """Test filtering with combined importance + type + confidence."""
        nodes = [
            # Should pass: high importance, correct type, high confidence
            KnowledgeNode(
                id="kn_001",
                node_type=NodeType.REQUIREMENT,
                title="Pass1",
                content="Should pass",
                importance=0.9,
                confidence=0.95,
            ),
            # Should fail: high importance, correct type, LOW confidence
            KnowledgeNode(
                id="kn_002",
                node_type=NodeType.DECISION,
                title="Fail1",
                content="Low confidence",
                importance=0.9,
                confidence=0.5,
            ),
            # Should fail: high importance, WRONG type, high confidence
            KnowledgeNode(
                id="kn_003",
                node_type=NodeType.INSIGHT,
                title="Fail2",
                content="Wrong type",
                importance=0.9,
                confidence=0.95,
            ),
            # Should fail: LOW importance, correct type, high confidence
            KnowledgeNode(
                id="kn_004",
                node_type=NodeType.FACT,
                title="Fail3",
                content="Low importance",
                importance=0.5,
                confidence=0.95,
            ),
            # Should pass: meets all criteria
            KnowledgeNode(
                id="kn_005",
                node_type=NodeType.FACT,
                title="Pass2",
                content="Should pass",
                importance=0.8,
                confidence=0.8,
            ),
        ]

        result = memory_sync.filter_sync_candidates(nodes)

        assert len(result) == 2
        titles = [n.title for n in result]
        assert "Pass1" in titles
        assert "Pass2" in titles

    def test_empty_list(self, memory_sync):
        """Test filtering empty list."""
        result = memory_sync.filter_sync_candidates([])
        assert result == []


class TestFormatForMemory:
    """Tests for format_for_memory method."""

    @pytest.fixture
    def node_manager(self):
        """Create NodeManager with mock storage."""
        mock_storage = Mock()
        return NodeManager(mock_storage)

    @pytest.fixture
    def memory_sync(self, node_manager):
        """Create MemorySync instance."""
        return MemorySync(node_manager)

    def test_requirement(self, memory_sync):
        """Test formatting a REQUIREMENT node."""
        node = KnowledgeNode(
            id="kn_req_001",
            node_type=NodeType.REQUIREMENT,
            title="User Login",
            content="Users must be able to log in with email",
            importance=0.9,
            confidence=0.95,
            tags=["auth", "user"],
            source_uri="docs/requirements.md",
        )

        result = memory_sync.format_for_memory(node)

        assert "### REQUIREMENT: User Login" in result
        assert "Users must be able to log in with email" in result
        assert "**Tags:** auth, user" in result
        assert "**Confidence:** 0.95" in result
        assert "**Source:** docs/requirements.md" in result
        assert "---" in result

    def test_decision(self, memory_sync):
        """Test formatting a DECISION node."""
        node = KnowledgeNode(
            id="kn_dec_001",
            node_type=NodeType.DECISION,
            title="Database Choice",
            content="PostgreSQL selected for primary database",
            importance=0.85,
            confidence=0.9,
            tags=["database", "postgresql"],
            source_uri="docs/adr/001.md",
        )

        result = memory_sync.format_for_memory(node)

        assert "### DECISION: Database Choice" in result
        assert "PostgreSQL selected for primary database" in result
        assert "**Tags:** database, postgresql" in result

    def test_fact(self, memory_sync):
        """Test formatting a FACT node."""
        node = KnowledgeNode(
            id="kn_fct_001",
            node_type=NodeType.FACT,
            title="API Version",
            content="Current API version is v2.1.0",
            importance=0.75,
            confidence=0.95,
            tags=["api", "version"],
            source_uri="docs/api.md",
        )

        result = memory_sync.format_for_memory(node)

        assert "### FACT: API Version" in result
        assert "Current API version is v2.1.0" in result
        assert "**Tags:** api, version" in result

    def test_with_metadata(self, memory_sync):
        """Test formatting node with metadata."""
        node = KnowledgeNode(
            id="kn_req_002",
            node_type=NodeType.REQUIREMENT,
            title="Complex Requirement",
            content="Multi-line content\nwith details",
            importance=0.9,
            confidence=0.9,
            tags=["complex"],
            source_uri="docs/spec.md",
            metadata={"author": "John Doe", "reviewed": True},
        )

        result = memory_sync.format_for_memory(node)

        assert "### REQUIREMENT: Complex Requirement" in result
        assert "Multi-line content" in result
        assert "with details" in result
        assert "**Tags:** complex" in result
        assert "**Metadata:**" in result
        assert "author: John Doe" in result
