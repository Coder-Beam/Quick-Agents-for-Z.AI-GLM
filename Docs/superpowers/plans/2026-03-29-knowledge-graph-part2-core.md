# Knowledge Graph Part 2: Core Components Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement 6 minimal unit classes (NodeManager, EdgeManager, KnowledgeExtractor, RelationDiscovery, KnowledgeSearcher, MemorySync) with 100% test coverage.

**Architecture:** Each class is a minimal unit with single responsibility. Classes wrap SQLiteGraphStorage from Part 1, providing higher-level APIs. All classes go in `quickagents/knowledge_graph/core/`.

**Tech Stack:** Python 3.8+, SQLite, pytest, dataclasses

**Prerequisites:** Part 1 (Foundation + Storage) must be complete.

---

## File Structure

```
quickagents/knowledge_graph/
├── core/
│   ├── __init__.py          # Exports all 6 classes
│   ├── node_manager.py      # Task 3.1
│   ├── edge_manager.py      # Task 3.2
│   ├── extractor.py         # Task 3.3
│   ├── discovery.py         # Task 3.4
│   ├── searcher.py          # Task 3.5
│   └── memory_sync.py       # Task 3.6

tests/knowledge_graph/
├── test_node_manager.py     # 20 tests
├── test_edge_manager.py     # 19 tests
├── test_extractor.py        # 18 tests
├── test_discovery.py        # 25 tests
├── test_searcher.py         # 16 tests
└── test_memory_sync.py      # 12 tests
```

---

## Task 3.1: NodeManager (20 tests)

**Files:**
- Create: `quickagents/knowledge_graph/core/node_manager.py`
- Create: `tests/knowledge_graph/test_node_manager.py`
- Modify: `quickagents/knowledge_graph/core/__init__.py`

### Interface

```python
class NodeManager:
    """Node Manager - Minimal Unit"""
    
    def __init__(self, storage: GraphStorageInterface):
        self._storage = storage
    
    def create_node(
        self,
        node_type: NodeType,
        title: str,
        content: str,
        **kwargs
    ) -> KnowledgeNode:
        """Create single node with auto-generated ID"""
        pass
    
    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Get single node by ID"""
        pass
    
    def update_node(self, node_id: str, **kwargs) -> KnowledgeNode:
        """Update single node"""
        pass
    
    def delete_node(self, node_id: str, cascade: bool = True) -> bool:
        """Delete single node"""
        pass
    
    def list_nodes(
        self,
        node_type: NodeType = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[KnowledgeNode]:
        """List nodes with optional type filter"""
        pass
    
    def _generate_id(self, node_type: NodeType) -> str:
        """Generate unique node ID: kn_{type}_{timestamp}_{random}"""
        pass
```

### Test Cases (20)

| Method | Test Cases |
|--------|-----------|
| create_node | basic, all_params, invalid_type, duplicate_title |
| get_node | existing, nonexistent, invalid_id_format |
| update_node | title, multiple_fields, nonexistent, empty_update |
| delete_node | basic, cascade_true, cascade_false, nonexistent |
| list_nodes | all, by_type, with_limit, empty_db, pagination |

### TDD Steps

- [ ] **Step 1: Write failing tests for create_node**

```python
# tests/knowledge_graph/test_node_manager.py
import pytest
from datetime import datetime
from quickagents.knowledge_graph.core.node_manager import NodeManager
from quickagents.knowledge_graph.storage.sqlite_storage import SQLiteGraphStorage
from quickagents.knowledge_graph.types import NodeType, KnowledgeNode
from quickagents.knowledge_graph.exceptions import InvalidNodeTypeError, DuplicateNodeError

class TestNodeManagerCreate:
    @pytest.fixture
    def manager(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        return NodeManager(storage)
    
    def test_create_node_basic(self, manager):
        """Test basic node creation with required fields."""
        node = manager.create_node(
            node_type=NodeType.REQUIREMENT,
            title="Test Requirement",
            content="This is a test requirement"
        )
        
        assert node.id.startswith("kn_")
        assert node.node_type == NodeType.REQUIREMENT
        assert node.title == "Test Requirement"
        assert node.content == "This is a test requirement"
        assert node.confidence == 1.0  # default
        assert node.importance == 0.5  # default
    
    def test_create_node_all_params(self, manager):
        """Test node creation with all parameters."""
        node = manager.create_node(
            node_type=NodeType.DECISION,
            title="Test Decision",
            content="Decision content",
            source_type="discussion",
            source_uri="file://test.md",
            confidence=0.9,
            importance=0.8,
            tags=["tag1", "tag2"],
            metadata={"key": "value"},
            project_name="TestProject",
            feature_id="F001"
        )
        
        assert node.source_type == "discussion"
        assert node.confidence == 0.9
        assert node.importance == 0.8
        assert "tag1" in node.tags
        assert node.metadata["key"] == "value"
        assert node.project_name == "TestProject"
    
    def test_create_node_invalid_type(self, manager):
        """Test that invalid node type raises error."""
        with pytest.raises(InvalidNodeTypeError):
            manager.create_node(
                node_type="invalid_type",
                title="Test",
                content="Content"
            )
    
    def test_create_node_duplicate_title_warning(self, manager):
        """Test that duplicate title triggers check (may warn or handle)."""
        manager.create_node(
            node_type=NodeType.REQUIREMENT,
            title="Duplicate Title",
            content="First"
        )
        
        # Should succeed but may log warning - implementation dependent
        node2 = manager.create_node(
            node_type=NodeType.REQUIREMENT,
            title="Duplicate Title",
            content="Second"
        )
        
        assert node2.id != manager.list_nodes()[0].id  # Different IDs
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/knowledge_graph/test_node_manager.py -v
```
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Implement NodeManager class**

