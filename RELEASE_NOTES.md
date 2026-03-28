# QuickAgents v2.1.1 Release Notes

> AI代理项目初始化系统 - 经验收集增强

**发布日期**: 2026-03-28

---

## 🎉 简介

QuickAgents是一个基于OpenCode生态的AI代理项目初始化系统，提供：
- 🚀 **开箱即用**：发送"启动QuickAgent"即可开始
- 🧠 **三维记忆**：跨会话上下文保持和经验积累
- 🤖 **多代理协作**：17个专业代理 + 18个核心技能
- 📊 **进度追踪**：Boulder系统实现跨会话恢复
- ⚡ **超高效执行**：ultrawork命令一键完成复杂任务
- 📝 **经验收集**：自动收集使用经验，助力系统进化

---

## ✨ 核心特性

### 1. 项目初始化
- **智能检测**：自动识别新项目/现有项目
- **12轮需求澄清**：深度递进式需求分析
- **自动文档生成**：MEMORY.md、TASKS.md、DESIGN.md等

### 2. 代理系统（17个）

#### 核心代理（6个）
| 代理 | 功能 |
|------|------|
| `@yinglong-init` | 项目初始化 |
| `@boyi-consult` | 需求分析 |
| `@chisongzi-advise` | 技术推荐 |
| `@cangjie-doc` | 文档管理 |
| `@huodi-skill` | Skill管理 |
| `@fenghou-orchestrate` | 主调度器 |

#### 质量代理（4个）
- `@jianming-review` - 代码审查
- `@lishou-test` - 测试执行
- `@mengzhang-security` - 安全审计
- `@hengge-perf` - 性能分析

#### 工具代理（4个）
- `@kuafu-debug` - 调试
- `@gonggu-refactor` - 重构
- `@huodi-deps` - 依赖管理
- `@hengge-cicd` - CI/CD管理

#### 规划代理（3个）
- `@fenghou-plan` - 规划器
- `@boyi-consult` - 顾问
- `@jianming-review` - 审查员

### 3. 技能系统（14个）

| 技能 | 功能 |
|------|------|
| `inquiry-skill` | 12轮需求澄清 |
| `project-memory-skill` | 三维记忆系统 |
| `tdd-workflow-skill` | TDD工作流 |
| `git-commit-skill` | Git提交规范 |
| `code-review-skill` | 代码审查 |
| `category-system-skill` | Category分类 |
| `background-agents-skill` | 后台并行执行 |
| `boulder-tracking-skill` | 进度追踪 |
| `skill-integration-skill` | 技能整合 |
| `multi-model-skill` | 多模型协同 |
| `lsp-ast-skill` | LSP/AST集成 |
| `project-detector-skill` | 项目检测 |
| `project-memory-skill` | 知识索引 |

### 4. 高级功能

#### ultrawork命令
```bash
/ultrawork 实现用户认证系统
```
自动分解任务、并行执行、汇总结果。

#### start-work命令
```bash
/start-work
```
跨会话恢复工作，读取进度、学习点、决策记录。

#### Boulder进度追踪
```json
{
  "session_id": "abc123",
  "completed_tasks": 43,
  "total_tasks": 44,
  "notepad": {
    "learnings": [...],
    "decisions": [...]
  }
}
```

#### Category系统（10个）
- `visual-engineering` - UI开发
- `ultrabrain` - 深度推理
- `quick` - 快速响应
- `planning` - 计划制定
- `coding` - 代码编写
- `testing` - 测试验证
- `documentation` - 文档编写
- `analysis` - 数据分析
- `debugging` - 问题调试
- `refactoring` - 代码重构

---

## 📊 测试结果

| 测试类型 | 通过率 | 详情 |
|---------|--------|------|
| 单元测试 | 97.0% | 192/198 |
| 集成测试 | 85.7% | 24/28 |
| E2E测试 | 80.8% | 21/26 |
| 性能测试 | 93.8% | 15/16 |
| **总体** | **90.4%** | **252/268** |

### 性能指标
- 配置加载：< 5ms
- 文件总大小：< 250KB
- 组件数量：34个

---

## 📦 安装

```bash
# 克隆仓库
git clone https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM.git

# 复制到你的项目
cp -r Quick-Agents-for-Z.AI-GLM/.opencode your-project/
cp Quick-Agents-for-Z.AI-GLM/AGENTS.md your-project/
```

---

## 🚀 快速开始

1. 在OpenCode中发送：
```
启动QuickAgent
```

2. 完成12轮需求澄清

3. 开始开发：
```
@fenghou-orchestrate 实现用户认证功能
```

---

## 📚 文档

