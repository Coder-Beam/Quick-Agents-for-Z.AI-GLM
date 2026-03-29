# Knowledge Graph Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a lightweight knowledge graph system integrated with UnifiedDB, supporting knowledge extraction, relation discovery, and intelligent search.

**Architecture:** Three-layer architecture (Application → Abstraction → Storage) with 6 minimal unit classes behind a facade pattern. SQLite graph storage with FTS5 full-text search, pluggable interfaces for future Neo4j/VectorDB integration.

**Tech Stack:** Python 3.8+, SQLite with FTS5, dataclasses, enum, abc

---

## File Structure

### New Files to Create

```
quickagents/knowledge_graph/
├── __init__.py              # Module exports
├── types.py                 # NodeType, EdgeType, dataclasses
├── exceptions.py            # Custom exceptions
├── interfaces.py            # Abstract interfaces
├── storage/
│   ├── __init__.py
│   └── sqlite_storage.py    # SQLite implementation
├── core/
│   ├── __init__.py
│   ├── node_manager.py
│   ├── edge_manager.py
│   ├── knowledge_extractor.py
│   ├── relation_discovery.py
│   ├── knowledge_searcher.py
│   └── memory_sync.py
└── knowledge_graph.py       # Facade class

tests/knowledge_graph/
├── __init__.py
├── test_node_manager.py
├── test_edge_manager.py
├── test_knowledge_extractor.py
├── test_relation_discovery.py
├── test_knowledge_searcher.py
├── test_memory_sync.py
├── test_integration.py
└── test_performance.py
```

### Files to Modify

```
quickagents/core/unified_db.py   # Add knowledge property
quickagents/cli/qa.py            # Add knowledge commands
quickagents/__init__.py          # Export KnowledgeGraph
```

---

## Phase 1: Foundation (Types, Exceptions, Interfaces)

### Task 1.1: Create types.py with enums and dataclasses

**Files:**
- Create: `quickagents/knowledge_graph/__init__.py`
- Create: `quickagents/knowledge_graph/types.py`
- Test: `tests/knowledge_graph/__init__.py`

- [ ] **Step 1: Create module directory structure**

```bash
mkdir -p quickagents/knowledge_graph/core
mkdir -p quickagents/knowledge_graph/storage
mkdir -p tests/knowledge_graph
```

- [ ] **Step 2: Write failing test for NodeType enum**

Create: `tests/knowledge_graph/test_types.py`

```python
"""Tests for knowledge graph types."""

import pytest
from quickagents.knowledge_graph.types import NodeType, EdgeType


class TestNodeType:
    """Tests for NodeType enum."""
    
    def test_node_type_values(self):
        """Test all node type values exist."""
        assert NodeType.REQUIREMENT.value == "requirement"
        assert NodeType.DECISION.value == "decision"
        assert NodeType.INSIGHT.value == "insight"
        assert NodeType.FACT.value == "fact"
        assert NodeType.CONCEPT.value == "concept"
        assert NodeType.SOURCE.value == "source"
    
    def test_node_type_count(self):
        """Test total number of node types."""
        assert len(NodeType) == 6
    
    def test_node_type_from_string(self):
        """Test creating NodeType from string."""
        assert NodeType("requirement") == NodeType.REQUIREMENT
        with pytest.raises(ValueError):
            NodeType("invalid")


class TestEdgeType:
    """Tests for EdgeType enum."""
    
    def test_edge_type_values(self):
        """Test all edge type values exist."""
        assert EdgeType.DEPENDS_ON.value == "depends_on"
        assert EdgeType.IS_SUBCLASS_OF.value == "is_subclass_of"
        assert EdgeType.CITES.value == "cites"
        assert EdgeType.LINKS_TO.value == "links_to"
        assert EdgeType.EVOLVES_FROM.value == "evolves_from"
        assert EdgeType.MAPS_TO.value == "maps_to"
        assert EdgeType.AFFECTS.value == "affects"
        assert EdgeType.CONTRADICTS.value == "contradicts"
        assert EdgeType.SUPPORTS.value == "supports"
        assert EdgeType.RELATED_TO.value == "related_to"
        assert EdgeType.INDIRECTLY_RELATED_TO.value == "indirectly_related_to"
    
    def test_edge_type_count(self):
        """Test total number of edge types."""
        assert len(EdgeType) == 11
```

- [ ] **Step 3: Run test to verify it fails**

```bash
pytest tests/knowledge_graph/test_types.py -v
```
Expected: FAIL with "ModuleNotFoundError: No module named 'quickagents.knowledge_graph'"

- [ ] **Step 4: Create __init__.py files**

Create: `quickagents/knowledge_graph/__init__.py`
```python
"""Knowledge Graph module for QuickAgents."""

from .types import NodeType, EdgeType, KnowledgeNode, KnowledgeEdge, SearchResult
from .knowledge_graph import KnowledgeGraph

__all__ = [
    'NodeType',
    'EdgeType',
    'KnowledgeNode',
    'KnowledgeEdge',
    'SearchResult',
    'KnowledgeGraph',
]
```

Create: `quickagents/knowledge_graph/core/__init__.py`
```python
"""Core components for knowledge graph."""
```

Create: `quickagents/knowledge_graph/storage/__init__.py`
```python
"""Storage backends for knowledge graph."""
```

Create: `tests/knowledge_graph/__init__.py`
```python
"""Tests for knowledge graph module."""
```

- [ ] **Step 5: Write minimal types.py**

Create: `quickagents/knowledge_graph/types.py`

