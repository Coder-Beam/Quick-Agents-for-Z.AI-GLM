# Knowledge Graph Part 3: Integration Layer (Facade + UnifiedDB + CLI)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the KnowledgeGraph facade class, integrate with UnifiedDB, add `qa knowledge` CLI commands, and finalize the feature with documentation.

**Architecture:** Facade pattern unifying 6 minimal-unit components from Part 2. Lazy-loaded `knowledge` property on UnifiedDB. CLI subcommand following existing argparse pattern in `quickagents/cli/main.py`.

**Tech Stack:** Python 3.8+, SQLite, pytest, argparse

**Prerequisites:** Part 1 (Foundation + Storage) and Part 2 (Core Components) are complete. All 172 existing tests pass.

---

## Current State Summary

### Implemented (Parts 1-2)

| Layer | Files | Status |
|-------|-------|--------|
| Types | `knowledge_graph/types.py` | 6 NodeTypes, 11 EdgeTypes, KnowledgeNode, KnowledgeEdge, SearchResult |
| Exceptions | `knowledge_graph/exceptions.py` | 10 exception classes |
| Interfaces | `knowledge_graph/interfaces.py` | GraphStorageInterface (13 methods), VectorSearchInterface (6 methods) |
| Storage | `knowledge_graph/storage/sqlite_storage.py` | SQLiteGraphStorage with FTS5, triggers, indexes |
| Core | `knowledge_graph/core/node_manager.py` | NodeManager (5 methods, auto-ID) |
| Core | `knowledge_graph/core/edge_manager.py` | EdgeManager (5 methods, auto-ID) |
| Core | `knowledge_graph/core/extractor.py` | KnowledgeExtractor (4 methods, pattern matching) |
| Core | `knowledge_graph/core/discovery.py` | RelationDiscovery (6 methods, 4 strategies) |
| Core | `knowledge_graph/core/searcher.py` | KnowledgeSearcher (3 methods, FTS5) |
| Core | `knowledge_graph/core/memory_sync.py` | MemorySync (3 methods) |

### Key Implementation Details

1. **Constructor patterns**: Core classes use dependency injection:
   - `NodeManager(storage: GraphStorageInterface)`
   - `EdgeManager(storage: GraphStorageInterface)`
   - `KnowledgeExtractor(node_manager: NodeManager, confidence_threshold: float = 0.8)`
   - `RelationDiscovery(storage: GraphStorageInterface, edge_manager: EdgeManager)`
   - `KnowledgeSearcher(storage: GraphStorageInterface)`
   - `MemorySync(node_manager: NodeManager)`

2. **UnifiedDB** (`quickagents/core/unified_db.py`):
   - Constructor: `UnifiedDB(db_path: str = '.quickagents/unified.db')`
   - Has `_get_connection()` context manager
   - Already exports `get_unified_db()` global singleton
   - Has `get_stats()` method returning dict
   - **No** `knowledge` property yet (Part 3 adds this)

3. **CLI** (`quickagents/cli/main.py`):
   - Uses `argparse.ArgumentParser` with `subparsers`
   - Pattern: `subparsers.add_parser('command')` → `add_argument()` → `set_defaults(func=cmd_handler)`
   - Handler functions defined as `def cmd_xxx(args)` at module level
   - Entry: `main()` function with `parser.parse_args()`

4. **Package exports** (`quickagents/__init__.py`):
   - Exports core modules but **not** knowledge_graph yet
   - `knowledge_graph/__init__.py` has comment: `# Note: KnowledgeGraph will be added in Part 3`

5. **Test patterns** (`tests/knowledge_graph/`):
   - 9 test files, 172 tests total
   - Fixtures use `tempfile.NamedTemporaryFile(suffix='.db', delete=False)` + cleanup in `os.unlink`
   - Tests organized by class method groups (e.g., `TestNodeManagerCreate`, `TestNodeManagerGet`)

### Spec Reference (Sections 6.2-6.5)

**Spec 6.2 - KnowledgeGraph Facade:**
```python
class KnowledgeGraph:
    def __init__(self, db_path: str = '.quickagents/unified.db'):
        self.storage = SQLiteGraphStorage(db_path)
        self.nodes = NodeManager(self.storage)
        self.edges = EdgeManager(self.storage)
        self.extractor = KnowledgeExtractor(self.nodes)
        self.discovery = RelationDiscovery(self.storage, self.edges)
        self.searcher = KnowledgeSearcher(self.storage)
        self.sync = MemorySync(self.nodes)
    
    # Delegate methods
    def create_node(self, *args, **kwargs): return self.nodes.create_node(...)
    def search(self, *args, **kwargs): return self.searcher.search(...)
    # ... other delegate methods
```

**Spec 6.5 - UnifiedDB Integration:**
```python
class UnifiedDB:
    @property
    def knowledge(self) -> KnowledgeGraph:
        if self._knowledge_graph is None:
            from quickagents.knowledge_graph import KnowledgeGraph
            self._knowledge_graph = KnowledgeGraph(self.db_path)
        return self._knowledge_graph
```

**Spec 6.4 - CLI Commands (subset for Part 3):**
```bash
qa knowledge create-node --type TYPE --title TITLE --content CONTENT [OPTIONS]
qa knowledge get-node NODE_ID [--expand]
qa knowledge update-node NODE_ID [OPTIONS]
qa knowledge delete-node NODE_ID [--cascade]
qa knowledge list-nodes --type TYPE [--project NAME] [--limit N]
qa knowledge create-edge --from SOURCE --to TARGET --type TYPE [OPTIONS]
qa knowledge delete-edge EDGE_ID
qa knowledge show-relations NODE_ID [--direction in|out|both]
qa knowledge discover NODE_ID [--strategies direct,semantic,structural]
qa knowledge search QUERY [--type TYPE] [--limit N]
qa knowledge sync [--memory-path PATH]
qa knowledge stats
qa knowledge find-path --from NODE_ID --to NODE_ID [--max-depth N]
qa knowledge trace-requirement NODE_ID
```

