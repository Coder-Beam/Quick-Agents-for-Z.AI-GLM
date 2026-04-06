"""
MCPBridge - Read-only bridge to OpenCode's MCP configuration.

Discovers registered MCP servers and tools by reading OpenCode config files.
Does NOT implement an MCP client.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MCPToolInfo:
    name: str
    description: str = ""
    input_schema: Dict[str, Any] = field(default_factory=dict)
    server_name: str = ""


@dataclass
class MCPStatus:
    connected: bool = False
    servers: int = 0
    tools: int = 0
    config_path: str = ""


class MCPBridge:
    """Read-only bridge to OpenCode's MCP server/tool configuration."""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = project_root or os.getcwd()
        self._config_cache: Optional[Dict] = None

    def list_tools(self) -> List[MCPToolInfo]:
        config = self._load_opencode_config()
        if not config:
            return []

        tools: List[MCPToolInfo] = []
        mcp_servers = config.get("mcpServers", config.get("mcp_servers", {}))

        if isinstance(mcp_servers, list):
            mcp_servers = {s.get("name", f"server-{i}"): s for i, s in enumerate(mcp_servers) if isinstance(s, dict)}

        if not isinstance(mcp_servers, dict):
            return tools

        for server_name, server_config in mcp_servers.items():
            if not isinstance(server_config, dict):
                continue

            server_tools = server_config.get("tools", [])
            if not isinstance(server_tools, list):
                continue

            for tool_entry in server_tools:
                if isinstance(tool_entry, str):
                    tools.append(MCPToolInfo(name=tool_entry, server_name=server_name))
                elif isinstance(tool_entry, dict):
                    tools.append(
                        MCPToolInfo(
                            name=tool_entry.get("name", "unknown"),
                            description=tool_entry.get("description", ""),
                            input_schema=tool_entry.get(
                                "inputSchema",
                                tool_entry.get("input_schema", {}),
                            ),
                            server_name=server_name,
                        )
                    )

        return tools

    def get_tool(self, name: str) -> Optional[MCPToolInfo]:
        for tool in self.list_tools():
            if tool.name == name:
                return tool
        return None

    def check_status(self) -> MCPStatus:
        config = self._load_opencode_config()
        if not config:
            return MCPStatus()

        mcp_servers = config.get("mcpServers", config.get("mcp_servers", {}))
        if isinstance(mcp_servers, (list, dict)):
            server_count = len(mcp_servers)
        else:
            server_count = 0

        return MCPStatus(
            connected=server_count > 0,
            servers=server_count,
            tools=len(self.list_tools()),
            config_path=self._get_config_path() or "",
        )

    def _get_config_path(self) -> Optional[str]:
        candidates = [
            os.path.join(self.project_root, ".opencode", "config.json"),
            os.path.join(self.project_root, "opencode.json"),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    def _load_opencode_config(self) -> Optional[Dict]:
        if self._config_cache is not None:
            return self._config_cache

        config_path = self._get_config_path()
        if not config_path:
            return None

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self._config_cache = json.load(f)
                return self._config_cache
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("Failed to load OpenCode config from %s: %s", config_path, e)
            return None

    def invalidate_cache(self) -> None:
        self._config_cache = None
