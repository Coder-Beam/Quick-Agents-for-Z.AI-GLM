"""
GitHooks - Git钩子集成

功能:
- 自动安装Git钩子
- post-commit钩子: 提交后自动触发进化分析
- pre-commit钩子: 提交前检查

使用方式:
    from quickagents import GitHooks

    hooks = GitHooks()
    hooks.install()  # 安装钩子
    hooks.uninstall()  # 卸载钩子
"""

import stat
from pathlib import Path
from typing import Dict


class GitHooks:
    """
    Git钩子管理器

    使用方式:
        hooks = GitHooks()

        # 安装所有钩子
        hooks.install()

        # 仅安装post-commit
        hooks.install_post_commit()

        # 卸载
        hooks.uninstall()
    """

    def __init__(self, repo_path: str = "."):
        """
        初始化

        Args:
            repo_path: Git仓库路径
        """
        self.repo_path = Path(repo_path).resolve()
        self.git_dir = self.repo_path / ".git"
        self.hooks_dir = self.git_dir / "hooks"

        # 钩子脚本
        self.post_commit_script = """#!/bin/bash
# QuickAgents post-commit hook v2
# 自动触发进化分析 + 采集 files_changed

# 获取提交信息
COMMIT_HASH=$(git rev-parse HEAD)
COMMIT_MSG=$(git log -1 --pretty=%s)
FILES_CHANGED=$(git diff-tree --no-commit-id --name-only -r HEAD | tr '\\n' ',')

# 调用Python进化系统
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from quickagents import get_evolution
    evolution = get_evolution()
    files = [f for f in '$FILES_CHANGED'.split(',') if f]
    result = evolution.on_git_commit({
        'hash': '$COMMIT_HASH',
        'message': '$COMMIT_MSG',
        'files_changed': files
    })
    print(f'[Evolution] Triggered: {result}')
except Exception as e:
    print(f'[Evolution] Error: {e}')
" 2>/dev/null || true

exit 0
"""

    def is_git_repo(self) -> bool:
        """检查是否是Git仓库"""
        return self.git_dir.exists()

    def install(self) -> Dict[str, bool]:
        """
        安装所有钩子

        Returns:
            安装结果
        """
        if not self.is_git_repo():
            return {"error": "Not a git repository"}

        result = {"post_commit": self.install_post_commit()}

        return result

    def install_post_commit(self) -> bool:
        """
        安装post-commit钩子

        Returns:
            是否成功
        """
        if not self.is_git_repo():
            return False

        # 确保hooks目录存在
        self.hooks_dir.mkdir(parents=True, exist_ok=True)

        hook_path = self.hooks_dir / "post-commit"

        # 备份现有钩子
        if hook_path.exists():
            backup_path = hook_path.with_suffix(".backup")
            if not backup_path.exists():
                hook_path.rename(backup_path)

        # 写入新钩子
        hook_path.write_text(self.post_commit_script, encoding="utf-8")

        # 设置可执行权限
        hook_path.chmod(
            hook_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        )

        return True

    def uninstall(self) -> Dict[str, bool]:
        """
        卸载所有钩子

        Returns:
            卸载结果
        """
        result = {}

        # 卸载post-commit
        hook_path = self.hooks_dir / "post-commit"
        if hook_path.exists():
            hook_path.unlink()
            result["post_commit"] = True

            # 恢复备份
            backup_path = hook_path.with_suffix(".backup")
            if backup_path.exists():
                backup_path.rename(hook_path)
                result["post_commit_restored"] = True

        return result

    def get_status(self) -> Dict:
        """
        获取钩子状态

        Returns:
            状态信息
        """
        return {
            "is_git_repo": self.is_git_repo(),
            "hooks_dir_exists": self.hooks_dir.exists(),
            "post_commit_installed": (self.hooks_dir / "post-commit").exists(),
            "post_commit_has_backup": (self.hooks_dir / "post-commit.backup").exists(),
        }