---

## File Structure

```
quickagents/knowledge_graph/
├── __init__.py              # MODIFY: add KnowledgeGraph export
├── knowledge_graph.py       # NEW: Facade class

quickagents/core/
├── unified_db.py            # MODIFY: add knowledge property

quickagents/cli/
├── main.py                  # MODIFY: add knowledge subcommand

quickagents/__init__.py      # MODIFY: add KnowledgeGraph exports

tests/knowledge_graph/
├── test_knowledge_graph_facade.py   # NEW: ~15 tests
├── test_unified_db_knowledge.py     # NEW: ~15 tests

tests/integration/
├── test_knowledge_graph_cli.py      # NEW: ~12 CLI tests
```

---

## Task 4.1: KnowledgeGraph Facade Class (~15 tests)

**Files:**
- Create: `quickagents/knowledge_graph/knowledge_graph.py`
- Create: `tests/knowledge_graph/test_knowledge_graph_facade.py`
- Modify: `quickagents/knowledge_graph/__init__.py`

### Interface

```python
class KnowledgeGraph:
    """
    Knowledge Graph Manager - Facade Pattern
    
    Combines all minimal units, provides unified interface.
    Single entry point for all knowledge graph operations.
    """
    
    def __init__(self, db_path: str = '.quickagents/unified.db'):
        """
        Initialize KnowledgeGraph with all sub-components.
        
        Creates SQLiteGraphStorage, initializes schema, and
        wires up all 6 core component instances.
        """
        pass
    
    # --- Node Operations (delegate to NodeManager) ---
    
    def create_node(self, node_type: NodeType, title: str, content: str, **kwargs) -> KnowledgeNode:
        """Create a knowledge node."""
        pass
    
    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Get a node by ID."""
        pass
    
    def update_node(self, node_id: str, **kwargs) -> KnowledgeNode:
        """Update a node."""
        pass
    
    def delete_node(self, node_id: str, cascade: bool = True) -> bool:
        """Delete a node."""
        pass
    
    def list_nodes(self, node_type: NodeType = None, limit: int = 100, offset: int = 0) -> List[KnowledgeNode]:
        """List nodes with optional filter."""
        pass
    
    # --- Edge Operations (delegate to EdgeManager) ---
    
    def create_edge(self, source_id: str, target_id: str, edge_type: EdgeType, **kwargs) -> KnowledgeEdge:
        """Create an edge between nodes."""
        pass
    
    def get_edge(self, edge_id: str) -> Optional[KnowledgeEdge]:
        """Get an edge by ID."""
        pass
    
    def delete_edge(self, edge_id: str) -> bool:
        """Delete an edge."""
        pass
    
    def get_outgoing_edges(self, node_id: str, edge_type: EdgeType = None) -> List[KnowledgeEdge]:
        """Get outgoing edges for a node."""
        pass
    
    def get_incoming_edges(self, node_id: str, edge_type: EdgeType = None) -> List[KnowledgeEdge]:
        """Get incoming edges for a node."""
        pass
    
    # --- Search Operations (delegate to KnowledgeSearcher) ---
    
    def search(self, query: str, **kwargs) -> SearchResult:
        """Search knowledge nodes."""
        pass
    
    def search_by_tags(self, tags: List[str], limit: int = 100) -> List[KnowledgeNode]:
        """Search by tags."""
        pass
    
    # --- Discovery Operations (delegate to RelationDiscovery) ---
    
    def discover(self, node_id: str, strategies: List[str] = None) -> List[KnowledgeEdge]:
        """
        Discover relations using specified strategies.
        
        Args:
            node_id: Node ID to discover relations for
            strategies: List of strategy names ('direct', 'semantic', 'structural', 'transitive')
                        Default: ['direct', 'semantic']
        """
        pass
    
    def find_path(self, from_node: str, to_node: str, max_depth: int = 5) -> Optional[List[str]]:
        """Find path between two nodes."""
        pass
    
    def trace_requirement(self, node_id: str, max_depth: int = 3) -> Dict[str, Any]:
        """Trace requirement chain."""
        pass
    
    # --- Extraction Operations (delegate to KnowledgeExtractor) ---
    
    def extract_from_text(self, text: str, **kwargs) -> List[KnowledgeNode]:
        """Extract knowledge from text."""
        pass
    
    def import_from_file(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Import knowledge from file."""
        pass
    
    # --- Sync Operations (delegate to MemorySync) ---
    
    def sync_to_memory(self, memory_path: str = "Docs/MEMORY.md") -> int:
        """Sync high-importance nodes to MEMORY.md."""
        pass
    
    # --- Stats ---
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics."""
        pass
    
    def show_relations(self, node_id: str, direction: str = "both") -> Dict[str, List[KnowledgeEdge]]:
        """
        Show all relations for a node.
        
        Args:
            node_id: Node ID
            direction: 'in', 'out', or 'both'
            
        Returns:
            Dict with 'incoming' and/or 'outgoing' edge lists
        """
        pass
```

### Test Cases (15)

| Method | Test Cases |
|--------|-----------|
| `__init__` | initializes all components, creates tables |
| `create_node` + `get_node` | round-trip create and retrieve |
| `create_edge` + `get_edge` | round-trip edge creation |
| `search` | search returns matching nodes |
| `discover` | discover with default strategies |
| `discover` | discover with explicit strategies |
| `find_path` | find path between connected nodes |
| `trace_requirement` | trace requirement chain |
| `extract_from_text` | extract knowledge from text |
| `import_from_file` | import from markdown file |
| `sync_to_memory` | sync high-importance nodes |
| `show_relations` | show both directions |
| `get_stats` | returns stats dict |
| `list_nodes` | list with type filter |
| `update_node` + `delete_node` | update and delete cycle |

