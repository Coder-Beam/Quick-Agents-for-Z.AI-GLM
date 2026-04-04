"""
QuickAgents v2.7.6 性能基准测试

验证核心架构升级的效果:
1. 单条读取性能（mmap优化）
2. 批量写入性能（batched VALUES）
3. 连接池内存占用（动态伸缩）
4. WAL文件大小可控

运行方式:
    python tests/benchmark_performance.py
"""

import os
import sys
import time
import shutil
import tempfile
import statistics
from pathlib import Path
from dataclasses import dataclass, field

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from quickagents.core import ConnectionManager, PoolConfig, TransactionManager, RetryConfig
from quickagents.core.unified_db import UnifiedDB, MemoryType


@dataclass
class BenchResult:
    """单个基准测试结果"""
    name: str
    iterations: int
    times_ms: list = field(default_factory=list)
    
    @property
    def avg_ms(self):
        return statistics.mean(self.times_ms) if self.times_ms else 0
    
    @property
    def median_ms(self):
        return statistics.median(self.times_ms) if self.times_ms else 0
    
    @property
    def min_ms(self):
        return min(self.times_ms) if self.times_ms else 0
    
    @property
    def max_ms(self):
        return max(self.times_ms) if self.times_ms else 0
    
    @property
    def stdev_ms(self):
        return statistics.stdev(self.times_ms) if len(self.times_ms) > 1 else 0


def time_ms(func, *args, **kwargs):
    """测量函数执行时间（毫秒）"""
    start = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = (time.perf_counter() - start) * 1000
    return elapsed, result


def bench_single_read(db: UnifiedDB, iterations: int = 500) -> BenchResult:
    """基准: 单条读取性能"""
    result = BenchResult(name="单条读取 (get_memory)", iterations=iterations)
    
    # 预填充数据
    for i in range(100):
        db.set_memory(f'bench.key.{i}', f'value_{i}' * 10, MemoryType.FACTUAL)
    
    # 热身
    for _ in range(50):
        db.get_memory('bench.key.0')
    
    # 测量
    keys = [f'bench.key.{i % 100}' for i in range(iterations)]
    for key in keys:
        ms, _ = time_ms(db.get_memory, key)
        result.times_ms.append(ms)
    
    return result


def bench_batch_write(db: UnifiedDB, batch_sizes: list = None) -> dict:
    """基准: 批量写入性能（使用 set_memory 单条循环作为基准参考）"""
    if batch_sizes is None:
        batch_sizes = [10, 50, 100, 500]
    
    results = {}
    
    for batch_size in batch_sizes:
        result = BenchResult(
            name=f"批量写入 (set_memory x{batch_size})",
            iterations=5
        )
        
        for run in range(5):
            items = [
                (f'batch.{batch_size}.key.{run}.{i}', f'val_{i}' * 5, MemoryType.FACTUAL)
                for i in range(batch_size)
            ]
            
            def write_batch():
                for key, val, mtype in items:
                    db.set_memory(key, val, mtype)
            
            ms, _ = time_ms(write_batch)
            result.times_ms.append(ms)
        
        results[batch_size] = result
    
    return results


def bench_connection_pool(db_path: str) -> dict:
    """基准: 连接池性能"""
    results = {}
    
    # 配置1: 小池 (min=1, max=3)
    config_small = PoolConfig(min_size=1, max_size=3, pre_ping=False)
    mgr_small = ConnectionManager(db_path, pool_config=config_small)
    
    times_small = []
    for _ in range(200):
        start = time.perf_counter()
        with mgr_small.get_connection() as conn:
            conn.execute("SELECT 1").fetchone()
        times_small.append((time.perf_counter() - start) * 1000)
    
    metrics_small = mgr_small.get_pool_metrics()
    mgr_small.close_all()
    
    results['small_pool'] = {
        'config': 'min=1, max=3',
        'avg_ms': statistics.mean(times_small),
        'p50_ms': statistics.median(times_small),
        'metrics': metrics_small,
    }
    
    # 配置2: 大池 (min=2, max=10) with pre_ping
    config_large = PoolConfig(min_size=2, max_size=10, pre_ping=True)
    mgr_large = ConnectionManager(db_path, pool_config=config_large)
    
    times_large = []
    for _ in range(200):
        start = time.perf_counter()
        with mgr_large.get_connection() as conn:
            conn.execute("SELECT 1").fetchone()
        times_large.append((time.perf_counter() - start) * 1000)
    
    metrics_large = mgr_large.get_pool_metrics()
    mgr_large.close_all()
    
    results['large_pool'] = {
        'config': 'min=2, max=10, pre_ping=True',
        'avg_ms': statistics.mean(times_large),
        'p50_ms': statistics.median(times_large),
        'metrics': metrics_large,
    }
    
    return results