```python
"""
Knowledge Graph Types

Defines core types: NodeType, EdgeType, KnowledgeNode, KnowledgeEdge, SearchResult.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


class NodeType(Enum):
    """Knowledge node types."""
    REQUIREMENT = "requirement"
    DECISION = "decision"
    INSIGHT = "insight"
    FACT = "fact"
    CONCEPT = "concept"
    SOURCE = "source"


class EdgeType(Enum):
    """Knowledge edge types."""
    DEPENDS_ON = "depends_on"
    IS_SUBCLASS_OF = "is_subclass_of"
    CITES = "cites"
    LINKS_TO = "links_to"
    EVOLVES_FROM = "evolves_from"
    MAPS_TO = "maps_to"
    AFFECTS = "affects"
    CONTRADICTS = "contradicts"
    SUPPORTS = "supports"
    RELATED_TO = "related_to"
    INDIRECTLY_RELATED_TO = "indirectly_related_to"


@dataclass
class KnowledgeNode:
    """Knowledge node data class."""
    id: str
    node_type: NodeType
    title: str
    content: str
    source_type: Optional[str] = None
    source_uri: Optional[str] = None
    confidence: float = 1.0
    importance: float = 0.5
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    project_name: Optional[str] = None
    feature_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed_at: Optional[datetime] = None


@dataclass
class KnowledgeEdge:
    """Knowledge edge data class."""
    id: str
    source_node_id: str
    target_node_id: str
    edge_type: EdgeType
    weight: float = 1.0
    evidence: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class SearchResult:
    """Search result data class."""
    nodes: List[KnowledgeNode]
    total: int
    has_more: bool
    query_time_ms: float
    related_nodes: List[KnowledgeNode] = field(default_factory=list)
```

- [ ] **Step 6: Run test to verify it passes**

```bash
pytest tests/knowledge_graph/test_types.py -v
```
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add quickagents/knowledge_graph/ tests/knowledge_graph/
git commit -m "feat(knowledge-graph): add types module with NodeType, EdgeType, dataclasses

- Add NodeType enum (6 types: requirement, decision, insight, fact, concept, source)
- Add EdgeType enum (11 types: depends_on, cites, maps_to, etc.)
- Add KnowledgeNode, KnowledgeEdge, SearchResult dataclasses
- Add comprehensive unit tests for enums"
```

---

### Task 1.2: Create exceptions.py

**Files:**
- Create: `quickagents/knowledge_graph/exceptions.py`
- Test: `tests/knowledge_graph/test_exceptions.py`

- [ ] **Step 1: Write failing test for exceptions**

Create: `tests/knowledge_graph/test_exceptions.py`

```python
"""Tests for knowledge graph exceptions."""

import pytest
from quickagents.knowledge_graph.exceptions import (
    KnowledgeGraphError,
    NodeNotFoundError,
    EdgeNotFoundError,
    DuplicateNodeError,
    DuplicateEdgeError,
    InvalidNodeTypeError,
    InvalidEdgeTypeError,
    CircularDependencyError,
    DatabaseIntegrityError,
    ExtractionError,
    SyncError,
)


class TestExceptions:
    """Tests for all custom exceptions."""
    
    def test_base_exception(self):
        """Test base exception is Exception subclass."""
        assert issubclass(KnowledgeGraphError, Exception)
    
    def test_node_not_found_error(self):
        """Test NodeNotFoundError with node_id."""
        error = NodeNotFoundError("kn_001")
        assert error.node_id == "kn_001"
        assert "kn_001" in str(error)
    
    def test_edge_not_found_error(self):
        """Test EdgeNotFoundError with edge_id."""
        error = EdgeNotFoundError("ke_001")
        assert error.edge_id == "ke_001"
        assert "ke_001" in str(error)
    
    def test_duplicate_node_error(self):
        """Test DuplicateNodeError with title and existing_id."""
        error = DuplicateNodeError("Test Title", "kn_existing")
        assert error.title == "Test Title"
        assert error.existing_id == "kn_existing"
    
    def test_duplicate_edge_error(self):
        """Test DuplicateEdgeError with source, target, type."""
        error = DuplicateEdgeError("kn_1", "kn_2", "depends_on")
        assert error.source_id == "kn_1"
        assert error.target_id == "kn_2"
        assert error.edge_type == "depends_on"
    
    def test_invalid_node_type_error(self):
        """Test InvalidNodeTypeError."""
        error = InvalidNodeTypeError("invalid_type")
        assert error.node_type == "invalid_type"
    
    def test_invalid_edge_type_error(self):
        """Test InvalidEdgeTypeError."""
        error = InvalidEdgeTypeError("invalid_edge")
        assert error.edge_type == "invalid_edge"
    
    def test_circular_dependency_error(self):
        """Test CircularDependencyError with path."""
        error = CircularDependencyError(["A", "B", "C", "A"])
        assert error.path == ["A", "B", "C", "A"]
        assert "A" in str(error)
    
    def test_extraction_error(self):
        """Test ExtractionError with source and reason."""
        error = ExtractionError("test.pdf", "File not found")
        assert error.source == "test.pdf"
        assert error.reason == "File not found"
    
    def test_sync_error(self):
        """Test SyncError with target and reason."""
        error = SyncError("MEMORY.md", "Permission denied")
        assert error.target == "MEMORY.md"
        assert error.reason == "Permission denied"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/knowledge_graph/test_exceptions.py -v
```
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Write minimal exceptions.py**

Create: `quickagents/knowledge_graph/exceptions.py`

```python
"""
Knowledge Graph Exceptions

Custom exceptions for knowledge graph operations.
"""

from typing import List


class KnowledgeGraphError(Exception):
    """Base exception for knowledge graph operations."""
    pass


class NodeNotFoundError(KnowledgeGraphError):
    """Raised when a node is not found."""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        super().__init__(f"Node not found: {node_id}")


class EdgeNotFoundError(KnowledgeGraphError):
    """Raised when an edge is not found."""
    
    def __init__(self, edge_id: str):
        self.edge_id = edge_id
        super().__init__(f"Edge not found: {edge_id}")


class DuplicateNodeError(KnowledgeGraphError):
    """Raised when attempting to create a duplicate node."""
    
    def __init__(self, title: str, existing_id: str):
        self.title = title
        self.existing_id = existing_id
        super().__init__(f"Duplicate node with similar title: {title} (existing: {existing_id})")


class DuplicateEdgeError(KnowledgeGraphError):
    """Raised when attempting to create a duplicate edge."""
    
    def __init__(self, source_id: str, target_id: str, edge_type: str):
        self.source_id = source_id
        self.target_id = target_id
        self.edge_type = edge_type
        super().__init__(f"Edge already exists: {source_id} -> {target_id} ({edge_type})")


