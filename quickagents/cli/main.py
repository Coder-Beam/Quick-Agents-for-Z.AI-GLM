"""
QuickAgents CLI - 命令行工具

命令:
    qka read <file>           # 智能读取文件（哈希检测）
    qka write <file> <content> # 写入文件
    qka edit <file> <old> <new> # 编辑文件
    qka hash <file>           # 获取文件哈希
    qka cache stats           # 查看缓存统计
    qka cache clear           # 清空缓存
    qka memory get <key>      # 获取记忆
    qka memory set <key> <val> # 设置记忆
    qka memory search <keyword> # 搜索记忆
    qka loop check            # 检查循环模式
    qka loop reset            # 重置循环检测
    qka stats                 # 查看整体统计
    qka sync [table]          # 同步SQLite到Markdown

    # 版本与升级命令
    qka version               # 查看当前版本
    qka version --check       # 检查所有模块完整性
    qka update                # 从PyPI升级到最新版
    qka update --target 2.7.6 # 升级到指定版本
    qka update --source github # 从GitHub源码安装
    qka update --dry-run      # 仅预览升级，不执行
    qka uninstall             # 卸载当前项目的QuickAgents文件（项目级）
    qka uninstall --dry-run   # 预览卸载内容
    qka uninstall --keep-data # 卸载但保留项目数据
    qka uninstall --force     # 跳过确认直接卸载

    # 导出命令
    qka export                # 导出到 Output/<版本号>/（自动检测版本+git commit）
    qka export --version 1.0  # 指定版本号
    qka export --dry-run      # 预览导出内容
    qka export --inject-gitignore  # 将QA排除规则注入 .gitignore
    qka export --list-excludes     # 列出所有排除规则

    # 模型配置命令
    qka models status         # 查看当前模型配置
    qka models check          # 检查GLM版本更新
    qka models upgrade [version] # 升级GLM模型
    qka models rollback       # 回滚到上一版本

    # 自我进化系统命令
    qka evolution status      # 进化系统状态
    qka evolution stats [skill] # Skills使用统计
    qka evolution optimize    # 执行定期优化
    qka evolution history <skill> # 查看Skill进化历史
    qka evolution sync        # 同步到Markdown

    # Git钩子命令
    qka hooks install         # 安装Git钩子
    qka hooks uninstall       # 卸载Git钩子
    qka hooks status          # 钩子状态

    # 审计问责命令（v2.9.0+）
    qka audit status          # 审计系统状态
    qka audit run --type atomic|full  # 手动触发质量检查
    qka audit log [--session ID] [--file PATH]  # 查看审计日志
    qka audit issues [--status OPEN|RESOLVED]  # 查看问责记录
    qka audit lessons [--category CAT]  # 查看学习经验
    qka audit report [--format md|json]  # 生成审计报告
    qka audit init            # 初始化审计配置文件

    # Skills本地化命令
    qka feedback bug <desc>   # 记录Bug
    qka feedback improve <desc> # 记录改进建议
    qka feedback best <desc>  # 记录最佳实践
    qka feedback view [type]  # 查看收集的经验

    qka tdd red [test_file]   # RED阶段：运行测试（应失败）
    qka tdd green [test_file] # GREEN阶段：运行测试（应通过）
    qka tdd refactor [test_file] # REFACTOR阶段
    qka tdd stats             # TDD统计
    qka tdd coverage          # 检查覆盖率

    qka git status            # Git状态
    qka git check             # Pre-commit检查
    qka git commit <type> <scope> <subject> # 执行提交
    qka git push              # 推送到远程

    # 文档导入命令
    qka import PALs/           # 导入PALs目录下的文档
    qka import PALs/ --with-source  # 同时导入源码
    qka import PALs/ --dry-run # 预览导入
"""

import sys
import os
import argparse
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

from ..core.file_manager import FileManager
from ..core.memory import MemoryManager
from ..core.reminder import Reminder
from ..core.cache_db import CacheDB
from ..core.unified_db import UnifiedDB
from ..core.markdown_sync import MarkdownSync
from ..core.evolution import SkillEvolution
from ..core.git_hooks import GitHooks
from ..skills.feedback_collector import FeedbackCollector
from ..skills.tdd_workflow import TDDWorkflow
from ..skills.git_commit import GitCommit
from ..utils.encoding import read_file_utf8, write_file_utf8
from .init_cmd import cmd_init


def cmd_read(args):
    """读取文件命令"""
    fm = FileManager()
    content, changed = fm.read_if_changed(args.file)

    print(f"文件: {args.file}")
    print(f"状态: {'已变化/新读取' if changed else '使用缓存（节省Token）'}")
    print("-" * 50)
    print(content)


def cmd_write(args):
    """写入文件命令"""
    fm = FileManager()
    fm.write(args.file, args.content)
    print(f"[OK] 已写入: {args.file}")


def cmd_edit(args):
    """编辑文件命令"""
    fm = FileManager()
    result = fm.edit(args.file, args.old, args.new)

    if result["success"]:
        print(f"[OK] 编辑成功: {args.file}")
        if result["token_saved"] > 0:
            print(f"[Token] 节省: ~{result['token_saved']}")
    else:
        print(f"[FAIL] 编辑失败: {result['message']}")


def cmd_hash(args):
    """获取文件哈希"""
    fm = FileManager()
    hash_val = fm.get_file_hash(args.file)
    print(f"文件: {args.file}")
    print(f"哈希: {hash_val}")


def cmd_cache(args):
    """缓存管理命令"""
    db = CacheDB()

    if args.action == "stats":
        stats = db.get_stats()["file_cache"]
        print("[Cache] 缓存统计")
        print(f"  缓存文件数: {stats['count']}")
        print(f"  总大小: {stats['total_kb']} KB")

    elif args.action == "clear":
        count = db.clear_file_cache()
        print(f"[OK] 已清空 {count} 个文件缓存")

    elif args.action == "list":
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT path, content_hash, size, access_count FROM file_cache")
            rows = cursor.fetchall()

            print("[Cache] 缓存文件列表")
            print("-" * 80)
            for row in rows:
                print(f"  {row['path']}")
                print(f"    哈希: {row['content_hash']}, 大小: {row['size']}B, 访问: {row['access_count']}次")


def cmd_memory(args):
    """记忆管理命令"""
    memory = MemoryManager()

    if args.action == "get":
        if not args.key:
            print("[FAIL] 请提供键名")
            return
        value = memory.get(args.key)
        if value is not None:
            print(f"{args.key}: {value}")
        else:
            print(f"[FAIL] 未找到: {args.key}")

    elif args.action == "set":
        memory.set_factual(args.key, args.value)
        memory.save()
        print(f"[OK] 已设置: {args.key} = {args.value}")

    elif args.action == "search":
        keyword = args.keyword or args.key  # 支持位置参数或选项
        if not keyword:
            print("[FAIL] 请提供搜索关键词")
            return
        results = memory.search(keyword)
        print(f"[Search] 搜索结果 ({len(results)} 条)")
        print("-" * 50)
        for r in results:
            print(f"  [{r['type']}] {r.get('key', r.get('category', ''))}: {r.get('value', r.get('content', ''))}")


def cmd_loop(args):
    """循环检测命令"""
    from ..core.loop_detector import get_loop_detector

    detector = get_loop_detector()

    if args.action == "check":
        # V3: 使用 analyze_patterns() 获取模式分析
        patterns = detector.analyze_patterns()
        if patterns.get("failure_distribution"):
            print("[WARN] 检测到失败模式")
            print("-" * 50)
            for tool, count in patterns["failure_distribution"].items():
                print(f"  {tool}: {count}次失败")
        else:
            print("[OK] 未检测到失败模式")

        # 显示状态
        status = detector.get_status()
        print(f"\n[状态] {status['state']}")
        print(f"  总调用: {status['total_calls']}")
        print(f"  连续失败: {status['consecutive_failures']}")

    elif args.action == "reset":
        detector.reset()
        print("[OK] 已重置循环检测")

    elif args.action == "stats":
        # V3: 使用 get_status() 获取统计信息
        stats = detector.get_status()
        print("[Loop] 循环检测统计 (V3)")
        print("=" * 50)
        print(f"  当前状态: {stats['state']}")
        print(f"  总调用数: {stats['total_calls']}")
        print(f"  连续失败: {stats['consecutive_failures']}")
        print(f"  失败记录: {stats['failure_count']}")
        print("\n[阈值配置]")
        print(f"  相同失败阈值: {stats['thresholds']['same_failure']}")
        print(f"  连续失败阈值: {stats['thresholds']['consecutive_failure']}")
        print(f"  策略: {stats['config']['strategy']}")
        print(f"  最大调用: {stats['config']['max_tool_calls']}")
        print(f"  最大时间: {stats['config']['max_time_seconds']}s")


def cmd_stats(args):
    """查看整体统计"""
    db = CacheDB()
    stats = db.get_stats()

    print("[Stats] QuickAgents 统计")
    print("=" * 50)

    print("\n[File] 文件缓存")
    print(f"  缓存文件: {stats['file_cache']['count']}")
    print(f"  总大小: {stats['file_cache']['total_kb']} KB")

    print("\n[Memory] 记忆系统")
    print(f"  记忆条目: {stats['memory']['count']}")

    print("\n[Token] 节省")
    print(f"  估算节省: {stats['tokens']['total_saved']} tokens")


def cmd_sync(args):
    """同步SQLite到Markdown"""
    from ..utils.sync_conflict import get_sync_conflict_detector

    db_path = ".quickagents/unified.db"

    if not os.path.exists(db_path):
        print(f"[FAIL] 数据库不存在: {db_path}")
        print("  请先使用UnifiedDB创建数据库")
        return

    db = UnifiedDB(db_path)
    sync = MarkdownSync(db)

    # 检查冲突（除非强制同步）
    force = hasattr(args, "force") and args.force
    table = args.table if hasattr(args, "table") and args.table else None

    if not force:
        detector = get_sync_conflict_detector()

        # 确定要检查的文件
        file_keys = None
        if table:
            file_keys = [table]

        conflicts = detector.check_conflicts(file_keys)

        if conflicts:
            print("[WARN] 检测到同步冲突！")
            print("-" * 50)
            print(detector.get_conflict_report(file_keys))
            print("\n使用 --force 强制同步，忽略冲突")
            return

    # 执行同步
    if table == "memory" or table is None:
        result = sync.sync_memory()
        if result:
            print("[OK] 已同步 memory -> Docs/MEMORY.md")

    if table == "tasks" or table is None:
        result = sync.sync_tasks()
        if result:
            print("[OK] 已同步 tasks -> Docs/TASKS.md")

    if table == "decisions" or table is None:
        result = sync.sync_decisions()
        if result:
            print("[OK] 已同步 decisions -> Docs/DECISIONS.md")

    if table == "progress" or table is None:
        result = sync.sync_progress()
        if result:
            print("[OK] 已同步 progress -> .quickagents/boulder.json")

    if table == "feedback" or table is None:
        result = sync.sync_feedback()
        if result:
            print("[OK] 已同步 feedback -> ~/.quickagents/feedback/")

    if table is None:
        print("\n[Done] 所有表同步完成")


def cmd_reminder(args):
    """提醒系统命令"""
    reminder = Reminder()

    if args.action == "check":
        alerts = reminder.check_alerts()
        if alerts:
            print("[WARN] 活跃提醒")
            print("-" * 50)
            for a in alerts:
                print(f"  [{a['level']}] {a['message']}")
        else:
            print("[OK] 无活跃提醒")

    elif args.action == "stats":
        stats = reminder.get_stats()
        print("[Reminder] 提醒系统统计")
        print(f"  工具调用: {stats['tool_calls']}")
        print(f"  错误次数: {stats['errors']}")
        print(f"  运行时间: {int(stats['elapsed_minutes'])} 分钟")
        print(f"  上下文使用: {stats['context_usage']}%")


# ==================== Skills本地化命令 ====================