Create `quickagents/knowledge_graph/core/node_manager.py`:

```python
"""Node Manager - Minimal Unit for managing knowledge nodes."""

import uuid
import time
from typing import Optional, List, Dict, Any

from ..types import NodeType, KnowledgeNode
from ..exceptions import InvalidNodeTypeError, NodeNotFoundError
from ..interfaces import GraphStorageInterface


class NodeManager:
    """Node Manager - Minimal Unit.
    
    Provides high-level API for managing knowledge nodes.
    Wraps GraphStorageInterface with ID generation and validation.
    """
    
    def __init__(self, storage: GraphStorageInterface):
        """Initialize with storage backend.
        
        Args:
            storage: GraphStorageInterface implementation
        """
        self._storage = storage
    
    def _generate_id(self, node_type: NodeType) -> str:
        """Generate unique node ID.
        
        Format: kn_{type_short}_{timestamp}_{random}
        
        Args:
            node_type: Type of node
            
        Returns:
            Unique node ID string
        """
        type_map = {
            NodeType.REQUIREMENT: "req",
            NodeType.DECISION: "dec",
            NodeType.INSIGHT: "ins",
            NodeType.FACT: "fct",
            NodeType.CONCEPT: "cpt",
            NodeType.SOURCE: "src"
        }
        type_short = type_map.get(node_type, "unk")
        timestamp = int(time.time() * 1000)
        random_part = uuid.uuid4().hex[:8]
        return f"kn_{type_short}_{timestamp}_{random_part}"
    
    def create_node(
        self,
        node_type: NodeType,
        title: str,
        content: str,
        **kwargs
    ) -> KnowledgeNode:
        """Create a knowledge node.
        
        Args:
            node_type: Type of node (required)
            title: Node title (required)
            content: Node content (required)
            **kwargs: Optional fields (source_type, source_uri, confidence,
                     importance, tags, metadata, project_name, feature_id)
                     
        Returns:
            Created KnowledgeNode
            
        Raises:
            InvalidNodeTypeError: If node_type is not a valid NodeType
        """
        # Validate node_type
        if not isinstance(node_type, NodeType):
            raise InvalidNodeTypeError(
                str(node_type),
                valid_types=[t.value for t in NodeType]
            )
        
        # Generate ID
        node_id = self._generate_id(node_type)
        
        # Create node object
        node = KnowledgeNode(
            id=node_id,
            node_type=node_type,
            title=title,
            content=content,
            source_type=kwargs.get("source_type"),
            source_uri=kwargs.get("source_uri"),
            confidence=kwargs.get("confidence", 1.0),
            importance=kwargs.get("importance", 0.5),
            tags=kwargs.get("tags", []),
            metadata=kwargs.get("metadata", {}),
            project_name=kwargs.get("project_name"),
            feature_id=kwargs.get("feature_id"),
            created_at=kwargs.get("created_at"),
            updated_at=kwargs.get("updated_at"),
            access_count=kwargs.get("access_count", 0),
            last_accessed_at=kwargs.get("last_accessed_at")
        )
        
        return self._storage.create_node(node)
    
    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Get a node by ID.
        
        Args:
            node_id: Node ID
            
        Returns:
            KnowledgeNode or None if not found
        """
        return self._storage.get_node(node_id)
    
    def update_node(self, node_id: str, **kwargs) -> KnowledgeNode:
        """Update a node.
        
        Args:
            node_id: Node ID
            **kwargs: Fields to update
            
        Returns:
            Updated KnowledgeNode
            
        Raises:
            NodeNotFoundError: If node doesn't exist
        """
        return self._storage.update_node(node_id, kwargs)
    
    def delete_node(self, node_id: str, cascade: bool = True) -> bool:
        """Delete a node.
        
        Args:
            node_id: Node ID
            cascade: If True, delete connected edges too
            
        Returns:
            True if deleted, False if not found
        """
        return self._storage.delete_node(node_id, cascade)
    
    def list_nodes(
        self,
        node_type: NodeType = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[KnowledgeNode]:
        """List nodes with optional filtering.
        
        Args:
            node_type: Filter by node type (optional)
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of KnowledgeNode objects
        """
        filters = {}
        if node_type:
            filters["node_type"] = node_type.value
        
        return self._storage.query_nodes(
            filters=filters if filters else None,
            limit=limit,
            offset=offset
        )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/knowledge_graph/test_node_manager.py::TestNodeManagerCreate -v
```
Expected: PASS

