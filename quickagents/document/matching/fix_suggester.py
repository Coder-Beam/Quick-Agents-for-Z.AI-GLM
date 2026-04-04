"""
Fix suggester - Generate correction suggestions for diffs.

Produces actionable suggestions for each diff entry,
with both "by doc" and "by code" perspectives.
"""

from typing import List

from ..models import DiffEntry


class FixSuggester:
    """Generate fix suggestions for diff entries."""

    def suggest(self, diffs: List[DiffEntry]) -> List[DiffEntry]:
        enriched: List[DiffEntry] = []
        for diff in diffs:
            suggestion_by_doc = diff.suggestion_by_doc
            suggestion_by_code = diff.suggestion_by_code

            if diff.diff_type == "gap":
                suggestion_by_doc = self._suggest_for_gap_by_doc(diff)
                suggestion_by_code = self._suggest_for_gap_by_code(diff)
            elif diff.diff_type == "extra":
                suggestion_by_doc = self._suggest_for_extra_by_doc(diff)
                suggestion_by_code = self._suggest_for_extra_by_code(diff)
            elif diff.diff_type == "inconsistency":
                suggestion_by_doc = self._suggest_for_inconsistency_by_doc(diff)
                suggestion_by_code = self._suggest_for_inconsistency_by_code(diff)

            enriched.append(
                DiffEntry(
                    diff_id=diff.diff_id,
                    diff_type=diff.diff_type,
                    description=diff.description,
                    req_side=diff.req_side,
                    code_side=diff.code_side,
                    suggestion_by_code=suggestion_by_code,
                    suggestion_by_doc=suggestion_by_doc,
                )
            )
        return enriched

    @staticmethod
    def _suggest_for_gap_by_doc(diff: DiffEntry) -> str:
        req_text = diff.req_side or ""
        return (
            f"[以文档为准] 需求未被实现，建议新增代码: {req_text[:100]}\n"
            f"  -> 分析需求描述，在相应模块中创建实现函数"
        )

    @staticmethod
    def _suggest_for_gap_by_code(diff: DiffEntry) -> str:
        return (
            "[以代码为准] 该需求描述无对应实现，可能是:\n"
            "  1. 需求已过时，建议从文档中移除\n"
            "  2. 需求已被合并到其他功能中"
        )

    @staticmethod
    def _suggest_for_extra_by_doc(diff: DiffEntry) -> str:
        code_desc = diff.code_side or ""
        return (
            f"[以文档为准] 代码无文档对应，建议补充文档:\n"
            f"  -> 在需求文档中添加 {code_desc[:60]} 的需求描述"
        )

    @staticmethod
    def _suggest_for_extra_by_code(diff: DiffEntry) -> str:
        code_desc = diff.code_side or ""
        return (
            f"[以代码为准] 该实现可能是实现细节或已废弃:\n"
            f"  1. 如为必要功能，补充对应需求文档\n"
            f"  2. 如为内部实现，标记为实现细节\n"
            f"  3. 如为废弃代码，考虑移除: {code_desc[:60]}"
        )

    @staticmethod
    def _suggest_for_inconsistency_by_doc(diff: DiffEntry) -> str:
        return (
            f"[以文档为准] 代码实现与需求描述不一致，建议修改代码:\n"
            f"  -> 对照需求 '{diff.req_side[:50] if diff.req_side else ''}' 调整实现"
        )

    @staticmethod
    def _suggest_for_inconsistency_by_code(diff: DiffEntry) -> str:
        return (
            f"[以代码为准] 文档描述与代码实现不一致，建议更新文档:\n"
            f"  -> 根据代码 '{diff.code_side[:50] if diff.code_side else ''}' 更新需求描述"
        )
