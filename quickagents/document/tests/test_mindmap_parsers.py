"""
Phase 3 Tests - Mind Map Parsers (XMind, FreeMind, OPML, Markdown)

T014-T018: Test all four mind map/outline parsers.
"""

import unittest
from pathlib import Path
import tempfile

from quickagents.document.parsers.xmind_parser import XMindParser
from quickagents.document.parsers.freemind_parser import FreeMindParser
from quickagents.document.parsers.opml_parser import OPMLParser
from quickagents.document.parsers.markdown_parser import MarkdownParser
from quickagents.document.models import DocumentResult

FIXTURES = Path(__file__).parent / "fixtures"


class TestXMindParser(unittest.TestCase):
    """T014: XMind parser"""

    @classmethod
    def setUpClass(cls):
        cls.parser = XMindParser()
        cls.sample = FIXTURES / "test_sample.xmind"
        cls.result = cls.parser.parse(cls.sample)

    def test_availability(self):
        self.assertTrue(self.parser.is_available())

    def test_parser_name(self):
        self.assertEqual(self.parser.PARSER_NAME, "xmind")

    def test_is_document_result(self):
        self.assertIsInstance(self.result, DocumentResult)

    def test_source_format(self):
        self.assertEqual(self.result.source_format, "xmind")

    def test_title(self):
        self.assertIsNotNone(self.result.title)

    def test_sections_detected(self):
        self.assertGreater(len(self.result.sections), 0)

    def test_section_hierarchy(self):
        levels = [s.level for s in self.result.sections]
        self.assertIn(1, levels)

    def test_parent_child_consistency(self):
        ids = {s.section_id for s in self.result.sections}
        for sec in self.result.sections:
            if sec.parent_id:
                self.assertIn(sec.parent_id, ids)

    def test_structure_tree(self):
        self.assertIsInstance(self.result.structure_tree, dict)
        if self.result.structure_tree.get("children"):
            self.assertGreater(len(self.result.structure_tree["children"]), 0)

    def test_raw_text_not_empty(self):
        self.assertTrue(len(self.result.raw_text) > 0)

    def test_contains_architecture(self):
        self.assertIn("Architecture", self.result.raw_text)

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            self.parser.parse(Path("nonexistent.xmind"))

    def test_to_dict(self):
        d = self.result.to_dict()
        self.assertEqual(d["source_format"], "xmind")


class TestFreeMindParser(unittest.TestCase):
    """T015: FreeMind .mm parser"""

    @classmethod
    def setUpClass(cls):
        cls.parser = FreeMindParser()
        cls.sample = FIXTURES / "test_sample.mm"
        cls.result = cls.parser.parse(cls.sample)

    def test_availability(self):
        self.assertTrue(self.parser.is_available())

    def test_parser_name(self):
        self.assertEqual(self.parser.PARSER_NAME, "freemind")

    def test_is_document_result(self):
        self.assertIsInstance(self.result, DocumentResult)

    def test_source_format(self):
        self.assertEqual(self.result.source_format, "mm")

    def test_sections_detected(self):
        self.assertGreater(len(self.result.sections), 0)

    def test_root_title(self):
        self.assertEqual(self.result.title, "Project Architecture")

    def test_nested_structure(self):
        levels = [s.level for s in self.result.sections]
        self.assertTrue(max(levels) >= 2, "Should have nested levels")

    def test_parent_child_consistency(self):
        ids = {s.section_id for s in self.result.sections}
        for sec in self.result.sections:
            if sec.parent_id:
                self.assertIn(sec.parent_id, ids)

    def test_raw_text_contains_backend(self):
        self.assertIn("Backend", self.result.raw_text)

    def test_structure_tree(self):
        tree = self.result.structure_tree
        self.assertIsInstance(tree, dict)

    def test_no_errors(self):
        self.assertEqual(len(self.result.errors), 0)

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            self.parser.parse(Path("nonexistent.mm"))

    def test_to_dict_roundtrip(self):
        d = self.result.to_dict()
        self.assertIn("sections", d)
        self.assertEqual(d["source_format"], "mm")


