"""
Smart Editor Utilities - 智能编辑辅助工具

提供智能编辑功能，解决常见的edit工具失败问题
"""

import os
import re
from typing import Dict, Optional
from difflib import SequenceMatcher


def smart_edit(file_path: str, old_str: str, new_str: str,
               ignore_whitespace: bool = True,
               ignore_line_endings: bool = True) -> Dict:
    """
    智能编辑文件
    
    自动处理:
    - 编辑前强制重新读取
    - 空白字符差异
    - 行尾符差异
    - 提供详细错误诊断
    
    Args:
        file_path: 文件路径
        old_str: 要替换的内容
        new_str: 替换后的内容
        ignore_whitespace: 是否忽略空白差异
        ignore_line_endings: 是否忽略行尾差异
        
    Returns:
        {
            'success': bool,
            'message': str,
            'diagnosis': str,
            'suggestion': str
        }
    """
    from ..utils.encoding import read_file_utf8, write_file_utf8
    
    # 强制重新读取
    try:
        content = read_file_utf8(file_path)
    except Exception as e:
        return {
            'success': False,
            'message': f'读取文件失败: {e}',
            'diagnosis': str(e),
            'suggestion': '检查文件路径是否正确'
        }
    
    # 尝试精确匹配
    if old_str in content:
        new_content = content.replace(old_str, new_str, 1)
        write_file_utf8(file_path, new_content)
        return {
            'success': True,
            'message': '编辑成功（精确匹配）',
            'diagnosis': '',
            'suggestion': ''
        }
    
    # 标准化后匹配
    normalized_content = _normalize(content, ignore_whitespace, ignore_line_endings)
    normalized_old = _normalize(old_str, ignore_whitespace, ignore_line_endings)
    
    if normalized_old in normalized_content:
        # 尝试智能替换
        result = _smart_replace(content, old_str, new_str, ignore_whitespace, ignore_line_endings)
        if result['success']:
            write_file_utf8(file_path, result['new_content'])
            return {
                'success': True,
                'message': '编辑成功（标准化匹配）',
                'diagnosis': '',
                'suggestion': ''
            }
    
    # 匹配失败，生成诊断
    diagnosis = _generate_diagnosis(content, old_str, file_path)
    suggestion = _generate_suggestion(file_path)
    
    return {
        'success': False,
        'message': f'未找到匹配内容',
        'diagnosis': diagnosis,
        'suggestion': suggestion
    }


def diagnose_edit(file_path: str, old_str: str) -> str:
    """
    诊断编辑失败原因
    
    返回详细的诊断报告
    """
    from ..utils.encoding import read_file_utf8
    
    try:
        content = read_file_utf8(file_path)
    except Exception as e:
        return f"无法读取文件: {e}"
    
    return _generate_diagnosis(content, old_str, file_path)


def _normalize(text: str, ignore_whitespace: bool, ignore_line_endings: bool) -> str:
    """标准化文本"""
    if ignore_line_endings:
        text = text.replace('\r\n', '\n').replace('\r', '\n')
    if ignore_whitespace:
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()
    return text


def _smart_replace(content: str, old_str: str, new_str: str,
                   ignore_whitespace: bool, ignore_line_endings: bool) -> Dict:
    """智能替换"""
    lines = content.split('\n')
    old_lines = old_str.strip().split('\n') if ignore_whitespace else old_str.split('\n')
    
    for i in range(len(lines) - len(old_lines) + 1):
        candidate = '\n'.join(lines[i:i+len(old_lines)])
        normalized_candidate = _normalize(candidate, ignore_whitespace, ignore_line_endings)
        normalized_old = _normalize(old_str, ignore_whitespace, ignore_line_endings)
        
        if normalized_candidate == normalized_old:
            new_lines = lines[:i] + [new_str] + lines[i+len(old_lines):]
            return {
                'success': True,
                'new_content': '\n'.join(new_lines)
            }
    
    return {'success': False}


def _generate_diagnosis(content: str, old_str: str, file_path: str) -> str:
    """生成诊断报告"""
    lines = content.split('\n')
    old_lines = old_str.split('\n')
    
    has_crlf = '\r\n' in content or '\r' in content
    content_indent = _detect_indent(content)
    old_indent = _detect_indent(old_str)
    
    diagnosis = [
        "📋 Edit 失败诊断",
        "-" * 50,
        f"文件: {file_path}",
        f"文件行数: {len(lines)} | 查找内容行数: {len(old_lines)}",
        f"文件行尾: {'CRLF' if has_crlf else 'LF'}",
        f"文件缩进: {content_indent} | 查找缩进: {old_indent}",
        ""
    ]
    
    # 找最相似的行
    if old_lines:
        first_line = old_lines[0].strip()[:50]
        best_match_idx = -1
        best_sim = 0
        
        for i, line in enumerate(lines):
            sim = SequenceMatcher(None, line.strip()[:50], first_line).ratio()
            if sim > best_sim:
                best_sim = sim
                best_match_idx = i
        
        if best_match_idx >= 0 and best_sim > 0.5:
            diagnosis.extend([
                f"💡 最相似行: 第 {best_match_idx + 1} 行 (相似度 {best_sim:.0%})",
                f"  实际: {lines[best_match_idx][:60]}...",
                f"  查找: {old_lines[0][:60]}...",
                ""
            ])
    
    return '\n'.join(diagnosis)


def _generate_suggestion(file_path: str) -> str:
    """生成修复建议"""
    return '\n'.join([
        "💡 建议:",
        f"1. 重新读取文件: read('{file_path}')",
        "2. 从文件内容复制 oldString",
        "3. 检查缩进和空白字符"
    ])


def _detect_indent(text: str) -> str:
    """检测缩进类型"""
    for line in text.split('\n'):
        if line.startswith('\t'):
            return 'TAB'
        if line.startswith('  '):
            return '空格'
    return '无'


__all__ = ['smart_edit', 'diagnose_edit']