### TDD Steps

- [ ] **Step 1: Write failing tests for KnowledgeGraph facade**

```python
# tests/knowledge_graph/test_knowledge_graph_facade.py
import pytest
import os
import tempfile
from quickagents.knowledge_graph.knowledge_graph import KnowledgeGraph
from quickagents.knowledge_graph.types import NodeType, EdgeType


class TestKnowledgeGraphInit:
    @pytest.fixture
    def kg(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        kg = KnowledgeGraph(db_path)
        yield kg
        os.unlink(db_path)
    
    def test_init_creates_components(self, kg):
        """Test that init creates all sub-components."""
        assert kg.storage is not None
        assert kg.nodes is not None
        assert kg.edges is not None
        assert kg.extractor is not None
        assert kg.discovery is not None
        assert kg.searcher is not None
        assert kg.sync is not None
    
    def test_init_creates_tables(self, kg):
        """Test that init creates database tables."""
        stats = kg.get_stats()
        assert 'total_nodes' in stats
        assert 'total_edges' in stats


class TestKnowledgeGraphNodeOps:
    @pytest.fixture
    def kg(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        kg = KnowledgeGraph(db_path)
        yield kg
        os.unlink(db_path)
    
    def test_create_and_get_node(self, kg):
        """Test round-trip create and retrieve."""
        created = kg.create_node(
            node_type=NodeType.REQUIREMENT,
            title="OAuth2.0 Support",
            content="System must support OAuth2.0",
            importance=0.9
        )
        
        assert created.id.startswith("kn_")
        
        retrieved = kg.get_node(created.id)
        assert retrieved is not None
        assert retrieved.title == "OAuth2.0 Support"
        assert retrieved.importance == 0.9
    
    def test_update_and_delete_node(self, kg):
        """Test update and delete cycle."""
        node = kg.create_node(
            node_type=NodeType.DECISION,
            title="Initial Title",
            content="Initial content"
        )
        
        updated = kg.update_node(node.id, title="Updated Title")
        assert updated.title == "Updated Title"
        
        deleted = kg.delete_node(node.id)
        assert deleted is True
        assert kg.get_node(node.id) is None


class TestKnowledgeGraphEdgeOps:
    @pytest.fixture
    def kg(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        kg = KnowledgeGraph(db_path)
        yield kg
        os.unlink(db_path)
    
    def test_create_and_get_edge(self, kg):
        """Test edge creation and retrieval."""
        n1 = kg.create_node(NodeType.REQUIREMENT, "Req", "Content 1")
        n2 = kg.create_node(NodeType.DECISION, "Dec", "Content 2")
        
        edge = kg.create_edge(n1.id, n2.id, EdgeType.DEPENDS_ON, evidence="Test evidence")
        
        assert edge.id.startswith("ke_")
        retrieved = kg.get_edge(edge.id)
        assert retrieved is not None
        assert retrieved.evidence == "Test evidence"


class TestKnowledgeGraphSearch:
    @pytest.fixture
    def kg(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        kg = KnowledgeGraph(db_path)
        kg.create_node(NodeType.REQUIREMENT, "OAuth Auth", "OAuth2.0 authentication", importance=0.9)
        kg.create_node(NodeType.DECISION, "JWT Token", "Use JWT tokens", importance=0.8)
        yield kg
        os.unlink(db_path)
    
    def test_search_basic(self, kg):
        """Test basic search returns matching nodes."""
        results = kg.search("OAuth")
        assert results.total >= 1
        assert any("OAuth" in n.title or "OAuth" in n.content for n in results.nodes)
    
    def test_list_nodes_by_type(self, kg):
        """Test listing nodes with type filter."""
        reqs = kg.list_nodes(node_type=NodeType.REQUIREMENT)
        assert len(reqs) >= 1
        assert all(n.node_type == NodeType.REQUIREMENT for n in reqs)


class TestKnowledgeGraphDiscovery:
    @pytest.fixture
    def kg(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        kg = KnowledgeGraph(db_path)
        n1 = kg.create_node(NodeType.REQUIREMENT, "Req", "Content about auth", tags=["auth"])
        n2 = kg.create_node(NodeType.DECISION, "Dec", "Decision about auth", tags=["auth"])
        kg.create_edge(n1.id, n2.id, EdgeType.DEPENDS_ON)
        yield kg
        os.unlink(db_path)
    
    def test_discover_default(self, kg):
        """Test discover with default strategies."""
        nodes = kg.list_nodes()
        discovered = kg.discover(nodes[0].id)
        assert isinstance(discovered, list)
    
    def test_discover_explicit_strategies(self, kg):
        """Test discover with explicit strategies."""
        nodes = kg.list_nodes()
        discovered = kg.discover(nodes[0].id, strategies=['semantic', 'structural'])
        assert isinstance(discovered, list)
    
    def test_find_path(self, kg):
        """Test find path between connected nodes."""
        nodes = kg.list_nodes()
        if len(nodes) >= 2:
            path = kg.find_path(nodes[0].id, nodes[1].id)
            # May or may not find a path depending on direction
            assert path is None or isinstance(path, list)
    
    def test_trace_requirement(self, kg):
        """Test trace requirement."""
        reqs = kg.list_nodes(node_type=NodeType.REQUIREMENT)
        if reqs:
            trace = kg.trace_requirement(reqs[0].id)
            assert 'node_id' in trace
            assert 'chains' in trace


class TestKnowledgeGraphSync:
    @pytest.fixture
    def kg(self, tmp_path):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        kg = KnowledgeGraph(db_path)
        kg.create_node(
            NodeType.REQUIREMENT, "Critical Req",
            "Must implement", importance=0.9, confidence=0.95
        )
        yield kg
        os.unlink(db_path)
    
    def test_sync_to_memory(self, kg, tmp_path):
        """Test sync writes to file."""
        memory_path = str(tmp_path / "MEMORY.md")
        count = kg.sync_to_memory(memory_path=memory_path)
        assert count >= 1
    
    def test_show_relations(self, kg):
        """Test show relations."""
        nodes = kg.list_nodes()
        if nodes:
            relations = kg.show_relations(nodes[0].id, direction="both")
            assert 'outgoing' in relations or 'incoming' in relations
    
    def test_get_stats(self, kg):
        """Test get stats."""
        stats = kg.get_stats()
        assert stats['total_nodes'] >= 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/knowledge_graph/test_knowledge_graph_facade.py -v
```
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Implement KnowledgeGraph facade class**

