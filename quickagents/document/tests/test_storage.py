"""
Tests for Phase 8: Storage Layer + Knowledge Graph extensions.

Covers:
- T042: Extended NodeType/EdgeType
- T044-T045: KnowledgeSaver (doc + source)
- T046: TraceSaver (trace edges)
- T047: MarkdownExporter
- T048: FTS5 search
- T049: ResultCache
"""

import tempfile
import os

from quickagents.document.models import (
    DocumentResult,
    DocumentSection,
    DocumentTable,
    SourceCodeResult,
    CodeModule,
    CodeFunction,
    CodeClass,
    CrossReferenceResult,
    TraceEntry,
    DiffEntry,
)
from quickagents.document.storage import (
    KnowledgeSaver,
    MarkdownExporter,
    ResultCache,
)
from quickagents.knowledge_graph.types import NodeType, EdgeType
from quickagents.knowledge_graph import KnowledgeGraph


def _make_doc(**kwargs):
    defaults = dict(
        source_file="test.pdf",
        source_format="pdf",
        title="Test Document",
        sections=[],
        paragraphs=["para1"],
        tables=[],
        images=[],
        formulas=[],
        structure_tree={},
        metadata={},
        raw_text="test text",
        errors=[],
    )
    defaults.update(kwargs)
    return DocumentResult(**defaults)


def _make_section(**kwargs):
    defaults = dict(
        section_id="S001",
        title="Test Section",
        level=1,
        page_number=1,
        content="section content",
    )
    defaults.update(kwargs)
    return DocumentSection(**defaults)


def _make_code(**kwargs):
    defaults = dict(
        source_dir="src/",
        languages=["python"],
        modules=[],
        dependencies=[],
        structure_tree={},
        stats={},
        raw_text={},
        errors=[],
    )
    defaults.update(kwargs)
    return SourceCodeResult(**defaults)


def _make_kg():
    tmp = tempfile.mktemp(suffix=".db")
    kg = KnowledgeGraph(db_path=tmp)
    kg._tmp_db = tmp
    return kg


def _cleanup_kg(kg):
    try:
        os.unlink(kg._tmp_db)
    except OSError:
        pass


# ===== T042: Extended NodeType/EdgeType =====


class TestExtendedTypes:
    def test_node_type_document(self):
        assert NodeType.DOCUMENT.value == "document"

    def test_node_type_section(self):
        assert NodeType.SECTION.value == "section"

    def test_node_type_module(self):
        assert NodeType.MODULE.value == "module"

    def test_node_type_function(self):
        assert NodeType.FUNCTION.value == "function"

    def test_edge_type_contains(self):
        assert EdgeType.CONTAINS.value == "contains"

    def test_edge_type_implements(self):
        assert EdgeType.IMPLEMENTS.value == "implements"

    def test_edge_type_calls(self):
        assert EdgeType.CALLS.value == "calls"

    def test_edge_type_extracted_from(self):
        assert EdgeType.EXTRACTED_FROM.value == "extracted_from"

    def test_all_new_node_types_in_enum(self):
        names = {e.name for e in NodeType}
        assert "DOCUMENT" in names
        assert "SECTION" in names
        assert "MODULE" in names
        assert "FUNCTION" in names

    def test_all_new_edge_types_in_enum(self):
        names = {e.name for e in EdgeType}
        assert "CONTAINS" in names
        assert "IMPLEMENTS" in names
        assert "CALLS" in names
        assert "EXTRACTED_FROM" in names


# ===== T044: KnowledgeSaver - Documents =====


