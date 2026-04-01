# QuickAgents v2.7.5 核心架构升级计划

> 版本: 1.0.0 | 创建时间: 2026-04-01 | 规划者: 风后-规划
> 状态: 待实施 | 预计工时: ~18h

---

## 元信息

| 属性 | 值 |
|------|-----|
| 计划ID | PLAN-2026-04-01-CORE-ARCH |
| 目标版本 | 2.7.5 |
| 前置版本 | 2.7.0 |
| 涉及模块 | ConnectionManager, TransactionManager, MigrationManager, Repository层 |
| 总测试数 | 461+ (当前) |
| 测试目标 | 100% 通过 |

---

## 一、ConnectionManager 升级方案

### 1.1 现状分析

| 维度 | 当前状态 | 问题 |
|------|----------|------|
| **连接池** | 固定5个连接，预创建 | 空闲浪费资源，无法动态伸缩 |
| **PRAGMA** | 6项基础配置 (foreign_keys, journal_mode, busy_timeout, synchronous, cache_size) | 缺少 mmap、temp_store 等关键优化 |
| **重连** | 无 | 连接断开后无法自动恢复 |
| **连接验证** | 仅 health_check() | 池中连接可能已过期/断开 |
| **统计** | 仅 pool_size/active/available | 无等待时间、命中率、错误率等指标 |
| **资源释放** | `__del__` + `atexit` | Windows 上 `__del__` 不可靠 |
| **线程模型** | threading.Lock | asyncio 场景不支持 |
| **WAL管理** | 无 | WAL 文件可能无限增长 |

### 1.2 参考来源

| 来源 | 关键建议 |
|------|---------|
| **PowerSync Blog** - SQLite Optimizations For Ultra High-Performance | `PRAGMA mmap_size`、`PRAGMA temp_store=MEMORY`、`PRAGMA page_size=4096` |
| **oldmoe.blog** - Turn on mmap support for your SQLite connections | mmap 可提升读取性能 40%+ |
| **SQLAlchemy 1.4** - Connection Pooling Documentation | 连接验证（`pre_ping`）、连接超时回收 |
| **kerkour.com** - Optimizing SQLite for servers | `busy_timeout=5000`、`cache_size=-20000`、连接池按需创建 |
| **Hacker News** - SQLite performance tuning | WAL 文件无限增长问题，需要自动 checkpoint |
| **briandouglas.ie** - Sensible SQLite defaults | cache_size=-20000 (20MB)、foreign_keys=ON |

### 1.3 升级方案

| 升级项 | 优先级 | 说明 | 预期收益 |
|--------|--------|------|---------|
| **动态连接池** | P0 | 按需创建，空闲超时回收，最大/最小连接数可配置 | 资源节省 40%+ |
| **连接验证 (pre_ping)** | P0 | 从池中获取连接前先 `SELECT 1` 验证存活 | 消除过期连接错误 |
| **PRAGMA 增强** | P0 | 添加 `mmap_size=256MB`、`temp_store=MEMORY`、`page_size=4096` | 读取性能提升 40%+ |
| **WAL 自动 Checkpoint** | P1 | 定期执行 `PRAGMA wal_checkpoint(TRUNCATE)`，防止 WAL 无限增长 | 磁盘空间管理 |
| **连接池指标** | P1 | 等待时间、命中率、创建数、错误数 | 可观测性 |
| **连接超时回收** | P1 | 空闲连接超过 N 秒自动关闭 | 资源管理 |
| **异步支持 (async)** | P2 | 添加 `async_get_connection()`，支持 asyncio 场景 | asyncio 兼容 |
| **连接事件回调** | P2 | on_create/on_acquire/on_release/on_close 钩子 | 可扩展性 |

### 1.4 PRAGMA 目标配置

