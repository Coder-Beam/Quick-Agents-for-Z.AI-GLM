import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CompressionTier(Enum):
    NONE = "none"
    MICRO = "micro"
    LLM = "llm"
    EMERGENCY = "emergency"


@dataclass
class ToolOutput:
    tool_name: str
    content: str
    token_estimate: int
    turn_index: int
    is_key_file: bool = False


@dataclass
class CompressionResult:
    tier: CompressionTier
    original_tokens: int
    compressed_tokens: int
    savings_pct: float
    outputs_removed: int
    outputs_trimmed: int
    key_files_preserved: int
    llm_prompt: Optional[str] = None


class ContextCompressor:
    """两级上下文压缩器

    基于上下文使用率自动选择压缩策略：
    - MICRO: 移除旧的工具输出，裁剪大体积输出
    - LLM: 生成摘要提示词，由大模型执行深度压缩
    - EMERGENCY: 激进裁剪，仅保留关键文件
    """

    THRESHOLDS: Dict[int, CompressionTier] = {
        70: CompressionTier.NONE,
        80: CompressionTier.MICRO,
        85: CompressionTier.MICRO,
        90: CompressionTier.LLM,
        95: CompressionTier.EMERGENCY,
    }

    MAX_OUTPUT_CHARS = 8000

    def __init__(self):
        self._outputs: List[ToolOutput] = []
        self._current_turn: int = 0

    def record_output(
        self,
        tool_name: str,
        content: str,
        turn_index: int,
        is_key_file: bool = False,
    ):
        """记录工具输出，用于后续压缩决策"""
        tokens = self._estimate_tokens(content)
        output = ToolOutput(
            tool_name=tool_name,
            content=content,
            token_estimate=tokens,
            turn_index=turn_index,
            is_key_file=is_key_file,
        )
        self._outputs.append(output)
        self._current_turn = max(self._current_turn, turn_index)
        logger.debug(
            "记录工具输出: %s, turn=%d, tokens≈%d, key=%s",
            tool_name,
            turn_index,
            tokens,
            is_key_file,
        )

    def check_and_compress(self, context_usage_pct: float) -> CompressionResult:
        """根据上下文使用率自动选择压缩策略

        Args:
            context_usage_pct: 上下文使用百分比（0-100）

        Returns:
            CompressionResult: 压缩结果
        """
        tier = CompressionTier.NONE
        for threshold in sorted(self.THRESHOLDS.keys(), reverse=True):
            if context_usage_pct >= threshold:
                tier = self.THRESHOLDS[threshold]
                break

        if tier == CompressionTier.NONE:
            return CompressionResult(
                tier=tier,
                original_tokens=0,
                compressed_tokens=0,
                savings_pct=0.0,
                outputs_removed=0,
                outputs_trimmed=0,
                key_files_preserved=0,
            )

        if tier == CompressionTier.MICRO:
            aggressive = context_usage_pct >= 85
            return self.micro_compact(context_usage_pct, aggressive=aggressive)

        if tier == CompressionTier.LLM:
            result = self.micro_compact(context_usage_pct, aggressive=True)
            result.llm_prompt = self._generate_llm_prompt(context_usage_pct)
            result.tier = CompressionTier.LLM
            return result

        if tier == CompressionTier.EMERGENCY:
            return self._emergency_compact(context_usage_pct)

        return CompressionResult(
            tier=CompressionTier.NONE,
            original_tokens=0,
            compressed_tokens=0,
            savings_pct=0.0,
            outputs_removed=0,
            outputs_trimmed=0,
            key_files_preserved=0,
        )

    def micro_compact(self, context_usage_pct: float, aggressive: bool = False) -> CompressionResult:
        """微压缩：移除旧的非关键输出，裁剪大体积输出

        Args:
            context_usage_pct: 上下文使用百分比
            aggressive: 是否使用激进策略（保留更少的轮次）

        Returns:
            CompressionResult: 压缩结果
        """
        original_tokens = sum(o.token_estimate for o in self._outputs)
        outputs_removed = 0
        outputs_trimmed = 0
        key_files_preserved = 0

        max_age_turns = 2 if aggressive else 3
        filtered: List[ToolOutput] = []

        for output in self._outputs:
            age = self._current_turn - output.turn_index

            if self._should_preserve(output):
                key_files_preserved += 1
                if len(output.content) > self.MAX_OUTPUT_CHARS:
                    trimmed_content = self._trim_content(output.content, self.MAX_OUTPUT_CHARS)
                    trimmed_tokens = self._estimate_tokens(trimmed_content)
                    filtered.append(
                        ToolOutput(
                            tool_name=output.tool_name,
                            content=trimmed_content,
                            token_estimate=trimmed_tokens,
                            turn_index=output.turn_index,
                            is_key_file=output.is_key_file,
                        )
                    )
                    outputs_trimmed += 1
                else:
                    filtered.append(output)
                continue

            if age > max_age_turns:
                outputs_removed += 1
                continue

            if len(output.content) > self.MAX_OUTPUT_CHARS:
                max_len = self.MAX_OUTPUT_CHARS // 2 if aggressive else self.MAX_OUTPUT_CHARS
                trimmed_content = self._trim_content(output.content, max_len)
                trimmed_tokens = self._estimate_tokens(trimmed_content)
                filtered.append(
                    ToolOutput(
                        tool_name=output.tool_name,
                        content=trimmed_content,
                        token_estimate=trimmed_tokens,
                        turn_index=output.turn_index,
                        is_key_file=output.is_key_file,
                    )
                )
                outputs_trimmed += 1
            else:
                filtered.append(output)

        self._outputs = filtered
        compressed_tokens = sum(o.token_estimate for o in self._outputs)
        savings_pct = ((original_tokens - compressed_tokens) / original_tokens * 100) if original_tokens > 0 else 0.0

        logger.info(
            "微压缩完成: tier=%s, aggressive=%s, 移除=%d, 裁剪=%d, 关键文件=%d, 节省=%.1f%%",
            "MICRO",
            aggressive,
            outputs_removed,
            outputs_trimmed,
            key_files_preserved,
            savings_pct,
        )

        return CompressionResult(
            tier=CompressionTier.MICRO,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            savings_pct=round(savings_pct, 2),
            outputs_removed=outputs_removed,
            outputs_trimmed=outputs_trimmed,
            key_files_preserved=key_files_preserved,
        )

    def _emergency_compact(self, context_usage_pct: float) -> CompressionResult:
        """紧急压缩：仅保留关键文件和最近一轮的输出"""
        original_tokens = sum(o.token_estimate for o in self._outputs)
        outputs_removed = 0
        outputs_trimmed = 0
        key_files_preserved = 0
        filtered: List[ToolOutput] = []

        for output in self._outputs:
            if output.is_key_file:
                key_files_preserved += 1
                max_len = self.MAX_OUTPUT_CHARS // 2
                if len(output.content) > max_len:
                    trimmed = self._trim_content(output.content, max_len)
                    filtered.append(
                        ToolOutput(
                            tool_name=output.tool_name,
                            content=trimmed,
                            token_estimate=self._estimate_tokens(trimmed),
                            turn_index=output.turn_index,
                            is_key_file=output.is_key_file,
                        )
                    )
                    outputs_trimmed += 1
                else:
                    filtered.append(output)
                continue

            if output.turn_index == self._current_turn:
                max_len = self.MAX_OUTPUT_CHARS // 3
                if len(output.content) > max_len:
                    trimmed = self._trim_content(output.content, max_len)
                    filtered.append(
                        ToolOutput(
                            tool_name=output.tool_name,
                            content=trimmed,
                            token_estimate=self._estimate_tokens(trimmed),
                            turn_index=output.turn_index,
                            is_key_file=output.is_key_file,
                        )
                    )
                    outputs_trimmed += 1
                else:
                    filtered.append(output)
            else:
                outputs_removed += 1

        self._outputs = filtered
        compressed_tokens = sum(o.token_estimate for o in self._outputs)
        savings_pct = ((original_tokens - compressed_tokens) / original_tokens * 100) if original_tokens > 0 else 0.0

        logger.warning(
            "紧急压缩完成: 移除=%d, 裁剪=%d, 关键文件=%d, 节省=%.1f%%",
            outputs_removed,
            outputs_trimmed,
            key_files_preserved,
            savings_pct,
        )

        return CompressionResult(
            tier=CompressionTier.EMERGENCY,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            savings_pct=round(savings_pct, 2),
            outputs_removed=outputs_removed,
            outputs_trimmed=outputs_trimmed,
            key_files_preserved=key_files_preserved,
        )

    def _should_preserve(self, output: ToolOutput) -> bool:
        """判断输出是否应该保留（不移除）

        保留条件：
        - 标记为关键文件（is_key_file=True）
        - 包含错误信息（error、exception、traceback）
        - 包含决策记录（decision、决定）

        Args:
            output: 工具输出

        Returns:
            bool: 是否保留
        """
        if output.is_key_file:
            return True

        content_lower = output.content.lower()
        error_patterns = ["error", "exception", "traceback", "fail"]
        decision_patterns = ["decision", "决定", "决策"]

        for pattern in error_patterns:
            if pattern in content_lower:
                return True

        for pattern in decision_patterns:
            if pattern in content_lower:
                return True

        return False

    def _trim_content(self, content: str, max_len: int) -> str:
        """裁剪内容，保留前75%和错误相关段落

        Args:
            content: 原始内容
            max_len: 最大长度

        Returns:
            str: 裁剪后的内容
        """
        if len(content) <= max_len:
            return content

        head_len = int(max_len * 0.75)
        head = content[:head_len]

        error_section = ""
        error_pattern = re.compile(
            r"(error|exception|traceback|错误|异常)",
            re.IGNORECASE,
        )
        lines = content.split("\n")
        error_lines: List[str] = []
        found_error = False

        for line in lines:
            if error_pattern.search(line):
                found_error = True
            if found_error:
                error_lines.append(line)

        if error_lines:
            remaining = max_len - head_len
            error_text = "\n".join(error_lines)
            error_section = "\n\n--- 错误相关内容 ---\n" + error_text[:remaining]

        truncation_notice = f"\n\n[... 内容已裁剪，原始长度 {len(content)} 字符，保留 {max_len} 字符 ...]"

        return head + error_section + truncation_notice

    def _generate_llm_prompt(self, pct: float) -> str:
        """生成LLM深度压缩的提示词

        Args:
            pct: 上下文使用百分比

        Returns:
            str: 提示词
        """
        return (
            f"上下文使用率已达 {pct:.0f}%，需要深度压缩。\n"
            "请执行以下操作：\n"
            "1. 保留所有关键文件（AGENTS.md、DESIGN.md、TASKS.md、MEMORY.md）的完整内容\n"
            "2. 对其他工具输出生成简洁摘要，保留关键信息和操作结果\n"
            "3. 移除已不再需要的中间过程输出\n"
            "4. 保持推理链条的完整性\n"
            "5. 用自然语言摘要替代冗长的文件内容\n"
        )

    def _estimate_tokens(self, text: str) -> int:
        """估算文本的token数量

        中文字符约占2个token，其他字符约占4个字符1个token

        Args:
            text: 输入文本

        Returns:
            int: 估算的token数量
        """
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        other_chars = len(text) - chinese_chars
        return chinese_chars // 2 + other_chars // 4

    def get_stats(self) -> Dict:
        """获取压缩器统计信息"""
        total_tokens = sum(o.token_estimate for o in self._outputs)
        key_file_count = sum(1 for o in self._outputs if o.is_key_file)
        tool_counts: Dict[str, int] = {}
        for o in self._outputs:
            tool_counts[o.tool_name] = tool_counts.get(o.tool_name, 0) + 1

        return {
            "total_outputs": len(self._outputs),
            "total_tokens": total_tokens,
            "key_file_count": key_file_count,
            "current_turn": self._current_turn,
            "tool_counts": tool_counts,
        }

    def reset(self):
        """重置压缩器状态"""
        self._outputs.clear()
        self._current_turn = 0
        logger.debug("压缩器已重置")
