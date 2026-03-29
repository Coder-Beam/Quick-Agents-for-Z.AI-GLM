"""Tests for SQLite storage backend."""

import pytest
import sqlite3
from pathlib import Path
from datetime import datetime
from quickagents.knowledge_graph.storage.sqlite_storage import SQLiteGraphStorage
from quickagents.knowledge_graph.types import KnowledgeNode, NodeType, KnowledgeEdge, EdgeType


class TestSQLiteStorageSchema:
    """Tests for SQLite storage schema initialization."""
    
    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create temporary database path."""
        return str(tmp_path / "test_kg.db")
    
    @pytest.fixture
    def storage(self, temp_db):
        """Create storage instance."""
        storage = SQLiteGraphStorage(temp_db)
        storage.initialize({})
        return storage
    
    def test_initialize_creates_database(self, temp_db):
        """Test that initialize creates the database file."""
        storage = SQLiteGraphStorage(temp_db)
        storage.initialize({})
        assert Path(temp_db).exists()
    
    def test_initialize_creates_knowledge_nodes_table(self, storage, temp_db):
        """Test that knowledge_nodes table is created."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_nodes'"
        )
        result = cursor.fetchone()
        conn.close()
        assert result is not None
    
    def test_initialize_creates_knowledge_edges_table(self, storage, temp_db):
        """Test that knowledge_edges table is created."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_edges'"
        )
        result = cursor.fetchone()
        conn.close()
        assert result is not None
    
    def test_initialize_creates_fts_index(self, storage, temp_db):
        """Test that FTS5 virtual table is created."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_index'"
        )
        result = cursor.fetchone()
        conn.close()
        assert result is not None
    
    def test_knowledge_nodes_columns(self, storage, temp_db):
        """Test knowledge_nodes table has all required columns."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(knowledge_nodes)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()
        
        required_columns = {
            'id', 'node_type', 'title', 'content', 'source_type',
            'source_uri', 'confidence', 'importance', 'tags', 'metadata',
            'project_name', 'feature_id', 'created_at', 'updated_at',
            'access_count', 'last_accessed_at'
        }
        assert required_columns.issubset(columns)
    
    def test_knowledge_edges_columns(self, storage, temp_db):
        """Test knowledge_edges table has all required columns."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(knowledge_edges)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()
        
        required_columns = {
            'id', 'source_node_id', 'target_node_id', 'edge_type',
            'weight', 'evidence', 'metadata', 'confidence',
            'created_at', 'updated_at'
        }
        assert required_columns.issubset(columns)
    
    def test_knowledge_nodes_indexes(self, storage, temp_db):
        """Test knowledge_nodes has required indexes."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA index_list(knowledge_nodes)")
        indexes = {row[1] for row in cursor.fetchall()}
        conn.close()
        
        assert 'idx_nodes_type' in indexes
        assert 'idx_nodes_project' in indexes
        assert 'idx_nodes_importance' in indexes
    
    def test_knowledge_edges_unique_constraint(self, storage, temp_db):
        """Test knowledge_edges has unique constraint on (source, target, type)."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("PRAGMA index_list(knowledge_edges)")
        indexes = cursor.fetchall()
        conn.close()
        
        unique_indexes = [idx for idx in indexes if idx[2] == 1]
        assert len(unique_indexes) > 0


