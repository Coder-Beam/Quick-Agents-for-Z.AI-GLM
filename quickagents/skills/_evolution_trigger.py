"""
_evolution_trigger - Skills层进化触发适配器

职责:
- 懒加载: 仅在首次调用时 import evolution 模块
- 错误隔离: 所有触发失败静默吞掉，不影响主流程
- 统一入口: Skills 通过本模块触发经验收集，无需关心底层细节

设计原则:
    Skills → _evolution_trigger → get_evolution() → SkillEvolution → UnifiedDB
    ↑ 失败时静默，不向上抛出异常
"""

import logging

logger = logging.getLogger(__name__)


def trigger_git_commit(commit_info: dict) -> None:
    """
    安全触发 Git 提交进化分析

    Args:
        commit_info: {
            'hash': str,           # 提交hash
            'message': str,        # 提交信息
            'files_changed': list  # 变更文件列表
        }
    """
    try:
        from quickagents import get_evolution
        evolution = get_evolution()
        evolution.on_git_commit(commit_info)
    except Exception as e:
        logger.debug(f"[Evolution] Git提交触发失败(可忽略): {e}")


def trigger_task_complete(task_info: dict) -> None:
    """
    安全触发任务完成进化分析

    Args:
        task_info: {
            'task_id': str,          # 任务ID
            'task_name': str,        # 任务名称
            'skills_used': list,     # 使用的Skills列表
            'success': bool,         # 是否成功
            'duration_ms': int,      # 耗时毫秒
            'error': str (optional)  # 错误信息
        }
    """
    try:
        from quickagents import get_evolution
        evolution = get_evolution()
        evolution.on_task_complete(task_info)
    except Exception as e:
        logger.debug(f"[Evolution] 任务完成触发失败(可忽略): {e}")


def trigger_error(error_info: dict) -> None:
    """
    安全触发错误检测进化分析

    Args:
        error_info: {
            'error_type': str,       # 错误类型
            'error_message': str,    # 错误信息
            'context': str,          # 上下文
            'skill_involved': str    # 涉及的Skill
        }
    """
    try:
        from quickagents import get_evolution
        evolution = get_evolution()
        evolution.on_error_detected(error_info)
    except Exception as e:
        logger.debug(f"[Evolution] 错误检测触发失败(可忽略): {e}")
