"""
Tests for EdgeManager - Minimal Unit for managing knowledge edges.

Test Cases (23):
- create_edge: basic, with_evidence, duplicate, invalid_source, invalid_target
- get_edge: existing, nonexistent, invalid_id_format
- delete_edge: basic, nonexistent, with_invalid_nodes
- get_outgoing_edges: basic, with_type_filter, no_edges, invalid_node
- get_incoming_edges: basic, with_type_filter, no_edges, invalid_node
- id_generation: format, uniqueness, type_mapping
- invalid_type: invalid_edge_type
"""

import pytest
import tempfile
import os

from quickagents.knowledge_graph.types import NodeType, EdgeType, KnowledgeNode, KnowledgeEdge
from quickagents.knowledge_graph.exceptions import InvalidEdgeTypeError, DuplicateEdgeError
from quickagents.knowledge_graph.storage.sqlite_storage import SQLiteGraphStorage


class TestEdgeManagerCreate:
    """Tests for EdgeManager.create_edge()"""
    
    @pytest.fixture
    def setup(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        
        from quickagents.knowledge_graph.core.edge_manager import EdgeManager
        manager = EdgeManager(storage)
        
        node1 = storage.create_node(KnowledgeNode(
            id="kn_req_source_node",
            node_type=NodeType.REQUIREMENT,
            title="Source Node",
            content="Source content"
        ))
        node2 = storage.create_node(KnowledgeNode(
            id="kn_dec_target_node",
            node_type=NodeType.DECISION,
            title="Target Node",
            content="Target content"
        ))
        
        yield {"manager": manager, "storage": storage, "node1": node1, "node2": node2}
        os.unlink(db_path)
    
    def test_create_edge_basic(self, setup):
        edge = setup["manager"].create_edge(
            source_id=setup["node1"].id,
            target_id=setup["node2"].id,
            edge_type=EdgeType.DEPENDS_ON
        )
        
        assert edge.id.startswith("ke_dep_")
        assert edge.source_node_id == setup["node1"].id
        assert edge.target_node_id == setup["node2"].id
        assert edge.edge_type == EdgeType.DEPENDS_ON
        assert edge.created_at is not None
    
    def test_create_edge_with_evidence(self, setup):
        edge = setup["manager"].create_edge(
            source_id=setup["node1"].id,
            target_id=setup["node2"].id,
            edge_type=EdgeType.SUPPORTS,
            evidence="This decision supports the requirement",
            weight=0.8,
            confidence=0.9,
            metadata={"author": "test"}
        )
        
        assert edge.evidence == "This decision supports the requirement"
        assert edge.weight == 0.8
        assert edge.confidence == 0.9
        assert edge.metadata.get("author") == "test"
    
    def test_create_edge_duplicate(self, setup):
        setup["manager"].create_edge(
            source_id=setup["node1"].id,
            target_id=setup["node2"].id,
            edge_type=EdgeType.DEPENDS_ON
        )
        
        with pytest.raises(DuplicateEdgeError) as exc_info:
            setup["manager"].create_edge(
                source_id=setup["node1"].id,
                target_id=setup["node2"].id,
                edge_type=EdgeType.DEPENDS_ON
            )
        
        assert setup["node1"].id in str(exc_info.value)
        assert setup["node2"].id in str(exc_info.value)
    
    def test_create_edge_invalid_source(self, setup):
        with pytest.raises(Exception):
            setup["manager"].create_edge(
                source_id="kn_req_nonexistent",
                target_id=setup["node2"].id,
                edge_type=EdgeType.DEPENDS_ON
            )
    
    def test_create_edge_invalid_target(self, setup):
        with pytest.raises(Exception):
            setup["manager"].create_edge(
                source_id=setup["node1"].id,
                target_id="kn_dec_nonexistent",
                edge_type=EdgeType.DEPENDS_ON
            )


class TestEdgeManagerGet:
    """Tests for EdgeManager.get_edge()"""
    
    @pytest.fixture
    def setup(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        
        from quickagents.knowledge_graph.core.edge_manager import EdgeManager
        manager = EdgeManager(storage)
        
        node1 = storage.create_node(KnowledgeNode(
            id="kn_req_source",
            node_type=NodeType.REQUIREMENT,
            title="Source",
            content="Content"
        ))
        node2 = storage.create_node(KnowledgeNode(
            id="kn_dec_target",
            node_type=NodeType.DECISION,
            title="Target",
            content="Content"
        ))
        
        yield {"manager": manager, "storage": storage, "node1": node1, "node2": node2}
        os.unlink(db_path)
    
    def test_get_edge_existing(self, setup):
        created = setup["manager"].create_edge(
            source_id=setup["node1"].id,
            target_id=setup["node2"].id,
            edge_type=EdgeType.CITES
        )
        
        retrieved = setup["manager"].get_edge(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.edge_type == EdgeType.CITES
    
    def test_get_edge_nonexistent(self, setup):
        result = setup["manager"].get_edge("ke_dep_nonexistent123")
        
        assert result is None
    
    def test_get_edge_invalid_id_format(self, setup):
        result = setup["manager"].get_edge("invalid_id_format")
        
        assert result is None


class TestEdgeManagerDelete:
    """Tests for EdgeManager.delete_edge()"""
    
    @pytest.fixture
    def setup(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        
        from quickagents.knowledge_graph.core.edge_manager import EdgeManager
        manager = EdgeManager(storage)
        
        node1 = storage.create_node(KnowledgeNode(
            id="kn_req_src",
            node_type=NodeType.REQUIREMENT,
            title="Source",
            content="Content"
        ))
        node2 = storage.create_node(KnowledgeNode(
            id="kn_dec_tgt",
            node_type=NodeType.DECISION,
            title="Target",
            content="Content"
        ))
        
        yield {"manager": manager, "storage": storage, "node1": node1, "node2": node2}
        os.unlink(db_path)
    
    def test_delete_edge_basic(self, setup):
        edge = setup["manager"].create_edge(
            source_id=setup["node1"].id,
            target_id=setup["node2"].id,
            edge_type=EdgeType.RELATED_TO
        )
        
        result = setup["manager"].delete_edge(edge.id)
        
        assert result is True
        assert setup["manager"].get_edge(edge.id) is None
    
    def test_delete_edge_nonexistent(self, setup):
        result = setup["manager"].delete_edge("ke_dep_nonexistent123")
        
        assert result is False
    
    def test_delete_edge_with_invalid_nodes(self, setup):
        edge = setup["manager"].create_edge(
            source_id=setup["node1"].id,
            target_id=setup["node2"].id,
            edge_type=EdgeType.LINKS_TO
        )
        
        setup["storage"].delete_node(setup["node1"].id, cascade=False)
        
        result = setup["manager"].get_edge(edge.id)
        
        assert result is None


class TestEdgeManagerGetOutgoing:
    """Tests for EdgeManager.get_outgoing_edges()"""
    
    @pytest.fixture
    def setup(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        
        from quickagents.knowledge_graph.core.edge_manager import EdgeManager
        manager = EdgeManager(storage)
        
        node1 = storage.create_node(KnowledgeNode(
            id="kn_req_out_src",
            node_type=NodeType.REQUIREMENT,
            title="Source",
            content="Content"
        ))
        node2 = storage.create_node(KnowledgeNode(
            id="kn_dec_out_tgt1",
            node_type=NodeType.DECISION,
            title="Target 1",
            content="Content"
        ))
        node3 = storage.create_node(KnowledgeNode(
            id="kn_ins_out_tgt2",
            node_type=NodeType.INSIGHT,
            title="Target 2",
            content="Content"
        ))
        
        yield {"manager": manager, "storage": storage, "node1": node1, "node2": node2, "node3": node3}
        os.unlink(db_path)
    
    def test_get_outgoing_edges_basic(self, setup):
        setup["manager"].create_edge(
            source_id=setup["node1"].id,
            target_id=setup["node2"].id,
            edge_type=EdgeType.DEPENDS_ON
        )
        setup["manager"].create_edge(
            source_id=setup["node1"].id,
            target_id=setup["node3"].id,
            edge_type=EdgeType.RELATED_TO
        )
        
        edges = setup["manager"].get_outgoing_edges(setup["node1"].id)
        
        assert len(edges) == 2
        assert all(e.source_node_id == setup["node1"].id for e in edges)
    
    def test_get_outgoing_edges_with_type_filter(self, setup):
        setup["manager"].create_edge(
            source_id=setup["node1"].id,
            target_id=setup["node2"].id,
            edge_type=EdgeType.DEPENDS_ON
        )
        setup["manager"].create_edge(
            source_id=setup["node1"].id,
            target_id=setup["node3"].id,
            edge_type=EdgeType.RELATED_TO
        )
        
        edges = setup["manager"].get_outgoing_edges(
            setup["node1"].id,
            edge_type=EdgeType.DEPENDS_ON
        )
        
        assert len(edges) == 1
        assert edges[0].edge_type == EdgeType.DEPENDS_ON
    
    def test_get_outgoing_edges_no_edges(self, setup):
        edges = setup["manager"].get_outgoing_edges(setup["node1"].id)
        
        assert edges == []
    
    def test_get_outgoing_edges_invalid_node(self, setup):
        edges = setup["manager"].get_outgoing_edges("kn_req_nonexistent")
        
        assert edges == []


class TestEdgeManagerGetIncoming:
    """Tests for EdgeManager.get_incoming_edges()"""
    
    @pytest.fixture
    def setup(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        
        from quickagents.knowledge_graph.core.edge_manager import EdgeManager
        manager = EdgeManager(storage)
        
        node1 = storage.create_node(KnowledgeNode(
            id="kn_req_in_src1",
            node_type=NodeType.REQUIREMENT,
            title="Source 1",
            content="Content"
        ))
        node2 = storage.create_node(KnowledgeNode(
            id="kn_dec_in_src2",
            node_type=NodeType.DECISION,
            title="Source 2",
            content="Content"
        ))
        node3 = storage.create_node(KnowledgeNode(
            id="kn_ins_in_tgt",
            node_type=NodeType.INSIGHT,
            title="Target",
            content="Content"
        ))
        
        yield {"manager": manager, "storage": storage, "node1": node1, "node2": node2, "node3": node3}
        os.unlink(db_path)
    
    def test_get_incoming_edges_basic(self, setup):
        setup["manager"].create_edge(
            source_id=setup["node1"].id,
            target_id=setup["node3"].id,
            edge_type=EdgeType.SUPPORTS
        )
        setup["manager"].create_edge(
            source_id=setup["node2"].id,
            target_id=setup["node3"].id,
            edge_type=EdgeType.CITES
        )
        
        edges = setup["manager"].get_incoming_edges(setup["node3"].id)
        
        assert len(edges) == 2
        assert all(e.target_node_id == setup["node3"].id for e in edges)
    
    def test_get_incoming_edges_with_type_filter(self, setup):
        setup["manager"].create_edge(
            source_id=setup["node1"].id,
            target_id=setup["node3"].id,
            edge_type=EdgeType.SUPPORTS
        )
        setup["manager"].create_edge(
            source_id=setup["node2"].id,
            target_id=setup["node3"].id,
            edge_type=EdgeType.CITES
        )
        
        edges = setup["manager"].get_incoming_edges(
            setup["node3"].id,
            edge_type=EdgeType.SUPPORTS
        )
        
        assert len(edges) == 1
        assert edges[0].edge_type == EdgeType.SUPPORTS
    
    def test_get_incoming_edges_no_edges(self, setup):
        edges = setup["manager"].get_incoming_edges(setup["node3"].id)
        
        assert edges == []
    
    def test_get_incoming_edges_invalid_node(self, setup):
        edges = setup["manager"].get_incoming_edges("kn_req_nonexistent")
        
        assert edges == []


class TestEdgeManagerIdGeneration:
    """Tests for EdgeManager._generate_id()"""
    
    @pytest.fixture
    def setup(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        
        from quickagents.knowledge_graph.core.edge_manager import EdgeManager
        manager = EdgeManager(storage)
        
        node1 = storage.create_node(KnowledgeNode(
            id="kn_req_id_src",
            node_type=NodeType.REQUIREMENT,
            title="Source",
            content="Content"
        ))
        node2 = storage.create_node(KnowledgeNode(
            id="kn_dec_id_tgt",
            node_type=NodeType.DECISION,
            title="Target",
            content="Content"
        ))
        
        yield {"manager": manager, "node1": node1, "node2": node2}
        os.unlink(db_path)
    
    def test_generate_id_format(self, setup):
        edge = setup["manager"].create_edge(
            source_id=setup["node1"].id,
            target_id=setup["node2"].id,
            edge_type=EdgeType.DEPENDS_ON
        )
        
        parts = edge.id.split("_")
        assert len(parts) == 4
        assert parts[0] == "ke"
        assert parts[1] == "dep"
        assert len(parts[3]) == 8
    
    def test_generate_id_uniqueness(self, setup):
        ids = set()
        for i in range(100):
            node = setup["manager"]._storage.create_node(KnowledgeNode(
                id=f"kn_req_{i}",
                node_type=NodeType.REQUIREMENT,
                title=f"Node {i}",
                content="Content"
            ))
            edge = setup["manager"].create_edge(
                source_id=setup["node1"].id,
                target_id=node.id,
                edge_type=EdgeType.RELATED_TO
            )
            ids.add(edge.id)
        
        assert len(ids) == 100
    
    def test_generate_id_type_mapping(self, setup):
        type_mapping = {
            EdgeType.DEPENDS_ON: "dep",
            EdgeType.IS_SUBCLASS_OF: "sub",
            EdgeType.CITES: "cit",
            EdgeType.LINKS_TO: "lnk",
            EdgeType.EVOLVES_FROM: "evo",
            EdgeType.MAPS_TO: "map",
            EdgeType.AFFECTS: "aff",
            EdgeType.CONTRADICTS: "con",
            EdgeType.SUPPORTS: "sup",
            EdgeType.RELATED_TO: "rel",
            EdgeType.INDIRECTLY_RELATED_TO: "ind",
        }
        
        for edge_type, expected_short in type_mapping.items():
            node = setup["manager"]._storage.create_node(KnowledgeNode(
                id=f"kn_test_{edge_type.value}",
                node_type=NodeType.FACT,
                title=f"Node for {edge_type.value}",
                content="Content"
            ))
            edge = setup["manager"].create_edge(
                source_id=setup["node1"].id,
                target_id=node.id,
                edge_type=edge_type
            )
            assert f"ke_{expected_short}_" in edge.id


class TestEdgeManagerInvalidType:
    """Tests for EdgeManager invalid edge type handling"""
    
    @pytest.fixture
    def setup(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        
        from quickagents.knowledge_graph.core.edge_manager import EdgeManager
        manager = EdgeManager(storage)
        
        yield {"manager": manager}
        os.unlink(db_path)
    
    def test_create_edge_invalid_type(self, setup):
        with pytest.raises(InvalidEdgeTypeError) as exc_info:
            setup["manager"].create_edge(
                source_id="kn_req_1",
                target_id="kn_dec_2",
                edge_type="invalid_type"
            )
        
        assert "invalid_type" in str(exc_info.value)
