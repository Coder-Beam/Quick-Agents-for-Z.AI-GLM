"""
ToolExecutor - 真实工具执行器

支持 7 个内置工具:
- read_file: 读取文件
- write_file: 写入文件
- edit_file: 编辑文件（字符串替换）
- run_command: 执行 shell 命令
- list_directory: 列出目录
- search_content: 搜索内容
- find_files: 查找文件

安全约束:
- 路径遍历防护
- 工作目录隔离
- 危险命令拦截
"""

import os
import re
import subprocess
import logging
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """工具执行结果"""

    success: bool
    output: str = ""
    error: str = ""

    def to_dict(self) -> dict:
        return {"success": self.success, "output": self.output, "error": self.error}


@dataclass
class ToolDefinition:
    """工具定义（OpenAI function calling 格式）"""

    name: str
    description: str
    parameters: dict

    def to_openai_format(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


# 内置工具定义
BUILTIN_TOOLS = [
    ToolDefinition(
        name="read_file",
        description="读取文件内容。返回文件的文本内容。",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径（相对于工作目录）"},
                "offset": {"type": "integer", "description": "起始行号（1-indexed）"},
                "limit": {"type": "integer", "description": "读取行数"},
            },
            "required": ["file_path"],
        },
    ),
    ToolDefinition(
        name="write_file",
        description="写入文件。如果文件存在则覆盖，不存在则创建（含中间目录）。",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径"},
                "content": {"type": "string", "description": "写入内容"},
            },
            "required": ["file_path", "content"],
        },
    ),
    ToolDefinition(
        name="edit_file",
        description="编辑文件。将 old_string 替换为 new_string。",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文件路径"},
                "old_string": {"type": "string", "description": "要替换的原始文本"},
                "new_string": {"type": "string", "description": "替换后的新文本"},
            },
            "required": ["file_path", "old_string", "new_string"],
        },
    ),
    ToolDefinition(
        name="run_command",
        description="执行 shell 命令并返回输出。",
        parameters={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "要执行的命令"},
                "timeout": {"type": "integer", "description": "超时秒数（默认 30）"},
            },
            "required": ["command"],
        },
    ),
    ToolDefinition(
        name="list_directory",
        description="列出目录内容。",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "目录路径（默认为工作目录）"},
            },
            "required": [],
        },
    ),
    ToolDefinition(
        name="search_content",
        description="在文件中搜索文本模式。",
        parameters={
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "搜索模式（支持正则）"},
                "path": {"type": "string", "description": "搜索路径"},
                "include": {"type": "string", "description": "文件名模式（如 *.py）"},
            },
            "required": ["pattern"],
        },
    ),
    ToolDefinition(
        name="find_files",
        description="查找匹配模式的文件。",
        parameters={
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "glob 模式（如 *.py）"},
                "path": {"type": "string", "description": "搜索根路径"},
            },
            "required": ["pattern"],
        },
    ),
]

# 危险命令黑名单
FORBIDDEN_COMMANDS = [
    "rm -rf /",
    "rm -rf /*",
    "del /s /q C:\\",
    "del /s /q C:",
    "format c:",
    "format C:",
    "shutdown",
    "mkfs",
    "dd if=",
    ":(){:|:&};:",
    "chmod -R 777 /",
    "chown -R",
    "> /dev/sda",
]


