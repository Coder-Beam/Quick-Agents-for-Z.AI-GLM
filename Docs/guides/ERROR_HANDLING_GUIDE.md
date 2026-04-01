# QuickAgents 错误处理指南

## 概述

QuickAgents采用统一的错误处理机制，确保错误信息清晰、可追踪、易调试。

## 错误类型层次结构

```
QuickAgentsError (基类)
├── DatabaseError (数据库错误)
│   ├── DatabaseConnectionError (连接错误)
│   ├── DatabaseQueryError (查询错误)
│   └── DatabaseIntegrityError (完整性错误)
│
├── MemoryError (记忆系统错误)
│   ├── MemoryNotFoundError (记忆未找到)
│   ├── MemoryValidationError (记忆验证失败)
│   └── MemorySyncError (记忆同步错误)
│
├── LoopDetectionError (循环检测错误)
│   ├── LoopThresholdError (阈值错误)
│   └── LoopPatternError (模式错误)
│
├── KnowledgeGraphError (知识图谱错误)
│   ├── NodeNotFoundError (节点未找到)
│   ├── EdgeNotFoundError (边未找到)
│   ├── DuplicateNodeError (节点重复)
│   └── DuplicateEdgeError (边重复)
│
├── EvolutionError (进化系统错误)
│   ├── EvolutionTriggerError (触发错误)
│   └── EvolutionOptimizationError (优化错误)
│
└── CLIError (CLI错误)
    ├── CommandNotFoundError (命令未找到)
    ├── InvalidArgumentError (参数无效)
    └── ExecutionError (执行错误)
```

## 使用示例

### 1. 基本错误处理

```python
from quickagents import QuickAgentsError, DatabaseError

try:
    db = UnifiedDB('invalid_path.db')
    db.set_memory('test.key', 'value')
except DatabaseError as e:
    print(f"数据库错误: {e}")
    print(f"错误代码: {e.error_code}")
    print(f"详细信息: {e.details}")
except QuickAgentsError as e:
    print(f"QuickAgents错误: {e}")
```

### 2. 特定错误处理

```python
from quickagents import MemoryNotFoundError, KnowledgeGraphError

try:
    value = db.get_memory('nonexistent.key')
    if value is None:
        raise MemoryNotFoundError('nonexistent.key')
except MemoryNotFoundError as e:
    print(f"记忆未找到: {e.key}")
    print(f"建议: {e.suggestion}")
```

### 3. 错误恢复

```python
from quickagents import UnifiedDB, LoopDetector

def safe_operation():
    try:
        # 尝试操作
        result = risky_operation()
        return result
    except QuickAgentsError as e:
        # 记录错误
        logger.error(f"操作失败: {e}")
        
        # 尝试恢复
        try:
            recovery_action()
        except Exception as recovery_error:
            logger.critical(f"恢复失败: {recovery_error}")
        
        # 重新抛出
        raise
```

## 错误消息格式

### 标准格式

```
[错误类型] 错误消息

详细信息:
- 键: value
- 操作: operation_name
- 时间戳: YYYY-MM-DD HH:MM:SS

建议解决方案:
1. 解决方案1
2. 解决方案2
```

### 示例

```
[DatabaseError] 无法连接到数据库

详细信息:
- 数据库路径: .quickagents/unified.db
- 错误代码: SQLITE_CANTOPEN
- 时间戳: 2026-03-31 14:30:00

建议解决方案:
1. 检查数据库路径是否存在
2. 确保有足够的文件权限
3. 检查磁盘空间是否充足
```

## 最佳实践

### 1. 错误日志记录

```python
import logging

logger = logging.getLogger('quickagents')

try:
    # 操作
    pass
except QuickAgentsError as e:
    logger.error(f"QuickAgents错误: {e}", exc_info=True)
    logger.debug(f"错误详情: {e.details}")
```

### 2. 错误恢复策略

```python
def operation_with_retry(max_retries=3):
    for attempt in range(max_retries):
        try:
            return risky_operation()
        except DatabaseError as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # 指数退避
```

### 3. 错误上下文

```python
from quickagents import QuickAgentsError

class ContextualError(QuickAgentsError):
    def __init__(self, message, context=None):
        super().__init__(message)
        self.context = context or {}
    
    def to_dict(self):
        return {
            'error': str(self),
            'context': self.context,
            'timestamp': datetime.now().isoformat()
        }
```

## 错误监控

### 1. 错误统计

```python
from quickagents import UnifiedDB

db = UnifiedDB()

# 记录错误
db.add_feedback('bug', '错误标题', description='错误详情')

# 获取错误统计
stats = db.get_stats()
print(f"错误总数: {stats['feedback']['bug']}")
```

### 2. 错误趋势分析

```python
from quickagents import UnifiedDB, FeedbackType

db = UnifiedDB()

# 分析错误趋势
bugs = db.get_feedbacks(FeedbackType.BUG)
recent_bugs = [b for b in bugs if is_recent(b['created_at'])]

print(f"最近错误数: {len(recent_bugs)}")
```

## 常见错误及解决方案

### 1. 数据库锁定

**错误**: `database is locked`

**原因**: 多个进程同时访问数据库

**解决方案**:
```python
# 使用WAL模式
db = UnifiedDB('.quickagents/unified.db')
db.enable_wal_mode()

# 或使用连接池
from quickagents import ConnectionPool
pool = ConnectionPool('.quickagents/unified.db')
```

### 2. 记忆溢出

**错误**: `Memory limit exceeded`

**原因**: 讣忆数据量过大

**解决方案**:
```python
# 定期清理
db.cleanup_old_records(days=30)

# 或分批处理
memories = db.get_all_memories()
for batch in chunk(memories, 1000):
    process_batch(batch)
```

### 3. 循环检测误报

**错误**: `Doom-Loop detected`

**原因**: 阈值设置过低

**解决方案**:
```python
# 调整阈值
detector = LoopDetector({
    'THRESHOLD': 10,  # 提高阈值
    'WINDOW_SIZE': 50  # 扩大窗口
})

# 添加白名单
detector.add_to_whitelist('read')
detector.add_to_whitelist('write')
```

## 错误调试技巧

### 1. 启用详细日志

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 2. 使用断言

```python
def validate_memory(key, value):
    assert key is not None, "键不能为None"
    assert isinstance(value, (str, int, float, bool, dict, list)), \
        f"值的类型无效: {type(value)}"
    return True
```

### 3. 错误追踪

```python
import traceback

try:
    risky_operation()
except Exception as e:
    trace = traceback.format_exc()
    print(f"完整错误追踪:\n{trace}")
```

## 总结

QuickAgents的错误处理系统遵循以下原则:

1. **明确的错误类型** - 每种错误都有明确的类型
2. **详细的错误信息** - 包含足够的上下文信息
3. **可恢复性** - 提供恢复建议
4. **可追踪** - 支持日志记录和监控
5. **一致性** - 统一的错误格式

通过遵循本指南，可以确保QuickAgents应用的稳定性和可维护性。
