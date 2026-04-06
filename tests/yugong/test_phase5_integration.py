"""
愚公循环 Phase 5 集成测试

端到端验证:
1. AgentExecutor + YuGongDB + YuGongLoop 全流程
2. 真实工具执行（文件读写）
3. 猢久化化 + 跨会话恢复
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime

from quickagents.yugong.config import YuGongConfig
from quickagents.yugong.models import (
    UserStory,
    LoopResult,
    LoopState,
    ParsedRequirement,
    StoryPriority,
    StoryStatus,
)
from quickagents.yugong.db import YuGongDB
from quickagents.yugong.autonomous_loop import YuGongLoop
from quickagents.yugong.llm_client import LLMClient, LLMConfig, ChatResponse, ToolCall
from quickagents.yugong.tool_executor import ToolExecutor
from quickagents.yugong.agent_executor import AgentExecutor, AgentConfig


# ================================================================
# Test 1: 真实文件操作端到端
# ================================================================


class TestRealFileOperations:
    """Agent 通过工具执行真实的文件读写"""

    def test_agent_writes_and_reads_file(self, tmp_path):
        """Agent 写入文件后读回验证"""
        tools = ToolExecutor(working_dir=str(tmp_path))
        llm = MagicMock(spec=LLMClient)
        llm.config = LLMConfig(api_key="test")

        # Turn 1: Agent 决定写入文件
        # Turn 2: Agent 完成
        llm.chat.side_effect = [
            ChatResponse(
                content="",
                tool_calls=[
                    ToolCall(
                        id="c1",
                        name="write_file",
                        arguments={
                            "file_path": "hello.py",
                            "content": "def greet(name): return f'Hello, {name}!'",
                        },
                    )
                ],
                usage={"prompt_tokens": 30, "completion_tokens": 20, "total_tokens": 50},
                finish_reason="tool_calls",
            ),
            ChatResponse(
                content="File written successfully. TASK_COMPLETE",
                tool_calls=None,
                usage={"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30},
                finish_reason="stop",
            ),
        ]

        agent = AgentExecutor(llm_client=llm, tool_executor=tools)
        result = agent("Create a greet function")

        assert result["success"] is True
        assert "hello.py" in result["files_changed"]
        assert (tmp_path / "hello.py").exists()
        content = (tmp_path / "hello.py").read_text(encoding="utf-8")
        assert "greet" in content

    def test_agent_edits_file(self, tmp_path):
        """Agent 编辑已存在的文件"""
        # 预置文件
        (tmp_path / "calc.py").write_text(
            "def add(a, b):\n    return a + b",
            encoding="utf-8",
        )

        tools = ToolExecutor(working_dir=str(tmp_path))
        llm = MagicMock(spec=LLMClient)
        llm.config = LLMConfig(api_key="test")

        llm.chat.side_effect = [
            ChatResponse(
                content="",
                tool_calls=[
                    ToolCall(
                        id="c1",
                        name="read_file",
                        arguments={"file_path": "calc.py"},
                    ),
                ],
                usage={"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30},
                finish_reason="tool_calls",
            ),
            ChatResponse(
                content="",
                tool_calls=[
                    ToolCall(
                        id="c2",
                        name="edit_file",
                        arguments={
                            "file_path": "calc.py",
                            "old_string": "return a + b",
                            "new_string": "return a + b  # addition",
                        },
                    ),
                ],
                usage={"prompt_tokens": 25, "completion_tokens": 15, "total_tokens": 40},
                finish_reason="tool_calls",
            ),
            ChatResponse(
                content="Added comment. TASK_COMPLETE",
                tool_calls=None,
                usage={"prompt_tokens": 15, "completion_tokens": 10, "total_tokens": 25},
                finish_reason="stop",
            ),
        ]

        agent = AgentExecutor(llm_client=llm, tool_executor=tools)
        result = agent("Add a comment to calc.py")

        assert result["success"] is True
        content = (tmp_path / "calc.py").read_text(encoding="utf-8")
        assert "# addition" in content


# ================================================================
# Test 2: YuGongLoop + AgentExecutor + YuGongDB
# ================================================================


class TestFullLoop:
    """完整的愚公循环: 真实 Agent 执行 + DB 持久化"""

    def test_loop_with_db(self, tmp_path):
        """循环执行并将结果持久化到数据库"""
        db = YuGongDB(":memory:")
        tools = ToolExecutor(working_dir=str(tmp_path))
        llm = MagicMock(spec=LLMClient)
        llm.config = LLMConfig(api_key="test")

        # Agent 成功完成 Story
        llm.chat.return_value = ChatResponse(
            content="Implementation complete. All tests pass. TASK_COMPLETE",
            tool_calls=None,
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            finish_reason="stop",
        )

        agent = AgentExecutor(llm_client=llm, tool_executor=tools)

        config = YuGongConfig(max_iterations=5, min_iterations=1)
        loop = YuGongLoop(config=config, agent_fn=agent)

        req = ParsedRequirement(
            project_name="test-project",
            branch_name="test/integration",
            description="Test project for integration",
            user_stories=[
                UserStory(id="US-001", title="Create hello", description="Create hello module"),
            ],
            raw_source="test",
            format="text",
        )

        outcome = loop.start(req)

        # 验证循环结果
        assert outcome.total_iterations >= 1
        assert outcome.total_stories == 1

        # 手动持久化到 DB
        db.save_state(loop.state)
        loaded_state = db.load_state()
        assert loaded_state is not None
        assert loaded_state.status == "completed"

    def test_loop_multi_stories(self, tmp_path):
        """多个 Stories 的循环"""
        db = YuGongDB(":memory:")
        tools = ToolExecutor(working_dir=str(tmp_path))
        llm = MagicMock(spec=LLMClient)
        llm.config = LLMConfig(api_key="test")

        call_count = 0

        def chat_fn(messages, **kwargs):
            nonlocal call_count
            call_count += 1
            return ChatResponse(
                content=f"Story done (iteration {call_count}). TASK_COMPLETE",
                tool_calls=None,
                usage={"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
                finish_reason="stop",
            )

        llm.chat.side_effect = chat_fn

        agent = AgentExecutor(llm_client=llm, tool_executor=tools)

        config = YuGongConfig(max_iterations=10, min_iterations=1)

        loop = YuGongLoop(config=config, agent_fn=agent)

        req = ParsedRequirement(
            project_name="multi-story",
            branch_name="test/multi",
            description="Multi-story test",
            user_stories=[
                UserStory(id="US-001", title="Task 1", description="First task"),
                UserStory(id="US-002", title="Task 2", description="Second task"),
            ],
            raw_source="test",
            format="text",
        )

        outcome = loop.start(req)

        assert outcome.total_iterations >= 2
        assert outcome.total_stories == 2

        # 持久化所有 Stories
        for story in loop.orchestrator.get_all_stories():
            db.save_story(story)

        stories_in_db = db.get_all_stories()
        assert len(stories_in_db) == 2


# ================================================================
# Test 3: 持久化验证
# ================================================================


class TestPersistence:
    """跨会话恢复验证"""

    def test_save_and_restore_state(self, tmp_path):
        """保存状态到 DB 并恢复"""
        db_path = str(tmp_path / "test_persistence.db")
        db = YuGongDB(db_path)

        # 创建循环状态
        state = LoopState(
            status="running",
            current_iteration=5,
            total_stories=10,
            completed_stories=3,
        )

        db.save_state(state)

        # 关闭并重新打开
        db.close()
        db2 = YuGongDB(db_path)

        loaded = db2.load_state()
        assert loaded is not None
        assert loaded.status == "running"
        assert loaded.current_iteration == 5
        assert loaded.total_stories == 10
        assert loaded.completed_stories == 3
        db2.close()

    def test_save_and_restore_stories(self, tmp_path):
        """保存 Stories 到 DB 并恢复"""
        db_path = str(tmp_path / "test_stories.db")
        db = YuGongDB(db_path)

        stories = [
            UserStory(
                id="US-001",
                title="Auth",
                description="Auth module",
                acceptance_criteria=["Login works", "JWT issued"],
                priority=StoryPriority(1),
            ),
            UserStory(
                id="US-002",
                title="Dashboard",
                description="User dashboard",
                dependencies=["US-001"],
                priority=StoryPriority(2),
            ),
        ]

        for s in stories:
            db.save_story(s)

        db.close()
        db2 = YuGongDB(db_path)

        loaded = db2.get_all_stories()
        assert len(loaded) == 2

        auth = db2.get_story("US-001")
        assert auth.title == "Auth"
        assert auth.priority.value == 1
        assert auth.acceptance_criteria == ["Login works", "JWT issued"]

        dashboard = db2.get_story("US-002")
        assert dashboard.dependencies == ["US-001"]

        db2.close()

    def test_save_and_restore_iterations(self, tmp_path):
        """保存迭代记录并恢复"""
        db_path = str(tmp_path / "test_iterations.db")
        db = YuGongDB(db_path)

        from quickagents.yugong.models import LoopResult

        result = LoopResult(
            iteration=1,
            story_id="US-001",
            success=True,
            output="Completed",
            duration_ms=5000,
            token_usage={"total": 100},
            files_changed=["auth.py", "test_auth.py"],
        )
        db.save_iteration(result)

        db.close()
        db2 = YuGongDB(db_path)

        iters = db2.get_iterations(story_id="US-001")
        assert len(iters) == 1
        assert iters[0].success is True
        assert iters[0].files_changed == ["auth.py", "test_auth.py"]
        db2.close()


# ================================================================
# Test 4: 统计验证
# ================================================================


class TestStatsWithDB:
    """统计数据完整性"""

    def test_stats_after_operations(self):
        """多次操作后统计"""
        db = YuGongDB(":memory:")

        # 写入数据
        db.save_story(UserStory(id="US-001", title="T1", description="D1"))
        db.save_story(UserStory(id="US-002", title="T2", description="D2"))
        db.save_iteration(
            LoopResult(
                iteration=1,
                story_id="US-001",
                success=True,
                output="ok",
                duration_ms=100,
                token_usage={"total": 50},
            )
        )
        db.add_log("INFO", "progress", "Started")

        stats = db.get_stats()
        assert stats["total_stories"] == 2
        assert stats["total_iterations"] == 1
        assert stats["total_logs"] == 1