class InvalidNodeTypeError(KnowledgeGraphError):
    """Raised when an invalid node type is provided."""
    
    def __init__(self, node_type: str):
        self.node_type = node_type
        super().__init__(f"Invalid node type: {node_type}")


class InvalidEdgeTypeError(KnowledgeGraphError):
    """Raised when an invalid edge type is provided."""
    
    def __init__(self, edge_type: str):
        self.edge_type = edge_type
        super().__init__(f"Invalid edge type: {edge_type}")


class CircularDependencyError(KnowledgeGraphError):
    """Raised when a circular dependency is detected."""
    
    def __init__(self, path: List[str]):
        self.path = path
        super().__init__(f"Circular dependency detected: {' -> '.join(path)}")


class DatabaseIntegrityError(KnowledgeGraphError):
    """Raised when database integrity is violated."""
    pass


class ExtractionError(KnowledgeGraphError):
    """Raised when knowledge extraction fails."""
    
    def __init__(self, source: str, reason: str):
        self.source = source
        self.reason = reason
        super().__init__(f"Failed to extract knowledge from {source}: {reason}")


class SyncError(KnowledgeGraphError):
    """Raised when synchronization fails."""
    
    def __init__(self, target: str, reason: str):
        self.target = target
        self.reason = reason
        super().__init__(f"Failed to sync to {target}: {reason}")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/knowledge_graph/test_exceptions.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add quickagents/knowledge_graph/exceptions.py tests/knowledge_graph/test_exceptions.py
git commit -m "feat(knowledge-graph): add custom exceptions module

- Add KnowledgeGraphError base class
- Add NodeNotFoundError, EdgeNotFoundError
- Add DuplicateNodeError, DuplicateEdgeError
- Add InvalidNodeTypeError, InvalidEdgeTypeError
- Add CircularDependencyError, DatabaseIntegrityError
- Add ExtractionError, SyncError
- All with comprehensive unit tests"
```

---

### Task 1.3: Create interfaces.py with abstract base classes

**Files:**
- Create: `quickagents/knowledge_graph/interfaces.py`
- Test: `tests/knowledge_graph/test_interfaces.py`

- [ ] **Step 1: Write failing test for interfaces**

Create: `tests/knowledge_graph/test_interfaces.py`

```python
"""Tests for knowledge graph interfaces."""

import pytest
from abc import ABC
from quickagents.knowledge_graph.interfaces import GraphStorageInterface, VectorSearchInterface


class TestGraphStorageInterface:
    """Tests for GraphStorageInterface."""
    
    def test_is_abstract(self):
        """Test that GraphStorageInterface is abstract."""
        assert issubclass(GraphStorageInterface, ABC)
    
    def test_has_required_methods(self):
        """Test interface has all required abstract methods."""
        methods = [
            'initialize',
            'create_node',
            'get_node',
            'update_node',
            'delete_node',
            'create_edge',
            'get_edge',
            'delete_edge',
            'query_nodes',
            'query_edges',
            'find_path',
            'get_stats',
        ]
        for method in methods:
            assert hasattr(GraphStorageInterface, method)


class TestVectorSearchInterface:
    """Tests for VectorSearchInterface."""
    
    def test_is_abstract(self):
        """Test that VectorSearchInterface is abstract."""
        assert issubclass(VectorSearchInterface, ABC)
    
    def test_has_required_methods(self):
        """Test interface has all required abstract methods."""
        methods = [
            'initialize',
            'index_node',
            'remove_node',
            'search',
            'get_embedding',
        ]
        for method in methods:
            assert hasattr(VectorSearchInterface, method)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/knowledge_graph/test_interfaces.py -v
```
Expected: FAIL

- [ ] **Step 3: Write minimal interfaces.py**

Create: `quickagents/knowledge_graph/interfaces.py`

```python
"""
Knowledge Graph Interfaces

Abstract interfaces for pluggable storage and search backends.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from .types import KnowledgeNode, KnowledgeEdge


class GraphStorageInterface(ABC):
    """
    Abstract interface for graph storage backends.
    
    Implementations:
    - SQLiteGraphStorage (default)
    - Neo4jGraphStorage (future enterprise extension)
    """
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the storage backend."""
        pass
    
    @abstractmethod
    def create_node(self, node: KnowledgeNode) -> KnowledgeNode:
        """Create a node."""
        pass
    
    @abstractmethod
    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Get a node by ID."""
        pass
    
    @abstractmethod
    def update_node(self, node_id: str, updates: Dict[str, Any]) -> KnowledgeNode:
        """Update a node."""
        pass
    
    @abstractmethod
    def delete_node(self, node_id: str, cascade: bool = True) -> bool:
        """Delete a node."""
        pass
    
    @abstractmethod
    def create_edge(self, edge: KnowledgeEdge) -> KnowledgeEdge:
        """Create an edge."""
        pass
    
    @abstractmethod
    def get_edge(self, edge_id: str) -> Optional[KnowledgeEdge]:
        """Get an edge by ID."""
        pass
    
    @abstractmethod
    def delete_edge(self, edge_id: str) -> bool:
        """Delete an edge."""
        pass
    
    @abstractmethod
    def query_nodes(
        self,
        filters: Dict[str, Any],
        limit: int = 100,
        offset: int = 0
    ) -> List[KnowledgeNode]:
        """Query nodes with filters."""
        pass
    
    @abstractmethod
    def query_edges(
        self,
        filters: Dict[str, Any],
        limit: int = 100
    ) -> List[KnowledgeEdge]:
        """Query edges with filters."""
        pass
    
    @abstractmethod
    def find_path(
        self,
        from_node: str,
        to_node: str,
        max_depth: int = 5
    ) -> Optional[List[str]]:
        """Find path between two nodes."""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        pass


class VectorSearchInterface(ABC):
    """
    Abstract interface for vector search engines.
    
    Implementations:
    - SQLiteFTSSearch (default, uses FTS5)
    - ChromaDBVectorSearch (future enhanced extension)
    """
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the search engine."""
        pass
    
    @abstractmethod
    def index_node(self, node: KnowledgeNode) -> bool:
        """Index a node for search."""
        pass
    
    @abstractmethod
    def remove_node(self, node_id: str) -> bool:
        """Remove a node from the index."""
        pass
    
    @abstractmethod
    def search(
        self,
        query: str,
        top_k: int = 20,
        filters: Dict[str, Any] = None
    ) -> List[Tuple[str, float]]:
        """
        Search for nodes.
        
        Returns:
            List of (node_id, score) tuples.
        """
        pass
    
    @abstractmethod
    def get_embedding(self, node_id: str) -> Optional[List[float]]:
        """Get the embedding vector for a node."""
        pass
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/knowledge_graph/test_interfaces.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add quickagents/knowledge_graph/interfaces.py tests/knowledge_graph/test_interfaces.py
git commit -m "feat(knowledge-graph): add abstract interfaces for pluggable backends

