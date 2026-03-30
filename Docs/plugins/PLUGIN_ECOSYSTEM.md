# QuickAgents 插件生态与业务流程

## 一、插件关系分析

### 1.1 当前配置的插件

| 插件 | 来源 | 功能 | 关系 |
|------|------|------|------|
| `@obra/superpowers` | GitHub obra/superpowers | 开发技能集合（brainstorming, TDD, code review等） | **独立** |
| `@coder-beam/quickagents` | 本地 `.opencode/plugins/` | Token优化（缓存、循环检测、本地执行） | **独立** |
| `@tarquinen/opencode-dcp` | - | DCP协议 | **未知**（可能来自superpowers） |
| `@zenobius/opencode-skillful` | - | 技能管理 | **未知**（可能来自superpowers） |
| `@kdco/worktree` | - | Git worktree | **未知**（可能来自superpowers） |

### 1.2 依赖关系

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenCode 插件系统                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  opencode.json                                               │
│       │                                                       │
│       ├─► @obra/superpowers (远程)                             │
│       │        ├─ brainstorming                                │
│       │        ├─ tdd-workflow                                 │
│       │        ├─ code-review                                  │
│       │        └─ ... (更多技能)                               │
│       │                                                       │
│       └─► @coder-beam/quickagents (本地)                        │
│                ├─ FileManager Cache                               │
│                ├─ LoopDetector                                    │
│                ├─ LocalExecutor                                    │
│                ├─ Reminder                                         │
│                └─ SkillEvolution                                   │
│                                                               │
│  关系：两者并列，无依赖关系                              │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**结论**：
- **Superpowers** 和 **QuickAgents** 是**并列关系**，各自独立工作
- **无依赖关系**：QuickAgents不依赖superpowers，反之亦然
- **功能互补**：
  - Superpowers：提供开发方法论（TDD、代码审查等）
  - QuickAgents：提供Token优化（缓存、本地执行等）

---

## 二、 QuickAgents 业务流程

### 2.1 启动流程（"启动QuickAgents"）

```
用户输入："启动QuickAgents"
         ↓
AI 读取 AGENTS.md
         ↓
检查 .opencode/plugins/quickagents.ts 是否存在
         ↓
    ┌─ 存在 → 跳过安装
    └─ 不存在 → 从仓库复制
         ↓
检查 pip install quickagents 是否已安装
         ↓
    ┌─ 已安装 → 跳过
    └─ 未安装 → 执行 pip install quickagents
         ↓
AI 输出："QuickAgents插件已安装"
         ↓
OpenCode 自动加载 .opencode/plugins/ 下的插件
         ↓
QuickAgents 插件激活（Hooks注册）
         ↓
开始7层询问卡 / 继续开发
```

### 2.2 插件工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                   QuickAgents 插件工作流                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. tool.execute.before Hook                               │
│     ├─ 拦截 read → FileManager Cache 检查                   │
│     │    └─ 文件未变化 → FILE_UNCHANGED → 节省Token         │
│     │    └─ 文件已变化 → 继续执行                            │
│     │                                                       │
│     ├─ 拦截 bash qa → LocalExecutor.qa 处理                │
│     │    └─ 本地执行Python → LOCAL_RESULT → 节省Token       │
│     │                                                       │
│     ├─ 拦截 grep → LocalExecutor.grep 处理                 │
│     │    └─ 本地执行ripgrep → LOCAL_RESULT → 节省Token      │
│     │                                                       │
│     ├─ 拦截 glob → LocalExecutor.glob 处理                 │
│     │    └─ 本地遍历文件 → LOCAL_RESULT → 节省Token         │
│     │                                                       │
│     └─ LoopDetector 检测                                   │
│          └─ 检测到循环 → DOOM_LOOP_DETECTED → 中断执行      │
│                                                               │
│  2. tool.execute.after Hook                                │
│     ├─ FileManager Cache 更新                               │
│     ├─ Reminder 计数                                        │
│     └─ SkillEvolution 记录                                  │
│                                                               │
│  3. 其他 Hooks                                              │
│     ├─ file.watcher.updated → 缓存失效                      │
│     ├─ session.status → 长时间运行提醒                      │
│     ├─ session.error → 错误收集                             │
│     ├─ session.deleted → 状态清理                           │
│     └─ command.executed → Git提交触发进化                   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、 安装时机

### 3.1 当前设计
- **触发时机**：用户输入"启动QuickAgents"时
- **安装位置**：`.opencode/plugins/quickagents.ts`
- **配置位置**：`opencode.json`

### 3.2 是否需要统一安装？

**当前状态**：
- QuickAgents插件已放置在 `.opencode/plugins/` 目录
- OpenCode会**自动加载**该目录下的插件
- 无需用户手动安装

**优化建议**：

由于QuickAgents插件是本地文件，OpenCode会自动加载，因此：

1. **不需要**在"启动QuickAgents"时重新安装插件
2. **需要**确保：
   - `.opencode/plugins/quickagents.ts` 存在
   - `opencode.json` 中配置了 `@coder-beam/quickagents`
   - `pip install quickagents` 已执行（Python API可用）

### 3.3 修改后的启动流程

```
用户输入："启动QuickAgents"
         ↓
AI 读取 AGENTS.md
         ↓
检查 .opencode/plugins/quickagents.ts
         ↓
    ┌─ 存在 → 检查Python包
    └─ 不存在 → 提示错误
         ↓
检查 pip show quickagents
         ↓
    ┌─ 已安装 → 继续
    └─ 未安装 → 执行 pip install quickagents
         ↓
AI 输出："QuickAgents已就绪"
         ↓
开始7层询问卡 / 继续开发
```

**注意**：由于插件文件已在 `.opencode/plugins/` 目录，OpenCode会自动加载，无需手动安装。

---

## 四、 总结

| 问题 | 答案 |
|------|------|
| Superpowers和QuickAgents关系？ | 并列关系，无依赖 |
| 是否需要统一安装？ | 不需要，OpenCode自动加载本地插件 |
| 启动时做什么？ | 检查Python包是否安装，插件自动加载 |
| 插件何时激活？ | OpenCode启动时自动加载 `.opencode/plugins/` 下的插件 |

---

*文档版本: 1.0.0 | 创建时间: 2026-03-30*
