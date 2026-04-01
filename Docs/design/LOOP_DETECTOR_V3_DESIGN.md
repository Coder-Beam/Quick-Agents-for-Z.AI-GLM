# LoopDetector V3 设计文档

> 版本: 1.0.0  
> 创建时间: 2026-03-31  
> 状态: 设计评审  
> 作者: 风后-规划

## 目录

1. [概述](#1-概述)
2. [设计决策](#2-设计决策)
3. [架构设计](#3-架构设计)
4. [详细设计](#4-详细设计)
5. [性能优化](#5-性能优化)
6. [旧代码清理](#6-旧代码清理)
7. [测试策略](#7-测试策略)
8. [实施计划](#8-实施计划)

---

## 1. 概述

### 1.1 背景

当前 QuickAgents 存在两套独立的循环检测系统：

| 位置 | 语言 | 状态 | 问题 |
|------|------|------|------|
| `quickagents/core/loop_detector.py` | Python | 未被使用 | 配置不一致，有白名单 |
| `.opencode/plugins/quickagents.ts` | TypeScript | 正在使用 | 本地逻辑，与Python脱节 |

### 1.2 目标

**统一到 Python V3 实现，确保：**
- ✅ 单一检测逻辑，避免冲突
- ✅ 稳定的阈值算法（固定阈值 + 分段策略）
- ✅ 高效的 Plugin-Python 通信
- ✅ 清晰的职责分离

### 1.3 核心原则

| 原则 | 说明 |
|------|------|
| **稳定性第一** | 阈值算法必须稳定可预测 |
| **性能优化** | 减少不必要的 Python 调用 |
| **完全可配置** | 用户可自定义所有参数 |
| **渐进式清理** | 先找到，再验证，后清理 |

---

## 2. 设计决策

### 2.1 阈值策略：分段固定阈值（放弃动态阈值）

**问题分析：**

动态阈值基于失败率计算存在稳定性问题：
- 样本量小时波动大（5次调用中3次失败 = 60%失败率）
- 阈值频繁变化导致行为不可预测
- 边界情况处理复杂

**解决方案：分段固定阈值**

```python
class ThresholdStrategy(Enum):
    """阈值策略"""
    STRICT = "strict"      # 严格模式：阈值=2
    NORMAL = "normal"      # 正常模式：阈值=3（默认）
    RELAXED = "relaxed"    # 宽松模式：阈值=5
    
    AGGRESSIVE = "aggressive"  # 激进模式：连续失败=3即触发
```

**配置方式：**

```json
{
  "loop_detector": {
    "threshold_strategy": "normal",
    "same_failure_threshold": 3,
    "consecutive_failure_threshold": 5
  }
}
```

**稳定性保证：**
- ✅ 阈值固定，行为可预测
- ✅ 用户可根据场景选择策略
- ✅ 无运行时计算，无波动

### 2.2 白名单策略：完全移除

**决策：移除所有白名单**

**理由：**
1. 白名单导致漏洞（白名单工具的真正卡住无法检测）
2. 统一逻辑更简单
3. 失败检测天然区分有效重试和无效循环

### 2.3 重试机制：采用 OpenCode 指数退避

```python
def get_backoff_delay(attempt: int) -> int:
    """
    指数退避（OpenCode 方式）
    
    attempt=1: 2000ms
    attempt=2: 4000ms
    attempt=3: 8000ms
    attempt=4: 16000ms
    attempt=5: 30000ms (cap)
    """
    delay = BACKOFF_BASE_MS * (BACKOFF_MULTIPLIER ** (attempt - 1))
    return min(delay, MAX_BACKOFF_MS)
```

### 2.4 持久化：UnifiedDB 集成

**存储内容：**
- 失败历史记录
- 检测器状态
- 配置快照

**表结构：**

```sql
CREATE TABLE loop_detector_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    state TEXT NOT NULL,           -- idle/busy/retry/stuck
    failure_count INTEGER DEFAULT 0,
    last_failure TEXT,
    last_failure_time REAL,
    config_json TEXT,
    created_at REAL DEFAULT (strftime('%s', 'now')),
    UNIQUE(session_id)
);
```

---

## 3. 架构设计

### 3.1 分层架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        OpenCode 平台                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  OpenCode 内置机制（平台级别）                            │    │
│  │  - LLM API 重试与退避                                    │    │
│  │  - 上下文溢出处理                                        │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  QuickAgents Plugin (quickagents.ts)                     │    │
│  │  ┌─────────────────────────────────────────────────┐     │    │
│  │  │  轻量级本地计数器（仅计数，不判断）              │     │    │
│  │  │  - 调用计数器                                    │     │    │
│  │  │  - 失败计数器                                    │     │    │
│  │  │  - 缓存配置                                      │     │    │
│  │  └─────────────────────────────────────────────────┘     │    │
│  │                        │                                  │    │
│  │                        ▼ 每5次或检测到异常时              │    │
│  │  ┌─────────────────────────────────────────────────┐     │    │
│  │  │  调用 Python LoopDetector V3                   │     │    │
│  │  └─────────────────────────────────────────────────┘     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Python LoopDetector V3 (loop_detector.py)              │    │
│  │  ┌─────────────────────────────────────────────────┐     │    │
│  │  │  核心检测逻辑（唯一判断点）                      │     │    │
│  │  │  - 失败检测                                      │     │    │
│  │  │  - 固定阈值判断                                  │     │    │
│  │  │  - 状态机管理                                    │     │    │
│  │  │  - 持久化存储                                    │     │    │
│  └─────────────────────────────────────────────────────────┘     │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 职责分离

| 层级 | 职责 | 检测内容 | 触发时机 |
|------|------|----------|----------|
| **OpenCode 平台** | LLM API 管理 | API 超时、速率限制 | API 调用时 |
| **Plugin 本地** | 轻量计数 | 调用次数、失败次数 | 每次工具调用 |
| **Python V3** | 深度检测 | 失败模式、阈值判断 | 定期或异常时 |

### 3.3 数据流

```
工具调用
    │
    ▼
┌─────────────────────────────────────┐
│  Plugin: tool.execute.before       │
│  - 本地计数器++                   │
│  - 检查是否需要深度检测          │
│    (每5次 或 有失败)             │
└─────────────────────────────────────┘
    │
    ▼ (需要深度检测时)
┌─────────────────────────────────────┐
│  调用 Python LoopDetectorV3.check() │
│  - 分析失败历史                  │
│  - 判断是否触发阈值              │
│  - 返回检测结果                  │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  根据结果决定：                    │
│  - 继续执行                        │
│  - 抛出 DOOM_LOOP_DETECTED        │
│  - 触发退避重试                    │
└─────────────────────────────────────┘
```

---

## 4. 详细设计

### 4.1 Python LoopDetector V3

#### 4.1.1 核心类设计

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import time
import json

class AgentState(Enum):
    """Agent 状态"""
    IDLE = "idle"          # 空闲
    BUSY = "busy"          # 工作中
    RETRY = "retry"        # 重试中
    STUCK = "stuck"        # 卡住
    DONE = "done"          # 完成

class ThresholdStrategy(Enum):
    """阈值策略"""
    STRICT = "strict"          # 严格：same=2, consecutive=3
    NORMAL = "normal"          # 正常：same=3, consecutive=5
    RELAXED = "relaxed"        # 宽松：same=5, consecutive=8
    AGGRESSIVE = "aggressive"  # 激进：连续3次失败即触发

class FailureType(Enum):
    """失败类型"""
    TRANSIENT = "transient"    # 临时错误（可重试）
    PERMANENT = "permanent"    # 永久错误（不可重试）
    UNKNOWN = "unknown"        # 未知错误

@dataclass
class FailureRecord:
    """失败记录"""
    tool_name: str
    tool_args: Dict[str, Any]
    error_message: str
    error_type: FailureType
    timestamp: float
    fingerprint: str

@dataclass
class ToolCallRecord:
    """工具调用记录"""
    tool_name: str
    tool_args: Dict[str, Any]
    success: bool
    timestamp: float
    fingerprint: str

@dataclass
class LoopDetectorConfig:
    """LoopDetector 配置（完全用户可配置）"""
    
    # 阈值策略
    threshold_strategy: ThresholdStrategy = ThresholdStrategy.NORMAL
    
    # 固定阈值（根据策略自动设置，也可手动覆盖）
    same_failure_threshold: int = 3
    consecutive_failure_threshold: int = 5
    
    # 预算限制
    max_tool_calls: int = 100
    max_time_seconds: int = 600
    
    # 重试机制（OpenCode 方式）
    max_retries: int = 5
    backoff_base_ms: int = 2000
    backoff_multiplier: int = 2
    max_backoff_ms: int = 30000
    
    # 临时错误模式
    transient_error_patterns: List[str] = field(default_factory=lambda: [
        "timeout", "rate_limit", "rate limit", "network", 
        "temporarily", "unavailable", "connection reset"
    ])
    
    # 深度检测触发频率
    deep_check_interval: int = 5  # 每5次调用触发一次深度检测
    
    @classmethod
    def from_file(cls, config_path: str = "quickagents.json") -> 'LoopDetectorConfig':
        """从配置文件加载"""
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                loop_config = config_data.get("loop_detector", {})
                
                # 处理阈值策略
                if "threshold_strategy" in loop_config:
                    loop_config["threshold_strategy"] = ThresholdStrategy(
                        loop_config["threshold_strategy"]
                    )
                
                return cls(**loop_config)
        return cls()
    
    def get_thresholds(self) -> Tuple[int, int]:
        """获取当前阈值（根据策略）"""
        strategy_thresholds = {
            ThresholdStrategy.STRICT: (2, 3),
            ThresholdStrategy.NORMAL: (3, 5),
            ThresholdStrategy.RELAXED: (5, 8),
            ThresholdStrategy.AGGRESSIVE: (3, 3),  # same和consecutive相同
        }
        return strategy_thresholds.get(self.threshold_strategy, (3, 5))
```

#### 4.1.2 主类实现

```python
class LoopDetector:
    """
    LoopDetector V3 - 基于失败检测的循环检测器
    
    核心特性：
    - 分段固定阈值（稳定可预测）
    - 失败检测（区分临时/永久错误）
    - 指数退避重试（OpenCode 方式）
    - 持久化存储（UnifiedDB）
    """
    
    def __init__(self, config: LoopDetectorConfig = None):
        self.config = config or LoopDetectorConfig.from_file()
        
        # 状态
        self.state = AgentState.IDLE
        self.failure_history: List[FailureRecord] = []
        self.call_history: List[ToolCallRecord] = []
        self.session_start_time = time.time()
        
        # 计数器
        self.total_calls = 0
        self.consecutive_failures = 0
        
        # 缓存
        self._fingerprint_cache: Dict[str, int] = {}
        
        # 持久化
        self._load_from_db()
    
    def check(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        result: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        检查工具调用是否触发循环
        
        Args:
            tool_name: 工具名称
            tool_args: 工具参数
            result: 工具执行结果（可选）
            
        Returns:
            (is_loop, info)
            - is_loop: 是否检测到循环
            - info: 详细信息
        """
        now = time.time()
        fingerprint = self._calculate_fingerprint(tool_name, tool_args)
        
        # 1. 检查预算
        budget_exceeded, budget_info = self._check_budget(now)
        if budget_exceeded:
            return True, {
                "type": "budget_exceeded",
                **budget_info
            }
        
        # 2. 记录调用
        self._record_call(tool_name, tool_args, fingerprint, result)
        
        # 3. 如果有结果，分析失败
        if result is not None:
            is_failure, failure_info = self._analyze_result(result)
            
            if is_failure:
                # 记录失败
                self._record_failure(
                    tool_name, tool_args, fingerprint, failure_info
                )
                
                # 检查失败阈值
                failure_exceeded, failure_pattern = self._check_failure_threshold(
                    fingerprint
                )
                
                if failure_exceeded:
                    self.state = AgentState.STUCK
                    return True, {
                        "type": "failure_loop",
                        "state": self.state.value,
                        **failure_pattern
                    }
        
        # 4. 更新状态
        self._update_state()
        
        # 5. 返回正常
        return False, {
            "state": self.state.value,
            "total_calls": self.total_calls,
            "consecutive_failures": self.consecutive_failures
        }
    
    def _check_budget(self, now: float) -> Tuple[bool, Dict[str, Any]]:
        """检查预算是否超限"""
        # 检查调用次数
        if self.total_calls >= self.config.max_tool_calls:
            return True, {
                "reason": "max_tool_calls_exceeded",
                "limit": self.config.max_tool_calls,
                "current": self.total_calls
            }
        
        # 检查时间
        elapsed = now - self.session_start_time
        if elapsed >= self.config.max_time_seconds:
            return True, {
                "reason": "max_time_exceeded",
                "limit": self.config.max_time_seconds,
                "elapsed": elapsed
            }
        
        return False, {}
    
    def _analyze_result(self, result: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """分析结果是否为失败"""
        # 检查显式错误
        if result.get("error"):
            error_msg = result["error"]
            error_type = self._classify_error(error_msg)
            return True, {
                "error": error_msg,
                "error_type": error_type.value,
                "is_transient": error_type == FailureType.TRANSIENT
            }
        
        # 检查显式失败
        if result.get("success") is False:
            return True, {
                "error": "explicit_failure",
                "error_type": FailureType.PERMANENT.value,
                "is_transient": False
            }
        
        return False, {}
    
    def _classify_error(self, error_message: str) -> FailureType:
        """分类错误类型"""
        error_lower = error_message.lower()
        
        for pattern in self.config.transient_error_patterns:
            if pattern.lower() in error_lower:
                return FailureType.TRANSIENT
        
        return FailureType.PERMANENT
    
    def _check_failure_threshold(self, fingerprint: str) -> Tuple[bool, Dict[str, Any]]:
        """检查失败是否超过阈值"""
        same_threshold, consecutive_threshold = self.config.get_thresholds()
        
        # 1. 检查相同失败次数
        same_failures = self._fingerprint_cache.get(fingerprint, 0)
        if same_failures >= same_threshold:
            return True, {
                "pattern": "same_failure_exceeded",
                "fingerprint": fingerprint[:16],
                "count": same_failures,
                "threshold": same_threshold
            }
        
        # 2. 检查连续失败次数
        if self.consecutive_failures >= consecutive_threshold:
            return True, {
                "pattern": "consecutive_failure_exceeded",
                "count": self.consecutive_failures,
                "threshold": consecutive_threshold
            }
        
        return False, {}
    
    def get_backoff_delay(self, attempt: int) -> int:
        """
        获取退避延迟（OpenCode 方式）
        
        Args:
            attempt: 重试次数（1-based）
            
        Returns:
            延迟毫秒数
        """
        if attempt < 1:
            return 0
        
        delay = self.config.backoff_base_ms * (
            self.config.backoff_multiplier ** (attempt - 1)
        )
        return min(delay, self.config.max_backoff_ms)
    
    def _calculate_fingerprint(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """计算工具调用指纹"""
        import hashlib
        normalized = json.dumps(tool_args, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(
            f"{tool_name}:{normalized}".encode('utf-8')
        ).hexdigest()
    
    def _record_call(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        fingerprint: str,
        result: Optional[Dict[str, Any]]
    ):
        """记录工具调用"""
        self.total_calls += 1
        
        record = ToolCallRecord(
            tool_name=tool_name,
            tool_args=tool_args,
            success=result is None or result.get("success", True),
            timestamp=time.time(),
            fingerprint=fingerprint
        )
        
        self.call_history.append(record)
        
        # 保持历史在合理范围
        if len(self.call_history) > 100:
            self.call_history = self.call_history[-50:]
    
    def _record_failure(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        fingerprint: str,
        failure_info: Dict[str, Any]
    ):
        """记录失败"""
        self.consecutive_failures += 1
        self._fingerprint_cache[fingerprint] = self._fingerprint_cache.get(fingerprint, 0) + 1
        
        record = FailureRecord(
            tool_name=tool_name,
            tool_args=tool_args,
            error_message=failure_info.get("error", ""),
            error_type=FailureType(failure_info.get("error_type", "unknown")),
            timestamp=time.time(),
            fingerprint=fingerprint
        )
        
        self.failure_history.append(record)
        
        # 保持历史在合理范围
        if len(self.failure_history) > 50:
            self.failure_history = self.failure_history[-25:]
    
    def _update_state(self):
        """更新状态"""
        if self.consecutive_failures == 0:
            self.state = AgentState.BUSY
        elif self.consecutive_failures > 0 and self.consecutive_failures < 3:
            self.state = AgentState.RETRY
        # STUCK 状态由检测到循环时设置
    
    def _load_from_db(self):
        """从 UnifiedDB 加载状态"""
        try:
            from .unified_db import get_unified_db
            db = get_unified_db()
            # 实现加载逻辑
        except Exception:
            pass  # 首次使用，无历史数据
    
    def _save_to_db(self):
        """保存状态到 UnifiedDB"""
        try:
            from .unified_db import get_unified_db
            db = get_unified_db()
            # 实现保存逻辑
        except Exception:
            pass
    
    def reset(self):
        """重置检测器状态"""
        self.state = AgentState.IDLE
        self.failure_history.clear()
        self.call_history.clear()
        self.consecutive_failures = 0
        self._fingerprint_cache.clear()
    
    def get_status(self) -> Dict[str, Any]:
        """获取检测器状态"""
        same_threshold, consecutive_threshold = self.config.get_thresholds()
        
        return {
            "state": self.state.value,
            "total_calls": self.total_calls,
            "consecutive_failures": self.consecutive_failures,
            "failure_count": len(self.failure_history),
            "thresholds": {
                "same_failure": same_threshold,
                "consecutive_failure": consecutive_threshold
            },
            "config": {
                "strategy": self.config.threshold_strategy.value,
                "max_tool_calls": self.config.max_tool_calls,
                "max_time_seconds": self.config.max_time_seconds
            }
        }


# 全局实例
_global_detector: Optional[LoopDetector] = None


def get_loop_detector() -> LoopDetector:
    """获取全局循环检测器"""
    global _global_detector
    if _global_detector is None:
        _global_detector = LoopDetector()
    return _global_detector
```

### 4.2 Plugin 改造

#### 4.2.1 移除本地检测逻辑

**删除的代码：**

```typescript
// 删除这些常量
const STUCK_THRESHOLD = 5;
const OSCILLATION_MIN = 3;

// 删除这些方法
detectStuck(sequence: ToolCall[]): { detected: boolean; pattern: string }
detectOscillation(sequence: ToolCall[]): { detected: boolean; pattern: string }

// 删除这些状态
const callSequence: ToolCall[] = [];
```

#### 4.2.2 新增轻量级计数器

```typescript
// 轻量级本地计数器
interface LocalCounters {
  totalCalls: number;
  failures: number;
  lastCheckTime: number;
  configCache: LoopDetectorConfig | null;
}

const counters: LocalCounters = {
  totalCalls: 0,
  failures: 0,
  lastCheckTime: 0,
  configCache: null
};

// 缓存配置
const loadConfig = (): LoopDetectorConfig => {
  if (counters.configCache) {
    return counters.configCache;
  }
  
  try {
    const configPath = path.join(directory, "quickagents.json");
    if (fs.existsSync(configPath)) {
      const config = JSON.parse(fs.readFileSync(configPath, "utf-8"));
      counters.configCache = config.loop_detector || {};
    }
  } catch (e) {
    // 使用默认配置
  }
  
  return counters.configCache || {
    deep_check_interval: 5,
    threshold_strategy: "normal"
  };
};
```

#### 4.2.3 调用 Python V3

```typescript
const loopDetector = {
  // 轻量级检查（本地）
  shouldDeepCheck: (): boolean => {
    const config = loadConfig();
    const interval = config.deep_check_interval || 5;
    
    // 每 N 次调用触发一次深度检测
    if (counters.totalCalls % interval === 0) {
      return true;
    }
    
    // 有失败时立即触发深度检测
    if (counters.failures > 0) {
      return true;
    }
    
    return false;
  },
  
  // 深度检查（调用 Python）
  deepCheck: (
    toolName: string, 
    toolArgs: any, 
    result?: any
  ): LocalResult => {
    return callPython(`
from quickagents import get_loop_detector
import json

detector = get_loop_detector()
is_loop, info = detector.check(
    tool_name='${toolName}',
    tool_args=${JSON.stringify(toolArgs)},
    result=${result ? JSON.stringify(result) : 'None'}
)

print(json.dumps({
    "success": True,
    "data": {
        "is_loop": is_loop,
        "info": info
    }
}))
    `, 5000);
  },
  
  // 主检查函数
  check: (
    toolName: string, 
    toolArgs: any,
    result?: any
  ): { detected: boolean; info: any } => {
    // 1. 更新本地计数器
    counters.totalCalls++;
    
    if (result && (result.error || result.success === false)) {
      counters.failures++;
    }
    
    // 2. 检查是否需要深度检测
    if (!loopDetector.shouldDeepCheck()) {
      return { detected: false, info: { source: "local_counter" } };
    }
    
    // 3. 执行深度检测
    const checkResult = loopDetector.deepCheck(toolName, toolArgs, result);
    
    if (checkResult.success && checkResult.data) {
      return {
        detected: checkResult.data.is_loop,
        info: checkResult.data.info
      };
    }
    
    return { detected: false, info: { source: "python_error", error: checkResult.error } };
  }
};
```

---

## 5. 性能优化

### 5.1 问题分析

**Plugin 调用 Python 的性能开销：**

| 操作 | 耗时 | 频率 |
|------|------|------|
| 启动 Python 进程 | ~50-100ms | 每次调用 |
| JSON 序列化 | ~1-5ms | 每次调用 |
| JSON 反序列化 | ~1-5ms | 每次调用 |
| Python 执行 | ~5-20ms | 每次调用 |
| **总计** | **~60-130ms** | 每次调用 |

### 5.2 优化策略：本地轻量 + 定期深度

```
┌─────────────────────────────────────────────────────────────────┐
│                     性能优化策略                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  调用 1: 本地计数++ (0.1ms)                                     │
│  调用 2: 本地计数++ (0.1ms)                                     │
│  调用 3: 本地计数++ (0.1ms)                                     │
│  调用 4: 本地计数++ (0.1ms)                                     │
│  调用 5: 本地计数++ → 触发深度检测 (100ms)                      │
│  调用 6: 本地计数++ (0.1ms)                                     │
│  ...                                                            │
│                                                                 │
│  平均开销: (0.1*4 + 100) / 5 = 20ms/次                          │
│  优化效果: 减少 80%+ 开销                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 配置缓存

```typescript
// 配置只在启动时加载一次
const configCache: Map<string, any> = new Map();

const loadConfigOnce = (key: string, defaultValue: any): any => {
  if (configCache.has(key)) {
    return configCache.get(key);
  }
  
  const config = loadConfig();
  const value = config[key] || defaultValue;
  configCache.set(key, value);
  return value;
};
```

### 5.4 性能对比

| 场景 | 旧方案（每次调用Python） | 新方案（本地+定期） | 提升 |
|------|------------------------|-------------------|------|
| 100次调用 | ~10秒 | ~2秒 | 80% |
| 有失败场景 | ~10秒 | ~2.5秒 | 75% |
| 无失败场景 | ~10秒 | ~0.5秒 | 95% |

---

## 6. 旧代码清理

### 6.1 清理流程："先找到，再验证，后清理"

#### Step 1: 找到所有引用

```bash
# 1. 搜索 Python 文件中的引用
grep -r "LoopDetector|loop_detector|get_loop_detector" --include="*.py" .

# 2. 搜索 TypeScript 文件中的引用
grep -r "STUCK_THRESHOLD|OSCILLATION|detectStuck|detectOscillation" --include="*.ts" .

# 3. 搜索文档中的引用
grep -r "LoopDetector|循环检测" --include="*.md" .
```

#### Step 2: 验证每个引用

**Python 文件引用分析：**

| 文件 | 引用类型 | 是否需要修改 |
|------|----------|---------------|
| `quickagents/__init__.py` | 导出 `LoopDetector` | ✅ 保持（接口不变） |
| `test_loop_detector.py` | 测试旧实现 | ⚠️ 需要更新测试 |
| `test_unified_db.py` | 可能间接引用 | ❓ 需检查 |

**TypeScript 文件引用分析：**

| 文件 | 引用类型 | 是否需要修改 |
|------|----------|---------------|
| `quickagents.ts` | 本地检测逻辑 | ✅ 需要删除并替换 |

**文档引用分析：**

| 文件 | 引用类型 | 是否需要修改 |
|------|----------|---------------|
| `doom-loop-skill/SKILL.md` | 描述旧机制 | ✅ 需要更新 |
| `AGENTS.md` | 配置常量 | ✅ 需要更新 |

#### Step 3: 执行清理

**清理顺序：**

```
1. 【创建】新的 loop_detector.py (V3 实现)
   ↓
2. 【验证】运行单元测试，确保新实现正确
   ↓
3. 【更新】 quickagents/__init__.py（导出接口保持不变）
   ↓
4. 【修改】 quickagents.ts（移除本地逻辑，调用 Python V3）
   ↓
5. 【更新】 doom-loop-skill/SKILL.md（反映 V3 设计）
   ↓
6. 【更新】 AGENTS.md（更新配置常量）
   ↓
7. 【更新】 test_loop_detector.py（适配新实现）
```

### 6.2 回归测试

**清理后必须验证：**

```bash
# 1. 运行单元测试
pytest tests/test_loop_detector.py -v

# 2. 运行集成测试
pytest tests/test_integration.py -v

# 3. 手动验证
# - 启动 OpenCode
# - 执行工具调用
# - 检查日志来源（应显示 [QuickAgents]）
# - 验证检测行为
```

---

## 7. 测试策略

### 7.1 单元测试

| 测试类 | 测试内容 | 优先级 |
|--------|----------|--------|
| `TestLoopDetectorConfig` | 配置加载、阈值计算 | P0 |
| `TestFailureDetection` | 失败分析、错误分类 | P0 |
| `TestThresholdCheck` | 相同失败、连续失败阈值 | P0 |
| `TestBackoffDelay` | 指数退避计算 | P1 |
| `TestStateManagement` | 状态转换 | P1 |
| `TestPersistence` | UnifiedDB 存取 | P1 |

### 7.2 集成测试

| 测试场景 | 验证内容 | 优先级 |
|----------|----------|--------|
| Plugin-Python 通信 | 调用链路正确性 | P0 |
| 性能测试 | 调用开销 < 阈值 | P1 |
| 配置热加载 | 修改配置后生效 | P2 |

### 7.3 测试用例示例

```python
class TestLoopDetectorV3:
    """LoopDetector V3 单元测试"""
    
    def test_config_loading(self):
        """测试配置加载"""
        config = LoopDetectorConfig.from_file("quickagents.json")
        assert config.threshold_strategy == ThresholdStrategy.NORMAL
        assert config.same_failure_threshold == 3
    
    def test_failure_detection_transient(self):
        """测试临时错误检测"""
        detector = LoopDetector()
        
        result = {"error": "timeout: connection reset"}
        is_loop, info = detector.check("bash", {"cmd": "test"}, result)
        
        assert info.get("error_type") == "transient"
    
    def test_same_failure_threshold(self):
        """测试相同失败阈值"""
        detector = LoopDetector()
        
        # 连续3次相同失败
        for i in range(3):
            result = {"error": "file not found"}
            is_loop, info = detector.check("read", {"path": "missing.txt"}, result)
        
        assert is_loop is True
        assert info["pattern"] == "same_failure_exceeded"
    
    def test_consecutive_failure_threshold(self):
        """测试连续失败阈值"""
        detector = LoopDetector()
        
        # 连续5次不同失败
        for i in range(5):
            result = {"error": f"error {i}"}
            is_loop, info = detector.check("bash", {"cmd": f"cmd{i}"}, result)
        
        assert is_loop is True
        assert info["pattern"] == "consecutive_failure_exceeded"
    
    def test_backoff_delay(self):
        """测试指数退避"""
        detector = LoopDetector()
        
        assert detector.get_backoff_delay(1) == 2000
        assert detector.get_backoff_delay(2) == 4000
        assert detector.get_backoff_delay(3) == 8000
        assert detector.get_backoff_delay(4) == 16000
        assert detector.get_backoff_delay(5) == 30000  # cap
        assert detector.get_backoff_delay(10) == 30000  # cap
    
    def test_budget_exceeded(self):
        """测试预算超限"""
        config = LoopDetectorConfig(max_tool_calls=5)
        detector = LoopDetector(config)
        
        # 执行5次调用
        for i in range(5):
            detector.check("read", {"path": f"file{i}.txt"})
        
        # 第6次应该超限
        is_loop, info = detector.check("read", {"path": "file6.txt"})
        assert is_loop is True
        assert info["type"] == "budget_exceeded"
```

---

## 8. 实施计划

### 8.1 阶段划分

```
Phase 1: Python 核心实现 (约2小时)
├── 创建 LoopDetectorConfig
├── 实现 LoopDetector V3
├── 编写单元测试
└── 验证功能正确

Phase 2: Plugin 改造 (约1小时)
├── 移除本地检测逻辑
├── 实现轻量级计数器
├── 集成 Python V3 调用
└── 测试通信链路

Phase 3: 配置与文档 (约1小时)
├── 创建 quickagents.json
├── 更新 SKILL.md
├── 更新 AGENTS.md
└── 创建配置示例

Phase 4: 清理与验证 (约1小时)
├── 搜索旧代码引用
├── 验证所有引用
├── 执行清理
└── 运行回归测试

Phase 5: 集成测试 (约1小时)
├── 端到端测试
├── 性能测试
└── 文档审查

总计: 约6小时
```

### 8.2 里程碑

| 里程碑 | 交付物 | 验收标准 |
|--------|--------|----------|
| M1 | Python V3 实现 | 单元测试100%通过 |
| M2 | Plugin 改造完成 | 通信链路正常 |
| M3 | 配置与文档更新 | 用户可配置 |
| M4 | 旧代码清理完成 | 无残留引用 |
| M5 | 集成测试通过 | 性能提升>50% |

### 8.3 风险与应对

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| Python 调用性能不达标 | 低 | 高 | 减少调用频率，优化序列化 |
| 配置加载失败 | 中 | 中 | 使用默认配置，记录警告 |
| 旧代码清理遗漏 | 中 | 高 | 多轮搜索，代码审查 |
| 测试覆盖不足 | 低 | 高 | 补充边界测试 |

---

## 附录

### A. 配置文件示例

```json
{
  "loop_detector": {
    "threshold_strategy": "normal",
    "same_failure_threshold": 3,
    "consecutive_failure_threshold": 5,
    "max_tool_calls": 100,
    "max_time_seconds": 600,
    "max_retries": 5,
    "backoff_base_ms": 2000,
    "backoff_multiplier": 2,
    "max_backoff_ms": 30000,
    "transient_error_patterns": [
      "timeout",
      "rate_limit",
      "rate limit",
      "network",
      "temporarily",
      "unavailable",
      "connection reset"
    ],
    "deep_check_interval": 5
  }
}
```

### B. 状态转换图

```
┌───────┐
│ IDLE  │ ← 初始状态
└───┬───┘
    │ 首次调用
    ▼
┌───────┐
│ BUSY  │ ← 正常工作
└───┬───┘
    │ 检测到失败
    ▼
┌───────┐
│ RETRY │ ← 重试中
└───┬───┘
    │ 失败超过阈值
    ▼
┌───────┐
│ STUCK │ ← 卡住（触发警告）
└───────┘
    │ 用户确认后
    ▼
┌───────┐
│ BUSY  │ ← 恢复工作
└───────┘
```

### C. 错误分类决策树

```
错误消息
    │
    ▼
包含临时错误关键词？
    │
    ├─ 是 → TRANSIENT（可重试）
    │
    └─ 否 → PERMANENT（不可重试）
```

---

**文档结束**

> 请审查此设计文档，确认后开始实施。
