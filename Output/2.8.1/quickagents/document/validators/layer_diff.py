"""
Three-layer diff and merge logic.

Compares results across all three pipeline layers and produces
a unified output with corrections, supplements, and confidence scores.
"""

import logging
from typing import List, Dict, Optional

from ..models import (
    DocumentResult,
    SourceCodeResult,
    CrossReferenceResult,
    RefinedDocumentResult,
    RefinedCodeResult,
    KnowledgeExtractionResult,
)

logger = logging.getLogger(__name__)


class LayerDiff:
    """Compare results across pipeline layers and merge."""

    def diff(
        self,
        layer1_docs: List[DocumentResult],
        layer1_code: Optional[SourceCodeResult],
        layer2_docs: List[RefinedDocumentResult],
        layer2_code: Optional[RefinedCodeResult],
        layer3: Optional[KnowledgeExtractionResult],
        cross_ref: Optional[CrossReferenceResult],
    ) -> Dict:
        """Three-layer diff: compare L1 → L2 → L3 results."""
        result: Dict = {
            "doc_changes": [],
            "code_changes": [],
            "knowledge_delta": {},
            "cross_ref_delta": {},
            "summary": "",
        }

        result["doc_changes"] = self._diff_docs(layer1_docs, layer2_docs)
        if layer1_code and layer2_code:
            result["code_changes"] = self._diff_code(layer1_code, layer2_code)
        if layer3:
            result["knowledge_delta"] = self._summarize_knowledge(layer3)
        if cross_ref:
            result["cross_ref_delta"] = self._summarize_cross_ref(cross_ref)

        parts = []
        if result["doc_changes"]:
            parts.append(f"{len(result['doc_changes'])} doc changes")
        if result["code_changes"]:
            parts.append(f"{len(result['code_changes'])} code changes")
        if result["knowledge_delta"]:
            parts.append(f"knowledge: {result['knowledge_delta'].get('summary', '')}")
        result["summary"] = "; ".join(parts) if parts else "No changes detected"

        return result

    def merge(
        self,
        layer2_docs: List[RefinedDocumentResult],
        layer2_code: Optional[RefinedCodeResult],
        layer3: Optional[KnowledgeExtractionResult],
        cross_ref: Optional[CrossReferenceResult],
        base: str = "doc",
    ) -> Dict:
        """Merge all layer results into a unified output."""
        merged: Dict = {
            "documents": [],
            "source": None,
            "knowledge": None,
            "cross_reference": None,
            "merge_base": base,
            "conflicts": [],
        }

        for doc in layer2_docs:
            doc_data = doc.to_dict()
            if layer3:
                for req in layer3.requirements:
                    for section in doc.sections:
                        if req.source_section and section.title in req.source_section:
                            doc_data.setdefault("extracted_requirements", []).append(
                                req.to_dict()
                            )
            merged["documents"].append(doc_data)

        if layer2_code:
            code_data = layer2_code.to_dict()
            if cross_ref:
                code_data["trace_count"] = len(cross_ref.trace_matrix)
                code_data["coverage_rate"] = cross_ref.coverage_report.get("rate", 0.0)
            merged["source"] = code_data

        if layer3:
            merged["knowledge"] = layer3.to_dict()

        if cross_ref:
            merged["cross_reference"] = cross_ref.to_dict()

        merged["conflicts"] = self._detect_conflicts(
            layer2_docs, layer2_code, layer3, cross_ref
        )

        return merged

    @staticmethod
    def _diff_docs(
        l1_docs: List[DocumentResult],
        l2_docs: List[RefinedDocumentResult],
    ) -> List[Dict]:
        changes: List[Dict] = []
        l2_by_file = {d.source_file: d for d in l2_docs}

        for l1 in l1_docs:
            l2 = l2_by_file.get(l1.source_file)
            if not l2:
                continue

            if l2.corrections:
                changes.append({
                    "file": l1.source_file,
                    "type": "corrections",
                    "count": len(l2.corrections),
                    "items": l2.corrections,
                })

            if l2.supplements:
                changes.append({
                    "file": l1.source_file,
                    "type": "supplements",
                    "count": len(l2.supplements),
                    "items": l2.supplements,
                })

            if l1.sections != l2.sections:
                l1_ids = {s.section_id for s in l1.sections}
                l2_ids = {s.section_id for s in l2.sections}
                added = l2_ids - l1_ids
                removed = l1_ids - l2_ids
                if added or removed:
                    changes.append({
                        "file": l1.source_file,
                        "type": "section_changes",
                        "added": len(added),
                        "removed": len(removed),
                    })

        return changes

    @staticmethod
    def _diff_code(
        l1_code: SourceCodeResult,
        l2_code: RefinedCodeResult,
    ) -> List[Dict]:
        changes: List[Dict] = []

        if l2_code.corrections:
            changes.append({
                "type": "code_corrections",
                "count": len(l2_code.corrections),
                "items": l2_code.corrections,
            })

        if l2_code.supplements:
            changes.append({
                "type": "code_supplements",
                "count": len(l2_code.supplements),
                "items": l2_code.supplements,
            })

        return changes

    @staticmethod
    def _summarize_knowledge(knowledge: KnowledgeExtractionResult) -> Dict:
        return {
            "requirements": knowledge.get_requirement_count(),
            "decisions": knowledge.get_decision_count(),
            "facts": knowledge.get_fact_count(),
            "concepts": len(knowledge.concepts),
            "summary": repr(knowledge),
        }

    @staticmethod
    def _summarize_cross_ref(cross_ref: CrossReferenceResult) -> Dict:
        return {
            "traces": len(cross_ref.trace_matrix),
            "diffs": len(cross_ref.diff_report),
            "coverage_rate": cross_ref.coverage_report.get("rate", 0.0),
            "unmatched_reqs": len(cross_ref.unmatched_reqs),
            "unmatched_code": len(cross_ref.unmatched_code),
        }

    @staticmethod
    def _detect_conflicts(
        docs: List[RefinedDocumentResult],
        code: Optional[RefinedCodeResult],
        knowledge: Optional[KnowledgeExtractionResult],
        cross_ref: Optional[CrossReferenceResult],
    ) -> List[Dict]:
        conflicts: List[Dict] = []

        if cross_ref:
            for diff_entry in cross_ref.diff_report:
                if diff_entry.diff_type == "inconsistency":
                    conflicts.append({
                        "type": "doc_code_mismatch",
                        "description": diff_entry.description,
                        "req_side": diff_entry.req_side,
                        "code_side": diff_entry.code_side,
                    })

        if docs:
            total_corrections = sum(len(d.corrections) for d in docs)
            if total_corrections > 10:
                conflicts.append({
                    "type": "high_correction_rate",
                    "description": f"{total_corrections} corrections across {len(docs)} docs",
                    "suggestion": "Consider re-parsing with adjusted settings",
                })

        return conflicts
