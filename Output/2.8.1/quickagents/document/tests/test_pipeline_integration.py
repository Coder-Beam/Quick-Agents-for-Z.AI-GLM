"""
Tests for Phase 9: Three-layer pipeline integration.

Covers:
- T051: CrossValidator
- T052-T053: KnowledgeExtractor (prompts + extraction)
- T054: LayerDiff (three-layer diff + merge)
- T055: ReviewFlow (user review confirmation)
- T056: Pipeline integration
"""

import pytest

from quickagents.document.models import (
    DocumentResult,
    DocumentSection,
    DocumentTable,
    SourceCodeResult,
    CodeModule,
    CodeFunction,
    RefinedDocumentResult,
    RefinedCodeResult,
    KnowledgeExtractionResult,
)
from quickagents.document.validators import (
    CrossValidator,
    KnowledgeExtractor,
    LayerDiff,
    ReviewFlow,
    ReviewItem,
    ReviewStatus,
)


def _doc(**kwargs):
    defaults = dict(
        source_file="test.pdf",
        source_format="pdf",
        title="Test",
        sections=[],
        paragraphs=["p1"],
        tables=[],
        images=[],
        formulas=[],
        structure_tree={},
        metadata={},
        raw_text="test",
        errors=[],
    )
    defaults.update(kwargs)
    return DocumentResult(**defaults)


def _sec(**kwargs):
    defaults = dict(
        section_id="S001", title="Section", level=1,
        page_number=1, content="content",
    )
    defaults.update(kwargs)
    return DocumentSection(**defaults)


def _code(**kwargs):
    defaults = dict(
        source_dir="src/", languages=["python"],
        modules=[], dependencies=[], structure_tree={},
        stats={}, raw_text={}, errors=[],
    )
    defaults.update(kwargs)
    return SourceCodeResult(**defaults)


def _func(**kwargs):
    defaults = dict(
        func_id="F001", name="authenticate",
        signature="def authenticate():", start_line=1, end_line=10,
        docstring="Authenticate user",
    )
    defaults.update(kwargs)
    return CodeFunction(**defaults)


def _module(**kwargs):
    defaults = dict(
        module_id="M001", file_path="auth.py",
        language="python", loc=50,
    )
    defaults.update(kwargs)
    return CodeModule(**defaults)


# ===== T051: CrossValidator =====

class TestCrossValidator:

    def test_validate_document_basic(self):
        doc = _doc(sections=[_sec(title="Auth")])
        code = _code(modules=[_module(functions=[_func()])])
        validator = CrossValidator()
        result = validator.validate_document(doc, code)
        assert isinstance(result, RefinedDocumentResult)
        assert result.source_file == "test.pdf"
        assert result.confidence >= 0.0

    def test_validate_document_no_code(self):
        doc = _doc(sections=[_sec(title="Auth")])
        validator = CrossValidator()
        result = validator.validate_document(doc)
        assert isinstance(result, RefinedDocumentResult)
        assert result.layer2_notes != ""

    def test_validate_detects_duplicate_sections(self):
        sections = [_sec(section_id="S1", title="Auth"), _sec(section_id="S2", title="Auth")]
        doc = _doc(sections=sections)
        validator = CrossValidator()
        result = validator.validate_document(doc)
        dup_corrections = [c for c in result.corrections if c["type"] == "duplicate_section"]
        assert len(dup_corrections) >= 1

    def test_validate_detects_broken_parent(self):
        sections = [
            _sec(section_id="S1", title="Auth"),
            _sec(section_id="S2", title="Login", parent_id="S999"),
        ]
        doc = _doc(sections=sections)
        validator = CrossValidator()
        result = validator.validate_document(doc)
        broken = [c for c in result.corrections if c["type"] == "broken_parent_ref"]
        assert len(broken) >= 1

    def test_validate_source(self):
        code = _code(modules=[_module(functions=[_func()])])
        docs = [_doc(sections=[_sec(title="Authentication")])]
        validator = CrossValidator()
        result = validator.validate_source(code, docs)
        assert isinstance(result, RefinedCodeResult)
        assert result.confidence >= 0.0

    def test_supplements_code_references(self):
        doc = _doc(sections=[_sec(title="authenticate user", content="login function")])
        code = _code(modules=[_module(functions=[_func(name="authenticate")])])
        validator = CrossValidator()
        result = validator.validate_document(doc, code)
        code_refs = [s for s in result.supplements if s["type"] == "code_reference"]
        assert len(code_refs) >= 1

    def test_confidence_decreases_with_corrections(self):
        sections = [_sec(section_id="S1", title="A"), _sec(section_id="S2", title="A")]
        doc = _doc(sections=sections)
        validator = CrossValidator()
        result = validator.validate_document(doc)
        assert result.confidence < 0.9


