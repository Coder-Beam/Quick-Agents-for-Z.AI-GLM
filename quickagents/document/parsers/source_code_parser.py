"""
Source Code Parser - Layer 1 parser for source code directories.

Uses Python ast module for .py files, optional tree-sitter for
JS/TS/Java/Go/Rust/C/C++, and plain text scanning for config files.
"""

import ast
import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..models import (
    SourceCodeResult,
    CodeModule,
    CodeClass,
    CodeFunction,
    CodeDependency,
)

logger = logging.getLogger(__name__)

_LANG_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".jsx": "javascript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".c": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".h": "c",
    ".hpp": "cpp",
}

_AST_LANGUAGES = {"python"}
_TREE_SITTER_LANGUAGES = {
    "javascript", "typescript", "java", "go", "rust", "c", "cpp",
}

_CONFIG_EXTENSIONS = {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"}

_SKIP_DIRS = {
    "__pycache__", ".git", ".svn", "node_modules", ".venv", "venv",
    ".env", ".tox", ".mypy_cache", ".pytest_cache", "dist", "build",
    ".eggs", ".idea", ".vscode", "target", "bin", "obj",
}


class SourceCodeParser:
    """Source code directory parser"""

    def parse_directory(self, source_dir: Path) -> SourceCodeResult:
        source_dir = Path(source_dir)
        if not source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {source_dir}")
        if not source_dir.is_dir():
            raise ValueError(f"Not a directory: {source_dir}")

        logger.info(f"Parsing source directory: {source_dir}")

        modules: List[CodeModule] = []
        dependencies: List[CodeDependency] = []
        raw_text: Dict[str, str] = {}
        errors: List[str] = []

        source_files = self._scan_source_files(source_dir)

        mod_counter = 0
        for file_path in source_files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
                lang = self._detect_language(file_path)

                if lang in _AST_LANGUAGES:
                    mod = self._parse_python(file_path, content, source_dir)
                elif lang in _TREE_SITTER_LANGUAGES:
                    mod = self._parse_with_tree_sitter(
                        file_path, content, source_dir, lang
                    )
                else:
                    mod = self._parse_generic(file_path, content, source_dir, lang)

                if mod:
                    mod_counter += 1
                    modules.append(mod)
                    raw_text[str(file_path.relative_to(source_dir))] = content

            except Exception as e:
                rel = self._rel_path(file_path, source_dir)
                errors.append(f"{rel}: {e}")
                logger.warning(f"Error parsing {file_path}: {e}")

        config_modules = self._parse_config_files(source_dir)
        for mod in config_modules:
            mod_counter += 1
            modules.append(mod)

        languages = sorted(set(m.language for m in modules))
        deps = self._build_dependencies(modules)
        dependencies.extend(deps)

        stats = self._compute_stats(modules)

        return SourceCodeResult(
            source_dir=str(source_dir),
            languages=languages,
            modules=modules,
            dependencies=dependencies,
            structure_tree=self._build_structure_tree(modules),
            stats=stats,
            raw_text=raw_text,
            errors=errors,
        )

    def _scan_source_files(self, source_dir: Path) -> List[Path]:
        files = []
        for p in sorted(source_dir.rglob("*")):
            if not p.is_file():
                continue
            if any(part in _SKIP_DIRS for part in p.parts):
                continue
            ext = p.suffix.lower()
            if ext in _LANG_MAP:
                files.append(p)
        return files

    def _detect_language(self, file_path: Path) -> str:
        return _LANG_MAP.get(file_path.suffix.lower(), "unknown")

    def _rel_path(self, file_path: Path, base: Path) -> str:
        try:
            return str(file_path.relative_to(base))
        except ValueError:
            return str(file_path)

    # ---------- Python AST Parser (T029) ----------

    def _parse_python(
        self, file_path: Path, content: str, base_dir: Path
    ) -> Optional[CodeModule]:
        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            return self._parse_generic(file_path, content, base_dir, "python")

        rel = self._rel_path(file_path, base_dir)
        loc = len(content.splitlines())
        docstring = ast.get_docstring(tree)
        imports = self._extract_python_imports(tree)
        classes = self._extract_python_classes(tree, rel)
        functions = self._extract_python_functions(tree, rel)
        variables = self._extract_python_variables(tree)

        return CodeModule(
            module_id=f"M{hash(rel) & 0xFFFF:04x}",
            file_path=rel,
            language="python",
            loc=loc,
            module_docstring=docstring,
            imports=imports,
            classes=classes,
            functions=functions,
            variables=variables,
        )

    def _extract_python_imports(self, tree: ast.AST) -> List[str]:
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for alias in node.names:
                    imports.append(f"from {mod} import {alias.name}")
        return imports

    def _extract_python_classes(
        self, tree: ast.AST, rel: str
    ) -> List[CodeClass]:
        classes = []
        for node in ast.iter_child_nodes(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            bases = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(ast.dump(base))

            decorators = []
            for dec in node.decorator_list:
                decorators.append(self._decorator_str(dec))

            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(self._parse_function_def(item, rel))

            attrs = []
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            attrs.append(target.id)

            classes.append(CodeClass(
                class_id=f"C{hash(f'{rel}:{node.name}') & 0xFFFF:04x}",
                name=node.name,
                docstring=ast.get_docstring(node),
                bases=bases,
                methods=methods,
                attributes=attrs,
                decorators=decorators,
            ))
        return classes

    def _extract_python_functions(
        self, tree: ast.AST, rel: str
    ) -> List[CodeFunction]:
        funcs = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                funcs.append(self._parse_function_def(node, rel))
        return funcs

    def _parse_function_def(
        self, node, rel: str
    ) -> CodeFunction:
        name = node.name
        params = self._parse_function_params(node)
        ret_type = self._parse_return_type(node)
        sig = self._build_signature(name, params, ret_type)
        calls = self._extract_function_calls(node)
        decorators = [self._decorator_str(d) for d in node.decorator_list]

        return CodeFunction(
            func_id=f"F{hash(f'{rel}:{name}:{node.lineno}') & 0xFFFF:04x}",
            name=name,
            signature=sig,
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            docstring=ast.get_docstring(node),
            parameters=params,
            return_type=ret_type,
            decorators=decorators,
            calls=calls,
        )

    def _parse_function_params(self, node) -> List[Dict]:
        params = []
        for arg in node.args.args:
            if arg.arg == "self":
                continue
            p: Dict[str, Any] = {"name": arg.arg}
            if arg.annotation:
                p["type"] = self._annotation_str(arg.annotation)
            params.append(p)
        if node.args.vararg:
            params.append({"name": f"*{node.args.vararg.arg}"})
        if node.args.kwarg:
            params.append({"name": f"**{node.args.kwarg.arg}"})
        return params

    def _parse_return_type(self, node) -> Optional[str]:
        if node.returns:
            return self._annotation_str(node.returns)
        return None

    def _build_signature(
        self, name: str, params: List[Dict], ret_type: Optional[str]
    ) -> str:
        parts = [p["name"] for p in params]
        sig = f"{name}({', '.join(parts)})"
        if ret_type:
            sig += f" -> {ret_type}"
        return sig

    def _extract_function_calls(self, node) -> List[str]:
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(child.func.attr)
        return sorted(set(calls))

    def _extract_python_variables(self, tree: ast.AST) -> List[str]:
        variables = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        if not name.startswith("_"):
                            variables.append(name)
        return variables

    def _annotation_str(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Constant):
            return str(node.value)
        if isinstance(node, ast.Subscript):
            base = self._annotation_str(node.value)
            sl = node.slice
            if isinstance(sl, ast.Index):
                sl = sl.value
            if isinstance(sl, ast.Tuple):
                inner = ", ".join(self._annotation_str(e) for e in sl.elts)
            else:
                inner = self._annotation_str(sl)
            return f"{base}[{inner}]"
        if isinstance(node, ast.Attribute):
            parts = []
            cur = node
            while isinstance(cur, ast.Attribute):
                parts.append(cur.attr)
                cur = cur.value
            if isinstance(cur, ast.Name):
                parts.append(cur.id)
            return ".".join(reversed(parts))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            return f"{self._annotation_str(node.left)} | {self._annotation_str(node.right)}"
        return ast.dump(node, annotate_fields=False)

    def _decorator_str(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return self._annotation_str(node)
        if isinstance(node, ast.Call):
            return self._decorator_str(node.func) + "(...)"
        return ast.dump(node, annotate_fields=False)

    # ---------- Tree-sitter Parser (T030) ----------

    def _parse_with_tree_sitter(
        self, file_path: Path, content: str, base_dir: Path, lang: str
    ) -> Optional[CodeModule]:
        try:
            import tree_sitter
        except ImportError:
            return self._parse_generic(file_path, content, base_dir, lang)

        rel = self._rel_path(file_path, base_dir)
        loc = len(content.splitlines())

        try:
            ts_lang = self._get_tree_sitter_language(lang)
            if ts_lang is None:
                return self._parse_generic(file_path, content, base_dir, lang)

            parser = tree_sitter.Parser(ts_lang)
            tree = parser.parse(content.encode("utf-8"))

            imports = self._ts_extract_imports(tree, content)
            classes = self._ts_extract_classes(tree, content, rel)
            functions = self._ts_extract_functions(tree, content, rel)

            return CodeModule(
                module_id=f"M{hash(rel) & 0xFFFF:04x}",
                file_path=rel,
                language=lang,
                loc=loc,
                module_docstring=None,
                imports=imports,
                classes=classes,
                functions=functions,
                variables=[],
            )
        except Exception as e:
            logger.warning(f"tree-sitter parsing failed for {file_path}: {e}")
            return self._parse_generic(file_path, content, base_dir, lang)

    def _get_tree_sitter_language(self, lang_name: str):
        try:
            import tree_sitter_languages
            return tree_sitter_languages.get_language(lang_name)
        except ImportError:
            pass

        try:
            mod_name = f"tree_sitter_{lang_name}"
            mod = __import__(mod_name)
            return mod.language()
        except ImportError:
            logger.warning(
                f"tree-sitter language '{lang_name}' not available. "
                f"Install with: pip install tree-sitter-languages"
            )
            return None

    def _ts_extract_imports(self, tree, content: str) -> List[str]:
        imports = []
        source = content.encode("utf-8")
        for node in self._ts_query_nodes(tree, "import_statement"):
            imports.append(source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")[:120])
        for node in self._ts_query_nodes(tree, "import_from_statement"):
            imports.append(source[node.start_byte:node.end_byte].decode("utf-8", errors="replace")[:120])
        return imports

    def _ts_extract_classes(self, tree, content: str, rel: str) -> List[CodeClass]:
        classes = []
        source = content.encode("utf-8")
        for node in self._ts_query_nodes(tree, "class_declaration"):
            name = self._ts_get_child_text(node, "identifier", source) or "Anonymous"
            classes.append(CodeClass(
                class_id=f"C{hash(f'{rel}:{name}') & 0xFFFF:04x}",
                name=name,
                docstring=None,
                bases=[],
                methods=[],
                attributes=[],
            ))
        return classes

    def _ts_extract_functions(
        self, tree, content: str, rel: str
    ) -> List[CodeFunction]:
        funcs = []
        source = content.encode("utf-8")
        for node in self._ts_query_nodes(tree, "function_declaration"):
            name = self._ts_get_child_text(node, "identifier", source) or "anonymous"
            funcs.append(CodeFunction(
                func_id=f"F{hash(f'{rel}:{name}:{node.start_point[0]}') & 0xFFFF:04x}",
                name=name,
                signature=f"{name}(...)",
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
            ))
        for node in self._ts_query_nodes(tree, "method_definition"):
            name = self._ts_get_child_text(node, "property_identifier", source) or "anonymous"
            funcs.append(CodeFunction(
                func_id=f"F{hash(f'{rel}:{name}:{node.start_point[0]}') & 0xFFFF:04x}",
                name=name,
                signature=f"{name}(...)",
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
            ))
        return funcs

    def _ts_query_nodes(self, tree, type_name: str) -> list:
        results = []
        def walk(node):
            if node.type == type_name:
                results.append(node)
            for child in node.children:
                walk(child)
        walk(tree.root_node)
        return results

    def _ts_get_child_text(self, node, child_type: str, source: bytes) -> Optional[str]:
        for child in node.children:
            if child.type == child_type:
                return source[child.start_byte:child.end_byte].decode("utf-8", errors="replace")
        return None

    # ---------- Generic / Regex Parser ----------

    def _parse_generic(
        self, file_path: Path, content: str, base_dir: Path, lang: str
    ) -> CodeModule:
        rel = self._rel_path(file_path, base_dir)
        loc = len(content.splitlines())

        functions = self._regex_extract_functions(content, rel, lang)
        imports = self._regex_extract_imports(content, lang)
        classes = self._regex_extract_classes(content, rel, lang)

        return CodeModule(
            module_id=f"M{hash(rel) & 0xFFFF:04x}",
            file_path=rel,
            language=lang,
            loc=loc,
            module_docstring=None,
            imports=imports,
            classes=classes,
            functions=functions,
            variables=[],
        )

    def _regex_extract_functions(
        self, content: str, rel: str, lang: str
    ) -> List[CodeFunction]:
        funcs = []
        patterns = {
            "python": re.compile(
                r"^(\s*)(async\s+)?def\s+(\w+)\s*\(", re.MULTILINE
            ),
            "javascript": re.compile(
                r"(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>))",
                re.MULTILINE,
            ),
            "typescript": re.compile(
                r"(?:function\s+(\w+)|(?:export\s+)?(?:async\s+)?function\s+(\w+))",
                re.MULTILINE,
            ),
            "java": re.compile(
                r"(?:public|private|protected|static|\s)+[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{",
                re.MULTILINE,
            ),
            "go": re.compile(r"func\s+(?:\([^)]+\)\s*)?(\w+)\s*\(", re.MULTILINE),
            "rust": re.compile(
                r"(?:pub\s+)?(?:async\s+)?fn\s+(\w+)", re.MULTILINE
            ),
            "c": re.compile(
                r"(?:[\w*]+\s+)+(\w+)\s*\([^)]*\)\s*\{", re.MULTILINE
            ),
            "cpp": re.compile(
                r"(?:[\w*]+\s+)+(\w+)\s*\([^)]*\)\s*(?:const)?\s*(?:\{|:)", re.MULTILINE
            ),
        }
        pat = patterns.get(lang)
        if not pat:
            return funcs

        for m in pat.finditer(content):
            name = m.group(1) or m.group(2) if m.lastindex and m.lastindex >= 2 else m.group(1)
            if not name:
                continue
            line_num = content[:m.start()].count("\n") + 1
            funcs.append(CodeFunction(
                func_id=f"F{hash(f'{rel}:{name}:{line_num}') & 0xFFFF:04x}",
                name=name,
                signature=f"{name}(...)",
                start_line=line_num,
                end_line=line_num,
            ))
        return funcs

    def _regex_extract_imports(self, content: str, lang: str) -> List[str]:
        imports = []
        patterns = {
            "javascript": re.compile(
                r"(?:import\s+.+\s+from\s+['\"](.+?)['\"]|require\s*\(\s*['\"](.+?)['\"]\s*\))",
                re.MULTILINE,
            ),
            "typescript": re.compile(
                r"import\s+.+\s+from\s+['\"](.+?)['\"]", re.MULTILINE
            ),
            "java": re.compile(r"import\s+([\w.]+)\s*;", re.MULTILINE),
            "go": re.compile(
                r'import\s+(?:"([^"]+)"|\(\s*([^)]+)\s*\))', re.MULTILINE
            ),
            "rust": re.compile(r"use\s+([\w:]+)", re.MULTILINE),
            "c": re.compile(r'#include\s*[<"]([^>"]+)[>"]', re.MULTILINE),
            "cpp": re.compile(r'#include\s*[<"]([^>"]+)[>"]', re.MULTILINE),
        }
        pat = patterns.get(lang)
        if not pat:
            return imports

        for m in pat.finditer(content):
            for g in m.groups():
                if g:
                    for line in g.strip().split("\n"):
                        line = line.strip().strip('"').strip()
                        if line:
                            imports.append(line)
                    break
        return imports

    def _regex_extract_classes(
        self, content: str, rel: str, lang: str
    ) -> List[CodeClass]:
        classes = []
        patterns = {
            "javascript": re.compile(
                r"class\s+(\w+)(?:\s+extends\s+(\w+))?", re.MULTILINE
            ),
            "typescript": re.compile(
                r"(?:export\s+)?class\s+(\w+)", re.MULTILINE
            ),
            "java": re.compile(
                r"(?:public|private|protected)?\s*(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?",
                re.MULTILINE,
            ),
            "go": re.compile(r"type\s+(\w+)\s+struct\s*\{", re.MULTILINE),
            "rust": re.compile(
                r"(?:pub\s+)?struct\s+(\w+)", re.MULTILINE
            ),
            "cpp": re.compile(r"class\s+(\w+)(?:\s*:\s*public\s+(\w+))?", re.MULTILINE),
        }
        pat = patterns.get(lang)
        if not pat:
            return classes

        for m in pat.finditer(content):
            name = m.group(1)
            bases = []
            if m.lastindex and m.lastindex >= 2 and m.group(2):
                bases.append(m.group(2))
            classes.append(CodeClass(
                class_id=f"C{hash(f'{rel}:{name}') & 0xFFFF:04x}",
                name=name,
                docstring=None,
                bases=bases,
            ))
        return classes

    # ---------- Config File Parser (T032) ----------

    def _parse_config_files(self, source_dir: Path) -> List[CodeModule]:
        modules = []
        for p in sorted(source_dir.rglob("*")):
            if not p.is_file():
                continue
            if any(part in _SKIP_DIRS for part in p.parts):
                continue
            ext = p.suffix.lower()
            if ext not in _CONFIG_EXTENSIONS:
                continue
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
                rel = self._rel_path(p, source_dir)
                loc = len(content.splitlines())

                imports = self._parse_config_imports(content, ext)

                lang = ext.lstrip(".")  # json, yaml, toml, etc.

                modules.append(CodeModule(
                    module_id=f"M{hash(rel) & 0xFFFF:04x}",
                    file_path=rel,
                    language=lang,
                    loc=loc,
                    module_docstring=None,
                    imports=imports,
                ))
            except Exception as e:
                logger.warning(f"Error parsing config {p}: {e}")
        return modules

    def _parse_config_imports(self, content: str, ext: str) -> List[str]:
        if ext == ".json":
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    return list(data.keys())[:30]
            except json.JSONDecodeError:
                pass
        return []

    # ---------- Dependencies (T031) ----------

    def _build_dependencies(
        self, modules: List[CodeModule]
    ) -> List[CodeDependency]:
        deps = []
        seen = set()
        for mod in modules:
            for imp in mod.imports:
                top = imp.split(".")[0].split(" ")[0].strip()
                if not top or top in ("", ".", ".."):
                    continue
                for other in modules:
                    other_stem = Path(other.file_path).stem
                    if other_stem == top or other.file_path.endswith(f"/{top}.py"):
                        key = (mod.file_path, other.file_path, "import")
                        if key not in seen:
                            seen.add(key)
                            deps.append(CodeDependency(
                                source_module=mod.file_path,
                                target_module=other.file_path,
                                dep_type="import",
                            ))

            for cls in mod.classes:
                for base in cls.bases:
                    for other in modules:
                        for other_cls in other.classes:
                            if other_cls.name == base and other.file_path != mod.file_path:
                                key = (mod.file_path, other.file_path, "inheritance")
                                if key not in seen:
                                    seen.add(key)
                                    deps.append(CodeDependency(
                                        source_module=mod.file_path,
                                        target_module=other.file_path,
                                        dep_type="inheritance",
                                    ))
        return deps

    # ---------- Stats & Structure Tree ----------

    def _compute_stats(self, modules: List[CodeModule]) -> Dict[str, Any]:
        total_loc = sum(m.loc for m in modules)
        total_funcs = sum(len(m.get_all_functions()) for m in modules)
        total_classes = sum(len(m.classes) for m in modules)
        lang_counts: Dict[str, int] = {}
        for m in modules:
            lang_counts[m.language] = lang_counts.get(m.language, 0) + 1

        return {
            "total_files": len(modules),
            "total_loc": total_loc,
            "total_functions": total_funcs,
            "total_classes": total_classes,
            "language_distribution": lang_counts,
        }

    def _build_structure_tree(self, modules: List[CodeModule]) -> Dict:
        if not modules:
            return {}
        root: Dict[str, Any] = {"children": []}
        for mod in modules:
            parts = Path(mod.file_path).parts
            current = root
            for part in parts[:-1]:
                found = None
                for child in current["children"]:
                    if child.get("name") == part and "children" in child:
                        found = child
                        break
                if found is None:
                    found = {"name": part, "type": "directory", "children": []}
                    current["children"].append(found)
                current = found
            current["children"].append({
                "name": parts[-1],
                "type": "file",
                "language": mod.language,
                "id": mod.module_id,
                "loc": mod.loc,
            })
        return root
