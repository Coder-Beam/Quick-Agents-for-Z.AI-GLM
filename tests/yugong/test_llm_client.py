"""
LLMClient 测试 - OpenAI 兼容 API 客户端

测试策略: mock httpx HTTP 响应，不依赖真实 API
"""

import pytest
import json
from unittest.mock import patch, MagicMock

from quickagents.yugong.llm_client import LLMClient, LLMConfig, Message, ToolCall, ChatResponse


@pytest.fixture
def config():
    """默认配置"""
    return LLMConfig(
        api_key="test-key-123",
        base_url="https://open.bigmodel.cn/api/coding/paas/v4",
        model="GLM-5",
    )


@pytest.fixture
def client(config):
    """LLM 客户端实例"""
    return LLMClient(config)


def _mock_response(status_code=200, json_data=None):
    """构建 mock HTTP 响应"""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        from httpx import HTTPStatusError

        resp.raise_for_status.side_effect = HTTPStatusError("error", request=MagicMock(), response=resp)
    return resp


# ================================================================
# Test 1: LLMConfig
# ================================================================


class TestLLMConfig:
    def test_defaults(self):
        """默认配置"""
        cfg = LLMConfig(api_key="key")
        assert cfg.model == "GLM-5"
        assert cfg.max_tokens == 8192
        assert cfg.temperature == 0.1
        assert cfg.timeout == 120

    def test_from_env(self):
        """从环境变量构建"""
        with patch.dict("os.environ", {"ZHIPUAI_API_KEY": "env-key"}):
            cfg = LLMConfig.from_env()
            assert cfg.api_key == "env-key"

    def test_from_env_custom_provider(self):
        """从环境变量构建自定义 provider"""
        env = {
            "OPENAI_API_KEY": "openai-key",
            "OPENAI_BASE_URL": "https://api.openai.com/v1",
        }
        with patch.dict("os.environ", env):
            cfg = LLMConfig.from_env(provider="openai")
            assert cfg.api_key == "openai-key"
            assert cfg.base_url == "https://api.openai.com/v1"

    def test_from_env_missing_key(self):
        """环境变量不存在时抛出"""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="API key"):
                LLMConfig.from_env()

    def test_to_dict(self):
        """序列化"""
        cfg = LLMConfig(api_key="key", model="GLM-4.7")
        d = cfg.to_dict()
        assert d["model"] == "GLM-4.7"
        assert d["api_key"] == "key"


# ================================================================
# Test 2: Chat 基础调用
# ================================================================


