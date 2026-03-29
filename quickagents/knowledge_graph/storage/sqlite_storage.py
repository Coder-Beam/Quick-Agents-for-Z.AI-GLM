"""
SQLite Graph Storage

Implements GraphStorageInterface using SQLite with FTS5.
"""

import sqlite3
import json
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
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
        finally:
            conn.close()
    
    def _row_to_node(self, row: sqlite3.Row) -> KnowledgeNode:
        """Convert database row to KnowledgeNode."""
        tags = json.loads(row["tags"]) if row["tags"] else []
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        
        created_at = None
        if row["created_at"]:
            created_at = datetime.fromisoformat(row["created_at"])
        
        updated_at = None
        if row["updated_at"]:
            updated_at = datetime.fromisoformat(row["updated_at"])
        
        last_accessed_at = None
        if row["last_accessed_at"]:
            last_accessed_at = datetime.fromisoformat(row["last_accessed_at"])
        
        return KnowledgeNode(
            id=row["id"],
            node_type=NodeType(row["node_type"]),
            title=row["title"],
            content=row["content"],
            source_type=row["source_type"],
            source_uri=row["source_uri"],
            confidence=row["confidence"],
            importance=row["importance"],
            tags=tags,
            metadata=metadata,
            project_name=row["project_name"],
            feature_id=row["feature_id"],
            created_at=created_at,
            updated_at=updated_at,
            access_count=row["access_count"],
            last_accessed_at=last_accessed_at
        )
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize database schema."""
        if self._initialized:
            return True
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
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
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_type ON knowledge_nodes(node_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_project ON knowledge_nodes(project_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_feature ON knowledge_nodes(feature_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_importance ON knowledge_nodes(importance DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_nodes_created ON knowledge_nodes(created_at DESC)')
            
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
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_edges_source ON knowledge_edges(source_node_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_edges_target ON knowledge_edges(target_node_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_edges_type ON knowledge_edges(edge_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_edges_weight ON knowledge_edges(weight DESC)')
            
            cursor.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_index USING fts5(
                    node_id UNINDEXED,
                    title,
                    content,
                    tags,
                    source_uri,
                    tokenize='porter unicode61'
                )
            ''')
            
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS idx_node_insert 
                AFTER INSERT ON knowledge_nodes BEGIN
                    INSERT INTO knowledge_index(node_id, title, content, tags, source_uri)
                    VALUES (NEW.id, NEW.title, NEW.content, NEW.tags, NEW.source_uri);
                END
            ''')
            
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS idx_node_update 
                AFTER UPDATE ON knowledge_nodes BEGIN
                    UPDATE knowledge_index 
                    SET title=NEW.title, content=NEW.content, tags=NEW.tags, source_uri=NEW.source_uri
                    WHERE node_id=NEW.id;
                END
            ''')
            
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS idx_node_delete 
                AFTER DELETE ON knowledge_nodes BEGIN
                    DELETE FROM knowledge_index WHERE node_id=OLD.id;
                END
            ''')
            
            conn.commit()
        
        self._initialized = True
        return True
    
    def create_node(self, node: KnowledgeNode) -> KnowledgeNode:
        """Create a new knowledge node."""
        now = datetime.now()
        created_at = node.created_at or now
        updated_at = node.updated_at or now
        
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
                created_at.isoformat(),
                updated_at.isoformat(),
                node.access_count,
                node.last_accessed_at.isoformat() if node.last_accessed_at else None
            ))
            conn.commit()
        
        return self.get_node(node.id)
    
    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Get a knowledge node by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM knowledge_nodes WHERE id = ?",
                (node_id,)
            )
            row = cursor.fetchone()
            
            if row is None:
                return None
            
            return self._row_to_node(row)
    
    def update_node(self, node_id: str, updates: Dict[str, Any]) -> KnowledgeNode:
        """Update a knowledge node."""
        if not updates:
            return self.get_node(node_id)
        
        valid_fields = {
            'node_type', 'title', 'content', 'source_type', 'source_uri',
            'confidence', 'importance', 'tags', 'metadata', 'project_name',
            'feature_id', 'access_count', 'last_accessed_at'
        }
        
        filtered_updates = {k: v for k, v in updates.items() if k in valid_fields}
        
        if not filtered_updates:
            return self.get_node(node_id)
        
        filtered_updates['updated_at'] = datetime.now()
        
        set_clauses = []
        values = []
        
        for field, value in filtered_updates.items():
            if field in ('tags', 'metadata'):
                set_clauses.append(f"{field} = ?")
                values.append(json.dumps(value) if value else None)
            elif field == 'node_type':
                set_clauses.append(f"{field} = ?")
                values.append(value.value if hasattr(value, 'value') else value)
            elif field in ('created_at', 'updated_at', 'last_accessed_at'):
                set_clauses.append(f"{field} = ?")
                values.append(value.isoformat() if value else None)
            else:
                set_clauses.append(f"{field} = ?")
                values.append(value)
        
        values.append(node_id)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE knowledge_nodes SET {', '.join(set_clauses)} WHERE id = ?",
                values
            )
            conn.commit()
            
            if cursor.rowcount == 0:
                raise NodeNotFoundError(node_id)
        
        return self.get_node(node_id)
    
    def delete_node(self, node_id: str, cascade: bool = True) -> bool:
        """Delete a knowledge node."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM knowledge_nodes WHERE id = ?", (node_id,))
            conn.commit()
            
            return cursor.rowcount > 0
    
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
