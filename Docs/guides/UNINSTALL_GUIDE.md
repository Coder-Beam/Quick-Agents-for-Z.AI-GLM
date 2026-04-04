# QuickAgents 卸载指导

> 适用于: QuickAgents v2.7.6+ 及所有老版本

---

## 一、标准卸载（v2.7.6+）

如果你安装的是 **v2.7.6 或更高版本**，使用内置的 `qka uninstall` 命令：

### 1.1 预览卸载内容

```bash
# 查看将要删除的文件和目录（不实际执行）
qka uninstall --dry-run
```

### 1.2 交互式卸载

```bash
# 逐步确认后卸载
qka uninstall
```

### 1.3 跳过确认直接卸载

```bash
# 跳过确认提示（适用于脚本/CI环境）
qka uninstall --force
```

### 1.4 保留数据卸载

```bash
# 仅卸载pip包，保留项目数据 (.quickagents/)
qka uninstall --keep-data

# 仅卸载pip包，保留全局配置 (~/.quickagents/)
qka uninstall --keep-config

# 同时保留项目和全局数据
qka uninstall --keep-data --keep-config
```

### 1.5 清理范围说明

| 清理项 | 路径 | 说明 |
|--------|------|------|
| Git Hooks | `.git/hooks/` (qa相关) | QuickAgents 安装的 post-commit 钩子 |
| 项目数据 | `.quickagents/` | SQLite数据库、缓存、日志、反馈 |
| 全局数据 | `~/.quickagents/` | 全局进化数据、经验备份 |
| pip包 | `site-packages/quickagents/` | Python包本体 |

---

## 二、老版本手动卸载（v2.7.5 及更早版本）

如果你安装的是 **v2.7.5 或更早版本**，没有 `qka uninstall` 命令，请按以下步骤手动卸载。

### 2.1 卸载步骤总览

```
步骤1: 卸载 pip 包
    ↓
步骤2: 清理 Git Hooks
    ↓
步骤3: 清理项目数据
    ↓
步骤4: 清理全局数据
    ↓
步骤5: 验证卸载完成
```

### 2.2 步骤1：卸载 pip 包

```bash
# 标准卸载
pip uninstall quickagents -y

# 如果安装了完整版（带 Windows 功能）
pip uninstall quickagents pywin32 wmi -y
```

验证：

```bash
# 以下命令应该报错 "command not found" 或 "No module named"
qka --help                    # 应该不存在
python -c "import quickagents"  # 应该报 ImportError
```

### 2.3 步骤2：清理 Git Hooks

QuickAgents 可能在 Git 仓库中安装了 post-commit 钩子。

**检查是否存在：**

```bash
# Linux / macOS
cat .git/hooks/post-commit 2>/dev/null | grep -i quickagents

# Windows (PowerShell)
if (Test-Path .git\hooks\post-commit) {
    $content = Get-Content .git\hooks\post-commit -Raw
    if ($content -match "quickagents|qka ") {
        Write-Host "Found QuickAgents hook"
    }
}
```

**删除方法：**

```bash
# 如果上面检测到 QuickAgents 钩子

# Linux / macOS
rm .git/hooks/post-commit

# Windows (PowerShell)
Remove-Item .git\hooks\post-commit -Force

# 如果 post-commit 文件里还有其他逻辑（非QuickAgents），只删除相关行
# 用文本编辑器打开 .git/hooks/post-commit，删除包含 quickagents 或 qka 的行
```

### 2.4 步骤3：清理项目数据

**每个使用过 QuickAgents 的项目** 都会生成 `.quickagents/` 目录。

**查找所有项目数据：**

```bash
# Linux / macOS — 查找所有包含 .quickagents 的项目
find ~ -type d -name ".quickagents" 2>/dev/null

# Windows (PowerShell) — 查找当前盘符
Get-ChildItem -Path C:\ -Directory -Recurse -Filter ".quickagents" -ErrorAction SilentlyContinue | Select-Object FullName
```

**删除项目数据：**

```bash
# 进入项目目录后删除

# Linux / macOS
rm -rf .quickagents/

# Windows (PowerShell)
Remove-Item -Recurse -Force .quickagents\
# 或
rmdir /s /q .quickagents
```

**项目数据目录内容说明：**

| 文件/目录 | 说明 | 是否可安全删除 |
|-----------|------|---------------|
| `unified.db` | SQLite主数据库 | ✅ |
| `cache.db` | 文件缓存数据库 | ✅ |
| `sync_state.json` | 同步状态 | ✅ |
| `boulder.json` | 进度追踪 | ✅ |
| `backups/` | 数据库备份 | ✅ |
| `feedback/` | 经验收集Markdown | ✅ |
| `logs/` | 运行日志 | ✅ |
| `notepads/` | 笔记本 | ✅ |
| `plans/` | 计划文件 | ✅ |

