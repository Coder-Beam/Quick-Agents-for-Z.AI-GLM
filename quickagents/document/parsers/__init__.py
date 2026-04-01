"""
Base parser interface for document parsing.
All parsers must inherit from this class and implement:
the parse() method to return a DocumentResult or SourceCodeResult.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging
from datetime import datetime
import hashlib
import json

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """解析器基类"""
    
    # 支持的文件格式（子类需要覆盖)
    SUPPORTED_FORMATS: List[str] = []
    # 是否需要特定依赖
    REQUIRES_DEPENDENCIES: List[str] = []
    # 解析器名称
    PARSER_NAME: str = "base"
    
    def __init__(self):
        """初始化解析器"""
        self._check_dependencies()
    
    def _check_dependencies(self) -> bool:
        """检查依赖是否安装"""
        pass
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希"""
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
    
    @abstractmethod
    def parse(self, file_path: Path, encoding: str = 'utf-8') -> Dict:
        """
        解析文件
        
        Args:
            file_path: 文件路径
            encoding: 文件编码
            
        Returns:
            解析结果字典，        """
        pass
    
    def _create_result_id(self, file_path: str) -> str:
        """创建结果ID"""
        return f"{Path(file_path).stem}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def _extract_metadata(self, file_path: Path) -> Dict:
        """提取文件元数据"""
        stat = file_path.stat()
        return {
            "file_name": file_path.name,
            "file_size": stat.st_size,
            "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "file_hash": self._calculate_file_hash(file_path),
        }
    
    def _log_parse_start(self, file_path: Path) -> None:
        """记录解析开始"""
        logger.info(f"Starting to parse {file_path} with {self.__class__.__name__}")
    
    def _log_parse_complete(self, file_path: Path, result: Dict) -> None:
        """记录解析完成"""
        logger.info(f"Completed parsing {file_path}: {len(result.get('sections', []))} sections, "
                     f"{len(result.get('tables', []))} tables, "
                     f"{len(result.get('errors', []))} errors")
    
 def get_supported_formats(cls) -> List[str]:
        """获取支持的格式列表"""
        return cls.SUPPORTED_FORMATS
    
    @classmethod
    def get_parser_name(cls) -> str:
        """获取解析器名称"""
        return cls.PARSER_NAME


class ParserRegistry:
    """解析器注册表"""
    
    def __init__(self):
        self._parsers: Dict[str, BaseParser] = {}
        self._format_mapping: Dict[str, str] = {}
    
    def register(self, format: str, parser: BaseParser) -> None:
        """注册解析器"""
        if not isinstance(parser, BaseParser):
            raise TypeError("Parser must be an instance of BaseParser")
        
        if not parser.supports_format(format):
            raise ValueError(f"Parser {parser.__class__.__name__} does not support format: {format}")
        
        self._parsers[parser.PARSER_NAME] = parser
        self._format_mapping[format] = parser.PARSER_NAME
        logger.info(f"Registered parser for {format}: {parser.PARSER_NAME}")
    
    def get_parser(self, format: str) -> Optional[BaseParser]:
        """获取解析器"""
        parser_name = self._format_mapping.get(format)
        if parser_name is None:
            return None
        
        return self._parsers.get(parser_name)
    
    def get_supported_formats(self) -> List[str]:
        """获取所有支持的格式"""
        return list(self._format_mapping.keys())
    
    def get_all_parsers(self) -> Dict[str, BaseParser]:
        """获取所有解析器"""
        return self._parsers.copy()
    
    def has_parser(self, format: str) -> bool:
        """检查是否有指定格式的解析器"""
        return format in self._format_mapping
    
    def clear(self) -> None:
        """清空所有解析器"""
        self._parsers.clear()
        self._format_mapping.clear()


def check_dependencies(format: str) -> bool:
    """
    检查处理指定格式所需的依赖是否已安装
    
    Args:
        format: 文档格式 (pdf/docx/xlsx等)
        
    Returns:
        True: 依赖已安装
        False: 依赖未安装
    """
    # 文档格式依赖映射
    doc_deps = {
        "pdf": ["fitz", "pdfplumber"],
        "docx": ["docx"],
        "doc": ["docx"],  # doc 和 docx 使用相同的库
 "xlsx": ["openpyxl"],
        "xls": ["openpyxl"],  # xls 和 xlsx 使用相同的库
        "xmind": ["xmind"],
        "mm": [],  # FreeMind 使用标准库
        "opml": [],  # OPML 使用标准库
        "md": [],  # Markdown 使用标准库
    }
    
    # 源码格式依赖映射
    source_deps = {
        "py": ["ast"],  # Python 使用标准库
        "js": ["tree_sitter"],
        "ts": ["tree_sitter"],
        "java": ["tree_sitter"],
        "go": ["tree_sitter"],
        "rs": ["tree_sitter"],
        "c": ["tree_sitter"],
        "cpp": ["tree_sitter"],
    }
    
    # 合并依赖映射
    all_deps = {**doc_deps, **source_deps}
    
    required_modules = all_deps.get(format, [])
    if not required_modules:
        return True  # 无需外部依赖
    
 return False
    
    # 检查每个依赖
    missing_modules = []
    for module_name in required_modules:
        if module_name == "ast":
            continue  # 标准库， always available
        
        try:
            __import__(module_name)
        except ImportError:
            missing_modules.append(module_name)
    
    if missing_modules:
        logger.warning(f"Missing dependencies for {format}: {missing_modules}")
        return False
    
    return True


def get_missing_dependencies(format: str) -> List[str]:
    """
    获取缺失的依赖列表
    
    Args:
        format: 文档格式
        
    Returns:
        缺失的依赖列表
    """
    doc_deps = {
        "pdf": ["fitz", "pdfplumber"],
        "docx": ["docx"],
        "doc": ["docx"],
        "xlsx": ["openpyxl"],
        "xls": ["openpyxl"],
        "xmind": ["xmind"],
        "mm": [],
        "opml": [],
        "md": [],
    }
    
    source_deps = {
        "py": ["ast"],
        "js": ["tree_sitter"],
        "ts": ["tree_sitter"],
        "java": ["tree_sitter"],
        "go": ["tree_sitter"],
        "rs": ["tree_sitter"],
        "c": ["tree_sitter"],
        "cpp": ["tree_sitter"],
    }
    
    all_deps = {**doc_deps, **source_deps}
    required_modules = all_deps.get(format, [])
    
    if not required_modules:
        return []
    
    missing = []
    for module_name in required_modules:
        if module_name == "ast":
                continue  # 标准库
            try:
                __import__(module_name)
            except ImportError:
                missing.append(module_name)
    
    return missing
