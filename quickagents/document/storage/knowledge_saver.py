"""
Knowledge Saver - Save document and source analysis results to Knowledge Graph.

Converts DocumentResult and SourceCodeResult into KnowledgeGraph nodes and edges.
"""

import logging
from typing import Dict, Optional

from ..models import (
    DocumentResult,
    DocumentTable,
    SourceCodeResult,
    CrossReferenceResult,
    TraceEntry,
)

logger = logging.getLogger(__name__)


class KnowledgeSaver:
    """Save document/source analysis results into Knowledge Graph."""

    def __init__(self, kg):
        self._kg = kg

    def save_document(self, doc: DocumentResult) -> Dict[str, str]:
        """Save DocumentResult → KG nodes+edges. Returns node_id map."""
        ids: Dict[str, str] = {}
        doc_node = self._kg.create_node(
            node_type=self._node_type("DOCUMENT"),
            title=doc.title or doc.source_file,
            content=doc.raw_text[:500] if doc.raw_text else "",
            source_uri=doc.source_file,
            tags=[doc.source_format, "document"],
        )
        ids["_doc"] = doc_node.id

        for section in doc.sections:
            sec_node = self._kg.create_node(
                node_type=self._node_type("SECTION"),
                title=section.title,
                content=section.content or "",
                source_uri=f"{doc.source_file}#S{section.section_id}",
                tags=["section", f"level-{section.level}"],
            )
            ids[section.section_id] = sec_node.id
            self._kg.create_edge(
                source_id=doc_node.id,
                target_id=sec_node.id,
                edge_type=self._edge_type("CONTAINS"),
            )
            if section.parent_id and section.parent_id in ids:
                self._kg.create_edge(
                    source_id=ids[section.parent_id],
                    target_id=sec_node.id,
                    edge_type=self._edge_type("CONTAINS"),
                )

        for table in doc.tables:
            tbl_content = self._table_to_text(table)
            tbl_node = self._kg.create_node(
                node_type=self._node_type("SECTION"),
                title=f"Table {table.table_id}",
                content=tbl_content,
                source_uri=f"{doc.source_file}#T{table.table_id}",
                tags=["table"],
            )
            ids[f"_T{table.table_id}"] = tbl_node.id
            self._kg.create_edge(
                source_id=doc_node.id,
                target_id=tbl_node.id,
                edge_type=self._edge_type("CONTAINS"),
            )

        logger.info(
            f"Saved document {doc.source_file}: "
            f"{len(ids)} nodes ({len(doc.sections)} sections, {len(doc.tables)} tables)"
        )
        return ids

    def save_source(self, code: SourceCodeResult) -> Dict[str, str]:
        """Save SourceCodeResult → KG nodes+edges. Returns node_id map."""
        ids: Dict[str, str] = {}

        for module in code.modules:
            mod_node = self._kg.create_node(
                node_type=self._node_type("MODULE"),
                title=module.file_path,
                content=module.module_docstring or "",
                source_uri=module.file_path,
                tags=["module", module.language],
            )
            ids[module.module_id] = mod_node.id

            for cls in module.classes:
                cls_content = cls.docstring or f"class {cls.name}"
                cls_node = self._kg.create_node(
                    node_type=self._node_type("SECTION"),
                    title=cls.name,
                    content=cls_content,
                    source_uri=f"{module.file_path}#C{cls.class_id}",
                    tags=["class"],
                )
                ids[cls.class_id] = cls_node.id
                self._kg.create_edge(
                    source_id=mod_node.id,
                    target_id=cls_node.id,
                    edge_type=self._edge_type("CONTAINS"),
                )

                for method in cls.methods:
                    m_node = self._kg.create_node(
                        node_type=self._node_type("FUNCTION"),
                        title=method.name,
                        content=method.docstring or method.signature,
                        source_uri=f"{module.file_path}#L{method.start_line}",
                        tags=["method"],
                    )
                    ids[method.func_id] = m_node.id
                    self._kg.create_edge(
                        source_id=cls_node.id,
                        target_id=m_node.id,
                        edge_type=self._edge_type("CONTAINS"),
                    )

            for func in module.functions:
                f_node = self._kg.create_node(
                    node_type=self._node_type("FUNCTION"),
                    title=func.name,
                    content=func.docstring or func.signature,
                    source_uri=f"{module.file_path}#L{func.start_line}",
                    tags=["function"],
                )
                ids[func.func_id] = f_node.id
                self._kg.create_edge(
                    source_id=mod_node.id,
                    target_id=f_node.id,
                    edge_type=self._edge_type("CONTAINS"),
                )

        logger.info(
            f"Saved source {code.source_dir}: "
            f"{len(ids)} nodes ({code.get_module_count()} modules)"
        )
        return ids

    def save_traces(
        self,
        cross_ref: CrossReferenceResult,
        doc_ids: Dict[str, str],
        code_ids: Dict[str, str],
    ) -> int:
        """Save CrossReferenceResult trace entries → KG edges."""
        edge_count = 0
        for trace in cross_ref.trace_matrix:
            source_id = self._find_trace_source(trace, doc_ids)
            target_id = self._find_trace_target(trace, code_ids)
            if source_id and target_id:
                self._kg.create_edge(
                    source_id=source_id,
                    target_id=target_id,
                    edge_type=self._edge_type("MAPS_TO"),
                    weight=trace.confidence,
                    evidence=trace.trace_type,
                )
                self._kg.create_edge(
                    source_id=target_id,
                    target_id=source_id,
                    edge_type=self._edge_type("IMPLEMENTS"),
                    weight=trace.confidence,
                    evidence=trace.trace_type,
                )
                edge_count += 2
        logger.info(f"Saved {edge_count} trace edges")
        return edge_count

    @staticmethod
    def _find_trace_source(trace: TraceEntry, doc_ids: Dict[str, str]) -> Optional[str]:
        if trace.req_node_id and trace.req_node_id in doc_ids:
            return doc_ids[trace.req_node_id]
        return doc_ids.get("_doc")

    @staticmethod
    def _find_trace_target(
        trace: TraceEntry, code_ids: Dict[str, str]
    ) -> Optional[str]:
        if trace.impl_node_id and trace.impl_node_id in code_ids:
            return code_ids[trace.impl_node_id]
        for nid, kid in code_ids.items():
            if nid.startswith("F") or nid.startswith("C"):
                continue
            return kid
        return None

    @staticmethod
    def _table_to_text(table: DocumentTable) -> str:
        header = " | ".join(table.headers)
        sep = " | ".join("---" for _ in table.headers)
        rows = []
        for row in table.rows:
            rows.append(" | ".join(str(c) for c in row))
        return f"{header}\n{sep}\n" + "\n".join(rows)

    @staticmethod
    def _node_type(name: str):
        from quickagents.knowledge_graph.types import NodeType

        return NodeType(name.lower())

    @staticmethod
    def _edge_type(name: str):
        from quickagents.knowledge_graph.types import EdgeType

        return EdgeType(name.lower())
