---
name: vero-evaluation-skill
description: |
  VeRO (Versioning-Rewards-Observations) evaluation skill based on VeRO paper.
  Provides task snapshot versioning, budget-controlled evaluation, and structured tracking.
license: MIT
allowed-tools:
  - read
  - write
  - bash
metadata:
  category: evaluation
  priority: medium
  version: 1.0.0
---

# VeRO Evaluation Skill

---

## 一、核心概念

### 1.1 VeRO 三大核心能力

```
V - Versioning (版本化)
    └─ 任务执行快照，支持回溯和对比

E - Rewards (奖励评估)
    └─ 预算控制的评估指标，量化任务效果

O - Observations (观察追踪)
    └─ 结构化的执行追踪，记录推理过程
```

### 1.2 评估框架架构

```
┌─────────────────────────────────────────────────────────────┐
│                    VeRO Evaluation Framework                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Versioning Layer (版本化层)                                │
│  ├─ Snapshot Manager    管理执行快照                        │
│  ├─ Version Control     版本对比与回溯                      │
│  └─ State Persistence   状态持久化存储                      │
│                                                             │
│  Rewards Layer (评估层)                                     │
│  ├─ Metrics Collector   指标收集器                          │
│  ├─ Budget Controller   预算控制器                          │
│  └─ Score Calculator    评分计算器                          │
│                                                             │
│  Observations Layer (追踪层)                                │
│  ├─ Trace Recorder      执行追踪记录                        │
│  ├─ Reasoning Logger    推理过程日志                        │
│  └─ Error Analyzer      错误模式分析                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、版本化快照 (Versioning)

### 2.1 快照结构

```yaml
# .opencode/snapshots/snapshot-20260327-001.yaml

snapshot_id: snap-20260327-001
created_at: 2026-03-27T10:30:00Z
task_id: T001
task_name: "实现用户认证模块"

state:
  files_modified:
    - src/auth/user.ts
    - src/auth/token.ts
    - tests/auth.test.ts
  
  tests_status:
    total: 15
    passed: 14
    failed: 1
  
  code_metrics:
    lines_added: 245
    lines_deleted: 12
    complexity_score: 3.2

metadata:
  commit_hash: abc123def
  branch: feature/auth
  duration_minutes: 45
```

### 2.2 快照管理

```python
class SnapshotManager:
    """快照管理器"""
    
    MAX_SNAPSHOTS = 10  # 最大保留快照数
    SNAPSHOT_DIR = ".opencode/snapshots/"
    
    def create_snapshot(self, task_id: str, state: dict) -> str:
        """创建执行快照"""
        snapshot_id = f"snap-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        snapshot = {
            "snapshot_id": snapshot_id,
            "created_at": datetime.utcnow().isoformat(),
            "task_id": task_id,
            "state": state
        }
        
        # 保存快照
        self._save(snapshot)
        
        # 清理旧快照
        self._cleanup_old_snapshots()
        
        return snapshot_id
    
    def compare_snapshots(self, id1: str, id2: str) -> dict:
        """对比两个快照的差异"""
        snap1 = self._load(id1)
        snap2 = self._load(id2)
        
        return {
            "files_diff": self._diff_files(snap1, snap2),
            "tests_diff": self._diff_tests(snap1, snap2),
            "metrics_diff": self._diff_metrics(snap1, snap2)
        }
    
    def rollback_to_snapshot(self, snapshot_id: str):
        """回滚到指定快照状态"""
        snapshot = self._load(snapshot_id)
        # 恢复文件状态
        # 恢复测试状态
        # 更新工作记忆
```

### 2.3 快照触发时机

| 触发点 | 快照类型 | 保留策略 |
|--------|----------|----------|
| 任务开始 | start_snapshot | 保留至任务完成 |
| 测试通过 | milestone_snapshot | 保留30天 |
| Git提交 | commit_snapshot | 永久保留 |
| 任务完成 | completion_snapshot | 永久保留 |
| 错误恢复 | recovery_snapshot | 保留7天 |

---

## 三、奖励评估 (Rewards)

### 3.1 评估指标体系

```yaml
# .opencode/evaluation/metrics.yaml

