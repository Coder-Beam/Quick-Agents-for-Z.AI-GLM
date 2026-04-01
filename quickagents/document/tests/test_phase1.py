"""
Phase 1 Tests - Document Pipeline core functionality.

Tests pipeline initialization, parser registry, PALs directory handling.
"""

import unittest
from pathlib import Path
import tempfile
import shutil

from quickagents.document.pipeline import DocumentPipeline
from quickagents.document.models import DocumentResult
from quickagents.document.parsers import ParserRegistry, BaseParser


class MockParser(BaseParser):
    """Mock parser for testing"""
    SUPPORTED_FORMATS = ["md"]
    PARSER_NAME = "mock_md"

    def parse(self, file_path: Path) -> DocumentResult:
        return DocumentResult(
            source_file=str(file_path),
            source_format="md",
            title="Mock Title",
            raw_text="Mock content",
        )


class TestPipelineInit(unittest.TestCase):
    def test_pipeline_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = DocumentPipeline(tmpdir)
            self.assertEqual(pipeline.project_root, Path(tmpdir))

    def test_registry_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = DocumentPipeline(tmpdir)
            self.assertIsInstance(pipeline.registry, ParserRegistry)


class TestParserRegistry(unittest.TestCase):
    def test_register_and_get(self):
        registry = ParserRegistry()
        parser = MockParser()
        registry.register("md", parser)

        result = registry.get_parser("md")
        self.assertIs(result, parser)

    def test_get_unknown_format(self):
        registry = ParserRegistry()
        self.assertIsNone(registry.get_parser("pdf"))

    def test_has_parser(self):
        registry = ParserRegistry()
        parser = MockParser()
        registry.register("md", parser)
        self.assertTrue(registry.has_parser("md"))
        self.assertFalse(registry.has_parser("pdf"))

    def test_supported_formats(self):
        registry = ParserRegistry()
        parser = MockParser()
        registry.register("md", parser)
        self.assertIn("md", registry.get_supported_formats())


class TestPalsDirectory(unittest.TestCase):
    def test_ensure_pals_dir_creates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = DocumentPipeline(tmpdir)
            pals = Path(tmpdir) / "PALs"
            result = pipeline.ensure_pals_dir(str(pals))
            self.assertTrue(result.exists())

    def test_ensure_pals_dir_existing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = DocumentPipeline(tmpdir)
            pals = Path(tmpdir) / "PALs"
            pals.mkdir()
            result = pipeline.ensure_pals_dir(str(pals))
            self.assertTrue(result.exists())

    def test_get_pals_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = DocumentPipeline(tmpdir)
            expected = Path(tmpdir) / "PALs"
            self.assertEqual(pipeline.get_pals_dir(), expected)


class TestScanFiles(unittest.TestCase):
    def test_scan_mixed_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = DocumentPipeline(tmpdir)
            pals = Path(tmpdir) / "PALs"
            pals.mkdir()
            (pals / "doc1.pdf").write_text("pdf")
            (pals / "notes.md").write_text("# Notes")
            (pals / "data.xlsx").write_text("xlsx")

            doc_files, source_files = pipeline._scan_files(str(pals), False)
            self.assertEqual(len(doc_files), 3)
            self.assertEqual(len(source_files), 0)

    def test_scan_with_source(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = DocumentPipeline(tmpdir)
            pals = Path(tmpdir) / "PALs"
            src = pals / "SourceReference"
            src.mkdir(parents=True)
            (pals / "req.pdf").write_text("pdf")
            (src / "main.py").write_text("print('hello')")

            doc_files, source_files = pipeline._scan_files(str(pals), True)
            self.assertGreaterEqual(len(doc_files), 1)
            self.assertGreaterEqual(len(source_files), 1)


class TestParseWithRegistry(unittest.TestCase):
    def test_parse_with_mock(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = DocumentPipeline(tmpdir)
            parser = MockParser()
            pipeline.registry.register("md", parser)

            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("# Test")

            result = pipeline.parse(test_file)
            self.assertEqual(result.source_format, "md")

    def test_parse_unsupported_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = DocumentPipeline(tmpdir)
            test_file = Path(tmpdir) / "test.xyz"
            test_file.write_text("data")

            with self.assertRaises(ValueError):
                pipeline.parse(test_file)

    def test_parse_batch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = DocumentPipeline(tmpdir)
            parser = MockParser()
            pipeline.registry.register("md", parser)

            files = []
            for i in range(3):
                f = Path(tmpdir) / f"test{i}.md"
                f.write_text(f"content {i}")
                files.append(f)

            results = pipeline.parse_batch(files)
            self.assertEqual(len(results), 3)


if __name__ == "__main__":
    unittest.main()