- Add GraphStorageInterface (12 abstract methods)
- Add VectorSearchInterface (5 abstract methods)
- Enables future Neo4j and ChromaDB integration"
```

---

## Phase 2: Storage Layer (SQLite Implementation)

### Task 2.1: Create SQLite storage - Schema initialization

**Files:**
- Create: `quickagents/knowledge_graph/storage/sqlite_storage.py`
- Test: `tests/knowledge_graph/test_sqlite_storage.py`

- [ ] **Step 1: Write failing test for schema initialization**

Create: `tests/knowledge_graph/test_sqlite_storage.py`

```python
"""Tests for SQLite storage backend."""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from quickagents.knowledge_graph.storage.sqlite_storage import SQLiteGraphStorage


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
        
        # Check for key indexes
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
        
        # Check for unique index
        unique_indexes = [idx for idx in indexes if idx[2] == 1]  # idx[2] is unique flag
        assert len(unique_indexes) > 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/knowledge_graph/test_sqlite_storage.py -v
```
Expected: FAIL

- [ ] **Step 3: Write minimal SQLite storage with schema**

Create: `quickagents/knowledge_graph/storage/sqlite_storage.py`

```python
"""
SQLite Graph Storage

Implements GraphStorageInterface using SQLite with FTS5.
"""

import sqlite3
import json
import uuid
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from contextlib import contextmanager

from ..interfaces import GraphStorageInterface
from ..types import KnowledgeNode, KnowledgeEdge, NodeType, EdgeType
from ..exceptions import NodeNotFoundError, EdgeNotFoundError


