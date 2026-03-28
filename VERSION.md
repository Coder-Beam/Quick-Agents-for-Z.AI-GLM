# QuickAgents Version

> 版本信息文件 - 用于版本检测和更新

---

## 当前版本

| 属性 | 值 |
|------|-----|
| 版本号 | 2.1.1 |
| Git标签 | v2.1.1 |
| 发布日期 | 2026-03-28 |
| 最低兼容版本 | 2.0.0 |
| 仓库地址 | https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM |

---

## 版本历史

### v2.1.1 (2026-03-28)

**新增功能**:
- `feedback-collector-skill` - 经验收集系统
  - 5种经验类型收集（Bug/改进/最佳实践/Skill评估/Agent评估）
  - 自动触发：任务完成+Git提交
  - 手动命令：`/feedback <类型> <描述>`
  - 存储位置：`~/.quickagents/feedback/`

**更新内容**:
- Skills总数: 18 → 19
- AGENTS.md 新增「二一、经验收集规范」章节

---

### v2.1.0 (2026-03-27)

**新增Skills** (基于研究论文):

| 优先级 | Skill | 来源 |
|--------|-------|------|
| P0 | lazy-discovery-skill | OpenDev |
| P0 | event-reminder-skill | OpenDev |
| P0 | doom-loop-skill | OpenDev |
| P1 | adaptive-compression-skill | VeRO |
| P1 | vero-evaluation-skill | VeRO |
| P2 | aci-design-skill | SWE-agent |

**新增配置**:
- `.opencode/evaluation/vero-config.yaml`
- `.opencode/snapshots/`
- `.opencode/traces/`

**AGENTS.md 更新**:
- 新增「八、事件驱动提醒机制」章节
- 新增「九、ACI设计原则」章节
- 添加压缩阈值策略(70%/80%/85%/90%/99%)

---

### v2.0.1 (2026-03-25)

**首个正式版本**:
- 标准化启动流程
- 三维记忆系统
- 17个专业代理
- 12个核心技能
- 完整文档体系

---

## 远程版本检测URL

```
https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/VERSION.md
```

---

## 更新命令

```bash
/qa-update              # 检测并更新
/qa-update --check      # 仅检测，不更新
/qa-update --version    # 显示当前版本
```

---

*最后更新: 2026-03-28*
