"""
Knowledge extractors - Extract requirements, decisions, facts from documents.

Uses pattern matching for local extraction and optional LLM for deep analysis.
"""

import re
import logging
from typing import List, Dict, Optional, Callable

from ..models import (
    DocumentResult,
    SourceCodeResult,
    ExtractedRequirement,
    ExtractedDecision,
    ExtractedFact,
    KnowledgeExtractionResult,
)

logger = logging.getLogger(__name__)

REQ_KEYWORDS = {
    "functional": [
        "必须", "需要", "要求", "实现", "功能", "支持", "提供",
        "must", "shall", "should", "required", "implement", "support",
        "enable", "provide", "allow",
    ],
    "non-functional": [
        "性能", "安全", "可靠", "可用", "可扩展", "响应时间",
        "performance", "security", "reliability", "availability",
        "scalability", "latency", "throughput",
    ],
    "constraint": [
        "约束", "限制", "不超过", "至少", "最多", "兼容",
        "constraint", "limit", "maximum", "minimum", "compatible",
        "不大于", "不小于", "不得超过",
    ],
}

DECISION_PATTERNS = [
    re.compile(r'选择\s*(\S+)\s*(?:方案|技术|框架)', re.IGNORECASE),
    re.compile(r'(?:使用|采用|基于)\s*(\S+)(?:\s*(?:作为|进行|实现))', re.IGNORECASE),
    re.compile(r'(?:使用|采用|基于)\s*(\S+)\s*(?:作为|进行|实现)', re.IGNORECASE),
    re.compile(r'(?:decided|choose|selected|adopted)\s+(?:to\s+)?(\S+)', re.IGNORECASE),
]

PRIORITY_MAP = {
    "高": "high", "紧急": "high", "critical": "high", "p0": "high",
    "中": "medium", "normal": "medium", "p1": "medium",
    "低": "low", "minor": "low", "p2": "low",
}

REQ_ID_RE = re.compile(r'(?:REQ|FR|NFR)[-_]?(\d+(?:\.\d+)*)', re.IGNORECASE)