def cmd_feedback(args):
    """经验收集命令"""
    collector = FeedbackCollector()

    if args.action == "bug":
        success = collector.record("bug", args.description, scenario=args.scenario)
        if success:
            print(f"[OK] 已记录Bug: {args.description}")
        else:
            print("[INFO] 重复记录已忽略")

    elif args.action == "improve":
        success = collector.record("improvement", args.description, scenario=args.scenario)
        if success:
            print(f"[OK] 已记录改进建议: {args.description}")
        else:
            print("[INFO] 重复记录已忽略")

    elif args.action == "best":
        success = collector.record("best_practice", args.description, scenario=args.scenario)
        if success:
            print(f"[OK] 已记录最佳实践: {args.description}")
        else:
            print("[INFO] 重复记录已忽略")

    elif args.action == "view":
        feedback_type = args.type if hasattr(args, "type") and args.type else None
        feedbacks = collector.get_feedback(feedback_type, limit=20)

        print(f"[Feedback] 经验收集 ({len(feedbacks)} 条)")
        print("-" * 50)
        for fb in feedbacks:
            print(f"  [{fb['type']}] {fb['timestamp']}")
            print(f"    {fb['description'][:50]}...")

    elif args.action == "stats":
        stats = collector.get_stats()
        print("[Feedback] 经验收集统计")
        print(f"  总计: {stats['total']} 条")
        for ftype, count in stats["by_type"].items():
            print(f"  {ftype}: {count} 条")


def cmd_tdd(args):
    """TDD工作流命令"""
    tdd = TDDWorkflow()

    if args.action == "red":
        result = tdd.run_red(args.test_file)
        # 检查文件不存在等错误
        if result.get("error") == "file_not_found":
            print(f"[RED] 错误: 测试文件不存在: {result.get('test_file', args.test_file)}")
            print("  请确认文件路径是否正确")
            return
        print(f"[RED] RED阶段: {'测试失败 [OK]' if not result['passed'] else '测试通过 [WARN]'}")
        print(f"  耗时: {result['duration_ms']}ms")
        if result["passed"]:
            print("  [WARN] 测试已通过，需要先写失败的测试！")

    elif args.action == "green":
        result = tdd.run_green(args.test_file)
        # 检查文件不存在等错误
        if result.get("error") == "file_not_found":
            print(f"[GREEN] 错误: 测试文件不存在: {result.get('test_file', args.test_file)}")
            print("  请确认文件路径是否正确")
            return
        print(f"[GREEN] GREEN阶段: {'测试通过 [OK]' if result['passed'] else '测试失败 [FAIL]'}")
        print(f"  耗时: {result['duration_ms']}ms")
        if result["passed"]:
            print("  [OK] 可以进入Refactor阶段")

    elif args.action == "refactor":
        result = tdd.run_refactor(args.test_file)
        # 检查文件不存在等错误
        if result.get("error") == "file_not_found":
            print(f"[REFACTOR] 错误: 测试文件不存在: {result.get('test_file', args.test_file)}")
            print("  请确认文件路径是否正确")
            return
        print(f"[REFACTOR] REFACTOR阶段: {'测试通过 [OK]' if result['passed'] else '测试失败 [FAIL]'}")
        print(f"  耗时: {result['duration_ms']}ms")

    elif args.action == "stats":
        stats = tdd.get_stats()
        print("[TDD] TDD统计")
        print(f"  RED次数: {stats['red_count']}")
        print(f"  GREEN次数: {stats['green_count']}")
        print(f"  REFACTOR次数: {stats['refactor_count']}")
        print(f"  测试命令: {stats['test_command']}")

    elif args.action == "coverage":
        result = tdd.check_coverage(threshold=80)
        print(f"[Coverage] 测试覆盖率: {result['coverage']}%")
        print(f"  达标: {'[OK]' if result['meets_threshold'] else '[FAIL]'}")


def cmd_git(args):
    """Git提交命令"""
    git = GitCommit()

    if args.action == "status":
        status = git.get_status()
        print(f"[Git] 分支: {status['branch']}")
        print(f"  领先: {status['ahead']}, 落后: {status['behind']}")

        if status["staged"]:
            print(f"\n[Staged] 已暂存 ({len(status['staged'])})")
            for f in status["staged"][:5]:
                print(f"  {f}")

        if status["unstaged"]:
            print(f"\n[Unstaged] 未暂存 ({len(status['unstaged'])})")
            for f in status["unstaged"][:5]:
                print(f"  {f}")

        if status["untracked"]:
            print(f"\n[Untracked] 未跟踪 ({len(status['untracked'])})")
            for f in status["untracked"][:5]:
                print(f"  {f}")

    elif args.action == "check":
        print("[Git] 执行Pre-commit检查...")
        checks = git.run_pre_commit_checks()

        print(f"\n{'[OK]' if checks['all_passed'] else '[FAIL]'} 检查结果")
        for check_name, result in checks["checks"].items():
            status = "[OK]" if result["passed"] else ("[SKIP]" if result.get("skipped") else "[FAIL]")
            print(f"  {status} {check_name}")

    elif args.action == "commit":
        commit_type = getattr(args, "commit_type", None) or "chore"
        scope = getattr(args, "scope", None) or ""
        subject = getattr(args, "subject", None) or ""
        if not subject:
            print("[FAIL] 请提供提交信息")
            print("  用法: qka git commit <type> <scope> <subject>")
            print('  示例: qka git commit feat auth "添加JWT认证"')
            return
        print("[Git] 执行Pre-commit检查...")
        result = git.commit(commit_type, scope, subject, run_checks=True)

        if result["success"]:
            print(f"[OK] 提交成功: {result['commit_hash']}")
            print(f"   {result['message'].split(chr(10))[0]}")
        else:
            print(f"[FAIL] 提交失败: {result['message']}")

    elif args.action == "push":
        result = git.push()
        if result["success"]:
            print("[OK] 推送成功")
        else:
            print(f"[FAIL] 推送失败: {result['message']}")


# ==================== 自我进化系统命令 ====================


def cmd_evolution(args):
    """自我进化系统命令"""
    db_path = ".quickagents/unified.db"

    if not os.path.exists(db_path):
        print(f"[FAIL] 数据库不存在: {db_path}")
        print("  请先使用UnifiedDB创建数据库")
        return

    db = UnifiedDB(db_path)
    evolution = SkillEvolution(db)

    if args.action == "status":
        print("[Evolution] 自我进化系统状态")
        print("=" * 50)

        # 检查定期优化
        should_optimize = evolution.check_periodic_trigger()
        print(f"  需要优化: {'是' if should_optimize else '否'}")

        # 获取所有Skills统计
        stats = evolution.get_all_skills_stats()
        print(f"  已跟踪Skills: {len(stats)}")

        # 获取任务计数
        task_count = evolution._get_task_count()
        print(f"  任务计数: {task_count}/{evolution.PERIODIC_TASK_THRESHOLD}")

        # 获取上次优化时间
        last_opt = evolution._get_last_optimization_time()
        if last_opt:
            print(f"  上次优化: {last_opt.strftime('%Y-%m-%d %H:%M')}")
        else:
            print("  上次优化: 从未执行")

    elif args.action == "stats":
        skill_name = args.skill if hasattr(args, "skill") and args.skill else None

        if skill_name:
            # 单个Skill统计
            stats = evolution.get_skill_stats(skill_name)
            print(f"[Evolution] {skill_name} 统计")
            print("=" * 50)
            print(f"  总使用次数: {stats['total_usage']}")
            print(f"  成功次数: {stats['success_count']}")
            print(f"  失败次数: {stats['failure_count']}")
            print(f"  成功率: {stats['success_rate']:.1%}")
            if stats["avg_duration_ms"]:
                print(f"  平均耗时: {stats['avg_duration_ms']:.0f}ms")

            if stats["recent_errors"]:
                print("\n[Recent Errors]")
                for err in stats["recent_errors"][:3]:
                    print(f"  - {err['error_message'][:50]}...")
        else:
            # 所有Skills统计
            all_stats = evolution.get_all_skills_stats()
            print(f"[Evolution] 所有Skills统计 ({len(all_stats)} 个)")
            print("=" * 50)

            for skill, stats in sorted(all_stats.items(), key=lambda x: x[1]["count"], reverse=True):
                rate = stats["success_rate"]
                status = "[OK]" if rate >= 0.8 else ("[WARN]" if rate >= 0.6 else "[FAIL]")
                print(f"  {status} {skill}: {stats['count']}次, 成功率 {rate:.0%}")

    elif args.action == "optimize":
        print("[Evolution] 执行定期优化...")
        result = evolution.run_periodic_optimization()

        print("\n[OK] 优化完成")
        print(f"  审查Skills: {len(result['skills_reviewed'])}")

        if result["skills_to_update"]:
            print("\n[WARN] 需要改进的Skills:")
            for skill in result["skills_to_update"]:
                print(f"  - {skill}")

    elif args.action == "history":
        skill_name = args.skill
        if not skill_name:
            print("[FAIL] 请指定Skill名称")
            return

        history = evolution.get_skill_history(skill_name)
        print(f"[Evolution] {skill_name} 进化历史 ({len(history)} 条)")
        print("=" * 50)

        for entry in history[:10]:
            print(f"\n  [{entry['created_at'][:10]}] {entry['change_type']}")
            print(f"    触发: {entry['trigger_type']}")
            print(f"    描述: {entry['description']}")

    elif args.action == "sync":
        print("[Evolution] 同步到Markdown...")
        result = evolution.sync_to_markdown()

        print(f"[OK] 已同步 {result['skills_synced']} 个Skills")
        for f in result["files_created"][:5]:
            print(f"  - {f}")


def cmd_hooks(args):
    """Git钩子命令"""
    hooks = GitHooks()

    if args.action == "install":
        print("[Hooks] 安装Git钩子...")
        result = hooks.install()

        if "error" in result:
            print(f"[FAIL] {result['error']}")
        else:
            print("[OK] Git钩子已安装")
            for hook, success in result.items():
                print(f"  - {hook}: {'成功' if success else '失败'}")

    elif args.action == "uninstall":
        print("[Hooks] 卸载Git钩子...")
        result = hooks.uninstall()

        print("[OK] Git钩子已卸载")
        for hook, success in result.items():
            print(f"  - {hook}: {'成功' if success else '失败'}")

    elif args.action == "status":
        status = hooks.get_status()
        print("[Hooks] Git钩子状态")
        print("=" * 50)
        print(f"  是Git仓库: {'是' if status['is_git_repo'] else '否'}")
        print(f"  post-commit: {'已安装' if status['post_commit_installed'] else '未安装'}")
        if status["post_commit_has_backup"]:
            print("  存在备份: 是")


# ==================== 审计问责命令 ====================