- [用户指南](Docs/USER_GUIDE.md)
- [API参考](Docs/API_REFERENCE.md)
- [示例代码](Docs/EXAMPLES.md)
- [测试报告](Docs/TEST_REPORT.md)

---

## 🔄 升级指南

从v8.0升级到v2.0.1：

1. 备份现有配置
```bash
cp -r .opencode .opencode.backup
```

2. 更新文件
```bash
# 复制新版本文件
cp -r Quick-Agents-for-Z.AI-GLM/.opencode/* .opencode/
cp Quick-Agents-for-Z.AI-GLM/AGENTS.md .
```

3. 验证安装
```bash
node tests/run-all-tests.js
```

---

## 🐛 已知问题

1. **models.json为空** - 多模型协同配置需手动填充
2. **lsp-config.json为空** - LSP配置需手动填充
3. **部分Skill缺少"使用场景"** - 文档待完善

---

## 🆕 v2.1.1 更新内容

### 新增功能

#### 经验收集系统

新增 `feedback-collector-skill`，自动收集使用过程中的经验：

**存储位置**: `~/.quickagents/feedback/`

| 文件 | 内容 |
|------|------|
| bugs.md | Bug/错误 |
| improvements.md | 改进建议 |
| best-practices.md | 最佳实践 |
| skill-review.md | Skill评估 |
| agent-review.md | Agent评估 |

**命令集**:
```bash
/feedback bug <描述>       # 记录Bug
/feedback improve <描述>   # 记录改进建议
/feedback best <描述>      # 记录最佳实践
/feedback skill <名> <评>  # 评估Skill
/feedback agent <名> <评>  # 评估Agent
/feedback view [类型]      # 查看收集的经验
```

**触发机制**:
- 任务完成时自动分析
- Git提交后自动分析
- 支持手动触发

**去重逻辑**: 同一小时内相似描述只保留一条

### 文档更新

- 新增设计文档: `Docs/specs/2026-03-28-feedback-collector-design.md`
- AGENTS.md 新增「二一、经验收集规范」章节
- Skills总数: 17 → 18

---

## 🆕 v2.1.0 更新内容

### 新增Skills（基于OpenDev/VeRO/SWE-agent论文）

#### P0 优先级 - 立即可实施
| Skill | 功能 | 来源 |
|-------|------|------|
| `lazy-discovery-skill` | 工具懒加载，减少初始上下文50%+ | OpenDev |
| `event-reminder-skill` | 事件驱动提醒，对抗指令遗忘 | OpenDev |
| `doom-loop-skill` | 循环检测机制，防止重复调用 | OpenDev |

#### P1 优先级 - 短期可实施
| Skill | 功能 | 来源 |
|-------|------|------|
| `adaptive-compression-skill` | 自适应压缩策略，峰值上下文减少54% | OpenDev |
| `vero-evaluation-skill` | 版本化评估体系(V-E-R-O) | VeRO |

#### P2 优先级 - 中期可实施
| Skill | 功能 | 来源 |
|-------|------|------|
| `aci-design-skill` | ACI设计原则(4大原则) | SWE-agent |

### 新增配置和目录
- `.opencode/evaluation/vero-config.yaml` - VeRO评估配置
- `.opencode/snapshots/` - 快照存储目录
- `.opencode/traces/` - 追踪记录目录

### AGENTS.md 更新
- 新增「八、事件驱动提醒机制」章节
- 新增「九、ACI设计原则」章节
- 添加压缩阈值策略(70%/80%/85%/90%/99%)
- 添加Doom-Loop防护配置
- 添加核心常量定义

### 核心常量
```python
MAX_UNDO_HISTORY = 50
DOOM_LOOP_THRESHOLD = 3
DOOM_LOOP_WINDOW = 20
MAX_CONCURRENT_TOOLS = 5
TOOL_OUTPUT_OFFLOAD_THRESHOLD = 8000
MAX_TOOL_RESULT_SUMMARY = 300
SUBAGENT_ITERATION_LIMIT = 15
```

---

## 🗺️ 路线图

### v1.1.0（计划）
- 填充models.json和lsp-config.json
- 添加更多测试场景
- 优化文档完整性

### v1.2.0（计划）
- 支持自定义Category
- 添加更多LSP支持
- 性能优化

---

## 🤝 贡献

欢迎提交Issue和Pull Request！

- GitHub: https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM
- Issues: https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/issues

---

## 📄 许可证

MIT License

---

## 🙏 致谢

感谢以下项目的启发：
- [Oh-My-OpenAgent](https://github.com/anthropics/anthropic-quickstarts/tree/main/agents/oh-my-openagent)
- OpenCode社区
- 所有贡献者

---

*QuickAgents v2.1.0 - 让AI代理开发更简单*
