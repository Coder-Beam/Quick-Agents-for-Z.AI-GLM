"""
MigrationManager - 迁移管理器

核心功能:
- Schema 版本管理
- 迁移历史记录
- 回滚支持
- 校验和验证
- 内置迁移

设计原则:
- 单一职责：仅负责数据库迁移
- 依赖注入：通过构造函数接收 ConnectionManager
- 安全迁移：支持回滚和校验
"""

import logging
import hashlib
from typing import List, Optional
from dataclasses import dataclass

from .connection_manager import ConnectionManager

logger = logging.getLogger(__name__)


@dataclass
class Migration:
    """
    迁移定义
    
    Attributes:
        version: 版本号（如 "001", "002"）
        name: 迁移名称
        up_sql: 升级 SQL
        down_sql: 降级 SQL
        checksum: 校验和（自动计算）
    """
    version: str
    name: str
    up_sql: str
    down_sql: str
    
    def __post_init__(self):
        """初始化后计算校验和"""
        self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """
        计算校验和
        
        Returns:
            str: 16位校验和
        """
        content = f"{self.version}:{self.name}:{self.up_sql}:{self.down_sql}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class MigrationManager:
    """
    迁移管理器
    
    使用方式:
        mig_mgr = MigrationManager(conn_mgr)
        
        # 执行待处理的迁移
        mig_mgr.migrate()
        
        # 检查迁移状态
        pending = mig_mgr.get_pending_migrations()
    
    内置迁移:
        - 001: 初始 Schema（memory, tasks, progress, feedback, migration_history, operation_history）
        - 002: 添加 memory.content_hash 字段
    """
    
    # 内置迁移列表
    BUILTIN_MIGRATIONS: List[Migration] = []
    
    def __init__(self, connection_manager: ConnectionManager):
        """
        初始化迁移管理器
        
        Args:
            connection_manager: 连接管理器
        """
        self.conn_mgr = connection_manager
        self.migrations = self.BUILTIN_MIGRATIONS.copy()
        
        # 初始化内置迁移
        self._init_builtin_migrations()
    
    def _init_builtin_migrations(self) -> None:
        """初始化内置迁移"""
        # 迁移 001: 初始 Schema
        migration_001 = Migration(
            version="001",
            name="initial_schema",
            up_sql="""
                -- ==================== 记忆表 ====================
                CREATE TABLE IF NOT EXISTS memory (
                    id TEXT PRIMARY KEY,
                    memory_type TEXT NOT NULL,
                    category TEXT,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    importance_score REAL DEFAULT 0.5,
                    access_count INTEGER DEFAULT 0,
                    last_accessed_at REAL,
                    created_at REAL DEFAULT (strftime('%s', 'now')),
                    updated_at REAL DEFAULT (strftime('%s', 'now')),
                    metadata TEXT,
                    UNIQUE(key, memory_type, category)
                );
                
                -- 记忆索引
                CREATE INDEX IF NOT EXISTS idx_memory_type ON memory(memory_type);
                CREATE INDEX IF NOT EXISTS idx_memory_category ON memory(category);
                CREATE INDEX IF NOT EXISTS idx_memory_key ON memory(key);
                CREATE INDEX IF NOT EXISTS idx_memory_importance ON memory(importance_score);
                CREATE INDEX IF NOT EXISTS idx_memory_created ON memory(created_at);
                
                -- ==================== 任务表 ====================
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    priority TEXT DEFAULT 'P2',
                    status TEXT DEFAULT 'pending',
                    assignee TEXT,
                    start_time REAL,
                    end_time REAL,
                    created_at REAL DEFAULT (strftime('%s', 'now')),
                    updated_at REAL DEFAULT (strftime('%s', 'now')),
                    metadata TEXT
                );
                
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
                CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
                
                -- ==================== 进度表 ====================
                CREATE TABLE IF NOT EXISTS progress (
                    id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL UNIQUE,
                    current_task TEXT,
                    total_tasks INTEGER DEFAULT 0,
                    completed_tasks INTEGER DEFAULT 0,
                    last_checkpoint TEXT,
                    created_at REAL DEFAULT (strftime('%s', 'now')),
                    updated_at REAL DEFAULT (strftime('%s', 'now'))
                );
                
                -- ==================== 反馈表 ====================
                CREATE TABLE IF NOT EXISTS feedback (
                    id TEXT PRIMARY KEY,
                    feedback_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    project_name TEXT,
                    metadata TEXT,
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                );
                
                CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(feedback_type);
                CREATE INDEX IF NOT EXISTS idx_feedback_project ON feedback(project_name);
                
                -- ==================== 迁移历史表 ====================
                CREATE TABLE IF NOT EXISTS migration_history (
                    version TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    applied_at REAL DEFAULT (strftime('%s', 'now'))
                );
                
                -- ==================== 操作历史表 ====================
                CREATE TABLE IF NOT EXISTS operation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_type TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    record_id TEXT,
                    operation_data TEXT,
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                );
                
                CREATE INDEX IF NOT EXISTS idx_op_history_type ON operation_history(operation_type);
                CREATE INDEX IF NOT EXISTS idx_op_history_table ON operation_history(table_name);
                CREATE INDEX IF NOT EXISTS idx_op_history_time ON operation_history(created_at);
            """,
            down_sql="""
                DROP TABLE IF EXISTS memory;
                DROP TABLE IF EXISTS tasks;
                DROP TABLE IF EXISTS progress;
                DROP TABLE IF EXISTS feedback;
                DROP TABLE IF EXISTS migration_history;
                DROP TABLE IF EXISTS operation_history;
            """
        )
        migration_001.__post_init__()
        
        # 迁移 002: 添加 memory.content_hash 字段
        migration_002 = Migration(
            version="002",
            name="add_memory_hash",
            up_sql="""
                ALTER TABLE memory ADD COLUMN content_hash TEXT;
                CREATE INDEX IF NOT EXISTS idx_memory_hash ON memory(content_hash);
            """,
            down_sql="""
                -- SQLite 不支持 DROP COLUMN，保留字段
                -- 如需回滚，需要重建表
            """
        )
        migration_002.__post_init__()
        
        self.migrations = [migration_001, migration_002]
    
    def register_migration(self, migration: Migration) -> None:
        """
        注册自定义迁移
        
        Args:
            migration: 迁移对象
        """
        migration.__post_init__()
        self.migrations.append(migration)
        self.migrations.sort(key=lambda m: m.version)
        logger.info(f"Registered migration: {migration.version} - {migration.name}")
    
    def get_applied_migrations(self) -> List[str]:
        """
        获取已应用的迁移版本列表
        
        Returns:
            List[str]: 已应用的迁移版本号
        """
        try:
            with self.conn_mgr.get_connection() as conn:
                # 检查 migration_history 表是否存在
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='migration_history'"
                )
                if cursor.fetchone() is None:
                    return []
                
                cursor = conn.execute(
                    "SELECT version FROM migration_history ORDER BY version"
                )
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get applied migrations: {e}")
            return []
    
    def get_pending_migrations(self) -> List[Migration]:
        """
        获取待应用的迁移列表
        
        Returns:
            List[Migration]: 待应用的迁移
        """
        applied = set(self.get_applied_migrations())
        pending = [m for m in self.migrations if m.version not in applied]
        return pending
    
    def migrate(self) -> int:
        """
        执行所有待处理的迁移
        
        Returns:
            int: 应用的迁移数量
        """
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("No pending migrations")
            return 0
        
        applied_count = 0
        
        for migration in pending:
            logger.info(f"Applying migration: {migration.version} - {migration.name}")
            
            try:
                with self.conn_mgr.get_connection() as conn:
                    # 执行迁移 SQL
                    conn.executescript(migration.up_sql)
                    
                    # 记录迁移历史
                    conn.execute(
                        """
                        INSERT INTO migration_history (version, name, checksum)
                        VALUES (?, ?, ?)
                        """,
                        (migration.version, migration.name, migration.checksum)
                    )
                    
                    conn.commit()
                    applied_count += 1
                    logger.info(f"Migration applied successfully: {migration.version}")
                    
            except Exception as e:
                logger.error(f"Migration failed: {migration.version} - {e}")
                raise RuntimeError(f"Migration {migration.version} failed: {e}") from e
        
        logger.info(f"Applied {applied_count} migration(s)")
        return applied_count
    
    def rollback(self, version: str) -> bool:
        """
        回滚指定版本的迁移
        
        Args:
            version: 要回滚的版本号
        
        Returns:
            bool: 是否成功
        """
        migration = next(
            (m for m in self.migrations if m.version == version),
            None
        )
        
        if migration is None:
            logger.error(f"Migration not found: {version}")
            return False
        
        try:
            with self.conn_mgr.get_connection() as conn:
                # 执行降级 SQL
                conn.executescript(migration.down_sql)
                
                # 删除迁移记录
                conn.execute(
                    "DELETE FROM migration_history WHERE version = ?",
                    (version,)
                )
                
                conn.commit()
                logger.info(f"Migration rolled back: {version}")
                return True
                
        except Exception as e:
            logger.error(f"Rollback failed: {version} - {e}")
            return False
    
    def verify_checksums(self) -> bool:
        """
        验证所有已应用迁移的校验和
        
        Returns:
            bool: 是否全部通过
        """
        try:
            with self.conn_mgr.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT version, checksum FROM migration_history"
                )
                applied = {row[0]: row[1] for row in cursor.fetchall()}
        except Exception as e:
            logger.error(f"Failed to verify checksums: {e}")
            return False
        
        all_valid = True
        
        for migration in self.migrations:
            if migration.version in applied:
                if applied[migration.version] != migration.checksum:
                    logger.error(
                        f"Checksum mismatch for migration {migration.version}: "
                        f"expected {migration.checksum}, got {applied[migration.version]}"
                    )
                    all_valid = False
                else:
                    logger.debug(f"Checksum valid: {migration.version}")
        
        if all_valid:
            logger.info("All migration checksums verified")
        else:
            logger.warning("Some migration checksums are invalid")
        
        return all_valid
    
    def get_migration_status(self) -> dict:
        """
        获取迁移状态
        
        Returns:
            dict: 迁移状态信息
        """
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()
        
        return {
            "total_migrations": len(self.migrations),
            "applied_count": len(applied),
            "pending_count": len(pending),
            "applied_versions": applied,
            "pending_versions": [m.version for m in pending]
        }
    
    def __repr__(self) -> str:
        status = self.get_migration_status()
        return (
            f"MigrationManager(total={status['total_migrations']}, "
            f"applied={status['applied_count']}, "
            f"pending={status['pending_count']})"
        )