def cmd_audit(args):
    """审计问责命令"""
    from ..audit import AuditGuard

    db_path = ".quickagents/unified.db"

    if not os.path.exists(db_path):
        print(f"[FAIL] 数据库不存在: {db_path}")
        print("  请先使用UnifiedDB创建数据库")
        return

    guard = AuditGuard(db_path=db_path)

    try:
        if args.action == "status":
            print("[Audit] 审计系统状态")
            print("=" * 50)

            summary = guard.get_audit_summary()

            print("\n[CodeAudit] 变更追踪")
            tracker = summary["tracker"]
            print(f"  总变更数: {tracker['total_changes']}")
            print(f"  今日变更: {tracker['today_changes']}")

            print("\n[Accountability] 问责统计")
            acc = summary["accountability"]
            print(f"  总问题数: {acc['total_issues']}")
            print(f"  学习经验: {acc['total_lessons']}")
            if acc["by_status"]:
                print("  按状态:")
                for status, count in acc["by_status"].items():
                    print(f"    {status}: {count}")

            print("\n[Config] 配置")
            cfg = summary["config"]
            print(f"  变更追踪: {'启用' if cfg['code_audit_enabled'] else '禁用'}")
            print(f"  质量门禁: {'启用' if cfg['quality_gate_enabled'] else '禁用'}")
            print(f"  经验提取: {'启用' if cfg['lesson_extraction'] else '禁用'}")

        elif args.action == "run":
            check_type = args.type if hasattr(args, "type") and args.type else "atomic"

            if check_type == "atomic":
                print("[Audit] 执行原子级检查...")
                report = guard.on_git_commit(session_id="cli")

                if report.passed:
                    print("[OK] 所有检查通过")
                else:
                    print(f"[FAIL] 检查失败: {len(report.failed_checks)} 项")
                    for check in report.failed_checks:
                        print(f"  - {check.check_name}: {check.error_count} errors")

            elif check_type == "full":
                print("[Audit] 执行全量级检查...")
                report = guard.on_task_complete(task_id="cli-manual")

                if report.passed:
                    print("[OK] 所有检查通过")
                else:
                    print(f"[FAIL] 检查失败: {len(report.failed_checks)} 项")
                    for check in report.failed_checks:
                        print(f"  - {check.check_name}: {check.error_count} errors")

            else:
                print(f"[FAIL] 不支持的检查类型: {check_type}")

        elif args.action == "log":
            session_id = args.session if hasattr(args, "session") and args.session else None
            file_path = args.file if hasattr(args, "file") and args.file else None

            print("[Audit] 审计日志")
            print("=" * 50)

            if session_id:
                changes = guard.tracker.get_changes_by_session(session_id)
            elif file_path:
                changes = guard.tracker.get_file_history(file_path)
            else:
                changes = guard.tracker.get_changes(limit=20)

            for change in changes:
                print(f"  [{change.change_type}] {change.file_path}")
                print(f"    时间: {change.created_at}")

        elif args.action == "issues":
            status = args.status if hasattr(args, "status") and args.status else None
            severity = args.severity if hasattr(args, "severity") and args.severity else None

            print("[Audit] 问责记录")
            print("=" * 50)

            issues = guard.get_issues(status=status, severity=severity, limit=20)

            if not issues:
                print("  无匹配记录")
            else:
                for issue in issues:
                    icon = {"P0": "🔴", "P1": "🟡", "P2": "🔵"}.get(issue.severity.value, "⚪")
                    print(f"  {icon} [{issue.severity.value}] {issue.check_name}")
                    print(f"    文件: {issue.file_path or 'N/A'}")
                    print(f"    消息: {issue.error_message[:60]}...")
                    print(f"    状态: {issue.status.value}")

        elif args.action == "lessons":
            category = args.category if hasattr(args, "category") and args.category else None

            print("[Audit] 学习经验")
            print("=" * 50)

            lessons = guard.get_lessons(category=category, limit=20)

            if not lessons:
                print("  无学习经验")
            else:
                for lesson in lessons:
                    print(f"  [{lesson.lesson_type.value}] {lesson.title}")
                    print(f"    类别: {lesson.category}")
                    print(f"    建议: {lesson.prevention_tip[:50]}...")

        elif args.action == "report":
            fmt = args.format if hasattr(args, "format") and args.format else "markdown"
            session_id = args.session if hasattr(args, "session") and args.session else ""

            print("[Audit] 生成审计报告...")

            report = guard.generate_report(session_id=session_id, fmt=fmt)

            if fmt == "json":
                print(report)
            else:
                # Markdown 格式
                print(report)

        elif args.action == "init":
            import json

            config_path = "audit_config.json"
            default_config = {
                "version": "1.0.0",
                "code_audit": {
                    "enabled": True,
                    "ignore_patterns": [
                        "**/.git/**",
                        "**/__pycache__/**",
                        "**/node_modules/**",
                        "**/.quickagents/**",
                    ],
                    "max_diff_lines": 500,
                },
                "quality_gate": {
                    "enabled": True,
                    "atomic_checks": {
                        "lint_command": "auto",
                        "typecheck_command": "auto",
                        "test_command": "auto",
                        "timeout_seconds": 30,
                    },
                    "full_checks": {
                        "coverage_threshold": 80,
                        "timeout_seconds": 120,
                    },
                },
                "accountability": {
                    "enabled": True,
                    "lesson_extraction": True,
                    "auto_feedback_enabled": False,
                },
            }

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)

            print(f"[OK] 已创建配置文件: {config_path}")

    finally:
        guard.close()


# ==================== 模型管理命令 ====================