class TestSQLiteStorageNodeCRUD:
    """Tests for node CRUD operations."""
    
    @pytest.fixture
    def storage(self, tmp_path):
        """Create initialized storage."""
        db_path = str(tmp_path / "test_kg.db")
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        return storage
    
    @pytest.fixture
    def sample_node(self):
        """Create sample node data."""
        return KnowledgeNode(
            id="kn_test001",
            node_type=NodeType.REQUIREMENT,
            title="Test Requirement",
            content="This is a test requirement",
            tags=["test", "sample"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def test_create_node_basic(self, storage, sample_node):
        """Test basic node creation."""
        result = storage.create_node(sample_node)
        
        assert result.id == sample_node.id
        assert result.title == sample_node.title
        assert result.node_type == NodeType.REQUIREMENT
    
    def test_get_node_existing(self, storage, sample_node):
        """Test getting an existing node."""
        storage.create_node(sample_node)
        result = storage.get_node(sample_node.id)
        
        assert result is not None
        assert result.id == sample_node.id
        assert result.title == sample_node.title
    
    def test_get_node_nonexistent(self, storage):
        """Test getting a non-existent node."""
        result = storage.get_node("kn_nonexistent")
        assert result is None
    
    def test_update_node_title(self, storage, sample_node):
        """Test updating node title."""
        storage.create_node(sample_node)
        updated = storage.update_node(sample_node.id, {"title": "Updated Title"})
        
        assert updated.title == "Updated Title"
    
    def test_update_node_multiple_fields(self, storage, sample_node):
        """Test updating multiple fields."""
        storage.create_node(sample_node)
        updated = storage.update_node(
            sample_node.id,
            {"title": "New Title", "importance": 0.9}
        )
        
        assert updated.title == "New Title"
        assert updated.importance == 0.9
    
    def test_delete_node_basic(self, storage, sample_node):
        """Test deleting a node."""
        storage.create_node(sample_node)
        result = storage.delete_node(sample_node.id)
        
        assert result is True
        assert storage.get_node(sample_node.id) is None
    
    def test_delete_node_nonexistent(self, storage):
        """Test deleting non-existent node."""
        result = storage.delete_node("kn_nonexistent")
        assert result is False
    
    def test_create_node_with_all_fields(self, storage):
        """Test creating node with all optional fields."""
        node = KnowledgeNode(
            id="kn_full",
            node_type=NodeType.DECISION,
            title="Full Node",
            content="Content",
            source_type="doc",
            source_uri="file://test.md",
            confidence=0.95,
            importance=0.8,
            tags=["tag1", "tag2"],
            metadata={"key": "value"},
            project_name="TestProject",
            feature_id="F001",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        result = storage.create_node(node)
        
        assert result.source_type == "doc"
        assert result.confidence == 0.95
        assert "tag1" in result.tags


class TestSQLiteStorageEdgeCRUD:
    """Tests for edge CRUD operations."""
    
    @pytest.fixture
    def storage(self, tmp_path):
        """Create initialized storage with sample nodes."""
        db_path = str(tmp_path / "test_kg.db")
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        
        self.node1 = KnowledgeNode(
            id="kn_001", node_type=NodeType.REQUIREMENT,
            title="Req 1", content="Content 1",
            created_at=datetime.now(), updated_at=datetime.now()
        )
        self.node2 = KnowledgeNode(
            id="kn_002", node_type=NodeType.DECISION,
            title="Decision 1", content="Content 2",
            created_at=datetime.now(), updated_at=datetime.now()
        )
        storage.create_node(self.node1)
        storage.create_node(self.node2)
        
        return storage
    
    def test_create_edge_basic(self, storage):
        """Test basic edge creation."""
        edge = KnowledgeEdge(
            id="ke_001",
            source_node_id="kn_001",
            target_node_id="kn_002",
            edge_type=EdgeType.DEPENDS_ON,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        result = storage.create_edge(edge)
        
        assert result.id == edge.id
        assert result.edge_type == EdgeType.DEPENDS_ON
    
    def test_get_edge_existing(self, storage):
        """Test getting existing edge."""
        edge = KnowledgeEdge(
            id="ke_002", source_node_id="kn_001", target_node_id="kn_002",
            edge_type=EdgeType.MAPS_TO,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        storage.create_edge(edge)
        
        result = storage.get_edge("ke_002")
        assert result is not None
        assert result.id == "ke_002"
    
    def test_get_edge_nonexistent(self, storage):
        """Test getting non-existent edge."""
        result = storage.get_edge("ke_nonexistent")
        assert result is None
    
    def test_delete_edge_basic(self, storage):
        """Test deleting edge."""
        edge = KnowledgeEdge(
            id="ke_003", source_node_id="kn_001", target_node_id="kn_002",
            edge_type=EdgeType.CITES,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        storage.create_edge(edge)
        
        result = storage.delete_edge("ke_003")
        assert result is True
        assert storage.get_edge("ke_003") is None
    
    def test_create_duplicate_edge_fails(self, storage):
        """Test that duplicate edge creation fails."""
        edge1 = KnowledgeEdge(
            id="ke_004", source_node_id="kn_001", target_node_id="kn_002",
            edge_type=EdgeType.RELATED_TO,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        edge2 = KnowledgeEdge(
            id="ke_005", source_node_id="kn_001", target_node_id="kn_002",
            edge_type=EdgeType.RELATED_TO,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        storage.create_edge(edge1)
        
        with pytest.raises(Exception):
            storage.create_edge(edge2)
    
    def test_create_edge_with_evidence(self, storage):
        """Test creating edge with evidence."""
        edge = KnowledgeEdge(
            id="ke_006", source_node_id="kn_001", target_node_id="kn_002",
            edge_type=EdgeType.SUPPORTS,
            evidence="This decision supports the requirement",
            weight=0.9,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        result = storage.create_edge(edge)
        assert result.evidence == "This decision supports the requirement"
        assert result.weight == 0.9


class TestSQLiteStorageQuery:
    """Tests for query methods."""
    
    @pytest.fixture
    def storage_with_data(self, tmp_path):
        """Create storage with sample data."""
        db_path = str(tmp_path / "test_kg.db")
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        
        nodes = [
            KnowledgeNode(
                id=f"kn_{i:03d}",
                node_type=NodeType.REQUIREMENT if i < 3 else NodeType.DECISION,
                title=f"Node {i}",
                content=f"Content {i}",
                project_name="TestProject" if i < 4 else "OtherProject",
                importance=0.5 + (i * 0.05),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            for i in range(5)
        ]
        for node in nodes:
            storage.create_node(node)
        
        storage.create_edge(KnowledgeEdge(
            id="ke_001", source_node_id="kn_000", target_node_id="kn_001",
            edge_type=EdgeType.DEPENDS_ON,
            created_at=datetime.now(), updated_at=datetime.now()
        ))
        storage.create_edge(KnowledgeEdge(
            id="ke_002", source_node_id="kn_001", target_node_id="kn_002",
            edge_type=EdgeType.MAPS_TO,
            created_at=datetime.now(), updated_at=datetime.now()
        ))
        
        return storage
    
    def test_query_nodes_no_filter(self, storage_with_data):
        """Test query all nodes."""
        nodes = storage_with_data.query_nodes({})
        assert len(nodes) == 5
    
    def test_query_nodes_by_type(self, storage_with_data):
        """Test filter by node type."""
        nodes = storage_with_data.query_nodes({'node_type': 'requirement'})
        assert len(nodes) == 3
        assert all(n.node_type == NodeType.REQUIREMENT for n in nodes)
    
    def test_query_nodes_by_project(self, storage_with_data):
        """Test filter by project."""
        nodes = storage_with_data.query_nodes({'project_name': 'TestProject'})
        assert len(nodes) == 4
    
    def test_query_nodes_with_limit(self, storage_with_data):
        """Test pagination with limit."""
        nodes = storage_with_data.query_nodes({}, limit=2)
        assert len(nodes) == 2
    
    def test_query_nodes_with_offset(self, storage_with_data):
        """Test pagination with offset."""
        page1 = storage_with_data.query_nodes({}, limit=2, offset=0)
        page2 = storage_with_data.query_nodes({}, limit=2, offset=2)
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].id != page2[0].id
    
    def test_query_edges_no_filter(self, storage_with_data):
        """Test query all edges."""
        edges = storage_with_data.query_edges({})
        assert len(edges) == 2
    
    def test_query_edges_by_type(self, storage_with_data):
        """Test filter edges by type."""
        edges = storage_with_data.query_edges({'edge_type': 'depends_on'})
        assert len(edges) == 1
        assert edges[0].edge_type == EdgeType.DEPENDS_ON
    
    def test_query_edges_by_source(self, storage_with_data):
        """Test filter edges by source node."""
        edges = storage_with_data.query_edges({'source_node_id': 'kn_000'})
        assert len(edges) == 1
    
    def test_get_stats(self, storage_with_data):
        """Test get_stats returns correct counts."""
        stats = storage_with_data.get_stats()
        
        assert stats['total_nodes'] == 5
        assert stats['total_edges'] == 2
        assert 'by_type' in stats
        assert stats['by_type']['requirement'] == 3
        assert stats['by_type']['decision'] == 2
