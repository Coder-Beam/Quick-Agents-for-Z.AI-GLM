"""Tests for SQLite storage backend."""

import pytest
import sqlite3
from pathlib import Path
from datetime import datetime
from quickagents.knowledge_graph.storage.sqlite_storage import SQLiteGraphStorage
from quickagents.knowledge_graph.types import KnowledgeNode, NodeType


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
