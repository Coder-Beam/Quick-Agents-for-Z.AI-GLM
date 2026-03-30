# QuickAgents 统一插件架构

> 版本: 2.2.0 | 更新时间: 2026-03-30

## 概述

QuickAgents采用**单一统一插件**架构，将所有功能整合到 `.opencode/plugins/quickagents.ts` 中，在"启动QuickAgents"时自动安装。

---

## 一、统一插件设计

### 1.1 设计原则

| 原则 | 说明 |
|------|------|
| 单一入口 | 一个插件文件，而非多个分散插件 |
| 自动安装 | 启动流程中自动检测并安装 |
| 模块化内部 | 内部按功能模块划分，可独立开关 |
| 零配置启动 | 默认启用所有功能，无需手动配置 |

### 1.2 插件位置

```
.opencode/
└── plugins/
    └── quickagents.ts    # 统一插件（唯一）
```

### 1.3 启用方式

```json
// opencode.json
{
  "plugin": ["@quickagents/unified"]
}
```

---

## 二、插件模块

### 2.1 FileManager Cache

**功能**: 文件哈希检测，缓存未变文件

**Token节省**: 60-100%

**工作流程**:
```
read工具调用
    ↓
tool.execute.before
    ↓
检测文件哈希
    ↓
    ├─ 哈希相同 → 抛出FILE_UNCHANGED → AI使用缓存
    │
    └─ 哈希不同 → 正常读取 → 更新缓存
```

### 2.2 LoopDetector (Pattern-based)

**功能**: Pattern-based循环检测，防止死循环

**Token节省**: 100%（本地处理）

**检测模式**:

| 模式 | 定义 | 示例 | 触发阈值 |
|------|------|------|----------|
| Stuck | 同一操作连续重复 | A→A→A | 3次 |
| Oscillation | 两个操作交替循环 | A→B→A→B | 2周期 |

**允许模式**:
- A→B→C (正常探索，不同操作)
- read(file1)→read(file2)→read(file3) (不同参数)

**行为**:
```
检测到循环 → 抛出DOOM_LOOP_DETECTED → 显示Pattern类型 → 暂停执行
```

**实现细节**:
- 维护最近20次工具调用序列
- 60秒滑动窗口
- 指纹: `${toolName}:${normalizedArgs}`

### 2.3 Reminder

**功能**: 事件驱动提醒

**提醒类型**:
| 类型 | 触发条件 | 提醒内容 |
|------|----------|----------|
| 工具调用 | 每5次调用 | 检查进度 |
| 长时间运行 | 10/30分钟 | 分阶段建议 |
| 错误累计 | 连续错误 | 根因分析建议 |

### 2.4 SkillEvolution

**功能**: 自动触发Skills进化

**触发时机**:
| 时机 | 操作 |
|------|------|
| Skill使用后 | 记录使用统计 |
| Git提交后 | 分析提交内容 |
| Session结束 | 触发定期优化 |

### 2.5 FeedbackCollector

**功能**: 自动收集错误和经验

**收集类型**:
- 工具调用错误
- Session错误
- 循环检测事件

---

## 三、插件Hooks映射

| Hook | 模块 | 功能 |
|------|------|------|
| `tool.execute.before` | FileManager, LoopDetector | 缓存检查、循环检测 |
| `tool.execute.after` | FileManager, Reminder, SkillEvolution, Feedback | 缓存更新、计数、记录 |
| `file.watcher.updated` | FileManager | 缓存失效 |
| `session.status` | Reminder | 长时间运行检查 |
| `session.error` | Reminder, Feedback | 错误记录 |
| `session.deleted` | All | 状态清理 |
| `command.executed` | SkillEvolution | Git提交触发 |

---

## 四、安装流程

### 4.1 自动安装（推荐）

在"启动QuickAgents"时自动执行：

```
1. 检查 .opencode/plugins/quickagents.ts
   ├─ 存在 → 跳过
   └─ 不存在 → 从QuickAgents仓库复制

2. 检查 pip install quickagents
   ├─ 已安装 → 跳过
   └─ 未安装 → 执行安装

3. 输出：「QuickAgents插件已安装」
```

### 4.2 手动安装

```bash
# 1. 复制插件文件
cp /path/to/QuickAgents/.opencode/plugins/quickagents.ts .opencode/plugins/

# 2. 安装Python包
pip install quickagents

# 3. 验证
python -c "from quickagents import UnifiedDB; print('OK')"
```

---

## 五、配置选项

### 5.1 启用/禁用模块

插件内部支持模块开关：

```typescript
// 默认配置
const config = {
  fileManagerCache: true,   // 文件缓存
  loopDetector: true,       // 循环检测
  reminder: true,           // 提醒
  skillEvolution: true,     // 进化
  feedbackCollector: true,  // 反馈收集
};
```

### 5.2 阈值配置

```typescript
// 循环检测阈值
LOOP_THRESHOLD = 3;         // 重复次数
LOOP_TIME_WINDOW = 60000;   // 时间窗口（毫秒）

// 提醒阈值
TOOL_CALL_THRESHOLD = 5;    // 工具调用次数
LONG_RUN_MINUTES = [10, 30]; // 长时间运行提醒
```

---

## 六、性能影响

| 指标 | 数值 |
|------|------|
| 内存占用 | ~10MB |
| 延迟（每工具调用） | <10ms |
| Python调用延迟 | <50ms |
| 总体影响 | 可忽略 |

---

## 七、错误处理

### 7.1 FILE_UNCHANGED

```
[QuickAgents] FILE_UNCHANGED: /path/to/file.ts
文件未变化，请使用对话上下文中的缓存内容。
如需强制重新读取，请明确说明。
```

**AI行为**: 使用上下文中的缓存内容，不重新读取

### 7.2 DOOM_LOOP_DETECTED

```
[QuickAgents] DOOM_LOOP_DETECTED
工具: read
次数: 3 次/分钟
操作: 请验证你的方法或请求用户确认。
```

**AI行为**: 暂停执行，评估方法或请求用户确认

---

## 八、与旧架构对比

| 方面 | 旧架构（多插件） | 新架构（统一插件） |
|------|-----------------|-------------------|
| 插件数量 | 6个独立插件 | 1个统一插件 |
| 安装复杂度 | 需逐个启用 | 自动安装 |
| 维护成本 | 分散维护 | 集中维护 |
| 配置复杂度 | 多个配置 | 单一配置 |
| 启动时间 | 较慢 | 更快 |

---

## 九、版本历史

### v2.0.0 (2026-03-30)
- 合并所有插件为统一插件
- 添加自动安装流程
- 简化配置

### v1.0.0 (2026-03-30)
- 初始设计（多插件架构）

---

*文档版本: 2.0.0 | 更新时间: 2026-03-30*
