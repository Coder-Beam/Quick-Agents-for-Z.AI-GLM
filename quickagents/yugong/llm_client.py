"""
LLMClient - OpenAI 兼容 API 客户端

支持:
- ZhipuAI (智谱AI Coding Plan)
- OpenAI
- 任何 OpenAI 兼容 API

使用 httpx 进行 HTTP 调用，支持工具调用(function calling)
"""

import json
import time
import logging
import os
from dataclasses import dataclass, field
from typing import Optional, Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """LLM 客户端配置"""

    api_key: str
    base_url: str = "https://open.bigmodel.cn/api/coding/paas/v4"
    model: str = "GLM-5"
    max_tokens: int = 8192
    temperature: float = 0.1
    timeout: int = 120  # 秒
    max_retries: int = 4

    def to_dict(self) -> dict:
        return {
            "api_key": self.api_key,
            "base_url": self.base_url,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
        }

    @classmethod
    def from_env(cls, provider: str = "zhipuai") -> "LLMConfig":
        """
        从环境变量构建配置

        支持的 provider:
        - zhipuai: ZHIPUAI_API_KEY
        - openai: OPENAI_API_KEY, OPENAI_BASE_URL
        """
        if provider == "zhipuai":
            api_key = os.environ.get("ZHIPUAI_API_KEY", "")
            if not api_key:
                raise ValueError("API key not found: set ZHIPUAI_API_KEY environment variable")
            return cls(
                api_key=api_key,
                base_url="https://open.bigmodel.cn/api/coding/paas/v4",
                model="GLM-5",
            )
        elif provider == "openai":
            api_key = os.environ.get("OPENAI_API_KEY", "")
            if not api_key:
                raise ValueError("API key not found: set OPENAI_API_KEY environment variable")
            return cls(
                api_key=api_key,
                base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                model="gpt-4o",
            )
        else:
            raise ValueError(f"Unknown provider: {provider}")


@dataclass
class ToolCall:
    """工具调用"""

    id: str
    name: str
    arguments: dict

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": json.dumps(self.arguments, ensure_ascii=False),
            },
        }


@dataclass
class ChatResponse:
    """LLM 响应"""

    content: str
    tool_calls: Optional[list[ToolCall]]
    usage: dict
    finish_reason: str


@dataclass
class Message:
    """对话消息"""

    role: str  # system, user, assistant, tool
    content: str
    tool_calls: Optional[list[ToolCall]] = None
    tool_call_id: Optional[str] = None

    def to_dict(self) -> dict:
        d: dict[str, Any] = {"role": self.role, "content": self.content}

        if self.tool_calls:
            d["tool_calls"] = [tc.to_dict() for tc in self.tool_calls]

        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id

        return d


class LLMClient:
    """
    OpenAI 兼容 API 客户端

    用法:
        client = LLMClient(LLMConfig(api_key="..."))
        response = client.chat([
            Message(role="system", content="You are a coder"),
            Message(role="user", content="Write a function"),
        ])
        print(response.content)
    """

    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = httpx.Client(
            timeout=config.timeout,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            },
        )

    def chat(
        self,
        messages: list[Message],
        tools: Optional[list[dict]] = None,
    ) -> ChatResponse:
        """
        发送对话请求

        Args:
            messages: 消息列表
            tools: 可选的工具定义列表

        Returns:
            ChatResponse: LLM 响应
        """
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": [m.to_dict() for m in messages],
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }

        if tools:
            payload["tools"] = tools

        last_error = None
        for attempt in range(self.config.max_retries + 1):
            try:
                resp = self._http_post(
                    f"{self.config.base_url}/chat/completions",
                    json=payload,
                )
                return self._parse_response(resp.json())
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries:
                    if not self._is_retryable(e):
                        raise
                    wait = min(5 * (3 ** attempt), 120)
                    logger.warning("LLM 请求失败，%ds 后重试: %s", wait, e)
                    time.sleep(wait)
                else:
                    raise

    @staticmethod
    def _is_retryable(error: Exception) -> bool:
        if isinstance(error, Exception):
            err_msg = str(error).lower()
            retryable_keywords = [
                "timeout", "timed out", "connection", "429", "rate limit",
                "500", "502", "503", "504", "overloaded",
            ]
            return any(kw in err_msg for kw in retryable_keywords)
        return True

    def _http_post(self, url: str, **kwargs) -> httpx.Response:
        """HTTP POST（可被子类/mock 覆盖）"""
        resp = self._client.post(url, **kwargs)
        resp.raise_for_status()
        return resp

    def _parse_response(self, data: dict) -> ChatResponse:
        """解析 API 响应"""
        choice = data["choices"][0]
        msg = choice["message"]

        # 解析工具调用
        tool_calls = None
        if msg.get("tool_calls"):
            tool_calls = []
            for tc in msg["tool_calls"]:
                fn = tc["function"]
                args = fn["arguments"]
                if isinstance(args, str):
                    args = json.loads(args)
                tool_calls.append(
                    ToolCall(
                        id=tc["id"],
                        name=fn["name"],
                        arguments=args,
                    )
                )

        return ChatResponse(
            content=msg.get("content", ""),
            tool_calls=tool_calls,
            usage=data.get("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}),
            finish_reason=choice.get("finish_reason", "stop"),
        )
