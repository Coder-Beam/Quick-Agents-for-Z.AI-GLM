"""
Parser registry and base class for document parsing.

All parsers must inherit from BaseParser and implement the parse() method.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from pathlib import Path
import logging
from datetime import datetime
import hashlib

from ..models import DocumentResult

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """解析器基类"""

    SUPPORTED_FORMATS: List[str] = []
    REQUIRES_DEPENDENCIES: List[str] = []
    PARSER_NAME: str = "base"

    def __init__(self):
        self._deps_available = self._check_dependencies()

    def _check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        for module_name in self.REQUIRES_DEPENDENCIES:
            if module_name == "ast":
                continue
            try:
                __import__(module_name)
            except ImportError:
                logger.warning(
                    f"Parser {self.PARSER_NAME}: missing dependency '{module_name}'"
                )
                return False
        return True

    def is_available(self) -> bool:
        """Check if parser is available (dependencies installed)"""
        return self._deps_available

    def supports_format(self, fmt: str) -> bool:
        """Check if parser supports a given format"""
        return fmt.lower().lstrip(".") in [
            f.lower().lstrip(".") for f in self.SUPPORTED_FORMATS
        ]

    @abstractmethod
    def parse(self, file_path: Path) -> DocumentResult:
        """Parse a file and return DocumentResult"""
        pass

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate file hash"""
        with open(file_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]

    def _extract_metadata(self, file_path: Path) -> Dict:
        """Extract file metadata"""
        stat = file_path.stat()
        return {
            "file_name": file_path.name,
            "file_size": stat.st_size,
            "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "file_hash": self._calculate_file_hash(file_path),
        }

    @classmethod
    def get_supported_formats(cls) -> List[str]:
        """Get supported format list"""
        return cls.SUPPORTED_FORMATS

    @classmethod
    def get_parser_name(cls) -> str:
        """Get parser name"""
        return cls.PARSER_NAME


class ParserRegistry:
    """解析器注册表"""

    def __init__(self):
        self._parsers: Dict[str, BaseParser] = {}
        self._format_mapping: Dict[str, str] = {}

    def register(self, fmt: str, parser: BaseParser) -> None:
        """Register a parser for a format"""
        if not isinstance(parser, BaseParser):
            raise TypeError("Parser must be an instance of BaseParser")
        if not parser.supports_format(fmt):
            raise ValueError(
                f"Parser {parser.__class__.__name__} does not support format: {fmt}"
            )
        self._parsers[parser.PARSER_NAME] = parser
        self._format_mapping[fmt.lower().lstrip(".")] = parser.PARSER_NAME
        logger.info(f"Registered parser for {fmt}: {parser.PARSER_NAME}")

    def get_parser(self, fmt: str) -> Optional[BaseParser]:
        """Get parser for a format"""
        fmt = fmt.lower().lstrip(".")
        parser_name = self._format_mapping.get(fmt)
        if parser_name is None:
            return None
        return self._parsers.get(parser_name)

    def get_supported_formats(self) -> List[str]:
        """Get all supported formats"""
        return list(self._format_mapping.keys())

    def get_all_parsers(self) -> Dict[str, BaseParser]:
        """Get all parsers"""
        return self._parsers.copy()

    def has_parser(self, fmt: str) -> bool:
        """Check if a parser exists for a format"""
        return fmt.lower().lstrip(".") in self._format_mapping

    def clear(self) -> None:
        """Clear all parsers"""
        self._parsers.clear()
        self._format_mapping.clear()


_DEP_MAP = {
    "pdf": ["fitz", "pdfplumber"],
    "docx": ["docx"],
    "doc": ["docx"],
    "xlsx": ["openpyxl"],
    "xls": ["openpyxl"],
    "xmind": ["xmind"],
    "mm": [],
    "opml": [],
    "md": [],
    "py": [],
    "js": ["tree_sitter"],
    "ts": ["tree_sitter"],
    "java": ["tree_sitter"],
    "go": ["tree_sitter"],
    "rs": ["tree_sitter"],
    "c": ["tree_sitter"],
    "cpp": ["tree_sitter"],
}


def check_dependencies(fmt: str) -> bool:
    """Check if dependencies for a format are installed"""
    required = _DEP_MAP.get(fmt.lower().lstrip("."), [])
    if not required:
        return True
    for module_name in required:
        if module_name == "ast":
            continue
        try:
            __import__(module_name)
        except ImportError:
            return False
    return True


def get_missing_dependencies(fmt: str) -> List[str]:
    """Get list of missing dependencies for a format"""
    required = _DEP_MAP.get(fmt.lower().lstrip("."), [])
    if not required:
        return []
    missing = []
    for module_name in required:
        if module_name == "ast":
            continue
        try:
            __import__(module_name)
        except ImportError:
            missing.append(module_name)
    return missing
