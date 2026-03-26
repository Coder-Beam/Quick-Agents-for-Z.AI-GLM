---
name: skill-integration-skill
description: |
  提供Skill整合能力，帮助用户将外部skill与QuickAgents进行合并。
  支持冲突检测、合并策略、配置向导、版本管理。
license: MIT
allowed-tools:
  - read
  - write
  - edit
  - bash
  - grep
  - glob
metadata:
  category: system
  priority: high
  version: 1.0.0
---

# Skill整合技能

## 概述

帮助用户将外部skill整合到QuickAgents中，提供完整的skill生命周期管理：
- 自动检测skill结构和兼容性
- 智能冲突分析和解决
- 多种合并策略
- 版本管理和回滚支持

## 何时使用

- 用户想添加新的skill
- 检测到skill冲突需要解决
- 需要更新已安装的skill
- 需要了解skill的详细信息

## Skill结构标准

### OpenCode Skill标准结构

```
skill-name/
├── SKILL.md              # 必需：技能说明文档
├── README.md             # 可选：详细文档
├── scripts/              # 可选：脚本文件
│   └── *.py / *.sh
├── templates/            # 可选：模板文件
│   └── *.md / *.json
├── references/           # 可选：参考文档
│   └── *.md
└── data/                 # 可选：数据文件
    └── *.csv / *.json
```

### SKILL.md 元数据规范

```yaml
---
name: skill-name
description: 技能描述
license: MIT
allowed-tools:
  - read
  - write
  - bash
metadata:
  category: category-name
  priority: critical | high | medium | low
  version: 1.0.0
  author: author-name
  source: github:user/repo
---
```

## 整合流程

### Step 1: 分析源Skill

检查skill的结构和内容：

```markdown
分析项目：
1. 检查SKILL.md是否存在
2. 验证元数据完整性
3. 检查脚本和模板文件
4. 评估与QuickAgents的兼容性
5. 识别潜在冲突
```

**分析输出**：
```markdown
📊 Skill分析报告

基本信息：
• 名称: {name}
• 版本: {version}
• 类别: {category}
• 来源: {source}

文件结构：
✅ SKILL.md (存在)
✅ scripts/ (存在)
⚠️ templates/ (不存在，可选)

兼容性评估：
✅ OpenCode格式兼容
✅ 无命名冲突
⚠️ 功能与xxx-skill有重叠
```

### Step 2: 冲突检测

自动检测以下冲突类型：

| 冲突类型 | 检测方法 | 严重性 |
|----------|----------|--------|
| 命名冲突 | 检查skill目录名 | 高 |
| 功能重叠 | 分析skill描述和类别 | 中 |
| 资源冲突 | 检查脚本/模板路径 | 中 |
| 配置冲突 | 检查配置文件格式 | 低 |
| 依赖冲突 | 检查外部依赖 | 中 |

**冲突报告示例**：
```markdown
⚠️ 冲突检测报告

发现 2 个潜在冲突：

1. 功能重叠 [中等]
   • ui-ux-pro-max 与 inquiry-skill
   • 重叠：用户交互式问答
   • 影响：可能同时触发

2. 脚本路径冲突 [低]
   • scripts/search.py 已存在
   • 影响：文件将被覆盖

建议合并策略：
• 策略A: 并存（推荐）- 重命名脚本
• 策略B: 合并 - 整合功能
```

### Step 3: 选择合并策略

提供四种合并策略：

#### 策略A: 并存（Coexist）

```
适用场景：
• 无冲突或轻微冲突
• 功能互补
• 用户需要两个skill

操作：
• 保留两个skill独立
• 可能需要重命名文件
• 更新registry.json
```

#### 策略B: 合并（Merge）

```
适用场景：
• 功能有重叠
• 可以整合为一个更强的skill
• 用户只需要一个

操作：
• 分析两个skill的功能
• 创建新的整合skill
• 保留原有配置选项
```

#### 策略C: 替换（Replace）

```
适用场景：
• 新skill完全替代旧skill
• 旧skill不再维护
• 用户明确要求替换

操作：
• 备份旧skill
• 删除旧skill
• 安装新skill
```

#### 策略D: 跳过（Skip）

```
适用场景：
• 冲突严重无法解决
• 新skill不兼容
• 用户决定不安装

操作：
• 清理临时文件
• 记录跳过原因
• 提供替代建议
```

