"""
愚公循环需求解析器

将各种格式的需求转换为结构化的 UserStory 列表。

支持格式:
- prd.json (Ralph 标准格式)
- Markdown (从标题和列表项提取)
- 纯文本 (生成 AI 拆解 Prompt)
"""

import json
import logging
from pathlib import Path
from typing import Union

from .models import UserStory, ParsedRequirement, StoryPriority
from .config import YuGongConfig

logger = logging.getLogger(__name__)


class RequirementParser:
    """解析需求文档→结构化 UserStory 列表"""

    SUPPORTED_FORMATS = ["json", "markdown", "text", "auto"]

    def __init__(self, config: YuGongConfig | None = None):
        self.config = config or YuGongConfig()

    def parse(
        self,
        source: Union[str, Path],
        format: str = "auto",
    ) -> ParsedRequirement:
        """
        解析需求

        Args:
            source: 需求来源(文件路径或文本)
            format: 格式(json/markdown/text/auto)

        Returns:
            ParsedRequirement 对象
        """
        if isinstance(source, Path):
            content = source.read_text(encoding="utf-8")
            source_path = source
        elif source.endswith(".json") or source.endswith(".md"):
            source_path = Path(source)
            content = source_path.read_text(encoding="utf-8")
        else:
            return self._parse_text(source)

        if format == "auto":
            format = self._detect_format(source_path, content)

        if format == "json":
            return self._parse_json(content)
        elif format == "markdown":
            return self._parse_markdown(content)
        else:
            return self._parse_text(content)

    def _detect_format(self, path: Path, content: str) -> str:
        """自动检测格式"""
        if path.suffix == ".json":
            return "json"
        if path.suffix == ".md":
            return "markdown"
        try:
            json.loads(content)
            return "json"
        except (json.JSONDecodeError, ValueError) as e:
            logger.debug("Content is not valid JSON, trying other formats: %s", e)
            pass
        if content.startswith("#") or "##" in content:
            return "markdown"
        return "text"

    def _parse_json(self, content: str) -> ParsedRequirement:
        """解析 prd.json 格式 (Ralph 标准格式)"""
        data = json.loads(content)
        if not isinstance(data, dict):
            return self._parse_text(content)

        # 支持 userStories (camelCase) 和 user_stories (snake_case)
        raw_stories = data.get("userStories", data.get("user_stories", []))

        stories = []
        for i, s in enumerate(raw_stories):
            # 支持 acceptanceCriteria 和 acceptance_criteria
            ac = s.get("acceptanceCriteria", s.get("acceptance_criteria", []))
            stories.append(
                UserStory(
                    id=s.get("id", f"US-{i + 1:03d}"),
                    title=s.get("title", ""),
                    description=s.get("description", ""),
                    acceptance_criteria=ac if isinstance(ac, list) else [],
                    notes=s.get("notes", ""),
                )
            )

        # 支持 project/project_name, branchName/branch_name
        project_name = data.get("project", data.get("project_name", "Untitled"))
        branch_name = data.get("branchName", data.get("branch_name", "yugong/main"))

        return ParsedRequirement(
            project_name=project_name,
            branch_name=branch_name,
            description=data.get("description", ""),
            user_stories=stories,
            raw_source=content,
            format="json",
        )

    def _parse_markdown(self, content: str) -> ParsedRequirement:
        """解析 Markdown 格式需求"""
        lines = content.split("\n")

        # 提取项目名称 (# 一级标题)
        project_name = "Untitled"
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("# "):
                project_name = stripped[2:].strip()
                break

        # 提取 ## 二级标题作为 Story, - [ ] / - [x] 作为验收标准
        stories: list[UserStory] = []
        current_story: UserStory | None = None
        desc_lines: list[str] = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("## "):
                if current_story:
                    current_story.description = "\n".join(desc_lines).strip()
                    stories.append(current_story)
                current_story = UserStory(
                    id=f"US-{len(stories) + 1:03d}",
                    title=stripped[3:].strip(),
                    description="",
                )
                desc_lines = []
            elif stripped.startswith("- [") and "]" in stripped:
                # 验收标准 (checkbox)
                bracket_end = stripped.index("]")
                criteria = stripped[bracket_end + 1 :].strip()
                if current_story and criteria:
                    current_story.acceptance_criteria.append(criteria)
            elif current_story and stripped:
                desc_lines.append(stripped)

        if current_story:
            current_story.description = "\n".join(desc_lines).strip()
            stories.append(current_story)

        return ParsedRequirement(
            project_name=project_name,
            branch_name=f"yugong/{project_name.lower().replace(' ', '-')}",
            description="",
            user_stories=stories,
            raw_source=content,
            format="markdown",
        )

    def _parse_text(self, content: str) -> ParsedRequirement:
        """纯文本需求 → 标记为需要 AI 拆解"""
        return ParsedRequirement(
            project_name="AutoDetected",
            branch_name="yugong/auto-task",
            description=content,
            user_stories=[],
            raw_source=content,
            format="text",
        )

    def generate_split_prompt(self, requirement: str) -> str:
        """生成 AI 拆解 Prompt"""
        return f"""请将以下需求拆解为独立的 UserStory 列表 (JSON 格式):

需求:
{requirement}

拆解规则:
1. 每个 UserStory 必须能在单次上下文窗口内完成
2. 按依赖顺序排列: 数据库 -> 后端 -> UI -> 聚合
3. 每个 Story 包含: id, title, description, acceptance_criteria, priority
4. 验收标准必须可验证(不是"工作正常"而是"点击按钮显示确认对话框")

输出格式 (prd.json):
{{
  "project": "...",
  "branchName": "yugong/...",
  "description": "...",
  "userStories": [...]
}}"""
