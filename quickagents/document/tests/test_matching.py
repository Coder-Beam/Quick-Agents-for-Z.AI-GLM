"""
Tests for Phase 7: Joint Analysis Engine (matching module).

Tests cover:
- T034: TraceMatchEngine framework
- T035: Convention matcher (L1)
- T036: Keyword matcher + synonym table (L2)
- T037: Semantic matcher (L3)
- T038: Diff analyzer
- T039: Fix suggester
- T040: Granularity adjuster
"""

from quickagents.document.models import (
    DocumentResult,
    DocumentSection,
    DocumentTable,
    SourceCodeResult,
    CodeModule,
    CodeFunction,
    CodeClass,
    TraceEntry,
    DiffEntry,
    CrossReferenceResult,
)
from quickagents.document.matching import (
    TraceMatchEngine,
    ConventionMatcher,
    KeywordMatcher,
    SemanticMatcher,
    DiffAnalyzer,
    FixSuggester,
    GranularityAdjuster,
    SynonymTable,
)


def _make_doc_result(
    title="Test Doc",
    sections=None,
    tables=None,
    source_file="test.pdf",
) -> DocumentResult:
    return DocumentResult(
        source_file=source_file,
        source_format="pdf",
        title=title,
        sections=sections or [],
        paragraphs=["test paragraph"],
        tables=tables or [],
        images=[],
        formulas=[],
        structure_tree={},
        metadata={},
        raw_text="test raw text",
        errors=[],
    )


def _make_section(
    sid="S001",
    title="Section",
    level=1,
    content="",
    page=1,
    parent_id=None,
) -> DocumentSection:
    return DocumentSection(
        section_id=sid,
        title=title,
        level=level,
        page_number=page,
        content=content,
        parent_id=parent_id,
    )


def _make_code_result(
    modules=None,
    source_dir="src/",
) -> SourceCodeResult:
    return SourceCodeResult(
        source_dir=source_dir,
        languages=["python"],
        modules=modules or [],
        dependencies=[],
        structure_tree={},
        stats={},
        raw_text={},
        errors=[],
    )


def _make_module(
    mid="M001",
    path="auth.py",
    functions=None,
    classes=None,
) -> CodeModule:
    return CodeModule(
        module_id=mid,
        file_path=path,
        language="python",
        loc=50,
        functions=functions or [],
        classes=classes or [],
    )


def _make_func(
    fid="F001",
    name="test_func",
    start=1,
    end=10,
    docstring=None,
) -> CodeFunction:
    return CodeFunction(
        func_id=fid,
        name=name,
        signature=f"def {name}():",
        start_line=start,
        end_line=end,
        docstring=docstring,
    )


def _make_class(
    cid="C001",
    name="TestClass",
    methods=None,
    docstring=None,
) -> CodeClass:
    return CodeClass(
        class_id=cid,
        name=name,
        methods=methods or [],
        docstring=docstring,
    )


# ===== SynonymTable Tests =====


class TestSynonymTable:
    def test_lookup_chinese(self):
        table = SynonymTable()
        results = table.lookup("用户")
        assert "user" in results

    def test_lookup_english(self):
        table = SynonymTable()
        results = table.lookup("login")
        assert "登录" in results

    def test_match_score_exact(self):
        table = SynonymTable()
        score = table.match_score("登录", "login")
        assert score == 1.0

    def test_match_score_partial(self):
        table = SynonymTable()
        score = table.match_score("用户", "user_service")
        assert score >= 0.8

    def test_match_score_no_match(self):
        table = SynonymTable()
        score = table.match_score("量子计算", "quantum_compute")
        assert score == 0.0

    def test_add_synonym(self):
        table = SynonymTable()
        table.add_synonym("量子", "quantum")
        results = table.lookup("量子")
        assert "quantum" in results

    def test_add_custom_terms(self):
        table = SynonymTable()
        table.add_custom_terms({"量子": ["quantum"], "比特": ["bit"]})
        assert "quantum" in table.lookup("量子")
        assert "bit" in table.lookup("比特")

    def test_abbreviation_expansion(self):
        table = SynonymTable()
        results = table.lookup("RBAC")
        assert "rbac" in results


# ===== ConventionMatcher Tests =====


