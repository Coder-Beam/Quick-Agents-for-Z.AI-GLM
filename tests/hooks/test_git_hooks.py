"""
GitHooks 测试套件

测试范围:
1. 初始化
2. Git仓库检测
3. 钩子安装
4. 钩子状态
5. 钩子卸载
6. 备份恢复
7. 与SkillEvolution集成
"""

import os
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from quickagents.core.git_hooks import GitHooks


class TestGitHooks:
    """GitHooks 测试类"""

    def setup_method(self):
        """每个测试方法前的设置"""
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp(prefix="qa_hooks_test_")
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """每个测试方法后的清理"""
        # 清理临时目录
        if self.temp_path.exists():
            shutil.rmtree(self.temp_path, ignore_errors=True)

    def test_init_default_path(self):
        """测试1: 默认路径初始化"""
        hooks = GitHooks()

        # 验证默认路径是当前目录
        assert hooks.repo_path == Path(".").resolve()
        assert str(hooks.hooks_dir).endswith(".git/hooks") or ".git" in str(hooks.hooks_dir)

        print("✅ 测试1通过: 默认路径初始化")

    def test_init_custom_path(self):
        """测试2: 自定义路径初始化"""
        hooks = GitHooks(str(self.temp_path))

        # 验证自定义路径
        assert hooks.repo_path == self.temp_path
        assert hooks.git_dir == self.temp_path / ".git"
        assert hooks.hooks_dir == self.temp_path / ".git" / "hooks"

        print("✅ 测试2通过: 自定义路径初始化")

    def test_is_git_repo_false(self):
        """测试3: 非Git仓库检测"""
        hooks = GitHooks(str(self.temp_path))

        # 临时目录不是Git仓库
        assert hooks.is_git_repo() is False

        print("✅ 测试3通过: 非Git仓库检测")

    def test_is_git_repo_true(self):
        """测试4: Git仓库检测"""
        # 初始化Git仓库
        subprocess.run(["git", "init"], cwd=self.temp_dir, capture_output=True)

        hooks = GitHooks(str(self.temp_path))

        # 现在应该是Git仓库
        assert hooks.is_git_repo() is True

        print("✅ 测试4通过: Git仓库检测")

    def test_install_not_git_repo(self):
        """测试5: 非Git仓库安装失败"""
        hooks = GitHooks(str(self.temp_path))

        # 非Git仓库应该返回错误
        result = hooks.install()

        assert "error" in result
        assert result["error"] == "Not a git repository"

        print("✅ 测试5通过: 非Git仓库安装失败")

    def test_install_post_commit_success(self):
        """测试6: post-commit钩子安装成功"""
        # 初始化Git仓库
        subprocess.run(["git", "init"], cwd=self.temp_dir, capture_output=True)

        hooks = GitHooks(str(self.temp_path))

        # 安装钩子
        result = hooks.install_post_commit()

        assert result is True

        # 验证三个钩子文件都存在
        for name in ("post-commit", "post-commit.cmd", "post-commit.py"):
            assert (hooks.hooks_dir / name).exists(), f"{name} not found"

        # 验证bash钩子内容
        bash_content = (hooks.hooks_dir / "post-commit").read_text(encoding="utf-8")
        assert "#!/bin/bash" in bash_content
        assert "QA_COMMIT_HASH" in bash_content

        # 验证Python钩子内容
        py_content = (hooks.hooks_dir / "post-commit.py").read_text(encoding="utf-8")
        assert "SkillEvolution" in py_content
        assert "AuditGuard" in py_content
        assert "on_git_commit" in py_content

        # 验证Windows钩子内容
        cmd_content = (hooks.hooks_dir / "post-commit.cmd").read_text(encoding="utf-8")
        assert "@echo off" in cmd_content

        # 验证可执行权限（Unix系统）
        if os.name != "nt":
            import stat

            mode = (hooks.hooks_dir / "post-commit").stat().st_mode
            assert mode & stat.S_IXUSR

        # 验证日志目录已创建
        assert hooks.log_dir.exists()

        print("✅ 测试6通过: post-commit钩子安装成功")

    def test_install_all_hooks(self):
        """测试7: 安装所有钩子"""
        # 初始化Git仓库
        subprocess.run(["git", "init"], cwd=self.temp_dir, capture_output=True)

        hooks = GitHooks(str(self.temp_path))

        # 安装所有钩子
        result = hooks.install()

        assert "post_commit" in result
        assert result["post_commit"] is True

        print("✅ 测试7通过: 安装所有钩子")

    def test_get_status(self):
        """测试8: 获取钩子状态"""
        # 初始化Git仓库
        subprocess.run(["git", "init"], cwd=self.temp_dir, capture_output=True)

        hooks = GitHooks(str(self.temp_path))

        # 安装前状态
        status = hooks.get_status()

        assert status["is_git_repo"] is True
        assert status["post_commit_installed"] is False
        assert status["post_commit_cmd_installed"] is False
        assert status["post_commit_py_installed"] is False
        assert status["post_commit_has_backup"] is False

        # 安装钩子
        hooks.install_post_commit()

        # 安装后状态
        status = hooks.get_status()

        assert status["is_git_repo"] is True
        assert status["hooks_dir_exists"] is True
        assert status["post_commit_installed"] is True
        assert status["post_commit_cmd_installed"] is True
        assert status["post_commit_py_installed"] is True

        print("✅ 测试8通过: 获取钩子状态")

    def test_uninstall(self):
        """测试9: 卸载钩子"""
        # 初始化Git仓库
        subprocess.run(["git", "init"], cwd=self.temp_dir, capture_output=True)

        hooks = GitHooks(str(self.temp_path))

        # 安装钩子
        hooks.install_post_commit()

        # 卸载钩子
        result = hooks.uninstall()

        assert "post_commit" in result
        assert result["post_commit"] is True

        # 验证所有钩子文件已删除
        for name in ("post-commit", "post-commit.cmd", "post-commit.py"):
            assert not (hooks.hooks_dir / name).exists(), f"{name} still exists"

        print("✅ 测试9通过: 卸载钩子")

    def test_backup_existing_hook(self):
        """测试10: 备份现有钩子"""
        # 初始化Git仓库
        subprocess.run(["git", "init"], cwd=self.temp_dir, capture_output=True)

        hooks = GitHooks(str(self.temp_path))

        # 创建现有钩子
        hook_path = hooks.hooks_dir / "post-commit"
        hook_path.parent.mkdir(parents=True, exist_ok=True)
        hook_path.write_text('#!/bin/bash\n# Existing hook\necho "old"', encoding="utf-8")

        # 安装新钩子
        hooks.install_post_commit()

        # 验证备份文件存在
        backup_path = hooks.hooks_dir / "post-commit.backup"
        assert backup_path.exists()

        # 验证备份内容
        backup_content = backup_path.read_text(encoding="utf-8")
        assert "Existing hook" in backup_content

        print("✅ 测试10通过: 备份现有钩子")

    def test_restore_backup_on_uninstall(self):
        """测试11: 卸载时恢复备份"""
        # 初始化Git仓库
        subprocess.run(["git", "init"], cwd=self.temp_dir, capture_output=True)

        hooks = GitHooks(str(self.temp_path))

        # 创建现有钩子
        hook_path = hooks.hooks_dir / "post-commit"
        hook_path.parent.mkdir(parents=True, exist_ok=True)
        hook_path.write_text('#!/bin/bash\n# Existing hook\necho "old"', encoding="utf-8")

        # 安装新钩子（会备份）
        hooks.install_post_commit()

        # 卸载钩子（应该恢复备份）
        result = hooks.uninstall()

        assert "post_commit_restored" in result
        assert result["post_commit_restored"] is True

        # 验证旧钩子已恢复
        restored_content = hook_path.read_text(encoding="utf-8")
        assert "Existing hook" in restored_content

        print("✅ 测试11通过: 卸载时恢复备份")

    def test_hook_script_content(self):
        """测试12: 钩子脚本内容验证"""
        hooks = GitHooks(str(self.temp_path))

        bash_script = hooks._generate_bash_hook()
        py_script = hooks._generate_python_hook()
        cmd_script = hooks._generate_windows_hook()

        assert "#!/bin/bash" in bash_script
        assert "QA_COMMIT_HASH" in bash_script
        assert "post-commit.py" in bash_script
        assert "exit 0" in bash_script

        assert "SkillEvolution" in py_script
        assert "AuditGuard" in py_script
        assert "on_git_commit" in py_script
        assert "QA_COMMIT_HASH" in py_script

        assert "@echo off" in cmd_script
        assert "post-commit.py" in cmd_script

        print("✅ 测试12通过: 钩子脚本内容验证")

    def test_hooks_directory_creation(self):
        """测试13: 确保hooks目录和日志目录存在"""
        # 初始化Git仓库
        subprocess.run(["git", "init"], cwd=self.temp_dir, capture_output=True)

        hooks = GitHooks(str(self.temp_path))

        # Git init 会自动创建 hooks 目录
        assert hooks.hooks_dir.exists()

        # 安装钩子
        hooks.install_post_commit()

        # 验证目录仍然存在
        assert hooks.hooks_dir.exists()
        assert hooks.log_dir.exists()

        # 验证钩子文件已创建
        for name in ("post-commit", "post-commit.cmd", "post-commit.py"):
            assert (hooks.hooks_dir / name).exists(), f"{name} not found"

        print("✅ 测试13通过: 自动创建hooks和日志目录")

    def test_real_repo_integration(self):
        """测试14: 真实仓库集成测试"""
        # 使用当前项目目录（这是一个真实的Git仓库）
        current_repo = Path(__file__).parent.parent.parent
        hooks = GitHooks(str(current_repo))

        # 验证是Git仓库
        assert hooks.is_git_repo() is True

        # 获取状态
        status = hooks.get_status()

        assert status["is_git_repo"] is True
        assert status["hooks_dir_exists"] is True

        print("✅ 测试14通过: 真实仓库集成测试")