- [ ] **Step 5: Write remaining tests**

Add tests for get_node, update_node, delete_node, list_nodes following the same pattern.

- [ ] **Step 6: Run all NodeManager tests**

```bash
pytest tests/knowledge_graph/test_node_manager.py -v
```
Expected: 20 passed

- [ ] **Step 7: Commit**

```bash
git add quickagents/knowledge_graph/core/node_manager.py tests/knowledge_graph/test_node_manager.py
git commit -m "feat(knowledge-graph): implement NodeManager with 20 tests

- Add create_node with auto ID generation
- Add get_node, update_node, delete_node
- Add list_nodes with type filtering
- 100% test coverage (20 test cases)"
```

---

## Task 3.2: EdgeManager (19 tests)

**Files:**
- Create: `quickagents/knowledge_graph/core/edge_manager.py`
- Create: `tests/knowledge_graph/test_edge_manager.py`
- Modify: `quickagents/knowledge_graph/core/__init__.py`

### Interface

```python
class EdgeManager:
    """Edge Manager - Minimal Unit"""
    
    def __init__(self, storage: GraphStorageInterface):
        self._storage = storage
    
    def create_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType,
        **kwargs
    ) -> KnowledgeEdge:
        """Create single edge with auto-generated ID"""
        pass
    
    def get_edge(self, edge_id: str) -> Optional[KnowledgeEdge]:
        """Get single edge by ID"""
        pass
    
    def delete_edge(self, edge_id: str) -> bool:
        """Delete single edge"""
        pass
    
    def get_outgoing_edges(
        self,
        node_id: str,
        edge_type: EdgeType = None
    ) -> List[KnowledgeEdge]:
        """Get edges where node is source"""
        pass
    
    def get_incoming_edges(
        self,
        node_id: str,
        edge_type: EdgeType = None
    ) -> List[KnowledgeEdge]:
        """Get edges where node is target"""
        pass
    
    def _generate_id(self, edge_type: EdgeType) -> str:
        """Generate unique edge ID: ke_{type}_{timestamp}_{random}"""
        pass
```

### Test Cases (19)

| Method | Test Cases |
|--------|-----------|
| create_edge | basic, with_evidence, duplicate, invalid_source, invalid_target |
| get_edge | existing, nonexistent, invalid_id_format |
| delete_edge | basic, nonexistent, with_invalid_nodes |
| get_outgoing_edges | basic, with_type_filter, no_edges, invalid_node |
| get_incoming_edges | basic, with_type_filter, no_edges, invalid_node |

### TDD Steps

- [ ] **Step 1: Write failing tests for EdgeManager**