def cmd_models(args):
    """模型管理命令"""
    import json
    from pathlib import Path

    models_json_path = Path(".opencode/config/models.json")

    if not models_json_path.exists():
        print(f"[FAIL] 配置文件不存在: {models_json_path}")
        return

    config = json.loads(read_file_utf8(str(models_json_path)))

    if args.action == "show" or args.action == "status":
        print("[Models] 当前模型配置")
        print("=" * 50)
        print(f"  版本: {config.get('version', 'unknown')}")
        print(f"  策略: {config.get('strategy', 'unknown')}")
        print(f"  主模型: {config.get('default', {}).get('primary', 'unknown')}")
        print(f"  备用模型: {config.get('default', {}).get('fallback', 'unknown')}")

        # 显示 Coding Plan 信息
        if "codingPlanConfig" in config:
            print("\n[Coding Plan]")
            mapping = config["codingPlanConfig"].get("claudeCodeMapping", {})
            print(f"  Claude Opus -> {mapping.get('opus', 'N/A')}")
            print(f"  Claude Sonnet -> {mapping.get('sonnet', 'N/A')}")
            print(f"  Claude Haiku -> {mapping.get('haiku', 'N/A')}")

        # 显示 Agent 映射
        if args.agent:
            agent_map = config.get("agentMapping", {})
            categories = config.get("categories", {})

            if args.agent in agent_map:
                category = agent_map[args.agent]
                model = categories.get(category, "unknown")
                print(f"\n[Agent] {args.agent}")
                print(f"  类别: {category}")
                print(f"  模型: {model}")
            else:
                print(f"\n[FAIL] Agent '{args.agent}' 未找到")

    elif args.action == "list":
        print("[Models] 可用模型列表")
        print("=" * 50)

        providers = config.get("providers", {})
        for provider_name, provider in providers.items():
            print(f"\n[{provider.get('displayName', provider_name)}]")
            models = provider.get("models", {})
            for model_id, model_info in models.items():
                recommended = " (推荐)" if model_info.get("recommended") else ""
                reasoning = " [推理]" if model_info.get("reasoning") else ""
                print(f"  - {model_id}{recommended}{reasoning}")
                if model_info.get("description"):
                    print(f"    {model_info['description']}")

    elif args.action == "check-updates":
        print("[Models] 检查 GLM 模型更新...")
        print("=" * 50)

        version_config = config.get("versionUpgrade", {})
        check_url = version_config.get("checkUrl", "https://docs.bigmodel.cn/llms.txt")
        upgrade_path = version_config.get("upgradePath", {})

        print(f"  检查地址: {check_url}")
        print(f"  自动检测: {'开启' if version_config.get('autoDetect') else '关闭'}")

        # 显示升级路径
        if upgrade_path:
            print("\n[升级路径]")
            for old_ver, new_ver in upgrade_path.items():
                print(f"  {old_ver} -> {new_ver}")

        # 尝试获取远程信息
        try:
            import urllib.request

            with urllib.request.urlopen(check_url, timeout=10) as response:
                content = response.read().decode("utf-8")
                print(f"\n[OK] 成功获取远程模型信息 ({len(content)} bytes)")
        except Exception as e:
            print(f"\n[WARN] 无法获取远程信息: {e}")
            print("  请手动访问 https://docs.bigmodel.cn/llms.txt 查看")

    elif args.action == "upgrade":
        print("[Models] 模型升级")
        print("=" * 50)

        version_config = config.get("versionUpgrade", {})
        upgrade_path = version_config.get("upgradePath", {})

        current_primary = config.get("default", {}).get("primary", "")

        if args.target:
            target = args.target
        else:
            target = upgrade_path.get(current_primary, "")

        if not target:
            print(f"[FAIL] 未找到 {current_primary} 的升级路径")
            print("  使用: qka models upgrade --to GLM-5.1")
            return

        print(f"  当前: {current_primary}")
        print(f"  目标: {target}")

        if args.dry_run:
            print("\n[DRY-RUN] 预览变更:")
            print(f"  - default.primary: {current_primary} -> {target}")

            categories = config.get("categories", {})
            for cat, model in categories.items():
                if model == current_primary:
                    print(f"  - categories.{cat}: {model} -> {target}")

            print("\n  使用 --force 执行实际升级")
        else:
            if not args.force:
                print("\n[WARN] 需要确认")
                print("  使用 --force 执行升级")
                return

            # 创建备份
            import shutil
            from datetime import datetime

            backup_path = Path(f".quickagents/backups/models_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(models_json_path, backup_path)
            print(f"\n[OK] 备份已创建: {backup_path}")

            # 执行升级
            if config["default"]["primary"] == current_primary:
                config["default"]["primary"] = target

            for cat, model in config.get("categories", {}).items():
                if model == current_primary:
                    config["categories"][cat] = target

            write_file_utf8(str(models_json_path), json.dumps(config, indent=2, ensure_ascii=False))

            print(f"[OK] 升级完成: {current_primary} -> {target}")

    elif args.action == "strategy":
        print("[Models] 切换模型策略")
        print("=" * 50)

        # 支持从位置参数或选项获取策略名称
        strategy = args.strategy_name or args.model_name
        print(f"  目标策略: {strategy}")

        if strategy not in ["coding-plan", "single-model", "hybrid"]:
            print(f"[FAIL] 无效策略: {strategy}")
            print("  可用: coding-plan, single-model, hybrid")
            return

        if args.dry_run:
            print(f"\n[DRY-RUN] 将切换到: {strategy}")
            return

        if not args.force:
            print("\n[WARN] 需要确认")
            print("  使用 --force 执行切换")
            return

        config["strategy"] = strategy

        if strategy == "single-model" and args.model:
            config["lockModel"] = args.model
            config["default"]["primary"] = args.model

        write_file_utf8(str(models_json_path), json.dumps(config, indent=2, ensure_ascii=False))

        print(f"[OK] 策略已切换: {strategy}")

    elif args.action == "lock":
        model = args.model_name
        print(f"[Models] 锁定模型: {model}")

        if args.dry_run:
            print(f"\n[DRY-RUN] 将锁定所有 Agent 使用: {model}")
            return

        if not args.force:
            print("\n[WARN] 需要确认")
            print("  使用 --force 执行锁定")
            return

        config["lockModel"] = model
        config["default"]["primary"] = model

        write_file_utf8(str(models_json_path), json.dumps(config, indent=2, ensure_ascii=False))

        print(f"[OK] 已锁定模型: {model}")

    elif args.action == "unlock":
        print("[Models] 解除模型锁定")

        config["lockModel"] = None

        write_file_utf8(str(models_json_path), json.dumps(config, indent=2, ensure_ascii=False))

        print("[OK] 已解除锁定")


def cmd_uninstall(args):
    """卸载QuickAgents命令（项目级）

    仅清理当前项目中的 QuickAgents 相关文件，不影响其他项目。
    不卸载 pip 包，不删除全局数据。

    清理范围:
        1. Git Hooks (项目级 .git/hooks/ 中的qa相关钩子)
        2. 项目数据 (项目级 .quickagents/ 目录)
        3. 项目配置 (.opencode/ 目录中的qa相关文件)

    用法:
        qka uninstall                # 交互式卸载（仅项目级）
        qka uninstall --dry-run      # 预览将被清理的内容
        qka uninstall --keep-data    # 保留 .quickagents/ 目录
        qka uninstall --keep-opencode # 保留 .opencode/ 目录
        qka uninstall --force        # 跳过确认提示
    """
    import shutil

    from .. import __version__

    dry_run = getattr(args, "dry_run", False)
    keep_data = getattr(args, "keep_data", False)
    keep_opencode = getattr(args, "keep_opencode", False)
    force = getattr(args, "force", False)

    print(f"[Uninstall] QuickAgents v{__version__} — 项目级卸载")
    print("=" * 60)
    print("  ⚠️  仅清理当前项目，不影响其他项目或 pip 包")
    print("=" * 60)

    # --- 1. 收集需要清理的内容 ---
    items_to_clean = []

    # 1a. Git Hooks (qa相关)
    git_hooks_dir = Path(".git/hooks")
    qa_hooks = []
    if git_hooks_dir.exists():
        for hook_file in git_hooks_dir.iterdir():
            if hook_file.is_file() and not hook_file.name.endswith(".sample"):
                try:
                    content = hook_file.read_text(encoding="utf-8", errors="ignore")
                    if "quickagents" in content.lower() or "qka " in content:
                        qa_hooks.append(hook_file)
                except Exception:
                    logger.debug("Failed to read git hook file: %s", hook_file)
    if qa_hooks:
        items_to_clean.append(("git_hooks", qa_hooks, f"Git Hooks (qa相关, {len(qa_hooks)}个)"))

    # 1b. 项目数据 .quickagents/
    project_data = Path(".quickagents")
    if project_data.exists():
        total_size = sum(f.stat().st_size for f in project_data.rglob("*") if f.is_file())
        items_to_clean.append(
            (
                "project_data",
                [project_data],
                f"项目数据 (.quickagents/) [{_format_size(total_size)}]",
            )
        )

    # 1c. .opencode/ 目录
    opencode_dir = Path(".opencode")
    if opencode_dir.exists():
        total_size = sum(f.stat().st_size for f in opencode_dir.rglob("*") if f.is_file())
        items_to_clean.append(
            (
                "opencode_dir",
                [opencode_dir],
                f"IDE配置 (.opencode/) [{_format_size(total_size)}]",
            )
        )

    # 1d. 项目根目录的QA配置文件
    qa_config_files = []
    for fname in ["quickagents.json", "AGENTS.md", "VERSION.md"]:
        fpath = Path(fname)
        if fpath.exists():
            qa_config_files.append(fpath)
    if qa_config_files:
        items_to_clean.append(
            (
                "config_files",
                qa_config_files,
                f"配置文件 ({', '.join(str(f) for f in qa_config_files)})",
            )
        )

    if not items_to_clean:
        print("\n[INFO] 当前项目中没有 QuickAgents 相关文件")
        return

    # --- 2. 显示清理计划 ---
    print(f"\n将要清理以下内容 (项目: {Path.cwd().name}):\n")

    action_plan = []
    for item_type, paths, description in items_to_clean:
        if item_type == "project_data" and keep_data:
            print(f"  [SKIP] {description} (--keep-data)")
            continue
        if item_type == "opencode_dir" and keep_opencode:
            print(f"  [SKIP] {description} (--keep-opencode)")
            continue
        print(f"  [REMOVE] {description}")
        action_plan.append(item_type)

    if not action_plan:
        print("\n[INFO] 所有项目已标记为保留，无需清理")
        return

    # --- 3. dry-run 模式 ---
    if dry_run:
        print("\n[DRY-RUN] 以上是预览，未执行任何操作")
        print("  移除 --dry-run 参数以执行实际卸载")
        return

    # --- 4. 确认 ---
    if not force:
        print()
        try:
            answer = input("确认卸载当前项目中的 QuickAgents 文件? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n[INFO] 已取消卸载")
            return
        if answer not in ("y", "yes"):
            print("[INFO] 已取消卸载")
            return

    # --- 5. 执行清理 ---
    print(f"\n[执行] 开始清理项目: {Path.cwd().name}...")

    # 5a. 移除 Git Hooks
    if "git_hooks" in action_plan:
        for hook_file in qa_hooks:
            try:
                hook_file.unlink()
                print(f"  [OK] 已删除: {hook_file}")
            except Exception as e:
                print(f"  [WARN] 无法删除 {hook_file}: {e}")

    # 5b. 移除项目数据
    if "project_data" in action_plan and project_data.exists():
        try:
            shutil.rmtree(str(project_data))
            print("  [OK] 已删除: .quickagents/")
        except Exception as e:
            print(f"  [WARN] 无法删除 .quickagents/: {e}")
            print("         请手动删除: rmdir /s /q .quickagents  (Windows)")
            print("                   rm -rf .quickagents          (Linux/Mac)")

    # 5c. 移除 .opencode/
    if "opencode_dir" in action_plan and opencode_dir.exists():
        try:
            shutil.rmtree(str(opencode_dir))
            print("  [OK] 已删除: .opencode/")
        except Exception as e:
            print(f"  [WARN] 无法删除 .opencode/: {e}")

    # 5d. 移除配置文件
    if "config_files" in action_plan:
        for fpath in qa_config_files:
            try:
                fpath.unlink()
                print(f"  [OK] 已删除: {fpath}")
            except Exception as e:
                print(f"  [WARN] 无法删除 {fpath}: {e}")

    print("\n" + "=" * 60)
    print("[OK] 项目级卸载完成!")
    print()
    print("  ℹ️  pip 包未被卸载，其他项目不受影响")
    print("  ℹ️  如需完全移除 QuickAgents，请手动执行:")
    print("      pip uninstall quickagents")
    print()
    print("  如需重新初始化此项目:")
    print("      启动QuickAgent")


# ==================== 导出命令 ====================

# QuickAgents 在用户项目中生成/使用的所有文件和目录
# 这些文件不应出现在用户的发布包中
QA_PROJECT_PATTERNS = {
    # 运行时数据目录
    "dirs": [
        ".quickagents",
        ".opencode",
        ".pytest_cache",
        "__pycache__",
    ],
    # 配置和文档文件（项目根目录）
    "root_files": [
        "AGENTS.md",
        "VERSION.md",
        "quickagents.json",
        "opencode.json",
    ],
    # Docs/ 下的 QA 生成文件
    "docs_files": [
        "Docs/MEMORY.md",
        "Docs/TASKS.md",
        "Docs/DECISIONS.md",
        "Docs/INDEX.md",
    ],
    # Docs/ 下的 QA 生成子目录
    "docs_dirs": [
        "Docs/features",
        "Docs/modules",
    ],
    # 通用排除（非QA但也不应发布）
    "generic_exclude": [
        "node_modules",
        ".git",
        "dist",
        "build",
        "*.egg-info",
        "*.pyc",
        "*.pyo",
        ".env",
        ".env.local",
    ],
}

# .gitignore 注入模板
QA_GITIGNORE_BLOCK = """
# === QuickAgents Runtime (DO NOT publish) ===
.quickagents/
.opencode/
.pytest_cache/
AGENTS.md
VERSION.md
quickagents.json
opencode.json
Docs/MEMORY.md
Docs/TASKS.md
Docs/DECISIONS.md
Docs/INDEX.md
Docs/features/
Docs/modules/
# === End QuickAgents ==="""

QA_GITIGNORE_MARKER_START = "# === QuickAgents Runtime (DO NOT publish) ==="
QA_GITIGNORE_MARKER_END = "# === End QuickAgents ==="


def _should_exclude(rel_path: str, project_root: Path) -> bool:
    """判断文件是否应被排除（不出现在导出包中）"""
    # 统一用正斜杠比较
    rel_path_posix = rel_path.replace("\\", "/")
    parts = rel_path_posix.split("/")

    # 加载自定义配置
    custom_config = _load_custom_export_config(project_root)

    # 合并规则
    all_dirs = QA_PROJECT_PATTERNS["dirs"] + custom_config.get("dirs", [])
    all_root_files = QA_PROJECT_PATTERNS["root_files"] + custom_config.get("root_files", [])
    all_docs_files = QA_PROJECT_PATTERNS["docs_files"] + custom_config.get("docs_files", [])
    all_docs_dirs = QA_PROJECT_PATTERNS["docs_dirs"] + custom_config.get("docs_dirs", [])
    all_generic = QA_PROJECT_PATTERNS["generic_exclude"]
    custom_patterns = custom_config.get("patterns", [])

    # 排除目录
    for d in all_dirs:
        if d in parts:
            return True

    # 排除通用目录
    for d in all_generic:
        clean = d.replace("*", "")
        if clean in parts:
            return True
        # glob 匹配 (如 *.egg-info)
        if "*" in d:
            import fnmatch

            for p in parts:
                if fnmatch.fnmatch(p, d):
                    return True

    # 文件名匹配
    filename = parts[-1] if parts else ""

    # 根目录文件（只在根目录时排除）
    if len(parts) == 1:
        for f in all_root_files:
            if filename == f:
                return True
        for f in all_generic:
            if "*" in f:
                import fnmatch

                if fnmatch.fnmatch(filename, f):
                    return True

    # Docs/ 下的 QA 文件
    if len(parts) >= 2 and parts[0] == "Docs":
        docs_rel = "/".join(parts[:2]) if len(parts) >= 2 else parts[0]
        for f in all_docs_files:
            if docs_rel == f:
                return True
        for d in all_docs_dirs:
            if rel_path_posix.startswith(d + "/"):
                return True

    # 自定义模式匹配
    if custom_patterns:
        import fnmatch

        for pattern in custom_patterns:
            # 支持 **/test_*.py 这样的模式
            if pattern.startswith("**/"):
                sub_pattern = pattern[3:]
                if fnmatch.fnmatch(filename, sub_pattern):
                    return True
            elif "*" in pattern:
                if fnmatch.fnmatch(rel_path_posix, pattern):
                    return True

    # __pycache__ 在任意层级
    if "__pycache__" in parts:
        return True

    return False


def _load_custom_export_config(project_root: Path) -> dict:
    """加载用户自定义的导出配置文件"""
    config_path = project_root / ".qkaexport"
    if not config_path.exists():
        return {}

    try:
        import json as _json

        content = config_path.read_text(encoding="utf-8")
        config = _json.loads(content)

        # 返回 exclude 部分
        if "exclude" in config:
            return config["exclude"]
        return {}
    except Exception as e:
        print(f"[WARN] 加载 .qkaexport 配置文件失败: {e}")
        return {}


def cmd_export(args):
    """导出命令 - 导出干净的项目文件（不含QuickAgents运行时文件）

    用于项目发布、打包、上传到GitHub/PyPI等场景。
    排除所有 QuickAgents 生成的运行时文件、配置文件和IDE文件。
    输出到 Output/<版本号>/ 目录，必须与 git commit 对应。

    核心约束:
        - 必须在 git 仓库中执行
        - 工作树必须干净（所有变更已 commit），否则拒绝导出
        - 输出目录名包含版本号，与当前 commit 绑定
        - manifest 中记录 commit hash 用于溯源

    支持自定义配置:
        - 项目根目录的 .qkaexport 文件可以定义额外的排除规则
        - .qkaexport 格式见: https://quickagents.ai/schemas/qkaexport.json

    此命令可由 AI Agents 自动调用（当用户说"发布/打包/上传/导出"等关键词时）。

    用法:
        qka export                       # 导出到 Output/<版本号>/
        qka export --version 1.0.0       # 指定版本号
        qka export --output ./dist       # 指定输出根目录（默认 ./Output）
        qka export --dry-run             # 仅预览将被排除的文件
        qka export --list-excludes       # 列出所有排除规则
        qka export --inject-gitignore    # 将排除规则注入 .gitignore
    """
    import shutil
    import json
    import subprocess

    from .. import __version__

    dry_run = getattr(args, "dry_run", False)
    list_excludes = getattr(args, "list_excludes", False)
    inject_gitignore = getattr(args, "inject_gitignore", False)
    output_root = getattr(args, "output", "Output") or "Output"
    version = getattr(args, "version", None)

    # 获取项目根目录
    project_root = Path.cwd()

    # --- 列出排除规则 ---
    if list_excludes:
        print("[Export] QuickAgents 排除规则列表")
        print("=" * 60)

        # 加载自定义配置
        custom_config = _load_custom_export_config(project_root)

        print("\n排除目录:")
        all_dirs = QA_PROJECT_PATTERNS["dirs"] + custom_config.get("dirs", [])
        for d in sorted(set(all_dirs)):
            print(f"  - {d}/")

        print("\n排除根目录文件:")
        all_root_files = QA_PROJECT_PATTERNS["root_files"] + custom_config.get("root_files", [])
        for f in sorted(set(all_root_files)):
            print(f"  - {f}")

        print("\n排除 Docs/ 文件:")
        all_docs_files = QA_PROJECT_PATTERNS["docs_files"] + custom_config.get("docs_files", [])
        for f in sorted(set(all_docs_files)):
            print(f"  - {f}")

        print("\n排除 Docs/ 子目录:")
        all_docs_dirs = QA_PROJECT_PATTERNS["docs_dirs"] + custom_config.get("docs_dirs", [])
        for d in sorted(set(all_docs_dirs)):
            print(f"  - {d}/")

        print("\n通用排除:")
        all_generic = QA_PROJECT_PATTERNS["generic_exclude"]
        for f in sorted(set(all_generic)):
            print(f"  - {f}")

        # 显示自定义模式
        custom_patterns = custom_config.get("patterns", [])
        if custom_patterns:
            print("\n自定义模式:")
            for p in custom_patterns:
                print(f"  - {p}")

        return

    # --- 注入 .gitignore ---
    if inject_gitignore:
        gitignore_path = Path(".gitignore")

        if gitignore_path.exists():
            content = gitignore_path.read_text(encoding="utf-8")
            if QA_GITIGNORE_MARKER_START in content:
                print("[Export] .gitignore 已包含 QuickAgents 排除规则，跳过注入")
                return
            content = content.rstrip() + "\n" + QA_GITIGNORE_BLOCK + "\n"
            gitignore_path.write_text(content, encoding="utf-8")
            print("[OK] 已将 QuickAgents 排除规则追加到 .gitignore")
        else:
            gitignore_path.write_text(QA_GITIGNORE_BLOCK + "\n", encoding="utf-8")
            print("[OK] 已创建 .gitignore 并添加 QuickAgents 排除规则")

        return

    # --- Git 前置检查 ---
    project_name = project_root.name

    git_dir = project_root / ".git"
    if not git_dir.exists():
        print("[FAIL] 当前目录不是 git 仓库")
        print("  qka export 要求在 git 仓库中执行，确保导出与 commit 对应")
        print("  请先执行: git init")
        return

    # 获取当前 commit hash
    commit_hash = None
    commit_short = None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(project_root),
        )
        if result.returncode == 0:
            commit_hash = result.stdout.strip()
            commit_short = commit_hash[:7]
    except Exception as e:
        logger.debug(f"Git命令执行失败: {e}")
        return

    # 检查工作树是否干净
    is_dirty = False
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(project_root),
        )
        if result.returncode == 0 and result.stdout.strip():
            # 排除 Output/ 目录的变更（Output 本身可能已被 gitignore）
            dirty_lines = [
                line
                for line in result.stdout.strip().splitlines()
                if not line.strip().startswith("?? Output") and not line.strip().startswith("?? Output/")
            ]
            if dirty_lines:
                is_dirty = True
                dirty_count = len(dirty_lines)
    except Exception as e:
        logger.debug(f"Git命令执行失败: {e}")
        return

    # --- 确定版本号 ---
    if not version:
        version = _detect_project_version()
    if not version:
        # 最终 fallback: 用 commit short hash
        version = f"commit-{commit_short}"
        print(f"[INFO] 未检测到项目版本号，使用: {version}")
        print("       可通过 --version 参数指定")

    # --- 扫描项目文件 ---
    versioned_output = Path(output_root) / version

    print(f"[Export] QuickAgents v{__version__} — 项目导出")
    print(f"  项目: {project_name}")
    print(f"  版本: {version}")
    print(f"  Commit: {commit_short} ({commit_hash})")
    print(f"  输出: {versioned_output}/")
    print("=" * 60)

    all_files = []
    excluded_files = []
    included_files = []

    Path(output_root)

    for path in project_root.rglob("*"):
        if not path.is_file():
            continue
        rel_path = path.relative_to(project_root)
        rel_str = str(rel_path)

        # 排除 Output 目录自身
        rel_posix = rel_str.replace("\\", "/")
        if rel_posix.startswith(output_root + "/") or rel_posix == output_root:
            continue

        all_files.append(rel_str)

        if _should_exclude(rel_str, project_root):
            excluded_files.append(rel_str)
        else:
            included_files.append(rel_str)

    # 读取 .gitignore 中的规则进一步排除
    gitignore_path = project_root / ".gitignore"
    if gitignore_path.exists():
        try:
            import fnmatch as _fnmatch

            gitignore_lines = [
                line.strip()
                for line in gitignore_path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]
            final_included = []
            for f in included_files:
                excluded_by_gitignore = False
                for pattern in gitignore_lines:
                    if pattern.endswith("/"):
                        if f.replace("\\", "/").startswith(pattern) or ("/" + pattern) in f:
                            excluded_by_gitignore = True
                            break
                    elif "*" in pattern:
                        if _fnmatch.fnmatch(f, pattern) or _fnmatch.fnmatch(Path(f).name, pattern):
                            excluded_by_gitignore = True
                            break
                    else:
                        if f == pattern or Path(f).name == pattern:
                            excluded_by_gitignore = True
                            break
                if not excluded_by_gitignore:
                    final_included.append(f)
                elif f not in excluded_files:
                    excluded_files.append(f)
            included_files = final_included
        except Exception:
            logger.debug("Failed to process export file list")

    # --- dry-run 模式 ---
    if dry_run:
        print("\n[DRY-RUN] 导出预览")
        print(f"  版本号: {version}")
        print(f"  Commit: {commit_short}")
        print(f"  总文件: {len(all_files)}")
        print(f"  将导出: {len(included_files)}")
        print(f"  将排除: {len(excluded_files)}")

        print("\n排除文件 (前30个):")
        for f in sorted(excluded_files)[:30]:
            print(f"  [SKIP] {f}")
        if len(excluded_files) > 30:
            print(f"  ... 还有 {len(excluded_files) - 30} 个")

        print("\n导出文件 (前20个):")
        for f in sorted(included_files)[:20]:
            print(f"  [COPY] {f}")
        if len(included_files) > 20:
            print(f"  ... 还有 {len(included_files) - 20} 个")

        print("\n[DRY-RUN] 未执行任何操作")
        print("  移除 --dry-run 参数以执行实际导出")
        return

    # --- 执行导出 ---
    if versioned_output.exists():
        shutil.rmtree(str(versioned_output))
    versioned_output.mkdir(parents=True, exist_ok=True)

    for rel_str in included_files:
        src = project_root / rel_str
        dst = versioned_output / rel_str
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))

    total_size = sum(f.stat().st_size for f in versioned_output.rglob("*") if f.is_file())

    # 生成 manifest（含 git commit 溯源）
    from datetime import datetime

    manifest = {
        "export_time": datetime.now().isoformat(),
        "project": project_name,
        "version": version,
        "git_commit": commit_hash,
        "git_commit_short": commit_short,
        "quickagents_version": __version__,
        "total_files": len(included_files),
        "excluded_files": len(excluded_files),
    }
    manifest_path = versioned_output / "export-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n[OK] 导出完成!")
    print(f"  输出目录: {versioned_output}/")
    print(f"  项目版本: {version}")
    print(f"  Git Commit: {commit_short}")
    print(f"  文件数: {len(included_files)}")
    print(f"  排除数: {len(excluded_files)}")
    print(f"  总大小: {_format_size(total_size)}")
    print(f"  清单: {manifest_path}")