class TestKnowledgeSaverDocument:
    def test_save_document_creates_nodes(self):
        kg = _make_kg()
        try:
            saver = KnowledgeSaver(kg)
            doc = _make_doc(title="Requirements")
            ids = saver.save_document(doc)
            assert "_doc" in ids
            node = kg.get_node(ids["_doc"])
            assert node is not None
            assert node.title == "Requirements"
            assert node.node_type == NodeType.DOCUMENT
        finally:
            _cleanup_kg(kg)

    def test_save_sections_as_nodes(self):
        kg = _make_kg()
        try:
            saver = KnowledgeSaver(kg)
            sections = [
                _make_section(section_id="S001", title="Auth", level=1),
                _make_section(
                    section_id="S002", title="Login", level=2, parent_id="S001"
                ),
            ]
            doc = _make_doc(sections=sections)
            ids = saver.save_document(doc)
            assert "S001" in ids
            assert "S002" in ids
        finally:
            _cleanup_kg(kg)

    def test_section_parent_child_edge(self):
        kg = _make_kg()
        try:
            saver = KnowledgeSaver(kg)
            sections = [
                _make_section(section_id="S001", title="Auth", level=1),
                _make_section(
                    section_id="S002", title="Login", level=2, parent_id="S001"
                ),
            ]
            doc = _make_doc(sections=sections)
            ids = saver.save_document(doc)
            edges = kg.get_outgoing_edges(ids["S001"], EdgeType.CONTAINS)
            child_ids = [e.target_node_id for e in edges]
            assert ids["S002"] in child_ids
        finally:
            _cleanup_kg(kg)

    def test_save_tables_as_nodes(self):
        kg = _make_kg()
        try:
            saver = KnowledgeSaver(kg)
            table = DocumentTable(
                table_id="T001",
                page_number=1,
                headers=["ID", "Desc"],
                rows=[["REQ-001", "Auth"]],
            )
            doc = _make_doc(tables=[table])
            ids = saver.save_document(doc)
            assert "_TT001" in ids
        finally:
            _cleanup_kg(kg)


# ===== T045: KnowledgeSaver - Source Code =====


class TestKnowledgeSaverSource:
    def test_save_source_creates_module_nodes(self):
        kg = _make_kg()
        try:
            saver = KnowledgeSaver(kg)
            func = CodeFunction(
                func_id="F001",
                name="login",
                signature="def login():",
                start_line=1,
                end_line=10,
            )
            module = CodeModule(
                module_id="M001",
                file_path="auth.py",
                language="python",
                loc=50,
                functions=[func],
            )
            code = _make_code(modules=[module])
            ids = saver.save_source(code)
            assert "M001" in ids
        finally:
            _cleanup_kg(kg)

    def test_save_functions(self):
        kg = _make_kg()
        try:
            saver = KnowledgeSaver(kg)
            func = CodeFunction(
                func_id="F001",
                name="login",
                signature="def login():",
                start_line=1,
                end_line=10,
                docstring="Login handler",
            )
            module = CodeModule(
                module_id="M001",
                file_path="auth.py",
                language="python",
                loc=50,
                functions=[func],
            )
            code = _make_code(modules=[module])
            ids = saver.save_source(code)
            assert "F001" in ids
            node = kg.get_node(ids["F001"])
            assert node.node_type == NodeType.FUNCTION
        finally:
            _cleanup_kg(kg)

    def test_save_class_with_methods(self):
        kg = _make_kg()
        try:
            saver = KnowledgeSaver(kg)
            method = CodeFunction(
                func_id="F002",
                name="check",
                signature="def check(self):",
                start_line=5,
                end_line=8,
            )
            cls = CodeClass(
                class_id="C001",
                name="Auth",
                methods=[method],
                docstring="Auth class",
            )
            module = CodeModule(
                module_id="M001",
                file_path="auth.py",
                language="python",
                loc=50,
                classes=[cls],
            )
            code = _make_code(modules=[module])
            ids = saver.save_source(code)
            assert "C001" in ids
            assert "F002" in ids
            cls_node = kg.get_node(ids["C001"])
            assert cls_node.title == "Auth"
        finally:
            _cleanup_kg(kg)

    def test_module_contains_function_edge(self):
        kg = _make_kg()
        try:
            saver = KnowledgeSaver(kg)
            func = CodeFunction(
                func_id="F001",
                name="login",
                signature="def login():",
                start_line=1,
                end_line=5,
            )
            module = CodeModule(
                module_id="M001",
                file_path="auth.py",
                language="python",
                loc=10,
                functions=[func],
            )
            code = _make_code(modules=[module])
            ids = saver.save_source(code)
            edges = kg.get_outgoing_edges(ids["M001"], EdgeType.CONTAINS)
            assert len(edges) >= 1
            assert edges[0].target_node_id == ids["F001"]
        finally:
            _cleanup_kg(kg)


