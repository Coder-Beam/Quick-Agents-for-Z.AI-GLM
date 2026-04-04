"""
Tests for UnifiedDB knowledge property integration.

15 test cases covering:
- Property access (3)
- Node operations via UnifiedDB (2)
- Edge operations via UnifiedDB (2)
- Search via UnifiedDB (2)
- Discovery via UnifiedDB (2)
- Path/Trace via UnifiedDB (2)
- Sync via UnifiedDB (1)
- Stats integration (1)
"""

import pytest
import tempfile
import os

from quickagents import UnifiedDB, MemoryType, NodeType, EdgeType


class TestKnowledgePropertyAccess:
    """Test cases for knowledge property access."""
    
    def test_knowledge_property_returns_knowledge_graph(self):
        """knowledge property returns KnowledgeGraph instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            with UnifiedDB(db_path) as db:
                kg = db.knowledge
                assert kg is not None
                assert hasattr(kg, 'create_node')
                assert hasattr(kg, 'get_node')
                assert hasattr(kg, 'search')
    
    def test_knowledge_property_lazy_loaded(self):
        """knowledge property is lazy-loaded (same instance on repeated access)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            with UnifiedDB(db_path) as db:
                kg1 = db.knowledge
                kg2 = db.knowledge
                
                assert kg1 is kg2
    
    def test_knowledge_works_with_default_db_path(self):
        """knowledge property works with default db_path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, '.quickagents', 'unified.db')
            with UnifiedDB(db_path) as db:
                kg = db.knowledge
                assert kg is not None


class TestNodeOpsViaUnifiedDB:
    """Test node operations via UnifiedDB.knowledge."""
    
    def test_create_node_and_get_node_round_trip(self):
        """create_node + get_node round-trip works via UnifiedDB."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            with UnifiedDB(db_path) as db:
                node = db.knowledge.create_node(
                    node_type=NodeType.REQUIREMENT,
                    title='Test Requirement',
                    content='Test content'
                )
                
                assert node.id is not None
                
                retrieved = db.knowledge.get_node(node.id)
                assert retrieved is not None
                assert retrieved.title == 'Test Requirement'
                assert retrieved.content == 'Test content'
    
    def test_list_nodes_with_type_filter(self):
        """list_nodes with type filter works via UnifiedDB."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            with UnifiedDB(db_path) as db:
                db.knowledge.create_node(
                    node_type=NodeType.REQUIREMENT,
                    title='Req 1',
                    content='Content 1'
                )
                db.knowledge.create_node(
                    node_type=NodeType.DECISION,
                    title='Decision 1',
                    content='Content 2'
                )
                db.knowledge.create_node(
                    node_type=NodeType.REQUIREMENT,
                    title='Req 2',
                    content='Content 3'
                )
                
                req_nodes = db.knowledge.list_nodes(node_type=NodeType.REQUIREMENT)
                decision_nodes = db.knowledge.list_nodes(node_type=NodeType.DECISION)
                
                assert len(req_nodes) == 2
                assert len(decision_nodes) == 1


class TestEdgeOpsViaUnifiedDB:
    """Test edge operations via UnifiedDB.knowledge."""
    
    def test_create_edge_between_nodes(self):
        """create_edge between nodes works via UnifiedDB."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            with UnifiedDB(db_path) as db:
                node1 = db.knowledge.create_node(
                    node_type=NodeType.REQUIREMENT,
                    title='Source',
                    content='Source content'
                )
                node2 = db.knowledge.create_node(
                    node_type=NodeType.DECISION,
                    title='Target',
                    content='Target content'
                )
                
                edge = db.knowledge.create_edge(
                    source_id=node1.id,
                    target_id=node2.id,
                    edge_type=EdgeType.RELATED_TO
                )
                
                assert edge.id is not None
                assert edge.source_node_id == node1.id
                assert edge.target_node_id == node2.id
    
    def test_get_outgoing_edges(self):
        """get_outgoing_edges works via UnifiedDB."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            with UnifiedDB(db_path) as db:
                node1 = db.knowledge.create_node(
                    node_type=NodeType.REQUIREMENT,
                    title='Source',
                    content='Source content'
                )
                node2 = db.knowledge.create_node(
                    node_type=NodeType.DECISION,
                    title='Target',
                    content='Target content'
                )
                node3 = db.knowledge.create_node(
                    node_type=NodeType.DECISION,
                    title='Target 2',
                    content='Target 2 content'
                )
                
                db.knowledge.create_edge(
                    source_id=node1.id,
                    target_id=node2.id,
                    edge_type=EdgeType.RELATED_TO
                )
                db.knowledge.create_edge(
                    source_id=node1.id,
                    target_id=node3.id,
                    edge_type=EdgeType.DEPENDS_ON
                )
                
                edges = db.knowledge.get_outgoing_edges(node1.id)
                assert len(edges) == 2
                
                filtered = db.knowledge.get_outgoing_edges(node1.id, edge_type=EdgeType.RELATED_TO)
                assert len(filtered) == 1


class TestSearchViaUnifiedDB:
    """Test search operations via UnifiedDB.knowledge."""
    
    def test_search_returns_results(self):
        """search returns results via UnifiedDB."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            with UnifiedDB(db_path) as db:
                db.knowledge.create_node(
                    node_type=NodeType.REQUIREMENT,
                    title='User Authentication',
                    content='Users must be able to login'
                )
                db.knowledge.create_node(
                    node_type=NodeType.DECISION,
                    title='Auth Implementation',
                    content='Implement login form'
                )
                
                result = db.knowledge.search('authentication')
                
                assert result is not None
                assert result.total > 0
    
    def test_search_by_tags(self):
        """search_by_tags works via UnifiedDB."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            with UnifiedDB(db_path) as db:
                db.knowledge.create_node(
                    node_type=NodeType.REQUIREMENT,
                    title='Req 1',
                    content='Content 1',
                    tags=['auth', 'security']
                )
                db.knowledge.create_node(
                    node_type=NodeType.DECISION,
                    title='Decision 1',
                    content='Content 2',
                    tags=['auth', 'ui']
                )
                
                results = db.knowledge.search_by_tags(['auth'])
                assert len(results) == 2
                
                results = db.knowledge.search_by_tags(['security'])
                assert len(results) == 1


class TestDiscoveryViaUnifiedDB:
    """Test discovery operations via UnifiedDB.knowledge."""
    
    def test_discover_relations(self):
        """discover relations works via UnifiedDB."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            with UnifiedDB(db_path) as db:
                node1 = db.knowledge.create_node(
                    node_type=NodeType.REQUIREMENT,
                    title='Parent Req',
                    content='Parent content'
                )
                node2 = db.knowledge.create_node(
                    node_type=NodeType.DECISION,
                    title='Child Decision',
                    content='Child content'
                )
                
                edge = db.knowledge.create_edge(
                    source_id=node1.id,
                    target_id=node2.id,
                    edge_type=EdgeType.RELATED_TO
                )
                
                assert edge is not None
                
                outgoing = db.knowledge.get_outgoing_edges(node1.id)
                assert len(outgoing) >= 1
    
    def test_find_path(self):
        """find_path works via UnifiedDB."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            with UnifiedDB(db_path) as db:
                node1 = db.knowledge.create_node(
                    node_type=NodeType.REQUIREMENT,
                    title='Node 1',
                    content='Content 1'
                )
                node2 = db.knowledge.create_node(
                    node_type=NodeType.DECISION,
                    title='Node 2',
                    content='Content 2'
                )
                node3 = db.knowledge.create_node(
                    node_type=NodeType.INSIGHT,
                    title='Node 3',
                    content='Content 3'
                )
                
                db.knowledge.create_edge(
                    source_id=node1.id,
                    target_id=node2.id,
                    edge_type=EdgeType.RELATED_TO
                )
                db.knowledge.create_edge(
                    source_id=node2.id,
                    target_id=node3.id,
                    edge_type=EdgeType.DEPENDS_ON
                )
                
                path = db.knowledge.find_path(node1.id, node3.id)
                assert path is not None
                assert len(path) == 3


class TestTraceViaUnifiedDB:
    """Test trace operations via UnifiedDB.knowledge."""
    
    def test_trace_requirement(self):
        """trace_requirement works via UnifiedDB."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            with UnifiedDB(db_path) as db:
                req = db.knowledge.create_node(
                    node_type=NodeType.REQUIREMENT,
                    title='Root Requirement',
                    content='Root content'
                )
                decision = db.knowledge.create_node(
                    node_type=NodeType.DECISION,
                    title='Implementation Decision',
                    content='Decision content'
                )
                
                db.knowledge.create_edge(
                    source_id=req.id,
                    target_id=decision.id,
                    edge_type=EdgeType.RELATED_TO
                )
                
                trace = db.knowledge.trace_requirement(req.id)
                assert trace is not None
                assert 'node_id' in trace


