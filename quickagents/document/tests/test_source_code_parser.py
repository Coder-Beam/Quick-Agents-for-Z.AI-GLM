"""
Tests for Source Code Parser (Phase 6).

Covers:
- T028: SourceCodeResult + data models (already in models.py, tested here via parsing)
- T029: Python ast parser (module/class/function/dependency/docstring)
- T030: tree-sitter multi-language parser (conditional import)
- T031: Directory structure scanning + language detection
- T032: Config file parsing (json/yaml/toml)
- T033: Edge cases and regression
"""

import pytest
from pathlib import Path

from quickagents.document.parsers.source_code_parser import SourceCodeParser
from quickagents.document.models import SourceCodeResult

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SOURCE_FIXTURE = FIXTURES_DIR / "source_sample"


@pytest.fixture
def parser():
    return SourceCodeParser()


@pytest.fixture
def sample_result(parser):
    return parser.parse_directory(SOURCE_FIXTURE)


# ============================================================
# T028: Data Models (via parsing)
# ============================================================

class TestSourceCodeResultType:
    def test_is_source_code_result(self, sample_result):
        assert isinstance(sample_result, SourceCodeResult)

    def test_source_dir(self, sample_result):
        assert sample_result.source_dir == str(SOURCE_FIXTURE)

    def test_no_errors(self, sample_result):
        assert sample_result.errors == []

    def test_has_errors_false(self, sample_result):
        assert not sample_result.has_errors()

    def test_repr(self, sample_result):
        r = repr(sample_result)
        assert "SourceCodeResult" in r


# ============================================================
# T029: Python AST Parser
# ============================================================

class TestPythonASTParser:
    def test_python_modules_found(self, sample_result):
        py_mods = [m for m in sample_result.modules if m.language == "python"]
        assert len(py_mods) == 2

    def test_auth_module_functions(self, sample_result):
        auth = sample_result.find_module_by_path("auth.py")
        assert auth is not None
        func_names = [f.name for f in auth.functions]
        assert "hash_password" in func_names
        assert "verify_password" in func_names

    def test_auth_module_classes(self, sample_result):
        auth = sample_result.find_module_by_path("auth.py")
        assert auth is not None
        class_names = [c.name for c in auth.classes]
        assert "User" in class_names
        assert "AdminUser" in class_names

    def test_auth_module_docstring(self, sample_result):
        auth = sample_result.find_module_by_path("auth.py")
        assert auth is not None
        assert auth.module_docstring == "Authentication module."

    def test_function_docstring(self, sample_result):
        auth = sample_result.find_module_by_path("auth.py")
        hp = auth.find_function_by_name("hash_password")
        assert hp is not None
        assert hp.docstring is not None
        assert "password" in hp.docstring.lower() or "Hash" in hp.docstring

    def test_function_parameters(self, sample_result):
        auth = sample_result.find_module_by_path("auth.py")
        hp = auth.find_function_by_name("hash_password")
        assert hp is not None
        param_names = [p["name"] for p in hp.parameters]
        assert "password" in param_names
        assert "salt" in param_names

    def test_function_return_type(self, sample_result):
        auth = sample_result.find_module_by_path("auth.py")
        hp = auth.find_function_by_name("hash_password")
        assert hp is not None
        assert hp.return_type == "str"

    def test_function_line_numbers(self, sample_result):
        auth = sample_result.find_module_by_path("auth.py")
        hp = auth.find_function_by_name("hash_password")
        assert hp is not None
        assert hp.start_line > 0
        assert hp.end_line >= hp.start_line

    def test_function_calls(self, sample_result):
        auth = sample_result.find_module_by_path("auth.py")
        vp = auth.find_function_by_name("verify_password")
        assert vp is not None
        assert "hash_password" in vp.calls

    def test_class_methods(self, sample_result):
        auth = sample_result.find_module_by_path("auth.py")
        user_cls = auth.find_class_by_name("User")
        assert user_cls is not None
        method_names = [m.name for m in user_cls.methods]
        assert "set_password" in method_names
        assert "check_password" in method_names

    def test_class_inheritance(self, sample_result):
        auth = sample_result.find_module_by_path("auth.py")
        admin = auth.find_class_by_name("AdminUser")
        assert admin is not None
        assert "User" in admin.bases

    def test_class_attributes(self, sample_result):
        auth = sample_result.find_module_by_path("auth.py")
        admin = auth.find_class_by_name("AdminUser")
        assert admin is not None
        assert "role" in admin.attributes

    def test_imports_extracted(self, sample_result):
        auth = sample_result.find_module_by_path("auth.py")
        assert auth is not None
        assert any("hashlib" in i for i in auth.imports)
        assert any("typing" in i for i in auth.imports)

    def test_module_loc(self, sample_result):
        auth = sample_result.find_module_by_path("auth.py")
        assert auth is not None
        assert auth.loc > 0

    def test_utils_module(self, sample_result):
        utils = sample_result.find_module_by_path("utils.py")
        assert utils is not None
        func_names = [f.name for f in utils.functions]
        assert "read_json" in func_names
        assert "write_json" in func_names

    def test_module_variables(self, sample_result):
        utils = sample_result.find_module_by_path("utils.py")
        assert utils is not None
        assert "MAX_RETRIES" in utils.variables
        assert "DEFAULT_TIMEOUT" in utils.variables

    def test_get_all_functions(self, sample_result):
        auth = sample_result.find_module_by_path("auth.py")
        all_fns = auth.get_all_functions()
        assert len(all_fns) >= 4  # 2 top-level + at least 2 methods


