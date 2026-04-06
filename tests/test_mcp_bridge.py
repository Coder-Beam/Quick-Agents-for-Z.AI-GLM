"""
Tests for MCPBridge - OpenCode MCP bridge (v2.11.0)
"""

import json
import os
import tempfile

import pytest

from quickagents.core.mcp_bridge import MCPBridge, MCPToolInfo, MCPStatus


class TestMCPBridgeInit:
    def test_default_project_root(self):
        bridge = MCPBridge()
        assert bridge.project_root == os.getcwd()

    def test_custom_project_root(self):
        bridge = MCPBridge(project_root="/tmp")
        assert bridge.project_root == "/tmp"


class TestMCPToolInfo:
    def test_tool_info_creation(self):
        info = MCPToolInfo(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object"},
            server_name="test_server",
        )
        assert info.name == "test_tool"
        assert info.description == "A test tool"
        assert info.server_name == "test_server"

    def test_tool_info_defaults(self):
        info = MCPToolInfo(name="minimal")
        assert info.description == ""
        assert info.input_schema == {}
        assert info.server_name == ""


class TestMCPStatus:
    def test_status_connected(self):
        status = MCPStatus(connected=True, servers=1, tools=5, config_path="/path")
        assert status.connected is True
        assert status.servers == 1
        assert status.tools == 5

    def test_status_disconnected(self):
        status = MCPStatus(connected=False, servers=0, tools=0, config_path="")
        assert status.connected is False


class TestListTools:
    def test_list_tools_no_config(self):
        """Returns empty list when no config found"""
        with tempfile.TemporaryDirectory() as tmpdir:
            bridge = MCPBridge(project_root=tmpdir)
            tools = bridge.list_tools()
            assert tools == []


class TestCheckStatus:
    def test_status_with_no_config(self):
        """Returns disconnected status when no config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            bridge = MCPBridge(project_root=tmpdir)
            status = bridge.check_status()
            assert isinstance(status, MCPStatus)
            assert status.connected is False
            assert status.tools == 0

    def test_status_with_config(self):
        """Returns status from OpenCode config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create opencode config
            config_dir = os.path.join(tmpdir, ".opencode")
            os.makedirs(config_dir, exist_ok=True)
            config_path = os.path.join(config_dir, "config.json")
            config = {"mcpServers": {"test_server": {"url": "http://localhost:3000", "tools": ["tool_a", "tool_b"]}}}
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f)

            bridge = MCPBridge(project_root=tmpdir)
            status = bridge.check_status()
            assert status.servers == 1
            assert status.tools == 2
            assert status.connected is True


class TestCacheInvalidation:
    def test_invalidate_cache(self):
        bridge = MCPBridge()
        bridge._config_cache = {"test": True}
        bridge.invalidate_cache()
        assert bridge._config_cache is None
