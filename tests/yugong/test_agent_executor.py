"""
AgentExecutor 测试 - 多轮对话 + 工具调用

测试策略: mock LLM 客户端，验证 AgentExecutor 的多轮编排逻辑
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from quickagents.yugong.agent_executor import AgentExecutor, AgentConfig
from quickagents.yugong.llm_client import LLMClient, LLMConfig, Message, ChatResponse, ToolCall
from quickagents.yugong.tool_executor import ToolExecutor


@pytest.fixture
def mock_llm():
    """Mock LLM 客户端"""
    client = MagicMock(spec=LLMClient)
    client.config = LLMConfig(api_key="test")
    return client


@pytest.fixture
def tool_executor(tmp_path):
    """真实 ToolExecutor"""
    return ToolExecutor(working_dir=str(tmp_path))


@pytest.fixture
def executor(mock_llm, tool_executor):
    """AgentExecutor"""
    return AgentExecutor(
        llm_client=mock_llm,
        tool_executor=tool_executor,
    )


def _text_response(content: str, tokens: int = 50) -> ChatResponse:
    """构建文本响应"""
    return ChatResponse(
        content=content,
        tool_calls=None,
        usage={"prompt_tokens": tokens, "completion_tokens": tokens, "total_tokens": tokens * 2},
        finish_reason="stop",
    )


def _tool_response(calls: list[ToolCall], tokens: int = 30) -> ChatResponse:
    """构建工具调用响应"""
    return ChatResponse(
        content="",
        tool_calls=calls,
        usage={"prompt_tokens": tokens, "completion_tokens": tokens, "total_tokens": tokens * 2},
        finish_reason="tool_calls",
    )


# ================================================================
# Test 1: 基础配置
# ================================================================


class TestAgentConfig:
    def test_defaults(self):
        """默认配置"""
        cfg = AgentConfig()
        assert cfg.max_turns == 15
        assert cfg.system_prompt is not None
        assert "autonomous" in cfg.system_prompt.lower() or "coding" in cfg.system_prompt.lower()

    def test_custom_system_prompt(self):
        """自定义系统提示"""
        cfg = AgentConfig(system_prompt="You are a test writer")
        assert cfg.system_prompt == "You are a test writer"


# ================================================================
# Test 2: 简单对话（无工具调用）
# ================================================================


class TestSimpleConversation:
    def test_single_turn(self, executor, mock_llm):
        """单轮对话"""
        mock_llm.chat.return_value = _text_response("Task completed successfully")

        result = executor("Write a hello world function")

        assert result["output"] == "Task completed successfully"
        # 累计 token_usage: _text_response 的 usage={"prompt_tokens":50, "completion_tokens":50, "total_tokens":100}
        assert result["token_usage"]["total_tokens"] == 100
        assert result["success"] is True
        assert mock_llm.chat.call_count == 1

    def test_system_prompt_included(self, executor, mock_llm):
        """系统提示应该被包含"""
        mock_llm.chat.return_value = _text_response("OK")

        executor("Do something")

        call_args = mock_llm.chat.call_args
        messages = call_args[0][0]
        assert messages[0].role == "system"

    def test_user_message_passed(self, executor, mock_llm):
        """用户消息应该被传递"""
        mock_llm.chat.return_value = _text_response("OK")

        executor("My specific prompt")

        call_args = mock_llm.chat.call_args
        messages = call_args[0][0]
        user_msgs = [m for m in messages if m.role == "user"]
        assert any("My specific prompt" in m.content for m in user_msgs)


# ================================================================
# Test 3: 多轮工具调用
# ================================================================


class TestMultiTurnToolUse:
    def test_read_then_write(self, executor, mock_llm, tmp_path):
        """读取文件 → 修改 → 完成"""
        # 创建一个文件
        (tmp_path / "calc.py").write_text("def add(a, b): return a + b", encoding="utf-8")

        # Turn 1: LLM 请求读取文件
        # Turn 2: LLM 请求写入文件
        # Turn 3: LLM 完成
        mock_llm.chat.side_effect = [
            _tool_response([ToolCall(id="c1", name="read_file", arguments={"file_path": "calc.py"})]),
            _tool_response(
                [
                    ToolCall(
                        id="c2",
                        name="write_file",
                        arguments={
                            "file_path": "calc.py",
                            "content": "def add(a, b): return a + b\ndef sub(a, b): return a - b",
                        },
                    )
                ]
            ),
            _text_response("Added subtract function to calc.py"),
        ]

        result = executor("Add a subtract function to calc.py")

        assert result["success"] is True
        assert "subtract" in result["output"]
        assert mock_llm.chat.call_count == 3
        # 验证文件确实被修改了
        assert "sub" in (tmp_path / "calc.py").read_text(encoding="utf-8")

    def test_multiple_tools_per_turn(self, executor, mock_llm, tmp_path):
        """单轮多个工具调用"""
        (tmp_path / "a.py").write_text("content_a", encoding="utf-8")
        (tmp_path / "b.py").write_text("content_b", encoding="utf-8")

        mock_llm.chat.side_effect = [
            _tool_response(
                [
                    ToolCall(id="c1", name="read_file", arguments={"file_path": "a.py"}),
                    ToolCall(id="c2", name="read_file", arguments={"file_path": "b.py"}),
                ]
            ),
            _text_response("Read both files"),
        ]

        result = executor("Read a.py and b.py")

        assert result["success"] is True
        assert mock_llm.chat.call_count == 2

    def test_tool_results_passed_back(self, executor, mock_llm, tmp_path):
        """工具执行结果应该传回 LLM"""
        (tmp_path / "hello.py").write_text("print('hello')", encoding="utf-8")

        # Turn 1: read file
        # Turn 2: LLM sees the file content and responds
        responses = [
            _tool_response([ToolCall(id="c1", name="read_file", arguments={"file_path": "hello.py"})]),
        ]

        def check_messages(messages, **kwargs):
            if len(responses) > 0:
                # 验证第二轮调用包含了 tool 结果消息
                tool_msgs = [m for m in messages if m.role == "tool"]
                if mock_llm.chat.call_count == 1:
                    # 第一轮只有 system + user
                    pass
                elif mock_llm.chat.call_count == 2:
                    # 第二轮应该有 tool 消息
                    assert len(tool_msgs) == 1
                    assert "print('hello')" in tool_msgs[0].content
                return responses.pop(0)
            return _text_response("Done")

        mock_llm.chat.side_effect = check_messages

        executor("Read hello.py")

    def test_files_changed_tracked(self, executor, mock_llm, tmp_path):
        """文件变更被追踪"""
        mock_llm.chat.side_effect = [
            _tool_response(
                [
                    ToolCall(
                        id="c1",
                        name="write_file",
                        arguments={
                            "file_path": "new_file.py",
                            "content": "x = 1",
                        },
                    )
                ]
            ),
            _text_response("Created file"),
        ]

        result = executor("Create a file")

        assert "new_file.py" in result["files_changed"]


# ================================================================
# Test 4: 错误处理
# ================================================================


class TestErrorHandling:
    def test_tool_execution_error(self, executor, mock_llm):
        """工具执行错误时传回 LLM"""
        responses = [
            _tool_response([ToolCall(id="c1", name="read_file", arguments={"file_path": "nonexistent.py"})]),
        ]

        def check_error_handling(messages, **kwargs):
            if mock_llm.chat.call_count == 1:
                return responses.pop(0)
            # 第二轮应该包含错误消息
            tool_msgs = [m for m in messages if m.role == "tool"]
            assert len(tool_msgs) == 1
            assert "error" in tool_msgs[0].content.lower() or "not found" in tool_msgs[0].content.lower()
            return _text_response("File doesn't exist, creating it instead")

        mock_llm.chat.side_effect = check_error_handling
        result = executor("Read nonexistent.py")
        assert result["success"] is True

    def test_llm_api_error(self, executor, mock_llm):
        """LLM API 错误"""
        mock_llm.chat.side_effect = ConnectionError("API unreachable")

        result = executor("Do something")

        assert result["success"] is False
        assert "API unreachable" in result["output"] or result["error"] is not None

    def test_max_turns_exceeded(self, executor, mock_llm):
        """超过最大轮次限制"""
        executor.config.max_turns = 2

        # 永远返回工具调用，永远不会自行结束
        mock_llm.chat.return_value = _tool_response(
            [
                ToolCall(id="c1", name="run_command", arguments={"command": "echo hi"}),
            ]
        )

        result = executor("Infinite loop")

        assert result["success"] is False
        assert "max" in result["output"].lower() or "turn" in result["output"].lower()


# ================================================================
# Test 5: 作为 agent_fn 集成
# ================================================================


class TestAsAgentFn:
    def test_callable_interface(self, executor, mock_llm):
        """实现 Callable[[str], dict] 接口"""
        mock_llm.chat.return_value = _text_response("OK")

        # 应该可以作为函数调用
        result = executor("test prompt")

        assert isinstance(result, dict)
        assert "output" in result
        assert "token_usage" in result
        assert "files_changed" in result
        assert "success" in result

    def test_with_yugong_loop(self, mock_llm, tool_executor, tmp_path):
        """与 YuGongLoop 集成"""
        from quickagents.yugong import YuGongLoop, YuGongConfig, ParsedRequirement, UserStory

        mock_llm.chat.return_value = _text_response("Story implemented successfully")

        agent_exec = AgentExecutor(llm_client=mock_llm, tool_executor=tool_executor)

        config = YuGongConfig(max_iterations=2, min_iterations=1)
        loop = YuGongLoop(config=config, agent_fn=agent_exec)

        req = ParsedRequirement(
            project_name="test",
            branch_name="test/feature",
            description="Test project",
            user_stories=[
                UserStory(id="US-001", title="Task 1", description="Do task 1"),
            ],
            raw_source="test",
            format="text",
        )

        outcome = loop.start(req)

        # 应该至少执行了一次 agent
        assert mock_llm.chat.call_count >= 1
        assert outcome.total_iterations >= 1