def bench_wal_growth(db_path: str) -> dict:
    """基准: WAL文件增长控制"""
    db = UnifiedDB(db_path)
    
    # 插入大量数据
    for i in range(1000):
        db.set_memory(f'wal.key.{i}', f'x' * 100, MemoryType.FACTUAL)
    
    db.close()
    
    # 检查文件大小
    db_file = Path(db_path)
    wal_file = Path(db_path + '-wal')
    shm_file = Path(db_path + '-shm')
    
    db_size = db_file.stat().st_size if db_file.exists() else 0
    wal_size = wal_file.stat().st_size if wal_file.exists() else 0
    shm_size = shm_file.stat().st_size if shm_file.exists() else 0
    
    return {
        'db_size_kb': db_size / 1024,
        'wal_size_kb': wal_size / 1024,
        'shm_size_kb': shm_size / 1024,
        'wal_ratio': wal_size / db_size if db_size > 0 else 0,
        'total_kb': (db_size + wal_size + shm_size) / 1024,
    }


def run_all_benchmarks():
    """运行所有基准测试"""
    print("=" * 70)
    print("  QuickAgents v2.7.6 性能基准测试")
    print("=" * 70)
    
    # 创建临时目录
    test_dir = tempfile.mkdtemp(prefix='qa_bench_')
    db_path = os.path.join(test_dir, 'bench.db')
    
    try:
        # ========== 1. 单条读取 ==========
        print("\n📊 基准1: 单条读取性能")
        print("-" * 50)
        
        db = UnifiedDB(db_path)
        read_result = bench_single_read(db, iterations=500)
        db.close()
        
        print(f"  迭代次数: {read_result.iterations}")
        print(f"  平均耗时: {read_result.avg_ms:.3f} ms")
        print(f"  中位数:   {read_result.median_ms:.3f} ms")
        print(f"  最小:     {read_result.min_ms:.3f} ms")
        print(f"  最大:     {read_result.max_ms:.3f} ms")
        print(f"  标准差:   {read_result.stdev_ms:.3f} ms")
        print(f"  QPS:      {1000 / read_result.avg_ms:.0f} ops/sec")
        
        # ========== 2. 批量写入 ==========
        print("\n📊 基准2: 批量写入性能")
        print("-" * 50)
        
        db = UnifiedDB(db_path)
        batch_results = bench_batch_write(db)
        db.close()
        
        for batch_size, result in batch_results.items():
            per_item = result.avg_ms / batch_size
            print(f"  batch={batch_size:>4}: 平均 {result.avg_ms:>8.2f} ms, "
                  f"每条 {per_item:.3f} ms, QPS {1000/per_item:.0f} ops/sec")
        
        # ========== 3. 连接池 ==========
        print("\n📊 基准3: 连接池性能")
        print("-" * 50)
        
        pool_db_path = os.path.join(test_dir, 'pool_bench.db')
        pool_results = bench_connection_pool(pool_db_path)
        
        for name, data in pool_results.items():
            print(f"\n  [{data['config']}]")
            print(f"    平均获取: {data['avg_ms']:.3f} ms")
            print(f"    P50:      {data['p50_ms']:.3f} ms")
            if 'metrics' in data and data['metrics']:
                m = data['metrics']
                if isinstance(m, dict) and 'metrics' in m:
                    mm = m['metrics']
                    print(f"    命中率:   {mm.get('hit_rate', 'N/A')}")
                    print(f"    池大小:   {m.get('pool_size', 'N/A')}")
        
        # ========== 4. WAL 增长 ==========
        print("\n📊 基准4: WAL文件增长")
        print("-" * 50)
        
        wal_db_path = os.path.join(test_dir, 'wal_bench.db')
        wal_result = bench_wal_growth(wal_db_path)
        
        print(f"  DB大小:    {wal_result['db_size_kb']:.1f} KB")
        print(f"  WAL大小:   {wal_result['wal_size_kb']:.1f} KB")
        print(f"  SHM大小:   {wal_result['shm_size_kb']:.1f} KB")
        print(f"  WAL比率:   {wal_result['wal_ratio']:.2f}x")
        print(f"  总占用:    {wal_result['total_kb']:.1f} KB")
        
        wal_controllable = wal_result['wal_ratio'] < 2.0
        print(f"  WAL可控:   {'✅ 是' if wal_controllable else '⚠️ WAL偏大'}")
        
        # ========== 总结 ==========
        print("\n" + "=" * 70)
        print("  测试总结")
        print("=" * 70)
        
        checks = {
            "单条读取 (QPS)": 1000 / read_result.avg_ms,
            "批量写入10条/批": batch_results[10].avg_ms,
            "WAL文件可控": wal_controllable,
        }
        
        all_pass = True
        for name, value in checks.items():
            if isinstance(value, bool):
                status = "✅ PASS" if value else "❌ FAIL"
                print(f"  {name}: {status}")
                if not value:
                    all_pass = False
            else:
                print(f"  {name}: {value:.1f}")
        
        print(f"\n  结论: {'✅ 所有基准通过' if all_pass else '⚠️ 部分基准需关注'}")
        
    finally:
        # 清理
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == '__main__':
    run_all_benchmarks()
