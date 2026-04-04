"""
UnifiedDB V2 - 统一数据访问层

核心功能:
- 门面模式：统一 API 入口
- 组件整合：ConnectionManager, TransactionManager, MigrationManager
- Repository 管理：Memory, Task, Progress, Feedback
- V1 API 兼容：保持向后兼容

架构:
    ┌─────────────────────────────────────┐
    │           UnifiedDB (Facade)         │
    ├─────────────────────────────────────┤
    │  ConnectionManager                   │
    │  TransactionManager                  │
    │  MigrationManager                    │
    ├─────────────────────────────────────┤
    │  MemoryRepository                    │
    │  TaskRepository                      │
    │  ProgressRepository                  │
    │  FeedbackRepository                  │
    └─────────────────────────────────────┘

版本: 2.0.0
创建时间: 2026-03-31
"""

import uuid
import logging
import sqlite3
import atexit
from typing import Optional, List, Dict, Any
from pathlib import Path
from contextlib import contextmanager

from .connection_manager import ConnectionManager
from .transaction_manager import TransactionManager
from .migration_manager import MigrationManager
from .session import Session
from .repositories import (
    MemoryRepository,
    TaskRepository,
    ProgressRepository,
    FeedbackRepository,
    Memory,
    MemoryType,
    Task,
    TaskStatus,
    TaskPriority,
    Progress,
    Feedback,
    FeedbackType,
    SearchResult,
    RetrievalConfig,
)

logger = logging.getLogger(__name__)


def _register_audit_migration(migration_manager) -> None:
    """注册 AuditGuard 迁移（003_audit_tables）"""
    from pathlib import Path

    audit_sql_path = Path(__file__).parent.parent / "audit" / "migrations" / "003_audit_tables.sql"
    audit_rollback_path = Path(__file__).parent.parent / "audit" / "migrations" / "003_audit_tables_rollback.sql"

    if not audit_sql_path.exists():
        return

    up_sql = audit_sql_path.read_text(encoding="utf-8")
    down_sql = ""
    if audit_rollback_path.exists():
        down_sql = audit_rollback_path.read_text(encoding="utf-8")

    from .migration_manager import Migration

    migration = Migration(
        version="003",
        name="audit_tables",
        up_sql=up_sql,
        down_sql=down_sql,
        source="registered",
    )
    migration_manager.register_migration(migration)


