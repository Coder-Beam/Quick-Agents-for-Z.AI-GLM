"""
Tests for RelationDiscovery - Minimal Unit for discovering relations.

Test Cases (25):
- discover_direct_relations: by_reference, by_link, by_tags, no_relations
- discover_semantic_relations: high_sim, low_sim, threshold_boundary, empty_content
- discover_structural_relations: same_feature, same_project, temporal_proximity, no_relations
- discover_transitive_relations: two_hop, three_hop, cycle_detection, no_transitive
- find_path: direct, multi_hop, no_path, max_depth_exceeded, circular_graph
- trace_requirement: full_chain, partial_chain, no_chain, circular_reference
"""

import pytest
import tempfile
import os
import time

from quickagents.knowledge_graph.types import NodeType, EdgeType, KnowledgeNode, KnowledgeEdge
from quickagents.knowledge_graph.storage.sqlite_storage import SQLiteGraphStorage
from quickagents.knowledge_graph.core.edge_manager import EdgeManager


class TestDiscoverDirectRelations:
    """Tests for RelationDiscovery.discover_direct_relations()"""
    
    @pytest.fixture
    def setup(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        
        from quickagents.knowledge_graph.core.discovery import RelationDiscovery
        edge_manager = EdgeManager(storage)
        discovery = RelationDiscovery(storage, edge_manager)
        
        yield {"storage": storage, "edge_manager": edge_manager, "discovery": discovery}
        os.unlink(db_path)
    
    def test_discover_direct_relations_by_reference(self, setup):
        node1 = setup["storage"].create_node(KnowledgeNode(
            id="kn_req_ref1",
            node_type=NodeType.REQUIREMENT,
            title="Source Node",
            content="This references kn_req_ref2 in the content"
        ))
        node2 = setup["storage"].create_node(KnowledgeNode(
            id="kn_req_ref2",
            node_type=NodeType.REQUIREMENT,
            title="Referenced Node",
            content="Referenced content"
        ))
        
        edges = setup["discovery"].discover_direct_relations("kn_req_ref1")
        
        assert len(edges) >= 1
        assert any(e.target_node_id == "kn_req_ref2" for e in edges)
    
    def test_discover_direct_relations_by_link(self, setup):
        node1 = setup["storage"].create_node(KnowledgeNode(
            id="kn_req_link1",
            node_type=NodeType.REQUIREMENT,
            title="Source Node",
            content="See related at [link](kn_dec_link2)"
        ))
        node2 = setup["storage"].create_node(KnowledgeNode(
            id="kn_dec_link2",
            node_type=NodeType.DECISION,
            title="Linked Node",
            content="Linked content"
        ))
        
        edges = setup["discovery"].discover_direct_relations("kn_req_link1")
        
        assert len(edges) >= 1
        assert any(e.target_node_id == "kn_dec_link2" for e in edges)
    
    def test_discover_direct_relations_by_tags(self, setup):
        node1 = setup["storage"].create_node(KnowledgeNode(
            id="kn_req_tag1",
            node_type=NodeType.REQUIREMENT,
            title="Node with Tag",
            content="Content",
            tags=["auth", "security"]
        ))
        node2 = setup["storage"].create_node(KnowledgeNode(
            id="kn_dec_tag2",
            node_type=NodeType.DECISION,
            title="Related Tag Node",
            content="Content",
            tags=["auth", "login"]
        ))
        node3 = setup["storage"].create_node(KnowledgeNode(
            id="kn_fac_tag3",
            node_type=NodeType.FACT,
            title="Unrelated Node",
            content="Content",
            tags=["database", "storage"]
        ))
        
        edges = setup["discovery"].discover_direct_relations("kn_req_tag1")
        
        tag_related = [e for e in edges if e.target_node_id == "kn_dec_tag2"]
        assert len(tag_related) >= 1
    
    def test_discover_direct_relations_no_relations(self, setup):
        node1 = setup["storage"].create_node(KnowledgeNode(
            id="kn_req_none",
            node_type=NodeType.REQUIREMENT,
            title="Isolated Node",
            content="No references or links",
            tags=["unique"]
        ))
        
        edges = setup["discovery"].discover_direct_relations("kn_req_none")
        
        assert edges == []


class TestDiscoverSemanticRelations:
    """Tests for RelationDiscovery.discover_semantic_relations()"""
    
    @pytest.fixture
    def setup(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        
        from quickagents.knowledge_graph.core.discovery import RelationDiscovery
        edge_manager = EdgeManager(storage)
        discovery = RelationDiscovery(storage, edge_manager)
        
        yield {"storage": storage, "discovery": discovery}
        os.unlink(db_path)
    
    def test_discover_semantic_relations_high_similarity(self, setup):
        node1 = setup["storage"].create_node(KnowledgeNode(
            id="kn_req_sim1",
            node_type=NodeType.REQUIREMENT,
            title="Authentication",
            content="User authentication with password and email login"
        ))
        node2 = setup["storage"].create_node(KnowledgeNode(
            id="kn_dec_sim2",
            node_type=NodeType.DECISION,
            title="Login Decision",
            content="Authentication login with password email user"
        ))
        
        edges = setup["discovery"].discover_semantic_relations("kn_req_sim1", threshold=0.5)
        
        assert len(edges) >= 1
        assert any(e.target_node_id == "kn_dec_sim2" for e in edges)
    
    def test_discover_semantic_relations_low_similarity(self, setup):
        node1 = setup["storage"].create_node(KnowledgeNode(
            id="kn_req_low1",
            node_type=NodeType.REQUIREMENT,
            title="Authentication",
            content="User authentication login password"
        ))
        node2 = setup["storage"].create_node(KnowledgeNode(
            id="kn_dec_low2",
            node_type=NodeType.DECISION,
            title="Database",
            content="Database storage connection pool"
        ))
        
        edges = setup["discovery"].discover_semantic_relations("kn_req_low1", threshold=0.7)
        
        low_sim_edges = [e for e in edges if e.target_node_id == "kn_dec_low2"]
        assert len(low_sim_edges) == 0
    
    def test_discover_semantic_relations_threshold_boundary(self, setup):
        node1 = setup["storage"].create_node(KnowledgeNode(
            id="kn_req_bound1",
            node_type=NodeType.REQUIREMENT,
            title="A B C",
            content="word1 word2 word3"
        ))
        node2 = setup["storage"].create_node(KnowledgeNode(
            id="kn_dec_bound2",
            node_type=NodeType.DECISION,
            title="A B D",
            content="word1 word2 word4"
        ))
        
        edges_high = setup["discovery"].discover_semantic_relations("kn_req_bound1", threshold=0.9)
        edges_low = setup["discovery"].discover_semantic_relations("kn_req_bound1", threshold=0.3)
        
        high_sim = [e for e in edges_high if e.target_node_id == "kn_dec_bound2"]
        low_sim = [e for e in edges_low if e.target_node_id == "kn_dec_bound2"]
        
        assert len(high_sim) == 0
        assert len(low_sim) >= 1
    
    def test_discover_semantic_relations_empty_content(self, setup):
        node1 = setup["storage"].create_node(KnowledgeNode(
            id="kn_req_empty",
            node_type=NodeType.REQUIREMENT,
            title="Empty Node",
            content=""
        ))
        node2 = setup["storage"].create_node(KnowledgeNode(
            id="kn_dec_empty2",
            node_type=NodeType.DECISION,
            title="Other Node",
            content="Some content"
        ))
        
        edges = setup["discovery"].discover_semantic_relations("kn_req_empty")
        
        assert isinstance(edges, list)


class TestDiscoverStructuralRelations:
    """Tests for RelationDiscovery.discover_structural_relations()"""
    
    @pytest.fixture
    def setup(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        
        from quickagents.knowledge_graph.core.discovery import RelationDiscovery
        edge_manager = EdgeManager(storage)
        discovery = RelationDiscovery(storage, edge_manager)
        
        yield {"storage": storage, "discovery": discovery}
        os.unlink(db_path)
    
    def test_discover_structural_relations_same_feature(self, setup):
        node1 = setup["storage"].create_node(KnowledgeNode(
            id="kn_req_feat1",
            node_type=NodeType.REQUIREMENT,
            title="Feature Node 1",
            content="Content",
            feature_id="auth-module"
        ))
        node2 = setup["storage"].create_node(KnowledgeNode(
            id="kn_dec_feat2",
            node_type=NodeType.DECISION,
            title="Feature Node 2",
            content="Content",
            feature_id="auth-module"
        ))
        
        edges = setup["discovery"].discover_structural_relations("kn_req_feat1")
        
        assert len(edges) >= 1
        assert any(e.target_node_id == "kn_dec_feat2" for e in edges)
    
    def test_discover_structural_relations_same_project(self, setup):
        node1 = setup["storage"].create_node(KnowledgeNode(
            id="kn_req_proj1",
            node_type=NodeType.REQUIREMENT,
            title="Project Node 1",
            content="Content",
            project_name="my-project"
        ))
        node2 = setup["storage"].create_node(KnowledgeNode(
            id="kn_dec_proj2",
            node_type=NodeType.DECISION,
            title="Project Node 2",
            content="Content",
            project_name="my-project"
        ))
        node3 = setup["storage"].create_node(KnowledgeNode(
            id="kn_ins_proj3",
            node_type=NodeType.INSIGHT,
            title="Other Project",
            content="Content",
            project_name="other-project"
        ))
        
        edges = setup["discovery"].discover_structural_relations("kn_req_proj1")
        
        project_edges = [e for e in edges if e.target_node_id == "kn_dec_proj2"]
        other_edges = [e for e in edges if e.target_node_id == "kn_ins_proj3"]
        
        assert len(project_edges) >= 1
        assert len(other_edges) == 0
    
    def test_discover_structural_relations_temporal_proximity(self, setup):
        t1 = time.time()
        node1 = setup["storage"].create_node(KnowledgeNode(
            id="kn_req_temp1",
            node_type=NodeType.REQUIREMENT,
            title="Time Node 1",
            content="Content"
        ))
        time.sleep(0.01)
        node2 = setup["storage"].create_node(KnowledgeNode(
            id="kn_dec_temp2",
            node_type=NodeType.DECISION,
            title="Time Node 2",
            content="Content"
        ))
        
        edges = setup["discovery"].discover_structural_relations("kn_req_temp1")
        
        assert isinstance(edges, list)
    
    def test_discover_structural_relations_no_relations(self, setup):
        node1 = setup["storage"].create_node(KnowledgeNode(
            id="kn_req_iso",
            node_type=NodeType.REQUIREMENT,
            title="Isolated Node",
            content="Content",
            project_name="unique-project",
            feature_id="unique-feature"
        ))
        
        edges = setup["discovery"].discover_structural_relations("kn_req_iso")
        
        assert edges == []


class TestDiscoverTransitiveRelations:
    """Tests for RelationDiscovery.discover_transitive_relations()"""
    
    @pytest.fixture
    def setup(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        
        from quickagents.knowledge_graph.core.discovery import RelationDiscovery
        edge_manager = EdgeManager(storage)
        discovery = RelationDiscovery(storage, edge_manager)
        
        yield {"storage": storage, "edge_manager": edge_manager, "discovery": discovery}
        os.unlink(db_path)
    
    def test_discover_transitive_relations_two_hop(self, setup):
        node_a = setup["storage"].create_node(KnowledgeNode(
            id="kn_req_a",
            node_type=NodeType.REQUIREMENT,
            title="Node A",
            content="Content A"
        ))
        node_b = setup["storage"].create_node(KnowledgeNode(
            id="kn_dec_b",
            node_type=NodeType.DECISION,
            title="Node B",
            content="Content B"
        ))
        node_c = setup["storage"].create_node(KnowledgeNode(
            id="kn_ins_c",
            node_type=NodeType.INSIGHT,
            title="Node C",
            content="Content C"
        ))
        
        setup["edge_manager"].create_edge(
            source_id="kn_req_a",
            target_id="kn_dec_b",
            edge_type=EdgeType.DEPENDS_ON
        )
        setup["edge_manager"].create_edge(
            source_id="kn_dec_b",
            target_id="kn_ins_c",
            edge_type=EdgeType.DEPENDS_ON
        )
        
        edges = setup["discovery"].discover_transitive_relations("kn_req_a", max_depth=3)
        
        transitive_to_c = [e for e in edges if e.target_node_id == "kn_ins_c"]
        assert len(transitive_to_c) >= 1
    
    def test_discover_transitive_relations_three_hop(self, setup):
        node_a = setup["storage"].create_node(KnowledgeNode(
            id="kn_req_a3",
            node_type=NodeType.REQUIREMENT,
            title="Node A",
            content="Content"
        ))
        node_b = setup["storage"].create_node(KnowledgeNode(
            id="kn_dec_b3",
            node_type=NodeType.DECISION,
            title="Node B",
            content="Content"
        ))
        node_c = setup["storage"].create_node(KnowledgeNode(
            id="kn_ins_c3",
            node_type=NodeType.INSIGHT,
            title="Node C",
            content="Content"
        ))
        node_d = setup["storage"].create_node(KnowledgeNode(
            id="kn_fac_d3",
            node_type=NodeType.FACT,
            title="Node D",
            content="Content"
        ))
        
        setup["edge_manager"].create_edge(
            source_id="kn_req_a3",
            target_id="kn_dec_b3",
            edge_type=EdgeType.DEPENDS_ON
        )
        setup["edge_manager"].create_edge(
            source_id="kn_dec_b3",
            target_id="kn_ins_c3",
            edge_type=EdgeType.DEPENDS_ON
        )
        setup["edge_manager"].create_edge(
            source_id="kn_ins_c3",
            target_id="kn_fac_d3",
            edge_type=EdgeType.DEPENDS_ON
        )
        
        edges = setup["discovery"].discover_transitive_relations("kn_req_a3", max_depth=4)
        
        transitive_to_d = [e for e in edges if e.target_node_id == "kn_fac_d3"]
        assert len(transitive_to_d) >= 1
    
    def test_discover_transitive_relations_cycle_detection(self, setup):
        node_a = setup["storage"].create_node(KnowledgeNode(
            id="kn_req_cycle_a",
            node_type=NodeType.REQUIREMENT,
            title="Node A",
            content="Content"
        ))
        node_b = setup["storage"].create_node(KnowledgeNode(
            id="kn_dec_cycle_b",
            node_type=NodeType.DECISION,
            title="Node B",
            content="Content"
        ))
        
        setup["edge_manager"].create_edge(
            source_id="kn_req_cycle_a",
            target_id="kn_dec_cycle_b",
            edge_type=EdgeType.DEPENDS_ON
        )
        setup["edge_manager"].create_edge(
            source_id="kn_dec_cycle_b",
            target_id="kn_req_cycle_a",
            edge_type=EdgeType.DEPENDS_ON
        )
        
        edges = setup["discovery"].discover_transitive_relations("kn_req_cycle_a", max_depth=5)
        
        assert isinstance(edges, list)
    
    def test_discover_transitive_relations_no_transitive(self, setup):
        node1 = setup["storage"].create_node(KnowledgeNode(
            id="kn_req_iso_trans",
            node_type=NodeType.REQUIREMENT,
            title="Isolated Node",
            content="Content"
        ))
        
        edges = setup["discovery"].discover_transitive_relations("kn_req_iso_trans")
        
        assert edges == []


class TestFindPath:
    """Tests for RelationDiscovery.find_path()"""
    
    @pytest.fixture
    def setup(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        
        from quickagents.knowledge_graph.core.discovery import RelationDiscovery
        edge_manager = EdgeManager(storage)
        discovery = RelationDiscovery(storage, edge_manager)
        
        yield {"storage": storage, "edge_manager": edge_manager, "discovery": discovery}
        os.unlink(db_path)
    
    def test_find_path_direct(self, setup):
        node1 = setup["storage"].create_node(KnowledgeNode(
            id="kn_req_path_direct1",
            node_type=NodeType.REQUIREMENT,
            title="Node 1",
            content="Content"
        ))
        node2 = setup["storage"].create_node(KnowledgeNode(
            id="kn_dec_path_direct2",
            node_type=NodeType.DECISION,
            title="Node 2",
            content="Content"
        ))
        
        setup["edge_manager"].create_edge(
            source_id="kn_req_path_direct1",
            target_id="kn_dec_path_direct2",
            edge_type=EdgeType.LINKS_TO
        )
        
        path = setup["discovery"].find_path("kn_req_path_direct1", "kn_dec_path_direct2")
        
        assert path is not None
        assert path[0] == "kn_req_path_direct1"
        assert path[-1] == "kn_dec_path_direct2"
        assert len(path) == 2
    
    def test_find_path_multi_hop(self, setup):
        node1 = setup["storage"].create_node(KnowledgeNode(
            id="kn_req_multi_1",
            node_type=NodeType.REQUIREMENT,
            title="Node 1",
            content="Content"
        ))
        node2 = setup["storage"].create_node(KnowledgeNode(
            id="kn_dec_multi_2",
            node_type=NodeType.DECISION,
            title="Node 2",
            content="Content"
        ))
        node3 = setup["storage"].create_node(KnowledgeNode(
            id="kn_ins_multi_3",
            node_type=NodeType.INSIGHT,
            title="Node 3",
            content="Content"
        ))
        
        setup["edge_manager"].create_edge(
            source_id="kn_req_multi_1",
            target_id="kn_dec_multi_2",
            edge_type=EdgeType.DEPENDS_ON
        )
        setup["edge_manager"].create_edge(
            source_id="kn_dec_multi_2",
            target_id="kn_ins_multi_3",
            edge_type=EdgeType.DEPENDS_ON
        )
        
        path = setup["discovery"].find_path("kn_req_multi_1", "kn_ins_multi_3")
        
        assert path is not None
        assert path[0] == "kn_req_multi_1"
        assert path[-1] == "kn_ins_multi_3"
        assert len(path) == 3
    
    def test_find_path_no_path(self, setup):
        node1 = setup["storage"].create_node(KnowledgeNode(
            id="kn_req_nopath1",
            node_type=NodeType.REQUIREMENT,
            title="Node 1",
            content="Content"
        ))
        node2 = setup["storage"].create_node(KnowledgeNode(
            id="kn_dec_nopath2",
            node_type=NodeType.DECISION,
            title="Node 2",
            content="Content"
        ))
        
        path = setup["discovery"].find_path("kn_req_nopath1", "kn_dec_nopath2")
        
        assert path is None
    
    def test_find_path_max_depth_exceeded(self, setup):
        nodes = []
        for i in range(7):
            node = setup["storage"].create_node(KnowledgeNode(
                id=f"kn_req_depth_{i}",
                node_type=NodeType.REQUIREMENT,
                title=f"Node {i}",
                content="Content"
            ))
            nodes.append(node)
        
        for i in range(len(nodes) - 1):
            setup["edge_manager"].create_edge(
                source_id=nodes[i].id,
                target_id=nodes[i + 1].id,
                edge_type=EdgeType.DEPENDS_ON
            )
        
        path = setup["discovery"].find_path(nodes[0].id, nodes[-1].id, max_depth=3)
        
        assert path is None
    
    def test_find_path_circular_graph(self, setup):
        node1 = setup["storage"].create_node(KnowledgeNode(
            id="kn_req_circ1",
            node_type=NodeType.REQUIREMENT,
            title="Node 1",
            content="Content"
        ))
        node2 = setup["storage"].create_node(KnowledgeNode(
            id="kn_dec_circ2",
            node_type=NodeType.DECISION,
            title="Node 2",
            content="Content"
        ))
        node3 = setup["storage"].create_node(KnowledgeNode(
            id="kn_ins_circ3",
            node_type=NodeType.INSIGHT,
            title="Node 3",
            content="Content"
        ))
        
        setup["edge_manager"].create_edge(
            source_id="kn_req_circ1",
            target_id="kn_dec_circ2",
            edge_type=EdgeType.LINKS_TO
        )
        setup["edge_manager"].create_edge(
            source_id="kn_dec_circ2",
            target_id="kn_ins_circ3",
            edge_type=EdgeType.LINKS_TO
        )
        setup["edge_manager"].create_edge(
            source_id="kn_ins_circ3",
            target_id="kn_req_circ1",
            edge_type=EdgeType.LINKS_TO
        )
        
        path = setup["discovery"].find_path("kn_req_circ1", "kn_ins_circ3")
        
        assert path is not None
        assert path[0] == "kn_req_circ1"
        assert path[-1] == "kn_ins_circ3"


class TestTraceRequirement:
    """Tests for RelationDiscovery.trace_requirement()"""
    
    @pytest.fixture
    def setup(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        
        from quickagents.knowledge_graph.core.discovery import RelationDiscovery
        edge_manager = EdgeManager(storage)
        discovery = RelationDiscovery(storage, edge_manager)
        
        yield {"storage": storage, "edge_manager": edge_manager, "discovery": discovery}
        os.unlink(db_path)
    
    def test_trace_requirement_full_chain(self, setup):
        req = setup["storage"].create_node(KnowledgeNode(
            id="kn_req_trace1",
            node_type=NodeType.REQUIREMENT,
            title="Requirement",
            content="Auth requirement"
        ))
        decision = setup["storage"].create_node(KnowledgeNode(
            id="kn_dec_trace1",
            node_type=NodeType.DECISION,
            title="Decision",
            content="Auth decision"
        ))
        insight = setup["storage"].create_node(KnowledgeNode(
            id="kn_ins_trace1",
            node_type=NodeType.INSIGHT,
            title="Insight",
            content="Auth insight"
        ))
        
        setup["edge_manager"].create_edge(
            source_id="kn_req_trace1",
            target_id="kn_dec_trace1",
            edge_type=EdgeType.MAPS_TO
        )
        setup["edge_manager"].create_edge(
            source_id="kn_req_trace1",
            target_id="kn_ins_trace1",
            edge_type=EdgeType.DEPENDS_ON
        )
        
        result = setup["discovery"].trace_requirement("kn_req_trace1")
        
        assert result is not None
        assert "node_id" in result
        assert "chains" in result or "related" in result
    
    def test_trace_requirement_partial_chain(self, setup):
        req = setup["storage"].create_node(KnowledgeNode(
            id="kn_req_partial",
            node_type=NodeType.REQUIREMENT,
            title="Partial Req",
            content="Content"
        ))
        decision = setup["storage"].create_node(KnowledgeNode(
            id="kn_dec_partial",
            node_type=NodeType.DECISION,
            title="Decision",
            content="Content"
        ))
        
        setup["edge_manager"].create_edge(
            source_id="kn_req_partial",
            target_id="kn_dec_partial",
            edge_type=EdgeType.MAPS_TO
        )
        
        result = setup["discovery"].trace_requirement("kn_req_partial")
        
        assert result is not None
        assert result["node_id"] == "kn_req_partial"
    
    def test_trace_requirement_no_chain(self, setup):
        req = setup["storage"].create_node(KnowledgeNode(
            id="kn_req_nochain",
            node_type=NodeType.REQUIREMENT,
            title="Isolated Req",
            content="Content"
        ))
        
        result = setup["discovery"].trace_requirement("kn_req_nochain")
        
        assert result is not None
        assert result["node_id"] == "kn_req_nochain"
    
    def test_trace_requirement_circular_reference(self, setup):
        req = setup["storage"].create_node(KnowledgeNode(
            id="kn_req_circ_ref",
            node_type=NodeType.REQUIREMENT,
            title="Circular Req",
            content="Content"
        ))
        decision = setup["storage"].create_node(KnowledgeNode(
            id="kn_dec_circ_ref",
            node_type=NodeType.DECISION,
            title="Circular Dec",
            content="Content"
        ))
        
        setup["edge_manager"].create_edge(
            source_id="kn_req_circ_ref",
            target_id="kn_dec_circ_ref",
            edge_type=EdgeType.DEPENDS_ON
        )
        setup["edge_manager"].create_edge(
            source_id="kn_dec_circ_ref",
            target_id="kn_req_circ_ref",
            edge_type=EdgeType.DEPENDS_ON
        )
        
        result = setup["discovery"].trace_requirement("kn_req_circ_ref", max_depth=3)
        
        assert result is not None
        assert result["node_id"] == "kn_req_circ_ref"