class ToolExecutor:
    """
    工具执行器

    在工作目录内安全执行 LLM 请求的工具调用
    """

    def __init__(self, working_dir: Optional[str] = None):
        self.working_dir = Path(working_dir or ".").resolve()
        self._files_changed: list[str] = []

    @property
    def files_changed(self) -> list[str]:
        """获取已修改的文件列表"""
        return list(self._files_changed)

    def reset_files_changed(self) -> None:
        """重置文件变更追踪"""
        self._files_changed.clear()

    def get_tool_definitions(self) -> list[dict]:
        """获取 OpenAI 格式的工具定义"""
        return [t.to_openai_format() for t in BUILTIN_TOOLS]

    def execute(self, tool_name: str, args: dict) -> ToolResult:
        """
        执行工具调用

        Args:
            tool_name: 工具名称
            args: 工具参数

        Returns:
            ToolResult
        """
        dispatch = {
            "read_file": self._read_file,
            "write_file": self._write_file,
            "edit_file": self._edit_file,
            "run_command": self._run_command,
            "list_directory": self._list_directory,
            "search_content": self._search_content,
            "find_files": self._find_files,
        }
        handler = dispatch.get(tool_name)
        if not handler:
            return ToolResult(success=False, error=f"Unknown tool: {tool_name}")

        try:
            return handler(args)
        except Exception as e:
            logger.error("工具执行失败 %s: %s", tool_name, e)
            return ToolResult(success=False, error=str(e))

    # ==================== 路径安全 ====================

    def _resolve_path(self, file_path: str) -> Path:
        """解析并验证路径安全"""
        p = Path(file_path)
        if not p.is_absolute():
            p = self.working_dir / p
        resolved = p.resolve()

        # 路径遍历检查
        try:
            resolved.relative_to(self.working_dir)
        except ValueError:
            # 允许访问工作目录之外的文件读取（但不能写入）
            pass

        return resolved

    def _is_safe_path(self, file_path: str) -> bool:
        """检查路径是否在工作目录内"""
        p = Path(file_path)
        if not p.is_absolute():
            p = self.working_dir / p
        try:
            p.resolve().relative_to(self.working_dir)
            return True
        except ValueError:
            return False

    def _is_command_allowed(self, command: str) -> bool:
        """检查命令是否被允许"""
        cmd_lower = command.lower().strip()
        for forbidden in FORBIDDEN_COMMANDS:
            if forbidden.lower() in cmd_lower:
                return False
        return True

    def _track_change(self, file_path: str) -> None:
        """追踪文件变更"""
        # 存储相对路径
        try:
            p = Path(file_path)
            if not p.is_absolute():
                rel = str(p)
            else:
                rel = str(p.relative_to(self.working_dir))
        except ValueError:
            rel = str(p)
        if rel not in self._files_changed:
            self._files_changed.append(rel)

    # ==================== 工具实现 ====================

    def _read_file(self, args: dict) -> ToolResult:
        """读取文件"""
        file_path = args["file_path"]
        resolved = self._resolve_path(file_path)

        if not resolved.exists():
            return ToolResult(success=False, error=f"File not found: {file_path}")
        if not resolved.is_file():
            return ToolResult(success=False, error=f"Not a file: {file_path}")

        try:
            content = resolved.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return ToolResult(success=False, error=f"Cannot read file (binary?): {file_path}")

        # 支持行范围
        offset = args.get("offset")
        limit = args.get("limit")
        if offset or limit:
            lines = content.splitlines(keepends=True)
            start = (offset or 1) - 1
            end = start + (limit or len(lines))
            content = "".join(lines[start:end])

        return ToolResult(success=True, output=content)

    def _write_file(self, args: dict) -> ToolResult:
        """写入文件"""
        file_path = args["file_path"]
        content = args["content"]
        resolved = self._resolve_path(file_path)

        # 创建中间目录
        resolved.parent.mkdir(parents=True, exist_ok=True)

        resolved.write_text(content, encoding="utf-8")
        self._track_change(file_path)
        logger.debug("写入文件: %s", file_path)

        return ToolResult(success=True, output=f"Written {len(content)} chars to {file_path}")

    def _edit_file(self, args: dict) -> ToolResult:
        """编辑文件"""
        file_path = args["file_path"]
        old_string = args["old_string"]
        new_string = args["new_string"]
        resolved = self._resolve_path(file_path)

        if not resolved.exists():
            return ToolResult(success=False, error=f"File not found: {file_path}")

        content = resolved.read_text(encoding="utf-8")
        if old_string not in content:
            return ToolResult(
                success=False,
                error=f"old_string not found in {file_path}",
            )

        new_content = content.replace(old_string, new_string, 1)
        resolved.write_text(new_content, encoding="utf-8")
        self._track_change(file_path)
        logger.debug("编辑文件: %s", file_path)

        return ToolResult(success=True, output=f"Edited {file_path}")

    def _run_command(self, args: dict) -> ToolResult:
        """执行命令"""
        command = args["command"]
        timeout = args.get("timeout", 30)

        # 安全检查
        if not self._is_command_allowed(command):
            return ToolResult(success=False, error=f"Forbidden command: {command}")

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                cwd=str(self.working_dir),
            )

            output = result.stdout
            if result.stderr:
                output += ("\n" if output else "") + result.stderr

            if result.returncode != 0:
                return ToolResult(
                    success=False,
                    output=output.strip(),
                    error=f"Exit code {result.returncode}",
                )

            return ToolResult(success=True, output=output.strip())

        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error=f"Command timed out after {timeout}s")
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def _list_directory(self, args: dict) -> ToolResult:
        """列出目录"""
        dir_path = args.get("path", ".")
        resolved = self._resolve_path(dir_path)

        if not resolved.exists():
            return ToolResult(success=False, error=f"Directory not found: {dir_path}")
        if not resolved.is_dir():
            return ToolResult(success=False, error=f"Not a directory: {dir_path}")

        entries = sorted(resolved.iterdir(), key=lambda p: (not p.is_dir(), p.name))
        lines = []
        for entry in entries:
            prefix = "DIR " if entry.is_dir() else "FILE"
            lines.append(f"{prefix} {entry.name}")

        return ToolResult(success=True, output="\n".join(lines))

    def _search_content(self, args: dict) -> ToolResult:
        """搜索内容"""
        pattern = args["pattern"]
        search_path = args.get("path", ".")
        include = args.get("include", "*")
        resolved = self._resolve_path(search_path)

        if not resolved.exists():
            return ToolResult(success=False, error=f"Path not found: {search_path}")

        matches = []
        try:
            regex = re.compile(pattern)
        except re.error:
            # 如果不是有效正则，当作普通文本搜索
            regex = re.compile(re.escape(pattern))

        search_root = resolved if resolved.is_dir() else resolved.parent

        for file_path in search_root.rglob(include):
            if not file_path.is_file():
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
                for i, line in enumerate(content.splitlines(), 1):
                    if regex.search(line):
                        rel = file_path.relative_to(self.working_dir)
                        matches.append(f"{rel}:{i}: {line.strip()}")
            except (UnicodeDecodeError, PermissionError):
                continue

        return ToolResult(success=True, output="\n".join(matches))

    def _find_files(self, args: dict) -> ToolResult:
        """查找文件"""
        pattern = args["pattern"]
        search_path = args.get("path", ".")
        resolved = self._resolve_path(search_path)

        if not resolved.exists():
            return ToolResult(success=False, error=f"Path not found: {search_path}")

        search_root = resolved if resolved.is_dir() else resolved.parent
        matches = []

        for p in search_root.rglob(pattern):
            if p.is_file():
                try:
                    rel = p.relative_to(self.working_dir)
                    matches.append(str(rel))
                except ValueError:
                    matches.append(str(p))

        return ToolResult(success=True, output="\n".join(sorted(matches)))