def run_all_tests():
    """运行所有测试"""
    test_instance = TestGitHooks()

    tests = [
        ("test_init_default_path", "默认路径初始化"),
        ("test_init_custom_path", "自定义路径初始化"),
        ("test_is_git_repo_false", "非Git仓库检测"),
        ("test_is_git_repo_true", "Git仓库检测"),
        ("test_install_not_git_repo", "非Git仓库安装失败"),
        ("test_install_post_commit_success", "post-commit钩子安装成功"),
        ("test_install_all_hooks", "安装所有钩子"),
        ("test_get_status", "获取钩子状态"),
        ("test_uninstall", "卸载钩子"),
        ("test_backup_existing_hook", "备份现有钩子"),
        ("test_restore_backup_on_uninstall", "卸载时恢复备份"),
        ("test_hook_script_content", "钩子脚本内容验证"),
        ("test_hooks_directory_creation", "自动创建hooks目录"),
        ("test_real_repo_integration", "真实仓库集成测试"),
    ]

    passed = 0
    failed = 0

    print("\n" + "=" * 60)
    print("GitHooks 测试套件")
    print("=" * 60 + "\n")

    for test_name, test_desc in tests:
        try:
            # 设置
            test_instance.setup_method()

            # 执行测试
            test_method = getattr(test_instance, test_name)
            test_method()

            passed += 1
            print(f"  ✅ {test_desc}")

        except AssertionError as e:
            failed += 1
            import traceback

            print(f"  ❌ {test_desc}")
            print(f"     AssertionError: {str(e) or 'No message'}")
            traceback.print_exc()

        except Exception as e:
            failed += 1
            import traceback

            print(f"  ❌ {test_desc}")
            print(f"     {type(e).__name__}: {str(e)}")
            traceback.print_exc()

        finally:
            # 清理
            test_instance.teardown_method()

    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{len(tests)} 通过")
    print("=" * 60 + "\n")

    return passed, failed, len(tests)


if __name__ == "__main__":
    passed, failed, total = run_all_tests()

    # 返回退出码
    sys.exit(0 if failed == 0 else 1)
