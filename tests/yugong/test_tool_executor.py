"""
ToolExecutor 测试 - 真实工具执行

测试策略: 使用 tmp_path 进行真实文件操作
"""

import pytest
import os
from pathlib import Path

from quickagents.yugong.tool_executor import (
    ToolExecutor,
    ToolResult,
    ToolDefinition,
)


@pytest.fixture
def executor(tmp_path):
    """工具执行器（限制在 tmp_path 工作目录内）"""
    return ToolExecutor(working_dir=str(tmp_path))


@pytest.fixture
def executor_with_files(executor, tmp_path):
    """带预置文件的执行器"""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')", encoding="utf-8")
    (tmp_path / "src" / "utils.py").write_text("def add(a, b): return a + b", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    return executor


# ================================================================
# Test 1: 工具定义
# ================================================================


class TestToolDefinitions:
    def test_builtin_tools_registered(self, executor):
        """内置工具应该被注册"""
        tools = executor.get_tool_definitions()
        tool_names = {t["function"]["name"] for t in tools}
        expected = {
            "read_file",
            "write_file",
            "edit_file",
            "run_command",
            "list_directory",
            "search_content",
            "find_files",
        }
        assert expected.issubset(tool_names)

    def test_tool_has_required_fields(self, executor):
        """工具定义包含必要字段"""
        tools = executor.get_tool_definitions()
        for tool in tools:
            func = tool["function"]
            assert "name" in func
            assert "parameters" in func


# ================================================================
# Test 2: read_file
# ================================================================


class TestReadFile:
    def test_read_existing(self, executor_with_files, tmp_path):
        """读取已存在的文件"""
        result = executor_with_files.execute("read_file", {"file_path": "src/main.py"})
        assert result.success
        assert "print('hello')" in result.output

    def test_read_with_absolute_path(self, executor_with_files, tmp_path):
        """使用绝对路径读取"""
        abs_path = str(tmp_path / "src" / "main.py")
        result = executor_with_files.execute("read_file", {"file_path": abs_path})
        assert result.success
        assert "print('hello')" in result.output

    def test_read_nonexistent(self, executor):
        """读取不存在的文件"""
        result = executor.execute("read_file", {"file_path": "nonexistent.py"})
        assert not result.success
        assert "not found" in result.error.lower() or "error" in result.error.lower()

    def test_read_with_offset(self, executor_with_files, tmp_path):
        """带偏移读取文件"""
        # 创建多行文件
        (tmp_path / "multiline.py").write_text("line1\nline2\nline3\nline4\n", encoding="utf-8")
        result = executor_with_files.execute(
            "read_file",
            {
                "file_path": "multiline.py",
                "offset": 2,
                "limit": 2,
            },
        )
        assert result.success
        assert "line2" in result.output
        assert "line3" in result.output


# ================================================================
# Test 3: write_file
# ================================================================


class TestWriteFile:
    def test_write_new_file(self, executor, tmp_path):
        """写入新文件"""
        result = executor.execute(
            "write_file",
            {
                "file_path": "new_module.py",
                "content": "def hello():\n    return 'world'\n",
            },
        )
        assert result.success
        assert (tmp_path / "new_module.py").exists()
        assert "def hello" in (tmp_path / "new_module.py").read_text(encoding="utf-8")

    def test_write_creates_dirs(self, executor, tmp_path):
        """写入时自动创建目录"""
        result = executor.execute(
            "write_file",
            {
                "file_path": "deep/nested/dir/file.py",
                "content": "pass",
            },
        )
        assert result.success
        assert (tmp_path / "deep" / "nested" / "dir" / "file.py").exists()

    def test_write_overwrites(self, executor, tmp_path):
        """覆盖已存在的文件"""
        (tmp_path / "overwrite.py").write_text("old content", encoding="utf-8")
        executor.execute(
            "write_file",
            {
                "file_path": "overwrite.py",
                "content": "new content",
            },
        )
        assert "new content" in (tmp_path / "overwrite.py").read_text(encoding="utf-8")

    def test_tracks_files_changed(self, executor, tmp_path):
        """追踪文件变更"""
        executor.execute("write_file", {"file_path": "a.py", "content": "a"})
        executor.execute("write_file", {"file_path": "b.py", "content": "b"})
        changed = executor.files_changed
        assert "a.py" in changed
        assert "b.py" in changed


# ================================================================
# Test 4: edit_file
# ================================================================


class TestEditFile:
    def test_replace_text(self, executor_with_files, tmp_path):
        """替换文件中的文本"""
        result = executor_with_files.execute(
            "edit_file",
            {
                "file_path": "src/main.py",
                "old_string": "print('hello')",
                "new_string": "print('world')",
            },
        )
        assert result.success
        assert "print('world')" in (tmp_path / "src" / "main.py").read_text(encoding="utf-8")
        assert "print('hello')" not in (tmp_path / "src" / "main.py").read_text(encoding="utf-8")

    def test_old_string_not_found(self, executor_with_files):
        """old_string 不存在时报错"""
        result = executor_with_files.execute(
            "edit_file",
            {
                "file_path": "src/main.py",
                "old_string": "nonexistent_text_xyz",
                "new_string": "replacement",
            },
        )
        assert not result.success
        assert "not found" in result.error.lower() or "error" in result.error.lower()


# ================================================================
# Test 5: run_command
# ================================================================


class TestRunCommand:
    def test_simple_command(self, executor):
        """执行简单命令"""
        result = executor.execute("run_command", {"command": "echo hello"})
        assert result.success
        assert "hello" in result.output

    def test_command_failure(self, executor):
        """执行失败命令"""
        result = executor.execute("run_command", {"command": 'python -c "import nonexistent_module_xyz"'})
        assert not result.success

    def test_python_version(self, executor):
        """运行 python --version"""
        result = executor.execute("run_command", {"command": "python --version"})
        assert result.success
        assert "Python" in result.output

    def test_forbidden_command(self, executor):
        """禁止危险命令"""
        result = executor.execute("run_command", {"command": "rm -rf /"})
        assert not result.success


# ================================================================
# Test 6: list_directory
# ================================================================


class TestListDirectory:
    def test_list_root(self, executor_with_files):
        """列出根目录"""
        result = executor_with_files.execute("list_directory", {"path": "."})
        assert result.success
        assert "src" in result.output
        assert "tests" in result.output

    def test_list_subdirectory(self, executor_with_files):
        """列出子目录"""
        result = executor_with_files.execute("list_directory", {"path": "src"})
        assert result.success
        assert "main.py" in result.output
        assert "utils.py" in result.output

    def test_list_nonexistent(self, executor):
        """列出不存在的目录"""
        result = executor.execute("list_directory", {"path": "nonexistent"})
        assert not result.success


# ================================================================
# Test 7: search_content
# ================================================================


class TestSearchContent:
    def test_search_pattern(self, executor_with_files):
        """搜索内容模式"""
        result = executor_with_files.execute(
            "search_content",
            {
                "pattern": "print",
                "path": "src",
            },
        )
        assert result.success
        assert "main.py" in result.output

    def test_search_no_match(self, executor_with_files):
        """搜索无匹配"""
        result = executor_with_files.execute(
            "search_content",
            {
                "pattern": "nonexistent_pattern_xyz",
                "path": "src",
            },
        )
        assert result.success  # 搜索成功但无结果
        assert result.output.strip() == "" or "no match" in result.output.lower() or result.output == ""


# ================================================================
# Test 8: find_files
# ================================================================


class TestFindFiles:
    def test_find_by_pattern(self, executor_with_files):
        """按模式查找文件"""
        result = executor_with_files.execute(
            "find_files",
            {
                "pattern": "*.py",
                "path": "src",
            },
        )
        assert result.success
        assert "main.py" in result.output
        assert "utils.py" in result.output

    def test_find_no_match(self, executor_with_files):
        """查找无匹配"""
        result = executor_with_files.execute(
            "find_files",
            {
                "pattern": "*.xyz",
                "path": ".",
            },
        )
        assert result.success
        assert result.output.strip() == "" or result.output == ""


# ================================================================
# Test 9: 安全约束
# ================================================================


class TestSafety:
    def test_prevent_path_traversal(self, executor, tmp_path):
        """防止路径遍历攻击"""
        result = executor.execute("read_file", {"file_path": "../../etc/passwd"})
        assert not result.success or "error" in result.output.lower() or result.error

    def test_working_dir_isolation(self, executor, tmp_path):
        """工作目录隔离"""
        # 写入的文件应该在工作目录内
        executor.execute("write_file", {"file_path": "test.py", "content": "ok"})
        assert (tmp_path / "test.py").exists()

    def test_forbidden_commands(self, executor):
        """禁止的危险命令列表"""
        forbidden = [
            "rm -rf /",
            "del /s /q C:\\",
            "format c:",
            "shutdown -h now",
        ]
        for cmd in forbidden:
            result = executor.execute("run_command", {"command": cmd})
            assert not result.success, f"Should block: {cmd}"

    def test_reset_files_changed(self, executor):
        """重置文件变更追踪"""
        executor.execute("write_file", {"file_path": "a.py", "content": "a"})
        assert len(executor.files_changed) > 0
        executor.reset_files_changed()
        assert len(executor.files_changed) == 0
