# 这是 QuickAgents 源码仓库

## ⚠️ 如果你克隆了此仓库

如果你想在**自己的项目**中使用 QuickAgents，**不要直接使用克隆的文件**。

### 正确的安装方式

在你的项目目录中运行：

**macOS / Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/scripts/install.sh | bash
```

**Windows PowerShell:**
```powershell
iwr -useb https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/scripts/install.ps1 | iex
```

或使用 pip 安装：
```bash
pip install quickagents
qka init
```

### 为什么看不到 AGENTS.md 和 opencode.json？

这些文件是**运行时生成**的模板文件，已从 Git 追踪中移除以保持仓库纯净。

安装 QuickAgents 后，运行 `qka init` 会自动生成这些文件到你的项目根目录。

---

## 如果你是开发者

如果你想为 QuickAgents 贡献代码或查看源码：

1. 模板文件位于: `quickagents/templates/`
2. 安装开发环境: `pip install -e .`
3. 测试安装: `python -m quickagents.cli.main init --dry-run`

## 相关链接

- [完整文档](./README.md)
- [PyPI 包](https://pypi.org/project/quickagents/)
- [问题反馈](https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/issues)