```python
# v2.7.5 目标 PRAGMA 配置
PRAGMA foreign_keys = ON                    # 外键约束
PRAGMA journal_mode = WAL                   # WAL模式（并发读取）
PRAGMA busy_timeout = 5000                  # 忙碌超时5秒
PRAGMA synchronous = NORMAL                 # 性能与安全的平衡
PRAGMA cache_size = -20000                  # 20MB缓存
PRAGMA mmap_size = 268435456                # 256MB mmap
PRAGMA temp_store = MEMORY                  # 临时表在内存中
PRAGMA page_size = 4096                     # 4KB页大小
PRAGMA wal_autocheckpoint = 1000            # 每1000页自动checkpoint
```

### 1.5 动态连接池设计

```python
@dataclass
class PoolConfig:
    min_size: int = 1          # 最小连接数
    max_size: int = 10         # 最大连接数
    idle_timeout: float = 300  # 空闲超时（秒）
    max_lifetime: float = 3600 # 连接最大存活时间（秒）
    pre_ping: bool = True      # 获取前验证连接
    acquire_timeout: float = 30 # 获取连接超时（秒）
```

---

## 二、TransactionManager 升级方案

### 2.1 现状分析

| 维度 | 当前状态 | 问题 |
|------|----------|------|
| **嵌套事务** | SAVEPOINT 机制 | ✅ 基本可用 |
| **只读事务** | `read_only()` 方法 | 与写事务共享 `_transaction_depth`，计数不准确 |
| **线程安全** | threading.Lock（全局） | 全局锁粒度太粗，多线程事务串行化 |
| **事务隔离** | 无显式隔离级别 | SQLite 默认 SERIALIZABLE，但未暴露配置 |
| **重试机制** | 无 | `database is locked` 时直接失败 |
| **超时控制** | 无 | 事务无超时限制，可能无限等待 |
| **装饰器** | `@atomic` | ✅ 基本可用，但无法传递参数 |

### 2.2 参考来源

| 来源 | 关键建议 |
|------|---------|
| **oldmoe.blog** - The Write Stuff: Concurrent Write Transactions in SQLite | SQLite 单写者模型，重试+退避是关键 |
| **Medium** - Connection Pooling Patterns: Optimizing Database Connections | 事务超时、重试策略、指数退避 |
| **OpenDev 论文** (arXiv:2603.05344v2) | 指数退避重试（backoff_base_ms=2000, multiplier=2） |
| **SWE-agent 论文** | ACI 设计原则，错误反馈三要素 |

### 2.3 升级方案

| 升级项 | 优先级 | 说明 | 预期收益 |
|--------|--------|------|---------|
| **指数退避重试** | P0 | `database is locked` 时自动重试，退避策略可配置 | 消除锁定错误 |
| **事务超时** | P0 | 事务执行超过 N 秒自动回滚 | 防止死锁 |
| **线程独立事务** | P0 | 每个线程独立维护事务深度和连接，消除全局锁瓶颈 | 多线程性能 |
| **只读/读写分离** | P1 | 只读事务使用独立池，不阻塞写事务 | 并发读取性能 |
| **事务事件** | P1 | on_begin/on_commit/on_rollback 回调 | 可观测性 |
| **事务日志** | P1 | 记录事务开始/结束时间、耗时、状态 | 诊断能力 |
| **传播行为配置** | P2 | REQUIRED/REQUIRES_NEW/NESTED/SUPPORTS | 灵活性 |
| **死锁检测** | P2 | 检测长时间运行的事务并告警 | 可靠性 |

### 2.4 重试策略设计

```python
@dataclass
class RetryConfig:
    max_retries: int = 5             # 最大重试次数
    backoff_base_ms: int = 2000      # 基础退避时间（毫秒）
    backoff_multiplier: float = 2.0  # 退避倍数
    max_backoff_ms: int = 30000      # 最大退避时间
    retryable_errors: list = field(default_factory=lambda: [
        "database is locked",
        "database is busy",
    ])
```

### 2.5 线程独立事务设计

```python
# 当前: 全局共享状态
self._transaction_depth = 0        # 所有线程共享
self._current_conn = None          # 所有线程共享

# 目标: 线程独立状态
self._local = threading.local()    # 每个线程独立
self._local.depth = 0
self._local.conn = None
```

---

## 三、MigrationManager 升级方案

### 3.1 现状分析