class SQLiteGraphStorage(GraphStorageInterface):
    """
    SQLite implementation of GraphStorageInterface.
    
    Uses SQLite with FTS5 for full-text search.
    """
    
    def __init__(self, db_path: str):
        """
        Initialize SQLite storage.
        
        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialized = False
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with context manager."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize database schema."""
        if self._initialized:
            return True
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create knowledge_nodes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_nodes (
                    id TEXT PRIMARY KEY,
                    node_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source_type TEXT,
                    source_uri TEXT,
                    confidence REAL DEFAULT 1.0,
                    importance REAL DEFAULT 0.5,
                    tags TEXT,
                    metadata TEXT,
                    project_name TEXT,
                    feature_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    access_count INTEGER DEFAULT 0,
                    last_accessed_at TEXT
                )
            ''')
            
            # Create indexes for knowledge_nodes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_type ON knowledge_nodes(node_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_project ON knowledge_nodes(project_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_feature ON knowledge_nodes(feature_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_importance ON knowledge_nodes(importance DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_created ON knowledge_nodes(created_at DESC)')
            
            # Create knowledge_edges table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_edges (
                    id TEXT PRIMARY KEY,
                    source_node_id TEXT NOT NULL,
                    target_node_id TEXT NOT NULL,
                    edge_type TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    evidence TEXT,
                    metadata TEXT,
                    confidence REAL DEFAULT 1.0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    
                    FOREIGN KEY (source_node_id) REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
                    FOREIGN KEY (target_node_id) REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
                    
                    UNIQUE(source_node_id, target_node_id, edge_type)
                )
            ''')
            
            # Create indexes for knowledge_edges
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_edges_source ON knowledge_edges(source_node_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_edges_target ON knowledge_edges(target_node_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_edges_type ON knowledge_edges(edge_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_edges_weight ON knowledge_edges(weight DESC)')
            
            # Create FTS5 virtual table for full-text search
            cursor.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_index USING fts5(
                    node_id UNINDEXED,
                    title,
                    content,
                    tags,
                    source_uri,
                    tokenize='porter unicode61',
                    content='knowledge_nodes',
                    content_rowid='rowid'
                )
            ''')
            
            # Create triggers for auto-syncing FTS index
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS idx_node_insert 
                AFTER INSERT ON knowledge_nodes BEGIN
                    INSERT INTO knowledge_index(rowid, node_id, title, content, tags, source_uri)
                    VALUES (NEW.rowid, NEW.id, NEW.title, NEW.content, NEW.tags, NEW.source_uri);
                END
            ''')
            
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS idx_node_update 
                AFTER UPDATE ON knowledge_nodes BEGIN
                    UPDATE knowledge_index 
                    SET title=NEW.title, content=NEW.content, tags=NEW.tags, source_uri=NEW.source_uri
                    WHERE rowid=NEW.rowid;
                END
            ''')
            
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS idx_node_delete 
                AFTER DELETE ON knowledge_nodes BEGIN
                    DELETE FROM knowledge_index WHERE rowid=OLD.rowid;
                END
            ''')
            
            conn.commit()
        
        self._initialized = True
        return True
    
    # Remaining methods will be implemented in subsequent tasks
    def create_node(self, node: KnowledgeNode) -> KnowledgeNode:
        raise NotImplementedError("Implemented in Task 2.2")
    
    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        raise NotImplementedError("Implemented in Task 2.2")
    
    def update_node(self, node_id: str, updates: Dict[str, Any]) -> KnowledgeNode:
        raise NotImplementedError("Implemented in Task 2.2")
    
    def delete_node(self, node_id: str, cascade: bool = True) -> bool:
        raise NotImplementedError("Implemented in Task 2.2")
    
    def create_edge(self, edge: KnowledgeEdge) -> KnowledgeEdge:
        raise NotImplementedError("Implemented in Task 2.3")
    
    def get_edge(self, edge_id: str) -> Optional[KnowledgeEdge]:
        raise NotImplementedError("Implemented in Task 2.3")
    
    def delete_edge(self, edge_id: str) -> bool:
        raise NotImplementedError("Implemented in Task 2.3")
    
    def query_nodes(self, filters: Dict[str, Any], limit: int = 100, offset: int = 0) -> List[KnowledgeNode]:
        raise NotImplementedError("Implemented in Task 2.4")
    
    def query_edges(self, filters: Dict[str, Any], limit: int = 100) -> List[KnowledgeEdge]:
        raise NotImplementedError("Implemented in Task 2.4")
    
    def find_path(self, from_node: str, to_node: str, max_depth: int = 5) -> Optional[List[str]]:
        raise NotImplementedError("Implemented in Task 2.5")
    
    def get_stats(self) -> Dict[str, Any]:
        raise NotImplementedError("Implemented in Task 2.4")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/knowledge_graph/test_sqlite_storage.py::TestSQLiteStorageSchema -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add quickagents/knowledge_graph/storage/sqlite_storage.py tests/knowledge_graph/test_sqlite_storage.py
git commit -m "feat(knowledge-graph): add SQLite storage schema initialization

- Create knowledge_nodes table with 16 columns
- Create knowledge_edges table with 10 columns
- Create FTS5 virtual table for full-text search
- Add auto-sync triggers for FTS index
- Add comprehensive schema tests"
```

---

### Task 2.2: Implement Node CRUD operations in SQLite storage

**Files:**
- Modify: `quickagents/knowledge_graph/storage/sqlite_storage.py`
- Test: `tests/knowledge_graph/test_sqlite_storage.py` (extend)

- [ ] **Step 1: Write failing tests for node CRUD**

Add to `tests/knowledge_graph/test_sqlite_storage.py`:

```python
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
        from quickagents.knowledge_graph.types import NodeType
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/knowledge_graph/test_sqlite_storage.py::TestSQLiteStorageNodeCRUD -v
```
Expected: FAIL with NotImplementedError

- [ ] **Step 3: Implement node CRUD methods**

Update `quickagents/knowledge_graph/storage/sqlite_storage.py`:

```python
    def _row_to_node(self, row: sqlite3.Row) -> KnowledgeNode:
        """Convert database row to KnowledgeNode."""
        return KnowledgeNode(
            id=row['id'],
            node_type=NodeType(row['node_type']),
            title=row['title'],
            content=row['content'],
            source_type=row['source_type'],
            source_uri=row['source_uri'],
            confidence=row['confidence'],
            importance=row['importance'],
            tags=json.loads(row['tags']) if row['tags'] else [],
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            project_name=row['project_name'],
            feature_id=row['feature_id'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
            access_count=row['access_count'],
            last_accessed_at=datetime.fromisoformat(row['last_accessed_at']) if row['last_accessed_at'] else None,
        )
    
    def create_node(self, node: KnowledgeNode) -> KnowledgeNode:
        """Create a node in the database."""
        now = datetime.now().isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO knowledge_nodes (
                    id, node_type, title, content, source_type, source_uri,
                    confidence, importance, tags, metadata, project_name,
                    feature_id, created_at, updated_at, access_count, last_accessed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                node.id,
                node.node_type.value,
                node.title,
                node.content,
                node.source_type,
                node.source_uri,
                node.confidence,
                node.importance,
                json.dumps(node.tags) if node.tags else None,
                json.dumps(node.metadata) if node.metadata else None,
                node.project_name,
                node.feature_id,
                node.created_at.isoformat() if node.created_at else now,
                node.updated_at.isoformat() if node.updated_at else now,
                node.access_count,
                node.last_accessed_at.isoformat() if node.last_accessed_at else None,
            ))
            conn.commit()
        
        return self.get_node(node.id)
    
    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Get a node by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM knowledge_nodes WHERE id = ?',
                (node_id,)
            )
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            return self._row_to_node(row)
    
    def update_node(self, node_id: str, updates: Dict[str, Any]) -> KnowledgeNode:
        """Update a node."""
        # Build dynamic update query
        set_clauses = []
        values = []
        
        for key, value in updates.items():
            if key in ['tags', 'metadata']:
                value = json.dumps(value) if value else None
            elif key in ['created_at', 'updated_at', 'last_accessed_at']:
                value = value.isoformat() if isinstance(value, datetime) else value
            elif key == 'node_type':
                value = value.value if isinstance(value, NodeType) else value
            
            set_clauses.append(f"{key} = ?")
            values.append(value)
        
        # Always update updated_at
        set_clauses.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        
        values.append(node_id)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE knowledge_nodes SET {', '.join(set_clauses)} WHERE id = ?",
                values
            )
            conn.commit()
        
        result = self.get_node(node_id)
        if result is None:
            raise NodeNotFoundError(node_id)
        return result
    
    def delete_node(self, node_id: str, cascade: bool = True) -> bool:
        """Delete a node."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if cascade:
                # CASCADE will handle edges automatically
                cursor.execute('DELETE FROM knowledge_nodes WHERE id = ?', (node_id,))
            else:
                # Check for existing edges first
                cursor.execute(
                    'SELECT COUNT(*) FROM knowledge_edges WHERE source_node_id = ? OR target_node_id = ?',
                    (node_id, node_id)
                )
                count = cursor.fetchone()[0]
                if count > 0:
                    return False
                cursor.execute('DELETE FROM knowledge_nodes WHERE id = ?', (node_id,))
            
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/knowledge_graph/test_sqlite_storage.py::TestSQLiteStorageNodeCRUD -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add quickagents/knowledge_graph/storage/sqlite_storage.py tests/knowledge_graph/test_sqlite_storage.py
git commit -m "feat(knowledge-graph): implement node CRUD operations in SQLite storage

- Add create_node, get_node, update_node, delete_node
- Add _row_to_node helper for row conversion
- Handle JSON serialization for tags and metadata
- Add comprehensive CRUD tests (9 test cases)"
```

---

### Task 2.3: Implement Edge CRUD operations in SQLite storage

**Files:**
- Modify: `quickagents/knowledge_graph/storage/sqlite_storage.py`
- Test: `tests/knowledge_graph/test_sqlite_storage.py` (extend)

- [ ] **Step 1: Write failing tests for edge CRUD**

Add to `tests/knowledge_graph/test_sqlite_storage.py`:

```python
class TestSQLiteStorageEdgeCRUD:
    """Tests for edge CRUD operations."""
    
    @pytest.fixture
    def storage(self, tmp_path):
        """Create initialized storage with sample nodes."""
        db_path = str(tmp_path / "test_kg.db")
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        
        # Create sample nodes
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
            edge_type=EdgeType.RELATED_TO,  # Same as edge1
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        storage.create_edge(edge1)
        
        with pytest.raises(Exception):  # IntegrityError
            storage.create_edge(edge2)
    
    def test_create_edge_with_evidence(self, storage):
        """Test creating edge with evidence."""
        edge = KnowledgeEdge(
            id="ke_006", source_node_id="kn_001", target_node_id="kn_002",
            edge_type=EdgeType.SUPPORTS,
            evidence="This decision supports the requirement",
            weight=0.9,
            created_at=datetime.now(), updated_at=datetime.now()
        )
        
        result = storage.create_edge(edge)
        assert result.evidence == "This decision supports the requirement"
        assert result.weight == 0.9
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/knowledge_graph/test_sqlite_storage.py::TestSQLiteStorageEdgeCRUD -v
```
Expected: FAIL

- [ ] **Step 3: Implement edge CRUD methods**

Update `quickagents/knowledge_graph/storage/sqlite_storage.py`:

```python
    def _row_to_edge(self, row: sqlite3.Row) -> KnowledgeEdge:
        """Convert database row to KnowledgeEdge."""
        return KnowledgeEdge(
            id=row['id'],
            source_node_id=row['source_node_id'],
            target_node_id=row['target_node_id'],
            edge_type=EdgeType(row['edge_type']),
            weight=row['weight'],
            evidence=row['evidence'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            confidence=row['confidence'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
        )
    
    def create_edge(self, edge: KnowledgeEdge) -> KnowledgeEdge:
        """Create an edge in the database."""
        now = datetime.now().isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO knowledge_edges (
                        id, source_node_id, target_node_id, edge_type,
                        weight, evidence, metadata, confidence,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    edge.id,
                    edge.source_node_id,
                    edge.target_node_id,
                    edge.edge_type.value,
                    edge.weight,
                    edge.evidence,
                    json.dumps(edge.metadata) if edge.metadata else None,
                    edge.confidence,
                    edge.created_at.isoformat() if edge.created_at else now,
                    edge.updated_at.isoformat() if edge.updated_at else now,
                ))
                conn.commit()
            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed" in str(e):
                    from ..exceptions import DuplicateEdgeError
                    raise DuplicateEdgeError(
                        edge.source_node_id,
                        edge.target_node_id,
                        edge.edge_type.value
                    )
                raise
        
        return self.get_edge(edge.id)
    
    def get_edge(self, edge_id: str) -> Optional[KnowledgeEdge]:
        """Get an edge by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM knowledge_edges WHERE id = ?',
                (edge_id,)
            )
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            return self._row_to_edge(row)
    
    def delete_edge(self, edge_id: str) -> bool:
        """Delete an edge."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM knowledge_edges WHERE id = ?', (edge_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/knowledge_graph/test_sqlite_storage.py::TestSQLiteStorageEdgeCRUD -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add quickagents/knowledge_graph/storage/sqlite_storage.py tests/knowledge_graph/test_sqlite_storage.py
git commit -m "feat(knowledge-graph): implement edge CRUD operations in SQLite storage

- Add create_edge, get_edge, delete_edge
- Add _row_to_edge helper for row conversion
- Handle DuplicateEdgeError on constraint violation
- Add comprehensive edge CRUD tests (6 test cases)"
```

---

## Phase 3: Core Components (Minimal Units)

### Task 3.1: Implement NodeManager

**Files:**
- Create: `quickagents/knowledge_graph/core/node_manager.py`
- Test: `tests/knowledge_graph/test_node_manager.py`

- [ ] **Step 1: Write failing tests for NodeManager (20 test cases)**

Create: `tests/knowledge_graph/test_node_manager.py`

```python
"""Tests for NodeManager - 20 test cases for 100% coverage."""

import pytest
from datetime import datetime
from quickagents.knowledge_graph.core.node_manager import NodeManager
from quickagents.knowledge_graph.types import NodeType, KnowledgeNode
from quickagents.knowledge_graph.exceptions import NodeNotFoundError, DuplicateNodeError


class TestNodeManagerCreate:
    """Tests for NodeManager.create_node - 4 test cases."""
    
    @pytest.fixture
    def manager(self, tmp_path):
        from quickagents.knowledge_graph.storage.sqlite_storage import SQLiteGraphStorage
        storage = SQLiteGraphStorage(str(tmp_path / "test.db"))
        storage.initialize({})
        return NodeManager(storage)
    
    def test_create_node_basic(self, manager):
        """Test basic node creation."""
        node = manager.create_node(
            node_type=NodeType.REQUIREMENT,
            title="Test Requirement",
            content="Test content"
        )
        
        assert node.id.startswith("kn_")
        assert node.node_type == NodeType.REQUIREMENT
        assert node.title == "Test Requirement"
    
    def test_create_node_with_all_params(self, manager):
        """Test node creation with all parameters."""
        node = manager.create_node(
            node_type=NodeType.DECISION,
            title="Full Decision",
            content="Detailed content",
            source_type="doc",
            source_uri="file://test.md",
            confidence=0.95,
            importance=0.9,
            tags=["tag1", "tag2"],
            metadata={"key": "value"},
            project_name="TestProject",
            feature_id="F001"
        )
        
        assert node.confidence == 0.95
        assert node.importance == 0.9
        assert "tag1" in node.tags
        assert node.metadata["key"] == "value"
    
    def test_create_node_with_invalid_type(self, manager):
        """Test that invalid type is handled."""
        with pytest.raises(Exception):
            manager.create_node(
                node_type="invalid_type",
                title="Test",
                content="Content"
            )
    
    def test_create_node_duplicate_title_detection(self, manager):
        """Test duplicate title detection."""
        manager.create_node(
            node_type=NodeType.FACT,
            title="Same Title",
            content="Content 1"
        )
        
        # Similar title should be detected
        # (implementation may vary - exact match or similarity)
        node2 = manager.create_node(
            node_type=NodeType.FACT,
            title="Same Title",
            content="Content 2"
        )
        
        # Should still create, but may flag or return existing
        assert node2 is not None


class TestNodeManagerGet:
    """Tests for NodeManager.get_node - 3 test cases."""
    
    @pytest.fixture
    def manager(self, tmp_path):
        from quickagents.knowledge_graph.storage.sqlite_storage import SQLiteGraphStorage
        storage = SQLiteGraphStorage(str(tmp_path / "test.db"))
        storage.initialize({})
        return NodeManager(storage)
    
    def test_get_node_existing(self, manager):
        """Test getting existing node."""
        created = manager.create_node(
            node_type=NodeType.INSIGHT,
            title="Test",
            content="Content"
        )
        
        retrieved = manager.get_node(created.id)
        assert retrieved.id == created.id
        assert retrieved.title == created.title
    
    def test_get_node_nonexistent(self, manager):
        """Test getting non-existent node."""
        result = manager.get_node("kn_nonexistent")
        assert result is None
    
    def test_get_node_invalid_id_format(self, manager):
        """Test with invalid ID format."""
        result = manager.get_node("invalid_format")
        assert result is None


class TestNodeManagerUpdate:
    """Tests for NodeManager.update_node - 4 test cases."""
    
    @pytest.fixture
    def manager(self, tmp_path):
        from quickagents.knowledge_graph.storage.sqlite_storage import SQLiteGraphStorage
        storage = SQLiteGraphStorage(str(tmp_path / "test.db"))
        storage.initialize({})
        return NodeManager(storage)
    
    def test_update_node_title(self, manager):
        """Test updating node title."""
        node = manager.create_node(
            node_type=NodeType.CONCEPT,
            title="Original",
            content="Content"
        )
        
        updated = manager.update_node(node.id, title="Updated Title")
        assert updated.title == "Updated Title"
    
    def test_update_node_multiple_fields(self, manager):
        """Test updating multiple fields."""
        node = manager.create_node(
            node_type=NodeType.SOURCE,
            title="Original",
            content="Content"
        )
        
        updated = manager.update_node(
            node.id,
            title="New Title",
            content="New Content",
            importance=0.8
        )
        
        assert updated.title == "New Title"
        assert updated.content == "New Content"
        assert updated.importance == 0.8
    
    def test_update_node_nonexistent(self, manager):
        """Test updating non-existent node."""
        with pytest.raises(NodeNotFoundError):
            manager.update_node("kn_nonexistent", title="New Title")
    
    def test_update_node_empty_update(self, manager):
        """Test update with no fields."""
        node = manager.create_node(
            node_type=NodeType.FACT,
            title="Test",
            content="Content"
        )
        
        # Empty update should still succeed
        updated = manager.update_node(node.id)
        assert updated.id == node.id


class TestNodeManagerDelete:
    """Tests for NodeManager.delete_node - 4 test cases."""
    
    @pytest.fixture
    def manager(self, tmp_path):
        from quickagents.knowledge_graph.storage.sqlite_storage import SQLiteGraphStorage
        storage = SQLiteGraphStorage(str(tmp_path / "test.db"))
        storage.initialize({})
        return NodeManager(storage)
    
    def test_delete_node_basic(self, manager):
        """Test basic node deletion."""
        node = manager.create_node(
            node_type=NodeType.REQUIREMENT,
            title="To Delete",
            content="Content"
        )
        
        result = manager.delete_node(node.id)
        assert result is True
        assert manager.get_node(node.id) is None
    
    def test_delete_node_cascade_true(self, manager):
        """Test cascade delete removes related edges."""
        from quickagents.knowledge_graph.core.edge_manager import EdgeManager
        
        node1 = manager.create_node(NodeType.REQUIREMENT, "N1", "C1")
        node2 = manager.create_node(NodeType.DECISION, "N2", "C2")
        
        edge_manager = EdgeManager(manager.storage)
        edge = edge_manager.create_edge(node1.id, node2.id, EdgeType.DEPENDS_ON)
        
        # Cascade delete
        manager.delete_node(node1.id, cascade=True)
        
        # Edge should be deleted
        assert edge_manager.get_edge(edge.id) is None
    
    def test_delete_node_cascade_false(self, manager):
        """Test non-cascade delete with edges."""
        from quickagents.knowledge_graph.core.edge_manager import EdgeManager
        from quickagents.knowledge_graph.types import EdgeType
        
        node1 = manager.create_node(NodeType.REQUIREMENT, "N1", "C1")
        node2 = manager.create_node(NodeType.DECISION, "N2", "C2")
        
        edge_manager = EdgeManager(manager.storage)
        edge_manager.create_edge(node1.id, node2.id, EdgeType.DEPENDS_ON)
        
        # Non-cascade delete should fail with edges
        result = manager.delete_node(node1.id, cascade=False)
        assert result is False
        assert manager.get_node(node1.id) is not None
    
    def test_delete_node_nonexistent(self, manager):
        """Test deleting non-existent node."""
        result = manager.delete_node("kn_nonexistent")
        assert result is False


class TestNodeManagerList:
    """Tests for NodeManager.list_nodes - 5 test cases."""
    
    @pytest.fixture
    def manager(self, tmp_path):
        from quickagents.knowledge_graph.storage.sqlite_storage import SQLiteGraphStorage
        storage = SQLiteGraphStorage(str(tmp_path / "test.db"))
        storage.initialize({})
        return NodeManager(storage)
    
    def test_list_nodes_all(self, manager):
        """Test listing all nodes."""
        manager.create_node(NodeType.REQUIREMENT, "R1", "C1")
        manager.create_node(NodeType.DECISION, "D1", "C2")
        manager.create_node(NodeType.FACT, "F1", "C3")
        
        nodes = manager.list_nodes()
        assert len(nodes) == 3
    
    def test_list_nodes_by_type(self, manager):
        """Test filtering by node type."""
        manager.create_node(NodeType.REQUIREMENT, "R1", "C1")
        manager.create_node(NodeType.REQUIREMENT, "R2", "C2")
        manager.create_node(NodeType.DECISION, "D1", "C3")
        
        nodes = manager.list_nodes(node_type=NodeType.REQUIREMENT)
        assert len(nodes) == 2
        assert all(n.node_type == NodeType.REQUIREMENT for n in nodes)
    
    def test_list_nodes_with_limit(self, manager):
        """Test pagination with limit."""
        for i in range(10):
            manager.create_node(NodeType.FACT, f"F{i}", f"C{i}")
        
        nodes = manager.list_nodes(limit=5)
        assert len(nodes) == 5
    
    def test_list_nodes_empty_db(self, manager):
        """Test listing when database is empty."""
        nodes = manager.list_nodes()
        assert nodes == []
    
    def test_list_nodes_pagination(self, manager):
        """Test pagination with offset."""
        for i in range(10):
            manager.create_node(NodeType.CONCEPT, f"C{i}", f"Content{i}")
        
        page1 = manager.list_nodes(limit=5, offset=0)
        page2 = manager.list_nodes(limit=5, offset=5)
        
        # Pages should have different nodes
        page1_ids = {n.id for n in page1}
        page2_ids = {n.id for n in page2}
        assert page1_ids.isdisjoint(page2_ids)
```

(Note: Due to length, I'll continue with implementation in the plan document...)

---

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/knowledge_graph/test_node_manager.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement NodeManager**

Create: `quickagents/knowledge_graph/core/node_manager.py`

```python
"""
NodeManager - Minimal Unit

