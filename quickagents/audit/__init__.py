"""
AuditGuard - 审计问责与品控测试模块

核心功能:
- CodeAuditTracker: 实时文件变更追踪与 diff 记录
- QualityGate: 分层质量门禁（原子级/全量级）
- AccountabilityEngine: 问题归因、修复闭环、经验提取
- AuditConfig: 配置管理
- AuditReporter: Markdown/JSON 报告生成

版本: 0.1.0 (v2.9.0-preview)
创建时间: 2026-04-05
"""

from .models import (
    AuditLog,
    AuditIssue,
    AuditLesson,
    QualityResult,
    GateReport,
    ChangeType,
    IssueSeverity,
    IssueType,
    IssueStatus,
    LessonType,
    QualityStatus,
)
from .audit_config import AuditConfig
from .code_audit import CodeAuditTracker
from .audit_reporter import AuditReporter
from .quality_gate import QualityGate, CheckStatus
from .accountability import AccountabilityEngine

__all__ = [
    # 数据模型
    "AuditLog",
    "AuditIssue",
    "AuditLesson",
    "QualityResult",
    "GateReport",
    "ChangeType",
    "IssueSeverity",
    "IssueType",
    "IssueStatus",
    "LessonType",
    "QualityStatus",
    # 核心组件
    "AuditConfig",
    "CodeAuditTracker",
    "AuditReporter",
    "QualityGate",
    "CheckStatus",
    "AccountabilityEngine",
]
