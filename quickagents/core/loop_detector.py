"""
LoopDetector - 循环检测器

核心功能:
- 检测重复工具调用
- 防止无限循环
- 智能告警

本地化优势:
- 100%本地处理
- Token消耗为0
"""

from typing import Dict, Optional, List
from .cache_db import CacheDB


class LoopDetector:
    """
    循环检测器
    
    使用方式:
        detector = LoopDetector(threshold=3)
        
        # 每次工具调用前检查
        result = detector.check('read', {'path': 'file.md'})
        if result and result['detected']:
            print(f"检测到循环: {result['tool_name']} 已调用 {result['count']} 次")
            # 触发用户确认
    """
    
    def __init__(self, threshold: int = 3, window_size: int = 20,
                 db_path: str = '.quickagents/cache.db'):
        """
        初始化循环检测器
        
        Args:
            threshold: 重复次数阈值
            window_size: 检测窗口大小
            db_path: 数据库路径
        """
        self.threshold = threshold
        self.window_size = window_size
        self.db = CacheDB(db_path)
        self._history: List[str] = []  # 内存中的最近历史
    
    def check(self, tool_name: str, tool_args: Dict) -> Optional[Dict]:
        """
        检查是否出现循环
        
        Args:
            tool_name: 工具名称
            tool_args: 工具参数
            
        Returns:
            检测结果或None
        """
        # 添加到内存历史
        fingerprint = self.db._calculate_fingerprint(tool_name, tool_args)
        self._history.append(fingerprint)
        
        # 保持窗口大小
        if len(self._history) > self.window_size:
            self._history = self._history[-self.window_size:]
        
        # 检查数据库中的循环
        result = self.db.check_loop(tool_name, tool_args, self.threshold)
        
        if result:
            # 添加窗口内统计
            window_count = self._history.count(fingerprint)
            result['window_count'] = window_count
        
        return result
    
    def get_loop_patterns(self) -> List[Dict]:
        """
        获取所有循环模式
        
        Returns:
            循环模式列表
        """
        import sqlite3
        
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT fingerprint, tool_name, count, first_seen, last_seen
                FROM loop_detection
                WHERE count >= ?
                ORDER BY count DESC
            ''', (self.threshold,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def reset(self) -> None:
        """重置循环检测"""
        self._history.clear()
        self.db.reset_loop_detection()
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        patterns = self.get_loop_patterns()
        return {
            'total_patterns': len(patterns),
            'threshold': self.threshold,
            'window_size': self.window_size,
            'current_window_count': len(self._history),
            'patterns': patterns[:5]  # 返回前5个
        }
    
    def should_pause(self, tool_name: str, tool_args: Dict) -> bool:
        """
        判断是否应该暂停
        
        Args:
            tool_name: 工具名称
            tool_args: 工具参数
            
        Returns:
            是否应该暂停
        """
        result = self.check(tool_name, tool_args)
        return result is not None and result.get('detected', False)


# 全局实例
_global_detector: Optional[LoopDetector] = None

def get_loop_detector(threshold: int = 3) -> LoopDetector:
    """获取全局循环检测器"""
    global _global_detector
    if _global_detector is None:
        _global_detector = LoopDetector(threshold=threshold)
    return _global_detector