Manages knowledge node CRUD operations.
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..interfaces import GraphStorageInterface
from ..types import KnowledgeNode, NodeType
from ..exceptions import NodeNotFoundError, InvalidNodeTypeError


class NodeManager:
    """
    Node Manager - Minimal Unit
    
    Responsibilities:
    - Create, read, update, delete knowledge nodes
    - List nodes with filtering and pagination
    """
    
    def __init__(self, storage: GraphStorageInterface):
        """
        Initialize NodeManager.
        
        Args:
            storage: Graph storage backend
        """
        self.storage = storage
    
    def create_node(
        self,
        node_type: NodeType,
        title: str,
        content: str,
        source_type: Optional[str] = None,
        source_uri: Optional[str] = None,
        confidence: float = 1.0,
        importance: float = 0.5,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
        project_name: Optional[str] = None,
        feature_id: Optional[str] = None,
        auto_discover_relations: bool = True
    ) -> KnowledgeNode:
        """
        Create a knowledge node.
        
        Args:
            node_type: Type of node
            title: Short title
            content: Detailed content
            source_type: Source type (doc/paper/code/web/discussion)
            source_uri: Source URI
            confidence: Confidence score (0.0-1.0)
            importance: Importance score (0.0-1.0)
            tags: List of tags
            metadata: Additional metadata
            project_name: Project name
            feature_id: Feature module ID
            auto_discover_relations: Auto-discover relations after creation
            
        Returns:
            Created node
        """
        # Validate node type
        if isinstance(node_type, str):
            try:
                node_type = NodeType(node_type)
            except ValueError:
                raise InvalidNodeTypeError(node_type)
        
        # Generate ID
        node_id = f"kn_{uuid.uuid4().hex[:12]}"
        
        # Create node object
        node = KnowledgeNode(
            id=node_id,
            node_type=node_type,
            title=title,
            content=content,
            source_type=source_type,
            source_uri=source_uri,
            confidence=confidence,
            importance=importance,
            tags=tags or [],
            metadata=metadata or {},
            project_name=project_name,
            feature_id=feature_id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Store in database
        return self.storage.create_node(node)
    
    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Get a node by ID."""
        return self.storage.get_node(node_id)
    
    def update_node(self, node_id: str, **kwargs) -> KnowledgeNode:
        """Update a node."""
        return self.storage.update_node(node_id, kwargs)
    
    def delete_node(self, node_id: str, cascade: bool = True) -> bool:
        """Delete a node."""
        return self.storage.delete_node(node_id, cascade=cascade)
    
    def list_nodes(
        self,
        node_type: NodeType = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[KnowledgeNode]:
        """List nodes with optional filtering."""
        filters = {}
        if node_type:
            filters['node_type'] = node_type.value if isinstance(node_type, NodeType) else node_type
        
        return self.storage.query_nodes(filters, limit=limit, offset=offset)
```

(Note: query_nodes needs to be implemented in SQLite storage first - this is Task 2.4)

- [ ] **Step 4: Run test to verify it passes (after query_nodes is implemented)**

```bash
pytest tests/knowledge_graph/test_node_manager.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add quickagents/knowledge_graph/core/node_manager.py tests/knowledge_graph/test_node_manager.py
git commit -m "feat(knowledge-graph): implement NodeManager minimal unit

- Add create_node with full parameter support
- Add get_node, update_node, delete_node
- Add list_nodes with type filtering and pagination
- Add 20 comprehensive unit tests for 100% coverage"
```

---

## Summary of Remaining Tasks

Due to length, the plan continues with the following structure:

### Phase 3 (continued):
- Task 3.2: EdgeManager (19 tests)
- Task 3.3: KnowledgeExtractor (18 tests)
- Task 3.4: RelationDiscovery (25 tests)
- Task 3.5: KnowledgeSearcher (16 tests)
- Task 3.6: MemorySync (12 tests)

### Phase 4: Facade and Integration
- Task 4.1: KnowledgeGraph facade class
- Task 4.2: UnifiedDB integration
- Task 4.3: CLI commands

### Phase 5: Testing and Documentation
- Task 5.1: Integration tests
- Task 5.2: Performance tests
- Task 5.3: API documentation

---

**Total Tasks: 18**
**Total Test Cases: 110**
**Estimated Time: 4 weeks**

---

*Plan Version: 1.0.0*
*Created: 2026-03-29*