# ===== T052-T053: KnowledgeExtractor =====

class TestKnowledgeExtractor:

    def test_extract_requirements(self):
        sections = [
            _sec(title="用户认证", content="系统必须实现JWT认证功能"),
            _sec(title="性能要求", content="响应时间不超过200ms"),
        ]
        doc = _doc(sections=sections)
        extractor = KnowledgeExtractor()
        result = extractor.extract([doc])
        assert result.get_requirement_count() >= 1
        req_types = {r.req_type for r in result.requirements}
        assert "functional" in req_types or "non-functional" in req_types

    def test_extract_from_req_id_table(self):
        table = DocumentTable(
            table_id="T001", page_number=1,
            headers=["ID", "描述"],
            rows=[["REQ-001", "用户认证功能"], ["REQ-002", "权限管理"]],
        )
        doc = _doc(tables=[table])
        extractor = KnowledgeExtractor()
        result = extractor.extract([doc])
        req_ids = {r.req_id for r in result.requirements}
        assert "REQ-001" in req_ids
        assert "REQ-002" in req_ids

    def test_extract_decisions(self):
        sections = [
            _sec(title="技术选型", content="选择JWT作为认证方案，采用RESTful API设计"),
        ]
        doc = _doc(sections=sections)
        extractor = KnowledgeExtractor()
        result = extractor.extract([doc])
        assert result.get_decision_count() >= 1

    def test_extract_facts(self):
        sections = [
            _sec(title="环境", content="版本: Python 3.12, 数据库: PostgreSQL, 端口: 5432"),
        ]
        doc = _doc(sections=sections)
        extractor = KnowledgeExtractor()
        result = extractor.extract([doc])
        assert result.get_fact_count() >= 1

    def test_extract_tech_stack_facts(self):
        sections = [
            _sec(title="架构", content="使用React前端和Django后端，Redis缓存，Docker部署"),
        ]
        doc = _doc(sections=sections)
        extractor = KnowledgeExtractor()
        result = extractor.extract([doc])
        tech_facts = [f for f in result.facts if f.category == "tech_stack"]
        assert len(tech_facts) >= 3

    def test_extract_concepts(self):
        sections = [
            _sec(title="用户管理模块", content="用户注册和登录功能"),
        ]
        doc = _doc(sections=sections)
        extractor = KnowledgeExtractor()
        result = extractor.extract([doc])
        assert len(result.concepts) >= 1

    def test_classify_constraint(self):
        extractor = KnowledgeExtractor()
        t = extractor._classify_requirement("不得超过100次/分钟")
        assert t == "constraint"

    def test_classify_non_functional(self):
        extractor = KnowledgeExtractor()
        t = extractor._classify_requirement("系统响应时间性能要求")
        assert t == "non-functional"

    def test_priority_detection(self):
        extractor = KnowledgeExtractor()
        assert extractor._detect_priority("这是一个高优先级需求") == "high"
        assert extractor._detect_priority("P0 紧急修复") == "high"
        assert extractor._detect_priority("普通需求") is None

    def test_summary(self):
        doc = _doc(sections=[_sec(title="认证", content="必须实现JWT认证")])
        extractor = KnowledgeExtractor()
        result = extractor.extract([doc])
        assert result.summary != ""

    def test_extract_with_code_enrichment(self):
        doc = _doc(sections=[_sec(title="Auth", content="认证功能")])
        code = _code(modules=[_module()])
        extractor = KnowledgeExtractor()
        result = extractor.extract([doc], code)
        src_facts = [f for f in result.facts if f.category == "source_module"]
        assert len(src_facts) >= 1

    def test_extract_empty(self):
        extractor = KnowledgeExtractor()
        result = extractor.extract([_doc()])
        assert result.summary != ""

    def test_deduplication(self):
        sections = [_sec(title="认证", content="REQ-001 必须认证"), _sec(section_id="S2", title="认证2", content="REQ-001 认证功能")]
        doc = _doc(sections=sections)
        extractor = KnowledgeExtractor()
        result = extractor.extract([doc])
        req_ids = [r.req_id for r in result.requirements]
        assert req_ids.count("REQ-001") <= 1


