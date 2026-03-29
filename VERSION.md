# QuickAgents Version

> 版本信息文件 - 用于版本检测和更新

---

## 当前版本

| 属性 | 值 |
|------|-----|
| 版本号 | 2.4.0 |
| Git标签 | v2.4.0 |
| 发布日期 | 2026-03-29 |
| 最低兼容版本 | 2.0.0 |
| 仓库地址 | https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM |
| PyPI包 | https://pypi.org/project/quickagents/ |

---

## 安装方式

```bash
# 从PyPI安装
pip install quickagents

# 完整安装（包含Windows功能）
pip install quickagents[full]

# 使用CLI
qa --help
qa evolution status
qa hooks install
```

---

## 本次更新 (v2.4.0)

**重大更新 - 浏览器自动化强制安装 + Lightpanda默认**

### 架构变更

| 变更 | 之前 (v2.3.x) | 现在 (v2.4.0) |
|------|---------------|---------------|
| **Playwright** | 可选依赖 | **强制依赖** |
| **Lightpanda** | 用户自行安装 | **自动安装** |
| **默认后端** | Chromium | **Lightpanda** |
| **版本号** | 固定版本 | **latest (最新)** |

### 新增功能

#### 1. 强制安装浏览器依赖

```bash
pip install quickagents  # 自动安装 Playwright
```

首次使用时自动安装Chromium浏览器。

#### 2. 自动安装Lightpanda

```python
from quickagents import Browser

# 首次使用时自动检测和安装
browser = Browser()  # 自动确保依赖已安装
```

#### 3. 启动时更新第三方依赖

```python
from quickagents import update_browser_dependencies

# 更新Playwright和Chromium到最新版本
update_browser_dependencies()
```

#### 4. 默认使用Lightpanda

```python
from quickagents import Browser

# 默认使用Lightpanda（更快、更轻量）
browser = Browser()

# 如果Lightpanda不可用，自动回退到Chromium
# 或者明确指定回退
browser = Browser(fallback_to_chromium=True)
```

### Lightpanda优势

| 特性 | Lightpanda | Chromium |
|------|------------|----------|
| **速度** | 11x faster | 基准 |
| **内存** | 9x less | 基准 |
| **启动** | 秒级 | 秒级 |
| **专为AI** | ✅ | ❌ |

### pyproject.toml变更

```toml
# 之前
dependencies = ["psutil>=5.9.0"]
[project.optional-dependencies]
browser = ["playwright>=1.40.0"]

# 现在
dependencies = [
    "psutil",      # latest
    "playwright",  # latest - 强制依赖
]
```

### 新增模块

| 模块 | 文件 | 功能 |
|------|------|------|
| **BrowserInstaller** | `quickagents/browser/installer.py` | 自动检测和安装 |

### API变更

```python
# 新增函数
from quickagents import (
    ensure_browser_installed,     # 确保浏览器已安装
    update_browser_dependencies,  # 更新依赖
)

# 确保安装
ensure_browser_installed(auto_install=True)

# 更新到最新版本
update_browser_dependencies()
```

---

## 历史版本

### v2.3.1 (2026-03-29)
- 浏览器自动化模块（可选安装）

### v2.3.0 (2026-03-29)
- 统一自我进化系统

### v2.2.0 (2026-03-29)
- UnifiedDB统一存储架构
- SQLite主存储 + Markdown辅助备份
- Token节省60%+

### v2.1.1 (2026-03-28)
- `feedback-collector-skill` - 经验收集系统
- Skills本地化框架搭建

### v2.1.0 (2026-03-27)
- 基于OpenDev/VeRO/SWE-agent论文的6个新Skills
- 事件驱动提醒机制
- ACI设计原则

### v2.0.0 (2026-03-25)
- 三维记忆系统
- 17个专业代理
- 12个核心技能

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

*最后更新: 2026-03-29*
