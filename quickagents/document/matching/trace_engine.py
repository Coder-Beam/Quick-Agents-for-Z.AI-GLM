"""
Trace match engine - Three-level matching orchestrator.

Coordinates convention (L1), keyword (L2), and semantic (L3) matchers,
produces trace matrix, coverage report, and triggers diff analysis.
"""

import logging
from typing import List, Dict, Optional, Callable

from ..models import (
    DocumentResult,
    SourceCodeResult,
    CrossReferenceResult,
    TraceEntry,
)
from .convention_matcher import ConventionMatcher
from .keyword_matcher import KeywordMatcher
from .semantic_matcher import SemanticMatcher
from .diff_analyzer import DiffAnalyzer
from .fix_suggester import FixSuggester
from .synonym_table import SynonymTable

logger = logging.getLogger(__name__)


class TraceMatchEngine:
    """Three-level trace matching engine.

    Matching flow:
        1. Convention matching -> exact, confidence 1.0
        2. Keyword matching -> medium, confidence 0.7-0.9
        3. LLM semantic matching -> remaining, confidence >= 0.6
    """

    def __init__(
        self,
        synonym_table: Optional[SynonymTable] = None,
        llm_func: Optional[Callable] = None,
    ):
        self._synonyms = synonym_table or SynonymTable()
        self._convention = ConventionMatcher()
        self._keyword = KeywordMatcher(self._synonyms)
        self._semantic = SemanticMatcher(llm_func=llm_func)
        self._diff = DiffAnalyzer()
        self._fix = FixSuggester()

    def match(
        self,
        doc_results: List[DocumentResult],
        code_result: SourceCodeResult,
    ) -> CrossReferenceResult:
        logger.info(
            f"Starting trace match: {len(doc_results)} docs, "
            f"{code_result.get_module_count()} modules"
        )

        l1_traces = self._convention.match(doc_results, code_result)
        logger.info(f"L1 convention: {len(l1_traces)} matches")

        l2_traces = self._keyword.match(
            doc_results, code_result, existing_traces=l1_traces
        )
        logger.info(f"L2 keyword: {len(l2_traces)} matches")

        l1_l2 = l1_traces + l2_traces
        l3_traces = self._semantic.match(
            doc_results, code_result, existing_traces=l1_l2
        )
        logger.info(f"L3 semantic: {len(l3_traces)} matches")

        all_traces = l1_l2 + l3_traces
        coverage = self._compute_coverage(doc_results, code_result, all_traces)

        raw_diffs = self._diff.analyze(doc_results, code_result, all_traces)
        diffs = self._fix.suggest(raw_diffs)

        unmatched_reqs = self._get_unmatched_reqs(doc_results, all_traces)
        unmatched_code = self._get_unmatched_code(code_result, all_traces)

        return CrossReferenceResult(
            trace_matrix=all_traces,
            diff_report=diffs,
            coverage_report=coverage,
            unmatched_reqs=unmatched_reqs,
            unmatched_code=unmatched_code,
        )

    def _compute_coverage(
        self,
        doc_results: List[DocumentResult],
        code_result: SourceCodeResult,
        traces: List[TraceEntry],
    ) -> Dict:
        total_reqs = 0
        for doc in doc_results:
            total_reqs += len(doc.sections)
            total_reqs += sum(len(t.rows) for t in doc.tables)

        total_code = sum(len(m.get_all_functions()) for m in code_result.modules)

        covered_reqs = len({t.req_source for t in traces if t.req_source})
        covered_code = len(
            {
                (t.impl_file, t.impl_function)
                for t in traces
                if t.impl_file and t.impl_function
            }
        )

        by_type: Dict[str, int] = {}
        for t in traces:
            by_type[t.trace_type] = by_type.get(t.trace_type, 0) + 1

        return {
            "total_requirements": total_reqs,
            "covered_requirements": covered_reqs,
            "uncovered_requirements": max(0, total_reqs - covered_reqs),
            "rate": covered_reqs / total_reqs if total_reqs > 0 else 0.0,
            "total_code_items": total_code,
            "covered_code": covered_code,
            "uncovered_code": max(0, total_code - covered_code),
            "by_match_type": by_type,
        }

    @staticmethod
    def _get_unmatched_reqs(
        docs: List[DocumentResult], traces: List[TraceEntry]
    ) -> List[str]:
        matched = {t.req_source for t in traces if t.req_source}
        result: List[str] = []
        for doc in docs:
            for sec in doc.sections:
                src = f"{doc.source_file} {sec.title}"
                if src not in matched and sec.title:
                    result.append(src)
        return result

    @staticmethod
    def _get_unmatched_code(
        code_result: SourceCodeResult, traces: List[TraceEntry]
    ) -> List[str]:
        matched = set()
        for t in traces:
            if t.impl_file and t.impl_function:
                matched.add((t.impl_file, t.impl_function))
        result: List[str] = []
        for module in code_result.modules:
            for func in module.get_all_functions():
                if (module.file_path, func.name) not in matched:
                    result.append(f"{module.file_path}:{func.name}")
        return result
