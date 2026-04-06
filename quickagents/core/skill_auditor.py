"""
SkillAuditor - 技能描述质量评分器

基于 arXiv:2602.14878 论文的6组件评分体系:
- Purpose: 工具/技能的目的和功能描述
- Guidelines: 使用指南和激活条件
- Limitations: 已知限制和边界
- Params: 参数说明
- Length: 长度和完整性
- Examples: 示例

核心发现:
- 97.1%的MCP工具描述至少有一个"气味"(缺陷)
- P+G(Purpose+Guidelines)紧凑变体效果等同甚至优于完整描述
- Examples组件对性能提升不显著(Cochran's Q p>0.20)

设计原则:
- 纯Python规则评分, 0 Token消耗
- 优先完善Purpose+Guidelines(最高ROI)
- 评分标准对标论文5点Likert量表
"""

import logging
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class Component(Enum):
    """评分组件"""

    PURPOSE = "purpose"
    GUIDELINES = "guidelines"
    LIMITATIONS = "limitations"
    PARAMS = "params"
    LENGTH = "length"
    EXAMPLES = "examples"


class SmellType(Enum):
    """气味类型"""

    UNCLEAR_PURPOSE = "unclear_purpose"
    MISSING_GUIDELINES = "missing_guidelines"
    UNSTATED_LIMITATIONS = "unstated_limitations"
    OPAQUE_PARAMS = "opaque_params"
    UNDERSPECIFIED = "underspecified"
    EXEMPLAR_ISSUES = "exemplar_issues"


# 气味→组件映射
SMELL_TO_COMPONENT = {
    SmellType.UNCLEAR_PURPOSE: Component.PURPOSE,
    SmellType.MISSING_GUIDELINES: Component.GUIDELINES,
    SmellType.UNSTATED_LIMITATIONS: Component.LIMITATIONS,
    SmellType.OPAQUE_PARAMS: Component.PARAMS,
    SmellType.UNDERSPECIFIED: Component.LENGTH,
    SmellType.EXEMPLAR_ISSUES: Component.EXAMPLES,
}

# 组件显示名称
COMPONENT_LABELS = {
    Component.PURPOSE: "Purpose (目的)",
    Component.GUIDELINES: "Guidelines (指南)",
    Component.LIMITATIONS: "Limitations (限制)",
    Component.PARAMS: "Params (参数)",
    Component.LENGTH: "Length (完整性)",
    Component.EXAMPLES: "Examples (示例)",
}

SMELL_LABELS = {
    SmellType.UNCLEAR_PURPOSE: "Unclear Purpose (目的不清晰)",
    SmellType.MISSING_GUIDELINES: "Missing Guidelines (缺少使用指南)",
    SmellType.UNSTATED_LIMITATIONS: "Unstated Limitations (未说明限制)",
    SmellType.OPAQUE_PARAMS: "Opaque Params (参数说明不透明)",
    SmellType.UNDERSPECIFIED: "Underspecified (描述不完整)",
    SmellType.EXEMPLAR_ISSUES: "Exemplar Issues (示例问题)",
}


@dataclass
class ComponentScore:
    """单个组件的评分结果"""

    component: Component
    score: float  # 1.0-5.0
    smell_detected: bool
    reasoning: str  # 评分理由


@dataclass
class AuditResult:
    """完整审计结果"""

    skill_path: str
    skill_name: str
    scores: Dict[Component, ComponentScore]
    overall_score: float  # 加权平均分
    smells: List[SmellType]
    is_smell_free: bool
    priority_components: List[Component]  # 需优先完善的组件
    recommendations: List[str]  # 改进建议
    p_plus_g_score: float  # P+G紧凑变体得分


