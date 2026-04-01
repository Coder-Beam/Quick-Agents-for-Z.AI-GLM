---
name: doom-loop-skill
description: Doom-Loop检测机制 - 检测重复工具调用循环，防止无限循环
version: 1.0.0
created_at: 2026-03-27
source: OpenDev论文 (arXiv:2603.05344v2)
---

# Doom-Loop Skill - 循环检测机制

## 核心理念

来自OpenDev论文：**Doom-Loop检测** 防止Agent陷入重复工具调用循环。

```
问题场景:
Agent尝试修复问题 → 工具A失败 → 工具B → 又回到工具A → 无限循环

检测机制:
记录工具调用指纹 → 统计重复次数 → 超过阈值触发用户确认

解决效果:
防止token浪费、时间浪费、用户体验恶化
```

## 核心常量

```python
DOOM_LOOP_CONFIG = {
    "THRESHOLD": 3,              # 重复次数阈值
    "WINDOW_SIZE": 20,           # 检测窗口大小
    "ACTION": "approval_pause",  # 触发动作
    "MAX_HISTORY": 100,          # 最大历史记录
    "STUCK_THRESHOLD": 5,        # Stuck模式阈值
    "OSCILLATION_THRESHOLD": 3   # Oscillation模式阈值
}
```

## 指纹计算算法

### 工具调用指纹

```python
import hashlib
import json
from collections import Counter, deque

def calculate_fingerprint(tool_name: str, tool_args: dict) -> str:
    """
    计算工具调用的唯一指纹
    
    设计原则:
    1. 相同工具+相同参数 = 相同指纹
    2. 参数顺序不影响指纹
    3. 敏感参数需要脱敏
    """
    # 规范化参数（排序键）
    normalized_args = json.dumps(tool_args, sort_keys=True, ensure_ascii=False)
    
    # 计算MD5
    fingerprint = hashlib.md5(
        f"{tool_name}:{normalized_args}".encode('utf-8')
    ).hexdigest()[:16]  # 取前16位足够
    
    return fingerprint
```

### 敏感参数处理

```python
SENSITIVE_PARAMS = ["password", "token", "api_key", "secret"]

def sanitize_args(args: dict) -> dict:
    """脱敏敏感参数"""
    sanitized = args.copy()
    for key in SENSITIVE_PARAMS:
        if key in sanitized:
            sanitized[key] = "***REDACTED***"
    return sanitized
```

## 检测逻辑

### Doom-Loop检测器

```python
class DoomLoopDetector:
    """
    Doom-Loop检测器
    
    使用滑动窗口检测重复工具调用模式
    """
    
    def __init__(self, config: dict = None):
        self.config = config or DOOM_LOOP_CONFIG
        self.fingerprints = deque(maxlen=self.config["MAX_HISTORY"])
        self.loop_detected = False
        self.detected_patterns = []
    
    def check(self, tool_calls: list) -> tuple[bool, list]:
        """
        检查工具调用是否触发Doom-Loop
        
        Args:
            tool_calls: 工具调用列表
            
        Returns:
            (is_doom_loop, repeated_patterns)
        """
        # 计算本次调用的指纹
        current_fingerprints = []
        for tc in tool_calls:
            fp = calculate_fingerprint(tc["name"], tc.get("args", {}))
            current_fingerprints.append(fp)
            self.fingerprints.append(fp)
        
        # 检查窗口内的重复
        window = list(self.fingerprints)[-self.config["WINDOW_SIZE"]:]
        counter = Counter(window)
        
        # 找出超过阈值的指纹
        repeated = [
            {"fingerprint": fp, "count": count}
            for fp, count in counter.items()
            if count >= self.config["THRESHOLD"]
        ]
        
        if repeated:
            self.loop_detected = True
            self.detected_patterns = repeated
            return True, repeated
        
        return False, []
    
    def reset(self):
        """重置检测器状态"""
        self.fingerprints.clear()
        self.loop_detected = False
        self.detected_patterns = []
    
    def get_status(self) -> dict:
        """获取检测器状态"""
        window = list(self.fingerprints)[-self.config["WINDOW_SIZE"]:]
        counter = Counter(window)
        
        return {
            "total_calls": len(self.fingerprints),
            "window_size": self.config["WINDOW_SIZE"],
            "threshold": self.config["THRESHOLD"],
            "unique_in_window": len(counter),
            "most_common": counter.most_common(5),
            "loop_detected": self.loop_detected
        }
```

