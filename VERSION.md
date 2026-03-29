# QuickAgents Version

> 版本信息文件 - 用于版本检测和更新

---

## 当前版本

| 属性 | 值 |
|------|-----|
| 版本号 | 2.3.1 |
| Git标签 | v2.3.1 |
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

## 本次更新 (v2.3.1)

**重大更新 - 浏览器自动化与DevTools集成**

### 新增功能

#### Browser - 浏览器自动化模块

支持Chromium和Lightpanda两种后端：

| 后端 | 说明 | 安装 |
|------|------|------|
| chromium | 默认，Playwright + Chromium | `pip install quickagents[browser]` |
| lightpanda | 轻量级headless浏览器 | 用户自行安装 |

**功能**:
- 获取控制台日志 (Console) - 捕获所有console.log/warn/error
- 获取网络请求 (Network) - 分析HTTP请求和响应
- 获取性能指标 (Performance) - 页面性能分析
- 执行JavaScript - 在页面上下文中执行脚本
- 截图 - 页面截图
- Cookie管理 - 读写Cookie

#### Lightpanda 集成

Lightpanda是一个用Zig编写的轻量级headless浏览器：
- 比Chrome快11倍
- 内存少9倍
- CDP协议兼容
- 专为AI Agent设计

**使用方式**:
```python
from quickagents import Browser

# 默认Chromium
browser = Browser()

# 使用Lightpanda（需先启动lightpanda serve）
browser = Browser(backend='lightpanda')

# 打开页面
page = browser.open('https://example.com')

# 获取控制台日志
console_logs = page.get_console_logs()

# 获取网络请求
network = page.get_network_requests()

# 关闭
browser.close()
```

#### 新增CLI命令

```bash
# 浏览器相关（需要pip install quickagents[browser]）
qa browser open <url>     # 打开URL
qa browser screenshot <url> <file>  # 截图
qa browser console <url>  # 获取控制台日志
qa browser network <url>  # 获取网络请求
```

### 安装方式

```bash
# 基础安装
pip install quickagents

# 完整安装（包含浏览器自动化）
pip install quickagents[browser]

# 完整安装后还需要安装浏览器
playwright install chromium
```

### 依赖更新

pyproject.toml新增可选依赖：
```toml
[project.optional-dependencies]
browser = [
    "playwright>=1.40.0",
]
```

---

## 历史版本

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
