# QuickAgents 工具调用错误修复指南

## 概述

本文档解决QuickAgents在使用Write、Edit等工具时遇到的常见参数错误问题。

---

## 一、常见错误类型

### 1.1 Edit工具 - oldString not found

**错误表现**:
```
Error: oldString not found in content
```

**原因分析**:
1. 文件内容已变化，缓存的oldString失效
2. 换行符不一致（CRLF vs LF）
3. 特殊字符未正确转义
4. 复制粘贴时丢失格式

**解决方案**:

```python
# 方案A: 使用本地FileManager（推荐）
from quickagents import FileManager

fm = FileManager()
result = fm.edit('path/to/file.py', 'old content', 'new content')

if result['success']:
    print(f"✅ 编辑成功，节省Token: {result['token_saved']}")
else:
    print(f"❌ 编辑失败: {result['message']}")
```

```bash
# 方案B: 使用CLI工具
qka edit <file> "<old>" "<new>"
```

### 1.2 Write工具 - 文件未先读取

**错误表现**:
```
Error: You must use the Read tool first
```

**原因分析**:
- OpenCode要求在Write覆盖现有文件前先Read

**解决方案**:

```python
# 方案A: 使用本地FileManager（自动处理）
from quickagents import FileManager

fm = FileManager()
# FileManager内部自动处理哈希检测，无需手动Read
fm.write('path/to/file.py', 'new content')
```

```bash
# 方案B: 使用CLI工具
qka write <file> "<content>"
```

### 1.3 路径错误

**错误表现**:
```
Error: File not found
```

**原因分析**:
1. 相对路径与绝对路径混淆
2. 路径分隔符问题（Windows vs Unix）
3. 文件实际不存在

**解决方案**:

```python
# 始终使用绝对路径
import os

file_path = os.path.abspath('relative/path/to/file.py')
print(f"绝对路径: {file_path}")

# 或使用Path
from pathlib import Path
file_path = str(Path('relative/path').resolve())
```

### 1.4 编码问题

**错误表现**:
- 中文乱码
- 特殊字符丢失

**解决方案**:

```python
# 始终使用UTF-8编码
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(content)
```

---

## 二、哈希检测优化方案

### 2.1 核心原理

```
┌─────────────────────────────────────────────────────────────┐
│                    哈希检测工作流程                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  传统方式:                                                  │
│  AI调用Read → 读取整个文件 → 消耗大量Token                  │
│                                                             │
│  哈希检测方式:                                              │
│  1. 本地计算文件哈希 (0 Token)                              │
│  2. 对比SQLite缓存中的哈希 (0 Token)                        │
│  3. 哈希相同 → 使用缓存内容 (0 Token)                       │
│  4. 哈希不同 → 读取文件更新缓存 (消耗Token)                 │
│                                                             │
│  Token节省: 90%+                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 使用方式

```python
from quickagents import FileManager, CacheDB

# 初始化
fm = FileManager()
db = CacheDB('.quickagents/cache.db')

# 智能读取（自动哈希检测）
content, changed = fm.read_if_changed('Docs/MEMORY.md')

if changed:
    print("文件已变化，重新读取")
else:
    print("使用缓存，节省Token！")

# 查看统计
stats = db.get_stats()
print(f"已缓存 {stats['file_cache']['count']} 个文件")
print(f"节省Token估算: {stats['tokens']['total_saved']}")
```

### 2.3 CLI使用

```bash
# 智能读取
qka read Docs/MEMORY.md

# 查看缓存统计
qka cache stats

# 查看缓存文件列表
qka cache list

# 清空缓存
qka cache clear
```

---

## 三、SQLite缓存系统

### 3.1 数据库结构

```sql
-- 文件缓存表
CREATE TABLE file_cache (
    path TEXT PRIMARY KEY,
    content_hash TEXT,
    content TEXT,
    size INTEGER,
    mtime REAL,
    access_count INTEGER
);

-- 记忆存储表
CREATE TABLE memory (
    key TEXT PRIMARY KEY,
    value TEXT,
    memory_type TEXT,
    tags TEXT
);

-- 操作历史表
CREATE TABLE operation_history (
    operation TEXT,
    target TEXT,
    token_cost INTEGER,
    created_at TEXT
);

-- 循环检测表
CREATE TABLE loop_detection (
    fingerprint TEXT PRIMARY KEY,
    tool_name TEXT,
    count INTEGER
);
```

### 3.2 存储位置

```
项目根目录/
└── .quickagents/
    └── cache.db    # SQLite数据库
```

### 3.3 优势

| 特性 | 说明 |
|------|------|
| 零安装 | Python内置sqlite3模块 |
| 高性能 | 单文件数据库，读写快 |
| 事务安全 | 数据不会损坏 |
| 支持查询 | 可按路径、时间、哈希查询 |
| 跨平台 | Windows/Mac/Linux通用 |

---

## 四、最佳实践

### 4.1 文件操作流程

```python
# 推荐：使用FileManager
from quickagents import FileManager

fm = FileManager()

# 读取
content = fm.read('file.py')

# 编辑（自动验证缓存）
result = fm.edit('file.py', 'old', 'new')
if not result['success']:
    # 处理错误
    print(result['message'])

# 写入
fm.write('file.py', 'new content')
```

### 4.2 循环检测

```python
from quickagents import LoopDetector

detector = LoopDetector(threshold=3)

# 每次工具调用前检查
result = detector.check('read', {'path': 'file.py'})
if result and result['detected']:
    print(f"检测到循环: {result['tool_name']} 已调用 {result['count']} 次")
    # 触发用户确认或调整策略
```

### 4.3 记忆管理

```python
from quickagents import MemoryManager, CacheDB

# 使用SQLite存储记忆
db = CacheDB()

# 设置记忆
db.set_memory('project.name', 'QuickAgents', memory_type='factual')
db.set_memory('current_task', '实现FileManager', memory_type='working')

# 获取记忆
name = db.get_memory('project.name')

# 搜索记忆
results = db.search_memory('FileManager')
```

---

## 五、错误排查清单

当遇到工具调用错误时，按以下顺序检查：

- [ ] 1. 文件路径是否正确（使用绝对路径）
- [ ] 2. 文件是否存在
- [ ] 3. 文件编码是否为UTF-8
- [ ] 4. oldString是否完全匹配（注意换行符）
- [ ] 5. 是否使用了FileManager替代直接工具调用
- [ ] 6. 缓存是否需要清理
- [ ] 7. 查看错误日志定位具体问题

---

## 六、迁移指南

### 从直接工具调用迁移到本地化

**之前**:
```
AI调用Read → 消耗Token → AI调用Edit → 可能失败
```

**之后**:
```python
from quickagents import FileManager

fm = FileManager()
content = fm.read('file.py')  # 哈希检测，可能节省Token
fm.edit('file.py', 'old', 'new')  # 自动验证，减少失败
```

### Token节省估算

| 操作 | 之前 | 之后 | 节省 |
|------|------|------|------|
| Read未变文件 | ~1000 tokens | 0 tokens | 100% |
| Edit验证 | ~500 tokens | 0 tokens | 100% |
| 记忆读取 | ~300 tokens | 0 tokens | 100% |
| 循环检测 | ~200 tokens | 0 tokens | 100% |

---

*文档版本: 1.0.0 | 创建时间: 2026-03-29*
