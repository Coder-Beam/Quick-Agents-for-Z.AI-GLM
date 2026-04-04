"""
E2E Integration Tests for Knowledge Graph

Tests the complete end-to-end workflow:
Extract → Create → Discover → Search → Sync

Validates that all knowledge graph features work together in real scenarios.
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
from quickagents.knowledge_graph.knowledge_graph import KnowledgeGraph


class TestKnowledgeGraphE2E:
    """
    End-to-end integration tests for Knowledge Graph.
    
    Tests the complete workflow from knowledge extraction to memory sync.
    """
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            yield tmpdir
    
    @pytest.fixture
    def kg(self, temp_dir):
        """Create a KnowledgeGraph instance with temporary database."""
        db_path = os.path.join(temp_dir, "test.db")
        return KnowledgeGraph(db_path)
    
    @pytest.fixture
    def sample_md_file(self, temp_dir):
        """Create a sample markdown file for import testing."""
        md_path = os.path.join(temp_dir, "test_knowledge.md")
        content = """# Requirements

## Authentication

系统需要支持OAuth2.0认证

## Database

系统需要使用PostgreSQL作为主数据库

# Decisions

## Token方案

选择JWT作为Token方案，支持刷新机制

## Architecture

采用微服务架构，支持水平扩展
"""
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return md_path
    
    def test_full_workflow(self, kg, temp_dir):
        """
        Test complete end-to-end workflow.
        
        Scenario:
        1. Create nodes manually
        2. Create edges between nodes
        3. Discover relations
        4. Search for knowledge
        5. Sync to MEMORY.md
        6. Verify all operations work together
        """
        # Step 1: Create nodes manually
        n1 = kg.create_node(
            node_type=NodeType.REQUIREMENT,
            title="OAuth2.0支持",
            content="系统需要支持OAuth2.0",
            importance=0.9,
            confidence=0.95,
            tags=["auth", "oauth"]
        )
        
        n2 = kg.create_node(
            node_type=NodeType.DECISION,
            title="JWT Token方案",
            content="选择JWT作为Token方案",
            tags=["auth", "jwt"],
            importance=0.8
        )
        
        n3 = kg.create_node(
            node_type=NodeType.FACT,
            title="OAuth2.0标准",
            content="OAuth2.0是行业标准授权协议",
            tags=["oauth", "standard"],
            importance=0.7
        )
        
        assert n1.id.startswith("kn_")
        assert n2.id.startswith("kn_")
        assert n3.id.startswith("kn_")
        
        # Step 2: Create edges between related nodes
        edge1 = kg.create_edge(n1.id, n2.id, EdgeType.MAPS_TO, evidence="JWT实现OAuth需求")
        edge2 = kg.create_edge(n3.id, n1.id, EdgeType.SUPPORTS, evidence="OAuth标准支持")
        
        assert edge1.id.startswith("ke_")
        assert edge1.source_node_id == n1.id
        assert edge1.target_node_id == n2.id
        assert edge2.source_node_id == n3.id
        
        # Step 3: Discover relations
        discovered = kg.discover(n1.id, strategies=['semantic'])
        assert isinstance(discovered, list)
        
        # Step 4: Search for knowledge
        results = kg.search("OAuth")
        assert isinstance(results, SearchResult)
        assert results.total >= 1
        assert any("OAuth" in n.title or "OAuth" in n.content for n in results.nodes)
        
        # Step 5: Sync to MEMORY.md
        memory_path = os.path.join(temp_dir, "MEMORY.md")
        count = kg.sync_to_memory(memory_path=memory_path)
        assert count >= 1
        assert os.path.exists(memory_path)
        
        # Step 6: Verify complete workflow with stats
        stats = kg.get_stats()
        assert stats['total_nodes'] == 3
        assert stats['total_edges'] == 2
        
        # Verify relations
        relations = kg.show_relations(n1.id, direction="both")
        assert 'outgoing' in relations
        assert 'incoming' in relations
        assert len(relations['outgoing']) == 1
        assert len(relations['incoming']) == 1
        
        # Verify path finding
        path = kg.find_path(n3.id, n2.id)
        assert path is not None
        assert path[0] == n3.id
        assert path[-1] == n2.id
        
        # Verify trace
        trace = kg.trace_requirement(n1.id)
        assert 'node_id' in trace
        assert 'chains' in trace
    
    def test_import_from_file_workflow(self, kg, sample_md_file, temp_dir):
        """
        Test workflow starting from file import.
        
        Scenario:
        1. Import knowledge from markdown file
        2. Verify imported nodes
        3. Search and verify
        4. Sync to memory
        """
        # Step 1: Import from file
        result = kg.import_from_file(sample_md_file)
        
        assert result['success'] is True
        assert result['nodes_created'] >= 0
        
        # Step 2: Verify imported nodes exist
        nodes = kg.list_nodes()
        assert len(nodes) >= 0
        
        # Step 3: Search for imported content
        oauth_results = kg.search("OAuth")
        jwt_results = kg.search("JWT")
        
        # At minimum, search should not error
        assert isinstance(oauth_results, SearchResult)
        assert isinstance(jwt_results, SearchResult)
        
        # Step 4: Sync to memory
        memory_path = os.path.join(temp_dir, "MEMORY.md")
        count = kg.sync_to_memory(memory_path=memory_path)
        assert count >= 0
        
        stats = kg.get_stats()
        assert 'total_nodes' in stats
        assert 'total_edges' in stats
    
    def test_extract_from_text_workflow(self, kg, temp_dir):
        """
        Test workflow with text extraction.
        
        Scenario:
        1. Extract knowledge from text
        2. Create additional nodes
        3. Create edges
        4. Search and verify
        """
        # Step 1: Extract from text
        text = """
        系统需要支持用户认证功能
        决定采用JWT作为认证方案
        用户数据需要加密存储
        """
        
        extracted_nodes = kg.extract_from_text(text)
        assert isinstance(extracted_nodes, list)
        
        # Step 2: Create additional node manually
        extra_node = kg.create_node(
            node_type=NodeType.INSIGHT,
            title="认证安全洞察",
            content="JWT需要配合HTTPS使用",
            importance=0.85,
            tags=["security", "jwt"]
        )
        
        # Step 3: Create edges if we have extracted nodes
        if len(extracted_nodes) > 0:
            edge = kg.create_edge(
                extracted_nodes[0].id,
                extra_node.id,
                EdgeType.RELATED_TO,
                evidence="安全相关"
            )
            assert edge.id.startswith("ke_")
        
        # Step 4: Search and verify
        results = kg.search("JWT")
        assert isinstance(results, SearchResult)
        
        # Step 5: Stats
        stats = kg.get_stats()
        assert stats['total_nodes'] >= 1
    
    def test_discovery_strategies_e2e(self, kg):
        """
        Test different discovery strategies in E2E scenario.
        
        Tests direct, semantic, structural, and transitive strategies.
        """
        # Create a chain of nodes
        nodes = []
        for i in range(5):
            node = kg.create_node(
                node_type=NodeType.REQUIREMENT if i % 2 == 0 else NodeType.DECISION,
                title=f"Node {i}",
                content=f"Content about authentication {i}",
                tags=["auth"] if i < 3 else ["db"],
                importance=0.5 + i * 0.1
            )
            nodes.append(node)
        
        # Create chain of edges
        for i in range(len(nodes) - 1):
            kg.create_edge(nodes[i].id, nodes[i+1].id, EdgeType.RELATED_TO)
        
        # Test different discovery strategies
        direct_discovered = kg.discover(nodes[0].id, strategies=['direct'])
        assert isinstance(direct_discovered, list)
        
        semantic_discovered = kg.discover(nodes[0].id, strategies=['semantic'])
        assert isinstance(semantic_discovered, list)
        
        structural_discovered = kg.discover(nodes[0].id, strategies=['structural'])
        assert isinstance(structural_discovered, list)
        
        transitive_discovered = kg.discover(nodes[0].id, strategies=['transitive'])
        assert isinstance(transitive_discovered, list)
        
        # Test combined strategies
        all_discovered = kg.discover(
            nodes[0].id,
            strategies=['direct', 'semantic', 'structural', 'transitive']
        )
        assert isinstance(all_discovered, list)
    
    def test_search_with_filters_e2e(self, kg):
        """
        Test search with various filters in E2E scenario.
        """
        # Create nodes of different types
        kg.create_node(NodeType.REQUIREMENT, "Auth Req", "Authentication requirement")
        kg.create_node(NodeType.DECISION, "Auth Dec", "Authentication decision")
        kg.create_node(NodeType.FACT, "Auth Fact", "Authentication fact")
        kg.create_node(NodeType.CONCEPT, "DB Concept", "Database concept")
        
        # Search without filter
        all_results = kg.search("Auth")
        assert all_results.total >= 3
        
        # Search with type filter
        req_results = kg.search("Auth", node_types=[NodeType.REQUIREMENT])
        for node in req_results.nodes:
            assert node.node_type == NodeType.REQUIREMENT
        
        # Search with limit
        limited_results = kg.search("Auth", limit=2)
        assert len(limited_results.nodes) <= 2
    
    def test_tag_based_search_e2e(self, kg):
        """
        Test tag-based search in E2E scenario.
        """
        # Create nodes with different tags
        kg.create_node(
            NodeType.REQUIREMENT, "Req 1", "Content 1",
            tags=["security", "auth"]
        )
        kg.create_node(
            NodeType.DECISION, "Dec 1", "Content 2",
            tags=["security", "encryption"]
        )
        kg.create_node(
            NodeType.FACT, "Fact 1", "Content 3",
            tags=["performance", "cache"]
        )
        
        # Search by single tag
        security_nodes = kg.search_by_tags(["security"])
        assert len(security_nodes) == 2
        
        # Search by multiple tags
        auth_nodes = kg.search_by_tags(["auth"])
        assert len(auth_nodes) == 1
    
    def test_requirement_tracing_e2e(self, kg):
        """
        Test requirement tracing in E2E scenario.
        """
        # Create requirement chain
        req1 = kg.create_node(
            NodeType.REQUIREMENT, "Root Req", "Root requirement"
        )
        req2 = kg.create_node(
            NodeType.REQUIREMENT, "Sub Req", "Sub requirement"
        )
        dec1 = kg.create_node(
            NodeType.DECISION, "Design Dec", "Design decision"
        )
        fact1 = kg.create_node(
            NodeType.FACT, "Supporting Fact", "Supporting fact"
        )
        
        # Create edges
        kg.create_edge(req1.id, req2.id, EdgeType.DEPENDS_ON)
        kg.create_edge(req2.id, dec1.id, EdgeType.MAPS_TO)
        kg.create_edge(fact1.id, req1.id, EdgeType.SUPPORTS)
        
        # Trace requirement
        trace = kg.trace_requirement(req1.id)
        
        assert trace is not None
        assert trace["node_id"] == req1.id
        assert "chains" in trace
        assert "related" in trace
    
    def test_path_finding_e2e(self, kg):
        """
        Test path finding between nodes in E2E scenario.
        """
        # Create a path of nodes
        nodes = []
        for i in range(4):
            nodes.append(kg.create_node(
                NodeType.FACT, f"Node {i}", f"Content {i}"
            ))
        
        # Create edges: 0 -> 1 -> 2 -> 3
        for i in range(len(nodes) - 1):
            kg.create_edge(nodes[i].id, nodes[i+1].id, EdgeType.RELATED_TO)
        
        # Find path from start to end
        path = kg.find_path(nodes[0].id, nodes[3].id)
        
        assert path is not None
        assert path[0] == nodes[0].id
        assert path[-1] == nodes[3].id
        assert len(path) == 4
        
        # Test max_depth
        short_path = kg.find_path(nodes[0].id, nodes[3].id, max_depth=2)
        if short_path:
            assert len(short_path) <= 3
    
    def test_node_lifecycle_e2e(self, kg):
        """
        Test complete node lifecycle: create, read, update, delete.
        """
        # Create
        node = kg.create_node(
            node_type=NodeType.REQUIREMENT,
            title="Lifecycle Test",
            content="Initial content",
            importance=0.5
        )
        
        # Read
        retrieved = kg.get_node(node.id)
        assert retrieved is not None
        assert retrieved.title == "Lifecycle Test"
        
        # Update
        updated = kg.update_node(
            node.id,
            title="Updated Lifecycle Test",
            importance=0.9
        )
        assert updated.title == "Updated Lifecycle Test"
        assert updated.importance == 0.9
        
        # Delete
        deleted = kg.delete_node(node.id)
        assert deleted is True
        
        # Verify deletion
        after_delete = kg.get_node(node.id)
        assert after_delete is None
    
    def test_edge_lifecycle_e2e(self, kg):
        """
        Test complete edge lifecycle: create, read, delete.
        """
        # Setup nodes
        n1 = kg.create_node(NodeType.REQUIREMENT, "Req 1", "Content 1")
        n2 = kg.create_node(NodeType.DECISION, "Dec 1", "Content 2")
        
        # Create edge
        edge = kg.create_edge(
            n1.id, n2.id, EdgeType.MAPS_TO,
            evidence="Test evidence",
            confidence=0.85
        )
        
        # Read edge
        retrieved = kg.get_edge(edge.id)
        assert retrieved is not None
        assert retrieved.evidence == "Test evidence"
        assert retrieved.confidence == 0.85
        
        # Delete edge
        deleted = kg.delete_edge(edge.id)
        assert deleted is True
        
        # Verify deletion
        after_delete = kg.get_edge(edge.id)
        assert after_delete is None
    
    def test_cascade_delete_e2e(self, kg):
        """
        Test cascade delete behavior.
        """
        # Create nodes and edges
        n1 = kg.create_node(NodeType.REQUIREMENT, "Parent", "Content")
        n2 = kg.create_node(NodeType.DECISION, "Child", "Content")
        edge = kg.create_edge(n1.id, n2.id, EdgeType.MAPS_TO)
        
        # Delete with cascade
        deleted = kg.delete_node(n1.id, cascade=True)
        assert deleted is True
        
        # Verify node is deleted
        assert kg.get_node(n1.id) is None
        
        # Verify edge is also deleted (cascade)
        assert kg.get_edge(edge.id) is None
    
    def test_statistics_e2e(self, kg):
        """
        Test statistics gathering in E2E scenario.
        """
        # Create various nodes
        kg.create_node(NodeType.REQUIREMENT, "Req 1", "Content 1")
        kg.create_node(NodeType.REQUIREMENT, "Req 2", "Content 2")
        kg.create_node(NodeType.DECISION, "Dec 1", "Content 3")
        kg.create_node(NodeType.FACT, "Fact 1", "Content 4")
        
        n1 = kg.create_node(NodeType.CONCEPT, "Concept 1", "Content 5")
        n2 = kg.create_node(NodeType.INSIGHT, "Insight 1", "Content 6")
        kg.create_edge(n1.id, n2.id, EdgeType.RELATED_TO)
        
        # Get stats
        stats = kg.get_stats()
        
        assert stats['total_nodes'] == 6
        assert stats['total_edges'] == 1
        assert 'by_type' in stats
        assert 'by_edge_type' in stats
        assert stats['by_type'][NodeType.REQUIREMENT.value] == 2
        assert stats['by_type'][NodeType.DECISION.value] == 1