| 维度 | 当前状态 | 问题 |
|------|----------|------|
| **迁移定义** | Python 代码硬编码 (405行) | 不可维护，应使用独立迁移文件 |
| **回滚** | `rollback()` 方法 | 多数 `down_sql` 为空或无效（SQLite 不支持 DROP COLUMN） |
| **校验和** | SHA256 前16位 | ✅ 基本可用 |
| **迁移顺序** | 按版本号排序 | ✅ 基本可用 |
| **迁移日志** | 仅 applied_at 时间戳 | 缺少执行耗时、成功/失败状态 |
| **条件迁移** | 不支持 | 无法根据数据库状态决定是否执行 |
| **数据迁移** | 不支持 | 仅支持 DDL，不支持数据转换 |
| **Schema快照** | 不支持 | 无法回溯历史 Schema |

### 3.2 参考来源

| 来源 | 关键建议 |
|------|---------|
| **Django Migrations** | 迁移文件序列化、前向依赖声明、自动生成 |
| **Alembic (SQLAlchemy)** | 迁移脚本独立、自动生成、支持数据迁移 |
| **Hacker News** - Simple declarative schema migration for SQLite | 声明式 Schema vs 迁移脚本，后者更灵活 |
| **Reddit** - SQLite migration best practices | 迁移文件版本控制、不可变迁移 |

### 3.3 升级方案

| 升级项 | 优先级 | 说明 | 预期收益 |
|--------|--------|------|---------|
| **外部迁移文件** | P0 | 支持从 `migrations/` 目录加载 `.sql` 文件 | 可维护性 |
| **迁移执行日志增强** | P0 | 记录执行耗时、状态、错误信息 | 诊断能力 |
| **数据迁移支持** | P1 | 支持 Python 迁移脚本（不仅是 SQL） | 功能完整性 |
| **条件迁移** | P1 | `condition(db) -> bool` 决定是否执行 | 灵活性 |
| **不可变迁移** | P1 | 已应用迁移不可修改（校验和强制验证） | 安全性 |
| **Schema 快照** | P2 | 每次迁移后保存完整 Schema 快照 | 回溯能力 |
| **迁移生成器** | P2 | 自动对比两个 Schema 生成迁移 SQL | 开发效率 |
| **迁移依赖声明** | P2 | `depends_on=["001"]` 显式依赖 | 可靠性 |

### 3.4 外部迁移文件设计

```
migrations/
├── 001_initial_schema.sql
├── 001_initial_schema_rollback.sql
├── 002_add_memory_hash.sql
├── 002_add_memory_hash_rollback.sql
├── 003_add_decisions_table.py      # Python 数据迁移
└── migration_config.json           # 迁移配置
```

```json
// migration_config.json
{
    "migrations_dir": "migrations/",
    "immutable": true,
    "auto_snapshot": true,
    "checkpoint_interval": 5
}
```

---

## 四、Repository 层升级方案

### 4.1 现状分析

| 维度 | 当前状态 | 问题 |
|------|----------|------|
| **泛型支持** | `Generic[T]` | ✅ 可用 |
| **查询构建** | 字符串拼接 `f"SELECT * FROM {self.table_name}"` | 代码可读性差，难以扩展 |
| **分页** | LIMIT/OFFSET | 无游标分页，大数据量性能差 |
| **批量操作** | 逐条 INSERT 循环 | 未使用 `executemany` 或批量 VALUES |
| **事务集成** | 混用 conn_mgr 和 tx_mgr | 耦合不清，单条操作用 conn，批量用 tx |
| **缓存** | 无 | 频繁查询相同数据无缓存 |
| **事件通知** | 无 | 数据变更无通知机制 |
| **单元测试** | 依赖真实 SQLite 文件 | 缺少 Mock/内存数据库支持 |
| **软删除** | 不支持 | 物理删除无法恢复 |

### 4.2 参考来源

| 来源 | 关键建议 |
|------|---------|
| **DDD - Repository Pattern** (intentional-architecture-in-python) | Repository 是领域集合的抽象，应像内存集合一样使用 |
| **SQLAlchemy Session** | Unit of Work 模式，延迟提交 |
| **LinkedIn - Repository Pattern** | 不仅用于持久层，也可用于缓存层 |
| **go-eagle/eagle-layout** | 业务逻辑与数据访问彻底分离 |

