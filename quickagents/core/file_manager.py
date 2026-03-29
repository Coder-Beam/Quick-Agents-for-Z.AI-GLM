"""
FileManager - 智能文件管理器

核心功能:
- 哈希检测的文件读取
- 安全的文件编辑
- 缓存管理

Token节省:
- 相同文件不重复读取
- Edit前智能验证
- 批量操作优化
"""

import os
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from ..utils.hash_cache import HashCache, get_global_cache


class FileManager:
    """
    智能文件管理器
    
    解决问题:
    1. Edit工具要求先Read，造成Token浪费
    2. 文件内容变化后oldString失效
    3. 重复读取相同文件
    
    使用方式:
        fm = FileManager()
        
        # 智能读取（哈希检测）
        content = fm.read('file.md')  # 未变化则使用缓存
        
        # 安全编辑（自动验证）
        fm.edit('file.md', 'old', 'new')  # 自动检查缓存有效性
        
        # 批量操作
        fm.batch_read(['file1.md', 'file2.md'])
    """
    
    def __init__(self, use_global_cache: bool = True):
        """
        初始化文件管理器
        
        Args:
            use_global_cache: 是否使用全局缓存（跨实例共享）
        """
        self.cache = get_global_cache() if use_global_cache else HashCache()
        self._last_read_path: Optional[str] = None
        self._last_read_content: Optional[str] = None
    
    def read(self, file_path: str, force: bool = False) -> str:
        """
        智能读取文件（带哈希检测）
        
        Args:
            file_path: 文件路径
            force: 是否强制重新读取
            
        Returns:
            文件内容
            
        Token节省:
        - 文件未变化: 节省100%读取Token
        - 文件已变化: 正常读取
        """
        file_path = self._normalize_path(file_path)
        
        if force:
            content = self._read_file(file_path)
            self.cache.update(file_path, content)
            self._update_last_read(file_path, content)
            return content
        
        content, changed = self.cache.read_if_changed(file_path)
        self._update_last_read(file_path, content)
        
        if changed:
            # 文件有变化，需要返回新内容
            return content
        else:
            # 文件未变化，使用缓存（Token节省点）
            return content
    
    def read_if_changed(self, file_path: str) -> Tuple[str, bool]:
        """
        读取文件并返回是否变化
        
        Args:
            file_path: 文件路径
            
        Returns:
            (内容, 是否变化)
        """
        file_path = self._normalize_path(file_path)
        return self.cache.read_if_changed(file_path)
    
    def write(self, file_path: str, content: str) -> bool:
        """
        写入文件并更新缓存
        
        Args:
            file_path: 文件路径
            content: 文件内容
            
        Returns:
            是否成功
        """
        file_path = self._normalize_path(file_path)
        
        # 创建目录
        dir_path = os.path.dirname(file_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
        
        # 更新缓存
        self.cache.update(file_path, content)
        
        return True
    
    def edit(self, file_path: str, old_str: str, new_str: str, 
             validate_cache: bool = True) -> Dict:
        """
        安全编辑文件
        
        Args:
            file_path: 文件路径
            old_str: 要替换的内容
            new_str: 替换后的内容
            validate_cache: 是否验证缓存
            
        Returns:
            {
                'success': bool,
                'message': str,
                'token_saved': int,  # 估算节省的Token
                'lines_changed': int
            }
        """
        file_path = self._normalize_path(file_path)
        result = {
            'success': False,
            'message': '',
            'token_saved': 0,
            'lines_changed': 0
        }
        
        # 验证缓存
        if validate_cache:
            content, changed = self.cache.read_if_changed(file_path)
            if changed:
                result['message'] = '文件已变化，已重新读取'
                # 需要重新读取，但这已经在read_if_changed中完成
            else:
                result['message'] = '使用缓存内容'
                result['token_saved'] = len(content.split('\n'))  # 估算节省的Token
        else:
            content = self._read_file(file_path)
        
        # 检查old_str是否存在
        if old_str not in content:
            result['message'] = f'oldString not found in {file_path}'
            return result
        
        # 执行替换
        new_content = content.replace(old_str, new_str, 1)
        lines_changed = content.count('\n') - new_content.count('\n')
        result['lines_changed'] = abs(lines_changed) + old_str.count('\n')
        
        # 写入文件
        self.write(file_path, new_content)
        
        result['success'] = True
        result['message'] = '编辑成功'
        
        return result
    
    def batch_read(self, file_paths: List[str]) -> Dict[str, str]:
        """
        批量读取文件
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            {路径: 内容} 字典
        """
        results = {}
        for path in file_paths:
            try:
                results[path] = self.read(path)
            except Exception as e:
                results[path] = f'ERROR: {str(e)}'
        return results
    
    def get_file_hash(self, file_path: str) -> str:
        """
        获取文件哈希
        
        Args:
            file_path: 文件路径
            
        Returns:
            MD5哈希值（前8位）
        """
        file_path = self._normalize_path(file_path)
        return self.cache.get_hash(file_path)
    
    def is_cached(self, file_path: str) -> bool:
        """
        检查文件是否已缓存
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否已缓存
        """
        file_path = self._normalize_path(file_path)
        return self.cache.is_cached(file_path)
    
    def invalidate(self, file_path: str) -> None:
        """
        使缓存失效
        
        Args:
            file_path: 文件路径
        """
        file_path = self._normalize_path(file_path)
        self.cache.invalidate(file_path)
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计"""
        return self.cache.get_cache_stats()
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self.cache.clear()
    
    def _normalize_path(self, file_path: str) -> str:
        """规范化路径"""
        return str(Path(file_path).resolve())
    
    def _read_file(self, file_path: str) -> str:
        """读取文件内容"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _update_last_read(self, path: str, content: str) -> None:
        """更新最后读取记录"""
        self._last_read_path = path
        self._last_read_content = content
    
    def get_last_read(self) -> Tuple[Optional[str], Optional[str]]:
        """
        获取最后读取的文件信息
        
        Returns:
            (路径, 内容)
        """
        return self._last_read_path, self._last_read_content


# 便捷函数
def read(file_path: str) -> str:
    """便捷读取函数"""
    return FileManager().read(file_path)

def write(file_path: str, content: str) -> bool:
    """便捷写入函数"""
    return FileManager().write(file_path, content)

def edit(file_path: str, old_str: str, new_str: str) -> Dict:
    """便捷编辑函数"""
    return FileManager().edit(file_path, old_str, new_str)
