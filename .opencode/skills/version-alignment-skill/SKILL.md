---
name: version-alignment-skill
version: 1.0.0
description: QuickAgents版本对齐检查 - 确保所有Agent和Skill与当前版本功能对齐
license: MIT
allowed-tools:
  - read
  - grep
  - glob
  - bash
---

# 版本对齐检查技能

## 功能说明

此技能用于确保QuickAgents的所有组件（Agent、Skill、Plugin）与当前版本（v2.6.8）的功能对齐。

## 检查项

### 1. Agent API 对齐

检查所有Agent是否包含当前版本的Python API使用说明：

| API | 必须包含在 |
|-----|----------|
| UnifiedDB | yinglong-init, cangjie-doc, fenghou-orchestrate |
| MarkdownSync | cangjie-doc |
| SkillEvolution | huodi-skill, jianming-review |
| KnowledgeGraph | boyi-consult, cangjie-doc |
| LoopDetector | kuafu-debug, fenghou-orchestrate |
| Reminder | 所有执行类Agent |

### 2. 版本号一致性

检查所有文件中的版本号是否一致：

```
pyproject.toml: version = "2.6.8"
quickagents/__init__.py: __version__ = '2.6.8'
.opencode/plugins/package.json: "version": "2.6.8"
VERSION.md: ## 2.6.8
```

### 3. 功能完整性

检查新版本功能是否在相关组件中体现：

| v2.6.8 功能 | 必须出现在 |
|-------------|----------|
| Pattern-based LoopDetector | kuafu-debug, doom-loop-skill |
| SkillEvolution | huodi-skill, feedback-collector-skill |
| KnowledgeGraph | boyi-consult, cangjie-doc |
| MarkdownSync | cangjie-doc, project-memory-skill |

## 使用方法

### 手动检查

```bash
# 检查所有组件
/qa-check-alignment

# 检查特定组件
/qa-check-alignment --agent cangjie-doc
/qa-check-alignment --skill tdd-workflow-skill
```

### 自动检查

在以下场景自动触发：
- Git提交前（通过pre-commit hook）
- QuickAgents版本更新后
- 新Agent/Skill安装后

## 检查流程

```
1. 读取当前版本号（VERSION.md）
2. 获取版本功能列表
3. 扫描所有Agent配置文件
4. 检查API使用情况
5. 检查版本号一致性
6. 生成对齐报告
7. 提供修复建议
```

## 对齐报告格式

```markdown
# 版本对齐检查报告

## 检查信息
- QuickAgents版本: 2.6.8
- 检查时间: 2026-03-30T10:00:00Z
- 检查组件数: 15 Agents, 24 Skills

## 对齐状态

### Agents (15/15 已对齐)
| Agent | 状态 | 缺失功能 |
|-------|------|----------|
| yinglong-init | ✅ | - |
| cangjie-doc | ✅ | - |
| fenghou-orchestrate | ✅ | - |
| ... | ... | ... |

### Skills (24/24 已对齐)
| Skill | 状态 | 缺失功能 |
|-------|------|----------|
| tdd-workflow-skill | ✅ | - |
| code-review-skill | ✅ | - |
| ... | ... | ... |

## 版本号一致性
- pyproject.toml: ✅ 2.6.8
- quickagents/__init__.py: ✅ 2.6.8
- .opencode/plugins/package.json: ✅ 2.6.8

## 修复建议

### 需要更新的组件
1. **agent-name**: 缺少 UnifiedDB API 使用说明
2. **skill-name**: 缺少 v2.6.8 新功能集成

## 下一步操作
1. 运行 `/qa-update-agent agent-name` 更新Agent
2. 运行 `/qa-update-skill skill-name` 更新Skill
```

## 版本更新检查清单

当QuickAgents版本更新时，必须执行以下检查：

### 必须更新
- [ ] pyproject.toml 版本号
- [ ] quickagents/__init__.py __version__
- [ ] .opencode/plugins/package.json 版本号
- [ ] VERSION.md 版本说明
- [ ] CHANGELOG.md 变更日志

### Agent更新
- [ ] 检查所有Agent是否包含新API
- [ ] 更新yinglong-init的启动流程
- [ ] 更新cangjie-doc的同步逻辑
- [ ] 更新huodi-skill的进化集成
- [ ] 更新其他相关Agent

### Skill更新
- [ ] 检查所有Skill是否使用新功能
- [ ] 更新doom-loop-skill的检测算法
- [ ] 更新project-memory-skill的存储方式
- [ ] 更新feedback-collector-skill的收集逻辑

### 文档更新
- [ ] AGENTS.md 添加新API使用说明
- [ ] README.md 更新功能列表
- [ ] Docs/api/ 更新API文档

## 自动修复

对于检测到的对齐问题，可以自动修复：

```bash
# 自动修复所有对齐问题
/qa-auto-align

# 仅修复特定类型
/qa-auto-align --type agents
/qa-auto-align --type skills
```

## 注意事项

1. **版本号必须一致**：所有组件必须使用相同的版本号
2. **API必须完整**：所有相关组件必须包含新版本API
3. **文档必须同步**：功能更新必须同步更新文档
4. **测试必须通过**：更新后必须运行测试确保兼容性

---

*版本: 1.0.0 | 创建时间: 2026-03-30*
*适用于 QuickAgents v2.6.8+*
