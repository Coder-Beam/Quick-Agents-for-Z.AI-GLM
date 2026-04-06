# QuickAgents Version

> Version information file - for version detection and updates | 版本信息文件 - 用于版本检测和更新

---

## Current Version | 当前版本

| Property | Value |
|-----------|-------|
| Version | 2.11.0 |
| Git Tag | v2.11.0 |
| Release Date | 2026-04-06 |
| Minimum Compatible | 2.0.0 |
| Repository | https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM |
| PyPI Package | https://pypi.org/project/quickagents/ |
| Author | Coder-Beam |

---

## Installation | 安装

```bash
# Install from PyPI | 从PyPI安装
pip install quickagents

# Full installation (with Windows features)
pip install quickagents[full]

# Verify installation
python -c "from quickagents import __version__; print(f'QuickAgents v{__version__}')

# CLI commands
qka --help
qka stats
qka hooks install
```
---
## What's New (v2.11.0) | 一句话安装 + qka init

**One-Line Installation + qka init Command**

### 1. One-Line Installation Scripts

**macOS/Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/scripts/install.sh | bash
```

**Windows PowerShell:**
```powershell
iwr -useb https://raw.githubusercontent.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM/main/scripts/install.ps1 | iex
```

### 2. qka init Command

New command for project initialization:
```bash
qka init                    # Interactive initialization
qka init --force            # Overwrite existing files
qka init --dry-run          # Preview without changes
qka init --with-ui-ux       # Include ui-ux-pro-max skill
qka init --minimal          # Minimal installation
```

### 3. Templates Package

- All configuration files now packaged in pip wheel
- 15 Agents + 7 default Skills + 5 Commands + Hooks
- Automatic backup before updates
- Deprecated file cleanup

### 4. Upgrade Strategy

- `qka update` now backs up old configs
- Detects and prompts to remove deprecated files
- Smart merge for user-modified configs

---

## What's New (v2.10.0) | 产品化改造

**Productization — Phase 1+2 cleanup + new real local modules**

### 1. YuGong Loop (愚公循环)

**删除18个概念存根Skills, 清理Skills注册表和文档**

- 新建 9个真实本地模块替代已删除的概念存根
ProjectDetector, Category_router, Model_router
 ReportGenerator CLI报告
10个真实Agent执行器 (agent接入真实LLM)
- `qka yugong report/resume` 从DB恢复状态继续执行

修复3个静默异常（`except Exception: pass`)
- AGENTS.md: EdgeType.TRACES_TO 不存在的引用
  → 改用 EdgeType.MAPS_TO

Version History

...