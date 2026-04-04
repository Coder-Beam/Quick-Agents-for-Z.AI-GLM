"""
Tests for KnowledgeGraph Facade Class

Tests the unified facade that combines all minimal units.
"""

import os
import tempfile
import pytest

from quickagents.knowledge_graph import (
    NodeType,
    EdgeType,
    KnowledgeNode,
    KnowledgeEdge,
    SearchResult,
)
from quickagents.knowledge_graph.storage.sqlite_storage import SQLiteGraphStorage


class TestKnowledgeGraphInit:
    """Tests for KnowledgeGraph initialization."""
    
    def test_initializes_all_components(self):
        """Test that KnowledgeGraph initializes all sub-components."""
        from quickagents.knowledge_graph.knowledge_graph import KnowledgeGraph
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            kg = KnowledgeGraph(db_path)
            
            assert kg.storage is not None
            assert kg.nodes is not None
            assert kg.edges is not None
            assert kg.extractor is not None
            assert kg.discovery is not None
            assert kg.searcher is not None
            assert kg.sync is not None
    
    def test_creates_tables(self):
        """Test that KnowledgeGraph creates database tables."""
        from quickagents.knowledge_graph.knowledge_graph import KnowledgeGraph
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            kg = KnowledgeGraph(db_path)
            
            assert os.path.exists(db_path)
            
            stats = kg.get_stats()
            assert 'total_nodes' in stats
            assert 'total_edges' in stats


class TestNodeOperations:
    """Tests for node operations delegation."""
    
    def test_create_and_get_node_round_trip(self):
        """Test create_node and get_node round-trip."""
        from quickagents.knowledge_graph.knowledge_graph import KnowledgeGraph
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            kg = KnowledgeGraph(db_path)
            
            created = kg.create_node(
                node_type=NodeType.REQUIREMENT,
                title="Test Requirement",
                content="System must support authentication",
                importance=0.8,
                tags=["auth", "security"]
            )
            
            assert created.id.startswith("kn_")
            assert created.node_type == NodeType.REQUIREMENT
            assert created.title == "Test Requirement"
            
            retrieved = kg.get_node(created.id)
            assert retrieved is not None
            assert retrieved.id == created.id
            assert retrieved.title == "Test Requirement"
            assert "auth" in retrieved.tags
    
    def test_update_and_delete_node(self):
        """Test update_node and delete_node cycle."""
        from quickagents.knowledge_graph.knowledge_graph import KnowledgeGraph
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            kg = KnowledgeGraph(db_path)
            
            node = kg.create_node(
                node_type=NodeType.DECISION,
                title="Initial Decision",
                content="Use PostgreSQL"
            )
            
            updated = kg.update_node(node.id, title="Updated Decision", importance=0.9)
            assert updated.title == "Updated Decision"
            assert updated.importance == 0.9
            
            deleted = kg.delete_node(node.id)
            assert deleted is True
            
            retrieved = kg.get_node(node.id)
            assert retrieved is None
    
    def test_list_nodes_with_type_filter(self):
        """Test list_nodes with type filter."""
        from quickagents.knowledge_graph.knowledge_graph import KnowledgeGraph
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            kg = KnowledgeGraph(db_path)
            
            kg.create_node(NodeType.REQUIREMENT, "Req 1", "Content 1")
            kg.create_node(NodeType.REQUIREMENT, "Req 2", "Content 2")
            kg.create_node(NodeType.DECISION, "Dec 1", "Content 3")
            
            all_nodes = kg.list_nodes()
            assert len(all_nodes) == 3
            
            req_nodes = kg.list_nodes(node_type=NodeType.REQUIREMENT)
            assert len(req_nodes) == 2
            
            dec_nodes = kg.list_nodes(node_type=NodeType.DECISION)
            assert len(dec_nodes) == 1