metrics:
  task_completion_rate:
    weight: 0.30
    description: "任务完成率"
    calculation: "completed_tasks / total_tasks"
    
  test_pass_rate:
    weight: 0.25
    description: "测试通过率"
    calculation: "passed_tests / total_tests"
    
  code_quality_score:
    weight: 0.20
    description: "代码质量评分"
    factors:
      - complexity: 0.3
      - coverage: 0.4
      - lint_score: 0.3
    
  time_efficiency:
    weight: 0.15
    description: "时间效率"
    calculation: "estimated_time / actual_time"
    
  error_recovery_rate:
    weight: 0.10
    description: "错误恢复率"
    calculation: "recovered_errors / total_errors"
```

### 3.2 预算控制

```python
class BudgetController:
    """预算控制器"""
    
    DEFAULT_BUDGET = {
        "max_llm_calls": 100,      # 单任务最大LLM调用次数
        "max_tool_calls": 500,     # 单任务最大工具调用次数
        "max_time_minutes": 120,   # 单任务最大时间(分钟)
        "max_tokens": 500000       # 单任务最大token数
    }
    
    def __init__(self, budget: dict = None):
        self.budget = {**self.DEFAULT_BUDGET, **(budget or {})}
        self.usage = {
            "llm_calls": 0,
            "tool_calls": 0,
            "time_start": datetime.now(),
            "tokens_used": 0
        }
    
    def check_budget(self) -> dict:
        """检查预算使用情况"""
        elapsed = (datetime.now() - self.usage["time_start"]).total_seconds() / 60
        
        return {
            "llm_calls": {
                "used": self.usage["llm_calls"],
                "limit": self.budget["max_llm_calls"],
                "percentage": self.usage["llm_calls"] / self.budget["max_llm_calls"] * 100
            },
            "tool_calls": {
                "used": self.usage["tool_calls"],
                "limit": self.budget["max_tool_calls"],
                "percentage": self.usage["tool_calls"] / self.budget["max_tool_calls"] * 100
            },
            "time": {
                "used_minutes": elapsed,
                "limit_minutes": self.budget["max_time_minutes"],
                "percentage": elapsed / self.budget["max_time_minutes"] * 100
            },
            "tokens": {
                "used": self.usage["tokens_used"],
                "limit": self.budget["max_tokens"],
                "percentage": self.usage["tokens_used"] / self.budget["max_tokens"] * 100
            }
        }
    
    def should_warn(self) -> bool:
        """是否应该发出预算警告"""
        status = self.check_budget()
        return any(s["percentage"] > 80 for s in status.values())
    
    def is_exceeded(self) -> bool:
        """是否已超出预算"""
        status = self.check_budget()
        return any(s["percentage"] >= 100 for s in status.values())
```

### 3.3 评分计算

```python
class ScoreCalculator:
    """评分计算器"""
    
    def calculate_task_score(self, task_result: dict, metrics: dict) -> float:
        """
        计算任务综合评分
        
        Args:
            task_result: 任务执行结果
            metrics: 评估指标配置
        
        Returns:
            综合评分 (0-100)
        """
        scores = {}
        
        for metric_name, config in metrics.items():
            weight = config["weight"]
            raw_score = self._calculate_metric(metric_name, task_result)
            scores[metric_name] = raw_score * weight
        
        total_score = sum(scores.values())
        return min(100, max(0, total_score))
    
    def _calculate_metric(self, metric_name: str, result: dict) -> float:
        """计算单个指标得分"""
        if metric_name == "task_completion_rate":
            return 100 if result.get("completed") else 0
        
        elif metric_name == "test_pass_rate":
            passed = result.get("tests_passed", 0)
            total = result.get("tests_total", 1)
            return (passed / total) * 100
        
        elif metric_name == "code_quality_score":
            return result.get("quality_score", 0)
        
        elif metric_name == "time_efficiency":
            estimated = result.get("estimated_time", 1)
            actual = result.get("actual_time", 1)
            return min(100, (estimated / actual) * 100)
        
        elif metric_name == "error_recovery_rate":
            recovered = result.get("errors_recovered", 0)
            total = result.get("errors_total", 1)
            return (recovered / total) * 100
        
        return 0
```

---

## 四、观察追踪 (Observations)

### 4.1 执行追踪结构

```yaml
# .opencode/traces/trace-20260327-001.yaml

trace_id: trace-20260327-001
task_id: T001
started_at: 2026-03-27T10:00:00Z
ended_at: 2026-03-27T10:45:00Z

execution_flow:
  - step: 1
    action: "read_file"
    target: "src/auth/user.ts"
    result: "success"
    duration_ms: 45
    
  - step: 2
    action: "analyze_code"
    reasoning: "识别到用户认证逻辑需要重构"
    result: "analysis_complete"
    duration_ms: 2300
    
  - step: 3
    action: "write_test"
    target: "tests/auth.test.ts"
    result: "success"
    duration_ms: 1200