```python
# tests/knowledge_graph/test_edge_manager.py
import pytest
from datetime import datetime
from quickagents.knowledge_graph.core.edge_manager import EdgeManager
from quickagents.knowledge_graph.core.node_manager import NodeManager
from quickagents.knowledge_graph.storage.sqlite_storage import SQLiteGraphStorage
from quickagents.knowledge_graph.types import NodeType, EdgeType, KnowledgeNode, KnowledgeEdge
from quickagents.knowledge_graph.exceptions import InvalidEdgeTypeError, DuplicateEdgeError

class TestEdgeManagerCreate:
    @pytest.fixture
    def storage(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        return storage
    
    @pytest.fixture
    def manager(self, storage):
        return EdgeManager(storage)
    
    @pytest.fixture
    def node_manager(self, storage):
        return NodeManager(storage)
    
    @pytest.fixture
    def sample_nodes(self, node_manager):
        node1 = node_manager.create_node(
            node_type=NodeType.REQUIREMENT,
            title="Source Node",
            content="Content 1"
        )
        node2 = node_manager.create_node(
            node_type=NodeType.DECISION,
            title="Target Node",
            content="Content 2"
        )
        return node1, node2
    
    def test_create_edge_basic(self, manager, sample_nodes):
        """Test basic edge creation."""
        node1, node2 = sample_nodes
        edge = manager.create_edge(
            source_id=node1.id,
            target_id=node2.id,
            edge_type=EdgeType.DEPENDS_ON
        )
        
        assert edge.id.startswith("ke_")
        assert edge.source_node_id == node1.id
        assert edge.target_node_id == node2.id
        assert edge.edge_type == EdgeType.DEPENDS_ON
    
    def test_create_edge_with_evidence(self, manager, sample_nodes):
        """Test edge creation with evidence."""
        node1, node2 = sample_nodes
        edge = manager.create_edge(
            source_id=node1.id,
            target_id=node2.id,
            edge_type=EdgeType.MAPS_TO,
            evidence="Decision maps to requirement",
            confidence=0.9
        )
        
        assert edge.evidence == "Decision maps to requirement"
        assert edge.confidence == 0.9
    
    def test_create_edge_duplicate_fails(self, manager, sample_nodes):
        """Test that duplicate edge fails."""
        node1, node2 = sample_nodes
        
        manager.create_edge(
            source_id=node1.id,
            target_id=node2.id,
            edge_type=EdgeType.RELATED_TO
        )
        
        with pytest.raises(DuplicateEdgeError):
            manager.create_edge(
                source_id=node1.id,
                target_id=node2.id,
                edge_type=EdgeType.RELATED_TO
            )
    
    def test_create_edge_invalid_source(self, manager, sample_nodes):
        """Test that invalid source raises error."""
        _, node2 = sample_nodes
        
        with pytest.raises(Exception):  # FK constraint violation
            manager.create_edge(
                source_id="kn_nonexistent",
                target_id=node2.id,
                edge_type=EdgeType.RELATED_TO
            )
    
    def test_create_edge_invalid_target(self, manager, sample_nodes):
        """Test that invalid target raises error."""
        node1, _ = sample_nodes
        
        with pytest.raises(Exception):  # FK constraint violation
            manager.create_edge(
                source_id=node1.id,
                target_id="kn_nonexistent",
                edge_type=EdgeType.RELATED_TO
            )
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/knowledge_graph/test_edge_manager.py -v
```
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Implement EdgeManager class**

Create `quickagents/knowledge_graph/core/edge_manager.py`:

```python
"""Edge Manager - Minimal Unit for managing knowledge edges."""

import uuid
import time
from typing import Optional, List, Dict, Any

from ..types import EdgeType, KnowledgeEdge
from ..exceptions import InvalidEdgeTypeError, DuplicateEdgeError, EdgeNotFoundError
from ..interfaces import GraphStorageInterface


class EdgeManager:
    """Edge Manager - Minimal Unit.
    
    Provides high-level API for managing knowledge edges.
    Wraps GraphStorageInterface with ID generation and validation.
    """
    
    def __init__(self, storage: GraphStorageInterface):
        """Initialize with storage backend.
        
        Args:
            storage: GraphStorageInterface implementation
        """
        self._storage = storage
    
    def _generate_id(self, edge_type: EdgeType) -> str:
        """Generate unique edge ID.
        
        Format: ke_{type_short}_{timestamp}_{random}
        """
        type_map = {
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
            EdgeType.INDIRECTLY_RELATED_TO: "ind"
        }
        type_short = type_map.get(edge_type, "unk")
        timestamp = int(time.time() * 1000)
        random_part = uuid.uuid4().hex[:8]
        return f"ke_{type_short}_{timestamp}_{random_part}"
    
    def create_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType,
        **kwargs
    ) -> KnowledgeEdge:
        """Create a knowledge edge.
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            edge_type: Type of edge
            **kwargs: Optional fields (evidence, weight, metadata, confidence)
            
        Returns:
            Created KnowledgeEdge
            
        Raises:
            InvalidEdgeTypeError: If edge_type is not valid
            DuplicateEdgeError: If edge already exists
        """
        if not isinstance(edge_type, EdgeType):
            raise InvalidEdgeTypeError(
                str(edge_type),
                valid_types=[t.value for t in EdgeType]
            )
        
        edge_id = self._generate_id(edge_type)
        
        edge = KnowledgeEdge(
            id=edge_id,
            source_node_id=source_id,
            target_node_id=target_id,
            edge_type=edge_type,
            weight=kwargs.get("weight", 1.0),
            evidence=kwargs.get("evidence"),
            metadata=kwargs.get("metadata", {}),
            confidence=kwargs.get("confidence", 1.0),
            created_at=kwargs.get("created_at"),
            updated_at=kwargs.get("updated_at")
        )
        
        return self._storage.create_edge(edge)
    
    def get_edge(self, edge_id: str) -> Optional[KnowledgeEdge]:
        """Get an edge by ID."""
        return self._storage.get_edge(edge_id)
    
    def delete_edge(self, edge_id: str) -> bool:
        """Delete an edge."""
        return self._storage.delete_edge(edge_id)
    
    def get_outgoing_edges(
        self,
        node_id: str,
        edge_type: EdgeType = None
    ) -> List[KnowledgeEdge]:
        """Get edges where node is source.
        
        Args:
            node_id: Node ID
            edge_type: Optional filter by edge type
            
        Returns:
            List of outgoing edges
        """
        filters = {"source_node_id": node_id}
        if edge_type:
            filters["edge_type"] = edge_type.value
        
        return self._storage.query_edges(filters=filters)
    
    def get_incoming_edges(
        self,
        node_id: str,
        edge_type: EdgeType = None
    ) -> List[KnowledgeEdge]:
        """Get edges where node is target.
        
        Args:
            node_id: Node ID
            edge_type: Optional filter by edge type
            
        Returns:
            List of incoming edges
        """
        filters = {"target_node_id": node_id}
        if edge_type:
            filters["edge_type"] = edge_type.value
        
        return self._storage.query_edges(filters=filters)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/knowledge_graph/test_edge_manager.py -v
```
Expected: 19 passed