Create `quickagents/knowledge_graph/knowledge_graph.py`:

```python
class KnowledgeGraph:
    def __init__(self, db_path: str = '.quickagents/unified.db'):
        self.db_path = db_path
        self.storage = SQLiteGraphStorage(db_path)
        self.storage.initialize({})
        
        self.nodes = NodeManager(self.storage)
        self.edges = EdgeManager(self.storage)
        self.extractor = KnowledgeExtractor(self.nodes)
        self.discovery = RelationDiscovery(self.storage, self.edges)
        self.searcher = KnowledgeSearcher(self.storage)
        self.sync = MemorySync(self.nodes)
    
    def create_node(self, node_type, title, content, **kwargs):
        return self.nodes.create_node(node_type, title, content, **kwargs)
    
    # ... delegate all methods ...
    
    def discover(self, node_id, strategies=None):
        strategies = strategies or ['direct', 'semantic']
        discovered = []
        if 'direct' in strategies:
            discovered.extend(self.discovery.discover_direct_relations(node_id))
        if 'semantic' in strategies:
            discovered.extend(self.discovery.discover_semantic_relations(node_id))
        if 'structural' in strategies:
            discovered.extend(self.discovery.discover_structural_relations(node_id))
        if 'transitive' in strategies:
            discovered.extend(self.discovery.discover_transitive_relations(node_id))
        return discovered
    
    def show_relations(self, node_id, direction="both"):
        result = {}
        if direction in ('out', 'both'):
            result['outgoing'] = self.edges.get_outgoing_edges(node_id)
        if direction in ('in', 'both'):
            result['incoming'] = self.edges.get_incoming_edges(node_id)
        return result
    
    def get_stats(self):
        return self.storage.get_stats()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/knowledge_graph/test_knowledge_graph_facade.py -v
```
Expected: 15 passed

- [ ] **Step 5: Update `knowledge_graph/__init__.py` to export KnowledgeGraph**

Uncomment and enable the KnowledgeGraph import:
```python
from .knowledge_graph import KnowledgeGraph
__all__ = [..., 'KnowledgeGraph']
```

- [ ] **Step 6: Run all existing tests to verify no regressions**

```bash
pytest tests/knowledge_graph/ -v
```
Expected: 172 (existing) + 15 (new) = 187 passed

- [ ] **Step 7: Commit**

```bash
git add quickagents/knowledge_graph/knowledge_graph.py \
        quickagents/knowledge_graph/__init__.py \
        tests/knowledge_graph/test_knowledge_graph_facade.py
git commit -m "feat(knowledge-graph): implement KnowledgeGraph facade class with 15 tests

- Add KnowledgeGraph facade unifying all 6 core components
- Add discover() with configurable strategies
- Add show_relations() with direction support
- Delegate methods to sub-components
- 15 facade integration tests"
```

---

## Task 4.2: UnifiedDB Integration (~15 tests)

**Files:**
- Modify: `quickagents/core/unified_db.py` (add `knowledge` property)
- Modify: `quickagents/__init__.py` (add KnowledgeGraph exports)
- Create: `tests/knowledge_graph/test_unified_db_knowledge.py`

### Interface Changes

Add to `UnifiedDB`:

```python
class UnifiedDB:
    def __init__(self, db_path: str = '.quickagents/unified.db'):
        # ... existing code ...
        self._knowledge_graph = None  # NEW: lazy-loaded
    
    @property
    def knowledge(self) -> 'KnowledgeGraph':
        """Get knowledge graph manager (lazy-loaded)."""
        if self._knowledge_graph is None:
            from quickagents.knowledge_graph import KnowledgeGraph
            self._knowledge_graph = KnowledgeGraph(str(self.db_path))
        return self._knowledge_graph
```

Add to `quickagents/__init__.py`:

```python
from .knowledge_graph import (
    KnowledgeGraph, NodeType, EdgeType,
    KnowledgeNode, KnowledgeEdge, SearchResult,
    # exceptions
    KnowledgeGraphError, NodeNotFoundError, EdgeNotFoundError,
    DuplicateNodeError, DuplicateEdgeError,
    InvalidNodeTypeError, InvalidEdgeTypeError,
    CircularDependencyError, DatabaseIntegrityError,
    ExtractionError, SyncError,
)
```

### Test Cases (15)

| Category | Test Cases |
|----------|-----------|
| Property access | knowledge property returns KnowledgeGraph |
| Property access | lazy-loaded (same instance on repeated access) |
| Property access | works with default db_path |
| Node ops via UnifiedDB | create_node + get_node round-trip |
| Node ops via UnifiedDB | list_nodes with type filter |
| Edge ops via UnifiedDB | create_edge between nodes |
| Edge ops via UnifiedDB | get_outgoing_edges |
| Search via UnifiedDB | search returns results |
| Search via UnifiedDB | search_by_tags |
| Discovery via UnifiedDB | discover relations |
| Path via UnifiedDB | find_path |
| Trace via UnifiedDB | trace_requirement |
| Sync via UnifiedDB | sync_to_memory |
| Stats integration | knowledge stats accessible from db.get_stats() |
| Cross-system | UnifiedDB memory + knowledge coexist |