class TestEdgeOperations:
    """Tests for edge operations delegation."""
    
    def test_create_and_get_edge_round_trip(self):
        """Test create_edge and get_edge round-trip."""
        from quickagents.knowledge_graph.knowledge_graph import KnowledgeGraph
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            kg = KnowledgeGraph(db_path)
            
            node1 = kg.create_node(NodeType.REQUIREMENT, "Req 1", "Content 1")
            node2 = kg.create_node(NodeType.DECISION, "Dec 1", "Content 2")
            
            edge = kg.create_edge(
                source_id=node1.id,
                target_id=node2.id,
                edge_type=EdgeType.MAPS_TO,
                evidence="Decision maps to requirement"
            )
            
            assert edge.id.startswith("ke_")
            assert edge.source_node_id == node1.id
            assert edge.target_node_id == node2.id
            assert edge.edge_type == EdgeType.MAPS_TO
            
            retrieved = kg.get_edge(edge.id)
            assert retrieved is not None
            assert retrieved.id == edge.id


class TestSearchOperations:
    """Tests for search operations delegation."""
    
    def test_search_returns_matching_nodes(self):
        """Test search returns matching nodes."""
        from quickagents.knowledge_graph.knowledge_graph import KnowledgeGraph
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            kg = KnowledgeGraph(db_path)
            
            kg.create_node(NodeType.REQUIREMENT, "Authentication", "User login required")
            kg.create_node(NodeType.DECISION, "Auth Decision", "Use JWT tokens")
            kg.create_node(NodeType.FACT, "Other Fact", "Unrelated content")
            
            result = kg.search("auth")
            
            assert isinstance(result, SearchResult)
            assert result.total >= 2
            assert len(result.nodes) >= 2
    
    def test_search_by_tags(self):
        """Test search_by_tags returns matching nodes."""
        from quickagents.knowledge_graph.knowledge_graph import KnowledgeGraph
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            kg = KnowledgeGraph(db_path)
            
            kg.create_node(
                NodeType.REQUIREMENT, 
                "Req 1", 
                "Content 1",
                tags=["security", "auth"]
            )
            kg.create_node(
                NodeType.DECISION,
                "Dec 1",
                "Content 2",
                tags=["security", "database"]
            )
            kg.create_node(
                NodeType.FACT,
                "Fact 1",
                "Content 3",
                tags=["general"]
            )
            
            nodes = kg.search_by_tags(["security"])
            assert len(nodes) == 2


class TestDiscoveryOperations:
    """Tests for discovery operations delegation."""
    
    def test_discover_with_default_strategies(self):
        """Test discover with default strategies ['direct', 'semantic']."""
        from quickagents.knowledge_graph.knowledge_graph import KnowledgeGraph
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            kg = KnowledgeGraph(db_path)
            
            node1 = kg.create_node(
                NodeType.REQUIREMENT,
                "Req 1",
                "Content about authentication",
                tags=["auth"]
            )
            node2 = kg.create_node(
                NodeType.DECISION,
                "Dec 1",
                "Decision about authentication",
                tags=["auth"]
            )
            
            discovered = kg.discover(node1.id)
            
            assert isinstance(discovered, list)
    
    def test_discover_with_explicit_strategies(self):
        """Test discover with explicit strategies."""
        from quickagents.knowledge_graph.knowledge_graph import KnowledgeGraph
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            kg = KnowledgeGraph(db_path)
            
            node1 = kg.create_node(NodeType.REQUIREMENT, "Req 1", "Content 1")
            node2 = kg.create_node(NodeType.DECISION, "Dec 1", "Content 2")
            node3 = kg.create_node(NodeType.FACT, "Fact 1", "Content 3")
            
            kg.create_edge(node1.id, node2.id, EdgeType.DEPENDS_ON)
            kg.create_edge(node2.id, node3.id, EdgeType.RELATED_TO)
            
            discovered_direct = kg.discover(node1.id, strategies=['direct'])
            discovered_transitive = kg.discover(node1.id, strategies=['transitive'])
            
            assert isinstance(discovered_direct, list)
            assert isinstance(discovered_transitive, list)
    
    def test_find_path_between_connected_nodes(self):
        """Test find_path between connected nodes."""
        from quickagents.knowledge_graph.knowledge_graph import KnowledgeGraph
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            kg = KnowledgeGraph(db_path)
            
            node1 = kg.create_node(NodeType.REQUIREMENT, "Req 1", "Content 1")
            node2 = kg.create_node(NodeType.DECISION, "Dec 1", "Content 2")
            node3 = kg.create_node(NodeType.FACT, "Fact 1", "Content 3")
            
            kg.create_edge(node1.id, node2.id, EdgeType.DEPENDS_ON)
            kg.create_edge(node2.id, node3.id, EdgeType.RELATED_TO)
            
            path = kg.find_path(node1.id, node3.id)
            
            assert path is not None
            assert path[0] == node1.id
            assert path[-1] == node3.id
            assert len(path) == 3
    
    def test_trace_requirement_chain(self):
        """Test trace_requirement follows DEPENDS_ON and MAPS_TO edges."""
        from quickagents.knowledge_graph.knowledge_graph import KnowledgeGraph
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            kg = KnowledgeGraph(db_path)
            
            req1 = kg.create_node(NodeType.REQUIREMENT, "Req 1", "Root requirement")
            req2 = kg.create_node(NodeType.REQUIREMENT, "Req 2", "Sub requirement")
            dec1 = kg.create_node(NodeType.DECISION, "Dec 1", "Decision")
            
            kg.create_edge(req1.id, req2.id, EdgeType.DEPENDS_ON)
            kg.create_edge(req2.id, dec1.id, EdgeType.MAPS_TO)
            
            result = kg.trace_requirement(req1.id)
            
            assert result["node_id"] == req1.id
            assert "chains" in result
            assert "related" in result