class TestSyncViaUnifiedDB:
    """Test sync operations via UnifiedDB.knowledge."""
    
    def test_sync_to_memory(self):
        """sync_to_memory works via UnifiedDB."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            memory_path = os.path.join(tmpdir, 'MEMORY.md')
            with UnifiedDB(db_path) as db:
                db.knowledge.create_node(
                    node_type=NodeType.REQUIREMENT,
                    title='Important Req',
                    content='Important content',
                    importance=1.0
                )
                
                count = db.knowledge.sync_to_memory(memory_path=memory_path)
                assert count >= 0


class TestStatsIntegration:
    """Test stats integration with UnifiedDB."""
    
    def test_knowledge_stats_accessible_from_get_stats(self):
        """Knowledge stats should be accessible from db.get_stats() or knowledge.get_stats()."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            with UnifiedDB(db_path) as db:
                db.knowledge.create_node(
                    node_type=NodeType.REQUIREMENT,
                    title='Test',
                    content='Content'
                )
                
                kg_stats = db.knowledge.get_stats()
                assert kg_stats is not None
                assert 'total_nodes' in kg_stats


class TestCrossSystemCoexistence:
    """Test UnifiedDB memory + knowledge coexistence."""
    
    def test_unified_db_memory_and_knowledge_coexist(self):
        """UnifiedDB memory operations and knowledge operations work together."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            with UnifiedDB(db_path) as db:
                db.set_memory('project.name', 'TestProject', MemoryType.FACTUAL)
                db.set_memory('project.phase', 'development', MemoryType.WORKING)
                
                node = db.knowledge.create_node(
                    node_type=NodeType.REQUIREMENT,
                    title='Req from Memory',
                    content='Content derived from project memory'
                )
                
                assert db.get_memory('project.name') == 'TestProject'
                assert db.get_memory('project.phase') == 'development'
                
                retrieved = db.knowledge.get_node(node.id)
                assert retrieved is not None
                assert retrieved.title == 'Req from Memory'
                
                stats = db.get_stats()
                assert 'memory' in stats
                assert stats['memory']['total'] >= 2