### 4.3 升级方案

| 升级项 | 优先级 | 说明 | 预期收益 |
|--------|--------|------|---------|
| **查询构建器** | P0 | 链式 API: `repo.query().filter(type='factual').order_by('-created_at').limit(10)` | 代码可读性 + 安全性 |
| **批量操作优化** | P0 | 使用 `executemany()` 或批量 VALUES | 批量写入性能提升 5-10x |
| **事务边界统一** | P0 | 所有写操作统一走 TransactionManager | 一致性 |
| **游标分页** | P1 | keyset pagination: 基于 ID/时间戳的高性能分页 | 大数据量查询性能 |
| **Unit of Work** | P1 | 批量变更延迟提交，减少事务次数 | 写入性能 |
| **内存数据库支持** | P1 | `:memory:` 模式，方便测试 | 测试效率 |
| **查询缓存** | P2 | LRU 缓存热点查询结果 | 读取性能 |
| **数据变更事件** | P2 | `on_add/on_update/on_delete` 回调 | 可扩展性 |
| **软删除** | P2 | `deleted_at` 字段，逻辑删除而非物理删除 | 数据安全 |

### 4.4 查询构建器设计

```python
# 当前方式
db.get_memories_by_type(MemoryType.FACTUAL, limit=10)

# 目标方式 - 链式查询
results = memory_repo.query() \
    .filter(memory_type=MemoryType.FACTUAL) \
    .filter(importance_score__gte=0.8) \
    .order_by('-created_at') \
    .limit(10) \
    .all()

# 复杂条件
results = memory_repo.query() \
    .filter(category__in=['pitfalls', 'best-practices']) \
    .filter(key__contains='auth') \
    .exclude(importance_score__lt=0.3) \
    .only(['key', 'value', 'created_at']) \
    .all()

# 聚合查询
stats = memory_repo.query() \
    .filter(memory_type=MemoryType.FACTUAL) \
    .group_by('category') \
    .count()
```

### 4.5 批量操作优化设计

```python
# 当前: 逐条 INSERT
for data in data_list:
    conn.execute(f"INSERT INTO {table} ({fields}) VALUES ({placeholders})", values)

# 目标1: executemany
conn.executemany(f"INSERT INTO {table} ({fields}) VALUES ({placeholders})", all_values)

# 目标2: 批量 VALUES (更快)
# INSERT INTO table (a, b, c) VALUES (?,?,?), (?,?,?), (?,?,?)
batch_size = 100
for i in range(0, len(data_list), batch_size):
    batch = data_list[i:i+batch_size]
    values_clause = ",".join([f"({placeholders})" for _ in batch])
    conn.execute(f"INSERT INTO {table} ({fields}) VALUES {values_clause}", flat_values)
```

---

## 五、跨模块耦合性优化

### 5.1 当前耦合问题

| 问题 | 涉及模块 | 影响 | 严重程度 |
|------|----------|------|---------|
| TransactionManager 直接调用 `conn_mgr._acquire()` | TM → CM | 违反封装，访问私有方法 | 🔴 高 |
| Repository 混用 conn_mgr/tx_mgr | Repo → CM+TM | 事务边界不清晰 | 🔴 高 |
| MigrationManager 直接使用 conn_mgr | MM → CM | 迁移无法在事务中执行 | 🟡 中 |
| evolution.py 调用 `db._get_connection()` | External → DB | V1 兼容层是临时方案 | 🟡 中 |

### 5.2 耦合性优化方案

| 升级项 | 优先级 | 说明 |
|--------|--------|------|
| **统一 Session 接口** | P0 | 所有模块通过 Session 访问数据库，隐藏 CM/TM 细节 |
| **移除 `_acquire`/`_release` 直接调用** | P0 | TM 应通过 CM 的公共接口获取连接 |
| **依赖注入容器** | P1 | 统一管理 CM/TM/MM/Repo 的创建和注入 |