class UnifiedDB:
    """
    UnifiedDB V2 - 统一数据访问层

    作为门面（Facade）模式，提供统一的 API 入口

    使用方式:
        db = UnifiedDB('.quickagents/unified.db')

        # 记忆操作
        db.set_memory('project.name', 'QuickAgents', MemoryType.FACTUAL)
        name = db.get_memory('project.name')

        # 任务操作
        db.add_task('T001', '实现认证', priority='P0')
        db.update_task_status('T001', 'in_progress')

        # 进度操作
        db.init_progress('my-project', total_tasks=10)
        db.increment_progress('my-project')

        # 反馈操作
        db.add_feedback('bug', '发现一个问题', '详细描述')

        # 统计
        stats = db.get_stats()

    特性:
        - 自动迁移：初始化时自动执行数据库迁移
        - V1 兼容：保持与 V1 API 的向后兼容
        - 线程安全：所有操作都是线程安全的
        - 事务支持：支持 ACID 事务
    """

    def __init__(self, db_path: str = ".quickagents/unified.db"):
        """
        初始化 UnifiedDB

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)

        # 初始化核心组件
        self._connection_manager = ConnectionManager(str(db_path))
        self._transaction_manager = TransactionManager(self._connection_manager)
        self._migration_manager = MigrationManager(self._connection_manager)

        # Session 统一接口（v2.7.5）
        self._session = Session(self._connection_manager, self._transaction_manager)

        # 初始化 Repositories
        self._memory_repo = MemoryRepository(self._connection_manager, self._transaction_manager)
        self._task_repo = TaskRepository(self._connection_manager, self._transaction_manager)
        self._progress_repo = ProgressRepository(self._connection_manager, self._transaction_manager)
        self._feedback_repo = FeedbackRepository(self._connection_manager, self._transaction_manager)

        # 注册外部迁移（AuditGuard 003）
        _register_audit_migration(self._migration_manager)

        # 自动执行迁移
        self._migration_manager.migrate()

        # 知识图谱（延迟加载）
        self._knowledge_graph = None

        logger.debug(f"UnifiedDB V2 initialized: {db_path}")

    # ==================== 属性 ====================

    @property
    def connection_manager(self) -> ConnectionManager:
        """连接管理器"""
        return self._connection_manager

    @property
    def transaction_manager(self) -> TransactionManager:
        """事务管理器"""
        return self._transaction_manager

    @property
    def migration_manager(self) -> MigrationManager:
        """迁移管理器"""
        return self._migration_manager

    @property
    def session(self) -> Session:
        """
        统一数据库会话（v2.7.5）

        所有模块通过 Session 访问数据库，隐藏 CM/TM 实现细节。

        Returns:
            Session: 统一数据库会话实例
        """
        return self._session

    @property
    def knowledge(self):
        """
        知识图谱管理器（延迟加载）

        Returns:
            KnowledgeGraph: 知识图谱实例
        """
        if self._knowledge_graph is None:
            from ..knowledge_graph import KnowledgeGraph

            self._knowledge_graph = KnowledgeGraph(str(self.db_path))
        return self._knowledge_graph

    # ==================== 记忆 API ====================

    def get_memory(
        self,
        key: str,
        memory_type: Optional[MemoryType] = None,
        category: Optional[str] = None,
        default: Optional[Any] = None,
    ) -> Any:
        """
        获取记忆值

        Args:
            key: 键名
            memory_type: 记忆类型（可选）
            category: 分类（可选）
            default: 默认值

        Returns:
            Any: 记忆值，不存在则返回 default
        """
        memory = self._memory_repo.get_by_key(key, memory_type, category)
        if memory:
            self._memory_repo.touch(memory.id)
            return memory.value
        return default

    def set_memory(
        self,
        key: str,
        value: Any,
        memory_type: MemoryType = MemoryType.FACTUAL,
        category: Optional[str] = None,
        importance_score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Memory:
        """
        设置记忆

        Args:
            key: 键名
            value: 值
            memory_type: 记忆类型
            category: 分类
            importance_score: 重要性分数
            metadata: 元数据

        Returns:
            Memory: 记忆实体
        """
        # 转换值为字符串
        if not isinstance(value, str):
            import json

            value_str = json.dumps(value, ensure_ascii=False)
        else:
            value_str = value

        # 使用 upsert
        memory = self._memory_repo.upsert(
            key=key,
            value=value_str,
            memory_type=memory_type,
            category=category,
            importance_score=importance_score,
        )

        # 更新元数据
        if metadata:
            memory.metadata.update(metadata)
            self._memory_repo.update(memory)

        return memory

    def search_memory(self, query: str, memory_type: Optional[MemoryType] = None, limit: int = 10) -> List[Memory]:
        """
        搜索记忆

        Args:
            query: 搜索关键词
            memory_type: 记忆类型（可选）
            limit: 返回数量限制

        Returns:
            List[Memory]: 记忆列表
        """
        return self._memory_repo.search(query, memory_type, limit)

    def search_memory_with_scoring(
        self, query: str, config: Optional[RetrievalConfig] = None, memory_type: Optional[MemoryType] = None
    ) -> List[SearchResult]:
        """
        带评分的搜索

        Args:
            query: 搜索关键词
            config: 检索配置
            memory_type: 记忆类型（可选）

        Returns:
            List[SearchResult]: 检索结果列表
        """
        return self._memory_repo.search_with_scoring(query, config, memory_type)

    def delete_memory(self, key: str, memory_type: Optional[MemoryType] = None, category: Optional[str] = None) -> bool:
        """
        删除记忆

        Args:
            key: 键名
            memory_type: 记忆类型（可选）
            category: 分类（可选）

        Returns:
            bool: 是否删除成功
        """
        memory = self._memory_repo.get_by_key(key, memory_type, category)
        if memory:
            return self._memory_repo.delete(memory.id)
        return False

    def get_memories_by_type(self, memory_type: MemoryType) -> List[Memory]:
        """
        获取指定类型的所有记忆

        Args:
            memory_type: 记忆类型

        Returns:
            List[Memory]: 记忆列表
        """
        return self._memory_repo.get_by_type(memory_type)

    def get_all_memories(self) -> List[Memory]:
        """
        获取所有记忆（不分类型）

        Returns:
            List[Memory]: 所有记忆列表
        """
        return self._memory_repo.get_all()

    def get_important_memories(self, min_score: float = 0.7, limit: int = 10) -> List[Memory]:
        """
        获取高重要性记忆

        Args:
            min_score: 最小重要性分数
            limit: 返回数量限制

        Returns:
            List[Memory]: 记忆列表
        """
        return self._memory_repo.get_important(min_score, limit)

    # ==================== 任务 API ====================

    def add_task(
        self,
        task_id: str,
        name: str,
        priority: str = "P2",
        description: Optional[str] = None,
        assignee: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Task:
        """
        添加任务

        Args:
            task_id: 任务 ID
            name: 任务名称
            priority: 优先级 (P0/P1/P2/P3)
            description: 描述
            assignee: 负责人
            metadata: 元数据

        Returns:
            Task: 任务实体
        """
        task = Task(
            id=task_id,
            name=name,
            priority=TaskPriority(priority),
            assignee=assignee,
            metadata=metadata or {},
        )
        if description:
            task.metadata["description"] = description

        return self._task_repo.add(task)

    def update_task_status(self, task_id: str, status: str, notes: Optional[str] = None) -> Optional[Task]:
        """
        更新任务状态

        Args:
            task_id: 任务 ID
            status: 新状态 (pending/in_progress/completed/blocked/cancelled)
            notes: 备注

        Returns:
            Optional[Task]: 更新后的任务
        """
        return self._task_repo.update_status(task_id, TaskStatus(status), notes)

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取任务

        Args:
            task_id: 任务 ID

        Returns:
            Optional[Task]: 任务实体
        """
        return self._task_repo.get(task_id)

    def get_tasks(self, status: Optional[str] = None, priority: Optional[str] = None, limit: int = 100) -> List[Task]:
        """
        获取任务列表

        Args:
            status: 状态过滤
            priority: 优先级过滤
            limit: 返回数量限制

        Returns:
            List[Task]: 任务列表
        """
        filters = {}
        if status:
            filters["status"] = status
        if priority:
            filters["priority"] = priority

        return self._task_repo.get_all(filters=filters, order_by="created_at DESC", limit=limit)

    def get_pending_tasks(self, limit: int = 100) -> List[Task]:
        """
        获取待处理任务

        Args:
            limit: 返回数量限制

        Returns:
            List[Task]: 任务列表
        """
        return self._task_repo.get_pending(limit)

    def get_decisions(self) -> List[Dict[str, Any]]:
        """
        获取所有决策日志

        Returns:
            List[Dict]: 决策列表，每个决策包含 id, title, decision, created_at 等信息
        """
        try:
            # 从数据库查询决策表
            with self._connection_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT id, title, decision, context, created_at
                    FROM decisions
                    ORDER BY created_at DESC
                """)
                decisions = []
                for row in cursor.fetchall():
                    decisions.append(
                        {
                            "id": row[0],
                            "title": row[1],
                            "decision": row[2],
                            "context": row[3] if len(row) > 3 else None,
                            "created_at": row[4] if len(row) > 4 else None,
                        }
                    )
                return decisions
        except Exception as e:
            logger.error(f"获取决策失败: {e}")
            return []

    def get_next_task(self) -> Optional[Task]:
        """
        获取下一个待处理的任务（最高优先级）

        Returns:
            Optional[Task]: 任务实体
        """
        return self._task_repo.get_next_task()

    def complete_task(self, task_id: str, notes: Optional[str] = None) -> Optional[Task]:
        """
        完成任务

        Args:
            task_id: 任务 ID
            notes: 完成备注

        Returns:
            Optional[Task]: 更新后的任务
        """
        return self._task_repo.complete_task(task_id, notes)

    def block_task(self, task_id: str, reason: Optional[str] = None) -> Optional[Task]:
        """
        阻塞任务

        Args:
            task_id: 任务 ID
            reason: 阻塞原因

        Returns:
            Optional[Task]: 更新后的任务
        """
        return self._task_repo.block_task(task_id, reason)

    # ==================== 进度 API ====================

    def init_progress(self, project_name: str, total_tasks: int = 0) -> Progress:
        """
        初始化进度

        Args:
            project_name: 项目名称
            total_tasks: 总任务数

        Returns:
            Progress: 进度实体
        """
        return self._progress_repo.init_progress(project_name, total_tasks)

    def get_progress(self, project_name: Optional[str] = None) -> Optional[Progress]:
        """
        获取进度

        Args:
            project_name: 项目名称（可选）

        Returns:
            Optional[Progress]: 进度实体
        """
        if project_name:
            return self._progress_repo.get_by_project(project_name)
        else:
            # 返回最新的进度
            results = self._progress_repo.get_latest(limit=1)
            return results[0] if results else None

    def update_progress(
        self, project_name: str, current_task: Optional[str] = None, completed_increment: int = 0
    ) -> Optional[Progress]:
        """
        更新进度

        Args:
            project_name: 项目名称
            current_task: 当前任务
            completed_increment: 完成增量

        Returns:
            Optional[Progress]: 更新后的进度
        """
        if current_task:
            self._progress_repo.update_current_task(project_name, current_task)

        if completed_increment > 0:
            return self._progress_repo.increment_completed(project_name, completed_increment)

        return self._progress_repo.get_by_project(project_name)

    def increment_progress(self, project_name: str, increment: int = 1) -> Optional[Progress]:
        """
        增加进度

        Args:
            project_name: 项目名称
            increment: 增量

        Returns:
            Optional[Progress]: 更新后的进度
        """
        return self._progress_repo.increment_completed(project_name, increment)

    def save_checkpoint(self, project_name: str, checkpoint: str) -> Optional[Progress]:
        """
        保存检查点

        Args:
            project_name: 项目名称
            checkpoint: 检查点描述

        Returns:
            Optional[Progress]: 更新后的进度
        """
        return self._progress_repo.save_checkpoint(project_name, checkpoint)

    # ==================== 反馈 API ====================

    def add_feedback(
        self,
        feedback_type: str,
        title: str,
        description: Optional[str] = None,
        project_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Feedback:
        """
        添加反馈

        Args:
            feedback_type: 反馈类型 (bug/improvement/best_practice/pitfall/question)
            title: 标题
            description: 描述
            project_name: 项目名称
            metadata: 元数据

        Returns:
            Feedback: 反馈实体
        """
        return self._feedback_repo.add_feedback(
            feedback_type=FeedbackType(feedback_type),
            title=title,
            description=description,
            project_name=project_name,
            metadata=metadata,
        )

    def get_feedbacks(
        self, feedback_type: Optional[str] = None, project_name: Optional[str] = None, limit: int = 100
    ) -> List[Feedback]:
        """
        获取反馈列表

        Args:
            feedback_type: 反馈类型（可选）
            project_name: 项目名称（可选）
            limit: 返回数量限制

        Returns:
            List[Feedback]: 反馈列表
        """
        if feedback_type:
            return self._feedback_repo.get_by_type(FeedbackType(feedback_type), limit)
        elif project_name:
            return self._feedback_repo.get_by_project(project_name, limit=limit)
        else:
            return self._feedback_repo.get_recent(limit)

    # ==================== 统计 API ====================

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "memory": {
                "total": self._memory_repo.count(),
                "by_type": {t.value: self._memory_repo.count({"memory_type": t.value}) for t in MemoryType},
            },
            "tasks": {
                "total": self._task_repo.count(),
                "by_status": self._task_repo.count_by_status(),
                "by_priority": self._task_repo.count_by_priority(),
            },
            "progress": {"total_projects": self._progress_repo.count()},
            "feedback": {
                "total": self._feedback_repo.count(),
                "by_type": self._feedback_repo.count_by_type(),
            },
        }

    # ==================== V1 兼容层 ====================

    @contextmanager
    def _get_connection(self):
        """
        V1 兼容：获取数据库连接（上下文管理器）

        此方法为 V1 API 兼容层，供 SkillEvolution 等模块直接使用。
        v2.7.5 起委托给 Session.query() 统一接口。

        注意: 退出时自动 commit，确保连接回到池中时不带未提交事务。

        Yields:
            sqlite3.Connection: 数据库连接，已设置 row_factory
        """
        with self._session.query() as conn:
            # V1 使用 sqlite3.Row 作为行工厂
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                # 正常退出时自动 commit
                if conn.in_transaction:
                    conn.commit()
            except Exception:
                # 异常时 rollback（由 get_connection 的 finally 处理）
                raise

    def _execute_sql(self, sql: str, params: Optional[tuple] = None) -> Any:
        """
        V1 兼容：执行原始 SQL

        Args:
            sql: SQL 语句
            params: 参数元组

        Returns:
            执行结果
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)

            # 判断是查询还是修改
            if sql.strip().upper().startswith("SELECT"):
                return cursor.fetchall()
            else:
                return cursor.rowcount

    # ==================== 工具方法 ====================

    def _generate_id(self) -> str:
        """生成唯一 ID"""
        return str(uuid.uuid4())

    def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: 数据库是否健康
        """
        return self._connection_manager.health_check()

    def close(self) -> None:
        """关闭数据库连接"""
        self._connection_manager.close_all()
        logger.debug("UnifiedDB closed")

    def __enter__(self) -> "UnifiedDB":
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器退出"""
        self.close()

    def __repr__(self) -> str:
        return f"UnifiedDB(db_path='{self.db_path}')"

    def __del__(self):
        """Auto-close on garbage collection"""
        try:
            self.close()
        except Exception:
            pass


# ==================== 全局实例 ====================

_global_db: Optional[UnifiedDB] = None


def _cleanup_global_db():
    """Cleanup function for atexit"""
    global _global_db
    if _global_db is not None:
        try:
            _global_db.close()
        except Exception:
            pass
        _global_db = None


def get_unified_db(db_path: str = ".quickagents/unified.db") -> UnifiedDB:
    """
    获取全局 UnifiedDB 实例

    Args:
        db_path: 数据库文件路径

    Returns:
        UnifiedDB: UnifiedDB 实例
    """
    global _global_db
    if _global_db is None:
        _global_db = UnifiedDB(db_path)
        atexit.register(_cleanup_global_db)
    return _global_db


def reset_global_db() -> None:
    """重置全局实例"""
    global _global_db
    if _global_db is not None:
        _global_db.close()
        _global_db = None
