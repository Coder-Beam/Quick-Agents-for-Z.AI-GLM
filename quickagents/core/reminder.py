"""
Reminder - 事件驱动提醒系统

核心功能:
- 工具调用计数提醒
- 上下文压力提醒
- 任务切换提醒
- 长时间运行提醒

本地化优势:
- 100%本地处理
- 智能阈值管理
"""

from typing import Dict, Optional, List
from datetime import datetime
from .cache_db import CacheDB


class Reminder:
    """
    事件驱动提醒系统

    使用方式:
        reminder = Reminder()

        # 工具调用后记录
        reminder.on_tool_call('read', {'path': 'file.md'})

        # 检查是否需要提醒
        alerts = reminder.check_alerts()
        for alert in alerts:
            print(f"[{alert['level']}] {alert['message']}")
    """

    # 阈值配置
    TOOL_CALL_THRESHOLD = 5  # 每5次工具调用检查一次
    CONTEXT_PRESSURE_LEVELS = [70, 85, 95]  # 上下文压力阈值
    LONG_RUN_MINUTES = [10, 30]  # 长时间运行提醒
    ERROR_THRESHOLD = 3  # 连续错误阈值

    def __init__(self, db_path: str = ".quickagents/cache.db"):
        """
        初始化提醒系统

        Args:
            db_path: 数据库路径
        """
        self.db = CacheDB(db_path)
        self._tool_call_count = 0
        self._start_time = datetime.now()
        self._error_count = 0
        self._last_task: Optional[str] = None
        self._context_usage = 0  # 模拟的上下文使用率
        self._alert_history: List[Dict] = []

    def on_tool_call(self, tool_name: str, tool_args: Dict) -> List[Dict]:
        """
        工具调用事件

        Args:
            tool_name: 工具名称
            tool_args: 工具参数

        Returns:
            触发的提醒列表
        """
        self._tool_call_count += 1
        alerts = []

        # 记录操作
        self.db.log_operation(tool_name, tool_args.get("path"), params=tool_args)

        # 检查工具调用阈值
        if self._tool_call_count % self.TOOL_CALL_THRESHOLD == 0:
            alerts.append(
                {
                    "type": "tool_call",
                    "level": "info",
                    "message": f"已执行 {self._tool_call_count} 次工具调用，请检查进度",
                    "count": self._tool_call_count,
                }
            )

        # 检查长时间运行
        elapsed = (datetime.now() - self._start_time).total_seconds() / 60
        for threshold in self.LONG_RUN_MINUTES:
            if elapsed >= threshold and not self._has_alerted("long_run", threshold):
                alerts.append(
                    {
                        "type": "long_run",
                        "level": "warning",
                        "message": f"已运行 {int(elapsed)} 分钟，建议评估是否需要分阶段",
                        "elapsed_minutes": int(elapsed),
                    }
                )
                self._mark_alerted("long_run", threshold)

        self._alert_history.extend(alerts)
        return alerts

    def on_error(self, error_type: str, error_msg: str) -> Optional[Dict]:
        """
        错误事件

        Args:
            error_type: 错误类型
            error_msg: 错误消息

        Returns:
            触发的提醒或None
        """
        self._error_count += 1

        if self._error_count >= self.ERROR_THRESHOLD:
            return {
                "type": "error_pattern",
                "level": "error",
                "message": f"连续 {self._error_count} 次错误，建议使用调试代理",
                "error_type": error_type,
                "count": self._error_count,
            }

        return None

    def on_success(self) -> None:
        """成功事件（重置错误计数）"""
        self._error_count = 0

    def on_task_switch(self, new_task: str) -> Optional[Dict]:
        """
        任务切换事件

        Args:
            new_task: 新任务名称

        Returns:
            触发的提醒或None
        """
        alert = None

        if self._last_task and self._last_task != new_task:
            alert = {
                "type": "task_switch",
                "level": "info",
                "message": f"任务切换: {self._last_task} → {new_task}",
                "from_task": self._last_task,
                "to_task": new_task,
            }

        self._last_task = new_task
        return alert

    def update_context_usage(self, usage_percent: int) -> List[Dict]:
        """
        更新上下文使用率

        Args:
            usage_percent: 使用百分比

        Returns:
            触发的提醒列表
        """
        self._context_usage = usage_percent
        alerts = []

        for threshold in self.CONTEXT_PRESSURE_LEVELS:
            if usage_percent >= threshold:
                level = "warning" if threshold < 90 else "critical"
                action = self._get_pressure_action(threshold)

                if not self._has_alerted("context", threshold):
                    alerts.append(
                        {
                            "type": "context_pressure",
                            "level": level,
                            "message": f"上下文使用率 {usage_percent}%，{action}",
                            "usage": usage_percent,
                            "threshold": threshold,
                            "suggested_action": action,
                        }
                    )
                    self._mark_alerted("context", threshold)

        self._alert_history.extend(alerts)
        return alerts

    def check_alerts(self) -> List[Dict]:
        """
        检查所有提醒条件

        Returns:
            当前所有待处理提醒
        """
        alerts = []

        # 检查长时间运行
        elapsed = (datetime.now() - self._start_time).total_seconds() / 60
        if elapsed >= self.LONG_RUN_MINUTES[0]:
            alerts.append(
                {
                    "type": "long_run",
                    "level": "info",
                    "message": f"已运行 {int(elapsed)} 分钟",
                    "elapsed_minutes": int(elapsed),
                }
            )

        # 添加最近的提醒历史
        recent = self._alert_history[-5:] if self._alert_history else []

        return alerts + recent

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "tool_calls": self._tool_call_count,
            "errors": self._error_count,
            "elapsed_minutes": (datetime.now() - self._start_time).total_seconds() / 60,
            "context_usage": self._context_usage,
            "current_task": self._last_task,
            "alert_count": len(self._alert_history),
        }

    def reset(self) -> None:
        """重置提醒系统"""
        self._tool_call_count = 0
        self._start_time = datetime.now()
        self._error_count = 0
        self._last_task = None
        self._context_usage = 0
        self._alert_history.clear()
        self._alerted_flags.clear()

    _alerted_flags: Dict[str, int] = {}

    def _has_alerted(self, alert_type: str, threshold: int) -> bool:
        """检查是否已提醒过"""
        key = f"{alert_type}_{threshold}"
        return self._alerted_flags.get(key, 0) > 0

    def _mark_alerted(self, alert_type: str, threshold: int) -> None:
        """标记已提醒"""
        key = f"{alert_type}_{threshold}"
        self._alerted_flags[key] = 1

    def _get_pressure_action(self, threshold: int) -> str:
        """获取压力阈值对应的动作"""
        actions = {
            70: "考虑压缩策略",
            85: "建议快速修剪大体积输出",
            95: "需要紧急压缩，保护关键文件",
        }
        return actions.get(threshold, "监控上下文使用")


# 全局实例
_global_reminder: Optional[Reminder] = None


def get_reminder() -> Reminder:
    """获取全局提醒系统"""
    global _global_reminder
    if _global_reminder is None:
        _global_reminder = Reminder()
    return _global_reminder
