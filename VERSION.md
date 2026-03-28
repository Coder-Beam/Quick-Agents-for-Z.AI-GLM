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

## 本次更新 (v2.1.1)

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