tool_calls:
  - name: "read"
    count: 5
    avg_duration_ms: 50
    
  - name: "edit"
    count: 3
    avg_duration_ms: 200
    
  - name: "bash"
    count: 8
    avg_duration_ms: 1500

error_patterns:
  - type: "test_failure"
    message: "Token validation failed"
    occurred_at: "2026-03-27T10:30:00Z"
    resolved: true
    resolution: "修复了token过期时间计算"
```

### 4.2 追踪记录器

```python
class TraceRecorder:
    """执行追踪记录器"""
    
    TRACE_DIR = ".opencode/traces/"
    
    def __init__(self, task_id: str):
        self.trace_id = f"trace-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.task_id = task_id
        self.steps = []
        self.tool_calls = defaultdict(list)
        self.errors = []
    
    def record_step(self, action: str, target: str, result: str, duration_ms: int):
        """记录执行步骤"""
        self.steps.append({
            "step": len(self.steps) + 1,
            "action": action,
            "target": target,
            "result": result,
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def record_tool_call(self, tool_name: str, duration_ms: int, success: bool):
        """记录工具调用"""
        self.tool_calls[tool_name].append({
            "duration_ms": duration_ms,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def record_error(self, error_type: str, message: str, resolved: bool = False):
        """记录错误"""
        self.errors.append({
            "type": error_type,
            "message": message,
            "occurred_at": datetime.utcnow().isoformat(),
            "resolved": resolved
        })
    
    def save(self):
        """保存追踪记录"""
        trace = {
            "trace_id": self.trace_id,
            "task_id": self.task_id,
            "started_at": self.steps[0]["timestamp"] if self.steps else None,
            "ended_at": self.steps[-1]["timestamp"] if self.steps else None,
            "execution_flow": self.steps,
            "tool_calls": self._summarize_tool_calls(),
            "error_patterns": self.errors
        }
        
        self._write_trace(trace)
```

### 4.3 推理日志

```python
class ReasoningLogger:
    """推理过程日志记录器"""
    
    def log_reasoning(self, context: str, reasoning: str, decision: str):
        """
        记录推理过程
        
        Args:
            context: 当前上下文
            reasoning: 推理过程
            decision: 最终决策
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "context": context,
            "reasoning": reasoning,
            "decision": decision
        }
        
        self._append_to_log(entry)
    
    def get_reasoning_chain(self, task_id: str) -> list:
        """获取任务的完整推理链"""
        return self._load_reasoning_log(task_id)
```

---

## 五、评估报告生成

### 5.1 任务评估报告模板

```markdown
# 任务评估报告

## 基本信息
- **任务ID**: T001
- **任务名称**: 实现用户认证模块
- **执行时间**: 2026-03-27 10:00 - 10:45
- **总耗时**: 45分钟

## 综合评分
| 指标 | 得分 | 权重 | 加权得分 |
|------|------|------|----------|
| 任务完成率 | 100 | 0.30 | 30.0 |
| 测试通过率 | 93.3 | 0.25 | 23.3 |
| 代码质量评分 | 85 | 0.20 | 17.0 |
| 时间效率 | 110 | 0.15 | 16.5 |
| 错误恢复率 | 100 | 0.10 | 10.0 |
| **总分** | - | - | **96.8** |

## 预算使用情况
| 资源 | 已用 | 限制 | 使用率 |
|------|------|------|--------|
| LLM调用 | 45 | 100 | 45% |
| 工具调用 | 120 | 500 | 24% |
| 时间 | 45分钟 | 120分钟 | 37.5% |
| Token | 125000 | 500000 | 25% |

## 执行追踪摘要
- 总步骤数: 32
- 工具调用分布:
  - read: 5次 (avg 50ms)
  - edit: 3次 (avg 200ms)
  - bash: 8次 (avg 1500ms)

## 错误分析
- 错误总数: 1
- 已解决: 1
- 解决率: 100%

## 快照信息
- 开始快照: snap-20260327-1000
- 里程碑快照: snap-20260327-1030
- 完成快照: snap-20260327-1045

## 改进建议
1. 测试覆盖率可进一步提升
2. 考虑添加更多边界条件测试
```

### 5.2 报告生成器

```python
class EvaluationReportGenerator:
    """评估报告生成器"""
    
    def generate_report(self, task_id: str) -> str:
        """生成任务评估报告"""
        # 1. 加载快照数据
        snapshots = self._load_snapshots(task_id)
        
        # 2. 加载追踪数据
        trace = self._load_trace(task_id)
        
        # 3. 计算评分
        score = self._calculate_score(task_id)
        
        # 4. 生成报告
        report = self._render_template({
            "task_id": task_id,
            "snapshots": snapshots,
            "trace": trace,
            "score": score
        })
        
        return report
```

---

## 六、与Git集成

### 6.1 Git钩子集成

```bash
# .git/hooks/pre-push

#!/bin/bash

# 在推送前生成评估报告
python .opencode/scripts/generate_evaluation.py

# 检查预算是否超限
python .opencode/scripts/check_budget.py

# 如果超限，阻止推送
if [ $? -ne 0 ]; then
    echo "预算超限，请优化任务执行"
    exit 1
fi
```

### 6.2 提交消息集成

```
feat(auth): 实现用户认证模块

- 添加token生成和验证
- 实现用户登录/登出
- 添加单元测试

Evaluation:
- Score: 96.8
- Test Pass Rate: 93.3%
- Time Efficiency: 110%

Snapshot: snap-20260327-1045
Trace: trace-20260327-001
```

---

## 七、配置文件

### 7.1 完整配置示例

```yaml
# .opencode/evaluation/vero-config.yaml

version: "1.0"
enabled: true

versioning:
  enabled: true
  snapshot_dir: ".opencode/snapshots/"
  max_snapshots: 10
  auto_snapshot:
    - task_start
    - test_pass
    - git_commit
    - task_complete

rewards:
  metrics:
    task_completion_rate:
      weight: 0.30
    test_pass_rate:
      weight: 0.25
    code_quality_score:
      weight: 0.20
    time_efficiency:
      weight: 0.15
    error_recovery_rate:
      weight: 0.10
  
  budget:
    max_llm_calls: 100
    max_tool_calls: 500
    max_time_minutes: 120
    max_tokens: 500000
    warn_threshold: 0.80
    halt_threshold: 1.00

observations:
  enabled: true
  trace_dir: ".opencode/traces/"
  capture:
    - tool_calls
    - reasoning_steps
    - error_patterns
    - performance_metrics
  
  retention_days: 30

reporting:
  auto_generate: true
  output_dir: "Docs/evaluation/"
  format: markdown
  include_snapshots: true
  include_traces: true
```

---

## 八、使用示例

### 8.1 基本使用

```python
# 初始化评估系统
from vero_evaluation import VeROEvaluator

evaluator = VeROEvaluator(config_path=".opencode/evaluation/vero-config.yaml")

# 开始任务评估
evaluator.start_task("T001", "实现用户认证模块")

# 记录执行过程
evaluator.record_step("read_file", "src/auth/user.ts", "success", 45)
evaluator.record_tool_call("read", 45, True)

# 创建快照
evaluator.create_snapshot("milestone", {"tests_passed": 14})

# 结束任务评估
result = evaluator.end_task()

# 生成报告
report = evaluator.generate_report()
print(report)
```

### 8.2 CLI命令

```bash
# 手动创建快照
/vero-snapshot create [task_id] [type]

# 对比快照
/vero-snapshot compare <id1> <id2>

# 查看评估报告
/vero-report [task_id]

# 检查预算
/vero-budget check

# 查看追踪
/vero-trace [task_id]
```

---

## 九、最佳实践

### 9.1 快照策略

| 任务类型 | 快照频率 | 保留策略 |
|----------|----------|----------|
| 简单任务 | 开始+完成 | 7天 |
| 中等任务 | 里程碑+完成 | 30天 |
| 复杂任务 | 每30分钟 | 永久 |
| 关键任务 | 每个步骤 | 永久 |

### 9.2 预算设置指南

| 项目规模 | LLM调用 | 工具调用 | 时间 | Token |
|----------|---------|----------|------|-------|
| 小型 | 50 | 200 | 60min | 200K |
| 中型 | 100 | 500 | 120min | 500K |
| 大型 | 200 | 1000 | 240min | 1M |

---

## 十、参考资源

| 资源 | 链接 |
|------|------|
| VeRO论文 | arXiv:2602.22480 |
| OpenDev论文 | arXiv:2603.05344v2 |
| SWE-agent | github.com/SWE-agent/SWE-agent |

---

*Skill版本: v1.0 | 创建日期: 2026-03-27 | 来源: VeRO论文*
