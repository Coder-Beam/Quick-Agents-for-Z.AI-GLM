"""
Phase 2 Tests - PDF Parser

Tests PDF text extraction, section detection, table extraction,
image extraction, and DocumentResult conversion.
"""

import unittest
from pathlib import Path
import tempfile

from quickagents.document.parsers.pdf_parser import PDFParser
from quickagents.document.models import DocumentResult

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_PDF = FIXTURES_DIR / "test_sample.pdf"


class TestPDFParserInit(unittest.TestCase):
    def test_parser_availability(self):
        parser = PDFParser()
        self.assertTrue(parser.is_available())

    def test_supported_formats(self):
        parser = PDFParser()
        self.assertTrue(parser.supports_format("pdf"))
        self.assertFalse(parser.supports_format("docx"))

    def test_parser_name(self):
        self.assertEqual(PDFParser.PARSER_NAME, "pdf")


class TestPDFTextExtraction(unittest.TestCase):
    """T008: PDF text extraction"""

    @classmethod
    def setUpClass(cls):
        cls.parser = PDFParser()
        cls.result = cls.parser.parse(SAMPLE_PDF)

    def test_raw_text_not_empty(self):
        self.assertTrue(len(self.result.raw_text) > 0)

    def test_raw_text_contains_keywords(self):
        self.assertIn("JWT", self.result.raw_text)
        self.assertIn("Authentication", self.result.raw_text)

    def test_paragraphs_extracted(self):
        self.assertTrue(len(self.result.paragraphs) > 0)

    def test_source_format_is_pdf(self):
        self.assertEqual(self.result.source_format, "pdf")

    def test_title_extracted(self):
        self.assertIsNotNone(self.result.title)


class TestPDFSectionDetection(unittest.TestCase):
    """T009: PDF section structure detection"""

    @classmethod
    def setUpClass(cls):
        cls.parser = PDFParser()
        cls.result = cls.parser.parse(SAMPLE_PDF)

    def test_sections_detected(self):
        self.assertTrue(len(self.result.sections) > 0)

    def test_section_levels(self):
        for sec in self.result.sections:
            self.assertGreaterEqual(sec.level, 1)
            self.assertLessEqual(sec.level, 6)

    def test_section_ids_unique(self):
        ids = [s.section_id for s in self.result.sections]
        self.assertEqual(len(ids), len(set(ids)))

    def test_section_page_numbers_valid(self):
        for sec in self.result.sections:
            self.assertGreater(sec.page_number, 0)

    def test_parent_child_consistency(self):
        section_map = {s.section_id: s for s in self.result.sections}
        for sec in self.result.sections:
            if sec.parent_id:
                self.assertIn(sec.parent_id, section_map)
                parent = section_map[sec.parent_id]
                self.assertLess(parent.level, sec.level)


class TestPDFTableExtraction(unittest.TestCase):
    """T010: PDF table extraction"""

    @classmethod
    def setUpClass(cls):
        cls.parser = PDFParser()

    def test_no_crash_on_no_tables(self):
        result = self.parser.parse(SAMPLE_PDF)
        self.assertIsInstance(result.tables, list)

    def test_table_structure_if_found(self):
        result = self.parser.parse(SAMPLE_PDF)
        for table in result.tables:
            self.assertTrue(hasattr(table, "table_id"))
            self.assertTrue(hasattr(table, "headers"))
            self.assertTrue(hasattr(table, "rows"))
            self.assertGreater(table.page_number, 0)


class TestPDFImageExtraction(unittest.TestCase):
    """T011: PDF image extraction"""

    @classmethod
    def setUpClass(cls):
        cls.parser = PDFParser()
        cls.result = cls.parser.parse(SAMPLE_PDF)

    def test_images_is_list(self):
        self.assertIsInstance(self.result.images, list)

    def test_image_structure_if_found(self):
        for img in self.result.images:
            self.assertTrue(hasattr(img, "image_id"))
            self.assertTrue(hasattr(img, "image_type"))
            self.assertGreater(img.page_number, 0)


class TestPDFDocumentResult(unittest.TestCase):
    """T012: PDF -> DocumentResult conversion"""

    @classmethod
    def setUpClass(cls):
        cls.parser = PDFParser()
        cls.result = cls.parser.parse(SAMPLE_PDF)

    def test_is_document_result(self):
        self.assertIsInstance(self.result, DocumentResult)

    def test_no_errors(self):
        self.assertEqual(
            len(self.result.errors), 0, f"Unexpected errors: {self.result.errors}"
        )

    def test_metadata_present(self):
        self.assertIn("page_count", self.result.metadata)
        self.assertEqual(self.result.metadata["page_count"], 3)

    def test_structure_tree_built(self):
        self.assertIsInstance(self.result.structure_tree, dict)

    def test_has_source_file(self):
        self.assertEqual(self.result.source_file, str(SAMPLE_PDF))

    def test_get_hash(self):
        h = self.result.get_hash()
        self.assertEqual(len(h), 16)

    def test_to_dict_roundtrip(self):
        d = self.result.to_dict()
        self.assertIn("source_file", d)
        self.assertIn("sections", d)
        self.assertIn("tables", d)
        self.assertEqual(d["source_format"], "pdf")


class TestPDFParserEdgeCases(unittest.TestCase):
    """Edge case tests"""

    def test_file_not_found(self):
        parser = PDFParser()
        with self.assertRaises(FileNotFoundError):
            parser.parse(Path("nonexistent.pdf"))

    def test_empty_pdf(self):
        import fitz

        with tempfile.TemporaryDirectory() as tmpdir:
            empty_path = Path(tmpdir) / "empty.pdf"
            doc = fitz.open()
            doc.new_page()
            doc.save(str(empty_path))
            doc.close()

            parser = PDFParser()
            result = parser.parse(empty_path)
            self.assertIsInstance(result, DocumentResult)
            self.assertEqual(len(result.sections), 0)
            self.assertEqual(result.raw_text.strip(), "")

    def test_single_page_pdf(self):
        import fitz

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "single.pdf"
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((72, 100), "Just a single page with text.", fontsize=12)
            doc.save(str(path))
            doc.close()

            parser = PDFParser()
            result = parser.parse(path)
            self.assertEqual(result.metadata["page_count"], 1)
            self.assertIn("single page", result.raw_text.lower())


class TestPDFTableWithPdfplumber(unittest.TestCase):
    """Test table extraction with pdfplumber fallback"""

    def test_table_with_real_table(self):
        import fitz

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "table_test.pdf"
            doc = fitz.open()
            page = doc.new_page()

            page.insert_text((72, 50), "Test Table", fontsize=16)

            table_data = [
                ["ID", "Name", "Value"],
                ["1", "Alpha", "100"],
                ["2", "Beta", "200"],
                ["3", "Gamma", "300"],
            ]
            y = 90
            for row in table_data:
                text = "  ".join(f"{c:<12}" for c in row)
                page.insert_text((72, y), text, fontsize=10)
                y += 16

            doc.save(str(path))
            doc.close()

            parser = PDFParser()
            result = parser.parse(path)
            self.assertIsInstance(result, DocumentResult)


if __name__ == "__main__":
    unittest.main()
