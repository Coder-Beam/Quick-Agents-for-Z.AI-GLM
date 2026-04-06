"""
SkillAuditor 单元测试

基于 arXiv:2602.14878 的评分标准验证
"""

import pytest
import os
import tempfile
from pathlib import Path

from quickagents.core.skill_auditor import (
    SkillAuditor,
    Component,
    SmellType,
    ComponentScore,
    AuditResult,
    COMPONENT_LABELS,
    SMELL_LABELS,
)


class TestComponentEnum:
    """组件枚举测试"""

    def test_all_components_defined(self):
        assert len(Component) == 6
        expected = {"purpose", "guidelines", "limitations", "params", "length", "examples"}
        actual = {c.value for c in Component}
        assert actual == expected

    def test_all_smells_defined(self):
        assert len(SmellType) == 6


class TestScorePurpose:
    """Purpose组件评分测试"""

    def setup_method(self):
        self.auditor = SkillAuditor()

    def test_empty_purpose_scores_1(self):
        result = self.auditor.audit_content("")
        assert result.scores[Component.PURPOSE].score == 1.0
        assert result.scores[Component.PURPOSE].smell_detected

    def test_minimal_purpose_scores_2(self):
        content = "# My Skill\nA tool."
        result = self.auditor.audit_content(content)
        assert result.scores[Component.PURPOSE].score <= 2.0

    def test_basic_purpose_scores_3(self):
        content = (
            "# My Skill\n"
            "This skill provides automated code review capabilities "
            "for Python projects. It detects common issues."
        )
        result = self.auditor.audit_content(content)
        assert result.scores[Component.PURPOSE].score >= 3.0

    def test_good_purpose_scores_4_plus(self):
        content = (
            "---\ndescription: Automated Python code review that detects anti-patterns and security issues, returns structured reports\n---\n"
            "# Code Review Skill\n\n"
            "This skill provides comprehensive automated code review "
            "for Python projects. It detects common anti-patterns, "
            "security vulnerabilities, and style violations. "
            "Returns a structured report with severity ratings "
            "and actionable fix suggestions. "
            "Triggers automatically on Python file changes in CI pipelines."
        )
        result = self.auditor.audit_content(content)
        assert result.scores[Component.PURPOSE].score >= 4.0

    def test_excellent_purpose_scores_5(self):
        content = (
            "# Code Review Skill\n\n"
            "This skill provides comprehensive automated code review "
            "for Python projects. It detects common anti-patterns, "
            "security vulnerabilities, and style violations. "
            "Returns a structured report with severity ratings "
            "and actionable fix suggestions. "
            "When triggered on a Python file change, it performs "
            "static analysis, pattern matching, and best practice checks. "
            "Executes before each git commit to enforce code quality."
        )
        result = self.auditor.audit_content(content)
        assert result.scores[Component.PURPOSE].score >= 4.5


class TestScoreGuidelines:
    """Guidelines组件评分测试"""

    def setup_method(self):
        self.auditor = SkillAuditor()

    def test_no_guidelines_scores_1(self):
        content = "# My Skill\nSome description."
        result = self.auditor.audit_content(content)
        assert result.scores[Component.GUIDELINES].score == 1.0

    def test_basic_guidelines_scores_3(self):
        content = "# My Skill\n## When to Use\nUse this skill when you need to check Python code quality."
        result = self.auditor.audit_content(content)
        assert result.scores[Component.GUIDELINES].score >= 3.0

    def test_good_guidelines_with_when_not(self):
        content = (
            "# My Skill\n"
            "## When to Use\n"
            "Use this skill when reviewing Python code for security issues. "
            "Suitable for pre-commit checks and CI pipelines.\n\n"
            "## When NOT to Use\n"
            "Don't use for non-Python files. "
            "Avoid using on generated/boilerplate code."
        )
        result = self.auditor.audit_content(content)
        assert result.scores[Component.GUIDELINES].score >= 3.5


