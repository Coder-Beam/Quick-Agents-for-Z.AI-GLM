"""
AgentExecutor - 多轮对话 + 工具调用

替换 mock agent_fn，提供真实的 AI Agent 执行能力:
- 多轮对话: LLM 可以反复调用工具直到任务完成
- 工具执行: 文件读写、命令执行、内容搜索
- 结果追踪: Token 消耗、文件变更、成功/失败状态

实现 Callable[[str], dict] 接口，可直接作为 YuGongLoop.agent_fn
"""

import time
import logging
from dataclasses import dataclass, field
from typing import Optional, Callable, Any

from .llm_client import LLMClient, Message, ToolCall
from .tool_executor import ToolExecutor, ToolResult

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Agent 执行配置"""

    max_turns: int = 15  # 单次执行最大对话轮次
    system_prompt: str = (
        "You are an autonomous coding agent. "
        "Your task is to implement the given user story completely.\n\n"
        "Workflow:\n"
        "1. Read existing files to understand the codebase\n"
        "2. Write tests first (TDD)\n"
        "3. Implement the minimum code to pass tests\n"
        "4. Run tests to verify\n"
        "5. Refactor if needed\n"
        "6. Commit changes\n\n"
        "Rules:\n"
        "- Always write tests before implementation\n"
        "- Follow existing code style and patterns\n"
        "- Keep functions under 50 lines\n"
        "- Add comments for complex logic\n"
        "- When done, output 'TASK_COMPLETE' on a line by itself"
    )


class AgentExecutor:
    """
    真实 AI Agent 执行器

    替换 mock agent_fn，实现 Callable[[str], dict] 接口

    工作流程:
        1. 接收 prompt（包含当前 Story 的完整上下文）
        2. 发送给 LLM
        3. 如果 LLM 请求工具调用，执行工具并返回结果
        4. 重复 2-3 直到 LLM 返回纯文本响应或达到 max_turns
        5. 返回汇总结果
    """

    def __init__(
        self,
        llm_client: LLMClient,
        tool_executor: ToolExecutor,
        config: Optional[AgentConfig] = None,
    ):
        self.llm = llm_client
        self.tools = tool_executor
        self.config = config or AgentConfig()

    def __call__(self, prompt: str) -> dict:
        """
        执行 Agent（实现 Callable[[str], dict]）

        Args:
            prompt: 完整的 Story prompt

        Returns:
            {"output": str, "token_usage": dict, "files_changed": list, "success": bool, "error": str|None}
        """
        return self.execute(prompt)

    def execute(self, prompt: str) -> dict:
        """
        执行多轮对话

        Args:
            prompt: 用户 prompt

        Returns:
            执行结果字典
        """
        start_time = time.monotonic()
        self.tools.reset_files_changed()

        messages = [
            Message(role="system", content=self.config.system_prompt),
            Message(role="user", content=prompt),
        ]

        total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        final_output = ""
        last_error = None
        llm_consecutive_failures = 0
        llm_max_retries = 3

        try:
            turn = 0
            while turn < self.config.max_turns:
                try:
                    response = self.llm.chat(
                        messages,
                        tools=self.tools.get_tool_definitions(),
                    )
                    llm_consecutive_failures = 0
                except Exception as llm_err:
                    llm_consecutive_failures += 1
                    err_msg = str(llm_err).lower()
                    is_transient = any(
                        kw in err_msg
                        for kw in ("timeout", "timed out", "connection", "429", "rate limit", "500", "502", "503", "504")
                    )
                    if is_transient and llm_consecutive_failures < llm_max_retries:
                        wait = min(5 * (3 ** (llm_consecutive_failures - 1)), 60)
                        logger.warning(
                            "LLM 调用失败 (%d/%d), %ds 后重试 (不消耗 turn): %s",
                            llm_consecutive_failures, llm_max_retries, wait, llm_err,
                        )
                        time.sleep(wait)
                        continue
                    raise

                for key in total_usage:
                    total_usage[key] += response.usage.get(key, 0)

                if response.tool_calls:
                    messages.append(
                        Message(
                            role="assistant",
                            content=response.content or "",
                            tool_calls=response.tool_calls,
                        )
                    )

                    for tc in response.tool_calls:
                        result = self._execute_tool(tc)
                        messages.append(
                            Message(
                                role="tool",
                                content=result.output or result.error,
                                tool_call_id=tc.id,
                            )
                        )

                    turn += 1
                    continue

                final_output = response.content or ""
                break

            else:
                final_output = f"Max turns ({self.config.max_turns}) exceeded"
                last_error = "max_turns_exceeded"
                logger.warning("Agent 达到最大轮次: %d", self.config.max_turns)

        except Exception as e:
            logger.error("Agent 执行失败: %s", e)
            final_output = str(e)
            last_error = str(e)

        duration_ms = int((time.monotonic() - start_time) * 1000)
        if last_error is None:
            success = bool(final_output) and "max_turns" not in final_output.lower()
        else:
            success = False

        return {
            "output": final_output,
            "token_usage": total_usage,
            "files_changed": self.tools.files_changed,
            "success": success,
            "error": last_error,
            "duration_ms": duration_ms,
        }

    def _execute_tool(self, tool_call: ToolCall) -> ToolResult:
        """执行单个工具调用"""
        logger.debug("工具调用: %s(%s)", tool_call.name, list(tool_call.arguments.keys()))
        result = self.tools.execute(tool_call.name, tool_call.arguments)

        if not result.success:
            logger.warning("工具失败 %s: %s", tool_call.name, result.error)

        return result
