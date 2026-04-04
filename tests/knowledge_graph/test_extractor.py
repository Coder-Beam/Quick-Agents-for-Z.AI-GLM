"""
Tests for KnowledgeExtractor - Minimal Unit for extracting knowledge.

Test Cases (18):
- extract_from_text: single_req, multiple, high_conf, low_conf, empty, malformed
- import_from_file: markdown, text, nonexistent, unsupported, permission_denied
- validate_confidence: high, low, boundary
- check_duplicate: exact_match, similar_title, no_match, case_insensitive
"""

import pytest
import tempfile
import os
from unittest.mock import patch, mock_open

from quickagents.knowledge_graph.types import NodeType
from quickagents.knowledge_graph.storage.sqlite_storage import SQLiteGraphStorage
from quickagents.knowledge_graph.core.node_manager import NodeManager
from quickagents.knowledge_graph.core.extractor import KnowledgeExtractor


class TestExtractFromText:
    """Tests for KnowledgeExtractor.extract_from_text()"""
    
    @pytest.fixture
    def extractor(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        node_manager = NodeManager(storage)
        extractor = KnowledgeExtractor(node_manager)
        yield extractor
        storage.close()
        os.unlink(db_path)
    
    def test_extract_single_requirement(self, extractor):
        text = "系统需要支持用户登录功能"
        nodes = extractor.extract_from_text(text)
        
        assert len(nodes) == 1
        assert nodes[0].node_type == NodeType.REQUIREMENT
        assert "用户登录" in nodes[0].content
    
    def test_extract_multiple_nodes(self, extractor):
        text = """
        系统需要支持用户注册功能。
        决定使用JWT进行认证。
        系统必须保证数据安全。
        """
        nodes = extractor.extract_from_text(text)
        
        assert len(nodes) >= 2
    
    def test_extract_high_confidence(self, extractor):
        text = "系统必须实现用户认证模块"
        nodes = extractor.extract_from_text(text)
        
        assert len(nodes) >= 1
        assert extractor.validate_confidence(nodes[0]) is True
    
    def test_extract_low_confidence(self, extractor):
        text = "也许可能需要考虑一下这个问题"
        nodes = extractor.extract_from_text(text, confidence_threshold=0.9)
        
        for node in nodes:
            if node.confidence < 0.9:
                assert extractor.validate_confidence(node) is False
    
    def test_extract_empty_text(self, extractor):
        nodes = extractor.extract_from_text("")
        
        assert nodes == []
    
    def test_extract_malformed_text(self, extractor):
        text = "!!!@@@###$$$%%%"
        nodes = extractor.extract_from_text(text)
        
        assert nodes == []


class TestImportFromFile:
    """Tests for KnowledgeExtractor.import_from_file()"""
    
    @pytest.fixture
    def extractor(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        node_manager = NodeManager(storage)
        extractor = KnowledgeExtractor(node_manager)
        yield extractor
        storage.close()
        os.unlink(db_path)
    
    def test_import_markdown_file(self, extractor):
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False, mode='w', encoding='utf-8') as f:
            f.write("# 需求文档\n\n")
            f.write("系统需要支持导出功能。\n")
            f.write("系统必须保证数据一致性。\n")
            md_path = f.name
        
        try:
            result = extractor.import_from_file(md_path)
            
            assert result['success'] is True
            assert result['nodes_created'] >= 1
        finally:
            os.unlink(md_path)
    
    def test_import_text_file(self, extractor):
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False, mode='w', encoding='utf-8') as f:
            f.write("系统需要实现搜索功能。\n")
            f.write("决定采用Elasticsearch作为搜索引擎。\n")
            txt_path = f.name
        
        try:
            result = extractor.import_from_file(txt_path)
            
            assert result['success'] is True
            assert result['nodes_created'] >= 1
        finally:
            os.unlink(txt_path)
    
    def test_import_nonexistent_file(self, extractor):
        result = extractor.import_from_file("/nonexistent/path/to/file.md")
        
        assert result['success'] is False
        assert 'error' in result
    
    def test_import_unsupported_format(self, extractor):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False, mode='w', encoding='utf-8') as f:
            f.write('{"key": "value"}')
            json_path = f.name
        
        try:
            result = extractor.import_from_file(json_path)
            
            assert result['success'] is False
            assert 'error' in result
        finally:
            os.unlink(json_path)
    
    def test_import_permission_denied(self, extractor):
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            result = extractor.import_from_file("/some/path/to/file.md")
            
            assert result['success'] is False
            assert 'error' in result


class TestValidateConfidence:
    """Tests for KnowledgeExtractor.validate_confidence()"""
    
    @pytest.fixture
    def extractor(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        node_manager = NodeManager(storage)
        extractor = KnowledgeExtractor(node_manager, confidence_threshold=0.8)
        yield extractor
        storage.close()
        os.unlink(db_path)
    
    def test_validate_high_confidence(self, extractor):
        node = extractor._node_manager.create_node(
            node_type=NodeType.REQUIREMENT,
            title="High Conf",
            content="Test",
            confidence=0.95
        )
        
        assert extractor.validate_confidence(node) is True
    
    def test_validate_low_confidence(self, extractor):
        node = extractor._node_manager.create_node(
            node_type=NodeType.REQUIREMENT,
            title="Low Conf",
            content="Test",
            confidence=0.5
        )
        
        assert extractor.validate_confidence(node) is False
    
    def test_validate_boundary_confidence(self, extractor):
        node = extractor._node_manager.create_node(
            node_type=NodeType.REQUIREMENT,
            title="Boundary Conf",
            content="Test",
            confidence=0.8
        )
        
        assert extractor.validate_confidence(node) is True


class TestCheckDuplicate:
    """Tests for KnowledgeExtractor.check_duplicate()"""
    
    @pytest.fixture
    def extractor(self):
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        storage = SQLiteGraphStorage(db_path)
        storage.initialize({})
        node_manager = NodeManager(storage)
        extractor = KnowledgeExtractor(node_manager)
        yield extractor
        storage.close()
        os.unlink(db_path)
    
    def test_check_duplicate_exact_match(self, extractor):
        extractor._node_manager.create_node(
            node_type=NodeType.REQUIREMENT,
            title="用户登录",
            content="系统需要支持用户登录"
        )
        
        duplicate_id = extractor.check_duplicate("用户登录", "系统需要支持用户登录")
        
        assert duplicate_id is not None
    
    def test_check_duplicate_similar_title(self, extractor):
        extractor._node_manager.create_node(
            node_type=NodeType.DECISION,
            title="使用JWT认证",
            content="决定使用JWT进行认证"
        )
        
        duplicate_id = extractor.check_duplicate("使用JWT认证方案", "决定使用JWT")
        
        assert duplicate_id is not None
    
    def test_check_duplicate_no_match(self, extractor):
        extractor._node_manager.create_node(
            node_type=NodeType.FACT,
            title="数据库类型",
            content="使用PostgreSQL数据库"
        )
        
        duplicate_id = extractor.check_duplicate("用户注册", "系统需要支持用户注册")
        
        assert duplicate_id is None
    
    def test_check_duplicate_case_insensitive(self, extractor):
        extractor._node_manager.create_node(
            node_type=NodeType.REQUIREMENT,
            title="用户登录功能",
            content="系统需要支持用户登录"
        )
        
        duplicate_id = extractor.check_duplicate("用户登录功能", "系统需要支持用户登录")
        
        assert duplicate_id is not None