# ===== T054: LayerDiff =====

class TestLayerDiff:

    def test_diff_docs(self):
        l1_docs = [_doc()]
        l2_docs = [RefinedDocumentResult(
            source_file="test.pdf", source_format="pdf", title="Test",
            sections=[], paragraphs=[], tables=[], images=[], formulas=[],
            structure_tree={}, metadata={}, raw_text="", errors=[],
            corrections=[{"type": "test", "msg": "fix"}],
        )]
        differ = LayerDiff()
        result = differ.diff(l1_docs, None, l2_docs, None, None, None)
        assert len(result["doc_changes"]) >= 1

    def test_diff_code(self):
        l1 = _code()
        l2 = RefinedCodeResult(
            source_dir="src/", languages=["python"], modules=[],
            dependencies=[], structure_tree={}, stats={}, raw_text={}, errors=[],
            corrections=[{"type": "test"}],
        )
        differ = LayerDiff()
        result = differ.diff([], l1, [], l2, None, None)
        assert len(result["code_changes"]) >= 1

    def test_merge(self):
        l2_doc = RefinedDocumentResult(
            source_file="test.pdf", source_format="pdf", title="Test",
            sections=[], paragraphs=[], tables=[], images=[], formulas=[],
            structure_tree={}, metadata={}, raw_text="", errors=[],
        )
        differ = LayerDiff()
        merged = differ.merge([l2_doc], None, None, None)
        assert len(merged["documents"]) == 1
        assert merged["conflicts"] == []

    def test_merge_with_conflicts(self):
        l2_doc = RefinedDocumentResult(
            source_file="test.pdf", source_format="pdf", title="Test",
            sections=[], paragraphs=[], tables=[], images=[], formulas=[],
            structure_tree={}, metadata={}, raw_text="", errors=[],
            corrections=[{"type": f"fix_{i}"} for i in range(15)],
        )
        differ = LayerDiff()
        merged = differ.merge([l2_doc], None, None, None)
        conflict_types = [c["type"] for c in merged["conflicts"]]
        assert "high_correction_rate" in conflict_types


# ===== T055: ReviewFlow =====

