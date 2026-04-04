"""
Granularity adjuster - User-level control over trace granularity.

Supports:
- Coarsen (merge): multiple trace entries -> module-level
- Refine (split): one trace entry -> line-level
- Add: manually create trace relationships
- Remove: delete incorrect trace relationships
"""

from typing import List, Dict, Optional

from ..models import TraceEntry, CrossReferenceResult


class GranularityAdjuster:
    """Adjust trace matrix granularity per user request."""

    def coarsen(
        self,
        result: CrossReferenceResult,
        target_file: Optional[str] = None,
    ) -> CrossReferenceResult:
        """Merge trace entries to module-level (one entry per file)."""
        file_groups: Dict[str, List[TraceEntry]] = {}
        for t in result.trace_matrix:
            key = t.impl_file or "unknown"
            if target_file and key != target_file:
                continue
            file_groups.setdefault(key, []).append(t)

        merged: List[TraceEntry] = []
        counter = 0
        for file_path, traces in file_groups.items():
            counter += 1
            reqs = [t.requirement for t in traces if t.requirement]
            req_sources = [t.req_source for t in traces if t.req_source]
            best_conf = max((t.confidence for t in traces), default=0.0)
            merged.append(
                TraceEntry(
                    trace_id=f"TRACE-M{counter:03d}",
                    requirement="; ".join(dict.fromkeys(reqs)),
                    req_source="; ".join(dict.fromkeys(req_sources)),
                    implementation=file_path,
                    impl_file=file_path,
                    impl_function=None,
                    impl_lines=None,
                    trace_type="module_level",
                    confidence=best_conf,
                    status="covered",
                )
            )

        return CrossReferenceResult(
            trace_matrix=merged,
            diff_report=result.diff_report,
            coverage_report=result.coverage_report,
            unmatched_reqs=result.unmatched_reqs,
            unmatched_code=result.unmatched_code,
        )

    def refine(
        self,
        result: CrossReferenceResult,
        trace_id: str,
        sub_entries: List[Dict],
    ) -> CrossReferenceResult:
        """Split one trace entry into multiple sub-entries."""
        new_traces: List[TraceEntry] = []
        counter = len(result.trace_matrix)

        for t in result.trace_matrix:
            if t.trace_id != trace_id:
                new_traces.append(t)
                continue

            for sub in sub_entries:
                counter += 1
                new_traces.append(
                    TraceEntry(
                        trace_id=f"TRACE-R{counter:03d}",
                        requirement=sub.get("requirement", t.requirement),
                        req_source=sub.get("req_source", t.req_source),
                        implementation=sub.get("implementation", t.implementation),
                        impl_file=sub.get("impl_file", t.impl_file),
                        impl_function=sub.get("impl_function", t.impl_function),
                        impl_lines=sub.get("impl_lines", t.impl_lines),
                        trace_type=sub.get("trace_type", t.trace_type),
                        confidence=sub.get("confidence", t.confidence),
                        status=sub.get("status", t.status),
                    )
                )

        return CrossReferenceResult(
            trace_matrix=new_traces,
            diff_report=result.diff_report,
            coverage_report=result.coverage_report,
            unmatched_reqs=result.unmatched_reqs,
            unmatched_code=result.unmatched_code,
        )

    def add_entry(
        self,
        result: CrossReferenceResult,
        req_text: str,
        req_source: str,
        impl_file: str,
        impl_function: str,
        impl_lines: str = "",
        confidence: float = 1.0,
    ) -> CrossReferenceResult:
        """Add a manual trace entry."""
        counter = len(result.trace_matrix) + 1
        new_entry = TraceEntry(
            trace_id=f"TRACE-A{counter:03d}",
            requirement=req_text,
            req_source=req_source,
            implementation=f"{impl_file}:{impl_function}",
            impl_file=impl_file,
            impl_function=impl_function,
            impl_lines=impl_lines,
            trace_type="manual",
            confidence=confidence,
            status="covered",
        )

        return CrossReferenceResult(
            trace_matrix=result.trace_matrix + [new_entry],
            diff_report=result.diff_report,
            coverage_report=result.coverage_report,
            unmatched_reqs=result.unmatched_reqs,
            unmatched_code=result.unmatched_code,
        )

    def remove_entry(
        self,
        result: CrossReferenceResult,
        trace_id: str,
    ) -> CrossReferenceResult:
        """Remove a trace entry by ID."""
        new_traces = [t for t in result.trace_matrix if t.trace_id != trace_id]

        return CrossReferenceResult(
            trace_matrix=new_traces,
            diff_report=result.diff_report,
            coverage_report=result.coverage_report,
            unmatched_reqs=result.unmatched_reqs,
            unmatched_code=result.unmatched_code,
        )