class TestConventionMatcher:
    def test_match_req_id_in_section(self):
        sec = _make_section(title="REQ-001 用户认证", content="通过JWT认证")
        doc = _make_doc_result(sections=[sec])
        func = _make_func(name="authenticate", docstring="Implements REQ-001")
        code = _make_code_result(modules=[_make_module(functions=[func])])

        matcher = ConventionMatcher()
        traces = matcher.match([doc], code)
        assert len(traces) >= 1
        assert traces[0].confidence == 1.0
        assert traces[0].trace_type == "convention"
        assert traces[0].status == "covered"

    def test_match_req_id_in_function_name(self):
        sec = _make_section(title="REQ-002 权限控制", content="RBAC")
        doc = _make_doc_result(sections=[sec])
        func = _make_func(name="req_002_check_permission")
        code = _make_code_result(modules=[_make_module(functions=[func])])

        matcher = ConventionMatcher()
        traces = matcher.match([doc], code)
        assert len(traces) >= 1

    def test_match_section_number(self):
        sec = _make_section(title="2.1 登录功能", content="登录页面")
        doc = _make_doc_result(sections=[sec])
        func = _make_func(name="login", docstring="# 2.1 login handler")
        code = _make_code_result(modules=[_make_module(functions=[func])])

        matcher = ConventionMatcher()
        traces = matcher.match([doc], code)
        assert len(traces) >= 1

    def test_no_match_different_ids(self):
        sec = _make_section(title="REQ-001 用户认证", content="认证")
        doc = _make_doc_result(sections=[sec])
        func = _make_func(name="delete_user", docstring="Implements REQ-999")
        code = _make_code_result(modules=[_make_module(functions=[func])])

        matcher = ConventionMatcher()
        traces = matcher.match([doc], code)
        assert len(traces) == 0

    def test_match_feature_prefix(self):
        sec = _make_section(title="FEATURE-AUTH 用户认证", content="认证")
        doc = _make_doc_result(sections=[sec])
        func = _make_func(name="feature_auth_login")
        code = _make_code_result(modules=[_make_module(functions=[func])])

        matcher = ConventionMatcher()
        traces = matcher.match([doc], code)
        assert len(traces) >= 1

    def test_match_in_table_row(self):
        table = DocumentTable(
            table_id="T001",
            page_number=1,
            headers=["ID", "描述"],
            rows=[["REQ-003", "密码强度校验"]],
        )
        doc = _make_doc_result(tables=[table])
        func = _make_func(name="validate", docstring="# REQ-003 password")
        code = _make_code_result(modules=[_make_module(functions=[func])])

        matcher = ConventionMatcher()
        traces = matcher.match([doc], code)
        assert len(traces) >= 1

    def test_empty_inputs(self):
        matcher = ConventionMatcher()
        assert matcher.match([], _make_code_result()) == []
        assert matcher.match([_make_doc_result()], _make_code_result()) == []


# ===== KeywordMatcher Tests =====


class TestKeywordMatcher:
    def test_match_by_synonym(self):
        sec = _make_section(title="用户认证", content="用户通过JWT认证登录")
        doc = _make_doc_result(sections=[sec])
        func = _make_func(name="authenticate_user", docstring="User JWT authentication")
        code = _make_code_result(modules=[_make_module(functions=[func])])

        matcher = KeywordMatcher()
        traces = matcher.match([doc], code)
        assert len(traces) >= 1
        assert traces[0].confidence >= 0.7
        assert traces[0].trace_type == "keyword"

    def test_match_login(self):
        sec = _make_section(title="登录功能", content="用户登录页面")
        doc = _make_doc_result(sections=[sec])
        func = _make_func(name="login")
        code = _make_code_result(modules=[_make_module(functions=[func])])

        matcher = KeywordMatcher()
        traces = matcher.match([doc], code)
        assert len(traces) >= 1

    def test_no_match_unrelated(self):
        sec = _make_section(title="量子计算", content="量子比特操作")
        doc = _make_doc_result(sections=[sec])
        func = _make_func(name="print_hello")
        code = _make_code_result(modules=[_make_module(functions=[func])])

        matcher = KeywordMatcher()
        traces = matcher.match([doc], code)
        assert len(traces) == 0

    def test_skips_already_matched(self):
        sec = _make_section(title="用户认证", content="认证")
        doc = _make_doc_result(sections=[sec])
        func = _make_func(name="authenticate_user")
        code = _make_code_result(modules=[_make_module(functions=[func])])

        existing = [
            TraceEntry(
                trace_id="TRACE-C001",
                requirement="认证",
                req_source="test.pdf 用户认证",
                implementation="auth.py:authenticate_user()",
                impl_file="auth.py",
                impl_function="authenticate_user",
                trace_type="convention",
                confidence=1.0,
                status="covered",
            )
        ]

        matcher = KeywordMatcher()
        traces = matcher.match([doc], code, existing_traces=existing)
        assert len(traces) == 0

    def test_match_class_name(self):
        sec = _make_section(title="订单管理", content="订单创建和查询")
        doc = _make_doc_result(sections=[sec])
        cls = _make_class(name="OrderManager", docstring="Order management")
        code = _make_code_result(modules=[_make_module(classes=[cls])])

        matcher = KeywordMatcher()
        traces = matcher.match([doc], code)
        assert len(traces) >= 1