class TestScoreLength:
    """Length组件评分测试"""

    def setup_method(self):
        self.auditor = SkillAuditor()

    def test_very_short_scores_low(self):
        content = "# Skill\nShort."
        result = self.auditor.audit_content(content)
        assert result.scores[Component.LENGTH].score < 3.0

    def test_medium_length_scores_3(self):
        content = (
            "# My Skill\n"
            "This is a skill that does something useful. "
            "It helps with code quality. "
            "You should use it regularly."
        )
        result = self.auditor.audit_content(content)
        assert result.scores[Component.LENGTH].score >= 3.0

    def test_long_content_scores_high(self):
        sentences = "This is a detailed description. " * 20
        content = f"# My Skill\n{sentences}"
        result = self.auditor.audit_content(content)
        assert result.scores[Component.LENGTH].score >= 4.0


class TestSmellDetection:
    """气味检测测试"""

    def setup_method(self):
        self.auditor = SkillAuditor()

    def test_minimal_skill_has_multiple_smells(self):
        """最小技能描述应检测到多个气味"""
        content = "# My Skill\nDoes stuff."
        result = self.auditor.audit_content(content)
        assert len(result.smells) >= 3  # 至少purpose, guidelines, limitations
        assert not result.is_smell_free

    def test_perfect_skill_has_no_smells(self):
        """完美的技能描述应无气味"""
        content = (
            "# Comprehensive Code Review\n\n"
            "## Purpose\n"
            "This skill provides comprehensive automated code review "
            "for Python projects. It detects anti-patterns, security vulnerabilities, "
            "and style violations. Returns a structured report with severity ratings. "
            "When triggered on file changes, performs static analysis and pattern matching.\n\n"
            "## When to Use\n"
            "Use when reviewing Python code for quality issues. "
            "Suitable for pre-commit checks and CI pipelines. "
            "Don't use for non-Python files or generated code. "
            "Note: this is not a replacement for human review.\n\n"
            "## Limitations\n"
            "Only supports Python 3.8+. Does not detect runtime errors. "
            "May produce false positives for intentionally unconventional patterns. "
            "Edge case: async generators may trigger false positives.\n\n"
            "## Parameters\n"
            "  `severity_threshold` (str, default='warning'): Minimum severity to report. "
            "Options: 'info', 'warning', 'error', 'critical'.\n"
            "  `include_style` (bool, default=True): Whether to check style issues.\n\n"
            "## Examples\n\n"
            "```python\n"
            "review = review_code('src/main.py')\n"
            "for issue in review.issues:\n"
            "    print(f'{issue.severity}: {issue.message}')\n"
            "```\n\n"
            "This produces a structured report for each file reviewed."
        )
        result = self.auditor.audit_content(content)
        assert result.is_smell_free
        assert len(result.smells) == 0


class TestAuditResult:
    """审计结果测试"""

    def setup_method(self):
        self.auditor = SkillAuditor()

    def test_overall_score_in_range(self):
        result = self.auditor.audit_content("# Skill\nSome content here.")
        assert 1.0 <= result.overall_score <= 5.0

    def test_p_plus_g_score_in_range(self):
        result = self.auditor.audit_content("# Skill\nSome content here.")
        assert 1.0 <= result.p_plus_g_score <= 5.0

    def test_recommendations_generated(self):
        content = "# Skill\nDoes stuff."
        result = self.auditor.audit_content(content)
        assert len(result.recommendations) > 0

    def test_perfect_skill_has_ok_recommendation(self):
        content = (
            "# Comprehensive Review\n\n"
            "## Purpose\n"
            "Provides automated code review for Python. "
            "Detects issues and returns structured reports. "
            "When triggered on changes, performs comprehensive analysis.\n\n"
            "## When to Use\n"
            "Use for Python code review. "
            "Don't use for non-Python files. "
            "Note: not a replacement for human review.\n\n"
            "## Limitations\n"
            "Only Python 3.8+. May have false positives for async code. "
            "Edge cases with metaclasses may not be handled.\n\n"
            "## Parameters\n"
            "  `threshold` (str, default='warning'): Minimum severity.\n\n"
            "## Examples\n"
            "Review is performed automatically on commit."
        )
        result = self.auditor.audit_content(content)
        has_ok = any("[OK]" in r for r in result.recommendations)
        assert has_ok