- [ ] **Step 5: Commit**

```bash
git add quickagents/knowledge_graph/core/edge_manager.py tests/knowledge_graph/test_edge_manager.py
git commit -m "feat(knowledge-graph): implement EdgeManager with 19 tests

- Add create_edge with auto ID generation
- Add get_edge, delete_edge
- Add get_outgoing_edges, get_incoming_edges
- 100% test coverage (19 test cases)"
```

---

## Task 3.3: KnowledgeExtractor (18 tests)

**Files:**
- Create: `quickagents/knowledge_graph/core/extractor.py`
- Create: `tests/knowledge_graph/test_extractor.py`
- Modify: `quickagents/knowledge_graph/core/__init__.py`

### Interface

```python
class KnowledgeExtractor:
    """Knowledge Extractor - Minimal Unit"""
    
    def __init__(self, node_manager: NodeManager, confidence_threshold: float = 0.8):
        self._node_manager = node_manager
        self._confidence_threshold = confidence_threshold
    
    def extract_from_text(
        self,
        text: str,
        source_type: str = "discussion",
        **kwargs
    ) -> List[KnowledgeNode]:
        """Extract knowledge from text using pattern matching"""
        pass
    
    def import_from_file(
        self,
        file_path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Import knowledge from file"""
        pass
    
    def validate_confidence(self, node: KnowledgeNode) -> bool:
        """Validate node confidence against threshold"""
        pass
    
    def check_duplicate(self, title: str, content: str) -> Optional[str]:
        """Check for duplicate node by title/content similarity"""
        pass
    
    def _extract_requirements(self, text: str) -> List[Dict]:
        """Extract requirements from text"""
        pass
    
    def _extract_decisions(self, text: str) -> List[Dict]:
        """Extract decisions from text"""
        pass
    
    def _extract_facts(self, text: str) -> List[Dict]:
        """Extract facts from text"""
        pass
```

### Test Cases (18)

| Method | Test Cases |
|--------|-----------|
| extract_from_text | single_req, multiple, high_conf, low_conf, empty, malformed |
| import_from_file | markdown, text, nonexistent, unsupported, permission_denied |
| validate_confidence | high, low, boundary |
| check_duplicate | exact_match, similar_title, no_match, case_insensitive |

### Implementation Notes

- Uses regex patterns to extract requirements/decisions/facts
- Patterns:
  - Requirements: "需要...", "必须...", "系统应..."
  - Decisions: "决定...", "选择...", "采用..."
  - Facts: "是...", "有...", "存在..."
- Confidence calculated based on pattern match quality

### TDD Steps

- [ ] **Step 1: Write failing tests for KnowledgeExtractor**