### 5.3 Session 接口设计

```python
class Session:
    """统一数据库会话接口"""
    
    def __init__(self, connection_manager, transaction_manager):
        self._cm = connection_manager
        self._tm = transaction_manager
    
    @contextmanager
    def query(self):
        """获取只读连接"""
        with self._tm.read_only() as conn:
            yield conn
    
    @contextmanager
    def transaction(self):
        """获取读写事务连接"""
        with self._tm.transaction() as conn:
            yield conn
    
    def execute(self, sql, params=None):
        """执行单条语句"""
        ...

# 使用方式 - 所有模块通过 Session 访问
class MemoryRepository(BaseRepository[Memory]):
    def __init__(self, session: Session):
        self._session = session
    
    def get(self, id: str) -> Optional[Memory]:
        with self._session.query() as conn:
            cursor = conn.execute(...)
            return self._row_to_entity(cursor.fetchone())
```

---

## 六、实施里程碑

| Phase | 内容 | 预计工时 | 测试要求 |
|-------|------|----------|---------|
| **Phase 1** | ConnectionManager 增强 | 4h | 新增 15+ 测试 |
| **Phase 2** | TransactionManager 增强 | 3h | 新增 12+ 测试 |
| **Phase 3** | Repository 层增强 | 4h | 新增 20+ 测试 |
| **Phase 4** | MigrationManager 增强 | 3h | 新增 10+ 测试 |
| **Phase 5** | 跨模块耦合优化 (Session) | 2h | 新增 8+ 测试 |
| **Phase 6** | 测试 + 文档 | 2h | 全量回归 500+ 测试 |
| **总计** | - | **~18h** | **65+ 新测试** |

### 依赖关系

```
Phase 1 (CM) ──→ Phase 2 (TM) ──→ Phase 5 (Session)
                                         ↑
Phase 3 (Repo) ─────────────────────────┘
Phase 4 (MM) ──→ Phase 5 (Session)
```

---

## 七、升级优先级总览

### P0 - 必须完成

| 模块 | 升级项 | 预期收益 |
|------|--------|---------|
| CM | 动态连接池 | 资源节省 40%+ |
| CM | 连接验证 pre_ping | 消除过期连接错误 |
| CM | PRAGMA 增强 (mmap, temp_store) | 读取性能提升 40%+ |
| TM | 指数退避重试 | 消除 `database is locked` 错误 |
| TM | 线程独立事务 | 多线程性能提升 |
| Repo | 查询构建器 | 代码可读性 + 安全性 |
| Repo | 批量操作优化 | 批量写入性能提升 5-10x |
| Cross | Session 接口统一 | 解耦、可测试性 |

### P1 - 应该完成

| 模块 | 升级项 | 预期收益 |
|------|--------|---------|
| CM | WAL 自动 Checkpoint | 防止 WAL 无限增长 |
| CM | 连接池指标 | 可观测性 |
| CM | 连接超时回收 | 资源管理 |
| TM | 事务超时 | 防止死锁 |
| TM | 只读/读写分离 | 并发读取性能 |
| TM | 事务事件/日志 | 可观测性 |
| Repo | 游标分页 | 大数据量查询性能 |
| Repo | Unit of Work | 减少事务次数 |
| Repo | 内存数据库支持 | 测试效率 |
| MM | 外部迁移文件 | 可维护性 |
| MM | 数据迁移支持 | 功能完整性 |
| MM | 条件迁移 | 灵活性 |
| MM | 不可变迁移 | 安全性 |

### P2 - 可以延后

| 模块 | 升级项 | 预期收益 |
|------|--------|---------|
| CM | async 支持 | asyncio 场景 |
| CM | 连接事件回调 | 可扩展性 |
| TM | 传播行为配置 | 灵活性 |
| TM | 死锁检测 | 可观测性 |
| Repo | 查询缓存 | 热点查询性能 |
| Repo | 数据变更事件 | 可扩展性 |
| Repo | 软删除 | 数据安全 |
| MM | Schema 快照 | 回溯能力 |
| MM | 迁移生成器 | 开发效率 |
| MM | 迁移依赖声明 | 可靠性 |

