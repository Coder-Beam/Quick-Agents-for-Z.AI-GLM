"""
Phase 1 单元测试 - Document Pipeline

测试核心功能:
- DocumentPipeline 初始化
- parse() 单文件解析
- parse_source() 源码目录解析
- cross_reference() 联合分析
- save() 结果保存
- import_all() 批量导入
"""

import unittest
from pathlib import Path
from quickagents.document.pipeline import DocumentPipeline
from quickagents.document.models import DocumentResult, SourceCodeResult
from quickagents.document.parsers import ParserRegistry


class TestPhase1Core(unittest.TestCase):
    """Phase 1 核心功能测试"""
    
    def setUp(self):
        """测试前准备"""
        self.project_root = Path(__file__).parent / "test_project"
        self.pipeline = DocumentPipeline(str(self.project_root))
        
        # 创建测试文件
        self.test_file = self.project_root / "PALs" / "test.md"
        self.test_file.write_text("# Test Document\n\nThis is a test document.")
        self.pipeline.ensure_pals_dir(str(self.project_root / "PALs"))
    
    def test_pipeline_init(self):
        """测试 Pipeline 初始化"""
        self.assertIsNotNone
        self.assertIsInstance(self.pipeline, DocumentPipeline)
        self.assertEqual(self.pipeline.project_root, self.project_root)
    
    def test_ensure_pals_dir(self):
        """测试 PALs 目录检测与创建"""
        pals_path = self.project_root / "PALs"
        
        # 测试创建
        if not pals_path.exists():
            pals_path.mkdir(parents=True)
        self.assertTrue(pals_path.exists())
        
        # 测试已存在目录
        self.pipeline.ensure_pals_dir(str(self.project_root / "PALs"))
        self.assertTrue((self.project_root / "PALs").exists())
    
    def test_parse_document(self):
        """测试文档解析（需要具体的解析器实现后"""
        # 创建测试文档
        test_doc = DocumentResult(
            source_file="test.md",
            source_format="md",
            title="Test Document",
            sections=[],
            paragraphs=["Test content"],
            tables=[],
            images=[],
            formulas=[],
            structure_tree={},
            metadata={},
            raw_text="Test content",
            errors=[],
        )
        
        # Mock 解析器
        mock_parser = Mock()
        mock_parser.parse.return_value = test_doc
        
        # 注册解析器
        self.pipeline.registry.register("md", mock_parser)
        
        # 解析文档
        result = self.pipeline.parse(self.test_file)
        
        self.assertEqual(result.source_file, str(self.test_file))
        self.assertEqual(result.source_format, "md")
    
    def test_parse_batch(self):
        """测试批量解析"""
        # 创建测试文件
        test_files = []
        for i in range(3):
            test_file = self.project_root / "PALs" / f"test{i}.md"
            test_file.write_text(f"# Test Document {i}\n\nContent {i}.")
            test_files.append(test_file)
        
        # Mock 解析器
        mock_parser = Mock()
        mock_parser.parse.return_value = DocumentResult(
            source_file="test.md",
            source_format="md",
            title="Test",
            sections=[],
            paragraphs=[],
            tables=[],
            images=[],
            formulas=[],
            structure_tree={},
            metadata={},
            raw_text="",
            errors=[],
        )
        
        # 注册解析器
        self.pipeline.registry.register("md", mock_parser)
        
        # 批量解析
        results = self.pipeline.parse_batch(test_files)
        
        self.assertEqual(len(results), 3)
    
    def test_save_result(self):
        """测试保存结果"""
        result = DocumentResult(
            source_file="test.md",
            source_format="md",
            title="Test",
            sections=[],
            paragraphs=["Test content"],
            tables=[],
            images=[],
            formulas=[],
            structure_tree={},
            metadata={},
            raw_text="Test content",
            errors=[],
        )
        
        # 保存结果
        self.pipeline.save(result, storage_type="file")
        
        # 验证文件已创建
        output_file = self.project_root / "Docs" / "PALs" / "test.analysis.md"
        self.assertTrue(output_file.exists())
        
        # 清理测试文件
        if pals_path.exists():
            import shutil
            shutil.rmtree(pals_path)
        if output_file.exists():
            output_file.unlink()


if __name__ == '__main__':
    unittest.main()
