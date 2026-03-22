# AGENTS.md 发布清单与指引

## 一、GitHub仓库创建步骤

### 手动创建仓库（推荐）

1. **访问GitHub创建页面**：
   https://github.com/new

2. **填写仓库信息**：
   - Repository name: `AGENTS.md`
   - Description: `通用AI编码代理开发规范 - 基于最佳实践的完整开发流程与工程化标准`
   - Public/Private: 选择Public（推荐）
   - Initialize with: 不勾选任何选项（我们已有本地仓库）

3. **创建仓库后**，复制仓库URL：
   ```
   https://github.com/Coder-Beam/AGENTS.md.git
   ```

### 使用gh CLI创建（需先安装gh）

```bash
# 安装gh CLI（Windows）
winget install --id GitHub.cli

# 登录
gh auth login

# 创建仓库
gh repo create Coder-Beam/AGENTS.md --public --description "通用AI编码代理开发规范" --source=. --remote=origin --push
```

## 二、配置远程仓库与推送

```bash
# 添加远程仓库
git remote add origin https://github.com/Coder-Beam/AGENTS.md.git

# 推送代码
git push -u origin main
```

## 三、发布后配置

### 添加仓库主题标签

在GitHub仓库页面：
1. 点击 "About" 区域的齿轮图标
2. 添加以下Topics：
   - `ai-agents`
   - `coding-standards`
   - `development-workflow`
   - `best-practices`
   - `software-engineering`

### 创建GitHub Release（v8.0）

```bash
# 创建标签
git tag -a v8.0 -m "AGENTS.md v8.0 - 通用AI编码代理开发规范"

# 推送标签
git push origin v8.0

# 或使用gh CLI创建Release
gh release create v8.0 --title "v8.0 - 通用AI编码代理开发规范" --notes "包含完整开发流程、9个标准开发代理、Skills自我进化系统"
```

## 四、发布清单

- [ ] 创建GitHub仓库
- [ ] 添加远程仓库配置
- [ ] 推送代码到GitHub
- [ ] 配置仓库主题标签
- [ ] 创建v8.0 Release
- [ ] 验证仓库内容完整性

## 五、项目结构验证

发布后验证以下结构：

```
AGENTS.md/
├── AGENTS.md           # 核心规范文档
├── README.md           # 项目介绍
├── PUBLISH.md          # 本发布指引
│
├── Docs/               # 项目文档
│   ├── MEMORY.md
│   ├── TASKS.md
│   ├── DESIGN.md
│   ├── INDEX.md
│   └── DECISIONS.md
│
└── .opencode/          # OpenCode配置
    ├── agents/         # 9个标准开发代理
    ├── skills/         # Skills系统
    ├── commands/
    ├── plugins/
    └── memory/         # 文档同步目录
```

## 六、下一步优化建议

1. **添加LICENSE文件**：MIT或Apache-2.0
2. **配置GitHub Actions**：自动化文档检查
3. **添加贡献指南**：CONTRIBUTING.md
4. **创建Wiki**：详细使用说明

---

*创建时间: 2026-03-22*
*版本: v1.0.0*