### TDD Steps

- [ ] **Step 1: Write failing tests for UnifiedDB knowledge integration**

```python
# tests/knowledge_graph/test_unified_db_knowledge.py
import pytest
import os
import tempfile
from quickagents.core.unified_db import UnifiedDB, MemoryType
from quickagents.knowledge_graph.types import NodeType, EdgeType


class TestUnifiedDBKnowledgeProperty:
    @pytest.fixture
    def db(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        db = UnifiedDB(db_path)
        yield db
        os.unlink(db_path)
    
    def test_knowledge_property_returns_instance(self, db):
        """Test knowledge property returns KnowledgeGraph."""
        kg = db.knowledge
        assert kg is not None
        assert hasattr(kg, 'create_node')
        assert hasattr(kg, 'search')
    
    def test_knowledge_lazy_loaded(self, db):
        """Test knowledge is lazy-loaded (same instance)."""
        kg1 = db.knowledge
        kg2 = db.knowledge
        assert kg1 is kg2
    
    def test_knowledge_default_path(self):
        """Test knowledge works with default db_path."""
        db = UnifiedDB('.quickagents/test_unified.db')
        kg = db.knowledge
        assert kg is not None
        os.unlink('.quickagents/test_unified.db')


class TestUnifiedDBKnowledgeNodeOps:
    @pytest.fixture
    def db(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        db = UnifiedDB(db_path)
        yield db
        os.unlink(db_path)
    
    def test_create_and_get_node(self, db):
        """Test node operations through UnifiedDB."""
        created = db.knowledge.create_node(
            node_type=NodeType.REQUIREMENT,
            title="Test via UnifiedDB",
            content="Created through UnifiedDB.knowledge"
        )
        retrieved = db.knowledge.get_node(created.id)
        assert retrieved.title == "Test via UnifiedDB"
    
    def test_list_nodes_by_type(self, db):
        """Test listing nodes with type filter."""
        db.knowledge.create_node(NodeType.REQUIREMENT, "Req 1", "Content")
        db.knowledge.create_node(NodeType.DECISION, "Dec 1", "Content")
        
        reqs = db.knowledge.list_nodes(node_type=NodeType.REQUIREMENT)
        assert len(reqs) >= 1
        assert all(n.node_type == NodeType.REQUIREMENT for n in reqs)


class TestUnifiedDBKnowledgeEdgeOps:
    @pytest.fixture
    def db(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        db = UnifiedDB(db_path)
        yield db
        os.unlink(db_path)
    
    def test_create_edge(self, db):
        """Test edge creation through UnifiedDB."""
        n1 = db.knowledge.create_node(NodeType.REQUIREMENT, "Req", "C1")
        n2 = db.knowledge.create_node(NodeType.DECISION, "Dec", "C2")
        edge = db.knowledge.create_edge(n1.id, n2.id, EdgeType.DEPENDS_ON)
        assert edge is not None
    
    def test_get_outgoing_edges(self, db):
        """Test getting outgoing edges."""
        n1 = db.knowledge.create_node(NodeType.REQUIREMENT, "Req", "C1")
        n2 = db.knowledge.create_node(NodeType.DECISION, "Dec", "C2")
        db.knowledge.create_edge(n1.id, n2.id, EdgeType.MAPS_TO)
        
        outgoing = db.knowledge.get_outgoing_edges(n1.id)
        assert len(outgoing) >= 1


class TestUnifiedDBKnowledgeSearch:
    @pytest.fixture
    def db(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        db = UnifiedDB(db_path)
        db.knowledge.create_node(
            NodeType.FACT, "Python Speed",
            "Python is an interpreted language", tags=["python"]
        )
        yield db
        os.unlink(db_path)
    
    def test_search(self, db):
        """Test search through UnifiedDB."""
        results = db.knowledge.search("Python")
        assert results.total >= 1
    
    def test_search_by_tags(self, db):
        """Test tag search through UnifiedDB."""
        nodes = db.knowledge.search_by_tags(["python"])
        assert len(nodes) >= 1


class TestUnifiedDBKnowledgeAdvanced:
    @pytest.fixture
    def db(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        db = UnifiedDB(db_path)
        yield db
        os.unlink(db_path)
    
    def test_discover_relations(self, db):
        """Test relation discovery through UnifiedDB."""
        n1 = db.knowledge.create_node(
            NodeType.REQUIREMENT, "Auth", "Auth requirement", tags=["auth"]
        )
        n2 = db.knowledge.create_node(
            NodeType.DECISION, "JWT", "JWT decision", tags=["auth"]
        )
        discovered = db.knowledge.discover(n1.id, strategies=['direct'])
        assert isinstance(discovered, list)
    
    def test_find_path(self, db):
        """Test find path through UnifiedDB."""
        n1 = db.knowledge.create_node(NodeType.REQUIREMENT, "Req", "C1")
        n2 = db.knowledge.create_node(NodeType.DECISION, "Dec", "C2")
        db.knowledge.create_edge(n1.id, n2.id, EdgeType.DEPENDS_ON)
        
        path = db.knowledge.find_path(n1.id, n2.id)
        assert path is not None
        assert len(path) == 2
    
    def test_trace_requirement(self, db):
        """Test trace requirement through UnifiedDB."""
        n1 = db.knowledge.create_node(NodeType.REQUIREMENT, "Req", "C1")
        n2 = db.knowledge.create_node(NodeType.DECISION, "Dec", "C2")
        db.knowledge.create_edge(n1.id, n2.id, EdgeType.MAPS_TO)
        
        trace = db.knowledge.trace_requirement(n1.id)
        assert trace['node_id'] == n1.id
    
    def test_sync_to_memory(self, db, tmp_path):
        """Test sync through UnifiedDB."""
        db.knowledge.create_node(
            NodeType.REQUIREMENT, "Critical",
            "Must do this", importance=0.9, confidence=0.95
        )
        memory_path = str(tmp_path / "MEMORY.md")
        count = db.knowledge.sync_to_memory(memory_path=memory_path)
        assert count >= 1


class TestUnifiedDBKnowledgeCoexistence:
    @pytest.fixture
    def db(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        db = UnifiedDB(db_path)
        yield db
        os.unlink(db_path)
    
    def test_memory_and_knowledge_coexist(self, db):
        """Test UnifiedDB memory and knowledge graph work together."""
        db.set_memory('project.name', 'TestProject', MemoryType.FACTUAL)
        db.knowledge.create_node(
            NodeType.FACT, "Project Info",
            "Project uses SQLite", importance=0.8
        )
        
        name = db.get_memory('project.name')
        assert name == 'TestProject'
        
        nodes = db.knowledge.list_nodes()
        assert len(nodes) >= 1
    
    def test_stats_includes_knowledge(self, db):
        """Test get_stats works alongside knowledge graph."""
        db.knowledge.create_node(NodeType.FACT, "Test", "Content")
        
        stats = db.get_stats()
        assert 'memory_count' in stats
        
        kg_stats = db.knowledge.get_stats()
        assert kg_stats['total_nodes'] >= 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/knowledge_graph/test_unified_db_knowledge.py -v
```
Expected: FAIL (AttributeError: 'UnifiedDB' object has no attribute 'knowledge')

