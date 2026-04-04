"""
Markdown Exporter - Export analysis results to Markdown files.

Generates human-readable Markdown reports:
- Trace matrix table
- Coverage report
- Diff report with fix suggestions
"""

from typing import List, Optional
from datetime import datetime
from pathlib import Path

from ..models import (
    CrossReferenceResult,
    DocumentResult,
    SourceCodeResult,
)


class MarkdownExporter:
    """Export document analysis results to Markdown format."""

    def export_trace_matrix(
        self,
        result: CrossReferenceResult,
        doc_sources: Optional[List[str]] = None,
        code_dir: Optional[str] = None,
    ) -> str:
        lines: List[str] = []
        lines.append("# 需求追踪矩阵")
        lines.append("")
        lines.append(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if doc_sources:
            lines.append(f"> 文档源: {', '.join(doc_sources)}")
        if code_dir:
            lines.append(f"> 源码源: {code_dir}")

        by_type = result.coverage_report.get("by_match_type", {})
        type_str = (
            " + ".join(f"{k}({v})" for k, v in by_type.items()) if by_type else "无匹配"
        )
        lines.append(f"> 匹配引擎: {type_str}")
        lines.append("")

        lines.append("## 追踪矩阵")
        lines.append("")
        lines.append(
            "| 需求ID | 需求描述 | 来源文档 | 实现模块 | "
            "实现函数 | 行范围 | 匹配方式 | 置信度 | 状态 |"
        )
        lines.append(
            "|--------|----------|----------|----------|"
            "----------|--------|----------|--------|------|"
        )
        for t in result.trace_matrix:
            lines.append(
                f"| {t.trace_id} | {_cell(t.requirement, 30)} | "
                f"{_cell(t.req_source, 20)} | {_cell(t.impl_file, 15)} | "
                f"{_cell(t.impl_function, 15)} | {t.impl_lines or '--'} | "
                f"{t.trace_type} | {t.confidence:.2f} | {t.status} |"
            )

        lines.append("")
        return "\n".join(lines)

    def export_coverage_report(self, result: CrossReferenceResult) -> str:
        lines: List[str] = []
        lines.append("## 覆盖率报告")
        lines.append("")

        cr = result.coverage_report
        total = cr.get("total_requirements", 0)
        covered = cr.get("covered_requirements", 0)
        uncovered = cr.get("uncovered_requirements", 0)
        rate = cr.get("rate", 0.0)
        total_code = cr.get("total_code_items", 0)
        covered_code = cr.get("covered_code", 0)

        lines.append("| 指标 | 数值 |")
        lines.append("|------|------|")
        lines.append(f"| 总需求数 | {total} |")
        lines.append(f"| 已覆盖 | {covered} ({rate:.1%}) |")
        lines.append(f"| 未覆盖 | {uncovered} |")
        lines.append(f"| 总代码项 | {total_code} |")
        lines.append(f"| 已关联代码 | {covered_code} |")

        by_type = cr.get("by_match_type", {})
        if by_type:
            lines.append("")
            lines.append("### 按匹配方式")
            lines.append("")
            lines.append("| 方式 | 数量 |")
            lines.append("|------|------|")
            for mt, count in by_type.items():
                lines.append(f"| {mt} | {count} |")

        lines.append("")
        return "\n".join(lines)

    def export_diff_report(
        self,
        result: CrossReferenceResult,
        base: str = "doc",
    ) -> str:
        lines: List[str] = []
        lines.append("# 差异报告")
        lines.append("")
        lines.append(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"> 修正基准: {'以文档为准' if base == 'doc' else '以代码为准'}")
        lines.append("")

        gaps = [d for d in result.diff_report if d.diff_type == "gap"]
        extras = [d for d in result.diff_report if d.diff_type == "extra"]
        inconsistencies = [
            d for d in result.diff_report if d.diff_type == "inconsistency"
        ]

        if gaps:
            lines.append("## 未覆盖的需求（有需求无实现）")
            lines.append("")
            for d in gaps:
                lines.append(f"### {d.diff_id}: {_cell(d.description, 60)}")
                lines.append(f"- **需求侧**: {d.req_side or '--'}")
                suggestion = (
                    d.suggestion_by_doc if base == "doc" else d.suggestion_by_code
                )
                if suggestion:
                    lines.append(f"- **建议**: {suggestion[:200]}")
                lines.append("")

        if extras:
            lines.append("## 无文档对应的实现（有实现无文档）")
            lines.append("")
            for d in extras:
                lines.append(f"### {d.diff_id}: {_cell(d.description, 60)}")
                lines.append(f"- **代码侧**: {d.code_side or '--'}")
                suggestion = (
                    d.suggestion_by_code if base == "code" else d.suggestion_by_doc
                )
                if suggestion:
                    lines.append(f"- **建议**: {suggestion[:200]}")
                lines.append("")

        if inconsistencies:
            lines.append("## 文档与代码不一致")
            lines.append("")
            for d in inconsistencies:
                lines.append(f"### {d.diff_id}")
                lines.append(f"- **描述**: {d.description}")
                lines.append(f"- **需求侧**: {d.req_side or '--'}")
                lines.append(f"- **代码侧**: {d.code_side or '--'}")
                if base == "doc" and d.suggestion_by_doc:
                    lines.append(
                        f"- **修正建议(以文档为准)**: {d.suggestion_by_doc[:200]}"
                    )
                elif base == "code" and d.suggestion_by_code:
                    lines.append(
                        f"- **修正建议(以代码为准)**: {d.suggestion_by_code[:200]}"
                    )
                lines.append("")

        if not result.diff_report:
            lines.append("无差异。")
            lines.append("")

        return "\n".join(lines)

    def export_full_report(
        self,
        result: CrossReferenceResult,
        doc_results: Optional[List[DocumentResult]] = None,
        code_result: Optional[SourceCodeResult] = None,
        base: str = "doc",
    ) -> str:
        parts: List[str] = []
        parts.append(
            self.export_trace_matrix(
                result,
                doc_sources=[d.source_file for d in doc_results]
                if doc_results
                else None,
                code_dir=code_result.source_dir if code_result else None,
            )
        )
        parts.append(self.export_coverage_report(result))
        parts.append(self.export_diff_report(result, base=base))
        return "\n".join(parts)

    def export_document_summary(self, doc: DocumentResult) -> str:
        lines: List[str] = []
        lines.append(f"# {doc.title or Path(doc.source_file).name}")
        lines.append("")
        lines.append(f"> Format: {doc.source_format}")
        lines.append(f"> Source: {doc.source_file}")
        lines.append(f"> Sections: {len(doc.sections)}")
        lines.append(f"> Tables: {len(doc.tables)}")
        lines.append(f"> Images: {len(doc.images)}")
        lines.append("")

        if doc.sections:
            lines.append("## Sections")
            lines.append("")
            for sec in doc.sections:
                indent = "  " * (sec.level - 1) if sec.level <= 6 else ""
                lines.append(f"{indent}- **{sec.title}** (L{sec.level})")
                if sec.content:
                    snippet = sec.content[:120].replace("\n", " ")
                    suffix = "..." if len(sec.content) > 120 else ""
                    lines.append(f"{indent}  > {snippet}{suffix}")
            lines.append("")

        if doc.tables:
            lines.append("## Tables")
            lines.append("")
            for i, table in enumerate(doc.tables):
                rows = len(table.rows)
                cols = len(table.headers) if table.headers else 0
                lines.append(f"- Table {i + 1}: {rows} rows x {cols} cols")
            lines.append("")

        return "\n".join(lines)

    def export_source_overview(self, code: SourceCodeResult) -> str:
        lines: List[str] = []
        lines.append("# Source Code Overview")
        lines.append("")
        lines.append(f"> Source: {code.source_dir}")
        lines.append(f"> Modules: {len(code.modules)}")
        total_funcs = sum(len(m.functions) for m in code.modules)
        total_classes = sum(len(m.classes) for m in code.modules)
        lines.append(f"> Functions: {total_funcs}")
        lines.append(f"> Classes: {total_classes}")
        lines.append("")

        if code.structure_tree:
            lines.append("## Directory Structure")
            lines.append("")
            lines.append("```")
            lines.append(code.structure_tree)  # type: ignore[arg-type]
            lines.append("```")
            lines.append("")

        if code.modules:
            lines.append("## Modules")
            lines.append("")
            for mod in code.modules:
                lines.append(f"### {mod.file_path}")
                if mod.module_docstring:
                    lines.append(f"> {mod.module_docstring[:100]}")
                for cls in mod.classes:
                    lines.append(f"- **class {cls.name}** ({len(cls.methods)} methods)")
                for func in mod.functions:
                    params = ", ".join(func.parameters) if func.parameters else ""  # type: ignore[arg-type]
                    lines.append(f"- `{func.name}({params})`")
                lines.append("")

        return "\n".join(lines)


def _cell(text: Optional[str], max_len: int = 30) -> str:
    if not text:
        return "--"
    cleaned = text.replace("|", "\\|").replace("\n", " ")
    if len(cleaned) > max_len:
        return cleaned[: max_len - 3] + "..."
    return cleaned