# ===== SemanticMatcher Tests =====


class TestSemanticMatcher:
    def test_heuristic_match(self):
        sec = _make_section(
            title="用户认证",
            content="user authentication login JWT token",
        )
        doc = _make_doc_result(sections=[sec])
        func = _make_func(
            name="authenticate",
            docstring="Authenticate user with JWT token login",
        )
        code = _make_code_result(modules=[_make_module(functions=[func])])

        matcher = SemanticMatcher()
        traces = matcher.match([doc], code)
        assert len(traces) >= 1
        assert traces[0].trace_type == "semantic"

    def test_no_match_empty(self):
        matcher = SemanticMatcher()
        assert matcher.match([], _make_code_result()) == []

    def test_skips_matched(self):
        sec = _make_section(title="认证", content="authentication")
        doc = _make_doc_result(sections=[sec])
        func = _make_func(name="authenticate")
        code = _make_code_result(modules=[_make_module(functions=[func])])

        existing = [
            TraceEntry(
                trace_id="TRACE-C001",
                requirement="认证",
                req_source="test.pdf 认证",
                impl_file="auth.py",
                impl_function="authenticate",
                trace_type="convention",
                confidence=1.0,
                status="covered",
            )
        ]

        matcher = SemanticMatcher()
        traces = matcher.match([doc], code, existing_traces=existing)
        assert len(traces) == 0

    def test_llm_func_called(self):
        sec = _make_section(title="认证", content="JWT")
        doc = _make_doc_result(sections=[sec])
        func = _make_func(name="authenticate")
        code = _make_code_result(modules=[_make_module(functions=[func])])

        def mock_llm(prompt):
            return "R0 <-> C0 | 0.8 | JWT authentication match"

        matcher = SemanticMatcher(llm_func=mock_llm)
        traces = matcher.match([doc], code)
        assert len(traces) >= 1
        assert traces[0].confidence == 0.8


# ===== DiffAnalyzer Tests =====


class TestDiffAnalyzer:
    def test_find_gaps(self):
        sec1 = _make_section(sid="S001", title="认证", content="JWT认证")
        sec2 = _make_section(sid="S002", title="权限", content="RBAC权限")
        doc = _make_doc_result(sections=[sec1, sec2])
        func = _make_func(name="authenticate")
        code = _make_code_result(modules=[_make_module(functions=[func])])

        traces = [
            TraceEntry(
                trace_id="T001",
                requirement="JWT认证",
                req_source="test.pdf 认证",
                impl_file="auth.py",
                impl_function="authenticate",
                trace_type="convention",
                confidence=1.0,
                status="covered",
            )
        ]

        analyzer = DiffAnalyzer()
        diffs = analyzer.analyze([doc], code, traces)
        gap_diffs = [d for d in diffs if d.diff_type == "gap"]
        assert len(gap_diffs) >= 1

    def test_find_extras(self):
        sec = _make_section(title="认证", content="JWT认证")
        doc = _make_doc_result(sections=[sec])
        f1 = _make_func(fid="F001", name="authenticate")
        f2 = _make_func(fid="F002", name="send_email")
        code = _make_code_result(modules=[_make_module(functions=[f1, f2])])

        traces = [
            TraceEntry(
                trace_id="T001",
                requirement="JWT认证",
                req_source="test.pdf 认证",
                impl_file="auth.py",
                impl_function="authenticate",
                trace_type="convention",
                confidence=1.0,
                status="covered",
            )
        ]

        analyzer = DiffAnalyzer()
        diffs = analyzer.analyze([doc], code, traces)
        extra_diffs = [d for d in diffs if d.diff_type == "extra"]
        assert len(extra_diffs) >= 1

    def test_no_diffs_full_coverage(self):
        sec = _make_section(title="认证", content="JWT")
        doc = _make_doc_result(sections=[sec])
        func = _make_func(name="authenticate")
        code = _make_code_result(modules=[_make_module(functions=[func])])

        traces = [
            TraceEntry(
                trace_id="T001",
                requirement="JWT",
                req_source="test.pdf 认证",
                impl_file="auth.py",
                impl_function="authenticate",
                trace_type="convention",
                confidence=1.0,
                status="covered",
            )
        ]

        analyzer = DiffAnalyzer()
        diffs = analyzer.analyze([doc], code, traces)
        gap_diffs = [d for d in diffs if d.diff_type == "gap"]
        assert len(gap_diffs) == 0

    def test_skips_private_functions_as_extras(self):
        doc = _make_doc_result(sections=[])
        func = _make_func(name="_helper")
        code = _make_code_result(modules=[_make_module(functions=[func])])

        analyzer = DiffAnalyzer()
        diffs = analyzer.analyze([doc], code, [])
        extra_diffs = [d for d in diffs if d.diff_type == "extra"]
        assert len(extra_diffs) == 0


