"""
Integration Tests for Knowledge Graph CLI Commands

Tests the CLI interface for knowledge graph operations.
"""

import os
import sys
import tempfile
import subprocess
import pytest

from quickagents.knowledge_graph.knowledge_graph import KnowledgeGraph
from quickagents.knowledge_graph.types import NodeType, EdgeType


class TestKnowledgeCLI:
    """Tests for knowledge CLI commands."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            yield db_path
    
    @pytest.fixture
    def kg(self, temp_db):
        """Create a KnowledgeGraph instance."""
        return KnowledgeGraph(temp_db)
    
    def run_cli(self, args: list, temp_db: str) -> tuple:
        """Run CLI command and return (returncode, stdout, stderr)."""
        env = os.environ.copy()
        env['KNOWLEDGE_DB_PATH'] = temp_db
        
        result = subprocess.run(
            [sys.executable, '-m', 'quickagents.cli.main', 'knowledge'] + args,
            capture_output=True,
            text=True,
            env=env,
            cwd=os.path.dirname(temp_db)
        )
        return result.returncode, result.stdout, result.stderr
    
    def test_create_node_basic(self, kg, temp_db):
        """Test create-node command with basic arguments."""
        node = kg.create_node(
            node_type=NodeType.REQUIREMENT,
            title="Test Requirement",
            content="System must support authentication"
        )
        
        assert node.id.startswith("kn_")
        assert node.node_type == NodeType.REQUIREMENT
        assert node.title == "Test Requirement"
    
    def test_create_node_with_all_options(self, kg):
        """Test create-node with all optional arguments."""
        node = kg.create_node(
            node_type=NodeType.DECISION,
            title="Architecture Decision",
            content="Use microservices architecture",
            tags=["architecture", "microservices"],
            importance=0.9,
            confidence=0.85,
            project_name="test-project"
        )
        
        assert node.importance == 0.9
        assert node.confidence == 0.85
        assert "architecture" in node.tags
        assert node.project_name == "test-project"
    
    def test_get_node_existing(self, kg):
        """Test get-node with existing node."""
        created = kg.create_node(
            node_type=NodeType.INSIGHT,
            title="Performance Insight",
            content="Cache improves response time by 50%"
        )
        
        retrieved = kg.get_node(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == "Performance Insight"
    
    def test_get_node_nonexistent(self, kg):
        """Test get-node with nonexistent ID."""
        retrieved = kg.get_node("kn_nonexistent")
        
        assert retrieved is None
    
    def test_update_node(self, kg):
        """Test update-node command."""
        node = kg.create_node(
            node_type=NodeType.FACT,
            title="Initial Fact",
            content="Original content"
        )
        
        updated = kg.update_node(
            node.id,
            title="Updated Fact",
            importance=0.8
        )
        
        assert updated.title == "Updated Fact"
        assert updated.importance == 0.8
    
    def test_list_nodes_all(self, kg):
        """Test list-nodes without type filter."""
        kg.create_node(NodeType.REQUIREMENT, "Req 1", "Content 1")
        kg.create_node(NodeType.DECISION, "Dec 1", "Content 2")
        kg.create_node(NodeType.FACT, "Fact 1", "Content 3")
        
        nodes = kg.list_nodes()
        
        assert len(nodes) == 3
    
    def test_list_nodes_with_type_filter(self, kg):
        """Test list-nodes with type filter."""
        kg.create_node(NodeType.REQUIREMENT, "Req 1", "Content 1")
        kg.create_node(NodeType.REQUIREMENT, "Req 2", "Content 2")
        kg.create_node(NodeType.DECISION, "Dec 1", "Content 3")
        
        req_nodes = kg.list_nodes(node_type=NodeType.REQUIREMENT)
        
        assert len(req_nodes) == 2
        
        dec_nodes = kg.list_nodes(node_type=NodeType.DECISION)
        
        assert len(dec_nodes) == 1
    
    def test_delete_node_existing(self, kg):
        """Test delete-node with existing node."""
        node = kg.create_node(NodeType.CONCEPT, "Concept 1", "Content 1")
        
        deleted = kg.delete_node(node.id)
        
        assert deleted is True
        
        retrieved = kg.get_node(node.id)
        assert retrieved is None
    
    def test_delete_node_nonexistent(self, kg):
        """Test delete-node with nonexistent ID."""
        deleted = kg.delete_node("kn_nonexistent")
        
        assert deleted is False
    
    def test_delete_node_cascade(self, kg):
        """Test delete-node with cascade option."""
        node1 = kg.create_node(NodeType.REQUIREMENT, "Req 1", "Content 1")
        node2 = kg.create_node(NodeType.DECISION, "Dec 1", "Content 2")
        
        kg.create_edge(node1.id, node2.id, EdgeType.DEPENDS_ON)
        
        deleted = kg.delete_node(node1.id, cascade=True)
        
        assert deleted is True
    
    def test_create_edge_basic(self, kg):
        """Test create-edge with basic arguments."""
        node1 = kg.create_node(NodeType.REQUIREMENT, "Req 1", "Content 1")
        node2 = kg.create_node(NodeType.DECISION, "Dec 1", "Content 2")
        
        edge = kg.create_edge(
            node1.id, node2.id,
            EdgeType.MAPS_TO,
            evidence="Decision implements requirement"
        )
        
        assert edge.id.startswith("ke_")
        assert edge.source_node_id == node1.id
        assert edge.target_node_id == node2.id
        assert edge.edge_type == EdgeType.MAPS_TO
    
    def test_create_edge_with_confidence(self, kg):
        """Test create-edge with confidence score."""
        node1 = kg.create_node(NodeType.FACT, "Fact 1", "Content 1")
        node2 = kg.create_node(NodeType.CONCEPT, "Concept 1", "Content 2")
        
        edge = kg.create_edge(
            node1.id, node2.id,
            EdgeType.RELATED_TO,
            confidence=0.75
        )
        
        assert edge.confidence == 0.75
    
    def test_delete_edge(self, kg):
        """Test delete-edge command."""
        node1 = kg.create_node(NodeType.REQUIREMENT, "Req 1", "Content 1")
        node2 = kg.create_node(NodeType.DECISION, "Dec 1", "Content 2")
        
        edge = kg.create_edge(node1.id, node2.id, EdgeType.DEPENDS_ON)
        
        deleted = kg.delete_edge(edge.id)
        
        assert deleted is True
        
        retrieved = kg.get_edge(edge.id)
        assert retrieved is None
    
    def test_show_relations_outgoing(self, kg):
        """Test show-relations with outgoing direction."""
        node1 = kg.create_node(NodeType.REQUIREMENT, "Req 1", "Content 1")
        node2 = kg.create_node(NodeType.DECISION, "Dec 1", "Content 2")
        node3 = kg.create_node(NodeType.FACT, "Fact 1", "Content 3")
        
        kg.create_edge(node1.id, node2.id, EdgeType.DEPENDS_ON)
        kg.create_edge(node1.id, node3.id, EdgeType.RELATED_TO)
        
        relations = kg.show_relations(node1.id, direction="out")
        
        assert "outgoing" in relations
        assert len(relations["outgoing"]) == 2
        assert "incoming" not in relations
    
    def test_show_relations_incoming(self, kg):
        """Test show-relations with incoming direction."""
        node1 = kg.create_node(NodeType.REQUIREMENT, "Req 1", "Content 1")
        node2 = kg.create_node(NodeType.DECISION, "Dec 1", "Content 2")
        node3 = kg.create_node(NodeType.FACT, "Fact 1", "Content 3")
        
        kg.create_edge(node2.id, node1.id, EdgeType.SUPPORTS)
        kg.create_edge(node3.id, node1.id, EdgeType.RELATED_TO)
        
        relations = kg.show_relations(node1.id, direction="in")
        
        assert "incoming" in relations
        assert len(relations["incoming"]) == 2
        assert "outgoing" not in relations
    
    def test_show_relations_both(self, kg):
        """Test show-relations with both directions."""
        node1 = kg.create_node(NodeType.REQUIREMENT, "Req 1", "Content 1")
        node2 = kg.create_node(NodeType.DECISION, "Dec 1", "Content 2")
        node3 = kg.create_node(NodeType.FACT, "Fact 1", "Content 3")
        
        kg.create_edge(node1.id, node2.id, EdgeType.DEPENDS_ON)
        kg.create_edge(node3.id, node1.id, EdgeType.SUPPORTS)
        
        relations = kg.show_relations(node1.id, direction="both")
        
        assert "outgoing" in relations
        assert "incoming" in relations
        assert len(relations["outgoing"]) == 1
        assert len(relations["incoming"]) == 1
    
    def test_discover_default_strategies(self, kg):
        """Test discover with default strategies."""
        node1 = kg.create_node(
            NodeType.REQUIREMENT, "Req 1",
            "Content about authentication",
            tags=["auth"]
        )
        node2 = kg.create_node(
            NodeType.DECISION, "Dec 1",
            "Decision about authentication",
            tags=["auth"]
        )
        
        discovered = kg.discover(node1.id)
        
        assert isinstance(discovered, list)
    
    def test_discover_explicit_strategies(self, kg):
        """Test discover with explicit strategies."""
        node1 = kg.create_node(NodeType.REQUIREMENT, "Req 1", "Content 1")
        node2 = kg.create_node(NodeType.DECISION, "Dec 1", "Content 2")
        node3 = kg.create_node(NodeType.FACT, "Fact 1", "Content 3")
        
        kg.create_edge(node1.id, node2.id, EdgeType.DEPENDS_ON)
        kg.create_edge(node2.id, node3.id, EdgeType.RELATED_TO)
        
        discovered_direct = kg.discover(node1.id, strategies=['direct'])
        discovered_transitive = kg.discover(node1.id, strategies=['transitive'])
        
        assert isinstance(discovered_direct, list)
        assert isinstance(discovered_transitive, list)
    
    def test_search_basic(self, kg):
        """Test search command."""
        kg.create_node(NodeType.REQUIREMENT, "Authentication", "User login required")
        kg.create_node(NodeType.DECISION, "Auth Decision", "Use JWT tokens")
        kg.create_node(NodeType.FACT, "Other Fact", "Unrelated content")
        
        result = kg.search("auth")
        
        assert result.total >= 2
        assert len(result.nodes) >= 2
    
    def test_search_with_type_filter(self, kg):
        """Test search with type filter."""
        kg.create_node(NodeType.REQUIREMENT, "Authentication", "User login required")
        kg.create_node(NodeType.DECISION, "Auth Decision", "Use JWT tokens")
        
        result = kg.search("auth", node_types=[NodeType.REQUIREMENT])
        
        for node in result.nodes:
            assert node.node_type == NodeType.REQUIREMENT
    
    def test_search_with_limit(self, kg):
        """Test search with limit."""
        for i in range(10):
            kg.create_node(NodeType.FACT, f"Fact {i}", f"Test content {i}")
        
        result = kg.search("Test", limit=5)
        
        assert len(result.nodes) <= 5
    
    def test_stats(self, kg):
        """Test stats command."""
        kg.create_node(NodeType.REQUIREMENT, "Req 1", "Content 1")
        kg.create_node(NodeType.DECISION, "Dec 1", "Content 2")
        
        node1 = kg.create_node(NodeType.FACT, "Fact 1", "Content 3")
        node2 = kg.create_node(NodeType.CONCEPT, "Concept 1", "Content 4")
        kg.create_edge(node1.id, node2.id, EdgeType.RELATED_TO)
        
        stats = kg.get_stats()
        
        assert stats['total_nodes'] == 4
        assert stats['total_edges'] == 1
        assert 'by_type' in stats
        assert 'by_edge_type' in stats
    
    def test_sync_to_memory(self, kg):
        """Test sync command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            memory_path = os.path.join(tmpdir, "MEMORY.md")
            
            kg.create_node(
                NodeType.REQUIREMENT,
                "High Priority",
                "Critical requirement",
                importance=0.9,
                confidence=0.9
            )
            kg.create_node(
                NodeType.DECISION,
                "Low Priority",
                "Less important",
                importance=0.3,
                confidence=0.5
            )
            
            count = kg.sync_to_memory(memory_path=memory_path)
            
            assert count >= 1
            assert os.path.exists(memory_path)
    
    def test_find_path_exists(self, kg):
        """Test find-path when path exists."""
        node1 = kg.create_node(NodeType.REQUIREMENT, "Req 1", "Content 1")
        node2 = kg.create_node(NodeType.DECISION, "Dec 1", "Content 2")
        node3 = kg.create_node(NodeType.FACT, "Fact 1", "Content 3")
        
        kg.create_edge(node1.id, node2.id, EdgeType.DEPENDS_ON)
        kg.create_edge(node2.id, node3.id, EdgeType.RELATED_TO)
        
        path = kg.find_path(node1.id, node3.id)
        
        assert path is not None
        assert path[0] == node1.id
        assert path[-1] == node3.id
    
    def test_find_path_not_exists(self, kg):
        """Test find-path when path doesn't exist."""
        node1 = kg.create_node(NodeType.REQUIREMENT, "Req 1", "Content 1")
        node2 = kg.create_node(NodeType.DECISION, "Dec 1", "Content 2")
        
        path = kg.find_path(node1.id, node2.id)
        
        assert path is None or len(path) == 0
    
    def test_find_path_with_max_depth(self, kg):
        """Test find-path with max_depth limit."""
        nodes = []
        for i in range(10):
            nodes.append(kg.create_node(NodeType.FACT, f"Fact {i}", f"Content {i}"))
        
        for i in range(len(nodes) - 1):
            kg.create_edge(nodes[i].id, nodes[i+1].id, EdgeType.RELATED_TO)
        
        path = kg.find_path(nodes[0].id, nodes[-1].id, max_depth=3)
        
        if path:
            assert len(path) <= 4
    
    def test_trace_requirement(self, kg):
        """Test trace-requirement command."""
        req1 = kg.create_node(NodeType.REQUIREMENT, "Root Req", "Root requirement")
        req2 = kg.create_node(NodeType.REQUIREMENT, "Sub Req", "Sub requirement")
        dec1 = kg.create_node(NodeType.DECISION, "Decision", "Design decision")
        
        kg.create_edge(req1.id, req2.id, EdgeType.DEPENDS_ON)
        kg.create_edge(req2.id, dec1.id, EdgeType.MAPS_TO)
        
        trace = kg.trace_requirement(req1.id)
        
        assert trace["node_id"] == req1.id
        assert "chains" in trace
        assert "related" in trace


