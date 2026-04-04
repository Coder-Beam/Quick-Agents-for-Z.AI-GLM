"""
FeedbackCollector - 经验收集系统

核心功能:
- 收集使用经验
- 记录改进建议
- 去重存储
- 完全本地化

存储位置: ~/.quickagents/feedback/
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class FeedbackCollector:
    """
    经验收集系统
    
    使用方式:
        collector = FeedbackCollector()
        
        # 记录Bug
        collector.record('bug', 'Edit工具oldString不匹配', 
                        scenario='编辑MEMORY.md时')
        
        # 记录改进
        collector.record('improve', '添加哈希检测减少Token消耗',
                        scenario='文件操作频繁时')
        
        # 查看收集
        bugs = collector.get_feedback('bug')
        stats = collector.get_stats()
    """
    
    FEEDBACK_TYPES = {
        'bug': 'bugs.md',
        'improve': 'improvements.md',
        'best': 'best-practices.md',
        'skill': 'skill-review.md',
        'agent': 'agent-review.md'
    }
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        初始化收集器
        
        Args:
            base_dir: 存储目录，默认 ~/.quickagents/feedback/
        """
        if base_dir is None:
            base_dir = os.path.expanduser('~/.quickagents/feedback')
        
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化所有反馈文件
        for filename in self.FEEDBACK_TYPES.values():
            filepath = self.base_dir / filename
            if not filepath.exists():
                filepath.write_text('# Feedback Collection\n\n', encoding='utf-8')
    
    def record(self, feedback_type: str, description: str, 
               scenario: Optional[str] = None, suggestion: Optional[str] = None,
               project: Optional[str] = None, dedup_hours: int = 1) -> bool:
        """
        记录反馈
        
        Args:
            feedback_type: 反馈类型 (bug/improve/best/skill/agent)
            description: 描述
            scenario: 场景上下文
            suggestion: 改进建议
            project: 项目名
            dedup_hours: 去重时间窗口（小时）
            
        Returns:
            是否成功记录（去重可能返回False）
        """
        if feedback_type not in self.FEEDBACK_TYPES:
            return False
        
        # 去重检查
        if self._is_duplicate(feedback_type, description, dedup_hours):
            return False
        
        # 生成记录
        record = self._format_record(description, scenario, suggestion, project)  # type: ignore[arg-type]
        
        # 追加到文件
        filepath = self.base_dir / self.FEEDBACK_TYPES[feedback_type]
        content = filepath.read_text(encoding='utf-8') if filepath.exists() else ''
        content += '\n' + record
        
        filepath.write_text(content, encoding='utf-8')
        
        return True
    
    def get_feedback(self, feedback_type: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """
        获取反馈记录
        
        Args:
            feedback_type: 反馈类型，None表示所有类型
            limit: 最大返回数量
            
        Returns:
            反馈记录列表
        """
        results = []
        
        if feedback_type:
            files = {feedback_type: self.FEEDBACK_TYPES.get(feedback_type)}
        else:
            files = self.FEEDBACK_TYPES  # type: ignore[assignment]
        
        for ftype, filename in files.items():
            if filename is None:
                continue
                
            filepath = self.base_dir / filename
            if not filepath.exists():
                continue
            
            content = filepath.read_text(encoding='utf-8')
            records = self._parse_records(content, ftype)
            results.extend(records)
        
        # 按时间排序
        results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return results[:limit]
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = {
            'total': 0,
            'by_type': {}
        }
        
        for ftype, filename in self.FEEDBACK_TYPES.items():
            filepath = self.base_dir / filename
            if filepath.exists():
                content = filepath.read_text(encoding='utf-8')
                count = content.count('## ') - 1  # 简单统计记录数
                stats['by_type'][ftype] = max(0, count)  # type: ignore[index]
                stats['total'] += count  # type: ignore[operator]
        
        return stats
    
    def clear(self, feedback_type: Optional[str] = None) -> int:
        """
        清空反馈
        
        Args:
            feedback_type: 指定类型，None表示清空所有
            
        Returns:
            清空的记录数
        """
        count = 0
        
        if feedback_type:
            files = {feedback_type: self.FEEDBACK_TYPES.get(feedback_type)}
        else:
            files = self.FEEDBACK_TYPES  # type: ignore[assignment]
        
        for ftype, filename in files.items():
            if filename is None:
                continue
                
            filepath = self.base_dir / filename
            if filepath.exists():
                content = filepath.read_text(encoding='utf-8')
                record_count = content.count('## ') - 1
                filepath.write_text('# Feedback Collection\n\n', encoding='utf-8')
                count += record_count
        
        return count
    
    def _format_record(self, description: str, scenario: str, 
                       suggestion: str, project: str) -> str:
        """格式化记录"""
        now = datetime.now()
        project_name = project or 'QuickAgents'
        
        lines = [
            f'## {now.strftime("%Y-%m-%d %H:%M")} - {project_name}',
            '',
            f'**描述**: {description}',
        ]
        
        if scenario:
            lines.append(f'**场景**: {scenario}')
        
        if suggestion:
            lines.append(f'**建议**: {suggestion}')
        
        lines.extend(['', '---', ''])
        
        return '\n'.join(lines)
    
    def _parse_records(self, content: str, feedback_type: str) -> List[Dict]:
        """解析记录"""
        records = []
        
        # 简单解析
        sections = content.split('## ')[1:]  # 跳过标题
        
        for section in sections:
            lines = section.strip().split('\n')
            if not lines:
                continue
            
            record = {
                'type': feedback_type,
                'timestamp': lines[0].split(' - ')[0] if lines else '',
                'description': '',
                'scenario': '',
                'suggestion': ''
            }
            
            for line in lines[1:]:
                if line.startswith('**描述**:'):
                    record['description'] = line.replace('**描述**:', '').strip()
                elif line.startswith('**场景**:'):
                    record['scenario'] = line.replace('**场景**:', '').strip()
                elif line.startswith('**建议**:'):
                    record['suggestion'] = line.replace('**建议**:', '').strip()
            
            records.append(record)
        
        return records
    
    def _is_duplicate(self, feedback_type: str, description: str, hours: int) -> bool:
        """
        检查是否重复
        
        同一时间窗口内，相同类型+相似描述只保留一条
        """
        filepath = self.base_dir / self.FEEDBACK_TYPES.get(feedback_type, '')
        if not filepath.exists():
            return False
        
        content = filepath.read_text(encoding='utf-8')
        
        # 计算当前描述的哈希
        desc_hash = hashlib.md5(description.encode()).hexdigest()[:8]
        
        # 检查时间窗口内的记录
        cutoff = datetime.now().timestamp() - (hours * 3600)
        
        for record in self._parse_records(content, feedback_type):
            try:
                record_time = datetime.strptime(record['timestamp'], '%Y-%m-%d %H:%M')
                if record_time.timestamp() >= cutoff:
                    # 检查描述相似度
                    existing_hash = hashlib.md5(record['description'].encode()).hexdigest()[:8]
                    if existing_hash == desc_hash:
                        return True
            except:
                pass
        
        return False


# 全局实例
_global_collector: Optional[FeedbackCollector] = None

def get_feedback_collector() -> FeedbackCollector:
    """获取全局收集器"""
    global _global_collector
    if _global_collector is None:
        _global_collector = FeedbackCollector()
    return _global_collector