---

## 八、风险评估

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|---------|
| **V1 API 兼容性破坏** | 中 | 高 | 保持 Facade 接口不变，仅修改内部实现 |
| **WAL 模式兼容性** | 低 | 中 | 检测 SQLite 版本，< 3.7.0 回退到 DELETE 模式 |
| **mmap 不支持** | 低 | 低 | try/except 回退到普通 I/O |
| **性能回退** | 低 | 高 | 每个 Phase 完成后基准测试 |
| **测试覆盖不足** | 中 | 高 | 每个 Phase 必须达到 100% 测试覆盖 |
| **Windows 文件锁加剧** | 中 | 中 | 动态连接池减少空闲连接数 |
| **线程安全问题** | 中 | 高 | 每个 Phase 添加并发测试 |

---

## 九、性能基准测试计划

### 测试指标

| 指标 | v2.7.0 基线 | v2.7.5 目标 | 提升幅度 |
|------|-------------|-------------|---------|
| **单条读取 (QPS)** | ~5,000 | ~8,000 | +60% |
| **单条写入 (QPS)** | ~1,000 | ~1,500 | +50% |
| **批量写入 1000条 (ms)** | ~500 | ~50 | +10x |
| **并发读取 10线程 (QPS)** | ~10,000 | ~20,000 | +100% |
| **连接池内存占用** | ~5MB | ~2MB | -60% |
| **WAL 文件最大大小** | 无限 | < 10MB | 可控 |

### 测试工具

```python
# 基准测试脚本结构
tests/
└── benchmarks/
    ├── bench_connection.py      # 连接管理基准
    ├── bench_transaction.py     # 事务管理基准
    ├── bench_repository.py      # Repository 基准
    ├── bench_migration.py       # 迁移管理基准
    └── bench_concurrent.py      # 并发性能基准
```

---

## 十、验收标准

### 功能验收

- [ ] ConnectionManager: 动态连接池、pre_ping、PRAGMA 增强
- [ ] TransactionManager: 指数退避重试、线程独立事务
- [ ] Repository: 查询构建器、批量操作优化
- [ ] MigrationManager: 外部迁移文件、日志增强
- [ ] Session 统一接口

### 性能验收

- [ ] 单条读取性能提升 ≥ 40%
- [ ] 批量写入性能提升 ≥ 5x
- [ ] 连接池内存占用减少 ≥ 40%
- [ ] WAL 文件大小可控

### 质量验收

- [ ] 所有 461 现有测试通过
- [ ] 新增 65+ 测试全部通过
- [ ] 代码覆盖率 ≥ 80%
- [ ] V1 API 完全向后兼容
- [ ] 无 Windows 文件锁问题

---

## 附录

### A. 参考论文与资源

| 资源 | 链接 | 关键收获 |
|------|------|---------|
| PowerSync - SQLite Optimizations | powersync.com/blog/sqlite-optimizations-for-ultra-high-performance | 10项SQLite优化，WAL模式7万读/秒 |
| oldmoe.blog - mmap support | oldmoe.blog/2024/02/03/turn-on-mmap-support | mmap 提升读取40%+ |
| oldmoe.blog - Concurrent Write | oldmoe.blog/2024/07/08/the-write-stuff | SQLite单写者模型，重试策略 |
| SQLAlchemy Pooling | docs.sqlalchemy.org/14/core/pooling.html | pre_ping、连接超时、池回收 |
| OpenDev 论文 | arXiv:2603.05344v2 | 指数退避重试、上下文压缩 |
| SWE-agent 论文 | ACI设计原则 | 简化命令空间、增强反馈 |
| kerkour.com - SQLite for Servers | kerkour.com/sqlite-for-servers | PRAGMA配置、连接池设计 |
| Django Migrations | docs.djangoproject.com | 迁移文件管理、依赖声明 |

### B. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0.0 | 2026-04-01 | 初始计划 |

---

*QuickAgents v2.7.5 核心架构升级计划 | 2026-04-01*
