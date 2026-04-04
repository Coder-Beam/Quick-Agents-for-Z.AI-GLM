"""
Convention matcher - Level 1 structured convention matching.

Matches requirements to code via structured conventions:
- Code comments: # REQ-001, # FEATURE-AUTH, // TODO-002
- Document IDs: "REQ-001 用户认证", "2.1 登录功能"
- Function names: req_001_login(), feature_auth()
- Config flags: feature_flag: "AUTH_LOGIN"
"""

import re
from typing import List, Dict

from ..models import (
    DocumentResult,
    SourceCodeResult,
    CodeModule,
    CodeFunction,
    TraceEntry,
)


class ConventionMatcher:
    """Level 1: Structured convention matching with confidence 1.0."""

    REQ_ID_PATTERN = re.compile(
        r"(?:REQ|FR|NFR|UC|FEATURE|BUG|TODO)[-_]?(\d+(?:\.\d+)*)",
        re.IGNORECASE,
    )
    FEATURE_TAG_PATTERN = re.compile(
        r"(?:FEATURE)[-_]([A-Za-z][A-Za-z0-9_-]*)",
        re.IGNORECASE,
    )
    SECTION_NUMBER_PATTERN = re.compile(r"^(\d+(?:\.\d+)*)\s+")
    TAG_COMMENT_PATTERN = re.compile(
        r"(?:#\s*|//\s*|/\*\s*)(?:REQ|FR|FEATURE|TODO)[-_]?(\w+)",
        re.IGNORECASE,
    )

    def match(
        self,
        doc_results: List[DocumentResult],
        code_result: SourceCodeResult,
    ) -> List[TraceEntry]:
        entries: List[TraceEntry] = []
        counter = 0

        req_map = self._build_req_map(doc_results)
        code_tags = self._extract_code_tags(code_result)

        for tag_key, code_locs in code_tags.items():
            norm_key = self._normalize_tag(tag_key)
            for req_key, req_info in req_map.items():
                norm_req = self._normalize_tag(req_key)
                if norm_key == norm_req or norm_key in norm_req or norm_req in norm_key:
                    for loc in code_locs:
                        counter += 1
                        entries.append(
                            TraceEntry(
                                trace_id=f"TRACE-C{counter:03d}",
                                requirement=req_info["text"],
                                req_source=req_info["source"],
                                implementation=loc["label"],
                                impl_file=loc["file"],
                                impl_function=loc["function"],
                                impl_lines=loc["lines"],
                                trace_type="convention",
                                confidence=1.0,
                                status="covered",
                            )
                        )

        return entries

    def _build_req_map(self, doc_results: List[DocumentResult]) -> Dict[str, Dict]:
        req_map: Dict[str, Dict] = {}
        for doc in doc_results:
            for section in doc.sections:
                title = section.title
                m = self.REQ_ID_PATTERN.search(title)
                if m:
                    tag = m.group(0).upper()
                    req_map[tag] = {
                        "text": section.content or title,
                        "source": f"{doc.source_file} {title}",
                    }
                mf = self.FEATURE_TAG_PATTERN.search(title)
                if mf:
                    tag = mf.group(0).upper()
                    req_map[tag] = {
                        "text": section.content or title,
                        "source": f"{doc.source_file} {title}",
                    }
                m2 = self.SECTION_NUMBER_PATTERN.match(title)
                if m2:
                    sec_num = m2.group(1)
                    req_map[sec_num] = {
                        "text": section.content or title,
                        "source": f"{doc.source_file} {title}",
                    }
            for table in doc.tables:
                for row in table.rows:
                    row_text = " ".join(str(c) for c in row)
                    m3 = self.REQ_ID_PATTERN.search(row_text)
                    if m3:
                        tag = m3.group(0).upper()
                        req_map[tag] = {
                            "text": row_text,
                            "source": f"{doc.source_file} T:{table.table_id}",
                        }
        return req_map

    def _extract_code_tags(
        self, code_result: SourceCodeResult
    ) -> Dict[str, List[Dict]]:
        tags: Dict[str, List[Dict]] = {}
        for module in code_result.modules:
            self._scan_functions(module, tags)
            self._scan_names(module, tags)
        return tags

    def _scan_functions(self, module: CodeModule, tags: Dict[str, List[Dict]]) -> None:
        all_funcs = module.get_all_functions()
        for func in all_funcs:
            if func.docstring:
                for m in self.REQ_ID_PATTERN.finditer(func.docstring):
                    tag = m.group(0).upper()
                    tags.setdefault(tag, []).append(self._make_loc(module, func))
                for mf in self.FEATURE_TAG_PATTERN.finditer(func.docstring):
                    tag = mf.group(0).upper()
                    tags.setdefault(tag, []).append(self._make_loc(module, func))
                for ms in self.SECTION_NUMBER_PATTERN.finditer(func.docstring):
                    sec_num = ms.group(1)
                    tags.setdefault(sec_num, []).append(self._make_loc(module, func))
                for line in func.docstring.split("\n"):
                    line = line.lstrip("#/ *")
                    ms = self.SECTION_NUMBER_PATTERN.match(line.strip())  # type: ignore[assignment]
                    if ms:
                        sec_num = ms.group(1)
                        tags.setdefault(sec_num, []).append(
                            self._make_loc(module, func)
                        )

            name_lower = func.name.lower()
            m = self.REQ_ID_PATTERN.search(name_lower)  # type: ignore[assignment]
            if m:
                tag = m.group(0).upper()
                tags.setdefault(tag, []).append(self._make_loc(module, func))
            mf = self.FEATURE_TAG_PATTERN.search(name_lower)  # type: ignore[assignment]
            if mf:
                tag = mf.group(0).upper()
                tags.setdefault(tag, []).append(self._make_loc(module, func))

    def _scan_names(self, module: CodeModule, tags: Dict[str, List[Dict]]) -> None:
        prefixes = ["req_", "feature_", "handle_", "process_"]
        all_funcs = module.get_all_functions()
        for func in all_funcs:
            name_lower = func.name.lower()
            for prefix in prefixes:
                if name_lower.startswith(prefix):
                    suffix = name_lower[len(prefix) :]
                    tags.setdefault(suffix, []).append(self._make_loc(module, func))
                    tag_upper = (prefix.rstrip("_") + "-" + suffix).upper()
                    tags.setdefault(tag_upper, []).append(self._make_loc(module, func))

    @staticmethod
    def _normalize_tag(tag: str) -> str:
        return re.sub(r"[-_\s]+", "", tag).upper()

    @staticmethod
    def _make_loc(module: CodeModule, func: CodeFunction) -> Dict:
        return {
            "file": module.file_path,
            "function": func.name,
            "label": f"{module.file_path}:{func.name}()",
            "lines": f"L{func.start_line}-{func.end_line}",
        }