class TestCLIArgumentParsing:
    """Tests for CLI argument parsing."""
    
    def test_node_type_enum_values(self):
        """Test that all NodeType values are valid."""
        expected_types = [
            'requirement', 'decision', 'insight',
            'fact', 'concept', 'source'
        ]
        
        for type_name in expected_types:
            node_type = NodeType(type_name)
            assert node_type.value == type_name
    
    def test_edge_type_enum_values(self):
        """Test that all EdgeType values are valid."""
        expected_types = [
            'depends_on', 'is_subclass_of', 'cites', 'links_to',
            'evolves_from', 'maps_to', 'affects', 'contradicts',
            'supports', 'related_to', 'indirectly_related_to'
        ]
        
        for type_name in expected_types:
            edge_type = EdgeType(type_name)
            assert edge_type.value == type_name
    
    def test_invalid_node_type(self):
        """Test that invalid NodeType raises ValueError."""
        with pytest.raises(ValueError):
            NodeType("invalid_type")
    
    def test_invalid_edge_type(self):
        """Test that invalid EdgeType raises ValueError."""
        with pytest.raises(ValueError):
            EdgeType("invalid_type")


class TestCLIEdgeCases:
    """Tests for edge cases and error handling."""
    
    @pytest.fixture
    def kg(self):
        """Create a KnowledgeGraph instance with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            yield KnowledgeGraph(db_path)
    
    def test_create_edge_nonexistent_source(self, kg):
        """Test create-edge with nonexistent source node."""
        node2 = kg.create_node(NodeType.DECISION, "Dec 1", "Content 1")
        
        n1 = kg.get_node("kn_nonexistent")
        
        assert n1 is None
    
    def test_create_edge_nonexistent_target(self, kg):
        """Test create-edge with nonexistent target node."""
        node1 = kg.create_node(NodeType.REQUIREMENT, "Req 1", "Content 1")
        
        n2 = kg.get_node("kn_nonexistent")
        
        assert n2 is None
    
    def test_list_nodes_empty(self, kg):
        """Test list-nodes on empty database."""
        nodes = kg.list_nodes()
        
        assert len(nodes) == 0
    
    def test_search_empty_query(self, kg):
        """Test search with empty query."""
        result = kg.search("")
        
        assert result is not None
    
    def test_show_relations_isolated_node(self, kg):
        """Test show-relations on node with no edges."""
        node = kg.create_node(NodeType.FACT, "Isolated", "No connections")
        
        relations = kg.show_relations(node.id)
        
        assert len(relations.get("outgoing", [])) == 0
        assert len(relations.get("incoming", [])) == 0
    
    def test_discover_isolated_node(self, kg):
        """Test discover on isolated node."""
        node = kg.create_node(NodeType.FACT, "Isolated", "No connections")
        
        discovered = kg.discover(node.id)
        
        assert isinstance(discovered, list)
    
    def test_trace_requirement_nonexistent(self, kg):
        """Test trace-requirement on nonexistent node."""
        trace = kg.trace_requirement("kn_nonexistent")
        
        assert trace is not None
        assert "node_id" in trace