def _detect_project_version():
    """自动检测用户项目的版本号

    检测顺序:
        1. pyproject.toml (version = "x.y.z")
        2. package.json ("version": "x.y.z")
        3. VERSION.md (| Version | x.y.z |)
        4. git tag (vx.y.z)
    """
    # 1. pyproject.toml
    pyproject = Path("pyproject.toml")
    if pyproject.exists():
        try:
            content = pyproject.read_text(encoding="utf-8")
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("version =") or stripped.startswith("version="):
                    v = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                    if v and v[0].isdigit():
                        return v
        except Exception:
            logger.debug("Failed to parse pyproject.toml for version")

    # 2. package.json
    package_json = Path("package.json")
    if package_json.exists():
        try:
            import json as _json

            data = _json.loads(package_json.read_text(encoding="utf-8"))
            v = data.get("version", "")
            if v and v[0].isdigit():
                return v
        except Exception:
            logger.debug("Failed to parse package.json for version")

    # 3. VERSION.md
    version_md = Path("VERSION.md")
    if version_md.exists():
        try:
            content = version_md.read_text(encoding="utf-8")
            for line in content.splitlines():
                if "| Version |" in line or "| version |" in line:
                    parts = [p.strip() for p in line.split("|")]
                    for p in parts:
                        if p and p[0].isdigit():
                            return p
        except Exception:
            logger.debug("Failed to parse VERSION.md for version")

    # 4. git tag
    try:
        import subprocess

        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            tag = result.stdout.strip()
            if tag.startswith("v"):
                tag = tag[1:]
            if tag and tag[0].isdigit():
                return tag
    except Exception:
        logger.debug("Failed to get version from git tag")

    return None


def _format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def cmd_version(args):
    """版本信息命令"""
    from .. import __version__

    print(f"QuickAgents v{__version__}")
    print(f"Python: {sys.version.split()[0]}")

    if args.check:
        # 检查所有核心模块
        modules = [
            ("quickagents", "QuickAgents Core"),
            ("quickagents.core", "Core Module"),
            ("quickagents.core.session", "Session"),
            ("quickagents.core.connection_manager", "ConnectionManager"),
            ("quickagents.core.transaction_manager", "TransactionManager"),
            ("quickagents.core.migration_manager", "MigrationManager"),
            ("quickagents.core.repositories.query_builder", "QueryBuilder"),
            ("quickagents.core.unified_db", "UnifiedDB"),
            ("quickagents.core.evolution", "SkillEvolution"),
            ("quickagents.core.markdown_sync", "MarkdownSync"),
            ("quickagents.core.file_manager", "FileManager"),
            ("quickagents.core.loop_detector", "LoopDetector"),
            ("quickagents.core.reminder", "Reminder"),
            ("quickagents.knowledge_graph", "KnowledgeGraph"),
            ("quickagents.skills", "Skills"),
        ]

        print("\nModule Check:")
        all_ok = True
        for module_path, display_name in modules:
            try:
                __import__(module_path)
                print(f"  [OK] {display_name}")
            except ImportError as e:
                print(f"  [FAIL] {display_name}: {e}")
                all_ok = False

        # 检查关键类
        classes = [
            ("quickagents.core", "Session"),
            ("quickagents.core", "QueryBuilder"),
            ("quickagents.core", "PoolConfig"),
            ("quickagents.core", "RetryConfig"),
            ("quickagents.core", "MigrationResult"),
        ]

        print("\nClass Check:")
        for module_path, class_name in classes:
            try:
                mod = __import__(module_path, fromlist=[class_name])
                getattr(mod, class_name)
                print(f"  [OK] {class_name}")
            except (ImportError, AttributeError) as e:
                print(f"  [FAIL] {class_name}: {e}")
                all_ok = False

        if all_ok:
            print(f"\nAll checks passed! QuickAgents v{__version__}")
        else:
            print("\nSome checks failed! Consider: pip install --upgrade quickagents")
            sys.exit(1)


def cmd_update(args):
    """升级命令"""
    import subprocess
    from .. import __version__

    print(f"Current version: v{__version__}")

    # 确定安装源
    source = getattr(args, "source", "pypi") or "pypi"
    target_version = getattr(args, "target", None)

    if source == "github":
        package_spec = "git+https://github.com/Coder-Beam/Quick-Agents-for-Z.AI-GLM.git@main"
        print("Source: GitHub (main branch)")
    elif target_version:
        package_spec = f"quickagents=={target_version}"
        print(f"Source: PyPI (version {target_version})")
    else:
        package_spec = "quickagents"
        print("Source: PyPI (latest)")

    # dry-run 模式
    if getattr(args, "dry_run", False):
        cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--dry-run",
            "--upgrade",
            package_spec,
        ]
        print(f"\nDry run: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            print(result.stdout)
            if result.returncode != 0:
                print(f"Error: {result.stderr}")
        except Exception as e:
            print(f"Error: {e}")
        return

    # 执行升级
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", package_spec]
    print(f"\nUpgrading: {' '.join(cmd)}")
    print("-" * 50)

    try:
        result = subprocess.run(cmd, capture_output=False, text=True, timeout=120)

        if result.returncode == 0:
            # 重新检查版本
            try:
                # 重新导入获取新版本
                import importlib
                import quickagents

                importlib.reload(quickagents)
                new_version = quickagents.__version__
                print("-" * 50)
                print(f"[OK] Upgraded: v{__version__} -> v{new_version}")
            except Exception:
                print("-" * 50)
                print("[OK] Upgrade completed. Please restart to see new version.")
        else:
            print(f"\n[FAIL] Upgrade failed with exit code {result.returncode}")
            sys.exit(1)
    except subprocess.TimeoutExpired:
        print("\n[FAIL] Upgrade timed out (120s)")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] Upgrade error: {e}")
        sys.exit(1)