class TestReviewFlow:

    def test_add_and_get_item(self):
        session = ReviewFlow()
        item = session.add_item("R001", "requirement", "User auth")
        assert item.item_id == "R001"
        assert session.get_item("R001") is not None

    def test_accept_item(self):
        session = ReviewFlow()
        session.add_item("R001", "requirement", "Auth")
        session.get_item("R001").accept("OK")
        assert session.get_item("R001").status == ReviewStatus.ACCEPTED

    def test_reject_item(self):
        session = ReviewFlow()
        session.add_item("R001", "requirement", "Auth")
        session.get_item("R001").reject("Wrong")
        assert session.get_item("R001").status == ReviewStatus.REJECTED

    def test_modify_item(self):
        session = ReviewFlow()
        session.add_item("R001", "requirement", "Old")
        session.get_item("R001").modify("New content")
        assert session.get_item("R001").status == ReviewStatus.MODIFIED
        assert session.get_item("R001").content == "New content"

    def test_accept_all(self):
        session = ReviewFlow()
        session.add_item("R001", "req", "A")
        session.add_item("R002", "req", "B")
        count = session.accept_all()
        assert count == 2
        assert session.is_complete()

    def test_reject_all(self):
        session = ReviewFlow()
        session.add_item("R001", "req", "A")
        session.add_item("R002", "req", "B")
        count = session.reject_all()
        assert count == 2

    def test_auto_accept_high_confidence(self):
        session = ReviewFlow()
        session.add_item("R001", "req", "A", confidence=0.95)
        session.add_item("R002", "req", "B", confidence=0.7)
        count = session.accept_auto(min_confidence=0.9)
        assert count == 1
        assert session.get_item("R001").status == ReviewStatus.ACCEPTED
        assert session.get_item("R002").status == ReviewStatus.PENDING

    def test_get_pending(self):
        session = ReviewFlow()
        session.add_item("R001", "req", "A")
        session.add_item("R002", "req", "B")
        session.get_item("R001").accept()
        assert len(session.get_pending()) == 1

    def test_summary(self):
        session = ReviewFlow()
        session.add_item("R001", "req", "A")
        summary = session.summary()
        assert summary["total"] == 1
        assert summary["pending"] == 1

    def test_get_results(self):
        session = ReviewFlow()
        session.add_item("R001", "req", "A")
        session.add_item("R002", "req", "B")
        session.get_item("R001").accept()
        session.get_item("R002").reject()
        results = session.get_results()
        assert len(results["accepted"]) == 1
        assert len(results["rejected"]) == 1

    def test_item_to_dict(self):
        item = ReviewItem("R001", "requirement", "Auth", "doc.pdf", 0.9)
        d = item.to_dict()
        assert d["item_id"] == "R001"
        assert d["status"] == "pending"
        assert d["confidence"] == 0.9


# ===== T056: Pipeline Integration =====

class TestPipelineIntegration:

    def test_pipeline_cross_validate(self):
        from quickagents.document.pipeline import DocumentPipeline

        pipeline = DocumentPipeline()
        doc = _doc(sections=[_sec(title="Auth")])
        code = _code(modules=[_module(functions=[_func()])])
        result = pipeline.cross_validate(doc, code)
        assert isinstance(result, RefinedDocumentResult)

    def test_pipeline_extract_knowledge(self):
        from quickagents.document.pipeline import DocumentPipeline

        pipeline = DocumentPipeline()
        doc = _doc(sections=[_sec(title="认证", content="必须实现JWT认证")])
        result = pipeline.extract_knowledge([doc])
        assert isinstance(result, KnowledgeExtractionResult)
        assert result.get_requirement_count() >= 1

    def test_full_three_layer_flow(self):
        sections = [
            _sec(section_id="S1", title="REQ-001 用户认证", content="必须实现JWT认证功能"),
            _sec(section_id="S2", title="性能要求", content="响应时间不超过200ms"),
        ]
        doc = _doc(sections=sections, raw_text="REQ-001 用户认证 必须实现JWT认证功能")
        code = _code(modules=[_module(functions=[_func()])])

        validator = CrossValidator()
        refined_doc = validator.validate_document(doc, code)
        assert isinstance(refined_doc, RefinedDocumentResult)

        extractor = KnowledgeExtractor()
        knowledge = extractor.extract([doc], code)
        assert knowledge.get_requirement_count() >= 1

        from quickagents.document.matching import TraceMatchEngine
        engine = TraceMatchEngine()
        cross_ref = engine.match([doc], code)
        assert len(cross_ref.trace_matrix) >= 0

        differ = LayerDiff()
        merged = differ.merge([refined_doc], None, knowledge, cross_ref)
        assert "documents" in merged
        assert merged["knowledge"] is not None