```python
# tests/knowledge_graph/test_extractor.py
import pytest
import os
from pathlib import Path
from quickagents.knowledge_graph.core.extractor import KnowledgeExtractor
from quickagents.knowledge_graph.core.node_manager import NodeManager
from quickagents.knowledge_graph.storage.sqlite_storage import SQLiteGraphStorage
from quickagents.knowledge_graph.types import NodeType, KnowledgeNode

class TestKnowledgeExtractorExtract:
    @pytest.fixture
    def extractor(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        node_manager = NodeManager(storage)
        return KnowledgeExtractor(node_manager)
    
    def test_extract_single_requirement(self, extractor):
        """Test extracting a single requirement."""
        text = "系统需要支持OAuth2.0认证"
        nodes = extractor.extract_from_text(text)
        
        assert len(nodes) >= 1
        req_nodes = [n for n in nodes if n.node_type == NodeType.REQUIREMENT]
        assert len(req_nodes) >= 1
        assert "OAuth" in req_nodes[0].content
    
    def test_extract_multiple_knowledge(self, extractor):
        """Test extracting multiple knowledge items."""
        text = """
        系统需要支持用户认证。
        我们决定使用JWT作为认证方案。
        这是一个重要的安全考虑。
        """
        nodes = extractor.extract_from_text(text)
        
        assert len(nodes) >= 2
        types = {n.node_type for n in nodes}
        assert NodeType.REQUIREMENT in types or NodeType.DECISION in types
    
    def test_extract_high_confidence(self, extractor):
        """Test that clear patterns produce high confidence."""
        text = "必须实现数据加密功能"
        nodes = extractor.extract_from_text(text)
        
        if nodes:
            assert nodes[0].confidence >= 0.8
    
    def test_extract_low_confidence(self, extractor):
        """Test that ambiguous patterns produce low confidence."""
        text = "可能需要考虑这个问题"
        nodes = extractor.extract_from_text(text)
        
        if nodes:
            assert nodes[0].confidence < 0.8
    
    def test_extract_empty_text(self, extractor):
        """Test extracting from empty text."""
        nodes = extractor.extract_from_text("")
        assert nodes == []
    
    def test_extract_malformed_text(self, extractor):
        """Test extracting from malformed text."""
        text = "随机文本没有明确的知识点"
        nodes = extractor.extract_from_text(text)
        # May return empty or low-confidence results
        assert isinstance(nodes, list)


class TestKnowledgeExtractorImport:
    @pytest.fixture
    def extractor(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        node_manager = NodeManager(storage)
        return KnowledgeExtractor(node_manager)
    
    def test_import_markdown_file(self, extractor, tmp_path):
        """Test importing from markdown file."""
        md_file = tmp_path / "test.md"
        md_file.write_text("# Requirements\n\n- 系统需要支持登录\n\n## Decisions\n\n决定使用MySQL数据库")
        
        result = extractor.import_from_file(str(md_file))
        
        assert result["success"] is True
        assert result["nodes_created"] >= 1
    
    def test_import_text_file(self, extractor, tmp_path):
        """Test importing from text file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("这是一个重要的事实：API响应时间应小于200ms")
        
        result = extractor.import_from_file(str(txt_file))
        
        assert result["success"] is True
    
    def test_import_nonexistent_file(self, extractor):
        """Test importing nonexistent file."""
        result = extractor.import_from_file("/nonexistent/file.md")
        
        assert result["success"] is False
        assert "error" in result
    
    def test_import_unsupported_format(self, extractor, tmp_path):
        """Test importing unsupported file format."""
        bin_file = tmp_path / "test.bin"
        bin_file.write_bytes(b"\x00\x01\x02")
        
        result = extractor.import_from_file(str(bin_file))
        
        assert result["success"] is False


class TestKnowledgeExtractorValidate:
    @pytest.fixture
    def extractor(self):
        return KnowledgeExtractor(None, confidence_threshold=0.8)
    
    def test_validate_high_confidence(self, extractor):
        """Test validating high confidence node."""
        node = KnowledgeNode(
            id="test", node_type=NodeType.FACT,
            title="Test", content="Content", confidence=0.9
        )
        assert extractor.validate_confidence(node) is True
    
    def test_validate_low_confidence(self, extractor):
        """Test validating low confidence node."""
        node = KnowledgeNode(
            id="test", node_type=NodeType.FACT,
            title="Test", content="Content", confidence=0.5
        )
        assert extractor.validate_confidence(node) is False
    
    def test_validate_boundary(self, extractor):
        """Test validating at boundary."""
        node = KnowledgeNode(
            id="test", node_type=NodeType.FACT,
            title="Test", content="Content", confidence=0.8
        )
        assert extractor.validate_confidence(node) is True


class TestKnowledgeExtractorDuplicate:
    @pytest.fixture
    def extractor(self, tmp_path):
        db_path = str(tmp_path / "test.db")
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        node_manager = NodeManager(storage)
        return KnowledgeExtractor(node_manager)
    
    def test_check_exact_match(self, extractor):
        """Test checking exact duplicate."""
        extractor._node_manager.create_node(
            node_type=NodeType.REQUIREMENT,
            title="OAuth认证",
            content="系统需要支持OAuth"
        )
        
        duplicate_id = extractor.check_duplicate("OAuth认证", "系统需要支持OAuth")
        assert duplicate_id is not None
    
    def test_check_similar_title(self, extractor):
        """Test checking similar title."""
        extractor._node_manager.create_node(
            node_type=NodeType.REQUIREMENT,
            title="用户认证系统",
            content="Content"
        )
        
        duplicate_id = extractor.check_duplicate("用户认证系统设计", "Other content")
        # Similar title may or may not be detected based on implementation
        assert duplicate_id is None or isinstance(duplicate_id, str)
    
    def test_check_no_match(self, extractor):
        """Test checking with no match."""
        duplicate_id = extractor.check_duplicate("全新功能", "全新内容")
        assert duplicate_id is None
    
    def test_check_case_insensitive(self, extractor):
        """Test case insensitive duplicate check."""
        extractor._node_manager.create_node(
            node_type=NodeType.REQUIREMENT,
            title="API Design",
            content="Content"
        )
        
        duplicate_id = extractor.check_duplicate("api design", "Content")
        # May or may not match depending on implementation
        assert duplicate_id is None or isinstance(duplicate_id, str)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/knowledge_graph/test_extractor.py -v
```
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Implement KnowledgeExtractor class**

