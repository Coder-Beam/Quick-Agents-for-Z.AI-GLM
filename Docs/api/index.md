# QuickAgents API Reference v2.7.0

> Complete API documentation for QuickAgents toolkit

## Table of Contents

1. [Core Modules](#core-modules)
   - [UnifiedDB](#unifieddb)
   - [SkillEvolution](#skillevolution)
   - [MarkdownSync](#markdownsync)
   - [FileManager](#filemanager)
   - [LoopDetector](#loopdetector)
   - [Reminder](#reminder)
2. [Knowledge Graph](#knowledge-graph)
   - [KnowledgeGraph](#knowledgegraph)
   - [NodeManager](#nodemanager)
   - [EdgeManager](#edgemanager)
   - [Searcher](#searcher)
3. [Skills Modules](#skills-modules)
   - [TDDWorkflow](#tddworkflow)
   - [GitCommit](#gitcommit)
   - [FeedbackCollector](#feedbackcollector)
4. [Browser Automation](#browser-automation)
   - [Browser](#browser)
5. [CLI Tools](#cli-tools)
6. [Utilities](#utilities)

---

## Core Modules

### UnifiedDB

Unified database management for memory, tasks, progress, feedback, and decisions.

#### Import

```python
from quickagents import UnifiedDB, MemoryType, TaskStatus, FeedbackType
```

#### Constructor

```python
db = UnifiedDB(db_path: str = '.quickagents/unified.db')
```

**Parameters:**
- `db_path` (str): Path to SQLite database file

#### Memory Operations

```python
# Set memory
db.set_memory(
    key: str,
    value: Any,
    memory_type: MemoryType,
    category: Optional[str] = None,
    ttl: Optional[int] = None
) -> None

# Get memory
db.get_memory(key: str) -> Optional[Any]

# Search memory
db.search_memory(
    query: str,
    memory_type: Optional[MemoryType] = None,
    limit: int = 10
) -> List[Dict]
```

**MemoryType Enum:**
- `FACTUAL`: Static factual information
- `EXPERIENTIAL`: Dynamic experiential information
- `WORKING`: Current working state

#### Task Operations

```python
# Add task
db.add_task(
    task_id: str,
    name: str,
    priority: str = 'P2',
    description: Optional[str] = None
) -> None

# Update task status
db.update_task_status(
    task_id: str,
    status: TaskStatus
) -> None

# Get tasks
db.get_tasks(
    status: Optional[TaskStatus] = None,
    limit: int = 50
) -> List[Dict]
```

**TaskStatus Enum:**
- `PENDING`: Task not started
- `IN_PROGRESS`: Task in progress
- `COMPLETED`: Task completed
- `BLOCKED`: Task blocked
- `CANCELLED`: Task cancelled

#### Progress Operations

```python
# Initialize progress
db.init_progress(project_id: str, total_tasks: int = 0) -> None

# Update progress
db.update_progress(field: str, value: Any) -> None

# Get progress
db.get_progress() -> Dict[str, Any]
```

#### Feedback Operations

```python
# Add feedback
db.add_feedback(
    feedback_type: FeedbackType,
    title: str,
    description: Optional[str] = None,
    **metadata
) -> None

# Get feedback
db.get_feedback(
    feedback_type: Optional[FeedbackType] = None,
    limit: int = 50
) -> List[Dict]
```

**FeedbackType Enum:**
- `BUG`: Bug reports
- `IMPROVEMENT`: Improvement suggestions
- `BEST_PRACTICE`: Best practices
- `PITFALL`: Pitfalls to avoid
- `SKILL_REVIEW`: Skill evaluations
- `AGENT_REVIEW`: Agent evaluations

#### Statistics

```python
# Get database statistics
db.get_stats() -> Dict[str, Any]
```

---

### SkillEvolution

Unified self-evolution system for skills.

#### Import

```python
from quickagents import get_evolution, EvolutionTrigger
```

#### Get Instance

```python
evolution = get_evolution(db_path: Optional[str] = None)
```

#### Methods

```python
# Task completion trigger
evolution.on_task_complete(task_info: Dict) -> None

# Git commit trigger
evolution.on_git_commit() -> None

# Check periodic trigger
evolution.check_periodic_trigger() -> bool

# Run periodic optimization
evolution.run_periodic_optimization() -> Dict

# Get evolution status
evolution.get_status() -> Dict
```

**Task Info Structure:**
```python
{
    'task_id': str,
    'task_name': str,
    'skills_used': List[str],
    'success': bool,
    'duration_ms': Optional[int],
    'error': Optional[str]
}
```

**EvolutionTrigger Enum:**
- `TASK_COMPLETE`: Triggered on task completion
- `GIT_COMMIT`: Triggered on git commit
- `PERIODIC`: Triggered periodically (10 tasks or 7 days)
- `ERROR_DETECTED`: Triggered on error detection

---

### MarkdownSync

Auto-sync SQLite data to Markdown files.

#### Import

```python
from quickagents import MarkdownSync
```

#### Constructor

```python
sync = MarkdownSync(db: UnifiedDB, docs_dir: str = 'Docs')
```

#### Methods

```python
# Sync all tables
sync.sync_all() -> Dict[str, bool]

# Sync specific table
sync.sync_memory() -> bool
sync.sync_tasks() -> bool
sync.sync_decisions() -> bool
sync.sync_progress() -> bool

# Restore from Markdown
sync.restore_all_from_md() -> Dict[str, int]
```

---

### FileManager

Smart file operations with hash-based caching.

#### Import

```python
from quickagents import FileManager
```

#### Constructor

```python
fm = FileManager(cache_db: Optional[CacheDB] = None)
```

#### Methods

```python
# Read file with caching
fm.read(file_path: str) -> Tuple[str, bool]
# Returns: (content, from_cache)

# Write file
fm.write(file_path: str, content: str) -> bool

# Check if file changed
fm.has_changed(file_path: str) -> bool

# Get file hash
fm.get_hash(file_path: str) -> str

# Invalidate cache
fm.invalidate(file_path: str) -> None
```

---

### LoopDetector

Pattern-based loop detection.

#### Import

```python
from quickagents import LoopDetector
```

#### Constructor

```python
detector = LoopDetector(
    threshold: int = 3,
    window_size: int = 20,
    window_time: int = 60000
)
```

#### Methods

```python
# Record tool call
detector.record_tool_call(tool_name: str, tool_args: Dict) -> None

# Check if looping
detector.is_looping() -> bool

# Get loop patterns
detector.get_loop_patterns() -> List[Dict]

# Clear history
detector.clear() -> None
```

**Detection Logic:**
- **Stuck Pattern**: Same operation repeated 3+ times (A→A→A)
- **Oscillation Pattern**: Two operations alternating 2+ times (A→B→A→B)

---

### Reminder

Event-driven reminders.

#### Import

```python
from quickagents import Reminder
```

#### Constructor

```python
reminder = Reminder()
```

#### Methods

```python
# Record tool call
reminder.record_tool_call() -> None

# Check alerts
reminder.check_alerts() -> List[Dict]

# Get session duration
reminder.get_session_duration() -> int  # seconds
```

**Alert Types:**
- `TOOL_COUNT`: Every 5 tool calls
- `LONG_RUNNING`: At 10 and 30 minutes
- `ERROR_STREAK`: After 3 consecutive errors

---

## Knowledge Graph

### KnowledgeGraph

Main facade for knowledge graph operations.

#### Import

```python
from quickagents import KnowledgeGraph, NodeType, EdgeType
```

#### Constructor

```python
kg = KnowledgeGraph(db_path: Optional[str] = None)
```

#### Node Operations

```python
# Create node
node = kg.create_node(
    node_type: NodeType,
    title: str,
    content: Optional[str] = None,
    metadata: Optional[Dict] = None,
    tags: Optional[List[str]] = None
) -> KnowledgeNode

# Get node
kg.get_node(node_id: str) -> Optional[KnowledgeNode]

# Update node
kg.update_node(
    node_id: str,
    **updates
) -> bool

# Delete node
kg.delete_node(node_id: str, cascade: bool = False) -> bool

# List nodes
kg.list_nodes(
    node_type: Optional[NodeType] = None,
    limit: int = 50,
    offset: int = 0
) -> List[KnowledgeNode]
```

**NodeType Enum:**
- `REQUIREMENT`: Requirements
- `DECISION`: Design decisions
- `FEATURE`: Features
- `MODULE`: Modules
- `COMPONENT`: Components
- `API`: API endpoints
- `TEST`: Tests
- `BUG`: Bugs
- `LESSON`: Lessons learned
- `NOTE`: Notes

#### Edge Operations

```python
# Create edge
edge = kg.create_edge(
    source_id: str,
    target_id: str,
    edge_type: EdgeType,
    confidence: float = 1.0,
    evidence: Optional[List[str]] = None
) -> KnowledgeEdge

# Get edge
kg.get_edge(edge_id: str) -> Optional[KnowledgeEdge]

# Delete edge
kg.delete_edge(edge_id: str) -> bool

# Get relations
kg.get_outgoing_edges(node_id: str) -> List[KnowledgeEdge]
kg.get_incoming_edges(node_id: str) -> List[KnowledgeEdge]
```

**EdgeType Enum:**
- `TRACES_TO`: Traces to requirement
- `IMPLEMENTS`: Implements feature
- `DEPENDS_ON`: Depends on
- `TESTS`: Tests
- `BLOCKS`: Blocks
- `RELATES_TO`: Relates to
- `DERIVES_FROM`: Derives from
- `CONTAINS`: Contains

#### Search & Discovery

```python
# Search
results = kg.search(
    query: str,
    node_type: Optional[NodeType] = None,
    limit: int = 10
) -> List[SearchResult]

# Discover relations
relations = kg.discover_relations(
    node_id: str,
    strategies: Optional[List[str]] = None
) -> List[KnowledgeEdge]

# Find path
path = kg.find_path(
    source_id: str,
    target_id: str,
    max_depth: int = 5
) -> Optional[List[str]]

# Trace requirement
trace = kg.trace_requirement(node_id: str) -> List[KnowledgeNode]
```

**Discovery Strategies:**
- `direct`: Direct references
- `semantic`: Semantic similarity
- `structural`: Same feature/project
- `temporal`: Temporal proximity
- `transitive`: Transitive relations

#### Statistics

```python
# Get statistics
stats = kg.get_stats() -> Dict[str, Any]
```

---

## Skills Modules

### TDDWorkflow

Test-Driven Development workflow enforcement.

#### Import

```python
from quickagents import TDDWorkflow, TDDPhase
```

#### Constructor

```python
tdd = TDDWorkflow()
```

#### Methods

```python
# Start RED phase
tdd.start_red(test_name: str) -> Dict

# Complete RED phase
tdd.complete_red(test_name: str, test_code: str) -> bool

# Start GREEN phase
tdd.start_green(test_name: str) -> Dict

# Complete GREEN phase
tdd.complete_green(test_name: str, impl_code: str) -> bool

# Start REFACTOR phase
tdd.start_refactor(test_name: str) -> Dict

# Complete REFACTOR phase
tdd.complete_refactor(test_name: str) -> bool

# Get current phase
tdd.get_current_phase(test_name: str) -> Optional[TDDPhase]
```

**TDDPhase Enum:**
- `RED`: Write failing test
- `GREEN`: Make test pass
- `REFACTOR`: Improve code

---

### GitCommit

Standardized git commit management.

#### Import

```python
from quickagents import GitCommit
```

#### Methods

```python
# Validate commit message
GitCommit.validate_message(message: str) -> Tuple[bool, Optional[str]]

# Generate commit message
GitCommit.generate_message(
    change_type: str,
    scope: str,
    subject: str,
    body: Optional[str] = None,
    breaking: bool = False
) -> str

# Run pre-commit checks
GitCommit.run_pre_commit_checks() -> Tuple[bool, List[str]]
```

**Commit Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Refactoring
- `test`: Tests
- `chore`: Maintenance

---

### FeedbackCollector

Automatic feedback collection.

#### Import

```python
from quickagents import get_feedback_collector
```

#### Get Instance

```python
collector = get_feedback_collector()
```

#### Methods

```python
# Collect bug report
collector.collect_bug(
    description: str,
    error: Optional[str] = None,
    context: Optional[Dict] = None
) -> None

# Collect improvement
collector.collect_improvement(
    description: str,
    impact: str = 'medium'
) -> None

# Collect best practice
collector.collect_best_practice(
    description: str,
    category: str
) -> None
```

---

## Browser Automation

### Browser

Playwright-based browser automation.

#### Import

```python
from quickagents import Browser, BrowserBackend
```

#### Constructor

```python
browser = Browser(backend: BrowserBackend = BrowserBackend.CHROMIUM)
```

**BrowserBackend Enum:**
- `CHROMIUM`: Chromium (default)
- `LIGHTPANDA`: Lightpanda

#### Methods

```python
# New page
page = browser.new_page(url: Optional[str] = None) -> Page

# Get all pages
browser.get_pages() -> List[Page]

# Close
browser.close() -> None
```

### Page

Page object for browser automation.

#### Methods

```python
# Navigate
page.goto(url: str) -> None

# Get console logs
page.get_console_logs() -> List[ConsoleLog]

# Get network requests
page.get_network_requests() -> List[NetworkRequest]

# Execute JavaScript
page.evaluate(script: str) -> Any

# Screenshot
page.screenshot(path: str) -> None

# Close
page.close() -> None
```

---

## CLI Tools

### Main Commands

```bash
qa <command> [options]
```

**Available Commands:**

| Command | Description |
|---------|-------------|
| `stats` | Show database statistics |
| `sync` | Sync to Markdown |
| `progress` | Show current progress |
| `hooks install` | Install Git hooks |
| `hooks status` | Check Git hooks status |
| `evolution status` | Show evolution status |
| `evolution optimize` | Run optimization |
| `memory get <key>` | Get memory value |
| `memory set <key> <value>` | Set memory value |
| `memory search <query>` | Search memory |
| `tasks list` | List tasks |
| `tasks add <id> <name>` | Add task |
| `tasks status <id> <status>` | Update task status |
| `kg create-node` | Create knowledge node |
| `kg search <query>` | Search knowledge |
| `kg trace <id>` | Trace requirement |

---

## Utilities

### HashCache

Hash-based caching utility.

```python
from quickagents import HashCache

cache = HashCache()

# Get or compute
content = cache.get_or_compute(
    key: str,
    compute_fn: Callable
) -> Any

# Invalidate
cache.invalidate(key: str) -> None

# Clear
cache.clear() -> None
```

### ScriptHelper

Windows script helper (optional).

```python
from quickagents import ScriptHelper

helper = ScriptHelper()

# Execute script
result = helper.execute(script_path: str) -> Dict

# Create shortcut
helper.create_shortcut(
    target: str,
    shortcut_path: str
) -> bool
```

---

## Exceptions

### Knowledge Graph Exceptions

```python
from quickagents import (
    KnowledgeGraphError,      # Base exception
    NodeNotFoundError,        # Node not found
    EdgeNotFoundError,        # Edge not found
    DuplicateNodeError,       # Duplicate node
    DuplicateEdgeError,       # Duplicate edge
    InvalidNodeTypeError,     # Invalid node type
    InvalidEdgeTypeError,     # Invalid edge type
    CircularDependencyError,  # Circular dependency
    DatabaseIntegrityError,   # Database error
    ExtractionError,          # Extraction failed
    SyncError                 # Sync failed
)
```

---

## Type Definitions

### KnowledgeNode

```python
@dataclass
class KnowledgeNode:
    id: str
    node_type: NodeType
    title: str
    content: Optional[str]
    metadata: Dict[str, Any]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
```

### KnowledgeEdge

```python
@dataclass
class KnowledgeEdge:
    id: str
    source_id: str
    target_id: str
    edge_type: EdgeType
    confidence: float
    evidence: List[str]
    created_at: datetime
```

### SearchResult

```python
@dataclass
class SearchResult:
    node: KnowledgeNode
    score: float
    highlights: List[str]
```

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `QUICKAGENTS_DB_PATH` | Database path | `.quickagents/unified.db` |
| `QUICKAGENTS_DOCS_DIR` | Documentation directory | `Docs` |
| `QUICKAGENTS_EVOLUTION_ENABLED` | Enable evolution | `true` |
| `QUICKAGENTS_LOOP_THRESHOLD` | Loop detection threshold | `3` |
| `QUICKAGENTS_CACHE_ENABLED` | Enable caching | `true` |

---

## Migration Guide

### From 2.x to 2.7.0

1. **Update imports**: No changes required
2. **New LoopDetector**: Pattern-based detection is automatic
3. **Python version**: Requires Python 3.9+ (was 3.8+)

### Database Schema

```sql
-- Memory table
CREATE TABLE memory (
    key TEXT PRIMARY KEY,
    value TEXT,
    memory_type TEXT,
    category TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Tasks table
CREATE TABLE tasks (
    task_id TEXT PRIMARY KEY,
    name TEXT,
    priority TEXT,
    status TEXT,
    description TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Knowledge nodes
CREATE TABLE knowledge_nodes (
    id TEXT PRIMARY KEY,
    node_type TEXT,
    title TEXT,
    content TEXT,
    metadata TEXT,
    tags TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Knowledge edges
CREATE TABLE knowledge_edges (
    id TEXT PRIMARY KEY,
    source_id TEXT,
    target_id TEXT,
    edge_type TEXT,
    confidence REAL,
    evidence TEXT,
    created_at TIMESTAMP
);
```

---

**API Version**: 2.7.0
**Last Updated**: 2026-03-30
**Documentation**: https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM
