# Knowledge Graph Feature Design Specification

> **Created**: 2026-03-29  
> **Version**: 1.0.0  
> **Author**: Prometheus (Planning Agent)  
> **Status**: Design Approved

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Requirements Analysis](#2-requirements-analysis)
3. [Architecture Design](#3-architecture-design)
4. [Data Model](#4-data-model)
5. [Core Functionality](#5-core-functionality)
6. [Interface Design](#6-interface-design)
7. [Error Handling](#7-error-handling)
8. [Testing Strategy](#8-testing-strategy)
9. [Implementation Roadmap](#9-implementation-roadmap)
10. [Appendices](#10-appendices)

---

## 1. Executive Summary

### 1.1 Problem Statement

QuickAgents currently lacks a persistent knowledge management system, leading to:

- **Context Loss**: AI loses understanding of requirements and decisions across sessions
- **Broken Associations**: Inconsistent decisions due to missing connections between knowledge
- **Retrieval Difficulty**: No efficient way to query historical knowledge
- **Update Synchronization**: Knowledge scattered across MEMORY.md, decisions, and code comments

### 1.2 Solution Overview

Implement a **Knowledge Graph** system integrated with UnifiedDB:

- **Lightweight SQLite Graph Storage**: No external dependencies
- **Pluggable Architecture**: Interfaces for future Neo4j/Vector DB integration
- **Intelligent Extraction**: Auto-extract knowledge with confidence scoring
- **Multi-Strategy Discovery**: Direct, semantic, structural, transitive relation discovery
- **Full-Text Search**: SQLite FTS5 powered retrieval
- **100% Test Coverage**: 110 test cases across 6 minimal units

### 1.3 Key Features

| Feature | Description |
|---------|-------------|
| Knowledge Nodes | 6 types: requirement, decision, insight, fact, concept, source |
| Knowledge Edges | 10 types: depends_on, cites, evolves_from, maps_to, etc. |
| Extraction | Auto-extract from text/files with confidence scoring |
| Discovery | 4 strategies for relation discovery |
| Search | Full-text search with filters, sorting, pagination |
| Sync | One-way sync to MEMORY.md for critical knowledge |

---

## 2. Requirements Analysis

### 2.1 Core Use Cases

| Use Case | Description | Priority |
|----------|-------------|----------|
| **Requirement Traceability** | Prevent AI from deviating from original requirements | P0 |
| **Knowledge Accumulation** | Store AI analysis of external materials long-term | P0 |
| **Relationship Discovery** | Auto-discover connections between knowledge nodes | P1 |

### 2.2 Knowledge Sources

- Technical documentation (markdown, PDF, docs)
- Academic papers
- Website content
- Code repositories
- Design specifications
- Business materials

### 2.3 Relationship Types

| Category | Types | Example |
|----------|-------|---------|
| Conceptual | depends_on, is_subclass_of | Module A depends on Module B |
| Citation | cites, links_to | Paper A cites Paper B |
| Evolution | evolves_from | Requirement v1 → v2 |
| Mapping | maps_to, affects | Requirement X maps to code file Y |

### 2.4 Pain Points to Solve

1. **Context loss on session restart**
2. **Broken associations leading to inconsistent decisions**
3. **Retrieval difficulty**
4. **Update synchronization issues**
5. **Inconsistent knowledge expression quality**

### 2.5 Integration Approach

**Hybrid Strategy**:
- Core knowledge storage in UnifiedDB (SQLite)
- Graph visualization/query as independent module
- Sync with existing MEMORY.md system

### 2.6 Non-Requirements

- **Visualization**: No visual graph rendering required
- Focus on AI-efficient querying and association

### 2.7 Knowledge Extraction Strategy

**Layered Auto-Extraction**:
- High-confidence (≥0.8): Auto-store without confirmation
- Low-confidence (<0.8): Wait for user confirmation

---

## 3. Architecture Design

### 3.1 Design Principles

| Principle | Description |
|-----------|-------------|
| **Pluggable Storage** | Abstract interface for Neo4j/other graph DBs |
| **Extensible Retrieval** | Interface for vector search (ChromaDB/Pinecone) |
| **Python API First** | All operations via local Python API, 0 token cost |
| **System Integration** | Extend UnifiedDB, share infrastructure |

### 3.2 Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│          Application Layer (Business Logic)             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ NodeManager  │  │ EdgeManager  │  │ Searcher     │  │
│  │ Extractor    │  │ Discovery    │  │ Sync         │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│         Abstraction Layer (Interfaces)                  │
│  ┌──────────────────┐  ┌──────────────────┐            │
│  │GraphStorageIntf  │  │VectorSearchIntf  │            │
│  │ (Pluggable)      │  │ (Extensible)     │            │
│  └──────────────────┘  └──────────────────┘            │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│          Storage Layer (Implementations)                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ SQLiteGraph │  │(Future)Neo4j│  │(Future)VecDB│    │
│  │   (Default) │  │  (Enterprise)│  │  (Enhanced) │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 3.3 Core Components

| Component | Responsibility | Dependencies |
|-----------|---------------|--------------|
| NodeManager | Node CRUD operations | GraphStorageInterface |
| EdgeManager | Edge CRUD operations | GraphStorageInterface |
| KnowledgeExtractor | Extract knowledge from sources | AI Interface |
| RelationDiscovery | Discover node relationships | GraphStorageInterface |
| KnowledgeSearcher | Full-text and filtered search | SQLite FTS5 |
| MemorySync | Sync to MEMORY.md | - |

### 3.4 System Integration Points

- **UnifiedDB Extension**: Add 3 tables (knowledge_nodes, knowledge_edges, knowledge_index)
- **MEMORY.md Sync**: Auto-sync high-importance nodes to Factual Memory
- **Python API**: Add knowledge_graph module to quickagents package
- **CLI Commands**: Add `qa knowledge` command series

---

## 4. Data Model

### 4.1 SQLite Schema

#### 4.1.1 knowledge_nodes

```sql
CREATE TABLE knowledge_nodes (
    id TEXT PRIMARY KEY,                    -- UUID: kn_xxxxx
    node_type TEXT NOT NULL,                -- requirement/decision/insight/fact/concept/source
    title TEXT NOT NULL,                    -- Short description
    content TEXT NOT NULL,                  -- Detailed description
    source_type TEXT,                       -- doc/paper/code/web/discussion
    source_uri TEXT,                        -- file:// or https://
    confidence REAL DEFAULT 1.0,            -- 0.0-1.0
    importance REAL DEFAULT 0.5,            -- 0.0-1.0
    tags TEXT,                              -- JSON array: ["tag1", "tag2"]
    metadata TEXT,                          -- JSON object: extensible
    project_name TEXT,                      -- Project name
    feature_id TEXT,                        -- Feature module (optional)
    created_at TEXT NOT NULL,               -- ISO 8601
    updated_at TEXT NOT NULL,               -- ISO 8601
    access_count INTEGER DEFAULT 0,         -- Access count for ranking
    last_accessed_at TEXT                   -- Last access timestamp
);

-- Indexes
CREATE INDEX idx_nodes_type ON knowledge_nodes(node_type);
CREATE INDEX idx_nodes_project ON knowledge_nodes(project_name);
CREATE INDEX idx_nodes_feature ON knowledge_nodes(feature_id);
CREATE INDEX idx_nodes_importance ON knowledge_nodes(importance DESC);
CREATE INDEX idx_nodes_created ON knowledge_nodes(created_at DESC);
```

#### 4.1.2 knowledge_edges

```sql
CREATE TABLE knowledge_edges (
    id TEXT PRIMARY KEY,                    -- UUID: ke_xxxxx
    source_node_id TEXT NOT NULL,
    target_node_id TEXT NOT NULL,
    edge_type TEXT NOT NULL,                -- depends_on/cites/evolves_from/etc.
    weight REAL DEFAULT 1.0,                -- 0.0-1.0
    evidence TEXT,                          -- Evidence/source
    metadata TEXT,                          -- JSON object
    confidence REAL DEFAULT 1.0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    
    FOREIGN KEY (source_node_id) REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (target_node_id) REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    
    UNIQUE(source_node_id, target_node_id, edge_type)
);

-- Indexes
CREATE INDEX idx_edges_source ON knowledge_edges(source_node_id);
CREATE INDEX idx_edges_target ON knowledge_edges(target_node_id);
CREATE INDEX idx_edges_type ON knowledge_edges(edge_type);
CREATE INDEX idx_edges_weight ON knowledge_edges(weight DESC);
```

#### 4.1.3 knowledge_index (FTS5)

```sql
CREATE VIRTUAL TABLE knowledge_index USING fts5(
    node_id UNINDEXED,
    title,
    content,
    tags,
    source_uri,
    
    tokenize='porter unicode61',
    content='knowledge_nodes',
    content_rowid='rowid'
);

-- Auto-sync triggers
CREATE TRIGGER idx_node_insert AFTER INSERT ON knowledge_nodes BEGIN
    INSERT INTO knowledge_index(rowid, node_id, title, content, tags, source_uri)
    VALUES (NEW.rowid, NEW.id, NEW.title, NEW.content, NEW.tags, NEW.source_uri);
END;

CREATE TRIGGER idx_node_update AFTER UPDATE ON knowledge_nodes BEGIN
    UPDATE knowledge_index 
    SET title=NEW.title, content=NEW.content, tags=NEW.tags, source_uri=NEW.source_uri
    WHERE rowid=NEW.rowid;
END;

CREATE TRIGGER idx_node_delete AFTER DELETE ON knowledge_nodes BEGIN
    DELETE FROM knowledge_index WHERE rowid=OLD.rowid;
END;
```

### 4.2 Node Types

| Type | Description | Example |
|------|-------------|---------|
| `requirement` | Requirements | "System must support OAuth2.0" |
| `decision` | Technical decisions | "Choose JWT for tokens" |
| `insight` | AI insights | Key findings from papers |
| `fact` | Technical facts | Constraints, rules |
| `concept` | Abstract concepts | Terms, definitions |
| `source` | External references | Papers, docs, websites |

### 4.3 Edge Types

| Type | Description | Typical Scenario |
|------|-------------|-----------------|
| `depends_on` | Dependency | Module A depends on B |
| `is_subclass_of` | Inheritance | Subclass relationship |
| `cites` | Citation | Paper A cites Paper B |
| `links_to` | Link | Doc A links to Doc B |
| `evolves_from` | Evolution | Requirement v2 from v1 |
| `maps_to` | Mapping | Requirement to code |
| `affects` | Influence | Decision affects module |
| `contradicts` | Conflict | Discovered contradiction |
| `supports` | Support | Evidence supports conclusion |
| `related_to` | General | Generic association |

---

## 5. Core Functionality

### 5.1 Knowledge Extraction Flow

```
Input Sources → Knowledge Identification → Confidence Calculation
    ↓
Deduplication Check → Storage → Post-processing
```

**Steps**:

1. **Input Sources**: External docs, AI conversations, code analysis, manual input
2. **Knowledge Identification**: Entity recognition, relation recognition, type classification
3. **Confidence Calculation**:
   - High (≥0.8): Auto-store
   - Medium (0.5-0.8): Mark for confirmation
   - Low (<0.5): Discard or request confirmation
4. **Deduplication**: Title/content similarity check via FTS5
5. **Storage**: Write to knowledge_nodes, update FTS5 index
6. **Post-processing**: Trigger relation discovery

### 5.2 Relation Discovery Flow

**Discovery Strategies**:

1. **Direct Discovery**:
   - Reference detection: Search for other node IDs/titles in content
   - Link detection: Check source_uri for other node paths
   - Tag overlap: Shared tags ≥ 2 → related_to

2. **Semantic Discovery**:
   - FTS5 full-text search
   - BM25 relevance scoring
   - High relevance (>0.7) → related_to

3. **Structural Discovery**:
   - Same feature_id → related_to
   - Same source_type → clustering
   - Temporal proximity: Similar created_at

4. **Transitive Discovery**:
   - A→B, B→C → A indirectly_related_to C
   - Relation chain analysis

### 5.3 Search Flow

```
Query Parsing → Multi-dimensional Retrieval → Result Merging & Sorting
    ↓
Relation Expansion (optional) → Return Results → Update Access Count
```

**Sorting Algorithm**:
```
score = 0.4 * relevance + 0.3 * importance + 0.3 * recency
```

### 5.4 MEMORY.md Sync Flow

**Sync Strategy**: One-way (SQLite → MEMORY.md)

**Sync Conditions**:
- Node importance ≥ 0.8
- Node type in [requirement, decision, fact]
- Manual sync_to_memory=True

**Sync Format**:
```markdown
## Knowledge Graph Sync

### Requirements
- [kn_001] OAuth2.0 support required
- [kn_002] Token refresh needed

### Decisions
- [kn_101] Choose JWT (source: RFC 7519)

### Key Facts
- [kn_201] CSRF protection required
```

---

## 6. Interface Design

### 6.1 Minimal Unit Classes

#### 6.1.1 NodeManager

```python
class NodeManager:
    """Node Manager - Minimal Unit"""
    
    def create_node(
        self,
        node_type: NodeType,
        title: str,
        content: str,
        **kwargs
    ) -> KnowledgeNode:
        """Create single node"""
        pass
    
    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Get single node"""
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
        """List nodes"""
        pass
```

#### 6.1.2 EdgeManager

```python
class EdgeManager:
    """Edge Manager - Minimal Unit"""
    
    def create_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType,
        **kwargs
    ) -> KnowledgeEdge:
        """Create single edge"""
        pass
    
    def get_edge(self, edge_id: str) -> Optional[KnowledgeEdge]:
        """Get single edge"""
        pass
    
    def delete_edge(self, edge_id: str) -> bool:
        """Delete single edge"""
        pass
    
    def get_outgoing_edges(
        self,
        node_id: str,
        edge_type: EdgeType = None
    ) -> List[KnowledgeEdge]:
        """Get outgoing edges"""
        pass
    
    def get_incoming_edges(
        self,
        node_id: str,
        edge_type: EdgeType = None
    ) -> List[KnowledgeEdge]:
        """Get incoming edges"""
        pass
```

#### 6.1.3 KnowledgeExtractor

```python
class KnowledgeExtractor:
    """Knowledge Extractor - Minimal Unit"""
    
    def extract_from_text(
        self,
        text: str,
        source_type: str = "discussion",
        **kwargs
    ) -> List[KnowledgeNode]:
        """Extract knowledge from text"""
        pass
    
    def import_from_file(
        self,
        file_path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Import knowledge from file"""
        pass
    
    def validate_confidence(self, node: KnowledgeNode) -> bool:
        """Validate confidence"""
        pass
    
    def check_duplicate(self, title: str, content: str) -> Optional[str]:
        """Check for duplicate node"""
        pass
```

#### 6.1.4 RelationDiscovery

```python
class RelationDiscovery:
    """Relation Discovery - Minimal Unit"""
    
    def discover_direct_relations(self, node_id: str) -> List[KnowledgeEdge]:
        """Discover direct relations"""
        pass
    
    def discover_semantic_relations(self, node_id: str) -> List[KnowledgeEdge]:
        """Discover semantic relations"""
        pass
    
    def discover_structural_relations(self, node_id: str) -> List[KnowledgeEdge]:
        """Discover structural relations"""
        pass
    
    def discover_transitive_relations(self, node_id: str) -> List[KnowledgeEdge]:
        """Discover transitive relations"""
        pass
    
    def find_path(
        self,
        from_node: str,
        to_node: str,
        max_depth: int = 5
    ) -> Optional[List[str]]:
        """Find path between nodes"""
        pass
    
    def trace_requirement(
        self,
        node_id: str,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """Trace requirement chain"""
        pass
```

#### 6.1.5 KnowledgeSearcher

```python
class KnowledgeSearcher:
    """Knowledge Searcher - Minimal Unit"""
    
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

#### 6.1.6 MemorySync

```python
class MemorySync:
    """Memory Sync - Minimal Unit"""
    
    def sync_to_memory(
        self,
        memory_path: str = "Docs/MEMORY.md"
    ) -> int:
        """Sync to MEMORY.md"""
        pass
    
    def filter_sync_candidates(
        self,
        nodes: List[KnowledgeNode]
    ) -> List[KnowledgeNode]:
        """Filter sync candidates"""
        pass
    
    def format_for_memory(self, node: KnowledgeNode) -> str:
        """Format for MEMORY.md"""
        pass
```

### 6.2 Facade Class: KnowledgeGraph

```python
class KnowledgeGraph:
    """
    Knowledge Graph Manager - Facade Pattern
    
    Combines all minimal units, provides unified interface
    """
    
    def __init__(self, db_path: str = '.quickagents/unified.db'):
        self.storage = SQLiteGraphStorage(db_path)
        self.nodes = NodeManager(self.storage)
        self.edges = EdgeManager(self.storage)
        self.extractor = KnowledgeExtractor(self.storage)
        self.discovery = RelationDiscovery(self.storage)
        self.searcher = KnowledgeSearcher(self.storage)
        self.sync = MemorySync(self.storage)
    
    # Delegate methods to sub-components
    def create_node(self, *args, **kwargs):
        return self.nodes.create_node(*args, **kwargs)
    
    def search(self, *args, **kwargs):
        return self.searcher.search(*args, **kwargs)
    
    # ... other delegate methods
```

### 6.3 Abstraction Interfaces

#### 6.3.1 GraphStorageInterface

```python
class GraphStorageInterface(ABC):
    """Graph Storage Abstract Interface - Pluggable Backend"""
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool: pass
    
    @abstractmethod
    def create_node(self, node: KnowledgeNode) -> KnowledgeNode: pass
    
    @abstractmethod
    def get_node(self, node_id: str) -> Optional[KnowledgeNode]: pass
    
    @abstractmethod
    def update_node(self, node_id: str, updates: Dict) -> KnowledgeNode: pass
    
    @abstractmethod
    def delete_node(self, node_id: str, cascade: bool = True) -> bool: pass
    
    @abstractmethod
    def create_edge(self, edge: KnowledgeEdge) -> KnowledgeEdge: pass
    
    @abstractmethod
    def get_edge(self, edge_id: str) -> Optional[KnowledgeEdge]: pass
    
    @abstractmethod
    def delete_edge(self, edge_id: str) -> bool: pass
    
    @abstractmethod
    def query_nodes(self, filters: Dict, limit: int = 100) -> List[KnowledgeNode]: pass
    
    @abstractmethod
    def query_edges(self, filters: Dict, limit: int = 100) -> List[KnowledgeEdge]: pass
    
    @abstractmethod
    def find_path(self, from_node: str, to_node: str, max_depth: int = 5) -> Optional[List[str]]: pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]: pass


class SQLiteGraphStorage(GraphStorageInterface):
    """SQLite Implementation (Default)"""
    pass


class Neo4jGraphStorage(GraphStorageInterface):
    """Neo4j Implementation (Enterprise Extension)"""
    pass
```

#### 6.3.2 VectorSearchInterface

```python
class VectorSearchInterface(ABC):
    """Vector Search Abstract Interface - Extensible Engine"""
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool: pass
    
    @abstractmethod
    def index_node(self, node: KnowledgeNode) -> bool: pass
    
    @abstractmethod
    def remove_node(self, node_id: str) -> bool: pass
    
    @abstractmethod
    def search(
        self,
        query: str,
        top_k: int = 20,
        filters: Dict = None
    ) -> List[Tuple[str, float]]:
        """Return [(node_id, score), ...]"""
        pass
    
    @abstractmethod
    def get_embedding(self, node_id: str) -> Optional[List[float]]: pass


class SQLiteFTSSearch(VectorSearchInterface):
    """SQLite FTS5 Implementation (Default)"""
    pass


class ChromaDBVectorSearch(VectorSearchInterface):
    """ChromaDB Implementation (Enhanced Extension)"""
    pass
```

### 6.4 CLI Commands

```bash
# Node Operations
qa knowledge create-node --type TYPE --title TITLE --content CONTENT [OPTIONS]
qa knowledge get-node NODE_ID [--expand]
qa knowledge update-node NODE_ID [OPTIONS]
qa knowledge delete-node NODE_ID [--cascade]
qa knowledge list-nodes --type TYPE [--project NAME] [--limit N]

# Edge Operations
qa knowledge create-edge --from SOURCE --to TARGET --type TYPE [OPTIONS]
qa knowledge get-edge EDGE_ID
qa knowledge delete-edge EDGE_ID
qa knowledge show-relations NODE_ID [--direction in|out|both]
qa knowledge discover NODE_ID [--strategies direct,semantic,structural]

# Search
qa knowledge search QUERY [--type TYPE] [--limit N]
qa knowledge search QUERY --type requirement,decision --project NAME --tags tag1,tag2 --min-importance 0.7 --sort-by importance --expand

# Import/Export
qa knowledge import FILE_PATH [--mode auto|manual] [--project NAME]
qa knowledge export --format json|markdown|graphml --output FILE

# Sync & Maintenance
qa knowledge sync [--memory-path PATH]
qa knowledge stats
qa knowledge rebuild-index
qa knowledge clean-orphans

# Path Queries
qa knowledge find-path --from NODE_ID --to NODE_ID [--max-depth N]
qa knowledge trace-requirement NODE_ID
qa knowledge subgraph NODE_ID1,NODE_ID2 [--depth N]
```

### 6.5 UnifiedDB Integration

```python
class UnifiedDB:
    """Extended UnifiedDB"""
    
    def __init__(self, db_path: str = '.quickagents/unified.db'):
        # ... existing code ...
        self._knowledge_graph = None
    
    @property
    def knowledge(self) -> KnowledgeGraph:
        """Get knowledge graph manager"""
        if self._knowledge_graph is None:
            from quickagents.knowledge_graph import KnowledgeGraph
            self._knowledge_graph = KnowledgeGraph(self.db_path)
        return self._knowledge_graph
```

---

## 7. Error Handling

### 7.1 Exception Hierarchy

```python
class KnowledgeGraphError(Exception):
    """Base exception"""
    pass

class NodeNotFoundError(KnowledgeGraphError):
    """Node not found"""
    pass

class EdgeNotFoundError(KnowledgeGraphError):
    """Edge not found"""
    pass

class DuplicateNodeError(KnowledgeGraphError):
    """Duplicate node"""
    pass

class DuplicateEdgeError(KnowledgeGraphError):
    """Duplicate edge"""
    pass

class InvalidNodeTypeError(KnowledgeGraphError):
    """Invalid node type"""
    pass

class InvalidEdgeTypeError(KnowledgeGraphError):
    """Invalid edge type"""
    pass

class CircularDependencyError(KnowledgeGraphError):
    """Circular dependency"""
    pass

class DatabaseIntegrityError(KnowledgeGraphError):
    """Database integrity error"""
    pass

class ExtractionError(KnowledgeGraphError):
    """Knowledge extraction failed"""
    pass

class SyncError(KnowledgeGraphError):
    """Sync failed"""
    pass
```

### 7.2 Error Recovery

| Error Type | Recovery Strategy | User Message |
|-----------|-------------------|--------------|
| Node not found | Return None/empty list | "Node {id} not found" |
| Edge not found | Return None | "Edge {id} not found" |
| Duplicate node | Return existing node | "Similar node {id} found, merge?" |
| Duplicate edge | Return existing edge | "Edge exists, update weight?" |
| Circular dependency | Reject creation | "Circular dependency detected" |
| Database error | Auto-retry (3x) | "DB operation failed, retried 3x" |
| Extraction failed | Log, continue | "Cannot extract from {source}: {reason}" |
| Sync failed | Keep local data | "Sync to {target} failed, local retained" |

---

## 8. Testing Strategy

### 8.1 Test Pyramid

```
                    ┌─────────┐
                    │  E2E    │ (5%)
                    │  Tests  │
                  ┌─┴─────────┴─┐
                  │ Integration │ (25%)
                  │   Tests     │
                ┌─┴─────────────┴─┐
                │   Unit Tests    │ (70%)
                │                 │
                └─────────────────┘
```

### 8.2 Unit Test Coverage (100% Required)

#### 8.2.1 TestNodeManager (20 test cases)

| Method | Test Cases |
|--------|-----------|
| create_node | basic, all_params, invalid_type, duplicate_title |
| get_node | existing, nonexistent, invalid_id_format |
| update_node | title, multiple_fields, nonexistent, empty_update |
| delete_node | basic, cascade_true, cascade_false, nonexistent |
| list_nodes | all, by_type, with_limit, empty_db, pagination |

#### 8.2.2 TestEdgeManager (19 test cases)

| Method | Test Cases |
|--------|-----------|
| create_edge | basic, with_evidence, duplicate, invalid_source, invalid_target |
| get_edge | existing, nonexistent, invalid_id_format |
| delete_edge | basic, nonexistent, with_invalid_nodes |
| get_outgoing_edges | basic, with_type_filter, no_edges, invalid_node |
| get_incoming_edges | basic, with_type_filter, no_edges, invalid_node |

#### 8.2.3 TestKnowledgeExtractor (18 test cases)

| Method | Test Cases |
|--------|-----------|
| extract_from_text | single_req, multiple, high_conf, low_conf, empty, malformed |
| import_from_file | markdown, text, nonexistent, unsupported, permission_denied |
| validate_confidence | high, low, boundary |
| check_duplicate | exact_match, similar_title, no_match, case_insensitive |

#### 8.2.4 TestRelationDiscovery (25 test cases)

| Method | Test Cases |
|--------|-----------|
| discover_direct_relations | by_reference, by_link, by_tags, no_relations |
| discover_semantic_relations | high_sim, low_sim, threshold_boundary, empty_content |
| discover_structural_relations | same_feature, same_project, temporal_proximity, no_relations |
| discover_transitive_relations | two_hop, three_hop, cycle_detection, no_transitive |
| find_path | direct, multi_hop, no_path, max_depth_exceeded, circular_graph |
| trace_requirement | full_chain, partial_chain, no_chain, circular_reference |

#### 8.2.5 TestKnowledgeSearcher (16 test cases)

| Method | Test Cases |
|--------|-----------|
| search | basic, type_filter, project_filter, tag_filter, date_filter, sorting, pagination, relation_expansion |
| search_by_tags | single_tag, multiple_tags, nonexistent_tag, with_limit |
| search_by_date_range | basic, open_ended, no_results, invalid_format |

#### 8.2.6 TestMemorySync (12 test cases)

| Method | Test Cases |
|--------|-----------|
| sync_to_memory | basic, no_candidates, file_not_found, permission_denied |
| filter_sync_candidates | by_importance, by_type, combined_criteria, empty_list |
| format_for_memory | requirement, decision, fact, with_metadata |

### 8.3 Test Coverage Summary

| Minimal Unit | Methods | Test Cases | Coverage |
|-------------|---------|-----------|----------|
| NodeManager | 5 | 20 | 100% |
| EdgeManager | 5 | 19 | 100% |
| KnowledgeExtractor | 4 | 18 | 100% |
| RelationDiscovery | 6 | 25 | 100% |
| KnowledgeSearcher | 3 | 16 | 100% |
| MemorySync | 3 | 12 | 100% |
| **Total** | **26** | **110** | **100%** |

### 8.4 Integration Tests

```python
class TestKnowledgeGraphIntegration:
    """Integration: Full workflows"""
    
    def test_full_extraction_workflow(self):
        """Test: Extract → Discover → Search → Sync"""
        pass
    
    def test_requirement_traceability(self):
        """Test: Create chain → Trace path"""
        pass
```

### 8.5 Performance Tests

| Test | Threshold | Description |
|------|-----------|-------------|
| Bulk insert | < 5s | 1000 nodes |
| Search | < 2s | 100 searches |
| Path query | < 1s | Complex path |
| DB size | < 100MB | 10K nodes |

---

## 9. Implementation Roadmap

### 9.1 Phase 1: Storage Layer (Week 1)

- [ ] Create SQLite tables
- [ ] Implement GraphStorageInterface
- [ ] Implement SQLiteGraphStorage
- [ ] Implement NodeManager
- [ ] Implement EdgeManager
- [ ] Unit tests (39 test cases)
- [ ] Integration tests

### 9.2 Phase 2: Association Layer (Week 2)

- [ ] Implement KnowledgeExtractor
- [ ] Implement RelationDiscovery
- [ ] Implement path finding algorithm
- [ ] Implement requirement tracing
- [ ] Unit tests (43 test cases)
- [ ] Integration tests

### 9.3 Phase 3: Retrieval Layer (Week 3)

- [ ] Implement KnowledgeSearcher
- [ ] Implement MemorySync
- [ ] Implement VectorSearchInterface (stub)
- [ ] CLI commands
- [ ] Unit tests (28 test cases)
- [ ] Integration tests
- [ ] Performance tests

### 9.4 Phase 4: Documentation & Polish (Week 4)

- [ ] API documentation
- [ ] Usage examples
- [ ] Error handling refinement
- [ ] Performance optimization
- [ ] Final testing

---

## 10. Appendices

### 10.1 Example Usage

```python
from quickagents import UnifiedDB, NodeType, EdgeType

db = UnifiedDB()
kg = db.knowledge

# Create nodes
req = kg.create_node(
    node_type=NodeType.REQUIREMENT,
    title="OAuth2.0支持",
    content="系统需要支持OAuth2.0认证",
    tags=["auth", "security"],
    importance=0.9
)

decision = kg.create_node(
    node_type=NodeType.DECISION,
    title="选择JWT",
    content="选择JWT作为Token方案",
    tags=["auth", "jwt"],
    importance=0.8
)

# Create edge
kg.create_edge(
    source_id=req.id,
    target_id=decision.id,
    edge_type=EdgeType.DEPENDS_ON,
    evidence="需求依赖技术决策"
)

# Search
results = kg.search("OAuth认证")
print(f"Found {results.total} results")

# Trace requirement
trace = kg.trace_requirement(req.id)
print(f"Trace path: {trace['path']}")

# Sync to MEMORY.md
synced = kg.sync_to_memory()
print(f"Synced {synced} nodes")
```

### 10.2 CLI Example

```bash
# Create node
qa knowledge create-node \
  --type requirement \
  --title "OAuth2.0支持" \
  --content "系统需要支持OAuth2.0认证" \
  --tags auth,security \
  --importance 0.9

# Search
qa knowledge search "OAuth" --type requirement --expand

# Trace requirement
qa knowledge trace-requirement kn_001

# Sync
qa knowledge sync
```

### 10.3 Future Extensions

| Extension | Interface | Implementation |
|-----------|-----------|----------------|
| Neo4j Integration | GraphStorageInterface | Neo4jGraphStorage |
| Vector Search | VectorSearchInterface | ChromaDBVectorSearch |
| Graph Visualization | - | Web-based viewer |
| Knowledge Import | - | Batch import from various formats |

---

**End of Specification**

---

*Document Version: 1.0.0*  
*Last Updated: 2026-03-29*