class TestOPMLParser(unittest.TestCase):
    """T016: OPML parser"""

    @classmethod
    def setUpClass(cls):
        cls.parser = OPMLParser()
        cls.sample = FIXTURES / "test_sample.opml"
        cls.result = cls.parser.parse(cls.sample)

    def test_availability(self):
        self.assertTrue(self.parser.is_available())

    def test_parser_name(self):
        self.assertEqual(self.parser.PARSER_NAME, "opml")

    def test_is_document_result(self):
        self.assertIsInstance(self.result, DocumentResult)

    def test_source_format(self):
        self.assertEqual(self.result.source_format, "opml")

    def test_title_from_head(self):
        self.assertEqual(self.result.title, "Project Requirements")

    def test_sections_detected(self):
        self.assertGreater(len(self.result.sections), 0)

    def test_nested_structure(self):
        levels = [s.level for s in self.result.sections]
        self.assertTrue(max(levels) >= 2)

    def test_notes_extracted(self):
        has_content = any(s.content for s in self.result.sections)
        self.assertTrue(has_content, "Some sections should have note content")

    def test_raw_text_not_empty(self):
        self.assertTrue(len(self.result.raw_text) > 0)

    def test_contains_authentication(self):
        self.assertIn("Authentication", self.result.raw_text)

    def test_structure_tree(self):
        self.assertIsInstance(self.result.structure_tree, dict)

    def test_parent_child_consistency(self):
        ids = {s.section_id for s in self.result.sections}
        for sec in self.result.sections:
            if sec.parent_id:
                self.assertIn(sec.parent_id, ids)

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            self.parser.parse(Path("nonexistent.opml"))


class TestMarkdownParser(unittest.TestCase):
    """T017: Markdown outline parser"""

    @classmethod
    def setUpClass(cls):
        cls.parser = MarkdownParser()
        cls.sample = FIXTURES / "test_sample.md"
        cls.result = cls.parser.parse(cls.sample)

    def test_availability(self):
        self.assertTrue(self.parser.is_available())

    def test_parser_name(self):
        self.assertEqual(self.parser.PARSER_NAME, "markdown")

    def test_is_document_result(self):
        self.assertIsInstance(self.result, DocumentResult)

    def test_source_format(self):
        self.assertEqual(self.result.source_format, "md")

    def test_title_from_h1(self):
        self.assertEqual(self.result.title, "Project Architecture")

    def test_sections_detected(self):
        self.assertGreater(len(self.result.sections), 0)

    def test_heading_levels(self):
        levels = {s.level for s in self.result.sections}
        self.assertIn(1, levels)
        self.assertIn(2, levels)
        self.assertIn(3, levels)

    def test_section_content_populated(self):
        has_content = any(s.content for s in self.result.sections)
        self.assertTrue(has_content, "Sections should have content")

    def test_paragraphs_extracted(self):
        self.assertGreater(len(self.result.paragraphs), 0)

    def test_raw_text_is_full_content(self):
        self.assertIn("Vue.js", self.result.raw_text)

    def test_parent_child_consistency(self):
        ids = {s.section_id for s in self.result.sections}
        for sec in self.result.sections:
            if sec.parent_id:
                self.assertIn(sec.parent_id, ids)

    def test_structure_tree(self):
        tree = self.result.structure_tree
        self.assertIsInstance(tree, dict)

    def test_no_errors(self):
        self.assertEqual(len(self.result.errors), 0)

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            self.parser.parse(Path("nonexistent.md"))

    def test_empty_markdown(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "empty.md"
            f.write_text("")
            result = self.parser.parse(f)
            self.assertIsInstance(result, DocumentResult)
            self.assertEqual(len(result.sections), 0)

    def test_single_heading(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "single.md"
            f.write_text("# Only Heading\n\nSome text.")
            result = self.parser.parse(f)
            self.assertEqual(len(result.sections), 1)
            self.assertEqual(result.sections[0].title, "Only Heading")

    def test_deep_nesting(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "deep.md"
            f.write_text(
                "# L1\n## L2\n### L3\n#### L4\n##### L5\n###### L6\n"
            )
            result = self.parser.parse(f)
            self.assertEqual(len(result.sections), 6)
            levels = [s.level for s in result.sections]
            self.assertEqual(levels, [1, 2, 3, 4, 5, 6])


class TestCrossParserConsistency(unittest.TestCase):
    """Cross-parser consistency checks"""

    def test_all_parsers_return_document_result(self):
        parsers_and_files = [
            (XMindParser(), FIXTURES / "test_sample.xmind"),
            (FreeMindParser(), FIXTURES / "test_sample.mm"),
            (OPMLParser(), FIXTURES / "test_sample.opml"),
            (MarkdownParser(), FIXTURES / "test_sample.md"),
        ]
        for parser, path in parsers_and_files:
            with self.subTest(parser=parser.PARSER_NAME):
                result = parser.parse(path)
                self.assertIsInstance(result, DocumentResult)
                self.assertEqual(result.errors, [])
                self.assertIsInstance(result.structure_tree, dict)
                self.assertIsInstance(result.sections, list)
                self.assertIsInstance(result.raw_text, str)


if __name__ == "__main__":
    unittest.main()
