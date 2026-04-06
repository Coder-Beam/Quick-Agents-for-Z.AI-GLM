"""
ParallelExecutor - 并行任务执行器 (v2.11.0)

基于OpenHarness研究的asyncio.gather模式，支持并行执行独立的只读操作。

核心功能:
- 并行执行多个独立的只读操作（最多3个并发）
- 超时控制
- 结果聚合
- 错误隔离（单个任务失败不影响其他任务）

使用方式:
    from quickagents.core.parallel_executor import ParallelExecutor

    executor = ParallelExecutor(max_workers=3)

    # 提交并行任务
    results = executor.execute([
        ("search_auth", lambda: db.search_memory("auth")),
        ("search_user", lambda: db.search_memory("user")),
        ("read_config", lambda: open("config.json").read()),
    ])

    for name, result in results.items():
        if result.success:
            print(f"{name}: {result.value}")
        else:
            print(f"{name}: FAILED - {result.error}")
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class TaskResult:
    """并行任务执行结果"""

    name: str
    success: bool
    value: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class ParallelStats:
    """并行执行统计"""

    total_tasks: int = 0
    successful: int = 0
    failed: int = 0
    total_duration_ms: float = 0.0
    avg_duration_ms: float = 0.0
    speedup_factor: float = 1.0  # vs串行执行的理论加速比

    def to_dict(self) -> Dict:
        return {
            "total_tasks": self.total_tasks,
            "successful": self.successful,
            "failed": self.failed,
            "total_duration_ms": round(self.total_duration_ms, 1),
            "avg_duration_ms": round(self.avg_duration_ms, 1),
            "speedup_factor": round(self.speedup_factor, 2),
        }


class ParallelExecutor:
    """
    并行任务执行器

    设计原则:
    1. 最多3个并发任务（避免资源争抢）
    2. 只适用于独立的只读操作
    3. 错误隔离：单个任务失败不影响其他任务
    4. 超时保护
    """

    DEFAULT_MAX_WORKERS = 3
    DEFAULT_TIMEOUT_SECONDS = 30.0

    def __init__(
        self,
        max_workers: int = DEFAULT_MAX_WORKERS,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ):
        """
        初始化并行执行器

        Args:
            max_workers: 最大并发数（默认3）
            timeout: 单个任务超时时间（秒）
        """
        self.max_workers = min(max(1, max_workers), 5)  # 1-5之间
        self.timeout = timeout
        self._stats = ParallelStats()

    def execute(
        self,
        tasks: List[Tuple[str, Callable]],
    ) -> Dict[str, TaskResult]:
        """
        并行执行多个任务

        Args:
            tasks: 任务列表，每个元素为 (name, callable) 元组

        Returns:
            Dict[str, TaskResult]: 以任务名为key的结果字典
        """
        if not tasks:
            return {}

        # 单任务直接执行，无需线程池
        if len(tasks) == 1:
            name, fn = tasks[0]
            result = self._execute_single(name, fn)
            self._update_stats({name: result}, result.duration_ms, [result.duration_ms])
            return {name: result}

        # 多任务并行执行
        results = {}  # type: Dict[str, TaskResult]
        overall_start = time.monotonic()
        individual_durations = []  # type: List[float]

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_name = {}
            for name, fn in tasks:
                future = executor.submit(self._execute_single, name, fn)
                future_to_name[future] = name

            for future in as_completed(future_to_name, timeout=self.timeout * len(tasks)):
                name = future_to_name[future]
                try:
                    result = future.result(timeout=self.timeout)
                    results[name] = result
                    individual_durations.append(result.duration_ms)
                except Exception as e:
                    results[name] = TaskResult(
                        name=name,
                        success=False,
                        error=str(e),
                    )

        overall_duration = (time.monotonic() - overall_start) * 1000
        self._update_stats(results, overall_duration, individual_durations)

        return results

    def _execute_single(self, name: str, fn: Callable) -> TaskResult:
        """执行单个任务并计时"""
        start = time.monotonic()
        try:
            value = fn()
            duration = (time.monotonic() - start) * 1000
            return TaskResult(
                name=name,
                success=True,
                value=value,
                duration_ms=duration,
            )
        except Exception as e:
            duration = (time.monotonic() - start) * 1000
            return TaskResult(
                name=name,
                success=False,
                error=str(e),
                duration_ms=duration,
            )

    def _update_stats(
        self,
        results: Dict[str, TaskResult],
        overall_ms: float,
        individual_durations: List[float],
    ) -> None:
        """更新执行统计"""
        total = len(results)
        successful = sum(1 for r in results.values() if r.success)
        serial_time = sum(individual_durations)

        self._stats.total_tasks += total
        self._stats.successful += successful
        self._stats.failed += total - successful
        self._stats.total_duration_ms += overall_ms
        self._stats.avg_duration_ms = self._stats.total_duration_ms / max(self._stats.total_tasks, 1)
        if serial_time > 0:
            self._stats.speedup_factor = serial_time / max(overall_ms, 0.1)

    def get_stats(self) -> Dict:
        """获取执行统计"""
        return self._stats.to_dict()

    def reset_stats(self) -> None:
        """重置统计"""
        self._stats = ParallelStats()