# ============================================================
# T030: Tree-sitter / Generic Parser (JS)
# ============================================================

class TestJavaScriptParser:
    def test_js_module_found(self, sample_result):
        js_mods = [m for m in sample_result.modules if m.language == "javascript"]
        assert len(js_mods) == 1

    def test_js_functions(self, sample_result):
        js_mods = [m for m in sample_result.modules if m.language == "javascript"]
        assert len(js_mods) == 1
        func_names = [f.name for f in js_mods[0].functions]
        assert "loginUser" in func_names

    def test_js_class(self, sample_result):
        js_mods = [m for m in sample_result.modules if m.language == "javascript"]
        assert len(js_mods) == 1
        class_names = [c.name for c in js_mods[0].classes]
        assert "AuthService" in class_names

    def test_js_imports(self, sample_result):
        js_mods = [m for m in sample_result.modules if m.language == "javascript"]
        assert len(js_mods) == 1
        assert any("validators" in i for i in js_mods[0].imports)


# ============================================================
# T031: Directory Scanning + Language Detection
# ============================================================

class TestDirectoryScanning:
    def test_languages_detected(self, sample_result):
        assert "python" in sample_result.languages
        assert "javascript" in sample_result.languages

    def test_total_modules(self, sample_result):
        assert sample_result.get_module_count() >= 4

    def test_total_loc(self, sample_result):
        assert sample_result.get_total_loc() > 0

    def test_all_functions(self, sample_result):
        all_fns = sample_result.get_all_functions()
        assert len(all_fns) > 0

    def test_all_classes(self, sample_result):
        all_cls = sample_result.get_all_classes()
        assert len(all_cls) > 0

    def test_structure_tree(self, sample_result):
        tree = sample_result.structure_tree
        assert "children" in tree

    def test_stats(self, sample_result):
        stats = sample_result.stats
        assert "total_files" in stats
        assert "total_loc" in stats
        assert "total_functions" in stats
        assert "total_classes" in stats
        assert "language_distribution" in stats

    def test_skip_dirs(self, parser, tmp_path):
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "cached.pyc").write_text("bytecode")
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "index").write_text("git index")
        (tmp_path / "main.py").write_text("print('hello')\n")
        result = parser.parse_directory(tmp_path)
        assert result.get_module_count() == 1
        assert result.modules[0].file_path == "main.py"


# ============================================================
# T032: Config File Parsing
# ============================================================

class TestConfigParsing:
    def test_json_config_found(self, sample_result):
        json_mods = [m for m in sample_result.modules if m.language == "json"]
        assert len(json_mods) == 1

    def test_json_config_imports(self, sample_result):
        json_mods = [m for m in sample_result.modules if m.language == "json"]
        assert len(json_mods) == 1
        assert any("app_name" in i for i in json_mods[0].imports)


# ============================================================
# T033: Edge Cases + Roundtrip
# ============================================================

class TestEdgeCases:
    def test_dir_not_found(self, parser):
        with pytest.raises(FileNotFoundError):
            parser.parse_directory(Path("nonexistent_dir_xyz"))

    def test_not_a_dir(self, parser, tmp_path):
        f = tmp_path / "file.py"
        f.write_text("x = 1")
        with pytest.raises(ValueError):
            parser.parse_directory(f)

    def test_empty_dir(self, parser, tmp_path):
        result = parser.parse_directory(tmp_path)
        assert isinstance(result, SourceCodeResult)
        assert result.get_module_count() == 0
        assert result.errors == []

    def test_syntax_error_handled(self, parser, tmp_path):
        (tmp_path / "broken.py").write_text("def foo(\n  # syntax error\n")
        result = parser.parse_directory(tmp_path)
        assert isinstance(result, SourceCodeResult)
        assert result.get_module_count() == 1
        mod = result.modules[0]
        assert mod.language == "python"
        assert mod.loc > 0

    def test_to_dict_roundtrip(self, sample_result):
        d = sample_result.to_dict()
        assert d["source_dir"] == str(SOURCE_FIXTURE)
        restored = SourceCodeResult.from_dict(d)
        assert restored.source_dir == sample_result.source_dir
        assert len(restored.modules) == len(sample_result.modules)

    def test_raw_text_populated(self, sample_result):
        assert len(sample_result.raw_text) > 0
        for path, content in sample_result.raw_text.items():
            assert isinstance(content, str)
            assert len(content) > 0

    def test_find_module_by_path(self, sample_result):
        auth = sample_result.find_module_by_path("auth.py")
        assert auth is not None
        assert auth.language == "python"

    def test_find_module_not_found(self, sample_result):
        assert sample_result.find_module_by_path("nonexistent.py") is None


class TestDependencies:
    def test_inheritance_dependency(self, parser, tmp_path):
        (tmp_path / "base.py").write_text(
            "class Base:\n    pass\n"
        )
        (tmp_path / "child.py").write_text(
            "from base import Base\n\nclass Child(Base):\n    pass\n"
        )
        result = parser.parse_directory(tmp_path)
        inh_deps = [d for d in result.dependencies if d.dep_type == "inheritance"]
        assert len(inh_deps) >= 1
        assert any("child.py" in d.source_module for d in inh_deps)

    def test_import_dependency(self, parser, tmp_path):
        (tmp_path / "a.py").write_text(
            "import json\n\nx = 1\n"
        )
        result = parser.parse_directory(tmp_path)
        assert isinstance(result, SourceCodeResult)