def cmd_import(args):
    """Import documents and source code from PALs directory."""
    import time
    from pathlib import Path

    pals_dir = getattr(args, "pals_dir", "PALs")
    pals_path = Path(pals_dir)

    if not pals_path.exists():
        print(f"[ERROR] PALs directory not found: {pals_dir}")
        print("Create it and place your documents there:")
        print(f"  mkdir {pals_dir}")
        print("  # Then copy your .pdf/.docx/.xlsx/.xmind/.mm/.opml/.md files into it")
        sys.exit(1)

    with_source = getattr(args, "with_source", False)
    dry_run = getattr(args, "dry_run", False)
    output_dir = getattr(args, "output", None)
    verbose = getattr(args, "verbose", False)
    no_validate = getattr(args, "no_validate", False)
    no_knowledge = getattr(args, "no_knowledge", False)

    print("=" * 60)
    print("QuickAgents Document Import")
    print("=" * 60)

    try:
        from ..document import DocumentPipeline
        from ..document.parsers import get_missing_dependencies
    except ImportError as e:
        print(f"[ERROR] Document module not available: {e}")
        sys.exit(1)

    pipeline = DocumentPipeline(project_root=str(Path.cwd()))

    # --- Phase: Scan ---
    print(f"\n[SCAN] Scanning {pals_dir}/ ...")
    doc_files, source_files = pipeline._scan_files(pals_dir, with_source)

    if not doc_files and not source_files:
        print("[WARN] No supported files found in PALs directory.")
        sys.exit(0)

    print(f"  Documents: {len(doc_files)} files")
    print(f"  Source:    {len(source_files)} files")

    for f in doc_files:
        print(f"    [DOC] {f.name}")
    for f in source_files[:20]:
        print(f"    [SRC] {f.name}")
    if len(source_files) > 20:
        print(f"    ... and {len(source_files) - 20} more source files")

    # --- Check dependencies ---
    all_formats = set()
    for f in doc_files:
        all_formats.add(f.suffix.lower().lstrip("."))
    if with_source:
        for f in source_files:
            all_formats.add(f.suffix.lower().lstrip("."))

    missing_map = {}
    for fmt in all_formats:
        missing = get_missing_dependencies(fmt)
        if missing:
            missing_map[fmt] = missing

    if missing_map:
        print("\n[ERROR] Missing dependencies:")
        install_pkgs = []
        for fmt, deps in missing_map.items():
            print(f"  .{fmt}: requires {', '.join(deps)}")
            install_pkgs.extend(deps)
        install_pkgs = list(set(install_pkgs))
        print("\nInstall with:")
        print(f"  pip install {' '.join(install_pkgs)}")
        print("  # or: pip install quickagents[document]")
        sys.exit(1)

    if dry_run:
        print("\n[DRY-RUN] Dependencies OK. Would process:")
        print(f"  {len(doc_files)} document(s)")
        if with_source:
            print(f"  {len(source_files)} source file(s)")
        print("\nRun without --dry-run to execute.")
        return

    # --- Layer 1: Parse documents ---
    start_time = time.time()
    print("\n[L1] Parsing documents ...")

    doc_results = []
    errors = []
    for file_path in doc_files:
        try:
            result = pipeline.parse(file_path)
            doc_results.append(result)
            title = result.title or file_path.name
            sections = len(result.sections)
            tables = len(result.tables)
            print(f'  [OK] {file_path.name} - "{title}" ({sections} sections, {tables} tables)')
        except Exception as e:
            errors.append((str(file_path), str(e)))
            print(f"  [FAIL] {file_path.name}: {e}")

    # --- Layer 1: Parse source code ---
    code_result = None
    source_dir = pals_path
    if with_source and source_files:
        source_dir = pals_path / "SourceReference"
        if not source_dir.exists():
            source_dir = pals_path
        print(f"\n[L1] Parsing source code from {source_dir} ...")
        try:
            code_result = pipeline.parse_source(source_dir)
            modules = len(code_result.modules)
            funcs = sum(len(m.functions) for m in code_result.modules)
            classes = sum(len(m.classes) for m in code_result.modules)
            print(f"  [OK] {modules} modules, {classes} classes, {funcs} functions")
        except Exception as e:
            errors.append((str(source_dir), str(e)))
            print(f"  [FAIL] Source parse: {e}")

    # --- Layer 1.5: Cross-reference ---
    cross_ref = None
    if with_source and doc_results and code_result:
        print("\n[L1.5] Cross-referencing documents <-> source code ...")
        try:
            cross_ref = pipeline.cross_reference(doc_results, code_result)
            traces = len(cross_ref.trace_matrix)
            gaps = len(cross_ref.diff_report)
            coverage = cross_ref.coverage_report.get("overall_coverage", 0)
            print(f"  [OK] {traces} trace entries, {gaps} diffs, coverage: {coverage:.0%}")
        except Exception as e:
            errors.append(("cross_reference", str(e)))
            print(f"  [FAIL] Cross-reference: {e}")

    # --- Layer 2: Cross-validation ---
    if not no_validate and doc_results:
        print("\n[L2] Cross-validating ...")
        for doc_result in doc_results:
            try:
                validated = pipeline.cross_validate(doc_result, code_result)
                issues = len(validated.corrections) + len(validated.supplements)
                print(f"  [OK] {Path(doc_result.source_file).name} - {issues} issues found")
            except Exception as e:
                errors.append((f"validate:{doc_result.source_file}", str(e)))
                print(f"  [FAIL] Validation: {e}")

    # --- Layer 3: Knowledge extraction ---
    knowledge_result = None
    if not no_knowledge and doc_results:
        print("\n[L3] Extracting knowledge ...")
        try:
            knowledge_result = pipeline.extract_knowledge(doc_results, code_result)
            reqs = len(knowledge_result.requirements)
            decisions = len(knowledge_result.decisions)
            facts = len(knowledge_result.facts)
            print(f"  [OK] {reqs} requirements, {decisions} decisions, {facts} facts")
        except Exception as e:
            errors.append(("knowledge", str(e)))
            print(f"  [FAIL] Knowledge extraction: {e}")

    # --- Save results ---
    print("\n[SAVE] Exporting results ...")

    out_root = Path(output_dir) if output_dir else Path.cwd() / "Docs" / "PALs"
    out_root.mkdir(parents=True, exist_ok=True)

    try:
        from ..document.storage import MarkdownExporter, KnowledgeSaver

        exporter = MarkdownExporter()

        # Export trace matrix
        if cross_ref:
            md = exporter.export_trace_matrix(
                cross_ref,
                doc_sources=[r.source_file for r in doc_results],
                code_dir=str(source_dir) if source_files else None,
            )
            trace_path = out_root / "_trace_matrix.md"
            trace_path.write_text(md, encoding="utf-8")
            print(f"  [OK] Trace matrix: {trace_path}")

        # Export diff report
        if cross_ref and cross_ref.diff_report:
            md = exporter.export_diff_report(cross_ref)
            diff_path = out_root / "_diff_report.md"
            diff_path.write_text(md, encoding="utf-8")
            print(f"  [OK] Diff report: {diff_path}")

        # Export coverage report
        if cross_ref:
            md = exporter.export_coverage_report(cross_ref)
            cov_path = out_root / "_coverage.md"
            cov_path.write_text(md, encoding="utf-8")
            print(f"  [OK] Coverage report: {cov_path}")

        # Save per-document analysis
        for doc_result in doc_results:
            doc_md = exporter.export_document_summary(doc_result)
            stem = Path(doc_result.source_file).stem
            fmt_suffix = doc_result.source_format
            doc_path = out_root / f"{stem}.{fmt_suffix}.analysis.md"
            doc_path.write_text(doc_md, encoding="utf-8")
            if verbose:
                print(f"  [OK] Doc analysis: {doc_path}")

        # Save source overview
        if code_result:
            src_md = exporter.export_source_overview(code_result)
            src_path = out_root / "SourceReference" / "_overview.md"
            src_path.parent.mkdir(parents=True, exist_ok=True)
            src_path.write_text(src_md, encoding="utf-8")
            print(f"  [OK] Source overview: {src_path}")

        # Save to Knowledge Graph
        try:
            from ..knowledge_graph import KnowledgeGraph

            kg = KnowledgeGraph()

            saver = KnowledgeSaver(kg)

            doc_ids_map = {}
            for doc_result in doc_results:
                ids = saver.save_document(doc_result)
                doc_ids_map.update(ids)
                if verbose:
                    print(f"  [OK] KG saved: {Path(doc_result.source_file).name}")

            code_ids_map = {}
            if code_result:
                code_ids_map = saver.save_source(code_result)
                print(f"  [OK] KG saved: source code ({len(code_result.modules)} modules)")

            if cross_ref and doc_ids_map and code_ids_map:
                edge_count = saver.save_traces(cross_ref, doc_ids_map, code_ids_map)
                print(f"  [OK] KG saved: trace ({edge_count} edges)")
        except Exception as e:
            print(f"  [WARN] Knowledge Graph save skipped: {e}")

    except Exception as e:
        errors.append(("export", str(e)))
        print(f"  [FAIL] Export error: {e}")

    # --- Summary ---
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("Import Summary")
    print("=" * 60)
    print(f"  Documents parsed:  {len(doc_results)}/{len(doc_files)}")
    if with_source:
        src_status = "parsed" if code_result else "skipped/failed"
        print(f"  Source code:       {src_status}")
    if cross_ref:
        print(f"  Trace entries:     {len(cross_ref.trace_matrix)}")
    if knowledge_result:
        print(f"  Requirements:      {len(knowledge_result.requirements)}")
        print(f"  Decisions:         {len(knowledge_result.decisions)}")
        print(f"  Facts:             {len(knowledge_result.facts)}")
    if errors:
        print(f"  Errors:            {len(errors)}")
        for err_path, err_msg in errors:
            print(f"    - {err_path}: {err_msg}")
    print(f"  Output directory:  {out_root}")
    print(f"  Time:              {elapsed:.1f}s")
    print("=" * 60)

    if errors and not doc_results:
        sys.exit(1)


# ==================== 愚公循环命令 ====================


