"""
Models - AuditGuard 数据模型

包含:
- AuditLog: 审计日志实体（反 DarkCode 核心）
- AuditIssue: 问责记录实体
- AuditLesson: 学习经验实体
- QualityResult: 单项质量检查结果
- GateReport: 质量门禁报告
- 枚举: ChangeType, IssueSeverity, IssueType, IssueStatus, LessonType
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


# ==================== 枚举定义 ====================


class ChangeType(Enum):
    """文件变更类型"""

    CREATE = "CREATE"
    MODIFY = "MODIFY"
    DELETE = "DELETE"


class IssueSeverity(Enum):
    """问题严重级别"""

    P0 = "P0"  # 阻断性（测试失败、类型错误）
    P1 = "P1"  # 重要（lint 错误、import 未使用）
    P2 = "P2"  # 一般（覆盖率不足、风格问题）


class IssueType(Enum):
    """问题类型"""

    LINT = "lint"
    TYPE = "type"
    TEST = "test"
    COVERAGE = "coverage"
    E2E = "e2e"
    INTEGRATION = "integration"
    REGRESSION = "regression"
    PERF = "perf"


class IssueStatus(Enum):
    """问题状态"""

    OPEN = "OPEN"
    FIXING = "FIXING"
    RESOLVED = "RESOLVED"
    WONTFIX = "WONTFIX"


class LessonType(Enum):
    """学习经验类型"""

    PITFALL = "pitfall"
    PATTERN = "pattern"
    BEST_PRACTICE = "best_practice"


class QualityStatus(Enum):
    """质量检查状态"""

    PENDING = "PENDING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


# ==================== 实体类定义 ====================


@dataclass
class AuditLog:
    """
    审计日志实体

    记录每次文件变更的详细信息，反 DarkCode 核心。

    Attributes:
        id: 唯一标识
        session_id: 会话 ID
        task_id: 关联任务 ID
        file_path: 变更文件路径
        change_type: 变更类型 (CREATE/MODIFY/DELETE)
        diff_content: unified diff 内容
        lines_added: 新增行数
        lines_removed: 删除行数
        tool_name: 触发工具名 (write/edit)
        quality_status: 质量状态
        summary: 轻量变更摘要（write/edit 时记录）
        created_at: 创建时间戳
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    session_id: str = ""
    task_id: Optional[str] = None
    file_path: str = ""
    change_type: ChangeType = ChangeType.MODIFY
    diff_content: Optional[str] = None
    lines_added: int = 0
    lines_removed: int = 0
    tool_name: Optional[str] = None
    quality_status: QualityStatus = QualityStatus.PENDING
    summary: Optional[str] = None
    created_at: float = field(default_factory=time.time)


@dataclass
class AuditIssue:
    """
    问责记录实体

    记录质量门禁发现的问题，追踪完整生命周期。

    Attributes:
        id: 唯一标识
        session_id: 会话 ID
        task_id: 关联任务 ID
        issue_type: 问题类型
        severity: 严重级别
        file_path: 问题所在文件
        line_number: 问题所在行号
        check_name: 检查器名称 (ruff/mypy/pytest/coverage)
        error_code: 错误码
        error_message: 完整错误消息
        root_cause: 归因分析
        status: 问题状态
        created_at: 创建时间戳
        resolved_at: 解决时间戳
        fix_strategy: 修复策略
        fix_commit: 修复提交 hash
        occurrence_count: 出现次数（修复循环检测）
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    session_id: str = ""
    task_id: Optional[str] = None
    issue_type: IssueType = IssueType.LINT
    severity: IssueSeverity = IssueSeverity.P2
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    check_name: Optional[str] = None
    error_code: Optional[str] = None
    error_message: str = ""
    root_cause: Optional[str] = None
    status: IssueStatus = IssueStatus.OPEN
    created_at: float = field(default_factory=time.time)
    resolved_at: Optional[float] = None
    fix_strategy: Optional[str] = None
    fix_commit: Optional[str] = None
    occurrence_count: int = 1


@dataclass
class AuditLesson:
    """
    学习经验实体

    从问题修复中提取的可复用经验。

    Attributes:
        id: 唯一标识
        issue_id: 关联的问题 ID
        lesson_type: 经验类型
        category: 分类
        title: 标题
        description: 详细描述
        trigger_pattern: 触发模式（错误码/签名，用于未来自动匹配）
        prevention_tip: 预防建议
        created_at: 创建时间戳
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    issue_id: Optional[str] = None
    lesson_type: LessonType = LessonType.PITFALL
    category: Optional[str] = None
    title: str = ""
    description: str = ""
    trigger_pattern: Optional[str] = None
    prevention_tip: Optional[str] = None
    created_at: float = field(default_factory=time.time)


# ==================== 质量门禁模型 ====================


@dataclass
class QualityResult:
    """
    单项质量检查结果

    Attributes:
        check_name: 检查器名称 (ruff/mypy/pytest/coverage)
        passed: 是否通过
        output: 原始输出
        duration_ms: 执行耗时
        file_paths: 涉及的文件列表
        error_count: 错误数量
        skipped: 是否跳过
    """

    check_name: str = ""
    passed: bool = True
    output: str = ""
    duration_ms: float = 0.0
    file_paths: List[str] = field(default_factory=list)
    error_count: int = 0
    skipped: bool = False


@dataclass
class GateReport:
    """
    质量门禁报告

    Attributes:
        all_passed: 是否全部通过
        checks: 各项检查结果
        timestamp: 报告时间戳
        duration_ms: 总耗时
        report_type: 报告类型 (atomic/full)
    """

    all_passed: bool = True
    checks: List[QualityResult] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    duration_ms: float = 0.0
    report_type: str = "atomic"  # atomic | full

    @property
    def failed_checks(self) -> List[QualityResult]:
        """获取失败的检查"""
        return [c for c in self.checks if not c.passed and not c.skipped]

    @property
    def total_errors(self) -> int:
        """总错误数"""
        return sum(c.error_count for c in self.checks if not c.skipped)