class KnowledgeExtractor:
    """Extract structured knowledge from document analysis results."""

    def __init__(self, llm_func: Optional[Callable] = None):
        self._llm_func = llm_func

    def extract(
        self,
        doc_results: List[DocumentResult],
        code_result: Optional[SourceCodeResult] = None,
    ) -> KnowledgeExtractionResult:
        requirements = self._extract_requirements(doc_results)
        decisions = self._extract_decisions(doc_results)
        facts = self._extract_facts(doc_results)
        concepts = self._extract_concepts(doc_results)

        if code_result:
            self._enrich_with_code(requirements, facts, code_result)

        if self._llm_func:
            llm_result = self._extract_with_llm(doc_results, code_result)
            if llm_result:
                requirements.extend(llm_result.requirements)
                decisions.extend(llm_result.decisions)
                facts.extend(llm_result.facts)
                concepts.extend(llm_result.concepts)

        seen_req = set()
        unique_reqs = []
        for r in requirements:
            if r.req_id not in seen_req:
                seen_req.add(r.req_id)
                unique_reqs.append(r)

        seen_dec = set()
        unique_decs = []
        for d in decisions:
            if d.decision_id not in seen_dec:
                seen_dec.add(d.decision_id)
                unique_decs.append(d)

        seen_fact = set()
        unique_facts = []
        for f in facts:
            if f.content not in seen_fact:
                seen_fact.add(f.content)
                unique_facts.append(f)

        summary = self._generate_summary(unique_reqs, unique_decs, unique_facts)

        return KnowledgeExtractionResult(
            requirements=unique_reqs,
            decisions=unique_decs,
            facts=unique_facts,
            concepts=concepts,
            summary=summary,
            layer3_notes="Extracted via pattern matching" + (" + LLM" if self._llm_func else ""),
        )

    def _extract_requirements(
        self, doc_results: List[DocumentResult]
    ) -> List[ExtractedRequirement]:
        requirements: List[ExtractedRequirement] = []
        counter = 0

        for doc in doc_results:
            for section in doc.sections:
                text = (section.title + " " + (section.content or "")).strip()
                if not text or len(text) < 5:
                    continue

                req_type = self._classify_requirement(text)
                priority = self._detect_priority(text)
                req_id_match = REQ_ID_RE.search(text)

                counter += 1
                req_id = req_id_match.group(0).upper() if req_id_match else f"EXT-REQ-{counter:03d}"

                requirements.append(ExtractedRequirement(
                    req_id=req_id,
                    title=section.title,
                    description=text[:500],
                    req_type=req_type,
                    priority=priority,
                    source_section=f"{doc.source_file} {section.title}",
                    confidence=self._compute_req_confidence(text, req_type),
                ))

            for table in doc.tables:
                for row in table.rows:
                    row_text = " ".join(str(c) for c in row if c)
                    if len(row_text) < 5:
                        continue
                    req_id_match = REQ_ID_RE.search(row_text)
                    if req_id_match:
                        counter += 1
                        requirements.append(ExtractedRequirement(
                            req_id=req_id_match.group(0).upper(),
                            title=row_text[:60],
                            description=row_text,
                            req_type=self._classify_requirement(row_text),
                            priority=self._detect_priority(row_text),
                            source_section=f"{doc.source_file} T:{table.table_id}",
                            confidence=0.85,
                        ))

        return requirements

    def _extract_decisions(
        self, doc_results: List[DocumentResult]
    ) -> List[ExtractedDecision]:
        decisions: List[ExtractedDecision] = []
        counter = 0
        decision_kw = ["选择", "决定", "方案", "采用", "决策", "decide", "choose", "select"]

        for doc in doc_results:
            for section in doc.sections:
                text = (section.title + " " + (section.content or "")).strip()
                has_decision = any(kw in text.lower() for kw in decision_kw)
                if not has_decision:
                    continue

                matched_tech = None
                for pattern in DECISION_PATTERNS:
                    m = pattern.search(text)
                    if m:
                        matched_tech = m.group(1)
                        break

                counter += 1
                decisions.append(ExtractedDecision(
                    decision_id=f"DEC-{counter:03d}",
                    title=section.title,
                    description=text[:300],
                    rationale=matched_tech,
                    alternatives=[],
                    source_section=f"{doc.source_file} {section.title}",
                    confidence=0.8 if matched_tech else 0.6,
                ))

        return decisions

    def _extract_facts(
        self, doc_results: List[DocumentResult]
    ) -> List[ExtractedFact]:
        facts: List[ExtractedFact] = []
        counter = 0
        fact_patterns = [
            re.compile(r'(?:版本|环境|系统|平台)\s*[:：]\s*(\S+)', re.IGNORECASE),
            re.compile(r'(?:接口|API|协议)\s*[:：]\s*(\S+)', re.IGNORECASE),
            re.compile(r'(?:数据库|存储)\s*[:：]\s*(\S+)', re.IGNORECASE),
            re.compile(r'(?:端口|地址|URL)\s*[:：]\s*(\S+)', re.IGNORECASE),
        ]

        for doc in doc_results:
            for section in doc.sections:
                text = section.content or ""
                for pattern in fact_patterns:
                    for m in pattern.finditer(text):
                        counter += 1
                        facts.append(ExtractedFact(
                            fact_id=f"FACT-{counter:03d}",
                            content=m.group(0),
                            category=self._classify_fact(m.group(0)),
                            source_section=f"{doc.source_file} {section.title}",
                            confidence=0.9,
                        ))

                technical_terms = re.findall(
                    r'(?:JWT|OAuth|RBAC|REST|gRPC|GraphQL|MySQL|PostgreSQL|'
                    r'MongoDB|Redis|Docker|Kubernetes|AWS|Azure|GCP|'
                    r'React|Vue|Angular|Spring|Django|Flask|FastAPI)',
                    text, re.IGNORECASE,
                )
                for term in technical_terms:
                    counter += 1
                    facts.append(ExtractedFact(
                        fact_id=f"FACT-{counter:03d}",
                        content=f"技术栈: {term}",
                        category="tech_stack",
                        source_section=f"{doc.source_file} {section.title}",
                        confidence=0.95,
                    ))

        return facts

    def _extract_concepts(
        self, doc_results: List[DocumentResult]
    ) -> List[Dict]:
        concepts: List[Dict] = []
        seen: set = set()
        concept_patterns = [
            re.compile(r'((?:用户|系统|管理|业务|数据|服务)\w*(?:模块|功能|流程|系统|服务))', re.IGNORECASE),
            re.compile(r'((?:User|System|Admin|Service|Data|Business)\w*(?:Module|Function|Flow|System|Service))', re.IGNORECASE),
        ]

        for doc in doc_results:
            for section in doc.sections:
                text = section.title + " " + (section.content or "")
                for pattern in concept_patterns:
                    for m in pattern.finditer(text):
                        concept = m.group(1)
                        if concept not in seen:
                            seen.add(concept)
                            concepts.append({
                                "name": concept,
                                "source": f"{doc.source_file} {section.title}",
                            })

        return concepts

    def _enrich_with_code(
        self,
        requirements: List[ExtractedRequirement],
        facts: List[ExtractedFact],
        code: SourceCodeResult,
    ) -> None:
        for module in code.modules:
            facts.append(ExtractedFact(
                fact_id=f"FACT-SRC-{module.file_path}",
                content=f"源码模块: {module.file_path} ({module.language}, {module.loc} LOC)",
                category="source_module",
                source_section=module.file_path,
                confidence=1.0,
            ))

    def _extract_with_llm(
        self,
        doc_results: List[DocumentResult],
        code_result: Optional[SourceCodeResult],
    ) -> Optional[KnowledgeExtractionResult]:
        doc_text = "\n".join(
            f"[{doc.source_file}]\n" + doc.raw_text[:2000]
            for doc in doc_results
        )
        prompt = (
            "从以下文档中提取需求、决策和事实。\n"
            "输出JSON格式:\n"
            '{"requirements": [{req_id, title, description, req_type, priority}],'
            ' "decisions": [{decision_id, title, description, rationale}],'
            ' "facts": [{fact_id, content, category}]}\n\n'
            f"文档内容:\n{doc_text[:4000]}\n\nJSON输出:"
        )
        try:
            response = self._llm_func(prompt)
            return self._parse_llm_json(response)
        except Exception as e:
            logger.warning(f"LLM extraction failed: {e}")
            return None

    def _parse_llm_json(self, response: str) -> Optional[KnowledgeExtractionResult]:
        import json
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start < 0 or end <= start:
                return None
            data = json.loads(response[start:end])
            reqs = [
                ExtractedRequirement(
                    req_id=r.get("req_id", f"LLM-{i}"),
                    title=r.get("title", ""),
                    description=r.get("description", ""),
                    req_type=r.get("req_type", "functional"),
                    priority=r.get("priority"),
                    confidence=0.7,
                )
                for i, r in enumerate(data.get("requirements", []))
            ]
            decs = [
                ExtractedDecision(
                    decision_id=d.get("decision_id", f"LLM-D{i}"),
                    title=d.get("title", ""),
                    description=d.get("description", ""),
                    rationale=d.get("rationale"),
                    confidence=0.7,
                )
                for i, d in enumerate(data.get("decisions", []))
            ]
            fcts = [
                ExtractedFact(
                    fact_id=f.get("fact_id", f"LLM-F{i}"),
                    content=f.get("content", ""),
                    category=f.get("category", ""),
                    confidence=0.7,
                )
                for i, f in enumerate(data.get("facts", []))
            ]
            return KnowledgeExtractionResult(
                requirements=reqs,
                decisions=decs,
                facts=fcts,
            )
        except (json.JSONDecodeError, KeyError):
            return None

    @staticmethod
    def _generate_summary(
        reqs: List[ExtractedRequirement],
        decs: List[ExtractedDecision],
        facts: List[ExtractedFact],
    ) -> str:
        parts = []
        if reqs:
            by_type: Dict[str, int] = {}
            for r in reqs:
                by_type[r.req_type] = by_type.get(r.req_type, 0) + 1
            type_str = ", ".join(f"{k}: {v}" for k, v in by_type.items())
            parts.append(f"提取 {len(reqs)} 个需求 ({type_str})")
        if decs:
            parts.append(f"提取 {len(decs)} 个决策")
        if facts:
            parts.append(f"提取 {len(facts)} 个事实")
        return "。".join(parts) if parts else "未提取到知识"

    @staticmethod
    def _classify_requirement(text: str) -> str:
        text_lower = text.lower()
        for kw in REQ_KEYWORDS["constraint"]:
            if kw in text_lower:
                return "constraint"
        for kw in REQ_KEYWORDS["non-functional"]:
            if kw in text_lower:
                return "non-functional"
        for kw in REQ_KEYWORDS["functional"]:
            if kw in text_lower:
                return "functional"
        return "functional"

    @staticmethod
    def _detect_priority(text: str) -> Optional[str]:
        text_lower = text.lower()
        for kw, pri in PRIORITY_MAP.items():
            if kw in text_lower:
                return pri
        return None

    @staticmethod
    def _compute_req_confidence(text: str, req_type: str) -> float:
        score = 0.5
        if req_type == "functional":
            score += 0.1
        kws = REQ_KEYWORDS.get(req_type, [])
        text_lower = text.lower()
        for kw in kws:
            if kw in text_lower:
                score += 0.05
        return min(score, 1.0)

    @staticmethod
    def _classify_fact(text: str) -> str:
        text_lower = text.lower()
        if any(kw in text_lower for kw in ["版本", "环境", "系统", "version", "environment"]):
            return "environment"
        if any(kw in text_lower for kw in ["接口", "api", "协议", "protocol"]):
            return "api"
        if any(kw in text_lower for kw in ["数据库", "存储", "database", "storage"]):
            return "database"
        if any(kw in text_lower for kw in ["端口", "地址", "url", "port"]):
            return "network"
        return "general"