## 触发动作

### 1. 用户确认暂停 (approval_pause)

```python
def approval_pause_action(patterns: list) -> str:
    """
    触发用户确认暂停
    
    向用户展示重复模式，请求确认是否继续
    """
    message = """
🚨 检测到重复工具调用循环

以下工具调用已重复超过阈值：

{patterns}

可能的原因：
1. 工具参数不正确
2. 目标文件/资源不存在
3. 权限不足
4. 需要更换策略

建议操作：
1. 检查工具参数是否正确
2. 尝试不同的工具或方法
3. 向用户确认目标是否可达
4. 考虑跳过此步骤或标记为阻塞

是否继续执行？[y/N]
""".format(
        patterns="\n".join(
            f"- {p['fingerprint']}: {p['count']}次"
            for p in patterns
        )
    )
    
    return message
```

### 2. 自动策略切换 (strategy_switch)

```python
def strategy_switch_action(patterns: list, context: dict) -> dict:
    """
    自动切换策略
    
    根据重复模式自动选择替代方案
    """
    suggestions = {
        "read_file_loop": {
            "alternative": "glob + selective read",
            "reason": "避免重复读取同一文件"
        },
        "bash_command_loop": {
            "alternative": "检查命令输出，修改参数",
            "reason": "命令可能执行失败"
        },
        "edit_file_loop": {
            "alternative": "检查文件是否被锁定或内容已变化",
            "reason": "编辑可能冲突"
        }
    }
    
    return {
        "action": "switch_strategy",
        "patterns": patterns,
        "suggestions": suggestions
    }
```

## 与QuickAgents集成

### 使用方式

```python
# 在Agent循环中集成
detector = DoomLoopDetector()

while True:
    response = llm.call(messages, tools)
    
    if response.stop_reason != "tool_use":
        break
    
    # Doom-Loop检测
    is_loop, patterns = detector.check(response.tool_calls)
    
    if is_loop:
        # 触发用户确认
        confirmation = approval_pause_action(patterns)
        user_input = ask_user(confirmation)
        
        if user_input.lower() != 'y':
            # 用户选择停止
            break
        
        # 用户选择继续，重置检测器
        detector.reset()
    
    # 执行工具
    results = execute_tools(response.tool_calls)
    messages.append(results)
```

### AGENTS.md 集成

```markdown
## Doom-Loop防护

系统内置Doom-Loop检测机制：

- **检测窗口**: 最近20次工具调用
- **触发阈值**: 同一指纹重复3次
- **触发动作**: 暂停并请求用户确认

当检测到重复模式时，Agent会：
1. 暂停执行
2. 展示重复模式分析
3. 提供可能的原因和建议
4. 请求用户确认下一步操作
```

## 调试与日志

### 日志记录

```python
import logging

logger = logging.getLogger("doom_loop")

def log_doom_loop_event(event_type: str, details: dict):
    """记录Doom-Loop事件"""
    logger.warning({
        "event": "doom_loop_detected",
        "type": event_type,
        "details": details,
        "timestamp": datetime.now().isoformat()
    })
```

### 状态监控

```python
def get_doom_loop_metrics(detector: DoomLoopDetector) -> dict:
    """获取Doom-Loop监控指标"""
    status = detector.get_status()
    
    return {
        "metrics": {
            "total_tool_calls": status["total_calls"],
            "unique_patterns": status["unique_in_window"],
            "loop_detected": status["loop_detected"],
            "top_patterns": status["most_common"]
        },
        "health": "unhealthy" if status["loop_detected"] else "healthy"
    }
```

## 最佳实践

### 1. 阈值调优

```
- THRESHOLD=3: 适合大多数场景
- THRESHOLD=5: 宽松模式，适合复杂任务
- THRESHOLD=2: 严格模式，适合简单任务
```

### 2. 窗口大小

```
- WINDOW_SIZE=20: 标准模式
- WINDOW_SIZE=50: 长任务模式
- WINDOW_SIZE=10: 短任务模式
```

### 3. 恢复策略

```
检测到循环后：
1. 分析重复的工具调用
2. 检查工具返回的错误信息
3. 尝试替代工具或方法
4. 必要时向用户报告
```

## 参考资源

- OpenDev论文: arXiv:2603.05344v2
- 核心概念: Doom-Loop Detection
- 相关代码: shareAI/learn-claude-code s03