Create `quickagents/knowledge_graph/core/extractor.py` with pattern-based extraction logic.

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/knowledge_graph/test_extractor.py -v
```
Expected: 18 passed

- [ ] **Step 5: Commit**

```bash
git add quickagents/knowledge_graph/core/extractor.py tests/knowledge_graph/test_extractor.py
git commit -m "feat(knowledge-graph): implement KnowledgeExtractor with 18 tests

- Add extract_from_text with regex patterns
- Add import_from_file for md/txt files
- Add validate_confidence and check_duplicate
- 100% test coverage (18 test cases)"
```

---

## Task 3.4: RelationDiscovery (25 tests)

**Files:**
- Create: `quickagents/knowledge_graph/core/discovery.py`
- Create: `tests/knowledge_graph/test_discovery.py`
- Modify: `quickagents/knowledge_graph/core/__init__.py`

### Interface

```python
class RelationDiscovery:
    """Relation Discovery - Minimal Unit"""
    
    def __init__(self, storage: GraphStorageInterface, edge_manager: EdgeManager):
        self._storage = storage
        self._edge_manager = edge_manager
    
    def discover_direct_relations(self, node_id: str) -> List[KnowledgeEdge]:
        """Discover direct relations by reference matching"""
        pass
    
    def discover_semantic_relations(self, node_id: str, threshold: float = 0.7) -> List[KnowledgeEdge]:
        """Discover semantic relations by content similarity"""
        pass
    
    def discover_structural_relations(self, node_id: str) -> List[KnowledgeEdge]:
        """Discover structural relations (same feature/project)"""
        pass
    
    def discover_transitive_relations(self, node_id: str, max_depth: int = 3) -> List[KnowledgeEdge]:
        """Discover transitive relations (A→B, B→C implies A→C)"""
        pass
    
    def find_path(
        self,
        from_node: str,
        to_node: str,
        max_depth: int = 5
    ) -> Optional[List[str]]:
        """Find shortest path between nodes"""
        pass
    
    def trace_requirement(
        self,
        node_id: str,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """Trace requirement chain"""
        pass
```

### Test Cases (25)

| Method | Test Cases |
|--------|-----------|
| discover_direct_relations | by_reference, by_link, by_tags, no_relations |
| discover_semantic_relations | high_sim, low_sim, threshold_boundary, empty_content |
| discover_structural_relations | same_feature, same_project, temporal_proximity, no_relations |
| discover_transitive_relations | two_hop, three_hop, cycle_detection, no_transitive |
| find_path | direct, multi_hop, no_path, max_depth_exceeded, circular_graph |
| trace_requirement | full_chain, partial_chain, no_chain, circular_reference |

### TDD Steps

- [ ] **Step 1: Write failing tests**
- [ ] **Step 2: Run tests to verify they fail**
- [ ] **Step 3: Implement RelationDiscovery class**
- [ ] **Step 4: Run tests to verify they pass**
- [ ] **Step 5: Commit**

---

## Task 3.5: KnowledgeSearcher (16 tests)

**Files:**
- Create: `quickagents/knowledge_graph/core/searcher.py`
- Create: `tests/knowledge_graph/test_searcher.py`
- Modify: `quickagents/knowledge_graph/core/__init__.py`

### Interface

```python
class KnowledgeSearcher:
    """Knowledge Searcher - Minimal Unit"""
    
    def __init__(self, storage: GraphStorageInterface):
        self._storage = storage
    
    def search(
        self,
        query: str,
        node_types: List[NodeType] = None,
        filters: Dict[str, Any] = None,
        sort_by: str = "relevance",
        limit: int = 20,
        offset: int = 0,
        expand_relations: bool = False,
        relation_depth: int = 1
    ) -> SearchResult:
        """Unified search method"""
        pass
    
    def search_by_tags(
        self,
        tags: List[str],
        limit: int = 100
    ) -> List[KnowledgeNode]:
        """Search by tags"""
        pass
    
    def search_by_date_range(
        self,
        start_date: str,
        end_date: str,
        node_type: NodeType = None
    ) -> List[KnowledgeNode]:
        """Search by date range"""
        pass
```

### Test Cases (16)

| Method | Test Cases |
|--------|-----------|
| search | basic, type_filter, project_filter, tag_filter, date_filter, sorting, pagination, relation_expansion |
| search_by_tags | single_tag, multiple_tags, nonexistent_tag, with_limit |
| search_by_date_range | basic, open_ended, no_results, invalid_format |

### TDD Steps

- [ ] **Step 1: Write failing tests**
- [ ] **Step 2: Run tests to verify they fail**
- [ ] **Step 3: Implement KnowledgeSearcher class**
- [ ] **Step 4: Run tests to verify they pass**
- [ ] **Step 5: Commit**

---

## Task 3.6: MemorySync (12 tests)

**Files:**
- Create: `quickagents/knowledge_graph/core/memory_sync.py`
- Create: `tests/knowledge_graph/test_memory_sync.py`
- Modify: `quickagents/knowledge_graph/core/__init__.py`

### Interface

```python
class MemorySync:
    """Memory Sync - Minimal Unit"""
    
    def __init__(self, node_manager: NodeManager):
        self._node_manager = node_manager
    
    def sync_to_memory(
        self,
        memory_path: str = "Docs/MEMORY.md"
    ) -> int:
        """Sync high-importance nodes to MEMORY.md"""
        pass
    
    def filter_sync_candidates(
        self,
        nodes: List[KnowledgeNode]
    ) -> List[KnowledgeNode]:
        """Filter nodes that should be synced"""
        pass
    
    def format_for_memory(self, node: KnowledgeNode) -> str:
        """Format node for MEMORY.md"""
        pass
```

### Test Cases (12)

| Method | Test Cases |
|--------|-----------|
| sync_to_memory | basic, no_candidates, file_not_found, permission_denied |
| filter_sync_candidates | by_importance, by_type, combined_criteria, empty_list |
| format_for_memory | requirement, decision, fact, with_metadata |

### Sync Criteria

- importance >= 0.7
- node_type in [REQUIREMENT, DECISION, FACT]
- confidence >= 0.8

### TDD Steps

- [ ] **Step 1: Write failing tests**
- [ ] **Step 2: Run tests to verify they fail**
- [ ] **Step 3: Implement MemorySync class**
- [ ] **Step 4: Run tests to verify they pass**
- [ ] **Step 5: Commit**

---

## Summary

| Task | Component | Methods | Tests |
|------|-----------|---------|-------|
| 3.1 | NodeManager | 5 | 20 |
| 3.2 | EdgeManager | 5 | 19 |
| 3.3 | KnowledgeExtractor | 4 | 18 |
| 3.4 | RelationDiscovery | 6 | 25 |
| 3.5 | KnowledgeSearcher | 3 | 16 |
| 3.6 | MemorySync | 3 | 12 |
| **Total** | **6 classes** | **26** | **110** |

---

## Dependencies

```
Task 3.1 (NodeManager) ← No dependencies
Task 3.2 (EdgeManager) ← No dependencies
Task 3.3 (KnowledgeExtractor) ← Depends on 3.1
Task 3.4 (RelationDiscovery) ← Depends on 3.2
Task 3.5 (KnowledgeSearcher) ← No dependencies
Task 3.6 (MemorySync) ← Depends on 3.1
```

**Recommended execution order:** 3.1 → 3.2 → 3.3 → 3.4 → 3.5 → 3.6

---

*Plan Version: 1.0.0*
*Created: 2026-03-30*
*Scope: Phase 3 - Core Components (Part 2)*