- [ ] **Step 3: Add `knowledge` property to UnifiedDB**

Modify `quickagents/core/unified_db.py`:
1. Add `self._knowledge_graph = None` in `__init__`
2. Add `@property knowledge` method with lazy import

- [ ] **Step 4: Update `quickagents/__init__.py` exports**

Add KnowledgeGraph and related types to package-level exports.

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/knowledge_graph/test_unified_db_knowledge.py -v
```
Expected: 15 passed

- [ ] **Step 6: Run all tests for regression check**

```bash
pytest tests/ -v
```
Expected: All existing + 30 new tests pass

- [ ] **Step 7: Commit**

```bash
git add quickagents/core/unified_db.py \
        quickagents/__init__.py \
        tests/knowledge_graph/test_unified_db_knowledge.py
git commit -m "feat(knowledge-graph): integrate KnowledgeGraph with UnifiedDB

- Add lazy-loaded knowledge property to UnifiedDB
- Export KnowledgeGraph types from package root
- 15 integration tests for UnifiedDB.knowledge"
```

---

## Task 4.3: CLI Commands (~12 tests)

**Files:**
- Modify: `quickagents/cli/main.py` (add `knowledge` subcommand + handler)
- Create: `tests/integration/test_knowledge_graph_cli.py`

### CLI Command Design

Follow existing argparse pattern. Add single `knowledge` subcommand with action-based routing:

```python
# In main():
p_knowledge = subparsers.add_parser('knowledge', help='知识图谱管理')
p_knowledge.add_argument('action', choices=[
    'create-node', 'get-node', 'update-node', 'delete-node',
    'list-nodes', 'create-edge', 'delete-edge', 'show-relations',
    'discover', 'search', 'stats', 'sync',
    'find-path', 'trace-requirement'
], help='操作')
# ... action-specific arguments ...
p_knowledge.set_defaults(func=cmd_knowledge)


