# UnifiedDB V2 深度设计方案

> 版本: 2.0.0  
> 创建时间: 2026-03-31  
> 状态: 设计评审  
> 参考: Cortex Memory, MemGPT, Zep, LangMem, Mem0

---

## 目录

1. [调研总结](#1-调研总结)
2. [现状分析](#2-现状分析)
3. [设计目标](#3-设计目标)
4. [架构设计](#4-架构设计)
5. [核心组件](#5-核心组件)
6. [数据模型](#6-数据模型)
7. [API 设计](#7-api-设计)
8. [性能优化](#8-性能优化)
9. [测试策略](#9-测试策略)
10. [实施计划](#10-实施计划)

---

## 1. 调研总结

### 1.1 行业最佳实践

| 项目 | 语言 | 核心特性 | 借鉴点 |
|------|------|----------|--------|
| **Cortex Memory** | Rust | 分层架构 + 依赖注入 + Trait抽象 | Repository模式、组件化设计 |
| **MemGPT** | Python | OS-inspired内存管理 | Core/Archival分层、自管理 |
| **Zep** | Go | 时序知识图谱 | 双时序建模、事实过期 |
| **Mem0** | Python | 三重后端存储 | Vector+KV+Graph、自动去重 |
| **LangMem** | Python | 过程记忆 | 自修改系统提示、技能学习 |

### 1.2 核心问题识别

| 问题 | 影响 | 现有方案 |
|------|------|----------|
| **Context Poisoning** | 错误信息自我强化 | 质量评分 + LLM验证 |
| **Context Distraction** | 信号被噪音淹没 | 分层路由 + 重要性评分 |
| **Context Clash** | 矛盾信息共存 | 时序建模 + 冲突解决 |
| **Work Duplication** | 多Agent重复工作 | 共享内存 + 事件溯源 |
| **Memory Pollution** | 低价值记忆堆积 | 选择性遗忘 + RIF评分 |

### 1.3 四种记忆类型

| 类型 | 用途 | 存储方式 | 持久性 |
|------|------|----------|--------|
| **Working Memory** | 当前活跃状态 | 内存 | 会话级 |
| **Episodic Memory** | 历史交互记录 | Vector DB | 永久 |
| **Semantic Memory** | 事实知识 | Vector + Graph | 永久 |
| **Procedural Memory** | 技能/流程 | 结构化存储 | 永久 |

---

## 2. 现状分析

### 2.1 当前 UnifiedDB 问题

```python
# 当前问题清单
ISSUES = {
    "架构问题": [
        "缺少统一抽象层，直接操作 SQL",
        "各表独立，缺少关联管理",
        "无事务支持，数据一致性风险",
        "无迁移系统，版本升级困难"
    ],
    "API问题": [
        "API 不一致，难用难记",
        "缺少类型提示",
        "错误处理不统一",
        "缺少批量操作"
    ],
    "性能问题": [
        "无索引优化",
        "无查询优化",
        "无缓存机制",
        "无连接池"
    ],
    "功能缺失": [
        "无语义检索",
        "无重要性评分",
        "无自动去重",
        "无遗忘机制"
    ]
}
```

### 2.2 与 MemoryManager 功能重叠

| 功能 | UnifiedDB | MemoryManager | 建议处理 |
|------|-----------|---------------|----------|
| 记忆存储 | ✅ | ✅ | 合并到 UnifiedDB |
| 记忆检索 | ✅ | ✅ | 合并到 UnifiedDB |
| 记忆分类 | 部分 | ✅ | 合并到 UnifiedDB |
| Markdown同步 | ❌ | ✅ | 保留为适配器 |

---

## 3. 设计目标

### 3.1 功能目标

| 目标 | 说明 | 优先级 |
|------|------|--------|
| **统一数据访问层** | Repository 模式，统一 API | P0 |
| **事务支持** | ACID 事务，数据一致性 | P0 |
| **分层存储** | Working/Episodic/Semantic/Procedural | P0 |
| **智能检索** | 多信号评分：相关性+时序+重要性 | P0 |
| **自动去重** | 哈希+语义+LLM验证 | P1 |
| **选择性遗忘** | RIF评分 + 时序衰减 | P1 |
| **迁移系统** | Schema 版本管理 | P1 |
| **语义检索** | 可选嵌入支持 | P2 |

### 3.2 非功能目标

| 目标 | 指标 | 说明 |
|------|------|------|
| **性能** | 查询 < 10ms | 本地 SQLite |
| **可靠性** | 100% 测试覆盖 | 所有代码 |
| **可扩展** | 插件式组件 | 依赖注入 |
| **易用性** | 统一 API | Repository 模式 |

### 3.3 验收标准

| 维度 | 标准 |
|------|------|
| **功能验收** | 所有 Repository 方法正常工作 |
| **性能验收** | 单次查询 < 10ms，批量操作 < 100ms |
| **质量验收** | **100% 测试覆盖率** |
| **文档验收** | API 文档 + 使用示例 |

---

## 4. 架构设计

### 4.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     UnifiedDB V2 架构                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Access Layer                          │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │    │
│  │  │   CLI   │  │REST API │  │   SDK   │  │   MCP   │    │    │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  Business Logic Layer                    │    │
│  │  ┌─────────────────────────────────────────────────┐    │    │
│  │  │              UnifiedDB (Facade)                  │    │    │
│  │  └─────────────────────────────────────────────────┘    │    │
│  │                          │                               │    │
│  │  ┌──────────┬──────────┬──────────┬──────────┐         │    │
│  │  │ Memory   │  Task    │ Progress │Feedback  │         │    │
│  │  │Repository│Repository│Repository│Repository│         │    │
│  │  └──────────┴──────────┴──────────┴──────────┘         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                   Processing Layer                       │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │    │
│  │  │Importance│ │Duplicate │ │ Conflict │ │  Forget  │   │    │
│  │  │ Evaluator│ │ Detector │ │ Resolver │ │  Manager │   │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Storage Layer                         │    │
│  │  ┌──────────────────────────────────────────────────┐   │    │
│  │  │          ConnectionManager + TransactionManager  │   │    │
│  │  └──────────────────────────────────────────────────┘   │    │
│  │                          │                               │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │    │
│  │  │  SQLite  │ │ Markdown │ │  Vector  │ │  Cache   │   │    │
│  │  │  (Core)  │ │  Adapter │ │(Optional)│ │ (LRU)    │   │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 设计原则

| 原则 | 说明 | 实现 |
|------|------|------|
| **单一职责** | 每个组件只做一件事 | Repository 分离 |
| **依赖注入** | 组件通过接口组合 | 构造函数注入 |
| **开闭原则** | 对扩展开放，对修改关闭 | Trait/Protocol 抽象 |
| **接口隔离** | 接口最小化 | 专用 Repository |
| **依赖倒置** | 依赖抽象，不依赖具体 | Protocol 定义 |

---

## 5. 核心组件

### 5.1 ConnectionManager

```python
from typing import Protocol, Optional, ContextManager
from contextlib import contextmanager
import sqlite3
from threading import Lock
import logging

logger = logging.getLogger(__name__)


class ConnectionProtocol(Protocol):
    """连接协议"""
    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor: ...
    def executemany(self, sql: str, params: list) -> sqlite3.Cursor: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def close(self) -> None: ...


class ConnectionManager:
    """
    连接管理器
    
    功能:
    - 连接池管理
    - 线程安全
    - 自动重连
    - 连接健康检查
    """
    
    def __init__(
        self, 
        db_path: str = ".quickagents/unified.db",
        pool_size: int = 5,
        timeout: float = 30.0
    ):
        self.db_path = db_path
        self.pool_size = pool_size
        self.timeout = timeout
        self._lock = Lock()
        self._pool: list[sqlite3.Connection] = []
        self._active_connections: set[sqlite3.Connection] = set()
        
        # 初始化连接池
        self._init_pool()
    
    def _init_pool(self):
        """初始化连接池"""
        for _ in range(self.pool_size):
            conn = self._create_connection()
            self._pool.append(conn)
    
    def _create_connection(self) -> sqlite3.Connection:
        """创建新连接"""
        conn = sqlite3.connect(
            self.db_path,
            timeout=self.timeout,
            check_same_thread=False
        )
        # 启用外键约束
        conn.execute("PRAGMA foreign_keys = ON")
        # 启用 WAL 模式
        conn.execute("PRAGMA journal_mode = WAL")
        # 设置超时
        conn.execute(f"PRAGMA busy_timeout = {int(self.timeout * 1000)}")
        return conn
    
    @contextmanager
    def get_connection(self) -> ContextManager[ConnectionProtocol]:
        """获取连接（上下文管理器）"""
        conn = self._acquire()
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        finally:
            self._release(conn)
    
    def _acquire(self) -> sqlite3.Connection:
        """获取连接"""
        with self._lock:
            if self._pool:
                conn = self._pool.pop()
            else:
                conn = self._create_connection()
            self._active_connections.add(conn)
            return conn
    
    def _release(self, conn: sqlite3.Connection):
        """释放连接"""
        with self._lock:
            if conn in self._active_connections:
                self._active_connections.remove(conn)
                if len(self._pool) < self.pool_size:
                    self._pool.append(conn)
                else:
                    conn.close()
    
    def close_all(self):
        """关闭所有连接"""
        with self._lock:
            for conn in self._pool:
                try:
                    conn.close()
                except Exception as e:
                    logger.warning(f"关闭连接失败: {e}")
            self._pool.clear()
            
            for conn in self._active_connections:
                try:
                    conn.close()
                except Exception as e:
                    logger.warning(f"关闭活动连接失败: {e}")
            self._active_connections.clear()
```

### 5.2 TransactionManager

```python
from typing import Protocol, Optional, Callable, TypeVar, Any
from contextlib import contextmanager
import logging
import functools

logger = logging.getLogger(__name__)
T = TypeVar('T')


class TransactionManager:
    """
    事务管理器
    
    功能:
    - ACID 事务支持
    - 嵌套事务 (SAVEPOINT)
    - 自动提交/回滚
    - 事务隔离级别
    """
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self._transaction_depth = 0
    
    @contextmanager
    def transaction(self):
        """
        事务上下文管理器
        
        使用方式:
            with tx_manager.transaction():
                # 数据库操作
                pass
        """
        conn = self.connection_manager._acquire()
        try:
            if self._transaction_depth == 0:
                # 开始新事务
                conn.execute("BEGIN")
            else:
                # 嵌套事务使用 SAVEPOINT
                conn.execute(f"SAVEPOINT sp_{self._transaction_depth}")
            
            self._transaction_depth += 1
            
            try:
                yield conn
                # 成功则提交
                if self._transaction_depth == 1:
                    conn.commit()
            except Exception as e:
                # 失败则回滚
                if self._transaction_depth == 1:
                    conn.rollback()
                    logger.error(f"事务回滚: {e}")
                else:
                    conn.execute(f"ROLLBACK TO SAVEPOINT sp_{self._transaction_depth - 1}")
                raise
        finally:
            self._transaction_depth -= 1
            self.connection_manager._release(conn)
    
    def atomic(func: Callable[..., T]) -> Callable[..., T]:
        """
        原子操作装饰器
        
        使用方式:
            @atomic
            def my_operation():
                # 数据库操作
                pass
        """
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs) -> T:
            with self.transaction():
                return func(self, *args, **kwargs)
        return wrapper
```

### 5.3 MigrationManager

```python
from typing import List, Dict, Optional
import hashlib
import json
from datetime import datetime


class Migration:
    """迁移定义"""
    
    def __init__(
        self,
        version: str,
        name: str,
        up_sql: str,
        down_sql: str
    ):
        self.version = version
        self.name = name
        self.up_sql = up_sql
        self.down_sql = down_sql
        self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """计算校验和"""
        content = f"{self.version}:{self.name}:{self.up_sql}:{self.down_sql}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class MigrationManager:
    """
    迁移管理器
    
    功能:
    - Schema 版本管理
    - 迁移历史记录
    - 回滚支持
    - 校验和验证
    """
    
    # 内置迁移
    BUILTIN_MIGRATIONS: List[Migration] = [
        Migration(
            version="001",
            name="initial_schema",
            up_sql="""
                -- 记忆表
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
                
                -- 任务表
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
                
                -- 进度表
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
                
                -- 反馈表
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
                
                -- 迁移历史表
                CREATE TABLE IF NOT EXISTS migration_history (
                    version TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    checksum TEXT NOT NULL,
                    applied_at REAL DEFAULT (strftime('%s', 'now'))
                );
                
                -- 操作历史表
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
        ),
        Migration(
            version="002",
            name="add_memory_hash",
            up_sql="""
                ALTER TABLE memory ADD COLUMN content_hash TEXT;
                CREATE INDEX IF NOT EXISTS idx_memory_hash ON memory(content_hash);
            """,
            down_sql="""
                -- SQLite 不支持 DROP COLUMN，保留字段
            """
        )
    ]
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.migrations = self.BUILTIN_MIGRATIONS.copy()
    
    def register_migration(self, migration: Migration):
        """注册迁移"""
        self.migrations.append(migration)
        self.migrations.sort(key=lambda m: m.version)
    
    def get_applied_migrations(self) -> List[str]:
        """获取已应用的迁移版本"""
        with self.connection_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT version FROM migration_history ORDER BY version"
            )
            return [row[0] for row in cursor.fetchall()]
    
    def get_pending_migrations(self) -> List[Migration]:
        """获取待应用的迁移"""
        applied = set(self.get_applied_migrations())
        return [m for m in self.migrations if m.version not in applied]
    
    def migrate(self):
        """执行迁移"""
        pending = self.get_pending_migrations()
        
        if not pending:
            logger.info("没有待应用的迁移")
            return
        
        for migration in pending:
            logger.info(f"应用迁移: {migration.version} - {migration.name}")
            
            with self.connection_manager.get_connection() as conn:
                try:
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
                    logger.info(f"迁移成功: {migration.version}")
                    
                except Exception as e:
                    conn.rollback()
                    logger.error(f"迁移失败: {migration.version} - {e}")
                    raise
    
    def verify_checksums(self) -> bool:
        """验证迁移校验和"""
        with self.connection_manager.get_connection() as conn:
            cursor = conn.execute(
                "SELECT version, checksum FROM migration_history"
            )
            applied = {row[0]: row[1] for row in cursor.fetchall()}
        
        for migration in self.migrations:
            if migration.version in applied:
                if applied[migration.version] != migration.checksum:
                    logger.error(
                        f"校验和不匹配: {migration.version}"
                    )
                    return False
        
        return True
```

---

## 6. 数据模型

### 6.1 基础模型

```python
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class MemoryType(Enum):
    """记忆类型"""
    FACTUAL = "factual"           # 事实记忆
    EXPERIENTIAL = "experiential"  # 经验记忆
    WORKING = "working"           # 工作记忆


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class TaskPriority(Enum):
    """任务优先级"""
    P0 = "P0"  # 紧急
    P1 = "P1"  # 高
    P2 = "P2"  # 中
    P3 = "P3"  # 低


class FeedbackType(Enum):
    """反馈类型"""
    BUG = "bug"
    IMPROVEMENT = "improvement"
    BEST_PRACTICE = "best_practice"
    PITFALL = "pitfall"
    QUESTION = "question"


@dataclass
class Memory:
    """记忆实体"""
    id: str
    memory_type: MemoryType
    key: str
    value: str
    category: Optional[str] = None
    importance_score: float = 0.5
    access_count: int = 0
    last_accessed_at: Optional[float] = None
    created_at: float = field(default_factory=lambda: time.time())
    updated_at: float = field(default_factory=lambda: time.time())
    metadata: Dict[str, Any] = field(default_factory=dict)
    content_hash: Optional[str] = None
    
    def touch(self):
        """更新访问时间和计数"""
        self.access_count += 1
        self.last_accessed_at = time.time()
    
    def calculate_hash(self) -> str:
        """计算内容哈希"""
        import hashlib
        content = f"{self.key}:{self.value}:{self.category or ''}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class Task:
    """任务实体"""
    id: str
    name: str
    priority: TaskPriority = TaskPriority.P2
    status: TaskStatus = TaskStatus.PENDING
    assignee: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    created_at: float = field(default_factory=lambda: time.time())
    updated_at: float = field(default_factory=lambda: time.time())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Progress:
    """进度实体"""
    id: str
    project_name: str
    current_task: Optional[str] = None
    total_tasks: int = 0
    completed_tasks: int = 0
    last_checkpoint: Optional[str] = None
    created_at: float = field(default_factory=lambda: time.time())
    updated_at: float = field(default_factory=lambda: time.time())
    
    @property
    def percentage(self) -> float:
        """完成百分比"""
        if self.total_tasks == 0:
            return 0.0
        return (self.completed_tasks / self.total_tasks) * 100


@dataclass
class Feedback:
    """反馈实体"""
    id: str
    feedback_type: FeedbackType
    title: str
    description: Optional[str] = None
    project_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=lambda: time.time())


@dataclass
class OperationHistory:
    """操作历史实体"""
    id: int
    operation_type: str
    table_name: str
    record_id: Optional[str] = None
    operation_data: Optional[str] = None
    created_at: float = field(default_factory=lambda: time.time())
```

### 6.2 检索结果模型

```python
@dataclass
class SearchResult:
    """检索结果"""
    memory: Memory
    relevance_score: float      # 相关性分数
    recency_score: float        # 时序分数
    importance_score: float     # 重要性分数
    final_score: float          # 综合分数
    
    @classmethod
    def calculate_final_score(
        cls,
        relevance: float,
        recency: float,
        importance: float,
        weights: Dict[str, float] = None
    ) -> float:
        """
        计算综合分数
        
        公式: S = α·R + β·γ + δ·I
        - R: 相关性 (cosine similarity)
        - γ: 时序衰减 (e^(-λ·t))
        - I: 重要性 (importance_score)
        - α, β, δ: 权重系数
        """
        w = weights or {
            'relevance': 0.5,
            'recency': 0.3,
            'importance': 0.2
        }
        
        return (
            w['relevance'] * relevance +
            w['recency'] * recency +
            w['importance'] * importance
        )


@dataclass
class RetrievalConfig:
    """检索配置"""
    # 权重配置
    relevance_weight: float = 0.5
    recency_weight: float = 0.3
    importance_weight: float = 0.2
    
    # 时序衰减
    decay_rate: float = 0.995  # γ (0.99-0.999)
    
    # 检索限制
    max_results: int = 10
    
    # 最小分数阈值
    min_score: float = 0.3
```

---

## 7. API 设计

### 7.1 Repository 基类

```python
from typing import Protocol, TypeVar, Generic, List, Optional, Dict, Any
from abc import ABC, abstractmethod

T = TypeVar('T')


class Repository(Protocol, Generic[T]):
    """Repository 协议"""
    
    def get(self, id: str) -> Optional[T]:
        """根据 ID 获取实体"""
        ...
    
    def get_all(self, filters: Dict[str, Any] = None) -> List[T]:
        """获取所有实体（支持过滤）"""
        ...
    
    def add(self, entity: T) -> T:
        """添加实体"""
        ...
    
    def update(self, entity: T) -> T:
        """更新实体"""
        ...
    
    def delete(self, id: str) -> bool:
        """删除实体"""
        ...
    
    def exists(self, id: str) -> bool:
        """检查实体是否存在"""
        ...


class BaseRepository(ABC, Generic[T]):
    """Repository 基类"""
    
    def __init__(
        self,
        connection_manager: ConnectionManager,
        transaction_manager: TransactionManager
    ):
        self.conn_mgr = connection_manager
        self.tx_mgr = transaction_manager
    
    @property
    @abstractmethod
    def table_name(self) -> str:
        """表名"""
        pass
    
    @abstractmethod
    def _row_to_entity(self, row: tuple) -> T:
        """行转实体"""
        pass
    
    @abstractmethod
    def _entity_to_dict(self, entity: T) -> Dict[str, Any]:
        """实体转字典"""
        pass
    
    def get(self, id: str) -> Optional[T]:
        """根据 ID 获取实体"""
        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(
                f"SELECT * FROM {self.table_name} WHERE id = ?",
                (id,)
            )
            row = cursor.fetchone()
            return self._row_to_entity(row) if row else None
    
    def get_all(
        self,
        filters: Dict[str, Any] = None,
        order_by: str = None,
        limit: int = None
    ) -> List[T]:
        """获取所有实体"""
        sql = f"SELECT * FROM {self.table_name}"
        params = []
        
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            sql += " WHERE " + " AND ".join(conditions)
        
        if order_by:
            sql += f" ORDER BY {order_by}"
        
        if limit:
            sql += f" LIMIT {limit}"
        
        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(sql, params)
            return [self._row_to_entity(row) for row in cursor.fetchall()]
    
    def exists(self, id: str) -> bool:
        """检查实体是否存在"""
        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(
                f"SELECT 1 FROM {self.table_name} WHERE id = ?",
                (id,)
            )
            return cursor.fetchone() is not None
    
    def count(self, filters: Dict[str, Any] = None) -> int:
        """计数"""
        sql = f"SELECT COUNT(*) FROM {self.table_name}"
        params = []
        
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(f"{key} = ?")
                params.append(value)
            sql += " WHERE " + " AND ".join(conditions)
        
        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(sql, params)
            return cursor.fetchone()[0]
```

### 7.2 MemoryRepository

```python
import time
import json
from typing import List, Optional, Dict, Any


class MemoryRepository(BaseRepository[Memory]):
    """记忆仓储"""
    
    @property
    def table_name(self) -> str:
        return "memory"
    
    def _row_to_entity(self, row: tuple) -> Memory:
        return Memory(
            id=row[0],
            memory_type=MemoryType(row[1]),
            category=row[2],
            key=row[3],
            value=row[4],
            importance_score=row[5],
            access_count=row[6],
            last_accessed_at=row[7],
            created_at=row[8],
            updated_at=row[9],
            metadata=json.loads(row[10]) if row[10] else {},
            content_hash=row[11]
        )
    
    def _entity_to_dict(self, entity: Memory) -> Dict[str, Any]:
        return {
            'id': entity.id,
            'memory_type': entity.memory_type.value,
            'category': entity.category,
            'key': entity.key,
            'value': entity.value,
            'importance_score': entity.importance_score,
            'access_count': entity.access_count,
            'last_accessed_at': entity.last_accessed_at,
            'created_at': entity.created_at,
            'updated_at': entity.updated_at,
            'metadata': json.dumps(entity.metadata, ensure_ascii=False),
            'content_hash': entity.content_hash
        }
    
    def add(self, memory: Memory) -> Memory:
        """添加记忆"""
        memory.content_hash = memory.calculate_hash()
        memory.created_at = time.time()
        memory.updated_at = time.time()
        
        data = self._entity_to_dict(memory)
        
        with self.conn_mgr.get_connection() as conn:
            conn.execute(
                f"""
                INSERT INTO memory (
                    id, memory_type, category, key, value,
                    importance_score, access_count, last_accessed_at,
                    created_at, updated_at, metadata, content_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data['id'], data['memory_type'], data['category'],
                    data['key'], data['value'], data['importance_score'],
                    data['access_count'], data['last_accessed_at'],
                    data['created_at'], data['updated_at'],
                    data['metadata'], data['content_hash']
                )
            )
            conn.commit()
        
        return memory
    
    def update(self, memory: Memory) -> Memory:
        """更新记忆"""
        memory.updated_at = time.time()
        data = self._entity_to_dict(memory)
        
        with self.conn_mgr.get_connection() as conn:
            conn.execute(
                f"""
                UPDATE memory SET
                    memory_type = ?, category = ?, key = ?, value = ?,
                    importance_score = ?, access_count = ?, last_accessed_at = ?,
                    updated_at = ?, metadata = ?, content_hash = ?
                WHERE id = ?
                """,
                (
                    data['memory_type'], data['category'], data['key'],
                    data['value'], data['importance_score'], data['access_count'],
                    data['last_accessed_at'], data['updated_at'],
                    data['metadata'], data['content_hash'], data['id']
                )
            )
            conn.commit()
        
        return memory
    
    def delete(self, id: str) -> bool:
        """删除记忆"""
        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(
                f"DELETE FROM {self.table_name} WHERE id = ?",
                (id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    # ========== 专用查询方法 ==========
    
    def get_by_key(
        self,
        key: str,
        memory_type: MemoryType = None,
        category: str = None
    ) -> Optional[Memory]:
        """根据 key 获取记忆"""
        filters = {'key': key}
        if memory_type:
            filters['memory_type'] = memory_type.value
        if category:
            filters['category'] = category
        
        results = self.get_all(filters=filters, limit=1)
        return results[0] if results else None
    
    def get_by_type(
        self,
        memory_type: MemoryType,
        limit: int = 100
    ) -> List[Memory]:
        """获取指定类型的所有记忆"""
        return self.get_all(
            filters={'memory_type': memory_type.value},
            order_by='updated_at DESC',
            limit=limit
        )
    
    def search(
        self,
        query: str,
        memory_type: MemoryType = None,
        limit: int = 10
    ) -> List[Memory]:
        """
        搜索记忆（简单文本匹配）
        
        注: 语义检索需要嵌入支持，这是基础实现
        """
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE value LIKE ? OR key LIKE ?
        """
        params = [f"%{query}%", f"%{query}%"]
        
        if memory_type:
            sql += " AND memory_type = ?"
            params.append(memory_type.value)
        
        sql += " ORDER BY importance_score DESC, updated_at DESC LIMIT ?"
        params.append(limit)
        
        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(sql, params)
            return [self._row_to_entity(row) for row in cursor.fetchall()]
    
    def search_with_scoring(
        self,
        query: str,
        config: RetrievalConfig = None,
        memory_type: MemoryType = None
    ) -> List[SearchResult]:
        """
        带评分的检索
        
        使用 RIF 公式: S = α·R + β·γ + δ·I
        """
        config = config or RetrievalConfig()
        
        # 获取候选记忆
        memories = self.search(
            query=query,
            memory_type=memory_type,
            limit=config.max_results * 3  # 获取更多候选
        )
        
        results = []
        current_time = time.time()
        
        for memory in memories:
            # 计算相关性分数（简单文本匹配）
            relevance = self._calculate_relevance(query, memory)
            
            # 计算时序分数
            time_diff = current_time - memory.created_at
            recency = config.decay_rate ** time_diff
            
            # 重要性分数
            importance = memory.importance_score
            
            # 综合分数
            final_score = SearchResult.calculate_final_score(
                relevance=relevance,
                recency=recency,
                importance=importance,
                weights={
                    'relevance': config.relevance_weight,
                    'recency': config.recency_weight,
                    'importance': config.importance_weight
                }
            )
            
            if final_score >= config.min_score:
                results.append(SearchResult(
                    memory=memory,
                    relevance_score=relevance,
                    recency_score=recency,
                    importance_score=importance,
                    final_score=final_score
                ))
        
        # 按综合分数排序
        results.sort(key=lambda r: r.final_score, reverse=True)
        
        return results[:config.max_results]
    
    def _calculate_relevance(self, query: str, memory: Memory) -> float:
        """计算相关性分数（简单实现）"""
        query_lower = query.lower()
        value_lower = memory.value.lower()
        key_lower = memory.key.lower()
        
        # 完全匹配
        if query_lower == value_lower or query_lower == key_lower:
            return 1.0
        
        # 包含匹配
        if query_lower in value_lower or query_lower in key_lower:
            # 根据匹配位置计算分数
            pos = value_lower.find(query_lower)
            if pos >= 0:
                return 0.8 - (pos / len(value_lower)) * 0.3
            return 0.6
        
        # 单词匹配
        query_words = set(query_lower.split())
        value_words = set(value_lower.split())
        common = query_words & value_words
        if common:
            return len(common) / len(query_words) * 0.5
        
        return 0.1
    
    def touch(self, id: str):
        """更新访问时间和计数"""
        with self.conn_mgr.get_connection() as conn:
            conn.execute(
                f"""
                UPDATE {self.table_name} SET
                    access_count = access_count + 1,
                    last_accessed_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (time.time(), time.time(), id)
            )
            conn.commit()
    
    def get_by_importance(
        self,
        min_score: float = 0.7,
        limit: int = 10
    ) -> List[Memory]:
        """获取高重要性记忆"""
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE importance_score >= ?
            ORDER BY importance_score DESC
            LIMIT ?
        """
        
        with self.conn_mgr.get_connection() as conn:
            cursor = conn.execute(sql, (min_score, limit))
            return [self._row_to_entity(row) for row in cursor.fetchall()]
```

### 7.3 UnifiedDB Facade

```python
from typing import Optional, List, Dict, Any


class UnifiedDB:
    """
    UnifiedDB V2 - 统一数据访问层
    
    作为门面（Facade）模式，提供统一的 API 入口
    """
    
    def __init__(self, db_path: str = ".quickagents/unified.db"):
        # 初始化核心组件
        self.connection_manager = ConnectionManager(db_path)
        self.transaction_manager = TransactionManager(self.connection_manager)
        self.migration_manager = MigrationManager(self.connection_manager)
        
        # 初始化 Repositories
        self._memory_repo = MemoryRepository(
            self.connection_manager,
            self.transaction_manager
        )
        self._task_repo = TaskRepository(
            self.connection_manager,
            self.transaction_manager
        )
        self._progress_repo = ProgressRepository(
            self.connection_manager,
            self.transaction_manager
        )
        self._feedback_repo = FeedbackRepository(
            self.connection_manager,
            self.transaction_manager
        )
        
        # 初始化处理器
        self.importance_evaluator = ImportanceEvaluator()
        self.duplicate_detector = DuplicateDetector()
        self.conflict_resolver = ConflictResolver()
        self.forget_manager = ForgetManager(self)
        
        # 自动迁移
        self.migration_manager.migrate()
    
    # ========== 记忆 API ==========
    
    def get_memory(
        self,
        key: str,
        memory_type: MemoryType = None,
        category: str = None
    ) -> Optional[str]:
        """获取记忆值"""
        memory = self._memory_repo.get_by_key(key, memory_type, category)
        if memory:
            self._memory_repo.touch(memory.id)
            return memory.value
        return None
    
    def set_memory(
        self,
        key: str,
        value: str,
        memory_type: MemoryType = MemoryType.FACTUAL,
        category: str = None,
        importance_score: float = None
    ) -> Memory:
        """设置记忆"""
        # 检查是否存在
        existing = self._memory_repo.get_by_key(key, memory_type, category)
        
        if existing:
            # 检测重复
            if self.duplicate_detector.is_duplicate(existing, value):
                return existing
            
            # 冲突解决
            if self.conflict_resolver.has_conflict(existing, value):
                value = self.conflict_resolver.resolve(existing, value)
            
            # 更新
            existing.value = value
            existing.updated_at = time.time()
            if importance_score is not None:
                existing.importance_score = importance_score
            return self._memory_repo.update(existing)
        else:
            # 创建新记忆
            memory = Memory(
                id=self._generate_id(),
                memory_type=memory_type,
                category=category,
                key=key,
                value=value,
                importance_score=importance_score or self.importance_evaluator.evaluate(value)
            )
            return self._memory_repo.add(memory)
    
    def search_memory(
        self,
        query: str,
        memory_type: MemoryType = None,
        limit: int = 10
    ) -> List[Memory]:
        """搜索记忆"""
        return self._memory_repo.search(query, memory_type, limit)
    
    def search_memory_with_scoring(
        self,
        query: str,
        config: RetrievalConfig = None,
        memory_type: MemoryType = None
    ) -> List[SearchResult]:
        """带评分的搜索"""
        return self._memory_repo.search_with_scoring(query, config, memory_type)
    
    def delete_memory(
        self,
        key: str,
        memory_type: MemoryType = None,
        category: str = None
    ) -> bool:
        """删除记忆"""
        memory = self._memory_repo.get_by_key(key, memory_type, category)
        if memory:
            return self._memory_repo.delete(memory.id)
        return False
    
    # ========== 任务 API ==========
    
    def add_task(
        self,
        task_id: str,
        name: str,
        priority: str = "P2"
    ) -> Task:
        """添加任务"""
        task = Task(
            id=task_id,
            name=name,
            priority=TaskPriority(priority)
        )
        return self._task_repo.add(task)
    
    def update_task_status(
        self,
        task_id: str,
        status: str
    ) -> Optional[Task]:
        """更新任务状态"""
        task = self._task_repo.get(task_id)
        if task:
            task.status = TaskStatus(status)
            task.updated_at = time.time()
            if status == "in_progress":
                task.start_time = time.time()
            elif status in ("completed", "cancelled"):
                task.end_time = time.time()
            return self._task_repo.update(task)
        return None
    
    def get_tasks(
        self,
        status: str = None,
        priority: str = None
    ) -> List[Task]:
        """获取任务列表"""
        filters = {}
        if status:
            filters['status'] = status
        if priority:
            filters['priority'] = priority
        return self._task_repo.get_all(filters=filters, order_by='created_at DESC')
    
    # ========== 进度 API ==========
    
    def init_progress(
        self,
        project_name: str,
        total_tasks: int = 0
    ) -> Progress:
        """初始化进度"""
        progress = Progress(
            id=self._generate_id(),
            project_name=project_name,
            total_tasks=total_tasks
        )
        return self._progress_repo.add(progress)
    
    def update_progress(
        self,
        project_name: str,
        current_task: str = None,
        completed_increment: int = 0
    ) -> Optional[Progress]:
        """更新进度"""
        progress = self._progress_repo.get_by_project(project_name)
        if progress:
            if current_task:
                progress.current_task = current_task
            progress.completed_tasks += completed_increment
            progress.updated_at = time.time()
            return self._progress_repo.update(progress)
        return None
    
    def get_progress(self, project_name: str = None) -> Optional[Progress]:
        """获取进度"""
        if project_name:
            return self._progress_repo.get_by_project(project_name)
        return self._progress_repo.get_latest()
    
    # ========== 反馈 API ==========
    
    def add_feedback(
        self,
        feedback_type: str,
        title: str,
        description: str = None,
        project_name: str = None
    ) -> Feedback:
        """添加反馈"""
        feedback = Feedback(
            id=self._generate_id(),
            feedback_type=FeedbackType(feedback_type),
            title=title,
            description=description,
            project_name=project_name
        )
        return self._feedback_repo.add(feedback)
    
    # ========== 统计 API ==========
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "memory": {
                "total": self._memory_repo.count(),
                "by_type": {
                    t.value: self._memory_repo.count({'memory_type': t.value})
                    for t in MemoryType
                }
            },
            "tasks": {
                "total": self._task_repo.count(),
                "by_status": {
                    s.value: self._task_repo.count({'status': s.value})
                    for s in TaskStatus
                }
            },
            "progress": {
                "total_projects": self._progress_repo.count()
            },
            "feedback": {
                "total": self._feedback_repo.count(),
                "by_type": {
                    t.value: self._feedback_repo.count({'feedback_type': t.value})
                    for t in FeedbackType
                }
            }
        }
    
    # ========== 工具方法 ==========
    
    def _generate_id(self) -> str:
        """生成唯一 ID"""
        import uuid
        return str(uuid.uuid4())
    
    def close(self):
        """关闭连接"""
        self.connection_manager.close_all()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
```

---

## 8. 性能优化

### 8.1 索引策略

```sql
-- 主键索引（自动创建）
PRIMARY KEY (id)

-- 查询优化索引
CREATE INDEX idx_memory_type ON memory(memory_type);
CREATE INDEX idx_memory_category ON memory(category);
CREATE INDEX idx_memory_key ON memory(key);
CREATE INDEX idx_memory_importance ON memory(importance_score);
CREATE INDEX idx_memory_created ON memory(created_at);
CREATE INDEX idx_memory_hash ON memory(content_hash);

-- 复合索引（针对常用查询模式）
CREATE INDEX idx_memory_type_cat ON memory(memory_type, category);
CREATE INDEX idx_memory_type_created ON memory(memory_type, created_at DESC);
```

### 8.2 查询优化

```python
# 使用 EXPLAIN QUERY PLAN 分析查询
def explain_query(conn, sql: str, params: tuple):
    """分析查询计划"""
    cursor = conn.execute(f"EXPLAIN QUERY PLAN {sql}", params)
    return cursor.fetchall()

# 批量操作
def batch_insert(memories: List[Memory], batch_size: int = 100):
    """批量插入"""
    for chunk in chunks(memories, batch_size):
        with conn:
            conn.executemany(sql, [(m.id, m.key, m.value) for m in chunk])
```

### 8.3 缓存策略

```python
from functools import lru_cache

class CachedMemoryRepository(MemoryRepository):
    """带缓存的记忆仓储"""
    
    def __init__(self, *args, cache_size: int = 1000, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache_size = cache_size
    
    @lru_cache(maxsize=1000)
    def get_by_key(self, key: str, memory_type: MemoryType = None, category: str = None) -> Optional[Memory]:
        """带缓存的查询"""
        return super().get_by_key(key, memory_type, category)
    
    def invalidate_cache(self, key: str, memory_type: MemoryType = None, category: str = None):
        """使缓存失效"""
        self.get_by_key.cache_clear()
```

---

## 9. 测试策略

### 9.1 测试覆盖要求

| 类型 | 覆盖率 | 说明 |
|------|--------|------|
| **单元测试** | 100% | 所有公共方法 |
| **集成测试** | 80% | Repository 集成 |
| **性能测试** | 关键路径 | 查询性能 |

### 9.2 测试用例模板

```python
import pytest
import tempfile
import os

class TestUnifiedDBV2:
    """UnifiedDB V2 测试套件"""
    
    @pytest.fixture
    def temp_db(self):
        """临时数据库"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db = UnifiedDB(db_path)
        yield db
        
        db.close()
        os.unlink(db_path)
    
    # ========== 连接管理测试 ==========
    
    def test_connection_pool(self, temp_db):
        """测试连接池"""
        conn_mgr = temp_db.connection_manager
        
        # 测试连接获取
        with conn_mgr.get_connection() as conn:
            assert conn is not None
            cursor = conn.execute("SELECT 1")
            assert cursor.fetchone()[0] == 1
    
    def test_connection_thread_safety(self, temp_db):
        """测试线程安全"""
        import threading
        
        results = []
        
        def worker():
            with temp_db.connection_manager.get_connection() as conn:
                cursor = conn.execute("SELECT 1")
                results.append(cursor.fetchone()[0])
        
        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert all(r == 1 for r in results)
    
    # ========== 事务测试 ==========
    
    def test_transaction_commit(self, temp_db):
        """测试事务提交"""
        with temp_db.transaction_manager.transaction():
            temp_db.set_memory("test_key", "test_value")
        
        assert temp_db.get_memory("test_key") == "test_value"
    
    def test_transaction_rollback(self, temp_db):
        """测试事务回滚"""
        try:
            with temp_db.transaction_manager.transaction():
                temp_db.set_memory("test_key", "test_value")
                raise Exception("模拟错误")
        except Exception:
            pass
        
        assert temp_db.get_memory("test_key") is None
    
    def test_nested_transaction(self, temp_db):
        """测试嵌套事务"""
        with temp_db.transaction_manager.transaction():
            temp_db.set_memory("key1", "value1")
            
            try:
                with temp_db.transaction_manager.transaction():
                    temp_db.set_memory("key2", "value2")
                    raise Exception("模拟错误")
            except Exception:
                pass
            
            # 外层事务应该可以继续
            temp_db.set_memory("key3", "value3")
        
        assert temp_db.get_memory("key1") == "value1"
        assert temp_db.get_memory("key2") is None  # 回滚
        assert temp_db.get_memory("key3") == "value3"
    
    # ========== 迁移测试 ==========
    
    def test_migration_applied(self, temp_db):
        """测试迁移应用"""
        applied = temp_db.migration_manager.get_applied_migrations()
        assert "001" in applied
    
    def test_migration_checksum(self, temp_db):
        """测试迁移校验和"""
        assert temp_db.migration_manager.verify_checksums()
    
    # ========== 记忆 API 测试 ==========
    
    def test_set_get_memory(self, temp_db):
        """测试设置和获取记忆"""
        temp_db.set_memory("test.key", "test value")
        value = temp_db.get_memory("test.key")
        assert value == "test value"
    
    def test_memory_types(self, temp_db):
        """测试记忆类型"""
        temp_db.set_memory("key1", "value1", MemoryType.FACTUAL)
        temp_db.set_memory("key2", "value2", MemoryType.EXPERIENTIAL)
        temp_db.set_memory("key3", "value3", MemoryType.WORKING)
        
        assert temp_db.get_memory("key1", MemoryType.FACTUAL) == "value1"
        assert temp_db.get_memory("key2", MemoryType.EXPERIENTIAL) == "value2"
        assert temp_db.get_memory("key3", MemoryType.WORKING) == "value3"
    
    def test_memory_update(self, temp_db):
        """测试记忆更新"""
        temp_db.set_memory("key", "value1")
        temp_db.set_memory("key", "value2")
        
        assert temp_db.get_memory("key") == "value2"
    
    def test_memory_delete(self, temp_db):
        """测试记忆删除"""
        temp_db.set_memory("key", "value")
        assert temp_db.delete_memory("key") is True
        assert temp_db.get_memory("key") is None
    
    def test_memory_search(self, temp_db):
        """测试记忆搜索"""
        temp_db.set_memory("key1", "hello world")
        temp_db.set_memory("key2", "hello python")
        temp_db.set_memory("key3", "goodbye")
        
        results = temp_db.search_memory("hello")
        assert len(results) == 2
    
    def test_memory_search_with_scoring(self, temp_db):
        """测试带评分的搜索"""
        temp_db.set_memory("key1", "important data", importance_score=0.9)
        temp_db.set_memory("key2", "normal data", importance_score=0.5)
        
        results = temp_db.search_memory_with_scoring("data")
        assert len(results) == 2
        assert results[0].final_score >= results[1].final_score
    
    def test_memory_importance(self, temp_db):
        """测试记忆重要性"""
        temp_db.set_memory("key1", "short", importance_score=0.3)
        temp_db.set_memory("key2", "longer content with more info", importance_score=0.8)
        
        high_importance = temp_db._memory_repo.get_by_importance(min_score=0.7)
        assert len(high_importance) == 1
        assert high_importance[0].key == "key2"
    
    # ========== 任务 API 测试 ==========
    
    def test_add_task(self, temp_db):
        """测试添加任务"""
        task = temp_db.add_task("T001", "Test Task", "P1")
        assert task.id == "T001"
        assert task.name == "Test Task"
        assert task.priority == TaskPriority.P1
    
    def test_update_task_status(self, temp_db):
        """测试更新任务状态"""
        temp_db.add_task("T001", "Test")
        updated = temp_db.update_task_status("T001", "in_progress")
        
        assert updated.status == TaskStatus.IN_PROGRESS
        assert updated.start_time is not None
    
    def test_get_tasks_by_status(self, temp_db):
        """测试按状态获取任务"""
        temp_db.add_task("T001", "Task 1")
        temp_db.add_task("T002", "Task 2")
        temp_db.update_task_status("T001", "completed")
        
        pending = temp_db.get_tasks(status="pending")
        assert len(pending) == 1
        assert pending[0].id == "T002"
    
    # ========== 进度 API 测试 ==========
    
    def test_init_progress(self, temp_db):
        """测试初始化进度"""
        progress = temp_db.init_progress("test-project", total_tasks=10)
        assert progress.project_name == "test-project"
        assert progress.total_tasks == 10
    
    def test_update_progress(self, temp_db):
        """测试更新进度"""
        temp_db.init_progress("test-project", total_tasks=10)
        updated = temp_db.update_progress("test-project", current_task="T003", completed_increment=1)
        
        assert updated.current_task == "T003"
        assert updated.completed_tasks == 1
        assert updated.percentage == 10.0
    
    # ========== 反馈 API 测试 ==========
    
    def test_add_feedback(self, temp_db):
        """测试添加反馈"""
        feedback = temp_db.add_feedback(
            "bug",
            "发现Bug",
            description="详细描述",
            project_name="test-project"
        )
        
        assert feedback.feedback_type == FeedbackType.BUG
        assert feedback.title == "发现Bug"
    
    # ========== 统计 API 测试 ==========
    
    def test_get_stats(self, temp_db):
        """测试获取统计"""
        temp_db.set_memory("key1", "value1")
        temp_db.set_memory("key2", "value2", MemoryType.EXPERIENTIAL)
        temp_db.add_task("T001", "Task")
        
        stats = temp_db.get_stats()
        
        assert stats["memory"]["total"] == 2
        assert stats["memory"]["by_type"]["factual"] == 1
        assert stats["memory"]["by_type"]["experiential"] == 1
        assert stats["tasks"]["total"] == 1
```

### 9.3 性能测试

```python
import time
import pytest

class TestPerformance:
    """性能测试"""
    
    @pytest.fixture
    def populated_db(self, temp_db):
        """填充测试数据"""
        for i in range(1000):
            temp_db.set_memory(f"key_{i}", f"value_{i}")
        return temp_db
    
    def test_query_performance(self, populated_db):
        """测试查询性能"""
        start = time.time()
        value = populated_db.get_memory("key_500")
        elapsed = time.time() - start
        
        assert value == "value_500"
        assert elapsed < 0.01  # < 10ms
    
    def test_search_performance(self, populated_db):
        """测试搜索性能"""
        start = time.time()
        results = populated_db.search_memory("value")
        elapsed = time.time() - start
        
        assert len(results) > 0
        assert elapsed < 0.1  # < 100ms
    
    def test_batch_insert_performance(self, temp_db):
        """测试批量插入性能"""
        memories = [
            (f"batch_key_{i}", f"batch_value_{i}")
            for i in range(100)
        ]
        
        start = time.time()
        for key, value in memories:
            temp_db.set_memory(key, value)
        elapsed = time.time() - start
        
        assert elapsed < 1.0  # < 1秒
```

---

## 10. 实施计划

### 10.1 阶段划分

| 阶段 | 任务 | 预估时间 |
|------|------|----------|
| **Phase 1** | 核心组件实现 | 2h |
| **Phase 2** | Repository 实现 | 2h |
| **Phase 3** | Facade API 实现 | 1h |
| **Phase 4** | 测试编写 (100%) | 3h |
| **Phase 5** | 文档更新 | 1h |
| **总计** | | **9h** |

### 10.2 Phase 1: 核心组件

```
1. ConnectionManager
   ├── 连接池管理
   ├── 线程安全
   └── 自动重连

2. TransactionManager
   ├── ACID 事务
   ├── 嵌套事务
   └── 装饰器支持

3. MigrationManager
   ├── Schema 迁移
   ├── 校验和验证
   └── 回滚支持
```

### 10.3 Phase 2: Repository

```
1. BaseRepository
   ├── CRUD 基础
   └── 过滤/排序

2. MemoryRepository
   ├── 记忆专用方法
   ├── 检索评分
   └── 重要性管理

3. TaskRepository
4. ProgressRepository
5. FeedbackRepository
```

### 10.4 Phase 3: Facade API

```
1. UnifiedDB 类
   ├── 统一 API 入口
   ├── 组件组合
   └── 自动迁移

2. 处理器集成
   ├── ImportanceEvaluator
   ├── DuplicateDetector
   ├── ConflictResolver
   └── ForgetManager
```

### 10.5 Phase 4: 测试

```
1. 单元测试 (100%)
   ├── 连接管理测试
   ├── 事务测试
   ├── 迁移测试
   ├── Repository 测试
   └── API 测试

2. 集成测试
   ├── 完整流程测试
   └── 组件协作测试

3. 性能测试
   ├── 查询性能
   ├── 批量操作性能
   └── 并发测试
```

### 10.6 Phase 5: 文档

```
1. API 文档
2. 使用示例
3. 迁移指南
4. 性能优化指南
```

---

## 验收标准

| 维度 | 标准 | 验证方式 |
|------|------|----------|
| **功能** | 所有 API 正常工作 | 单元测试 |
| **性能** | 查询 < 10ms | 性能测试 |
| **质量** | **100% 测试覆盖** | pytest --cov |
| **文档** | 完整 API 文档 | 文档审查 |
| **兼容** | 向后兼容 V1 | 回归测试 |

---

**设计完成，等待确认开始实施**