### Step 4: 执行整合

```markdown
整合执行步骤：

1. 备份现有配置
   ├── 创建 .backup/skills-{timestamp}/
   └── 复制相关文件

2. 创建目标目录
   ├── core/ 或 extensions/
   └── skill-name/

3. 复制skill文件
   ├── SKILL.md
   ├── scripts/
   ├── templates/
   └── ...

4. 更新注册表
   ├── 添加到 registry.json
   ├── 记录安装信息
   └── 记录合并策略

5. 生成安装报告
   ├── 安装位置
   ├── 合并详情
   └── 使用说明
```

## 注册表管理

### registry.json 结构

```json
{
  "version": "1.0.0",
  "lastUpdated": "2026-03-25T00:00:00Z",
  "core": [
    {
      "name": "inquiry-skill",
      "version": "1.0.0",
      "category": "requirements",
      "priority": "critical",
      "source": "builtin",
      "installDate": "2026-03-22",
      "path": ".opencode/skills/core/inquiry-skill"
    }
  ],
  "extensions": [
    {
      "name": "ui-ux-pro-max",
      "version": "2.0.0",
      "category": "ui-ux",
      "priority": "recommended",
      "source": "github:nextlevelbuilder/ui-ux-pro-max-skill",
      "installDate": "2026-03-25",
      "installCommand": "npm install -g uipro-cli && uipro init --ai opencode",
      "path": ".opencode/skills/extensions/ui-ux-pro-max",
      "mergeStrategy": "coexist",
      "conflicts": []
    }
  ],
  "conflicts": [
    {
      "skill1": "ui-ux-pro-max",
      "skill2": "inquiry-skill",
      "type": "functional-overlap",
      "severity": "low",
      "resolution": "coexist"
    }
  ],
  "mergeHistory": [
    {
      "timestamp": "2026-03-25T10:00:00Z",
      "action": "install",
      "skill": "ui-ux-pro-max",
      "strategy": "coexist",
      "backup": ".backup/skills-20260325-100000/"
    }
  ]
}
```

## 版本管理

### 版本检查

```markdown
检查skill版本：
1. 读取本地registry.json
2. 获取远程版本信息
3. 比较版本号
4. 生成更新报告
```

### 更新流程

```markdown
更新skill：
1. 检查是否有更新
2. 备份当前版本
3. 下载新版本
4. 执行整合流程
5. 更新registry.json
```

### 回滚支持

```markdown
回滚到之前版本：
1. 查找备份目录
2. 恢复文件
3. 更新registry.json
4. 验证功能正常
```

## 推荐Skill库

### UI/UX类

| Skill | 来源 | 功能 | 推荐度 |
|-------|------|------|--------|
| ui-ux-pro-max | github:nextlevelbuilder/ui-ux-pro-max-skill | 67种UI样式，自动设计系统 | ⭐⭐⭐⭐⭐ |

### 开发工具类

| Skill | 来源 | 功能 | 推荐度 |
|-------|------|------|--------|
| superpowers | github:obra/superpowers | TDD开发方法论 | ⭐⭐⭐⭐ |

### 代码质量类

| Skill | 来源 | 功能 | 推荐度 |
|-------|------|------|--------|
| code-review-skill | 内置 | 代码审查方法论 | ⭐⭐⭐⭐⭐ |

## 最佳实践

1. **安装前检查**: 始终先分析skill来源和内容
2. **备份重要**: 执行任何操作前备份现有配置
3. **小步验证**: 安装后立即测试功能
4. **记录历史**: 保持registry.json的更新
5. **定期清理**: 删除不再使用的skills

## 安全考虑

1. **来源验证**: 只从可信来源安装
2. **代码审查**: 安装前检查脚本内容
3. **权限最小化**: 限制skill的文件访问
4. **沙箱隔离**: 在隔离环境中测试新skill

## 故障排除

### 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| Skill不加载 | 格式不正确 | 检查SKILL.md格式 |
| 冲突无法解决 | 策略选择不当 | 尝试不同策略 |
| 功能异常 | 版本不兼容 | 检查版本要求 |
| 找不到skill | 路径错误 | 检查registry.json |

## 资源

- Skill模板: `./templates/skill-template/`
- 示例Skill: `./references/example-skills/`
- 冲突解决指南: `./references/conflict-resolution.md`
