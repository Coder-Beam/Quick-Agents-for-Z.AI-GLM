"""
HashCache - 哈希缓存系统 (SQLite后端)

核心功能:
- 文件内容哈希检测
- SQLite持久化存储
- 变化检测

优势:
- 零安装 (Python内置)
- 高性能
- 事务安全
"""

from typing import Dict, Optional, Tuple
from .cache_db import CacheDB, get_cache_db


class HashCache:
    """
    哈希缓存管理器 (SQLite后端)
    
    使用方式:
        cache = HashCache()
        
        # 智能读取
        content, changed = cache.read_if_changed('file.md')
        if changed:
            print("文件已变化，重新读取")
        else:
            print("使用缓存，节省Token")
    """
    
    def __init__(self, db_path: str = '.quickagents/cache.db'):
        """
        初始化哈希缓存
        
        Args:
            db_path: SQLite数据库路径
        """
        self.db = CacheDB(db_path)
    
    def calculate_hash(self, content: str) -> str:
        """计算内容哈希"""
        return self.db._calculate_hash(content)
    
    def get_file_hash(self, file_path: str) -> str:
        """获取文件当前哈希"""
        return self.db._calculate_file_hash(file_path)
    
    def has_changed(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """检查文件是否已改变"""
        return self.db.check_file_changed(file_path)
    
    def read_if_changed(self, file_path: str) -> Tuple[str, bool]:
        """
        智能读取：仅在文件改变时读取
        
        这是核心方法，替代传统的每次都Read
        
        Returns:
            (内容, 是否改变)
        """
        import os
        
        # 检查变化
        changed, current_hash = self.db.check_file_changed(file_path)
        
        if not changed:
            # 使用缓存
            cached = self.db.get_file_cache(file_path)
            if cached:
                return cached['content'], False
        
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新缓存
        self.db.cache_file(file_path, content, current_hash)
        
        return content, True
    
    def invalidate(self, file_path: str) -> bool:
        """使缓存失效"""
        return self.db.invalidate_file(file_path)
    
    def update_after_write(self, file_path: str, content: str) -> None:
        """写入后更新缓存"""
        content_hash = self.db._calculate_hash(content)
        self.db.cache_file(file_path, content, content_hash)
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计"""
        return self.db.get_stats()['file_cache']
    
    def clear(self) -> None:
        """清空所有缓存"""
        self.db.clear_file_cache()


# 全局单例
_global_cache: Optional[HashCache] = None

def get_global_cache() -> HashCache:
    """获取全局缓存实例"""
    global _global_cache
    if _global_cache is None:
        _global_cache = HashCache()
    return _global_cache

def reset_global_cache() -> None:
    """重置全局缓存"""
    global _global_cache
    _global_cache = None