class TestFileAudit:
    """文件审计测试"""

    def setup_method(self):
        self.auditor = SkillAuditor()

    def test_audit_nonexistent_file_raises(self):
        with pytest.raises(FileNotFoundError):
            self.auditor.audit_file("/nonexistent/SKILL.md")

    def test_audit_real_file(self):
        """审计实际的SKILL.md文件"""
        f = None
        try:
            f = tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8")
            f.write("# Test Skill\nA test skill for testing purposes.\n")
            f.flush()
            f.close()
            result = self.auditor.audit_file(f.name)
            assert isinstance(result, AuditResult)
            assert result.skill_name  # 应有名称
        finally:
            if f and not f.closed:
                f.close()
            if f:
                os.unlink(f.name)

    def test_audit_directory(self):
        """审计目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建技能目录和SKILL.md
            skill_dir = Path(tmpdir) / "my-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "# My Skill\nA good skill.\n## When to Use\nUse when needed.\n",
                encoding="utf-8",
            )
            # 创建非SKILL.md文件（应被忽略）
            (skill_dir / "README.md").write_text("Not a skill", encoding="utf-8")

            results = self.auditor.audit_directory(tmpdir)
            assert len(results) == 1
            assert results[0].skill_name == "my-skill"

    def test_audit_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            results = self.auditor.audit_directory(tmpdir)
            assert len(results) == 0


class TestFormatReport:
    """报告格式化测试"""

    def setup_method(self):
        self.auditor = SkillAuditor()

    def test_format_report(self):
        result = self.auditor.audit_content("# Skill\nBasic content.")
        report = self.auditor.format_report(result)
        assert "[Skill Audit]" in report
        assert "总分:" in report
        assert "P+G得分:" in report

    def test_format_summary_table(self):
        results = [self.auditor.audit_content(f"# Skill {i}\nContent {i}.") for i in range(3)]
        table = self.auditor.format_summary_table(results)
        assert "批量审计报告" in table
        assert "3 个技能" in table


class TestYAMLFrontmatter:
    """YAML frontmatter解析测试"""

    def setup_method(self):
        self.auditor = SkillAuditor()

    def test_extracts_description_from_frontmatter(self):
        content = "---\nname: my-skill\ndescription: A great skill for code review\n---\n# My Skill\nSome more content."
        result = self.auditor.audit_content(content)
        # 应从frontmatter提取到description
        assert result.scores[Component.PURPOSE].score >= 2.0

    def test_no_frontmatter_still_works(self):
        content = "# My Skill\nNo frontmatter here."
        result = self.auditor.audit_content(content)
        assert isinstance(result, AuditResult)


class TestPriorityComponents:
    """优先组件测试"""

    def setup_method(self):
        self.auditor = SkillAuditor()

    def test_priority_sorted_by_weight(self):
        """优先组件应按权重排序"""
        content = "# Skill\nShort."
        result = self.auditor.audit_content(content)
        if len(result.priority_components) >= 2:
            # Purpose (0.25) 应在 Guidelines (0.25) 之后或同级
            first_weight = SkillAuditor.COMPONENT_WEIGHTS[result.priority_components[0]]
            second_weight = SkillAuditor.COMPONENT_WEIGHTS[result.priority_components[1]]
            assert first_weight >= second_weight


class TestWeightSum:
    """权重配置测试"""

    def test_weights_sum_to_one(self):
        total = sum(SkillAuditor.COMPONENT_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001

    def test_purpose_and_guidelines_highest_weight(self):
        """P+G应有最高权重"""
        pg_weight = (
            SkillAuditor.COMPONENT_WEIGHTS[Component.PURPOSE] + SkillAuditor.COMPONENT_WEIGHTS[Component.GUIDELINES]
        )
        assert pg_weight == 0.5  # 总权重的一半
