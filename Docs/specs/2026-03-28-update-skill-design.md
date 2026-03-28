# QuickAgents Update Skill 设计文档

> **版本**: v1.0.0  
> **创建日期**: 2026-03-28  
> **状态**: 设计阶段

---

## 一、核心目标

让用户项目能及时获得QuickAgents的新特性，通过内置 `/qa-update` 命令实现版本检测和更新。

---

## 二、版本检测

### VERSION.md 结构

在QuickAgents仓库根目录创建：

```markdown
# QuickAgents Version

## 当前版本

| 属性 | 值 |
|------|-----|
| 版本号 | 2.1.1 |
| Git标签 | v2.1.1 |
| 发布日期 | 2026-03-28 |
| 最低兼容版本 | 2.0.0 |

## 更新说明

### v2.1.1 (2026-03-28)
- 新增 feedback-collector-skill 经验收集功能
- Skills总数: 18 → 19

### v2.1.0 (2026-03-27)
- 新增6个研究论文Skills
- 新增ACI设计原则

### v2.0.1 (2026-03-25)
- 首个正式版本
```

### 检测流程

```
启动QuickAgent
    ↓
读取本地 .quickagents/VERSION.md
    ↓
获取远程 VERSION.md (GitHub Raw)
    ↓
对比版本号
    ↓
┌─────────┬─────────┐
│ 相同    │ 不同    │
│ 无操作  │ 提示更新│
└─────────┴─────────┘
```

---

## 三、更新流程

```
/qa-update
    ↓
1. 检测新版本
    ↓
2. 显示更新日志，用户确认
    ↓
3. 备份当前配置
   - .opencode/config/ → .opencode/config.backup/
   - Docs/ → Docs.backup/
    ↓
4. 下载更新
   - .opencode/agents/
   - .opencode/skills/
   - .opencode/commands/
   - .opencode/hooks/
   - AGENTS.md
   - VERSION.md
    ↓
5. 处理配置
   - 智能合并用户修改
   - 冲突文件保留备份
    ↓
6. 同步文档
   - Docs/ ↔ .opencode/memory/
    ↓
7. 显示更新完成
```

---

## 四、配置处理策略

### 需备份的文件/目录

| 类型 | 路径 | 处理方式 |
|------|------|----------|
| 配置 | .opencode/config/ | 备份 + 智能合并 |
| 文档 | Docs/ | 备份 + 覆盖更新 |
| 记忆 | .opencode/memory/ | 不更新（用户数据） |
| 进度 | .quickagents/ | 不更新（用户数据） |

### 智能合并规则

```yaml
合并策略:
  categories.json:
    - 保留用户自定义分类
    - 新增官方分类
    - 冲突时用户优先
  
  quickagents.json:
    - 保留用户配置
    - 新增官方配置项
    - 冲突时提示用户选择

  models.json:
    - 完全保留用户配置
    - 不覆盖

  lsp-config.json:
    - 完全保留用户配置
    - 不覆盖
```

### 备份命名

```
.opencode/config.backup/YYYYMMDD_HHMMSS/
Docs.backup/YYYYMMDD_HHMMSS/
```

---

## 五、命令设计

### /qa-update

```bash
/qa-update              # 检测并更新
/qa-update --check      # 仅检测，不更新
/qa-update --version    # 显示当前版本
/qa-update --rollback   # 回滚到上一版本
```

### 交互流程

```
用户: /qa-update

AI: 检测到新版本 v2.1.1 (当前: v2.1.0)
    
    更新内容:
    - 新增 feedback-collector-skill
    - Skills总数: 18 → 19
    
    是否更新? (y/n)

用户: y

AI: 正在更新...
    ✓ 备份配置
    ✓ 下载更新
    ✓ 合并配置
    ✓ 同步文档
    
    更新完成! 版本: v2.1.1
    
    备份位置: .opencode/config.backup/20260328_103000/
```

---

## 六、文件结构

### 新增文件

```
QuickAgents仓库:
├── VERSION.md                    # 版本信息文件
└── .opencode/
    └── skills/
        └── update-skill/         # 更新技能
            └── SKILL.md

用户项目:
├── .quickagents/
│   └── VERSION.md                # 本地版本记录
└── .opencode/
    └── config.backup/            # 配置备份目录
        └── YYYYMMDD_HHMMSS/
```

---

## 七、错误处理

| 错误 | 处理 |
|------|------|
| 网络连接失败 | 提示检查网络，稍后重试 |
| 版本文件损坏 | 重新下载VERSION.md |
| 更新中断 | 提示从备份恢复 |
| 配置合并冲突 | 保留两份，提示用户处理 |

---

## 八、实现步骤

1. 创建 VERSION.md
2. 创建 update-skill
3. 更新 AGENTS.md 添加更新说明
4. 测试更新流程

---

*版本: v1.0.0 | 创建时间: 2026-03-28*
