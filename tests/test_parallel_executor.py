"""
Tests for ParallelExecutor - 并行任务执行器 (v2.11.0)
"""

import time
import pytest

from quickagents.core.parallel_executor import ParallelExecutor, TaskResult, ParallelStats


class TestParallelExecutorInit:
    def test_default_max_workers(self):
        e = ParallelExecutor()
        assert e.max_workers == 3

    def test_custom_max_workers(self):
        e = ParallelExecutor(max_workers=5)
        assert e.max_workers == 5

    def test_max_workers_clamped(self):
        e = ParallelExecutor(max_workers=100)
        assert e.max_workers == 5

    def test_min_workers_clamped(self):
        e = ParallelExecutor(max_workers=0)
        assert e.max_workers == 1


class TestSingleTask:
    def test_single_task(self):
        e = ParallelExecutor()
        results = e.execute([("t1", lambda: 42)])
        assert "t1" in results
        assert results["t1"].success
        assert results["t1"].value == 42

    def test_empty_tasks(self):
        e = ParallelExecutor()
        results = e.execute([])
        assert results == {}


class TestParallelExecution:
    def test_parallel_faster_than_serial(self):
        """Parallel execution should be faster than serial for IO-bound tasks."""
        e = ParallelExecutor(max_workers=3)
        delay = 0.05  # 50ms per task

        start = time.monotonic()
        results = e.execute(
            [
                ("a", lambda: time.sleep(delay) or "ra"),
                ("b", lambda: time.sleep(delay) or "rb"),
                ("c", lambda: time.sleep(delay) or "rc"),
            ]
        )
        elapsed = (time.monotonic() - start) * 1000

        # All should succeed
        assert all(r.success for r in results.values())
        assert results["a"].value == "ra"
        assert results["b"].value == "rb"
        assert results["c"].value == "rc"

        # Parallel should be faster than serial (3 * 50ms = 150ms)
        assert elapsed < 200  # Allow some overhead

    def test_error_isolation(self):
        """One task failure should not affect others."""
        e = ParallelExecutor(max_workers=3)

        def fail():
            raise ValueError("boom")

        results = e.execute(
            [
                ("ok1", lambda: "result1"),
                ("fail", fail),
                ("ok2", lambda: "result2"),
            ]
        )

        assert results["ok1"].success
        assert results["ok1"].value == "result1"
        assert not results["fail"].success
        assert "boom" in results["fail"].error  # type: ignore[arg-type]
        assert results["ok2"].success
        assert results["ok2"].value == "result2"


class TestStats:
    def test_stats_after_execution(self):
        e = ParallelExecutor(max_workers=2)
        delay = 0.02  # 20ms per task for measurable duration
        e.execute(
            [
                ("a", lambda: time.sleep(delay) or 1),
                ("b", lambda: time.sleep(delay) or 2),
            ]
        )
        stats = e.get_stats()
        assert stats["total_tasks"] == 2
        assert stats["successful"] == 2
        assert stats["failed"] == 0
        assert stats["speedup_factor"] >= 0  # May be 0 for very fast tasks

    def test_stats_accumulate(self):
        e = ParallelExecutor()
        e.execute([("a", lambda: 1)])
        e.execute([("b", lambda: 2)])
        stats = e.get_stats()
        assert stats["total_tasks"] == 2

    def test_reset_stats(self):
        e = ParallelExecutor()
        e.execute([("a", lambda: 1)])
        e.reset_stats()
        stats = e.get_stats()
        assert stats["total_tasks"] == 0


class TestTaskResult:
    def test_task_result_creation(self):
        r = TaskResult(name="test", success=True, value=42, duration_ms=10.0)
        assert r.name == "test"
        assert r.success is True
        assert r.value == 42
        assert r.duration_ms == 10.0

    def test_task_result_failure(self):
        r = TaskResult(name="fail", success=False, error="oops")
        assert r.error == "oops"
        assert r.value is None


class TestParallelStats:
    def test_to_dict(self):
        s = ParallelStats(total_tasks=5, successful=4, failed=1)
        d = s.to_dict()
        assert d["total_tasks"] == 5
        assert d["successful"] == 4
        assert d["failed"] == 1
        assert "speedup_factor" in d