# ===== FixSuggester Tests =====


class TestFixSuggester:
    def test_suggest_for_gap(self):
        diff = DiffEntry(
            diff_id="DIFF-G001",
            diff_type="gap",
            description="未覆盖的需求",
            req_side="test.pdf: 用户密码强度校验",
        )
        suggester = FixSuggester()
        results = suggester.suggest([diff])
        assert len(results) == 1
        assert results[0].suggestion_by_doc is not None
        assert results[0].suggestion_by_code is not None
        assert "以文档为准" in results[0].suggestion_by_doc

    def test_suggest_for_extra(self):
        diff = DiffEntry(
            diff_id="DIFF-E001",
            diff_type="extra",
            description="无文档对应",
            code_side="auth.py:send_email()",
        )
        suggester = FixSuggester()
        results = suggester.suggest([diff])
        assert len(results) == 1
        assert "以文档为准" in results[0].suggestion_by_doc

    def test_suggest_for_inconsistency(self):
        diff = DiffEntry(
            diff_id="DIFF-I001",
            diff_type="inconsistency",
            description="不一致",
            req_side="需求A",
            code_side="实现B",
        )
        suggester = FixSuggester()
        results = suggester.suggest([diff])
        assert len(results) == 1
        assert results[0].suggestion_by_doc is not None


# ===== GranularityAdjuster Tests =====


