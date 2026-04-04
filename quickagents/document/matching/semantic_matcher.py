"""
Semantic matcher - Level 3 LLM-based semantic matching.

Only processes unmatched items after Level 1 + Level 2.
Uses LLM to understand semantic relationships between requirements and code.
Confidence threshold: >= 0.6
"""

from typing import List, Dict, Optional, Callable

from ..models import (
    DocumentResult,
    SourceCodeResult,
    TraceEntry,
)
from .synonym_table import SynonymTable


class SemanticMatcher:
    """Level 3: LLM semantic matching for remaining unmatched items."""

    MIN_CONFIDENCE = 0.6

    def __init__(
        self,
        llm_client: Optional[object] = None,
        llm_func: Optional[Callable] = None,
    ):
        self._llm_client = llm_client
        self._llm_func = llm_func
        self._synonyms = SynonymTable()

    def match(
        self,
        doc_results: List[DocumentResult],
        code_result: SourceCodeResult,
        existing_traces: Optional[List[TraceEntry]] = None,
    ) -> List[TraceEntry]:
        matched_reqs = self._get_matched_reqs(existing_traces or [])
        matched_code = self._get_matched_code(existing_traces or [])

        unmatched_reqs = self._get_unmatched_reqs(doc_results, matched_reqs)
        unmatched_code = self._get_unmatched_code(code_result, matched_code)

        if not unmatched_reqs or not unmatched_code:
            return []

        if self._llm_func:
            return self._match_with_llm(
                unmatched_reqs, unmatched_code, len(existing_traces or [])
            )

        return self._match_heuristic(
            unmatched_reqs, unmatched_code, len(existing_traces or [])
        )

    def _match_with_llm(
        self,
        reqs: List[Dict],
        code_items: List[Dict],
        counter_start: int,
    ) -> List[TraceEntry]:
        prompt = self._build_prompt(reqs, code_items)
        try:
            response = self._llm_func(prompt)
            return self._parse_llm_response(response, reqs, code_items, counter_start)
        except Exception:
            return []

    def _build_prompt(self, reqs: List[Dict], code_items: List[Dict]) -> str:
        req_lines = []
        for i, r in enumerate(reqs):
            req_lines.append(f"  R{i}: {r['text'][:200]}")

        code_lines = []
        for i, c in enumerate(code_items):
            desc = c.get("docstring", "")[:100]
            code_lines.append(f"  C{i}: {c['name']} in {c['file']} - {desc}")

        return (
            "Match the following requirements to code functions.\n"
            "For each match, output: R<req_idx> <-> C<code_idx> | confidence(0-1) | reason\n"
            "Only include matches with confidence >= 0.6.\n\n"
            "Requirements:\n"
            + "\n".join(req_lines)
            + "\n\nCode functions:\n"
            + "\n".join(code_lines)
            + "\n\nMatches:"
        )

    def _parse_llm_response(
        self,
        response: str,
        reqs: List[Dict],
        code_items: List[Dict],
        counter_start: int,
    ) -> List[TraceEntry]:
        import re

        entries: List[TraceEntry] = []
        counter = counter_start
        pattern = re.compile(r"R(\d+)\s*<->\s*C(\d+)\s*\|\s*([\d.]+)\s*\|\s*(.+)")

        for line in response.strip().split("\n"):
            m = pattern.search(line)
            if not m:
                continue
            req_idx = int(m.group(1))
            code_idx = int(m.group(2))
            confidence = float(m.group(3))
            m.group(4).strip()

            if confidence < self.MIN_CONFIDENCE:
                continue
            if req_idx >= len(reqs) or code_idx >= len(code_items):
                continue

            req = reqs[req_idx]
            code = code_items[code_idx]
            counter += 1

            entries.append(
                TraceEntry(
                    trace_id=f"TRACE-S{counter:03d}",
                    requirement=req["text"],
                    req_source=req["source"],
                    implementation=f"{code['file']}:{code['name']}",
                    impl_file=code["file"],
                    impl_function=code["name"],
                    impl_lines=code.get("lines", ""),
                    trace_type="semantic",
                    confidence=round(confidence, 2),
                    status="covered",
                )
            )

        return entries

    def _match_heuristic(
        self,
        reqs: List[Dict],
        code_items: List[Dict],
        counter_start: int,
    ) -> List[TraceEntry]:
        entries: List[TraceEntry] = []
        counter = counter_start

        for req in reqs:
            best_score = 0.0
            best_code: Optional[Dict] = None

            req_words = set(w.lower() for w in _split_words(req["text"]))
            for code in code_items:
                code_name = code["name"]
                code_text = code_name + " " + code.get("docstring", "")

                syn_score = 0.0
                for rw in req_words:
                    s = self._synonyms.match_score(rw, code_name)
                    if s > syn_score:
                        syn_score = s

                code_words = set(w.lower() for w in _split_words(code_text))
                if req_words and code_words:
                    overlap = len(req_words & code_words)
                    union = len(req_words | code_words)
                    if union > 0:
                        jaccard = overlap / union
                        syn_score = max(syn_score, jaccard)
                    for rw in req_words:
                        for cw in code_words:
                            if rw.startswith(cw) or cw.startswith(rw):
                                if len(min(rw, cw)) >= 4:
                                    syn_score = max(syn_score, 0.65)

                if syn_score > best_score:
                    best_score = syn_score
                    best_code = code

            if best_score >= self.MIN_CONFIDENCE and best_code:
                counter += 1
                entries.append(
                    TraceEntry(
                        trace_id=f"TRACE-S{counter:03d}",
                        requirement=req["text"],
                        req_source=req["source"],
                        implementation=f"{best_code['file']}:{best_code['name']}",
                        impl_file=best_code["file"],
                        impl_function=best_code["name"],
                        impl_lines=best_code.get("lines", ""),
                        trace_type="semantic",
                        confidence=round(best_score, 2),
                        status="covered",
                    )
                )

        return entries

    @staticmethod
    def _get_matched_reqs(traces: List[TraceEntry]) -> set:
        return {t.req_source for t in traces if t.req_source}

    @staticmethod
    def _get_matched_code(traces: List[TraceEntry]) -> set:
        result: set = set()
        for t in traces:
            if t.impl_file and t.impl_function:
                result.add((t.impl_file, t.impl_function))
        return result

    def _get_unmatched_reqs(
        self, docs: List[DocumentResult], matched: set
    ) -> List[Dict]:
        items: List[Dict] = []
        for doc in docs:
            for sec in doc.sections:
                src = f"{doc.source_file} {sec.title}"
                if src not in matched and sec.title:
                    items.append(
                        {
                            "text": sec.content or sec.title,
                            "source": src,
                        }
                    )
        return items

    def _get_unmatched_code(
        self, code_result: SourceCodeResult, matched: set
    ) -> List[Dict]:
        items: List[Dict] = []
        for module in code_result.modules:
            for func in module.get_all_functions():
                if (module.file_path, func.name) not in matched:
                    items.append(
                        {
                            "file": module.file_path,
                            "name": func.name,
                            "docstring": func.docstring or "",
                            "lines": f"L{func.start_line}-{func.end_line}",
                        }
                    )
        return items


def _split_words(text: str) -> List[str]:
    import re

    cn_blocks = re.findall(r"[\u4e00-\u9fff]{2,}", text)
    en_words = re.findall(r"[a-zA-Z]{2,}", text)
    cn_parts: List[str] = []
    for block in cn_blocks:
        cn_parts.append(block)
        for i in range(len(block) - 1):
            cn_parts.append(block[i : i + 2])
    return cn_parts + en_words
