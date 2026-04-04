"""
Sync Conflict Detector - 同步冲突检测器

功能:
- 时间戳验证：检测文件最后修改时间
- 哈希验证：检测文件内容哈希变化
- 冲突警告：在同步前警告用户可能的冲突

使用方式:
    from quickagents.utils.sync_conflict import SyncConflictDetector
    
    detector = SyncConflictDetector()
    
    # 检查冲突
    conflicts = detector.check_conflicts()
    if conflicts:
        print("检测到冲突，请确认是否继续同步")
        for conflict in conflicts:
            print(f"  - {conflict['file']}: {conflict['reason']}")
    
    # 强制同步（忽略冲突）
    detector.sync_with_conflicts(force=True)
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class SyncConflictDetector:
    """
    同步冲突检测器
    
    使用时间戳+哈希双重验证检测文件冲突
    """
    
    def __init__(self, 
                 docs_dir: str = 'Docs',
                 quickagents_dir: str = '.quickagents',
                 db_path: str = '.quickagents/unified.db'):
        """
        初始化冲突检测器
        
        Args:
            docs_dir: 文档目录
            quickagents_dir: QuickAgents数据目录
            db_path: 数据库路径
        """
        self.docs_dir = Path(docs_dir)
        self.quickagents_dir = Path(quickagents_dir)
        self.db_path = Path(db_path)
        
        # 同步状态文件
        self.sync_state_file = self.quickagents_dir / 'sync_state.json'
        
        # 需要监控的文件
        self.monitored_files = {
            'memory': self.docs_dir / 'MEMORY.md',
            'tasks': self.docs_dir / 'TASKS.md',
            'decisions': self.docs_dir / 'DECISIONS.md',
            'progress': self.quickagents_dir / 'boulder.json',
            'feedback_bugs': self.quickagents_dir / 'feedback' / 'bugs.md',
            'feedback_improvements': self.quickagents_dir / 'feedback' / 'improvements.md',
            'feedback_best': self.quickagents_dir / 'feedback' / 'best-practices.md',
        }
    
    def _load_sync_state(self) -> Dict[str, Any]:
        """加载同步状态"""
        if self.sync_state_file.exists():
            try:
                return json.loads(self.sync_state_file.read_text(encoding='utf-8'))
            except:
                return {}
        return {}
    
    def _save_sync_state(self, state: Dict[str, Any]) -> None:
        """保存同步状态"""
        self.sync_state_file.parent.mkdir(parents=True, exist_ok=True)
        self.sync_state_file.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
    
    def _get_file_hash(self, file_path: Path) -> Optional[str]:
        """计算文件哈希"""
        if not file_path.exists():
            return None
        
        try:
            content = file_path.read_bytes()
            return hashlib.sha256(content).hexdigest()[:16]
        except:
            return None
    
    def _get_file_mtime(self, file_path: Path) -> Optional[float]:
        """获取文件修改时间"""
        if not file_path.exists():
            return None
        
        try:
            return file_path.stat().st_mtime
        except:
            return None
    
    def record_sync_state(self, file_key: str) -> None:
        """
        记录同步后的文件状态
        
        Args:
            file_key: 文件键名（如 'memory', 'tasks'）
        """
        state = self._load_sync_state()
        
        file_path = self.monitored_files.get(file_key)
        if file_path and file_path.exists():
            state[file_key] = {
                'hash': self._get_file_hash(file_path),
                'mtime': self._get_file_mtime(file_path),
                'sync_at': datetime.now().isoformat()
            }
            self._save_sync_state(state)
    
    def check_file_conflict(self, file_key: str) -> Optional[Dict[str, Any]]:
        """
        检查单个文件的冲突
        
        Args:
            file_key: 文件键名
        
        Returns:
            冲突信息，如果没有冲突返回 None
        """
        file_path = self.monitored_files.get(file_key)
        if not file_path:
            return None
        
        # 文件不存在，无冲突
        if not file_path.exists():
            return None
        
        # 获取当前状态
        current_hash = self._get_file_hash(file_path)
        current_mtime = self._get_file_mtime(file_path)
        
        # 加载上次同步状态
        state = self._load_sync_state()
        last_state = state.get(file_key, {})
        
        # 没有上次记录，无冲突
        if not last_state:
            return None
        
        last_hash = last_state.get('hash')
        last_mtime = last_state.get('mtime')
        last_sync_at = last_state.get('sync_at')
        
        # 检测哈希变化（内容被修改）
        hash_changed = current_hash != last_hash if last_hash else False
        
        # 检测时间戳变化（文件被修改）
        mtime_changed = abs(current_mtime - last_mtime) > 1 if last_mtime else False
        
        if hash_changed or mtime_changed:
            return {
                'file_key': file_key,
                'file_path': str(file_path),
                'reason': 'content_modified' if hash_changed else 'mtime_changed',
                'last_sync_at': last_sync_at,
                'last_hash': last_hash,
                'current_hash': current_hash,
                'last_mtime': last_mtime,
                'current_mtime': current_mtime,
                'message': f"文件 {file_path.name} 在上次同步后被修改（{last_sync_at}）"
            }
        
        return None
    
    def check_conflicts(self, file_keys: List[str] = None) -> List[Dict[str, Any]]:
        """
        检查所有文件的冲突
        
        Args:
            file_keys: 要检查的文件键名列表，默认检查所有
        
        Returns:
            冲突列表
        """
        if file_keys is None:
            file_keys = list(self.monitored_files.keys())
        
        conflicts = []
        for key in file_keys:
            conflict = self.check_file_conflict(key)
            if conflict:
                conflicts.append(conflict)
        
        return conflicts
    
    def has_conflicts(self, file_keys: List[str] = None) -> bool:
        """检查是否存在冲突"""
        return len(self.check_conflicts(file_keys)) > 0
    
    def get_conflict_report(self, file_keys: List[str] = None) -> str:
        """
        获取冲突报告
        
        Args:
            file_keys: 要检查的文件键名列表
        
        Returns:
            格式化的冲突报告
        """
        conflicts = self.check_conflicts(file_keys)
        
        if not conflicts:
            return "✅ 未检测到同步冲突"
        
        lines = [
            "⚠️ 检测到同步冲突！",
            "",
            "以下文件在上次同步后被手动修改：",
            ""
        ]
        
        for c in conflicts:
            lines.append(f"  📄 {c['file_path']}")
            lines.append(f"     原因: {c['message']}")
            lines.append(f"     上次同步: {c['last_sync_at']}")
            lines.append(f"     哈希变化: {c['last_hash'][:8]}... -> {c['current_hash'][:8]}...")
            lines.append("")
        
        lines.extend([
            "⚠️ 继续同步将覆盖这些手动修改！",
            "",
            "建议操作：",
            "  1. 如果手动修改很重要，请先备份文件",
            "  2. 使用 'qa sync --force' 强制同步",
            "  3. 或者使用 'qa restore' 从SQLite恢复"
        ])
        
        return '\n'.join(lines)
    
    def clear_conflict_state(self, file_key: str = None) -> None:
        """
        清除冲突状态（用于强制同步后）
        
        Args:
            file_key: 文件键名，为None时清除所有
        """
        if file_key:
            state = self._load_sync_state()
            if file_key in state:
                del state[file_key]
                self._save_sync_state(state)
        else:
            self._save_sync_state({})
    
    def record_sync_state(self, file_key: str) -> None:
        """
        记录单个文件的同步状态
        
        Args:
            file_key: 文件键名
        """
        file_path = self.monitored_files.get(file_key)
        if not file_path:
            return
        
        current_hash = self._get_file_hash(file_path)
        current_mtime = self._get_file_mtime(file_path)
        
        state = self._load_sync_state()
        state[file_key] = {
            'hash': current_hash,
            'mtime': current_mtime,
            'sync_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self._save_sync_state(state)
    
    def record_all_sync_states(self) -> None:
        """记录所有文件的同步状态"""
        for key in self.monitored_files.keys():
            self.record_sync_state(key)


# 全局实例
_detector_instance = None

def get_sync_conflict_detector() -> SyncConflictDetector:
    """获取全局冲突检测器实例"""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = SyncConflictDetector()
    return _detector_instance


def check_sync_conflicts(file_keys: List[str] = None) -> List[Dict[str, Any]]:
    """
    检查同步冲突的便捷函数
    
    Args:
        file_keys: 要检查的文件键名列表
    
    Returns:
        冲突列表
    """
    return get_sync_conflict_detector().check_conflicts(file_keys)


def get_sync_conflict_report(file_keys: List[str] = None) -> str:
    """
    获取同步冲突报告的便捷函数
    
    Args:
        file_keys: 要检查的文件键名列表
    
    Returns:
        格式化的冲突报告
    """
    return get_sync_conflict_detector().get_conflict_report(file_keys)


__all__ = [
    'SyncConflictDetector',
    'get_sync_conflict_detector',
    'check_sync_conflicts',
    'get_sync_conflict_report'
]