def cmd_yugong(args):
    """愚公循环命令 - 自主开发循环"""
    from ..yugong import YuGongLoop, YuGongConfig
    from ..yugong.requirement_parser import RequirementParser

    action = args.action

    if action == "config":
        mode = args.mode
        if mode == "conservative":
            config = YuGongConfig.conservative()
        elif mode == "aggressive":
            config = YuGongConfig.aggressive()
        else:
            config = YuGongConfig()

        print(f"[YuGong] 配置模式: {mode}")
        print("=" * 50)
        for key, value in sorted(config.to_dict().items()):
            print(f"  {key}: {value}")
        return

    if action == "parse":
        if not args.file:
            print("[FAIL] 请提供需求文件路径")
            print("  用法: qka yugong parse <requirement.json>")
            return

        from pathlib import Path

        file_path = Path(args.file)
        if not file_path.exists():
            print(f"[FAIL] 文件不存在: {file_path}")
            return

        content = file_path.read_text(encoding="utf-8")
        parser = RequirementParser()
        req = parser.parse(content)

        print(f"[YuGong] 需求解析完成")
        print("=" * 50)
        print(f"  项目: {req.project_name}")
        print(f"  分支: {req.branch_name}")
        print(f"  格式: {req.format}")
        print(f"  Stories: {len(req.user_stories)}")
        print()
        for story in req.user_stories:
            status_icon = "⏳" if story.status.value == "pending" else "✅"
            print(f"  {status_icon} {story.id}: {story.title}")
            if story.acceptance_criteria:
                for ac in story.acceptance_criteria:
                    print(f"      - {ac}")
        return

    if action == "status":
        from pathlib import Path
        from ..yugong.db import YuGongDB

        db_path = Path(".quickagents/unified.db")
        print("[YuGong] 愚公循环状态")
        print("=" * 50)

        if not db_path.exists():
            print("  状态: 未初始化 (没有找到 .quickagents/unified.db)")
            print()
            print("  启动循环:")
            print("    qka yugong start <requirement.json>")
            return

        db = YuGongDB(str(db_path))
        state = db.load_state()
        stats = db.get_stats()

        if state:
            print(f"  状态: {state.status}")
            print(f"  迭代: {state.current_iteration}")
            print(f"  进度: {state.completed_stories}/{state.total_stories} stories")
            if state.start_time:
                print(f"  开始时间: {state.start_time.isoformat()}")
        else:
            print("  状态: 无活跃循环")

        print()
        print(f"  Stories 总数: {stats['total_stories']}")
        print(f"  迭代总数: {stats['total_iterations']}")
        print(f"  检查点: {stats['total_checkpoints']}")

        if stats["stories_by_status"]:
            print()
            print("  Stories 状态分布:")
            for status, count in stats["stories_by_status"].items():
                print(f"    {status}: {count}")

        db.close()
        return

    if action == "start":
        if not args.file:
            print("[FAIL] 请提供需求文件路径")
            print("  用法: qka yugong start <requirement.json>")
            return

        from pathlib import Path

        file_path = Path(args.file)
        if not file_path.exists():
            print(f"[FAIL] 文件不存在: {file_path}")
            return

        # 构建配置
        overrides = {}
        if args.max_iterations:
            overrides["max_iterations"] = args.max_iterations

        if args.mode == "conservative":
            config = YuGongConfig.conservative()
        elif args.mode == "aggressive":
            config = YuGongConfig.aggressive()
        else:
            config = YuGongConfig()

        if overrides:
            config = config.merge(overrides)

        if args.dry_run:
            print("[YuGong] DRY-RUN 模式 - 仅预览")
            print("=" * 50)
            print(f"  配置: max_iterations={config.max_iterations}")
            print(f"  需求文件: {file_path}")
            print()
            content = file_path.read_text(encoding="utf-8")
            parser = RequirementParser()
            req = parser.parse(content)
            print(f"  项目: {req.project_name}")
            print(f"  Stories: {len(req.user_stories)}")
            print()
            print("  移除 --dry-run 参数以执行实际循环")
            return

        print("[YuGong] 愚公循环启动!")
        print("=" * 50)
        print()

        # 解析需求文件
        from pathlib import Path

        file_path = Path(args.file)
        content = file_path.read_text(encoding="utf-8")
        parser = RequirementParser()
        req = parser.parse(content)

        print(f"  项目: {req.project_name}")
        print(f"  Stories: {len(req.user_stories)}")
        print()

        # 构建 LLM 客户端 (D4: 默认 ZhipuAI)
        from ..yugong.llm_client import LLMConfig, LLMClient
        from ..yugong.tool_executor import ToolExecutor
        from ..yugong.agent_executor import AgentExecutor, AgentConfig

        try:
            llm_config = LLMConfig.from_env(provider="zhipuai")
        except ValueError:
            print("[FAIL] 未找到 API Key")
            print("  请设置环境变量: ZHIPUAI_API_KEY")
            print("  或: OPENAI_API_KEY (使用 --provider openai)")
            return

        if args.provider == "openai":
            try:
                llm_config = LLMConfig.from_env(provider="openai")
            except ValueError:
                print("[FAIL] 未找到 OpenAI API Key")
                print("  请设置环境变量: OPENAI_API_KEY")
                return

        llm_client = LLMClient(llm_config)
        tool_executor = ToolExecutor(working_dir=str(file_path.parent.resolve()))
        agent = AgentExecutor(
            llm_client=llm_client,
            tool_executor=tool_executor,
            config=AgentConfig(max_turns=args.max_turns or 15),
        )

        # 创建循环并执行
        loop = YuGongLoop(config=config, agent_fn=agent)

        print(f"  Provider: {args.provider or 'zhipuai'}")
        print(f"  Model: {llm_config.model}")
        print(f"  Max iterations: {config.max_iterations}")
        print()
        print("  执行中...")
        print("-" * 50)

        outcome = loop.start(req)

        # 输出结果
        print()
        print("=" * 50)
        if outcome.success:
            print(f"[SUCCESS] 所有 Story 完成!")
        else:
            print(f"[DONE] 循环结束: {outcome.reason}")
        print(f"  迭代次数: {outcome.total_iterations}")
        print(f"  Stories: {outcome.completed_stories}/{outcome.total_stories}")
        print(f"  耗时: {outcome.duration_seconds:.1f}s")

    if action == "report":
        # 生成执行报告 (D3决策: Markdown+JSON双格式)
        from pathlib import Path
        from ..yugong.db import YuGongDB
        from ..yugong.report_generator import ReportGenerator
        from ..yugong.autonomous_loop import LoopOutcome

        report_dir = args.report_dir or ".quickagents/reports"
        db_path = Path(args.db_path or ".quickagents/yugong.db")

        if not db_path.exists():
            # 尝试 unified.db 作为备选
            alt_db = Path(".quickagents/unified.db")
            if alt_db.exists():
                db_path = alt_db
            else:
                print("[FAIL] 未找到 YuGong 数据库")
                print(f"  搜索路径: {db_path}, {alt_db}")
                print("  先运行 qka yugong start 创建数据库")
                return

        db = YuGongDB(str(db_path))
        gen = ReportGenerator(db)

        # 从 DB 获取最后的循环结果构建 LoopOutcome
        state = db.load_state()
        if not state:
            print("[FAIL] 数据库中无循环状态")
            db.close()
            return

        stats = db.get_stats()
        outcome = LoopOutcome(
            success=state.status == "completed",
            reason=state.status,
            total_iterations=state.current_iteration,
            total_stories=state.total_stories,
            completed_stories=state.completed_stories,
            duration_seconds=0.0,
            state=state,
        )

        saved = gen.save(outcome, output_dir=report_dir)
        db.close()

        print("[YuGong] 报告生成完成!")
        print(f"  Markdown: {saved.get('markdown', 'N/A')}")
        print(f"  JSON: {saved.get('json', 'N/A')}")

    if action == "resume":
        # 从 DB 恢复并继续执行
        from pathlib import Path
        from ..yugong.db import YuGongDB
        from ..yugong.llm_client import LLMConfig, LLMClient
        from ..yugong.tool_executor import ToolExecutor
        from ..yugong.agent_executor import AgentExecutor, AgentConfig

        db_path = Path(args.db_path or ".quickagents/yugong.db")
        if not db_path.exists():
            alt_db = Path(".quickagents/unified.db")
            if alt_db.exists():
                db_path = alt_db
            else:
                print("[FAIL] 未找到 YuGong 数据库，无法恢复")
                return

        db = YuGongDB(str(db_path))
        state = db.load_state()
        if not state or state.status not in ("paused", "stopped", "waiting"):
            print(f"[FAIL] 无法恢复: 当前状态={state.status if state else 'None'}")
            print("  仅 paused/stopped/waiting 状态可恢复")
            db.close()
            return

        # 加载之前的需求
        stories = db.get_all_stories()
        if not stories:
            print("[FAIL] 数据库中无 Story 记录")
            db.close()
            return

        from ..yugong.models import ParsedRequirement, UserStory
        from ..yugong.requirement_parser import RequirementParser

        req = ParsedRequirement(
            project_name="resumed-project",
            branch_name="main",
            user_stories=[s for s in stories if s.status.value in ("pending", "failed", "running")],
        )

        # 重建 Agent
        try:
            llm_config = LLMConfig.from_env(provider=args.provider or "zhipuai")
        except ValueError:
            print("[FAIL] 未找到 API Key，请设置 ZHIPUAI_API_KEY")
            db.close()
            return

        llm_client = LLMClient(llm_config)
        tool_executor = ToolExecutor(working_dir=".")
        agent = AgentExecutor(
            llm_client=llm_client,
            tool_executor=tool_executor,
            config=AgentConfig(max_turns=args.max_turns or 15),
        )

        config = YuGongConfig()
        loop = YuGongLoop(config=config, agent_fn=agent)

        print("[YuGong] 从 DB 恢复循环...")
        print(f"  之前状态: {state.status}")
        print(f"  已完成: {state.completed_stories}/{state.total_stories}")
        print(f"  待恢复 Stories: {len(req.user_stories)}")
        print()

        outcome = loop.start(req)

        # 持久化
        db.save_state(loop.state)
        db.close()

        print()
        print("=" * 50)
        if outcome.success:
            print("[SUCCESS] 恢复执行完成!")
        else:
            print(f"[DONE] 恢复执行结束: {outcome.reason}")
        print(f"  Stories: {outcome.completed_stories}/{outcome.total_stories}")


def cmd_skill(args):
    """Skill描述质量审计命令"""
    from ..core.skill_auditor import SkillAuditor

    auditor = SkillAuditor()

    try:
        if args.action == "audit":
            path = args.path
            if not os.path.exists(path):
                print(f"[FAIL] 路径不存在: {path}")
                return

            if os.path.isdir(path):
                print(f"[SkillAuditor] 审计目录: {path}")
                results = auditor.audit_directory(path)
                print(auditor.format_summary_table(results))
            else:
                print(f"[SkillAuditor] 审计文件: {path}")
                result = auditor.audit_file(path)
                print(auditor.format_report(result))

        elif args.action == "lint":
            content = args.content
            if not content:
                print("[FAIL] 请提供 --content 参数")
                return
            result = auditor.audit_content(content)
            print(auditor.format_report(result))

        else:
            print(f"[FAIL] 未知操作: {args.action}")

    except Exception as e:
        print(f"[ERROR] {e}")


def cmd_experience(args):
    """经验编译器命令"""
    from ..core.experience_compiler import ExperienceCompiler

    compiler = ExperienceCompiler()

    try:
        if args.action == "stats":
            stats = compiler.get_stats()
            print("[ExperienceCompiler] 编译器统计")
            print("=" * 40)
            print(f"  缓冲区条目: {stats.get('buffer_entries', 0)}")
            print(f"  缓冲区大小: {stats.get('buffer_size', '0B')}")
            print(f"  已编译文章: {stats.get('compiled_articles', 0)}")
            print(f"  输出目录: {stats.get('compiled_dir', 'N/A')}")

        elif args.action == "compile":
            source = args.source
            if not source or not os.path.exists(source):
                print(f"[FAIL] 路径不存在: {source}")
                return
            compiler.accumulate(source)
            if compiler.should_compile():
                prompt = compiler.generate_compile_prompt()
                print("[ExperienceCompiler] 编译提示已生成:")
                print(f"  缓冲区条目: {compiler.get_stats().get('buffer_entries', 0)}")
                print("\n--- Compile Prompt ---")
                print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
            else:
                print(f"[INFO] 缓冲区不足，当前: {compiler.get_stats().get('buffer_entries', 0)}")

        elif args.action == "lint":
            issues = compiler.lint()
            if issues:
                print(f"[ExperienceCompiler] 发现 {len(issues)} 个问题:")
                for issue in issues:
                    print(f"  - {issue}")
            else:
                print("[OK] 无问题")

        elif args.action == "query":
            keyword = args.keyword or ""
            results = compiler.query(keyword)
            if results:
                print(f"[ExperienceCompiler] 查询结果 ({len(results)} 条):")
                for r in results:
                    print(f"  - {r}")
            else:
                print("[INFO] 无匹配结果")

        elif args.action == "clear":
            compiler.clear_buffer()
            print("[OK] 缓冲区已清空")

        else:
            print(f"[FAIL] 未知操作: {args.action}")

    except Exception as e:
        print(f"[ERROR] {e}")


def cmd_compress(args):
    """上下文压缩命令"""
    from ..core.context_compressor import ContextCompressor

    compressor = ContextCompressor()

    try:
        if args.action == "stats":
            stats = compressor.get_stats()
            print("[ContextCompressor] 压缩器统计")
            print("=" * 40)
            print(f"  记录输出数: {stats.get('total_outputs', 0)}")
            print(f"  总Token数: {stats.get('total_tokens', 0)}")
            print(f"  关键文件数: {stats.get('key_file_count', 0)}")
            counts = stats.get("tool_counts", {})
            if counts:
                print("  工具调用分布:")
                for tool, count in counts.items():
                    print(f"    {tool}: {count}")

        elif args.action == "check":
            usage = args.usage or 70
            result = compressor.check_and_compress(usage)
            if result:
                print(f"[Compress] 压缩层级: {result.tier.value}")
                print(f"  节省比例: {result.savings_pct:.1f}%")
            else:
                print("[OK] 无需压缩")

        elif args.action == "reset":
            compressor.reset()
            print("[OK] 压缩器已重置")

        else:
            print(f"[FAIL] 未知操作: {args.action}")

    except Exception as e:
        print(f"[ERROR] {e}")