# ===== T046: TraceSaver =====


class TestTraceSaver:
    def test_save_traces_creates_edges(self):
        kg = _make_kg()
        try:
            saver = KnowledgeSaver(kg)

            sections = [_make_section(section_id="S001", title="Auth")]
            doc = _make_doc(sections=sections)
            doc_ids = saver.save_document(doc)

            func = CodeFunction(
                func_id="F001",
                name="authenticate",
                signature="def authenticate():",
                start_line=1,
                end_line=5,
            )
            module = CodeModule(
                module_id="M001",
                file_path="auth.py",
                language="python",
                loc=10,
                functions=[func],
            )
            code = _make_code(modules=[module])
            code_ids = saver.save_source(code)

            cross_ref = CrossReferenceResult(
                trace_matrix=[
                    TraceEntry(
                        trace_id="T001",
                        requirement="Auth",
                        req_source="test.pdf Auth",
                        implementation="auth.py:authenticate()",
                        impl_file="auth.py",
                        impl_function="authenticate",
                        trace_type="keyword",
                        confidence=0.9,
                        status="covered",
                    )
                ],
            )
            edge_count = saver.save_traces(cross_ref, doc_ids, code_ids)
            assert edge_count >= 2
        finally:
            _cleanup_kg(kg)


# ===== T047: MarkdownExporter =====


class TestMarkdownExporter:
    def test_export_trace_matrix(self):
        exporter = MarkdownExporter()
        result = CrossReferenceResult(
            trace_matrix=[
                TraceEntry(
                    trace_id="T001",
                    requirement="User auth",
                    req_source="spec.pdf 2.1",
                    impl_file="auth.py",
                    impl_function="login",
                    impl_lines="L10-25",
                    trace_type="keyword",
                    confidence=0.85,
                    status="covered",
                )
            ],
            coverage_report={"by_match_type": {"keyword": 1}},
        )
        md = exporter.export_trace_matrix(result, doc_sources=["spec.pdf"])
        assert "需求追踪矩阵" in md
        assert "T001" in md
        assert "keyword" in md
        assert "spec.pdf" in md

    def test_export_coverage_report(self):
        exporter = MarkdownExporter()
        result = CrossReferenceResult(
            coverage_report={
                "total_requirements": 10,
                "covered_requirements": 7,
                "uncovered_requirements": 3,
                "rate": 0.7,
                "total_code_items": 15,
                "covered_code": 10,
            },
        )
        md = exporter.export_coverage_report(result)
        assert "覆盖率报告" in md
        assert "10" in md
        assert "70.0%" in md

    def test_export_diff_report_gaps(self):
        exporter = MarkdownExporter()
        result = CrossReferenceResult(
            diff_report=[
                DiffEntry(
                    diff_id="DIFF-G001",
                    diff_type="gap",
                    description="Uncovered requirement",
                    req_side="spec.pdf: Password validation",
                    suggestion_by_doc="[以文档为准] Add implementation",
                )
            ],
        )
        md = exporter.export_diff_report(result, base="doc")
        assert "差异报告" in md
        assert "DIFF-G001" in md
        assert "未覆盖的需求" in md

    def test_export_diff_report_extras(self):
        exporter = MarkdownExporter()
        result = CrossReferenceResult(
            diff_report=[
                DiffEntry(
                    diff_id="DIFF-E001",
                    diff_type="extra",
                    description="Undocumented implementation",
                    code_side="auth.py:send_email()",
                    suggestion_by_code="[以代码为准] Remove or document",
                )
            ],
        )
        md = exporter.export_diff_report(result, base="code")
        assert "无文档对应的实现" in md

    def test_export_full_report(self):
        exporter = MarkdownExporter()
        result = CrossReferenceResult(
            trace_matrix=[],
            diff_report=[],
            coverage_report={"total_requirements": 0, "rate": 0.0},
        )
        doc = _make_doc()
        code = _make_code()
        md = exporter.export_full_report(result, doc_results=[doc], code_result=code)
        assert "需求追踪矩阵" in md
        assert "覆盖率报告" in md
        assert "差异报告" in md

    def test_export_empty_diff(self):
        exporter = MarkdownExporter()
        result = CrossReferenceResult(diff_report=[])
        md = exporter.export_diff_report(result)
        assert "无差异" in md