def cmd_knowledge(args):
    """知识图谱管理命令"""
    db = UnifiedDB('.quickagents/unified.db')
    kg = db.knowledge
    
    if args.action == 'create-node':
        node = kg.create_node(
            node_type=NodeType(args.type),
            title=args.title,
            content=args.content,
            tags=args.tags.split(',') if args.tags else [],
            importance=float(args.importance) if args.importance else 0.5,
            project_name=args.project,
            confidence=float(args.confidence) if args.confidence else 1.0
        )
        print(f"[OK] 创建节点: {node.id}")
        print(f"  类型: {node.node_type.value}")
        print(f"  标题: {node.title}")
    
    elif args.action == 'get-node':
        node = kg.get_node(args.node_id)
        if node:
            print(f"[Node] {node.id}")
            print(f"  类型: {node.node_type.value}")
            print(f"  标题: {node.title}")
            print(f"  内容: {node.content}")
            print(f"  重要性: {node.importance}")
            print(f"  标签: {', '.join(node.tags) if node.tags else '无'}")
        else:
            print(f"[FAIL] 节点未找到: {args.node_id}")
    
    elif args.action == 'list-nodes':
        node_type = NodeType(args.type) if args.type else None
        nodes = kg.list_nodes(node_type=node_type, limit=args.limit or 20)
        print(f"[Nodes] 节点列表 ({len(nodes)} 个)")
        print("-" * 60)
        for n in nodes:
            print(f"  [{n.node_type.value}] {n.id}: {n.title}")
    
    elif args.action == 'delete-node':
        deleted = kg.delete_node(args.node_id, cascade=args.cascade)
        print(f"[OK] 删除成功" if deleted else f"[FAIL] 节点未找到: {args.node_id}")
    
    elif args.action == 'create-edge':
        n1 = kg.get_node(args.source)
        n2 = kg.get_node(args.target)
        if not n1:
            print(f"[FAIL] 源节点未找到: {args.source}")
            return
        if not n2:
            print(f"[FAIL] 目标节点未找到: {args.target}")
            return
        edge = kg.create_edge(
            args.source, args.target,
            EdgeType(args.type),
            evidence=args.evidence,
            confidence=float(args.confidence) if args.confidence else 1.0
        )
        print(f"[OK] 创建边: {edge.id}")
        print(f"  {args.source} --[{args.type}]--> {args.target}")
    
    elif args.action == 'delete-edge':
        deleted = kg.delete_edge(args.edge_id)
        print(f"[OK] 删除成功" if deleted else f"[FAIL] 边未找到: {args.edge_id}")
    
    elif args.action == 'show-relations':
        direction = args.direction or 'both'
        relations = kg.show_relations(args.node_id, direction=direction)
        print(f"[Relations] {args.node_id}")
        if 'outgoing' in relations:
            print(f"  出边 ({len(relations['outgoing'])} 个):")
            for e in relations['outgoing']:
                print(f"    --[{e.edge_type.value}]--> {e.target_node_id}")
        if 'incoming' in relations:
            print(f"  入边 ({len(relations['incoming'])} 个):")
            for e in relations['incoming']:
                print(f"    <--[{e.edge_type.value}]-- {e.source_node_id}")
    
    elif args.action == 'discover':
        strategies = args.strategies.split(',') if args.strategies else None
        discovered = kg.discover(args.node_id, strategies=strategies)
        print(f"[Discover] 发现 {len(discovered)} 个关系")
        for edge in discovered:
            print(f"  {edge.source_node_id} --[{edge.edge_type.value}]--> {edge.target_node_id}")
    
    elif args.action == 'search':
        results = kg.search(args.query, limit=args.limit or 20)
        print(f"[Search] 搜索结果 ({results.total} 个)")
        print("-" * 60)
        for n in results.nodes:
            print(f"  [{n.node_type.value}] {n.id}: {n.title}")
            print(f"    {n.content[:80]}...")
    
    elif args.action == 'stats':
        stats = kg.get_stats()
        print("[Knowledge] 知识图谱统计")
        print("=" * 50)
        print(f"  节点总数: {stats['total_nodes']}")
        print(f"  边总数: {stats['total_edges']}")
        if stats.get('by_type'):
            print("\n  节点类型分布:")
            for t, c in stats['by_type'].items():
                print(f"    {t}: {c}")
        if stats.get('by_edge_type'):
            print("\n  边类型分布:")
            for t, c in stats['by_edge_type'].items():
                print(f"    {t}: {c}")
    
    elif args.action == 'sync':
        memory_path = args.memory_path or 'Docs/MEMORY.md'
        count = kg.sync_to_memory(memory_path=memory_path)
        print(f"[OK] 同步 {count} 个高重要性节点到 {memory_path}")
    
    elif args.action == 'find-path':
        path = kg.find_path(args.source, args.target, max_depth=args.max_depth or 5)
        if path:
            print(f"[Path] 路径找到 ({len(path)} 步):")
            print(" -> ".join(path))
        else:
            print(f"[FAIL] 未找到路径: {args.source} -> {args.target}")
    
    elif args.action == 'trace-requirement':
        trace = kg.trace_requirement(args.node_id)
        print(f"[Trace] 需求追踪: {trace['node_id']}")
        if trace['chains']:
            for chain in trace['chains']:
                print(f"  [{chain['type']}] {' -> '.join(chain['path'])}")
        else:
            print("  无追踪链")
```

### Argument Registration

```python
# create-node
p_knowledge_create = ...  # Handled via shared args based on action

# Use add_arguments conditionally or shared arguments
p_knowledge.add_argument('--type', '-t', help='节点/边类型')
p_knowledge.add_argument('--title', help='标题')
p_knowledge.add_argument('--content', help='内容')
p_knowledge.add_argument('--tags', help='标签（逗号分隔）')
p_knowledge.add_argument('--importance', help='重要性 (0.0-1.0)')
p_knowledge.add_argument('--confidence', help='置信度 (0.0-1.0)')
p_knowledge.add_argument('--project', help='项目名称')
p_knowledge.add_argument('--source', '--from', help='源节点ID')
p_knowledge.add_argument('--target', '--to', help='目标节点ID')
p_knowledge.add_argument('--evidence', help='证据/说明')
p_knowledge.add_argument('--node-id', help='节点ID')
p_knowledge.add_argument('--edge-id', help='边ID')
p_knowledge.add_argument('--direction', choices=['in', 'out', 'both'], help='方向')
p_knowledge.add_argument('--strategies', help='发现策略（逗号分隔）')
p_knowledge.add_argument('--query', '-q', help='搜索查询')
p_knowledge.add_argument('--limit', '-n', help='数量限制')
p_knowledge.add_argument('--memory-path', help='MEMORY.md路径')
p_knowledge.add_argument('--cascade', action='store_true', default=True, help='级联删除')
p_knowledge.add_argument('--max-depth', help='最大深度')
```

### Test Cases (12)

| Action | Test Cases |
|--------|-----------|
| create-node | creates node and prints ID |
| get-node | prints node details |
| get-node (not found) | prints failure message |
| list-nodes | lists nodes with type filter |
| delete-node | deletes and confirms |
| create-edge | creates edge between nodes |
| search | returns matching results |
| stats | prints statistics |
| sync | syncs to memory file |
| find-path | finds and prints path |
| discover | discovers and prints relations |
| trace-requirement | traces and prints chain |

### TDD Steps

- [ ] **Step 1: Write failing CLI tests**

```python
# tests/integration/test_knowledge_graph_cli.py
import pytest
import subprocess
import sys
import os
import tempfile
from quickagents.cli.main import main
from quickagents.core.unified_db import UnifiedDB
from quickagents.knowledge_graph.types import NodeType, EdgeType