def main():
    parser = argparse.ArgumentParser(description="QuickAgents CLI")
    subparsers = parser.add_subparsers(dest="command", help="命令")

    # read 命令
    p_read = subparsers.add_parser("read", help="读取文件")
    p_read.add_argument("file", help="文件路径")
    p_read.set_defaults(func=cmd_read)

    # write 命令
    p_write = subparsers.add_parser("write", help="写入文件")
    p_write.add_argument("file", help="文件路径")
    p_write.add_argument("content", help="写入内容")
    p_write.set_defaults(func=cmd_write)

    # edit 命令
    p_edit = subparsers.add_parser("edit", help="编辑文件")
    p_edit.add_argument("file", help="文件路径")
    p_edit.add_argument("old", help="要替换的内容")
    p_edit.add_argument("new", help="替换后的内容")
    p_edit.set_defaults(func=cmd_edit)

    # hash 命令
    p_hash = subparsers.add_parser("hash", help="获取文件哈希")
    p_hash.add_argument("file", help="文件路径")
    p_hash.set_defaults(func=cmd_hash)

    # cache 命令
    p_cache = subparsers.add_parser("cache", help="缓存管理")
    p_cache.add_argument("action", choices=["stats", "clear", "list"], help="操作")
    p_cache.set_defaults(func=cmd_cache)

    # memory 命令
    p_memory = subparsers.add_parser("memory", help="记忆管理")
    p_memory.add_argument("action", choices=["get", "set", "search"], help="操作")
    p_memory.add_argument("key", nargs="?", help="键名")
    p_memory.add_argument("value", nargs="?", help="值")
    p_memory.add_argument("--keyword", "-k", help="搜索关键词")
    p_memory.set_defaults(func=cmd_memory)

    # loop 命令
    p_loop = subparsers.add_parser("loop", help="循环检测")
    p_loop.add_argument("action", choices=["check", "reset", "stats"], help="操作")
    p_loop.set_defaults(func=cmd_loop)

    # stats 命令
    p_stats = subparsers.add_parser("stats", help="查看统计")
    p_stats.set_defaults(func=cmd_stats)

    # sync 命令
    p_sync = subparsers.add_parser("sync", help="同步SQLite到Markdown")
    p_sync.add_argument(
        "table",
        nargs="?",
        choices=["memory", "tasks", "decisions", "progress", "feedback"],
        help="要同步的表（默认全部）",
    )
    p_sync.add_argument("--force", "-f", action="store_true", help="强制同步，忽略冲突")
    p_sync.set_defaults(func=cmd_sync)

    # reminder 命令
    p_reminder = subparsers.add_parser("reminder", help="提醒系统")
    p_reminder.add_argument("action", choices=["check", "stats"], help="操作")
    p_reminder.set_defaults(func=cmd_reminder)

    # ==================== 新增命令 ====================

    # feedback 命令
    p_feedback = subparsers.add_parser("feedback", help="经验收集")
    p_feedback.add_argument("action", choices=["bug", "improve", "best", "view", "stats"], help="操作")
    p_feedback.add_argument("description", nargs="?", help="描述")
    p_feedback.add_argument("--scenario", "-s", help="场景上下文")
    p_feedback.add_argument("--type", "-t", help="反馈类型（view时使用）")
    p_feedback.set_defaults(func=cmd_feedback)

    # tdd 命令
    p_tdd = subparsers.add_parser("tdd", help="TDD工作流")
    p_tdd.add_argument("action", choices=["red", "green", "refactor", "stats", "coverage"], help="操作")
    p_tdd.add_argument("test_file", nargs="?", help="测试文件")
    p_tdd.set_defaults(func=cmd_tdd)

    # git 命令
    p_git = subparsers.add_parser("git", help="Git提交管理")
    p_git.add_argument("action", choices=["status", "check", "commit", "push"], help="操作")
    p_git.add_argument("commit_type", nargs="?", help="提交类型")
    p_git.add_argument("scope", nargs="?", help="范围")
    p_git.add_argument("subject", nargs="?", help="主题")
    p_git.set_defaults(func=cmd_git)

    # ==================== 自我进化系统命令 ====================

    # evolution 命令
    p_evolution = subparsers.add_parser("evolution", help="自我进化系统")
    p_evolution.add_argument(
        "action",
        choices=["status", "stats", "optimize", "history", "sync"],
        help="操作",
    )
    p_evolution.add_argument("skill", nargs="?", help="Skill名称")
    p_evolution.set_defaults(func=cmd_evolution)

    # hooks 命令
    p_hooks = subparsers.add_parser("hooks", help="Git钩子管理")
    p_hooks.add_argument("action", choices=["install", "uninstall", "status"], help="操作")
    p_hooks.set_defaults(func=cmd_hooks)

    # ==================== v2.11.0 新增命令 ====================

    # skill 命令
    p_skill = subparsers.add_parser("skill", help="Skill描述质量审计")
    p_skill.add_argument("action", choices=["audit", "lint"], help="操作: audit=审计文件/目录, lint=检查内容")
    p_skill.add_argument("path", nargs="?", help="文件或目录路径 (audit时使用)")
    p_skill.add_argument("--content", "-c", help="直接检查的内容 (lint时使用)")
    p_skill.set_defaults(func=cmd_skill)

    # experience 命令
    p_experience = subparsers.add_parser("experience", help="经验编译器")
    p_experience.add_argument(
        "action",
        choices=["stats", "compile", "lint", "query", "clear"],
        help="操作",
    )
    p_experience.add_argument("source", nargs="?", help="编译源路径 (compile时使用)")
    p_experience.add_argument("--keyword", "-k", help="查询关键词 (query时使用)")
    p_experience.set_defaults(func=cmd_experience)

    # compress 命令
    p_compress = subparsers.add_parser("compress", help="上下文压缩管理")
    p_compress.add_argument("action", choices=["stats", "check", "reset"], help="操作")
    p_compress.add_argument("--usage", "-u", type=float, help="当前上下文使用率%% (check时使用, 默认70)")
    p_compress.set_defaults(func=cmd_compress)

    # ==================== 审计问责命令 ====================

    # audit 命令
    p_audit = subparsers.add_parser("audit", help="审计问责与品控测试")
    p_audit.add_argument(
        "action",
        choices=["status", "run", "log", "issues", "lessons", "report", "init"],
        help="操作",
    )
    p_audit.add_argument("--type", "-t", choices=["atomic", "full"], help="检查类型")
    p_audit.add_argument("--session", "-s", help="会话ID")
    p_audit.add_argument("--file", "-f", help="文件路径")
    p_audit.add_argument("--status", help="问题状态过滤 (OPEN/RESOLVED)")
    p_audit.add_argument("--severity", help="严重级别过滤 (P0/P1/P2)")
    p_audit.add_argument("--category", "-c", help="学习经验类别")
    p_audit.add_argument("--format", choices=["markdown", "md", "json"], help="报告格式")
    p_audit.set_defaults(func=cmd_audit)

    # ==================== 文档导入命令 ====================

    # import 命令
    p_import = subparsers.add_parser(
        "import",
        help="Import documents from PALs/ directory",
        usage="qka import [pals_dir] [options]",
    )
    p_import.add_argument(
        "pals_dir",
        nargs="?",
        default="PALs",
        help="PALs directory path (default: PALs)",
    )
    p_import.add_argument(
        "--with-source",
        "-s",
        action="store_true",
        help="Include source code from SourceReference/",
    )
    p_import.add_argument("--output", "-o", help="Output directory (default: Docs/PALs)")
    p_import.add_argument("--dry-run", "-d", action="store_true", help="Preview files without processing")
    p_import.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    p_import.add_argument("--no-validate", action="store_true", help="Skip Layer 2 cross-validation")
    p_import.add_argument("--no-knowledge", action="store_true", help="Skip Layer 3 knowledge extraction")
    p_import.set_defaults(func=cmd_import)

    # ==================== 模型管理命令 ====================

    # models 命令
    p_models = subparsers.add_parser("models", help="模型配置管理")
    p_models.add_argument(
        "action",
        choices=[
            "show",
            "list",
            "check-updates",
            "upgrade",
            "strategy",
            "lock",
            "unlock",
        ],
        help="操作",
    )
    p_models.add_argument("--agent", "-a", help="查看特定Agent的模型")
    p_models.add_argument("--target", help="升级目标版本")
    p_models.add_argument("--dry-run", "-d", action="store_true", help="预览变更")
    p_models.add_argument("--force", "-f", action="store_true", help="强制执行")
    p_models.add_argument("--strategy-name", dest="strategy_name", help="策略名称")
    p_models.add_argument("--model", dest="model_name", help="模型名称")
    p_models.add_argument("model_name", nargs="?", help="模型名称")
    p_models.set_defaults(func=cmd_models)

    # ==================== 版本与升级命令 ====================

    # version 命令
    p_version = subparsers.add_parser("version", help="查看版本信息")
    p_version.add_argument("--check", "-c", action="store_true", help="检查所有模块完整性")
    p_version.set_defaults(func=cmd_version)

    # update 命令
    p_update = subparsers.add_parser("update", help="升级QuickAgents")
    p_update.add_argument(
        "--source",
        "-s",
        choices=["pypi", "github"],
        default="pypi",
        help="安装源 (pypi/github, 默认pypi)",
    )
    p_update.add_argument("--target", "-t", help="指定目标版本 (如 2.7.5)")
    p_update.add_argument("--dry-run", "-d", action="store_true", help="仅预览，不执行升级")
    p_update.set_defaults(func=cmd_update)

    # uninstall 命令
    p_uninstall = subparsers.add_parser("uninstall", help="卸载当前项目的QuickAgents文件（项目级）")
    p_uninstall.add_argument("--dry-run", "-d", action="store_true", help="仅预览，不执行卸载")
    p_uninstall.add_argument("--keep-data", action="store_true", help="保留 .quickagents/ 目录")
    p_uninstall.add_argument("--keep-opencode", action="store_true", help="保留 .opencode/ 目录")
    p_uninstall.add_argument("--force", "-f", action="store_true", help="跳过确认提示")
    p_uninstall.set_defaults(func=cmd_uninstall)

    # export 命令
    p_export = subparsers.add_parser("export", help="导出干净的项目文件（排除QA运行时）")
    p_export.add_argument(
        "--output",
        "-o",
        default="Output",
        help="输出根目录（默认: Output，实际输出到 Output/<版本号>/）",
    )
    p_export.add_argument(
        "--version",
        "-v",
        help="指定版本号（默认自动检测 pyproject.toml/package.json/git tag）",
    )
    p_export.add_argument("--dry-run", "-d", action="store_true", help="仅预览，不执行导出")
    p_export.add_argument("--list-excludes", action="store_true", help="列出所有排除规则")
    p_export.add_argument("--inject-gitignore", action="store_true", help="将排除规则注入 .gitignore")
    p_export.set_defaults(func=cmd_export)

    # ==================== 愚公循环命令 ====================

    # init 命令
    p_init = subparsers.add_parser("init", help="初始化QuickAgents到当前项目")
    p_init.add_argument("project_dir", nargs="?", help="项目目录（默认当前目录）")
    p_init.add_argument("--force", "-f", action="store_true", help="覆盖现有文件")
    p_init.add_argument("--dry-run", "-d", action="store_true", help="预览模式，不执行实际操作")
    p_init.add_argument("--minimal", "-m", action="store_true", help="最小安装（仅核心文件）")
    p_init.add_argument("--with-ui-ux", action="store_true", help="包含ui-ux-pro-max技能（~410KB）")
    p_init.add_argument("--with-browser", action="store_true", help="包含browser-devtools技能")
    p_init.add_argument("--update-config", action="store_true", help="仅更新配置文件")
    p_init.set_defaults(func=cmd_init)

    # yugong 命令
    p_yugong = subparsers.add_parser("yugong", help="愚公循环 - 自主开发循环")
    p_yugong.add_argument(
        "action",
        choices=["start", "status", "parse", "config", "report", "resume"],
        help="操作: start=启动循环, status=查看状态, parse=解析需求, config=查看配置, report=生成报告, resume=恢复执行",
    )
    p_yugong.add_argument("file", nargs="?", help="需求文件路径 (JSON/Markdown)")
    p_yugong.add_argument(
        "--mode", "-m", choices=["default", "conservative", "aggressive"], default="default", help="配置模式"
    )
    p_yugong.add_argument("--max-iterations", "-i", type=int, help="最大迭代次数")
    p_yugong.add_argument("--dry-run", "-d", action="store_true", help="仅预览,不执行")
    p_yugong.add_argument(
        "--provider", "-p", choices=["zhipuai", "openai"], default="zhipuai", help="LLM Provider (默认: zhipuai)"
    )
    p_yugong.add_argument("--max-turns", "-t", type=int, default=15, help="单次执行最大对话轮次 (默认: 15)")
    p_yugong.add_argument("--db-path", "-b", type=str, default=".quickagents/yugong.db", help="数据库路径")
    p_yugong.add_argument("--report-dir", "-o", type=str, default=".quickagents/reports", help="报告输出目录")
    p_yugong.set_defaults(func=cmd_yugong)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
