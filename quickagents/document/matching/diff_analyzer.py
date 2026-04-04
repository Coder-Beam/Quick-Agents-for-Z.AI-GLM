"""
Diff analyzer - Gap/extra/inconsistency detection.

Compares document requirements against source code to find:
- gap: requirements without implementation
- extra: implementations without documented requirements
- inconsistency: mismatched details between requirement and implementation
"""

from typing import List, Set

from ..models import (
    DocumentResult,
    SourceCodeResult,
    TraceEntry,
    DiffEntry,
)


class DiffAnalyzer:
    """Analyze gaps, extras, and inconsistencies between docs and code."""

    def analyze(
        self,
        doc_results: List[DocumentResult],
        code_result: SourceCodeResult,
        traces: List[TraceEntry],
    ) -> List[DiffEntry]:
        entries: List[DiffEntry] = []
        counter = 0

        gaps = self._find_gaps(doc_results, traces)
        for req_text, source in gaps:
            counter += 1
            entries.append(
                DiffEntry(
                    diff_id=f"DIFF-G{counter:03d}",
                    diff_type="gap",
                    description=f"未覆盖的需求: {req_text[:100]}",
                    req_side=f"{source}: {req_text[:200]}",
                    code_side=None,
                )
            )

        extras = self._find_extras(code_result, traces)
        for impl_file, impl_func, lines in extras:
            counter += 1
            entries.append(
                DiffEntry(
                    diff_id=f"DIFF-E{counter:03d}",
                    diff_type="extra",
                    description=f"无文档对应的实现: {impl_file}:{impl_func}",
                    req_side=None,
                    code_side=f"{impl_file}:{impl_func} {lines}",
                )
            )

        inconsistencies = self._find_inconsistencies(traces)
        for trace, reason in inconsistencies:
            counter += 1
            entries.append(
                DiffEntry(
                    diff_id=f"DIFF-I{counter:03d}",
                    diff_type="inconsistency",
                    description=reason,
                    req_side=trace.requirement,
                    code_side=f"{trace.impl_file}:{trace.impl_function} {trace.impl_lines}",
                )
            )

        return entries

    def _find_gaps(
        self,
        doc_results: List[DocumentResult],
        traces: List[TraceEntry],
    ) -> List[tuple]:
        matched_sources: Set[str] = set()
        for t in traces:
            if t.req_source:
                matched_sources.add(t.req_source)

        gaps: List[tuple] = []
        for doc in doc_results:
            for section in doc.sections:
                if not section.title:
                    continue
                source = f"{doc.source_file} {section.title}"
                if source not in matched_sources:
                    text = section.content or section.title
                    if len(text.strip()) >= 5:
                        gaps.append((text, source))
            for table in doc.tables:
                for row in table.rows:
                    row_text = " ".join(str(c) for c in row if c)
                    if len(row_text.strip()) < 5:
                        continue
                    source = f"{doc.source_file} T:{table.table_id}"
                    if source not in matched_sources:
                        gaps.append((row_text, source))

        return gaps

    def _find_extras(
        self,
        code_result: SourceCodeResult,
        traces: List[TraceEntry],
    ) -> List[tuple]:
        matched_code: Set[tuple] = set()
        for t in traces:
            if t.impl_file and t.impl_function:
                matched_code.add((t.impl_file, t.impl_function))

        extras: List[tuple] = []
        for module in code_result.modules:
            for func in module.get_all_functions():
                key = (module.file_path, func.name)
                if key not in matched_code:
                    if func.name.startswith("_"):
                        continue
                    lines = f"L{func.start_line}-{func.end_line}"
                    extras.append((module.file_path, func.name, lines))

        return extras

    def _find_inconsistencies(self, traces: List[TraceEntry]) -> List[tuple]:
        results: List[tuple] = []
        for t in traces:
            if t.confidence < 0.7 and t.confidence > 0.0:
                results.append(
                    (
                        t,
                        f"低置信度匹配 ({t.confidence:.2f}): "
                        f"'{t.requirement[:50]}' <-> '{t.impl_function}' "
                        f"可能存在不一致",
                    )
                )
        return results
