"""
Knowledge Extractor - Minimal Unit

Extracts knowledge from text and files using pattern matching.
"""

import os
import re
from typing import List, Dict, Any, Optional

from ..types import NodeType, KnowledgeNode
from .node_manager import NodeManager


class KnowledgeExtractor:
    """
    Knowledge Extractor - Minimal Unit for extracting knowledge.
    
    Extracts knowledge from text using pattern matching and imports from files.
    """
    
    REQUIREMENT_PATTERNS = [
        r'系统需要(.+)',
        r'系统应(.+)',
        r'必须(.+)',
        r'需要(.+)',
        r'应当(.+)',
        r'支持(.+功能)',
    ]
    
    DECISION_PATTERNS = [
        r'决定(.+)',
        r'选择(.+)',
        r'采用(.+)',
        r'使用(.+作为.+)',
    ]
    
    FACT_PATTERNS = [
        r'是(.+)',
        r'有(.+)',
        r'存在(.+)',
        r'包含(.+)',
    ]
    
    def __init__(self, node_manager: NodeManager, confidence_threshold: float = 0.8):
        """
        Initialize KnowledgeExtractor.
        
        Args:
            node_manager: NodeManager instance for creating nodes
            confidence_threshold: Minimum confidence threshold (default 0.8)
        """
        self._node_manager = node_manager
        self._confidence_threshold = confidence_threshold
    
    def extract_from_text(
        self,
        text: str,
        source_type: str = "discussion",
        **kwargs
    ) -> List[KnowledgeNode]:
        """
        Extract knowledge from text using pattern matching.
        
        Args:
            text: Text to extract knowledge from
            source_type: Type of source (discussion, document, etc.)
            **kwargs: Additional arguments (confidence_threshold, etc.)
            
        Returns:
            List of extracted KnowledgeNode objects
        """
        if not text or not text.strip():
            return []
        
        threshold = kwargs.get('confidence_threshold', self._confidence_threshold)
        nodes: List[KnowledgeNode] = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            extracted = self._extract_from_line(line, source_type, threshold, kwargs)
            nodes.extend(extracted)
        
        return nodes
    
    def _extract_from_line(
        self,
        line: str,
        source_type: str,
        threshold: float,
        kwargs: Dict[str, Any]
    ) -> List[KnowledgeNode]:
        """Extract knowledge from a single line."""
        nodes: List[KnowledgeNode] = []
        
        requirement_node = self._try_extract_type(
            line, NodeType.REQUIREMENT, self.REQUIREMENT_PATTERNS,
            source_type, threshold, kwargs
        )
        if requirement_node:
            nodes.append(requirement_node)
        
        decision_node = self._try_extract_type(
            line, NodeType.DECISION, self.DECISION_PATTERNS,
            source_type, threshold, kwargs
        )
        if decision_node:
            nodes.append(decision_node)
        
        fact_node = self._try_extract_type(
            line, NodeType.FACT, self.FACT_PATTERNS,
            source_type, threshold, kwargs
        )
        if fact_node:
            nodes.append(fact_node)
        
        return nodes
    
    def _try_extract_type(
        self,
        line: str,
        node_type: NodeType,
        patterns: List[str],
        source_type: str,
        threshold: float,
        kwargs: Dict[str, Any]
    ) -> Optional[KnowledgeNode]:
        """Try to extract a specific node type from a line."""
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                content = match.group(1).strip()
                if not content:
                    continue
                
                confidence = self._calculate_confidence(line, pattern)
                
                if confidence < threshold:
                    continue
                
                title = self._generate_title(content, node_type)
                
                node = self._node_manager.create_node(
                    node_type=node_type,
                    title=title,
                    content=content,
                    source_type=source_type,
                    confidence=confidence,
                    **{k: v for k, v in kwargs.items() if k != 'confidence_threshold'}
                )
                
                return node
        
        return None
    
    def _calculate_confidence(self, line: str, pattern: str) -> float:
        """Calculate confidence score for extracted knowledge."""
        match = re.search(pattern, line)
        if not match:
            return 0.0
        
        content = match.group(1).strip()
        
        if len(content) < 3:
            return 0.5
        
        strong_keywords = ['必须', '一定', '确定', '明确', '决定']
        weak_keywords = ['可能', '也许', '或许', '考虑', '大概']
        
        confidence = 0.8
        
        for keyword in strong_keywords:
            if keyword in line:
                confidence = min(1.0, confidence + 0.1)
        
        for keyword in weak_keywords:
            if keyword in line:
                confidence = max(0.5, confidence - 0.2)
        
        return round(confidence, 2)
    
    def _generate_title(self, content: str, node_type: NodeType) -> str:
        """Generate a title from content."""
        if len(content) <= 20:
            return content
        
        return content[:20] + "..."
    
    def import_from_file(
        self,
        file_path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Import knowledge from file.
        
        Args:
            file_path: Path to file to import
            **kwargs: Additional arguments
            
        Returns:
            Dict with success, nodes_created, and optional error
        """
        if not os.path.exists(file_path):
            return {
                'success': False,
                'nodes_created': 0,
                'error': f'File not found: {file_path}'
            }
        
        _, ext = os.path.splitext(file_path.lower())
        supported_extensions = ['.md', '.txt']
        
        if ext not in supported_extensions:
            return {
                'success': False,
                'nodes_created': 0,
                'error': f'Unsupported file format: {ext}'
            }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except PermissionError:
            return {
                'success': False,
                'nodes_created': 0,
                'error': f'Permission denied: {file_path}'
            }
        except Exception as e:
            return {
                'success': False,
                'nodes_created': 0,
                'error': str(e)
            }
        
        source_type = 'file'
        source_uri = f'file:///{file_path.replace(os.sep, "/")}'
        
        nodes = self.extract_from_text(
            content,
            source_type=source_type,
            source_uri=source_uri,
            **kwargs
        )
        
        return {
            'success': True,
            'nodes_created': len(nodes),
            'nodes': [n.id for n in nodes]
        }
    
    def validate_confidence(self, node: KnowledgeNode) -> bool:
        """
        Validate node confidence against threshold.
        
        Args:
            node: KnowledgeNode to validate
            
        Returns:
            True if confidence >= threshold, False otherwise
        """
        return node.confidence >= self._confidence_threshold
    
    def check_duplicate(self, title: str, content: str) -> Optional[str]:
        """
        Check for duplicate node by title/content similarity.
        
        Args:
            title: Title to check
            content: Content to check
            
        Returns:
            Node ID if duplicate found, None otherwise
        """
        nodes = self._node_manager.list_nodes(limit=1000)
        
        for node in nodes:
            if self._is_similar(title, content, node):
                return node.id
        
        return None
    
    def _is_similar(self, title: str, content: str, node: KnowledgeNode) -> bool:
        """Check if title/content is similar to existing node."""
        title_lower = title.lower().strip()
        node_title_lower = node.title.lower().strip()
        
        if title_lower == node_title_lower:
            return True
        
        if title_lower in node_title_lower or node_title_lower in title_lower:
            return True
        
        content_lower = content.lower().strip()
        node_content_lower = node.content.lower().strip()
        
        if content_lower and node_content_lower:
            if content_lower == node_content_lower:
                return True
            
            similarity = self._calculate_similarity(content_lower, node_content_lower)
            if similarity > 0.8:
                return True
        
        return False
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple similarity between two texts."""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1)
        words2 = set(text2)
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