class TestGranularityAdjuster:
    def _make_cross_ref(self, traces=None):
        return CrossReferenceResult(
            trace_matrix=traces or [],
            diff_report=[],
            coverage_report={},
            unmatched_reqs=[],
            unmatched_code=[],
        )

    def test_coarsen(self):
        traces = [
            TraceEntry(
                trace_id="T001",
                requirement="登录",
                req_source="doc.pdf 登录",
                impl_file="auth.py",
                impl_function="login",
                trace_type="keyword",
                confidence=0.9,
                status="covered",
            ),
            TraceEntry(
                trace_id="T002",
                requirement="登出",
                req_source="doc.pdf 登出",
                impl_file="auth.py",
                impl_function="logout",
                trace_type="keyword",
                confidence=0.85,
                status="covered",
            ),
        ]
        ref = self._make_cross_ref(traces)
        adjuster = GranularityAdjuster()
        result = adjuster.coarsen(ref)
        assert len(result.trace_matrix) == 1
        assert result.trace_matrix[0].trace_type == "module_level"
        assert "登录" in result.trace_matrix[0].requirement

    def test_coarsen_specific_file(self):
        traces = [
            TraceEntry(
                trace_id="T001",
                requirement="认证",
                req_source="doc.pdf 认证",
                impl_file="auth.py",
                impl_function="auth",
                trace_type="keyword",
                confidence=0.9,
                status="covered",
            ),
            TraceEntry(
                trace_id="T002",
                requirement="支付",
                req_source="doc.pdf 支付",
                impl_file="pay.py",
                impl_function="pay",
                trace_type="keyword",
                confidence=0.8,
                status="covered",
            ),
        ]
        ref = self._make_cross_ref(traces)
        adjuster = GranularityAdjuster()
        result = adjuster.coarsen(ref, target_file="auth.py")
        assert len(result.trace_matrix) == 1

    def test_refine(self):
        traces = [
            TraceEntry(
                trace_id="T001",
                requirement="认证",
                req_source="doc.pdf",
                impl_file="auth.py",
                impl_function="auth_module",
                trace_type="keyword",
                confidence=0.9,
                status="covered",
            )
        ]
        ref = self._make_cross_ref(traces)
        adjuster = GranularityAdjuster()
        result = adjuster.refine(
            ref,
            "T001",
            [
                {"impl_function": "login", "impl_lines": "L10-20"},
                {"impl_function": "logout", "impl_lines": "L22-30"},
            ],
        )
        assert len(result.trace_matrix) == 2
        assert result.trace_matrix[0].impl_function == "login"

    def test_add_entry(self):
        ref = self._make_cross_ref()
        adjuster = GranularityAdjuster()
        result = adjuster.add_entry(
            ref,
            req_text="密码校验",
            req_source="doc.pdf 密码",
            impl_file="auth.py",
            impl_function="validate_password",
        )
        assert len(result.trace_matrix) == 1
        assert result.trace_matrix[0].trace_type == "manual"
        assert result.trace_matrix[0].confidence == 1.0

    def test_remove_entry(self):
        traces = [
            TraceEntry(trace_id="T001", trace_type="keyword", confidence=0.9),
            TraceEntry(trace_id="T002", trace_type="keyword", confidence=0.8),
        ]
        ref = self._make_cross_ref(traces)
        adjuster = GranularityAdjuster()
        result = adjuster.remove_entry(ref, "T001")
        assert len(result.trace_matrix) == 1
        assert result.trace_matrix[0].trace_id == "T002"


# ===== TraceMatchEngine Integration Tests =====


class TestTraceMatchEngine:
    def test_full_pipeline(self):
        sec1 = _make_section(
            sid="S001",
            title="REQ-001 用户认证",
            content="通过JWT认证登录系统",
        )
        sec2 = _make_section(
            sid="S002",
            title="用户权限管理",
            content="基于角色的访问控制RBAC",
        )
        doc = _make_doc_result(sections=[sec1, sec2])

        f1 = _make_func(fid="F001", name="req_001_authenticate", docstring="JWT auth")
        f2 = _make_func(
            fid="F002", name="check_permission", docstring="RBAC permission check"
        )
        code = _make_code_result(modules=[_make_module(functions=[f1, f2])])

        engine = TraceMatchEngine()
        result = engine.match([doc], code)

        assert isinstance(result, CrossReferenceResult)
        assert len(result.trace_matrix) >= 1
        assert result.coverage_report.get("total_requirements", 0) > 0
        assert isinstance(result.diff_report, list)

    def test_empty_inputs(self):
        engine = TraceMatchEngine()
        result = engine.match([], _make_code_result())
        assert result.trace_matrix == []

    def test_coverage_report(self):
        sec = _make_section(title="REQ-001 认证", content="JWT认证")
        doc = _make_doc_result(sections=[sec])
        func = _make_func(name="authenticate", docstring="REQ-001")
        code = _make_code_result(modules=[_make_module(functions=[func])])

        engine = TraceMatchEngine()
        result = engine.match([doc], code)

        cr = result.coverage_report
        assert "total_requirements" in cr
        assert "covered_requirements" in cr
        assert "rate" in cr
        assert "by_match_type" in cr

    def test_unmatched_lists(self):
        sec1 = _make_section(title="认证", content="JWT")
        sec2 = _make_section(title="量子计算", content="量子")
        doc = _make_doc_result(sections=[sec1, sec2])
        func = _make_func(name="authenticate")
        code = _make_code_result(modules=[_make_module(functions=[func])])

        engine = TraceMatchEngine()
        result = engine.match([doc], code)

        assert isinstance(result.unmatched_reqs, list)
        assert isinstance(result.unmatched_code, list)

    def test_repr(self):
        ref = CrossReferenceResult(
            trace_matrix=[TraceEntry(trace_id="T001")],
            diff_report=[],
            coverage_report={"rate": 0.5},
        )
        assert "0.5" in repr(ref) or "50" in repr(ref)