class TestKnowledgeCLICreate:
    @pytest.fixture
    def db_path(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            path = f.name
        yield path
        os.unlink(path)
    
    def test_create_node(self, db_path, capsys, monkeypatch):
        """Test qa knowledge create-node."""
        monkeypatch.setattr(sys, 'argv', [
            'qa', 'knowledge', 'create-node',
            '--type', 'requirement',
            '--title', 'Test CLI Node',
            '--content', 'Created via CLI',
        ])
        # Need to inject db_path... use env var or direct call
        # Implementation detail: may need to mock UnifiedDB
        pass  # Will be fleshed out during implementation
```

> **Implementation Note:** CLI tests should either mock `UnifiedDB` or use subprocess invocation with a temp DB path. The exact pattern depends on whether `cmd_knowledge` can accept a `db_path` override. Recommended approach: test the `cmd_knowledge` function directly with mocked `args`, using a temp DB.

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/integration/test_knowledge_graph_cli.py -v
```

- [ ] **Step 3: Implement CLI handler and argument registration in `main.py`**

Add `cmd_knowledge` function and register `knowledge` subparser with all arguments.

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/integration/test_knowledge_graph_cli.py -v
```
Expected: 12 passed

- [ ] **Step 5: Run full regression**

```bash
pytest tests/ -v
```

- [ ] **Step 6: Commit**

```bash
git add quickagents/cli/main.py \
        tests/integration/test_knowledge_graph_cli.py
git commit -m "feat(knowledge-graph): add qa knowledge CLI commands

- Add knowledge subcommand with 14 actions
- Node CRUD: create-node, get-node, update-node, delete-node, list-nodes
- Edge CRUD: create-edge, delete-edge, show-relations
- Discovery: discover, find-path, trace-requirement
- Search and sync: search, stats, sync
- 12 CLI integration tests"
```

---

## Task 5.1: Final Integration Test + Documentation

**Files:**
- Create: `tests/integration/test_knowledge_graph_e2e.py` (end-to-end workflow test)
- Update: `Docs/MEMORY.md` (if exists)
- Update: `quickagents/knowledge_graph/__init__.py` (final exports review)

### End-to-End Test Scenario

```python
class TestKnowledgeGraphE2E:
    """End-to-end workflow: Extract → Create → Discover → Search → Sync"""
    
    def test_full_workflow(self):
        """
        1. Import knowledge from a markdown file
        2. Create additional nodes manually
        3. Create edges between related nodes
        4. Discover additional relations
        5. Search for knowledge
        6. Sync to MEMORY.md
        7. Verify all operations work together
        """
        pass
```

### TDD Steps

- [ ] **Step 1: Write E2E test**
- [ ] **Step 2: Run and verify pass**
- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_knowledge_graph_e2e.py
git commit -m "test(knowledge-graph): add end-to-end integration test

- Full workflow: extract → create → discover → search → sync
- Validates all components work together"
```

---

## Task 5.2: Final Verification + Cleanup + Push

**Goal:** Verify all tests pass, clean up, and push to remote.

### Verification Checklist

- [ ] **Run full test suite**

```bash
pytest tests/ -v --tb=short
```
Expected: All tests pass (172 existing + ~42 new = ~214 total)

- [ ] **Run import check**

```bash
python -c "from quickagents import UnifiedDB, KnowledgeGraph, NodeType, EdgeType; print('OK')"
```

- [ ] **Run CLI smoke test**

```bash
qa knowledge stats
qa knowledge search "test" --limit 5
```

- [ ] **Verify no regressions in existing functionality**

```bash
python -c "
from quickagents import UnifiedDB, MemoryType
db = UnifiedDB('.quickagents/unified.db')
db.set_memory('test.key', 'test_value', MemoryType.FACTUAL)
val = db.get_memory('test.key')
assert val == 'test_value', f'Expected test_value, got {val}'
print('UnifiedDB memory: OK')

kg = db.knowledge
stats = kg.get_stats()
print(f'Knowledge stats: {stats}')
print('All checks passed')
"
```

- [ ] **Run linting (if configured)**

```bash
ruff check quickagents/ --select E,F
```

- [ ] **Final commit (if any cleanup needed)**

```bash
git add -A
git commit -m "chore(knowledge-graph): final cleanup and verification"
```

- [ ] **Use finishing-a-development-branch skill to present completion options**

```
Load skill: finishing-a-development-branch
```

This will:
1. Verify all tests pass
2. Present options (merge, PR, cleanup)
3. Push to remote with proper branch handling

---

## Summary

| Task | Component | Files | Tests | Est. Time |
|------|-----------|-------|-------|-----------|
| 4.1 | KnowledgeGraph facade | 3 files | 15 | 1.5h |
| 4.2 | UnifiedDB integration | 3 files | 15 | 1h |
| 4.3 | CLI commands | 2 files | 12 | 1.5h |
| 5.1 | E2E test + docs | 1 file | 1 | 30m |
| 5.2 | Verification + push | 0 files | 0 | 30m |
| **Total** | **5 tasks** | **9 files** | **~43** | **~5h** |

### Dependency Graph

```
Task 4.1 (Facade) ← No new dependencies (uses existing core components)
Task 4.2 (UnifiedDB) ← Depends on 4.1
Task 4.3 (CLI) ← Depends on 4.2
Task 5.1 (E2E + docs) ← Depends on 4.3
Task 5.2 (Final) ← Depends on 5.1
```

**Execution order:** 4.1 → 4.2 → 4.3 → 5.1 → 5.2

### After Completion

Total test count: 172 (existing) + ~43 (new) = **~215 tests**

The knowledge graph feature will be fully integrated:
- `from quickagents import UnifiedDB; db = UnifiedDB(); kg = db.knowledge`
- `qa knowledge create-node --type requirement --title "..." --content "..."`
- `qa knowledge search "query"`
- `qa knowledge stats`

---

*Plan Version: 1.0.0*
*Created: 2026-03-30*
*Scope: Phase 4-5 - Integration Layer (Part 3)*