class TestExtractionOperations:
    """Tests for extraction operations delegation."""
    
    def test_extract_from_text(self):
        """Test extract_from_text creates knowledge nodes."""
        from quickagents.knowledge_graph.knowledge_graph import KnowledgeGraph
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            kg = KnowledgeGraph(db_path)
            
            text = "系统需要支持用户认证\n决定采用JWT作为认证方案"
            
            nodes = kg.extract_from_text(text)
            
            assert isinstance(nodes, list)
            assert len(nodes) >= 1
    
    def test_import_from_file(self):
        """Test import_from_file imports knowledge from markdown."""
        from quickagents.knowledge_graph.knowledge_graph import KnowledgeGraph
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            md_path = os.path.join(tmpdir, "test.md")
            kg = KnowledgeGraph(db_path)
            
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write("# Test Document\n\n系统需要支持文件导入功能\n")
            
            result = kg.import_from_file(md_path)
            
            assert result['success'] is True
            assert result['nodes_created'] >= 0


class TestSyncOperations:
    """Tests for sync operations delegation."""
    
    def test_sync_to_memory(self):
        """Test sync_to_memory syncs high-importance nodes."""
        from quickagents.knowledge_graph.knowledge_graph import KnowledgeGraph
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            memory_path = os.path.join(tmpdir, "MEMORY.md")
            kg = KnowledgeGraph(db_path)
            
            kg.create_node(
                NodeType.REQUIREMENT,
                "High Priority Req",
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
            
            count = kg.sync_to_memory(memory_path)
            
            assert count >= 1
            assert os.path.exists(memory_path)


class TestStatsAndRelations:
    """Tests for stats and show_relations methods."""
    
    def test_show_relations_both_directions(self):
        """Test show_relations with both directions."""
        from quickagents.knowledge_graph.knowledge_graph import KnowledgeGraph
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            kg = KnowledgeGraph(db_path)
            
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
    
    def test_get_stats_returns_dict(self):
        """Test get_stats returns statistics dict."""
        from quickagents.knowledge_graph.knowledge_graph import KnowledgeGraph
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            kg = KnowledgeGraph(db_path)
            
            kg.create_node(NodeType.REQUIREMENT, "Req 1", "Content 1")
            kg.create_node(NodeType.DECISION, "Dec 1", "Content 2")
            
            stats = kg.get_stats()
            
            assert isinstance(stats, dict)
            assert stats['total_nodes'] == 2
            assert 'by_type' in stats