> ⚠️ **注意**: 删除前请确认 `.quickagents/` 中的数据不再需要。如果需要保留记忆或反馈数据，请先备份。

### 2.5 步骤4：清理全局数据

QuickAgents 还会在用户主目录创建全局数据。

**删除全局数据：**

```bash
# Linux / macOS
rm -rf ~/.quickagents/

# Windows (PowerShell)
Remove-Item -Recurse -Force "$env:USERPROFILE\.quickagents"
# 或
rmdir /s /q %USERPROFILE%\.quickagents
```

**全局数据目录内容说明：**

| 文件/目录 | 说明 |
|-----------|------|
| `~/.quickagents/feedback/` | 全局经验备份 |
| `~/.quickagents/evolution/` | Skills进化数据 |

### 2.6 步骤5：验证卸载完成

运行以下命令确认完全卸载：

```bash
# 1. pip包已卸载
pip show quickagents
# 预期输出: WARNING: Package(s) not found: quickagents

# 2. CLI命令已不存在
qka --help
# 预期: 'qa' is not recognized / command not found

# 3. Python模块已不存在
python -c "import quickagents"
# 预期: ModuleNotFoundError: No module named 'quickagents'

# 4. 项目数据已清理
ls .quickagents/ 2>/dev/null || echo "OK: no .quickagents directory"

# 5. 全局数据已清理
ls ~/.quickagents/ 2>/dev/null || echo "OK: no ~/.quickagents directory"
```

---

## 三、特殊情况处理

### 3.1 开发模式安装（pip install -e .）

如果你是从源码开发模式安装的：

```bash
# 1. 卸载开发包
pip uninstall quickagents -y

# 2. 删除源码目录（如果不再需要）
# rm -rf /path/to/QuickAgents
```

### 3.2 使用虚拟环境

如果在虚拟环境中安装：

```bash
# 方法1: 激活虚拟环境后卸载
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

pip uninstall quickagents -y

# 方法2: 直接删除整个虚拟环境
rm -rf venv/
```

### 3.3 多版本 Python

如果系统有多个 Python 版本：

```bash
# 检查所有 Python 版本中的安装情况
python3 -m pip show quickagents
python -m pip show quickagents
py -3.9 -m pip show quickagents
py -3.10 -m pip show quickagents
py -3.11 -m pip show quickagents
py -3.12 -m pip show quickagents

# 逐个卸载
python3 -m pip uninstall quickagents -y
python -m pip uninstall quickagents -y
# ...其他版本同理
```

### 3.4 Windows 权限问题

Windows 上删除 `.quickagents/` 可能遇到文件被占用：

```powershell
# 方法1: 使用 PowerShell 强制删除
Remove-Item -Recurse -Force .quickagents\

# 方法2: 先关闭所有 Python 进程，再删除
taskkill /f /im python.exe 2>$null
rmdir /s /q .quickagents

# 方法3: 重启后删除（如果 WAL 文件被锁定）
# 重启电脑后执行:
rmdir /s /q .quickagents
```

### 3.5 macOS/Linux 权限问题

```bash
# 如果提示 Permission denied
sudo rm -rf ~/.quickagents/
sudo rm -rf /path/to/project/.quickagents/
```

---

## 四、卸载后重新安装

如需重新安装：

```bash
# 标准安装
pip install quickagents

# 完整安装（包含 Windows 功能）
pip install quickagents[full]

# 安装特定版本
pip install quickagents==2.7.6

# 从 GitHub 安装最新版
pip install git+https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM.git@main
```

---

## 五、卸载常见问题 (FAQ)

### Q1: 卸载后 `.quickagents/` 目录还在？

如果 `rm -rf` 或 `rmdir /s /q` 报错，通常是因为 SQLite WAL 文件被其他进程锁定：

```bash
# 1. 关闭所有 Python 进程
# 2. 等待几秒
# 3. 再次尝试删除
```

### Q2: 卸载后 `qa` 命令仍然存在？

可能存在多个 Python 环境或 PATH 缓存：

```bash
# 查找 qka 命令位置
which qka        # Linux/macOS
where qka        # Windows

# 删除残留的 CLI 入口
# Linux/macOS
rm /usr/local/bin/qa
# 或
rm ~/.local/bin/qa

# Windows
del %USERPROFILE%\AppData\Local\Programs\Python\Python3XX\Scripts\qa.exe
```

### Q3: 我想保留数据只升级版本？

```bash
# 不需要卸载，直接升级即可
pip install --upgrade quickagents

# 或使用内置命令
qka update
```

### Q4: 老版本没有 `qka update` 怎么升级？

```bash
# 直接 pip 升级，不需要先卸载
pip install --upgrade quickagents

# 升级后验证
python -c "from quickagents import __version__; print(__version__)"
```

---

*文档版本: v1.0.0 | 更新时间: 2026-04-01*