class TestChat:
    def test_simple_chat(self, client):
        """简单文本对话"""
        mock_resp = _mock_response(
            json_data={
                "id": "chatcmpl-123",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "Hello!"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            }
        )

        with patch.object(client, "_http_post", return_value=mock_resp):
            response = client.chat([Message(role="user", content="Hi")])

        assert response.content == "Hello!"
        assert response.usage["total_tokens"] == 15
        assert response.tool_calls is None
        assert response.finish_reason == "stop"

    def test_chat_with_system_prompt(self, client):
        """带系统提示的对话"""
        mock_resp = _mock_response(
            json_data={
                "id": "chatcmpl-456",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "Done"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 20, "completion_tokens": 5, "total_tokens": 25},
            }
        )

        messages = [
            Message(role="system", content="You are a coder"),
            Message(role="user", content="Write code"),
        ]
        with patch.object(client, "_http_post", return_value=mock_resp):
            response = client.chat(messages)

        assert response.content == "Done"
        assert response.usage["total_tokens"] == 25

    def test_chat_with_tools(self, client):
        """带工具调用的对话"""
        mock_resp = _mock_response(
            json_data={
                "id": "chatcmpl-789",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "",
                            "tool_calls": [
                                {
                                    "id": "call_001",
                                    "type": "function",
                                    "function": {
                                        "name": "read_file",
                                        "arguments": '{"file_path": "/src/main.py"}',
                                    },
                                }
                            ],
                        },
                        "finish_reason": "tool_calls",
                    }
                ],
                "usage": {"prompt_tokens": 30, "completion_tokens": 20, "total_tokens": 50},
            }
        )

        tools = [{"type": "function", "function": {"name": "read_file", "parameters": {}}}]
        with patch.object(client, "_http_post", return_value=mock_resp):
            response = client.chat(
                [Message(role="user", content="Read main.py")],
                tools=tools,
            )

        assert response.tool_calls is not None
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0].name == "read_file"
        assert response.tool_calls[0].arguments == {"file_path": "/src/main.py"}

    def test_multiple_tool_calls(self, client):
        """多个并行工具调用"""
        mock_resp = _mock_response(
            json_data={
                "id": "chatcmpl-multi",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "",
                            "tool_calls": [
                                {
                                    "id": "call_1",
                                    "type": "function",
                                    "function": {"name": "read_file", "arguments": '{"file_path": "a.py"}'},
                                },
                                {
                                    "id": "call_2",
                                    "type": "function",
                                    "function": {"name": "run_command", "arguments": '{"command": "pytest"}'},
                                },
                            ],
                        },
                        "finish_reason": "tool_calls",
                    }
                ],
                "usage": {"prompt_tokens": 50, "completion_tokens": 30, "total_tokens": 80},
            }
        )

        with patch.object(client, "_http_post", return_value=mock_resp):
            response = client.chat([Message(role="user", content="Go")])

        assert len(response.tool_calls) == 2
        assert response.tool_calls[0].name == "read_file"
        assert response.tool_calls[1].name == "run_command"


# ================================================================
# Test 3: 错误处理
# ================================================================


class TestChatErrors:
    def test_api_error(self, client):
        """API 错误"""
        from httpx import HTTPStatusError

        mock_resp = _mock_response(status_code=429, json_data={"error": "rate limited"})
        mock_resp.raise_for_status.side_effect = HTTPStatusError(
            "rate limited", request=MagicMock(), response=mock_resp
        )

        with patch.object(client, "_http_post", return_value=mock_resp):
            with pytest.raises(Exception):
                client.chat([Message(role="user", content="Hi")])

    def test_retry_on_transient_error(self, client):
        """瞬时错误自动重试"""
        call_count = 0

        def mock_post(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                mock_resp = _mock_response(status_code=500, json_data={"error": "server error"})
                from httpx import HTTPStatusError

                mock_resp.raise_for_status.side_effect = HTTPStatusError("500", request=MagicMock(), response=mock_resp)
                return mock_resp
            return _mock_response(
                json_data={
                    "id": "ok",
                    "choices": [
                        {"index": 0, "message": {"role": "assistant", "content": "OK"}, "finish_reason": "stop"}
                    ],
                    "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7},
                }
            )

        client.config.max_retries = 3
        with patch.object(client, "_http_post", side_effect=mock_post):
            response = client.chat([Message(role="user", content="Hi")])

        assert response.content == "OK"
        assert call_count == 2


# ================================================================
# Test 4: Message 序列化
# ================================================================


class TestMessage:
    def test_to_dict_simple(self):
        """简单消息序列化"""
        msg = Message(role="user", content="hello")
        d = msg.to_dict()
        assert d == {"role": "user", "content": "hello"}

    def test_to_dict_with_tool_calls(self):
        """带工具调用的消息序列化"""
        msg = Message(
            role="assistant",
            content="",
            tool_calls=[
                ToolCall(id="call_1", name="read_file", arguments={"path": "x.py"}),
            ],
        )
        d = msg.to_dict()
        assert d["tool_calls"][0]["function"]["name"] == "read_file"

    def test_tool_result_message(self):
        """工具结果消息"""
        msg = Message(
            role="tool",
            content="file contents here",
            tool_call_id="call_1",
        )
        d = msg.to_dict()
        assert d["role"] == "tool"
        assert d["tool_call_id"] == "call_1"
