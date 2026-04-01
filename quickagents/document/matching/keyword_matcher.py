"""
Keyword matcher - Level 2 keyword-based matching.

Matches requirements to code via:
- Direct keyword matching: "用户认证" <-> UserAuth, auth, authentication
- Translation matching: "登录" <-> login, signin, sign_in
- Abbreviation matching: "RBAC" <-> rbac, role_based_access
- Synonym table lookup
"""

import re
from typing import List, Dict, Set, Tuple, Optional

from ..models import (
    DocumentSection,
    DocumentResult,
    SourceCodeResult,
    CodeModule,
    CodeFunction,
    TraceEntry,
)
from .synonym_table import SynonymTable


class KeywordMatcher:
    """Level 2: Keyword-based matching with confidence 0.7-0.9."""

    MIN_KEYWORD_LEN = 2

    def __init__(self, synonym_table: Optional[SynonymTable] = None):
        self._synonyms = synonym_table or SynonymTable()

    def match(
        self,
        doc_results: List[DocumentResult],
        code_result: SourceCodeResult,
        existing_traces: Optional[List[TraceEntry]] = None,
    ) -> List[TraceEntry]:
        matched_req_sources = self._get_matched_req_sources(existing_traces or [])
        matched_impls = self._get_matched_impls(existing_traces or [])

        req_items = self._extract_requirements(doc_results)
        code_items = self._extract_code_items(code_result)

        entries: List[TraceEntry] = []
        counter = len(existing_traces or [])

        for req in req_items:
            if req["source"] in matched_req_sources:
                continue
            best_score = 0.0
            best_code: Optional[Dict] = None
            for code in code_items:
                impl_key = f"{code['file']}:{code['function']}"
                if impl_key in matched_impls:
                    continue
                score = self._compute_score(req, code)
                if score > best_score:
                    best_score = score
                    best_code = code

            if best_score >= 0.7 and best_code:
                counter += 1
                entries.append(TraceEntry(
                    trace_id=f"TRACE-K{counter:03d}",
                    requirement=req["text"],
                    req_source=req["source"],
                    implementation=best_code["label"],
                    impl_file=best_code["file"],
                    impl_function=best_code["function"],
                    impl_lines=best_code["lines"],
                    trace_type="keyword",
                    confidence=round(best_score, 2),
                    status="covered",
                ))

        return entries

    def _extract_requirements(
        self, doc_results: List[DocumentResult]
    ) -> List[Dict]:
        items: List[Dict] = []
        for doc in doc_results:
            for section in doc.sections:
                if not section.title or len(section.title) < self.MIN_KEYWORD_LEN:
                    continue
                items.append({
                    "text": section.content or section.title,
                    "title": section.title,
                    "source": f"{doc.source_file} {section.title}",
                    "keywords": self._tokenize(section.title + " " + (section.content or "")),
                })
            for table in doc.tables:
                for row in table.rows:
                    row_text = " ".join(str(c) for c in row if c)
                    if len(row_text) < self.MIN_KEYWORD_LEN:
                        continue
                    items.append({
                        "text": row_text,
                        "title": row_text[:60],
                        "source": f"{doc.source_file} T:{table.table_id}",
                        "keywords": self._tokenize(row_text),
                    })
        return items

    def _extract_code_items(
        self, code_result: SourceCodeResult
    ) -> List[Dict]:
        items: List[Dict] = []
        for module in code_result.modules:
            for func in module.get_all_functions():
                tokens = self._tokenize_code(func.name, func.docstring)
                items.append({
                    "file": module.file_path,
                    "function": func.name,
                    "label": f"{module.file_path}:{func.name}()",
                    "lines": f"L{func.start_line}-{func.end_line}",
                    "tokens": tokens,
                    "name": func.name,
                    "docstring": func.docstring or "",
                })
            for cls in module.classes:
                cls_tokens = self._tokenize_code(cls.name, cls.docstring)
                items.append({
                    "file": module.file_path,
                    "function": cls.name,
                    "label": f"{module.file_path}:{cls.name}",
                    "lines": "",
                    "tokens": cls_tokens,
                    "name": cls.name,
                    "docstring": cls.docstring or "",
                })
        return items

    def _compute_score(self, req: Dict, code: Dict) -> float:
        score = 0.0
        req_kws = req["keywords"]
        code_tokens = code["tokens"]
        code_name = code["name"]

        if not req_kws:
            return 0.0

        for kw in req_kws:
            if len(kw) < self.MIN_KEYWORD_LEN:
                continue
            syn_score = self._synonyms.match_score(kw, code_name)
            if syn_score > score:
                score = syn_score

            for ct in code_tokens:
                if ct == kw.lower() or kw.lower() in ct or ct in kw.lower():
                    score = max(score, 0.75)
                    break

        docstring_lower = code.get("docstring", "").lower()
        for kw in req_kws:
            if len(kw) >= 3 and kw.lower() in docstring_lower:
                score = max(score, 0.7)
                break

        return score

    def _tokenize(self, text: str) -> List[str]:
        cn_chars = re.findall(r'[\u4e00-\u9fff]{2,}', text)
        en_words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', text)
        cn_bigrams: List[str] = []
        for block in cn_chars:
            if len(block) == 2:
                cn_bigrams.append(block)
            else:
                for i in range(len(block) - 1):
                    cn_bigrams.append(block[i:i + 2])
                for i in range(len(block) - 2):
                    cn_bigrams.append(block[i:i + 3])
        return cn_bigrams + en_words + cn_chars

    @staticmethod
    def _tokenize_code(name: str, docstring: Optional[str]) -> List[str]:
        parts = re.split(r'[_\s]+', name.lower())
        tokens = [p for p in parts if len(p) >= 2]
        if docstring:
            words = re.findall(r'[a-zA-Z]{3,}', docstring.lower())
            tokens.extend(words[:10])
        return tokens

    @staticmethod
    def _get_matched_req_sources(traces: List[TraceEntry]) -> Set[str]:
        return {t.req_source for t in traces if t.req_source}

    @staticmethod
    def _get_matched_impls(traces: List[TraceEntry]) -> Set[str]:
        result: Set[str] = set()
        for t in traces:
            if t.impl_file and t.impl_function:
                result.add(f"{t.impl_file}:{t.impl_function}")
        return result
