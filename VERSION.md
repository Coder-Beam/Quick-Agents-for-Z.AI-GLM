# QuickAgents Version

> Version information file - for version detection and updates | 版本信息文件 - 用于版本检测和更新

---

## Current Version | 当前版本

| Property | Value |
|-----------|-------|
| Version | 2.25.5 |
| Git Tag | v2.25.5 |
| Release Date | 2026-04-07 |
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
## What's New (v2.25.5) | 全架构A级验证通过

**Architecture Grade-A Verification — 991 Tests, 0 Failures**

### 1. ConnectionManager 完全统一

所有生产代码模块 100% 使用 `ConnectionManager`，零自建 `sqlite3.connect`：
- `ExperienceCompiler` — 经验编译器
- `YuGongDB` — 愚公循环持久化层
- `SQLiteGraphStorage` — 知识图谱存储

### 2. 全架构修复（v2.25.3 → v2.25.4 → v2.25.5）

| 版本 | 修复内容 |
|------|----------|
| v2.25.3 | ExperienceCompiler SQLite 重写 + 16 项 P0/P1/P2 修复 |
| v2.25.4 | 全架构 A 级修复（KG/DocPipeline/Evolution/Git钩子/YuGong） |
| v2.25.5 | 测试修复 + ConnectionManager 统一验证 |

### 3. 自我进化 5 阶段闭环

- Collect → Analyze → Compile → Act → Verify 全闭环
- Act: `modify_skill()` + `inject_context()` + `adjust_parameters()`
- Verify: `verify_evolution()` 成功率对比 + 回滚建议
- 自动编译：`on_task_complete()` → `should_compile()` → `_auto_compile_experiences()`

### 4. 跨模块互操作

- 愚公循环 → Evolution 自动触发
- AuditGuard → Evolution feedback 自动流入
- Evolution → ExperienceCompiler 编译文章查询
- Git 钩子 → Evolution + AuditGuard 双触发（Windows 兼容）

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