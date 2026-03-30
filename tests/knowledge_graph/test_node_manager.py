"""
Tests for NodeManager - Minimal Unit for managing knowledge nodes.

Test Cases (20):
- create_node: basic, all_params, invalid_type, duplicate_title
- get_node: existing, nonexistent, invalid_id_format
- update_node: title, multiple_fields, nonexistent, empty_update
- delete_node: basic, cascade_true, cascade_false, nonexistent
- list_nodes: all, by_type, with_limit, empty_db, pagination
"""

import pytest
import tempfile
import os
from datetime import datetime

from quickagents.knowledge_graph.types import NodeType, KnowledgeNode
from quickagents.knowledge_graph.exceptions import InvalidNodeTypeError, NodeNotFoundError
from quickagents.knowledge_graph.storage.sqlite_storage import SQLiteGraphStorage
from quickagents.knowledge_graph.core.node_manager import NodeManager


class TestNodeManagerCreate:
    """Tests for NodeManager.create_node()"""
    
    @pytest.fixture
    def manager(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        manager = NodeManager(storage)
        yield manager
        os.unlink(db_path)
    
    def test_create_node_basic(self, manager):
        node = manager.create_node(
            node_type=NodeType.REQUIREMENT,
            title="Test Requirement",
            content="Test content"
        )
        
        assert node.id.startswith("kn_req_")
        assert node.node_type == NodeType.REQUIREMENT
        assert node.title == "Test Requirement"
        assert node.content == "Test content"
        assert node.created_at is not None
        assert node.updated_at is not None
    
    def test_create_node_all_params(self, manager):
        node = manager.create_node(
            node_type=NodeType.DECISION,
            title="Test Decision",
            content="Decision content",
            source_type="meeting",
            source_uri="file:///docs/meeting.md",
            confidence=0.9,
            importance=0.8,
            tags=["urgent", "backend"],
            metadata={"author": "test"},
            project_name="test-project",
            feature_id="F001"
        )
        
        assert node.id.startswith("kn_dec_")
        assert node.node_type == NodeType.DECISION
        assert node.source_type == "meeting"
        assert node.source_uri == "file:///docs/meeting.md"
        assert node.confidence == 0.9
        assert node.importance == 0.8
        assert "urgent" in node.tags
        assert node.metadata.get("author") == "test"
        assert node.project_name == "test-project"
        assert node.feature_id == "F001"
    
    def test_create_node_invalid_type(self, manager):
        with pytest.raises(InvalidNodeTypeError) as exc_info:
            manager.create_node(
                node_type="invalid_type",
                title="Test",
                content="Content"
            )
        
        assert "invalid_type" in str(exc_info.value)
    
    def test_create_node_duplicate_title(self, manager):
        node1 = manager.create_node(
            node_type=NodeType.REQUIREMENT,
            title="Same Title",
            content="First content"
        )
        
        node2 = manager.create_node(
            node_type=NodeType.DECISION,
            title="Same Title",
            content="Second content"
        )
        
        assert node1.id != node2.id
        assert node1.title == node2.title


class TestNodeManagerGet:
    """Tests for NodeManager.get_node()"""
    
    @pytest.fixture
    def manager(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        manager = NodeManager(storage)
        yield manager
        os.unlink(db_path)
    
    def test_get_node_existing(self, manager):
        created = manager.create_node(
            node_type=NodeType.INSIGHT,
            title="Test Insight",
            content="Insight content"
        )
        
        retrieved = manager.get_node(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == "Test Insight"
    
    def test_get_node_nonexistent(self, manager):
        result = manager.get_node("kn_req_nonexistent123")
        
        assert result is None
    
    def test_get_node_invalid_id_format(self, manager):
        result = manager.get_node("invalid_id_format")
        
        assert result is None


class TestNodeManagerUpdate:
    """Tests for NodeManager.update_node()"""
    
    @pytest.fixture
    def manager(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        manager = NodeManager(storage)
        yield manager
        os.unlink(db_path)
    
    def test_update_node_title(self, manager):
        node = manager.create_node(
            node_type=NodeType.FACT,
            title="Original Title",
            content="Content"
        )
        
        updated = manager.update_node(node.id, title="Updated Title")
        
        assert updated.title == "Updated Title"
        assert updated.content == "Content"
    
    def test_update_node_multiple_fields(self, manager):
        node = manager.create_node(
            node_type=NodeType.CONCEPT,
            title="Original",
            content="Original content"
        )
        
        updated = manager.update_node(
            node.id,
            title="Updated Title",
            content="Updated content",
            importance=0.9,
            tags=["new", "tags"]
        )
        
        assert updated.title == "Updated Title"
        assert updated.content == "Updated content"
        assert updated.importance == 0.9
        assert "new" in updated.tags
    
    def test_update_node_nonexistent(self, manager):
        with pytest.raises(NodeNotFoundError) as exc_info:
            manager.update_node("kn_req_nonexistent123", title="New Title")
        
        assert "kn_req_nonexistent123" in str(exc_info.value)
    
    def test_update_node_empty_update(self, manager):
        node = manager.create_node(
            node_type=NodeType.SOURCE,
            title="Test Source",
            content="Content"
        )
        
        updated = manager.update_node(node.id)
        
        assert updated.id == node.id
        assert updated.title == "Test Source"


class TestNodeManagerDelete:
    """Tests for NodeManager.delete_node()"""
    
    @pytest.fixture
    def manager(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        manager = NodeManager(storage)
        yield manager
        os.unlink(db_path)
    
    def test_delete_node_basic(self, manager):
        node = manager.create_node(
            node_type=NodeType.REQUIREMENT,
            title="To Delete",
            content="Content"
        )
        
        result = manager.delete_node(node.id)
        
        assert result is True
        assert manager.get_node(node.id) is None
    
    def test_delete_node_cascade_true(self, manager):
        node1 = manager.create_node(
            node_type=NodeType.REQUIREMENT,
            title="Node 1",
            content="Content 1"
        )
        node2 = manager.create_node(
            node_type=NodeType.DECISION,
            title="Node 2",
            content="Content 2"
        )
        
        result = manager.delete_node(node1.id, cascade=True)
        
        assert result is True
        assert manager.get_node(node1.id) is None
    
    def test_delete_node_cascade_false(self, manager):
        node = manager.create_node(
            node_type=NodeType.INSIGHT,
            title="Node",
            content="Content"
        )
        
        result = manager.delete_node(node.id, cascade=False)
        
        assert result is True
        assert manager.get_node(node.id) is None
    
    def test_delete_node_nonexistent(self, manager):
        result = manager.delete_node("kn_req_nonexistent123")
        
        assert result is False


class TestNodeManagerList:
    """Tests for NodeManager.list_nodes()"""
    
    @pytest.fixture
    def manager(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        manager = NodeManager(storage)
        yield manager
        os.unlink(db_path)
    
    def test_list_nodes_all(self, manager):
        manager.create_node(NodeType.REQUIREMENT, "Req 1", "Content 1")
        manager.create_node(NodeType.DECISION, "Dec 1", "Content 2")
        manager.create_node(NodeType.INSIGHT, "Ins 1", "Content 3")
        
        nodes = manager.list_nodes()
        
        assert len(nodes) == 3
    
    def test_list_nodes_by_type(self, manager):
        manager.create_node(NodeType.REQUIREMENT, "Req 1", "Content 1")
        manager.create_node(NodeType.REQUIREMENT, "Req 2", "Content 2")
        manager.create_node(NodeType.DECISION, "Dec 1", "Content 3")
        
        nodes = manager.list_nodes(node_type=NodeType.REQUIREMENT)
        
        assert len(nodes) == 2
        assert all(n.node_type == NodeType.REQUIREMENT for n in nodes)
    
    def test_list_nodes_with_limit(self, manager):
        for i in range(10):
            manager.create_node(NodeType.FACT, f"Fact {i}", f"Content {i}")
        
        nodes = manager.list_nodes(limit=5)
        
        assert len(nodes) == 5
    
    def test_list_nodes_empty_db(self, manager):
        nodes = manager.list_nodes()
        
        assert nodes == []
    
    def test_list_nodes_pagination(self, manager):
        for i in range(15):
            manager.create_node(NodeType.CONCEPT, f"Concept {i}", f"Content {i}")
        
        page1 = manager.list_nodes(limit=5, offset=0)
        page2 = manager.list_nodes(limit=5, offset=5)
        
        assert len(page1) == 5
        assert len(page2) == 5
        assert page1[0].id != page2[0].id


class TestNodeManagerIdGeneration:
    """Tests for NodeManager._generate_id()"""
    
    @pytest.fixture
    def manager(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        manager = NodeManager(storage)
        yield manager
        os.unlink(db_path)
    
    def test_generate_id_format(self, manager):
        node = manager.create_node(
            node_type=NodeType.REQUIREMENT,
            title="Test",
            content="Content"
        )
        
        parts = node.id.split("_")
        assert len(parts) == 4
        assert parts[0] == "kn"
        assert parts[1] == "req"
        assert len(parts[3]) == 8
    
    def test_generate_id_uniqueness(self, manager):
        ids = set()
        for _ in range(100):
            node = manager.create_node(
                node_type=NodeType.DECISION,
                title=f"Node {_}",
                content="Content"
            )
            ids.add(node.id)
        
        assert len(ids) == 100
    
    def test_generate_id_type_mapping(self, manager):
        type_mapping = {
            NodeType.REQUIREMENT: "req",
            NodeType.DECISION: "dec",
            NodeType.INSIGHT: "ins",
            NodeType.FACT: "fct",
            NodeType.CONCEPT: "cpt",
            NodeType.SOURCE: "src",
        }
        
        for node_type, expected_short in type_mapping.items():
            node = manager.create_node(
                node_type=node_type,
                title=f"Test {node_type.value}",
                content="Content"
            )
            assert f"kn_{expected_short}_" in node.id