class SkillAuditor:
    """
    技能描述质量评分器

    基于论文6组件评分体系，对SKILL.md文件进行质量审计。
    纯规则评分，不消耗Token。

    使用方式:
        auditor = SkillAuditor()
        result = auditor.audit_file('.opencode/skills/tdd-workflow-skill/SKILL.md')
        print(f"总分: {result.overall_score:.1f}/5.0")
        print(f"气味: {[s.value for s in result.smells]}")
    """

    # 阈值: 低于3分视为"气味"
    SMELL_THRESHOLD = 3.0

    # 权重配置（基于论文ablation结果）
    # P+G效果最好，赋予更高权重
    COMPONENT_WEIGHTS = {
        Component.PURPOSE: 0.25,
        Component.GUIDELINES: 0.25,
        Component.LIMITATIONS: 0.15,
        Component.PARAMS: 0.15,
        Component.LENGTH: 0.10,
        Component.EXAMPLES: 0.10,
    }

    def audit_file(self, file_path: str) -> AuditResult:
        """
        审计单个SKILL.md文件

        Args:
            file_path: SKILL.md文件路径

        Returns:
            AuditResult: 完整审计结果
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        content = path.read_text(encoding="utf-8")
        skill_name = path.parent.name if path.parent.name else path.stem
        return self.audit_content(content, skill_name, str(path))

    def audit_content(self, content: str, skill_name: str = "unknown", skill_path: str = "") -> AuditResult:
        """
        审计技能描述内容

        Args:
            content: SKILL.md文件内容
            skill_name: 技能名称
            skill_path: 文件路径

        Returns:
            AuditResult: 完整审计结果
        """
        # 提取各部分内容
        sections = self._parse_sections(content)

        # 逐组件评分
        scores = {}
        scores[Component.PURPOSE] = self._score_purpose(content, sections)
        scores[Component.GUIDELINES] = self._score_guidelines(content, sections)
        scores[Component.LIMITATIONS] = self._score_limitations(content, sections)
        scores[Component.PARAMS] = self._score_params(content, sections)
        scores[Component.LENGTH] = self._score_length(content)
        scores[Component.EXAMPLES] = self._score_examples(content, sections)

        # 检测气味
        smells = [smell for smell, comp in SMELL_TO_COMPONENT.items() if scores[comp].smell_detected]

        # 加权总分
        overall = sum(scores[comp].score * self.COMPONENT_WEIGHTS[comp] for comp in Component)

        # P+G紧凑变体得分
        p_plus_g = scores[Component.PURPOSE].score * 0.5 + scores[Component.GUIDELINES].score * 0.5

        # 优先完善组件（低于阈值的，按权重排序）
        priority = sorted(
            [comp for comp in Component if scores[comp].smell_detected],
            key=lambda c: self.COMPONENT_WEIGHTS[c],
            reverse=True,
        )

        # 生成改进建议
        recommendations = self._generate_recommendations(scores, smells)

        return AuditResult(
            skill_path=skill_path,
            skill_name=skill_name,
            scores=scores,
            overall_score=overall,
            smells=smells,
            is_smell_free=len(smells) == 0,
            priority_components=priority,
            recommendations=recommendations,
            p_plus_g_score=p_plus_g,
        )

    def audit_directory(self, dir_path: str) -> List[AuditResult]:
        """
        审计目录下所有SKILL.md文件

        Args:
            dir_path: 包含技能子目录的目录

        Returns:
            List[AuditResult]: 所有审计结果
        """
        results = []
        base = Path(dir_path)

        if not base.exists():
            return results

        # 查找 SKILL.md 文件
        for skill_file in base.rglob("SKILL.md"):
            try:
                result = self.audit_file(str(skill_file))
                results.append(result)
            except Exception as e:
                logger.warning("审计失败 %s: %s", skill_file, e)

        return results

    def _parse_sections(self, content: str) -> Dict[str, str]:
        """解析Markdown章节"""
        sections = {}
        current_header = ""
        current_content = []

        for line in content.split("\n"):
            header_match = re.match(r"^#{1,4}\s+(.+)$", line)
            if header_match:
                if current_header:
                    sections[current_header.lower()] = "\n".join(current_content).strip()
                current_header = header_match.group(1).strip()
                current_content = []
            else:
                current_content.append(line)

        # 最后一个section
        if current_header:
            sections[current_header.lower()] = "\n".join(current_content).strip()

        return sections

    def _score_purpose(self, content: str, sections: Dict[str, str]) -> ComponentScore:
        """
        评分Purpose组件

        5: 清晰说明功能、行为和返回数据
        4: 说明功能和行为，有轻微歧义
        3: 基本说明但缺少行为细节
        2: 模糊或不完整的目的说明
        1: 目的不清晰或缺失
        """
        # 查找目的相关内容
        purpose_text = ""
        for key in sections:
            if any(
                kw in key
                for kw in ["purpose", "目的", "overview", "概述", "about", "about this", "description", "description"]
            ):
                purpose_text += sections[key] + "\n"

        # 也检查文件开头（描述部分）
        frontmatter_end = content.find("\n---\n")
        if frontmatter_end == -1:
            frontmatter_end = 0
        else:
            frontmatter_end += 5

        # 提取description字段（YAML frontmatter）
        desc_match = re.search(r"^description:\s*(.+)$", content, re.MULTILINE)
        if desc_match:
            purpose_text = desc_match.group(1).strip() + "\n" + purpose_text

        # 如果没有明确的purpose章节，取第一段
        if not purpose_text.strip():
            lines = content.split("\n")
            for line in lines:
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and not stripped.startswith("---"):
                    purpose_text += stripped + "\n"
                elif purpose_text.strip():
                    break

        text = purpose_text.strip()
        score = 1.0
        reasoning = ""

        if not text or len(text) < 10:
            score = 1.0
            reasoning = "缺少目的描述"
        elif len(text) < 30:
            score = 2.0
            reasoning = f"目的描述过于简短({len(text)}字符)，缺少行为细节"
        elif len(text) < 80:
            # 检查是否包含功能性动词
            has_action = bool(
                re.search(
                    r"(provides|performs|executes|handles|manages|implements|"
                    r"provides|enables|supports|detects|generates|validates|"
                    r"提供|执行|处理|管理|实现|支持|检测|生成|验证)",
                    text,
                    re.IGNORECASE,
                )
            )
            score = 3.0 if has_action else 2.0
            reasoning = f"基本说明({len(text)}字符)，{'有功能描述' if has_action else '缺少功能描述'}"
        elif len(text) < 200:
            has_action = bool(
                re.search(
                    r"(provides|performs|executes|handles|manages|implements|"
                    r"provides|enables|supports|detects|generates|validates|"
                    r"提供|执行|处理|管理|实现|支持|检测|生成|验证)",
                    text,
                    re.IGNORECASE,
                )
            )
            has_output = bool(
                re.search(
                    r"(returns|produces|outputs|results? in|yields|"
                    r"返回|输出|产生|生成)",
                    text,
                    re.IGNORECASE,
                )
            )
            if has_action and has_output:
                score = 4.0
                reasoning = f"说明功能和行为({len(text)}字符)，有轻微遗漏"
            elif has_action:
                score = 3.5
                reasoning = f"有功能描述但缺少输出/结果说明"
            else:
                score = 3.0
                reasoning = f"描述长度足够但缺少功能性描述"
        else:
            has_action = bool(
                re.search(
                    r"(provides|performs|executes|handles|manages|implements|"
                    r"enables|supports|detects|generates|validates|ensures|"
                    r"提供|执行|处理|管理|实现|支持|检测|生成|验证|确保)",
                    text,
                    re.IGNORECASE,
                )
            )
            has_output = bool(
                re.search(
                    r"(returns|produces|outputs|results? in|yields|"
                    r"返回|输出|产生|生成)",
                    text,
                    re.IGNORECASE,
                )
            )
            has_condition = bool(
                re.search(
                    r"(when|if|whenever|for|in case|during|after|before|"
                    r"当|如果|对于|在.*时|在.*后|在.*前)",
                    text,
                    re.IGNORECASE,
                )
            )
            detail_points = sum([has_action, has_output, has_condition])
            if detail_points >= 3:
                score = 5.0
                reasoning = f"清晰说明功能、行为和条件({len(text)}字符)"
            elif detail_points == 2:
                score = 4.5
                reasoning = f"详细描述但缺少部分细节"
            else:
                score = 4.0
                reasoning = f"描述长度充足但功能描述不够具体"

        return ComponentScore(
            component=Component.PURPOSE,
            score=score,
            smell_detected=score < self.SMELL_THRESHOLD,
            reasoning=reasoning,
        )

    def _score_guidelines(self, content: str, sections: Dict[str, str]) -> ComponentScore:
        """
        评分Guidelines组件

        5: 明确说明何时使用/不使用，包含消歧义说明
        4: 说明何时使用，有少量关于何时不使用的指导
        3: 隐含使用上下文但缺少明确边界
        2: 使用上下文不清晰或过于通用
        1: 无使用指南
        """
        guide_text = ""
        for key in sections:
            if any(
                kw in key
                for kw in [
                    "when to use",
                    "usage",
                    "guidelines",
                    "how to use",
                    "何时使用",
                    "使用指南",
                    "使用方式",
                    "用法",
                    "适用场景",
                    "activation",
                    "trigger",
                    "workflow",
                ]
            ):
                guide_text += sections[key] + "\n"

        text = guide_text.strip()
        score = 1.0
        reasoning = ""

        if not text or len(text) < 10:
            score = 1.0
            reasoning = "缺少使用指南"
        elif len(text) < 40:
            score = 2.0
            reasoning = f"使用指南过于简短({len(text)}字符)"
        elif len(text) < 100:
            has_when = bool(re.search(r"(when|use.*for|suitable|appropriate|apply|当|用于|适用)", text, re.IGNORECASE))
            score = 3.0 if has_when else 2.0
            reasoning = f"有基本使用场景({len(text)}字符)"
        elif len(text) < 300:
            has_when = bool(re.search(r"(when|use.*for|suitable|apply)", text, re.IGNORECASE))
            has_when_not = bool(
                re.search(r"(don't|avoid|not suitable|never|do not|不应|避免|不适合)", text, re.IGNORECASE)
            )
            if has_when and has_when_not:
                score = 4.0
                reasoning = f"包含使用和不使用场景({len(text)}字符)"
            elif has_when:
                score = 3.5
                reasoning = f"有使用场景但缺少不使用场景"
            else:
                score = 3.0
                reasoning = f"内容长度足够但缺少明确的使用条件"
        else:
            has_when = bool(re.search(r"(when|use.*for|suitable|apply|当|用于|适用)", text, re.IGNORECASE))
            has_when_not = bool(
                re.search(r"(don't|avoid|not suitable|never|do not|不应|避免|不适合)", text, re.IGNORECASE)
            )
            has_disambig = bool(re.search(r"(note|important|caution|warning|区别|注意|重要|警告)", text, re.IGNORECASE))
            detail = sum([has_when, has_when_not, has_disambig])
            if detail >= 3:
                score = 5.0
                reasoning = f"完整使用指南+消歧义({len(text)}字符)"
            elif detail == 2:
                score = 4.5
                reasoning = f"详细指南但有轻微遗漏"
            else:
                score = 4.0
                reasoning = f"内容丰富但缺少关键指导"

        return ComponentScore(
            component=Component.GUIDELINES,
            score=score,
            smell_detected=score < self.SMELL_THRESHOLD,
            reasoning=reasoning,
        )

    def _score_limitations(self, content: str, sections: Dict[str, str]) -> ComponentScore:
        """
        评分Limitations组件

        5: 清晰说明不返回什么、范围边界和重要约束
        4: 提及主要限制但遗漏部分边界情况
        3: 模糊或不完整的限制说明
        2: 最少或隐含的限制
        1: 无限制说明
        """
        lim_text = ""
        for key in sections:
            if any(
                kw in key
                for kw in [
                    "limitation",
                    "constraint",
                    "caveat",
                    "restriction",
                    "known issue",
                    "gotcha",
                    "边界",
                    "限制",
                    "约束",
                    "注意事项",
                    "已知问题",
                    "陷阱",
                    "不支持",
                ]
            ):
                lim_text += sections[key] + "\n"

        text = lim_text.strip()

        if not text or len(text) < 10:
            return ComponentScore(Component.LIMITATIONS, 1.0, True, "缺少限制说明")

        has_scope = bool(re.search(r"(does not|cannot|won't|only|must|不|不能|仅|必须)", text, re.IGNORECASE))
        has_edge = bool(re.search(r"(edge case|corner case|exception|boundary|边界|异常|特殊)", text, re.IGNORECASE))

        if len(text) < 50:
            score = 2.5 if has_scope else 2.0
            reasoning = f"限制说明过短({len(text)}字符)"
        elif len(text) < 150:
            score = 3.5 if has_scope else 3.0
            reasoning = f"基本限制说明({len(text)}字符)"
        else:
            if has_scope and has_edge:
                score = 4.5
                reasoning = f"详细限制+边界情况({len(text)}字符)"
            elif has_scope:
                score = 4.0
                reasoning = f"有范围限制但缺少边界情况"
            else:
                score = 3.5
                reasoning = f"内容长度足够但缺少具体限制描述"

        return ComponentScore(Component.LIMITATIONS, score, score < self.SMELL_THRESHOLD, reasoning)

    def _score_params(self, content: str, sections: Dict[str, str]) -> ComponentScore:
        """
        评分Params组件

        5: 每个参数有类型、含义、行为效果和必需/默认状态说明
        4: 大部分参数有解释，有少量遗漏
        3: 有基本参数信息但缺少行为影响说明
        2: 参数仅列出无有意义解释
        1: 参数未解释或仅有schema
        """
        param_text = ""
        for key in sections:
            if any(
                kw in key
                for kw in [
                    "parameter",
                    "argument",
                    "input",
                    "param",
                    "配置",
                    "参数",
                    "输入",
                    "option",
                    "选项",
                ]
            ):
                param_text += sections[key] + "\n"

        # 检查是否有参数列表（表格或列表形式）
        has_param_table = bool(re.search(r"\|.+\|.+\|", content))
        has_param_list = bool(re.search(r"^\s*[-*]\s+`?\w+`?\s*[:：]", content, re.MULTILINE))
        has_param_code = bool(re.search(r"```python|```json|```yaml", content))

        text = param_text.strip()

        if not text and not has_param_table and not has_param_list:
            # 检查是否是纯指导性技能（无参数）
            if re.search(r"(no param|no input|no argument|无参数|无输入)", content, re.IGNORECASE):
                return ComponentScore(Component.PARAMS, 5.0, False, "纯指导性技能，无需参数")
            return ComponentScore(Component.PARAMS, 1.0, True, "缺少参数说明")

        indicators = sum([bool(text), has_param_table, has_param_list, has_param_code])

        if indicators <= 1 and len(text) < 50:
            score = 2.0
            reasoning = "参数说明过于简短"
        elif indicators <= 1:
            score = 3.0
            reasoning = "有基本参数信息但缺少详细说明"
        elif indicators == 2:
            score = 3.5
            reasoning = "部分参数有详细说明"
        elif indicators >= 3:
            has_type = bool(
                re.search(r"(type|str|int|bool|float|list|dict|string|类型|字符串|整数|布尔)", text, re.IGNORECASE)
            )
            has_default = bool(re.search(r"(default|optional|required|默认|可选|必需)", text, re.IGNORECASE))
            detail = sum([has_type, has_default])
            score = 4.5 if detail >= 2 else 4.0
            reasoning = f"参数说明详细({'含类型和默认值' if detail >= 2 else '有少量遗漏'})"
        else:
            score = 3.5
            reasoning = "参数说明有格式但不够详细"

        return ComponentScore(Component.PARAMS, score, score < self.SMELL_THRESHOLD, reasoning)

    def _score_length(self, content: str) -> ComponentScore:
        """
        评分Length & Completeness组件

        5: 4+句子结构良好的散文覆盖所有方面
        4: 3-4句良好覆盖
        3: 2-3句基本完整
        2: 1-2句过于简短
        1: 单个短语或片段
        """
        # 去掉frontmatter
        body = content
        fm_match = re.match(r"^---\n.*?\n---\n", content, re.DOTALL)
        if fm_match:
            body = content[fm_match.end() :]

        # 计算有效行数（非空非标题非代码标记）
        effective_lines = [
            line
            for line in body.split("\n")
            if line.strip()
            and not line.strip().startswith("#")
            and not line.strip().startswith("```")
            and not line.strip().startswith("---")
        ]

        # 计算句子数（粗略：以. ! ? 。！？结尾的句子）
        text_content = " ".join(effective_lines)
        sentences = re.split(r"[.!?。！？]\s*", text_content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
        sentence_count = len(sentences)

        if sentence_count < 3:
            score = 1.5 if sentence_count < 1 else 2.0
            reasoning = f"仅{sentence_count}个有效句子，过于简短"
        elif sentence_count < 6:
            score = 3.0
            reasoning = f"{sentence_count}个有效句子，基本完整"
        elif sentence_count < 12:
            score = 4.0
            reasoning = f"{sentence_count}个有效句子，良好覆盖"
        else:
            score = 5.0
            reasoning = f"{sentence_count}个有效句子，结构完整"

        return ComponentScore(Component.LENGTH, score, score < self.SMELL_THRESHOLD, reasoning)

    def _score_examples(self, content: str, sections: Dict[str, str]) -> ComponentScore:
        """
        评分Examples组件

        5: 描述自足；示例补充而非替代说明
        4: 主要是描述，轻微依赖示例
        3: 描述和示例各半
        2: 过度依赖示例，最少散文说明
        1: 仅有示例无描述说明

        注: 论文发现Examples组件不显著影响性能(Cochran's Q p>0.20)
        因此此组件权重较低(0.10)
        """
        has_code_block = bool(re.search(r"```\w*\n", content))
        has_example_header = any(
            any(kw in key for kw in ["example", "示例", "用例", "demo", "sample", "usage example"]) for key in sections
        )
        has_example_keyword = bool(re.search(r"(example|示例|例如|比如|e\.g\.)", content, re.IGNORECASE))

        # 检查是否是纯指导性内容（不需要代码示例）
        is_guideline_skill = bool(
            re.search(r"(workflow|methodology|guideline|process|工作流|方法论|流程|指南)", content[:500], re.IGNORECASE)
        )

        if is_guideline_skill and not has_code_block:
            # 纯方法论技能，示例不是必需的
            if has_example_header or has_example_keyword:
                return ComponentScore(Component.EXAMPLES, 4.5, False, "方法论技能，有使用场景说明")
            return ComponentScore(Component.EXAMPLES, 4.0, False, "方法论技能，示例非必需")

        if not has_code_block and not has_example_header and not has_example_keyword:
            return ComponentScore(Component.EXAMPLES, 1.0, True, "缺少示例")

        if has_code_block and has_example_header:
            # 检查示例是否替代了描述
            code_blocks = re.findall(r"```\w*\n(.*?)```", content, re.DOTALL)
            code_ratio = sum(len(b) for b in code_blocks) / max(len(content), 1)

            if code_ratio > 0.6:
                score = 2.0
                reasoning = f"过度依赖示例({code_ratio:.0%}为代码)，缺少散文说明"
            elif code_ratio > 0.3:
                score = 3.0
                reasoning = f"描述和示例各半({code_ratio:.0%}为代码)"
            else:
                score = 4.5
                reasoning = "示例补充说明而非替代"
        elif has_example_header:
            score = 3.5
            reasoning = "有示例章节但缺少代码示例"
        elif has_code_block:
            score = 3.0
            reasoning = "有代码块但无明确示例章节"
        else:
            score = 2.5
            reasoning = "有示例关键词但缺少具体示例"

        return ComponentScore(Component.EXAMPLES, score, score < self.SMELL_THRESHOLD, reasoning)

    def _generate_recommendations(self, scores: Dict[Component, ComponentScore], smells: List[SmellType]) -> List[str]:
        """生成改进建议"""
        recs = []

        # 按优先级排序（P+G最高优先）
        priority_order = [
            Component.PURPOSE,
            Component.GUIDELINES,
            Component.LIMITATIONS,
            Component.PARAMS,
            Component.LENGTH,
            Component.EXAMPLES,
        ]

        for comp in priority_order:
            sc = scores[comp]
            if sc.smell_detected:
                label = COMPONENT_LABELS[comp]
                if comp == Component.PURPOSE:
                    recs.append(
                        f"[P0] {label} ({sc.score:.1f}/5.0): "
                        "添加1-2句清晰的功能描述，说明该技能做什么、什么时候用、返回什么结果"
                    )
                elif comp == Component.GUIDELINES:
                    recs.append(
                        f"[P0] {label} ({sc.score:.1f}/5.0): "
                        '添加"何时使用"和"何时不使用"的明确指南，帮助Agent正确选择技能'
                    )
                elif comp == Component.LIMITATIONS:
                    recs.append(f"[P1] {label} ({sc.score:.1f}/5.0): 添加已知限制和边界情况说明，避免Agent误用")
                elif comp == Component.PARAMS:
                    recs.append(f"[P1] {label} ({sc.score:.1f}/5.0): 为每个参数添加类型、含义和行为影响的说明")
                elif comp == Component.LENGTH:
                    recs.append(f"[P2] {label} ({sc.score:.1f}/5.0): 扩展描述内容至至少3-4个有效句子")
                elif comp == Component.EXAMPLES:
                    # 论文证明Examples不显著，降级建议
                    recs.append(
                        f"[P3] {label} ({sc.score:.1f}/5.0): (低优先级)添加1-2个使用示例（论文证明此组件影响不显著）"
                    )

        # 如果是smell-free，给出正面反馈
        if not smells:
            recs.append("[OK] 技能描述质量优秀，所有组件均达标")

        return recs

    def format_report(self, result: AuditResult) -> str:
        """格式化审计报告"""
        lines = []
        lines.append(f"{'=' * 60}")
        lines.append(f"[Skill Audit] {result.skill_name}")
        lines.append(f"{'=' * 60}")
        lines.append(f"  文件: {result.skill_path}")
        lines.append(f"  总分: {result.overall_score:.1f}/5.0")
        lines.append(f"  P+G得分: {result.p_plus_g_score:.1f}/5.0 (紧凑变体)")
        lines.append(f"  气味数: {len(result.smells)}")
        lines.append(f"  无缺陷: {'是 ✓' if result.is_smell_free else '否 ✗'}")

        lines.append(f"\n{'─' * 60}")
        lines.append("  组件评分:")
        for comp in Component:
            sc = result.scores[comp]
            bar = "█" * int(sc.score) + "░" * (5 - int(sc.score))
            smell_mark = " ✗" if sc.smell_detected else " ✓"
            label = COMPONENT_LABELS[comp]
            lines.append(f"    {label}: {bar} {sc.score:.1f}{smell_mark}")
            lines.append(f"      {sc.reasoning}")

        if result.smells:
            lines.append(f"\n{'─' * 60}")
            lines.append("  检测到的气味:")
            for smell in result.smells:
                lines.append(f"    - {SMELL_LABELS[smell]}")

        if result.recommendations:
            lines.append(f"\n{'─' * 60}")
            lines.append("  改进建议:")
            for rec in result.recommendations:
                lines.append(f"    {rec}")

        lines.append(f"\n{'=' * 60}")
        return "\n".join(lines)

    def format_summary_table(self, results: List[AuditResult]) -> str:
        """格式化批量审计汇总表"""
        if not results:
            return "[Skill Audit] 未找到任何技能文件"

        lines = []
        lines.append(f"{'=' * 80}")
        lines.append(f"[Skill Audit] 批量审计报告 ({len(results)} 个技能)")
        lines.append(f"{'=' * 80}")

        # 统计
        smell_free = sum(1 for r in results if r.is_smell_free)
        avg_score = sum(r.overall_score for r in results) / len(results)
        avg_pg = sum(r.p_plus_g_score for r in results) / len(results)

        lines.append(f"\n  概要:")
        lines.append(f"    总技能数: {len(results)}")
        lines.append(f"    无缺陷: {smell_free} ({smell_free / len(results) * 100:.0f}%)")
        lines.append(f"    平均总分: {avg_score:.1f}/5.0")
        lines.append(f"    平均P+G: {avg_pg:.1f}/5.0")

        # 气味分布
        smell_counts = {}
        for r in results:
            for smell in r.smells:
                label = SMELL_LABELS[smell]
                smell_counts[label] = smell_counts.get(label, 0) + 1

        if smell_counts:
            lines.append(f"\n  气味分布:")
            for label, count in sorted(smell_counts.items(), key=lambda x: -x[1]):
                pct = count / len(results) * 100
                lines.append(f"    {label}: {count} ({pct:.0f}%)")

        # 按总分排序的技能列表
        lines.append(f"\n{'─' * 80}")
        lines.append(f"  {'技能名称':<30} {'总分':>5} {'P+G':>5} {'气味':>4} {'状态':>6}")
        lines.append(f"  {'-' * 30} {'-' * 5} {'-' * 5} {'-' * 4} {'-' * 6}")

        sorted_results = sorted(results, key=lambda r: r.overall_score)
        for r in sorted_results:
            status = "✓" if r.is_smell_free else "✗"
            name = r.skill_name[:28] if len(r.skill_name) > 28 else r.skill_name
            lines.append(
                f"  {name:<30} {r.overall_score:>5.1f} {r.p_plus_g_score:>5.1f} {len(r.smells):>4} {status:>6}"
            )

        lines.append(f"\n{'=' * 80}")
        return "\n".join(lines)
