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

from .models import UserStory, ParsedRequirement
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
            ac = s.get("acceptanceCriteria", s.get("acceptance_criteria", []))
            if isinstance(ac, str):
                ac = [item.strip() for item in ac.replace("\n", ";").split(";") if item.strip()]
            elif not isinstance(ac, list):
                ac = []
            stories.append(
                UserStory(
                    id=s.get("id", f"US-{i + 1:03d}"),
                    title=s.get("title", ""),
                    description=s.get("description", ""),
                    acceptance_criteria=ac,
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
        """解析 Markdown 格式需求

        支持:
        - ## / ### / #### 标题作为 Story
        - - [ ] / - [x] checkbox 作为验收标准
        - - / * 无序列表项作为验收标准
        - | 表格行提取表头+内容
        - ``` 代码块追加到 description
        """
        import re

        lines = content.split("\n")

        project_name = "Untitled"
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("# ") and not stripped.startswith("## "):
                project_name = stripped[2:].strip()
                break

        stories: list[UserStory] = []
        current_story: UserStory | None = None
        desc_lines: list[str] = []
        in_code_block = False
        code_lines: list[str] = []

        heading_pattern = re.compile(r"^(#{2,4})\s+(.+)$")
        checkbox_pattern = re.compile(r"^[-*]\s+\[[ xX]\]\s*(.+)$")
        list_pattern = re.compile(r"^[-*]\s+(.+)$")
        table_separator = re.compile(r"^\|?[\s\-:|]+\|?$")
        bold_pattern = re.compile(r"\*\*(.+?)\*\*")

        def finalize_story():
            nonlocal current_story, desc_lines
            if current_story:
                current_story.description = "\n".join(desc_lines).strip()
                stories.append(current_story)

        for line in lines:
            raw = line.rstrip()
            stripped = raw.strip()

            if stripped.startswith("```"):
                if in_code_block:
                    in_code_block = False
                    if current_story:
                        code_text = "\n".join(code_lines)
                        if code_text.strip():
                            desc_lines.append("\n```\n" + code_text + "\n```")
                    code_lines = []
                else:
                    in_code_block = True
                    code_lines = []
                continue

            if in_code_block:
                code_lines.append(raw)
                continue

            heading_match = heading_pattern.match(stripped)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()

                if level == 2:
                    finalize_story()
                    current_story = UserStory(
                        id=f"US-{len(stories) + 1:03d}",
                        title=title,
                        description="",
                    )
                    desc_lines = []
                elif current_story:
                    bold_matches = bold_pattern.findall(title)
                    if bold_matches:
                        for bm in bold_matches:
                            current_story.acceptance_criteria.append(bm)
                    else:
                        desc_lines.append(f"{'#' * level} {title}")
                continue

            checkbox_match = checkbox_pattern.match(stripped)
            if checkbox_match and current_story:
                criteria = checkbox_match.group(1).strip()
                if criteria:
                    current_story.acceptance_criteria.append(criteria)
                continue

            if stripped.startswith("|") and current_story:
                cells = [c.strip() for c in stripped.strip("|").split("|")]
                if not table_separator.match(stripped):
                    meaningful = [c for c in cells if c and c not in ("-", "--", "---")]
                    if meaningful:
                        if len(meaningful) >= 2 and any(
                            kw in meaningful[0].lower()
                            for kw in ("criteria", "标准", "acceptance", "requirement", "验收")
                        ):
                            for cell in meaningful[1:]:
                                if cell.strip():
                                    current_story.acceptance_criteria.append(cell.strip())
                        else:
                            desc_lines.append("| " + " | ".join(meaningful) + " |")
                continue

            list_match = list_pattern.match(stripped)
            if list_match and current_story:
                item = list_match.group(1).strip()
                bold_in_item = bold_pattern.findall(item)
                if bold_in_item:
                    for bm in bold_in_item:
                        current_story.acceptance_criteria.append(bm)
                elif item and not item.startswith("["):
                    current_story.acceptance_criteria.append(item)
                continue

            if current_story and stripped:
                desc_lines.append(stripped)

        finalize_story()

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