# ===== T048: FTS5 Search =====


class TestFTS5Search:
    def test_fts5_index_exists(self):
        kg = _make_kg()
        try:
            kg.create_node(
                node_type=NodeType.DOCUMENT,
                title="JWT Authentication",
                content="Users authenticate via JWT tokens",
            )
            result = kg.search("JWT")
            assert result.total >= 1
            assert any("JWT" in n.title for n in result.nodes)
        finally:
            _cleanup_kg(kg)

    def test_fts5_search_by_type(self):
        kg = _make_kg()
        try:
            kg.create_node(
                node_type=NodeType.DOCUMENT,
                title="Auth Doc",
                content="Authentication documentation",
            )
            kg.create_node(
                node_type=NodeType.FUNCTION,
                title="authenticate",
                content="JWT authenticate function",
            )
            result = kg.search("auth", node_types=[NodeType.FUNCTION])
            assert all(n.node_type == NodeType.FUNCTION for n in result.nodes)
        finally:
            _cleanup_kg(kg)

    def test_fts5_search_with_tags(self):
        kg = _make_kg()
        try:
            kg.create_node(
                node_type=NodeType.SECTION,
                title="Authentication",
                content="JWT token auth",
                tags=["auth", "security"],
            )
            result = kg.search("security")
            assert result.total >= 1
        finally:
            _cleanup_kg(kg)


# ===== T049: ResultCache =====


class TestResultCache:
    def test_put_and_get(self):
        cache = ResultCache()
        cache.put("key1", {"data": "test"})
        result = cache.get("key1")
        assert result == {"data": "test"}

    def test_get_missing(self):
        cache = ResultCache()
        assert cache.get("nonexistent") is None

    def test_hash_mismatch(self):
        cache = ResultCache()
        cache.put("key1", "data", file_hash="abc123")
        assert cache.get("key1", file_hash="abc123") == "data"
        assert cache.get("key1", file_hash="different") is None

    def test_invalidate(self):
        cache = ResultCache()
        cache.put("key1", "data")
        cache.invalidate("key1")
        assert cache.get("key1") is None

    def test_clear(self):
        cache = ResultCache()
        cache.put("key1", "a")
        cache.put("key2", "b")
        cache.clear()
        assert cache.size() == 0

    def test_has(self):
        cache = ResultCache()
        cache.put("key1", "data")
        assert cache.has("key1")
        assert not cache.has("key2")

    def test_size(self):
        cache = ResultCache()
        cache.put("key1", "a")
        cache.put("key2", "b")
        assert cache.size() == 2

    def test_ttl_expiry(self):
        cache = ResultCache(ttl_seconds=0)
        cache.put("key1", "data")
        import time

        time.sleep(0.01)
        assert cache.get("key1") is None

    def test_eviction(self):
        cache = ResultCache(max_size=2)
        cache.put("key1", "a")
        cache.put("key2", "b")
        cache.put("key3", "c")
        assert cache.size() <= 2
