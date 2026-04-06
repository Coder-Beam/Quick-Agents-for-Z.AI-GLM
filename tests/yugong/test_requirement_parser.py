"""
愚公循环需求解析器测试
"""

import pytest
import json
import tempfile
from pathlib import Path

from quickagents.yugong.requirement_parser import RequirementParser
from quickagents.yugong.models import ParsedRequirement, UserStory
from quickagents.yugong.config import YuGongConfig


class TestFormatDetection:
    """格式自动检测"""

    def test_detect_json_by_extension(self):
        parser = RequirementParser()
        assert parser._detect_format(Path("test.json"), "") == "json"

    def test_detect_markdown_by_extension(self):
        parser = RequirementParser()
        assert parser._detect_format(Path("test.md"), "") == "markdown"

    def test_detect_json_by_content(self):
        parser = RequirementParser()
        assert parser._detect_format(Path("test.txt"), '{"project":"test"}') == "json"

    def test_detect_markdown_by_content(self):
        parser = RequirementParser()
        assert parser._detect_format(Path("test.txt"), "# 标题\n## 功能1") == "markdown"

    def test_detect_text_fallback(self):
        parser = RequirementParser()
        assert parser._detect_format(Path("test.txt"), "简单文本需求") == "text"


class TestJsonParsing:
    """JSON 格式解析"""

    def test_parse_standard_prd(self):
        parser = RequirementParser()
        prd = {
            "project": "测试项目",
            "branchName": "yugong/test",
            "description": "测试描述",
            "userStories": [
                {
                    "id": "US-001",
                    "title": "用户登录",
                    "description": "实现登录",
                    "acceptanceCriteria": ["输入用户名", "点击登录"],
                    "notes": "",
                },
                {
                    "id": "US-002",
                    "title": "用户注册",
                    "description": "实现注册",
                    "acceptanceCriteria": ["填写表单"],
                },
            ],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(prd, f, ensure_ascii=False)
            temp = Path(f.name)

        try:
            result = parser.parse(temp)
            assert result.project_name == "测试项目"
            assert result.branch_name == "yugong/test"
            assert len(result.user_stories) == 2
            assert result.user_stories[0].title == "用户登录"
            assert result.user_stories[0].acceptance_criteria == ["输入用户名", "点击登录"]
            assert result.format == "json"
        finally:
            temp.unlink(missing_ok=True)

    def test_parse_json_with_defaults(self):
        parser = RequirementParser()
        prd = {"userStories": [{"title": "功能A"}]}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(prd, f, ensure_ascii=False)
            temp = Path(f.name)

        try:
            result = parser.parse(temp)
            assert result.project_name == "Untitled"
            assert len(result.user_stories) == 1
            assert result.user_stories[0].id == "US-001"
        finally:
            temp.unlink(missing_ok=True)

    def test_parse_empty_json(self):
        parser = RequirementParser()
        prd = {"project": "空项目", "userStories": []}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(prd, f, ensure_ascii=False)
            temp = Path(f.name)

        try:
            result = parser.parse(temp)
            assert len(result.user_stories) == 0
        finally:
            temp.unlink(missing_ok=True)


class TestMarkdownParsing:
    """Markdown 格式解析"""

    def test_parse_simple_markdown(self):
        parser = RequirementParser()
        content = "# 我的博客\n\n## 用户登录\n- [ ] 登录页面\n- [ ] 登录API\n\n## 文章管理\n- [ ] 创建文章\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(content)
            temp = Path(f.name)

        try:
            result = parser.parse(temp)
            assert result.project_name == "我的博客"
            assert result.format == "markdown"
            assert len(result.user_stories) == 2
            assert result.user_stories[0].title == "用户登录"
            assert "登录页面" in result.user_stories[0].acceptance_criteria
            assert result.user_stories[1].title == "文章管理"
        finally:
            temp.unlink(missing_ok=True)


class TestTextParsing:
    """纯文本格式解析"""

    def test_parse_text_string(self):
        parser = RequirementParser()
        result = parser.parse("实现一个用户管理系统")
        assert result.format == "text"
        assert result.project_name == "AutoDetected"
        assert len(result.user_stories) == 0

    def test_parse_text_needs_split(self):
        parser = RequirementParser()
        result = parser.parse("做一个电商网站")
        assert result.format == "text"
        assert len(result.user_stories) == 0


class TestSplitPrompt:
    """需求拆解 Prompt"""

    def test_generate_split_prompt(self):
        parser = RequirementParser()
        prompt = parser.generate_split_prompt("实现用户认证系统")
        assert "用户认证系统" in prompt
        assert "UserStory" in prompt
        assert "prd.json" in prompt
