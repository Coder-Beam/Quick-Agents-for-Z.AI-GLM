"""
QuickAgents CLI - 命令行工具

命令:
    qa read <file>           # 智能读取文件（哈希检测）
    qa write <file> <content> # 写入文件
    qa edit <file> <old> <new> # 编辑文件
    qa hash <file>           # 获取文件哈希
    qa cache stats           # 查看缓存统计
    qa cache clear           # 清空缓存
    qa memory get <key>      # 获取记忆
    qa memory set <key> <val> # 设置记忆
    qa memory search <keyword> # 搜索记忆
    qa loop check            # 检查循环模式
    qa loop reset            # 重置循环检测
    qa stats                 # 查看整体统计
    qa sync [table]          # 同步SQLite到Markdown
    
    # 模型配置命令
    qa models status         # 查看当前模型配置
    qa models check          # 检查GLM版本更新
    qa models upgrade [version] # 升级GLM模型
    qa models rollback       # 回滚到上一版本
    
    # 自我进化系统命令
    qa evolution status      # 进化系统状态
    qa evolution stats [skill] # Skills使用统计
    qa evolution optimize    # 执行定期优化
    qa evolution history <skill> # 查看Skill进化历史
    qa evolution sync        # 同步到Markdown
    
    # Git钩子命令
    qa hooks install         # 安装Git钩子
    qa hooks uninstall       # 卸载Git钩子
    qa hooks status          # 钩子状态
    
    # Skills本地化命令
    qa feedback bug <desc>   # 记录Bug
    qa feedback improve <desc> # 记录改进建议
    qa feedback best <desc>  # 记录最佳实践
    qa feedback view [type]  # 查看收集的经验
    
    qa tdd red [test_file]   # RED阶段：运行测试（应失败）
    qa tdd green [test_file] # GREEN阶段：运行测试（应通过）
    qa tdd refactor [test_file] # REFACTOR阶段
    qa tdd stats             # TDD统计
    qa tdd coverage          # 检查覆盖率
    
    qa git status            # Git状态
    qa git check             # Pre-commit检查
    qa git commit <type> <scope> <subject> # 执行提交
    qa git push              # 推送到远程
"""

import sys
import os
import argparse
from pathlib import Path

from ..core.file_manager import FileManager
from ..core.memory import MemoryManager
from ..core.loop_detector import LoopDetector
from ..core.reminder import Reminder
from ..core.cache_db import CacheDB
from ..core.unified_db import UnifiedDB, MemoryType, TaskStatus, FeedbackType
from ..core.markdown_sync import MarkdownSync
from ..core.evolution import SkillEvolution, EvolutionTrigger, get_evolution
from ..core.git_hooks import GitHooks
from ..skills.feedback_collector import FeedbackCollector
from ..skills.tdd_workflow import TDDWorkflow, TDDPhase
from ..skills.git_commit import GitCommit
from ..utils.encoding import read_file_utf8, write_file_utf8


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
    
    if result['success']:
        print(f"[OK] 编辑成功: {args.file}")
        if result['token_saved'] > 0:
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
    
    if args.action == 'stats':
        stats = db.get_stats()['file_cache']
        print("[Cache] 缓存统计")
        print(f"  缓存文件数: {stats['count']}")
        print(f"  总大小: {stats['total_kb']} KB")
    
    elif args.action == 'clear':
        count = db.clear_file_cache()
        print(f"[OK] 已清空 {count} 个文件缓存")
    
    elif args.action == 'list':
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT path, content_hash, size, access_count FROM file_cache')
            rows = cursor.fetchall()
            
            print("[Cache] 缓存文件列表")
            print("-" * 80)
            for row in rows:
                print(f"  {row['path']}")
                print(f"    哈希: {row['content_hash']}, 大小: {row['size']}B, 访问: {row['access_count']}次")


def cmd_memory(args):
    """记忆管理命令"""
    memory = MemoryManager()
    
    if args.action == 'get':
        value = memory.get(args.key)
        if value is not None:
            print(f"{args.key}: {value}")
        else:
            print(f"[FAIL] 未找到: {args.key}")
    
    elif args.action == 'set':
        memory.set_factual(args.key, args.value)
        memory.save()
        print(f"[OK] 已设置: {args.key} = {args.value}")
    
    elif args.action == 'search':
        results = memory.search(args.keyword)
        print(f"[Search] 搜索结果 ({len(results)} 条)")
        print("-" * 50)
        for r in results:
            print(f"  [{r['type']}] {r.get('key', r.get('category', ''))}: {r.get('value', r.get('content', ''))}")


def cmd_loop(args):
    """循环检测命令"""
    detector = LoopDetector()
    
    if args.action == 'check':
        patterns = detector.get_loop_patterns()
        if patterns:
            print("[WARN] 检测到循环模式")
            print("-" * 50)
            for p in patterns:
                print(f"  {p['tool_name']}: {p['count']}次")
                print(f"    首次: {p['first_seen']}")
                print(f"    最后: {p['last_seen']}")
        else:
            print("[OK] 未检测到循环模式")
    
    elif args.action == 'reset':
        detector.reset()
        print("[OK] 已重置循环检测")
    
    elif args.action == 'stats':
        stats = detector.get_stats()
        print("[Loop] 循环检测统计")
        print(f"  检测阈值: {stats['threshold']}")
        print(f"  窗口大小: {stats['window_size']}")
        print(f"  循环模式: {stats['total_patterns']}")


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
    db_path = '.quickagents/unified.db'
    
    if not os.path.exists(db_path):
        print(f"[FAIL] 数据库不存在: {db_path}")
        print("  请先使用UnifiedDB创建数据库")
        return
    
    db = UnifiedDB(db_path)
    sync = MarkdownSync(db)
    
    table = args.table if hasattr(args, 'table') and args.table else None
    
    if table == 'memory' or table is None:
        sync.sync_memory()
        print("[OK] 已同步 memory -> Docs/MEMORY.md")
    
    if table == 'tasks' or table is None:
        sync.sync_tasks()
        print("[OK] 已同步 tasks -> Docs/TASKS.md")
    
    if table == 'decisions' or table is None:
        sync.sync_decisions()
        print("[OK] 已同步 decisions -> Docs/DECISIONS.md")
    
    if table == 'progress' or table is None:
        sync.sync_progress()
        print("[OK] 已同步 progress -> .quickagents/boulder.json")
    
    if table == 'feedback' or table is None:
        sync.sync_feedback()
        print("[OK] 已同步 feedback -> ~/.quickagents/feedback/")
    
    if table is None:
        print("\n[Done] 所有表同步完成")


def cmd_reminder(args):
    """提醒系统命令"""
    reminder = Reminder()
    
    if args.action == 'check':
        alerts = reminder.check_alerts()
        if alerts:
            print("[WARN] 活跃提醒")
            print("-" * 50)
            for a in alerts:
                print(f"  [{a['level']}] {a['message']}")
        else:
            print("[OK] 无活跃提醒")
    
    elif args.action == 'stats':
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
    
    if args.action == 'bug':
        success = collector.record('bug', args.description, scenario=args.scenario)
        if success:
            print(f"[OK] 已记录Bug: {args.description}")
        else:
            print("[INFO] 重复记录已忽略")
    
    elif args.action == 'improve':
        success = collector.record('improve', args.description, scenario=args.scenario)
        if success:
            print(f"[OK] 已记录改进建议: {args.description}")
        else:
            print("[INFO] 重复记录已忽略")
    
    elif args.action == 'best':
        success = collector.record('best', args.description, scenario=args.scenario)
        if success:
            print(f"[OK] 已记录最佳实践: {args.description}")
        else:
            print("[INFO] 重复记录已忽略")
    
    elif args.action == 'view':
        feedback_type = args.type if hasattr(args, 'type') and args.type else None
        feedbacks = collector.get_feedback(feedback_type, limit=20)
        
        print(f"[Feedback] 经验收集 ({len(feedbacks)} 条)")
        print("-" * 50)
        for fb in feedbacks:
            print(f"  [{fb['type']}] {fb['timestamp']}")
            print(f"    {fb['description'][:50]}...")
    
    elif args.action == 'stats':
        stats = collector.get_stats()
        print("[Feedback] 经验收集统计")
        print(f"  总计: {stats['total']} 条")
        for ftype, count in stats['by_type'].items():
            print(f"  {ftype}: {count} 条")


def cmd_tdd(args):
    """TDD工作流命令"""
    tdd = TDDWorkflow()
    
    if args.action == 'red':
        result = tdd.run_red(args.test_file)
        print(f"[RED] RED阶段: {'测试失败 [OK]' if not result['passed'] else '测试通过 [WARN]'}")
        print(f"  耗时: {result['duration_ms']}ms")
        if result['passed']:
            print("  [WARN] 测试已通过，需要先写失败的测试！")
    
    elif args.action == 'green':
        result = tdd.run_green(args.test_file)
        print(f"[GREEN] GREEN阶段: {'测试通过 [OK]' if result['passed'] else '测试失败 [FAIL]'}")
        print(f"  耗时: {result['duration_ms']}ms")
        if result['passed']:
            print("  [OK] 可以进入Refactor阶段")
    
    elif args.action == 'refactor':
        result = tdd.run_refactor(args.test_file)
        print(f"[REFACTOR] REFACTOR阶段: {'测试通过 [OK]' if result['passed'] else '测试失败 [FAIL]'}")
        print(f"  耗时: {result['duration_ms']}ms")
    
    elif args.action == 'stats':
        stats = tdd.get_stats()
        print("[TDD] TDD统计")
        print(f"  RED次数: {stats['red_count']}")
        print(f"  GREEN次数: {stats['green_count']}")
        print(f"  REFACTOR次数: {stats['refactor_count']}")
        print(f"  测试命令: {stats['test_command']}")
    
    elif args.action == 'coverage':
        result = tdd.check_coverage(threshold=80)
        print(f"[Coverage] 测试覆盖率: {result['coverage']}%")
        print(f"  达标: {'[OK]' if result['meets_threshold'] else '[FAIL]'}")


def cmd_git(args):
    """Git提交命令"""
    git = GitCommit()
    
    if args.action == 'status':
        status = git.get_status()
        print(f"[Git] 分支: {status['branch']}")
        print(f"  领先: {status['ahead']}, 落后: {status['behind']}")
        
        if status['staged']:
            print(f"\n[Staged] 已暂存 ({len(status['staged'])})")
            for f in status['staged'][:5]:
                print(f"  {f}")
        
        if status['unstaged']:
            print(f"\n[Unstaged] 未暂存 ({len(status['unstaged'])})")
            for f in status['unstaged'][:5]:
                print(f"  {f}")
        
        if status['untracked']:
            print(f"\n[Untracked] 未跟踪 ({len(status['untracked'])})")
            for f in status['untracked'][:5]:
                print(f"  {f}")
    
    elif args.action == 'check':
        print("[Git] 执行Pre-commit检查...")
        checks = git.run_pre_commit_checks()
        
        print(f"\n{'[OK]' if checks['all_passed'] else '[FAIL]'} 检查结果")
        for check_name, result in checks['checks'].items():
            status = '[OK]' if result['passed'] else ('[SKIP]' if result.get('skipped') else '[FAIL]')
            print(f"  {status} {check_name}")
    
    elif args.action == 'commit':
        print("[Git] 执行Pre-commit检查...")
        result = git.commit(
            args.type, args.scope, args.subject,
            run_checks=True
        )
        
        if result['success']:
            print(f"[OK] 提交成功: {result['commit_hash']}")
            print(f"   {result['message'].split(chr(10))[0]}")
        else:
            print(f"[FAIL] 提交失败: {result['message']}")
    
    elif args.action == 'push':
        result = git.push()
        if result['success']:
            print("[OK] 推送成功")
        else:
            print(f"[FAIL] 推送失败: {result['message']}")


# ==================== 自我进化系统命令 ====================

def cmd_evolution(args):
    """自我进化系统命令"""
    db_path = '.quickagents/unified.db'
    
    if not os.path.exists(db_path):
        print(f"[FAIL] 数据库不存在: {db_path}")
        print("  请先使用UnifiedDB创建数据库")
        return
    
    db = UnifiedDB(db_path)
    evolution = SkillEvolution(db)
    
    if args.action == 'status':
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
    
    elif args.action == 'stats':
        skill_name = args.skill if hasattr(args, 'skill') and args.skill else None
        
        if skill_name:
            # 单个Skill统计
            stats = evolution.get_skill_stats(skill_name)
            print(f"[Evolution] {skill_name} 统计")
            print("=" * 50)
            print(f"  总使用次数: {stats['total_usage']}")
            print(f"  成功次数: {stats['success_count']}")
            print(f"  失败次数: {stats['failure_count']}")
            print(f"  成功率: {stats['success_rate']:.1%}")
            if stats['avg_duration_ms']:
                print(f"  平均耗时: {stats['avg_duration_ms']:.0f}ms")
            
            if stats['recent_errors']:
                print("\n[Recent Errors]")
                for err in stats['recent_errors'][:3]:
                    print(f"  - {err['error_message'][:50]}...")
        else:
            # 所有Skills统计
            all_stats = evolution.get_all_skills_stats()
            print(f"[Evolution] 所有Skills统计 ({len(all_stats)} 个)")
            print("=" * 50)
            
            for skill, stats in sorted(all_stats.items(), key=lambda x: x[1]['count'], reverse=True):
                rate = stats['success_rate']
                status = '[OK]' if rate >= 0.8 else ('[WARN]' if rate >= 0.6 else '[FAIL]')
                print(f"  {status} {skill}: {stats['count']}次, 成功率 {rate:.0%}")
    
    elif args.action == 'optimize':
        print("[Evolution] 执行定期优化...")
        result = evolution.run_periodic_optimization()
        
        print(f"\n[OK] 优化完成")
        print(f"  审查Skills: {len(result['skills_reviewed'])}")
        
        if result['skills_to_update']:
            print(f"\n[WARN] 需要改进的Skills:")
            for skill in result['skills_to_update']:
                print(f"  - {skill}")
    
    elif args.action == 'history':
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
    
    elif args.action == 'sync':
        print("[Evolution] 同步到Markdown...")
        result = evolution.sync_to_markdown()
        
        print(f"[OK] 已同步 {result['skills_synced']} 个Skills")
        for f in result['files_created'][:5]:
            print(f"  - {f}")


def cmd_hooks(args):
    """Git钩子命令"""
    hooks = GitHooks()
    
    if args.action == 'install':
        print("[Hooks] 安装Git钩子...")
        result = hooks.install()
        
        if 'error' in result:
            print(f"[FAIL] {result['error']}")
        else:
            print("[OK] Git钩子已安装")
            for hook, success in result.items():
                print(f"  - {hook}: {'成功' if success else '失败'}")
    
    elif args.action == 'uninstall':
        print("[Hooks] 卸载Git钩子...")
        result = hooks.uninstall()
        
        print("[OK] Git钩子已卸载")
        for hook, success in result.items():
            print(f"  - {hook}: {'成功' if success else '失败'}")
    
    elif args.action == 'status':
        status = hooks.get_status()
        print("[Hooks] Git钩子状态")
        print("=" * 50)
        print(f"  是Git仓库: {'是' if status['is_git_repo'] else '否'}")
        print(f"  post-commit: {'已安装' if status['post_commit_installed'] else '未安装'}")
        if status['post_commit_has_backup']:
            print("  存在备份: 是")


# ==================== 模型管理命令 ====================

def cmd_models(args):
    """模型管理命令"""
    import json
    from pathlib import Path
    
    models_json_path = Path('.opencode/config/models.json')
    
    if not models_json_path.exists():
        print(f"[FAIL] 配置文件不存在: {models_json_path}")
        return
    
    from ..utils.encoding import read_file_utf8
    config = json.loads(read_file_utf8(str(models_json_path)))
    
    if args.action == 'show' or args.action == 'status':
        print("[Models] 当前模型配置")
        print("=" * 50)
        print(f"  版本: {config.get('version', 'unknown')}")
        print(f"  策略: {config.get('strategy', 'unknown')}")
        print(f"  主模型: {config.get('default', {}).get('primary', 'unknown')}")
        print(f"  备用模型: {config.get('default', {}).get('fallback', 'unknown')}")
        
        # 显示 Coding Plan 信息
        if 'codingPlanConfig' in config:
            print("\n[Coding Plan]")
            mapping = config['codingPlanConfig'].get('claudeCodeMapping', {})
            print(f"  Claude Opus -> {mapping.get('opus', 'N/A')}")
            print(f"  Claude Sonnet -> {mapping.get('sonnet', 'N/A')}")
            print(f"  Claude Haiku -> {mapping.get('haiku', 'N/A')}")
        
        # 显示 Agent 映射
        if args.agent:
            agent_map = config.get('agentMapping', {})
            categories = config.get('categories', {})
            
            if args.agent in agent_map:
                category = agent_map[args.agent]
                model = categories.get(category, 'unknown')
                print(f"\n[Agent] {args.agent}")
                print(f"  类别: {category}")
                print(f"  模型: {model}")
            else:
                print(f"\n[FAIL] Agent '{args.agent}' 未找到")
    
    elif args.action == 'list':
        print("[Models] 可用模型列表")
        print("=" * 50)
        
        providers = config.get('providers', {})
        for provider_name, provider in providers.items():
            print(f"\n[{provider.get('displayName', provider_name)}]")
            models = provider.get('models', {})
            for model_id, model_info in models.items():
                recommended = ' (推荐)' if model_info.get('recommended') else ''
                reasoning = ' [推理]' if model_info.get('reasoning') else ''
                print(f"  - {model_id}{recommended}{reasoning}")
                if model_info.get('description'):
                    print(f"    {model_info['description']}")
    
    elif args.action == 'check-updates':
        print("[Models] 检查 GLM 模型更新...")
        print("=" * 50)
        
        version_config = config.get('versionUpgrade', {})
        check_url = version_config.get('checkUrl', 'https://docs.bigmodel.cn/llms.txt')
        upgrade_path = version_config.get('upgradePath', {})
        
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
                content = response.read().decode('utf-8')
                print(f"\n[OK] 成功获取远程模型信息 ({len(content)} bytes)")
        except Exception as e:
            print(f"\n[WARN] 无法获取远程信息: {e}")
            print("  请手动访问 https://docs.bigmodel.cn/llms.txt 查看")
    
    elif args.action == 'upgrade':
        print("[Models] 模型升级")
        print("=" * 50)
        
        version_config = config.get('versionUpgrade', {})
        upgrade_path = version_config.get('upgradePath', {})
        
        current_primary = config.get('default', {}).get('primary', '')
        
        if args.target:
            target = args.target
        else:
            target = upgrade_path.get(current_primary, '')
        
        if not target:
            print(f"[FAIL] 未找到 {current_primary} 的升级路径")
            print("  使用: qa models upgrade --to GLM-5.1")
            return
        
        print(f"  当前: {current_primary}")
        print(f"  目标: {target}")
        
        if args.dry_run:
            print("\n[DRY-RUN] 预览变更:")
            print(f"  - default.primary: {current_primary} -> {target}")
            
            categories = config.get('categories', {})
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
            backup_path = Path(f'.quickagents/backups/models_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(models_json_path, backup_path)
            print(f"\n[OK] 备份已创建: {backup_path}")
            
            # 执行升级
            if config['default']['primary'] == current_primary:
                config['default']['primary'] = target
            
            for cat, model in config.get('categories', {}).items():
                if model == current_primary:
                    config['categories'][cat] = target
            
            write_file_utf8(str(models_json_path), json.dumps(config, indent=2, ensure_ascii=False))
            
            print(f"[OK] 升级完成: {current_primary} -> {target}")
    
    elif args.action == 'strategy':
        print("[Models] 切换模型策略")
        print("=" * 50)
        
        strategy = args.strategy_name
        print(f"  目标策略: {strategy}")
        
        if strategy not in ['coding-plan', 'single-model', 'hybrid']:
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
        
        config['strategy'] = strategy
        
        if strategy == 'single-model' and args.model:
            config['lockModel'] = args.model
            config['default']['primary'] = args.model
        
        write_file_utf8(str(models_json_path), json.dumps(config, indent=2, ensure_ascii=False))
        
        print(f"[OK] 策略已切换: {strategy}")
    
    elif args.action == 'lock':
        model = args.model_name
        print(f"[Models] 锁定模型: {model}")
        
        if args.dry_run:
            print(f"\n[DRY-RUN] 将锁定所有 Agent 使用: {model}")
            return
        
        if not args.force:
            print("\n[WARN] 需要确认")
            print("  使用 --force 执行锁定")
            return
        
        config['lockModel'] = model
        config['default']['primary'] = model
        
        write_file_utf8(str(models_json_path), json.dumps(config, indent=2, ensure_ascii=False))
        
        print(f"[OK] 已锁定模型: {model}")
    
    elif args.action == 'unlock':
        print("[Models] 解除模型锁定")
        
        config['lockModel'] = None
        
        write_file_utf8(str(models_json_path), json.dumps(config, indent=2, ensure_ascii=False))
        
        print("[OK] 已解除锁定")


def main():
    parser = argparse.ArgumentParser(description='QuickAgents CLI')
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # read 命令
    p_read = subparsers.add_parser('read', help='读取文件')
    p_read.add_argument('file', help='文件路径')
    p_read.set_defaults(func=cmd_read)
    
    # write 命令
    p_write = subparsers.add_parser('write', help='写入文件')
    p_write.add_argument('file', help='文件路径')
    p_write.add_argument('content', help='写入内容')
    p_write.set_defaults(func=cmd_write)
    
    # edit 命令
    p_edit = subparsers.add_parser('edit', help='编辑文件')
    p_edit.add_argument('file', help='文件路径')
    p_edit.add_argument('old', help='要替换的内容')
    p_edit.add_argument('new', help='替换后的内容')
    p_edit.set_defaults(func=cmd_edit)
    
    # hash 命令
    p_hash = subparsers.add_parser('hash', help='获取文件哈希')
    p_hash.add_argument('file', help='文件路径')
    p_hash.set_defaults(func=cmd_hash)
    
    # cache 命令
    p_cache = subparsers.add_parser('cache', help='缓存管理')
    p_cache.add_argument('action', choices=['stats', 'clear', 'list'], help='操作')
    p_cache.set_defaults(func=cmd_cache)
    
    # memory 命令
    p_memory = subparsers.add_parser('memory', help='记忆管理')
    p_memory.add_argument('action', choices=['get', 'set', 'search'], help='操作')
    p_memory.add_argument('key', nargs='?', help='键名')
    p_memory.add_argument('value', nargs='?', help='值')
    p_memory.add_argument('--keyword', '-k', help='搜索关键词')
    p_memory.set_defaults(func=cmd_memory)
    
    # loop 命令
    p_loop = subparsers.add_parser('loop', help='循环检测')
    p_loop.add_argument('action', choices=['check', 'reset', 'stats'], help='操作')
    p_loop.set_defaults(func=cmd_loop)
    
    # stats 命令
    p_stats = subparsers.add_parser('stats', help='查看统计')
    p_stats.set_defaults(func=cmd_stats)
    
    # sync 命令
    p_sync = subparsers.add_parser('sync', help='同步SQLite到Markdown')
    p_sync.add_argument('table', nargs='?', choices=['memory', 'tasks', 'decisions', 'progress', 'feedback'], 
                        help='要同步的表（默认全部）')
    p_sync.set_defaults(func=cmd_sync)
    
    # reminder 命令
    p_reminder = subparsers.add_parser('reminder', help='提醒系统')
    p_reminder.add_argument('action', choices=['check', 'stats'], help='操作')
    p_reminder.set_defaults(func=cmd_reminder)
    
    # ==================== 新增命令 ====================
    
    # feedback 命令
    p_feedback = subparsers.add_parser('feedback', help='经验收集')
    p_feedback.add_argument('action', choices=['bug', 'improve', 'best', 'view', 'stats'], help='操作')
    p_feedback.add_argument('description', nargs='?', help='描述')
    p_feedback.add_argument('--scenario', '-s', help='场景上下文')
    p_feedback.add_argument('--type', '-t', help='反馈类型（view时使用）')
    p_feedback.set_defaults(func=cmd_feedback)
    
    # tdd 命令
    p_tdd = subparsers.add_parser('tdd', help='TDD工作流')
    p_tdd.add_argument('action', choices=['red', 'green', 'refactor', 'stats', 'coverage'], help='操作')
    p_tdd.add_argument('test_file', nargs='?', help='测试文件')
    p_tdd.set_defaults(func=cmd_tdd)
    
    # git 命令
    p_git = subparsers.add_parser('git', help='Git提交管理')
    p_git.add_argument('action', choices=['status', 'check', 'commit', 'push'], help='操作')
    p_git.add_argument('commit_type', nargs='?', help='提交类型')
    p_git.add_argument('scope', nargs='?', help='范围')
    p_git.add_argument('subject', nargs='?', help='主题')
    p_git.set_defaults(func=cmd_git)
    
    # ==================== 自我进化系统命令 ====================
    
    # evolution 命令
    p_evolution = subparsers.add_parser('evolution', help='自我进化系统')
    p_evolution.add_argument('action', choices=['status', 'stats', 'optimize', 'history', 'sync'], help='操作')
    p_evolution.add_argument('skill', nargs='?', help='Skill名称')
    p_evolution.set_defaults(func=cmd_evolution)
    
    # hooks 命令
    p_hooks = subparsers.add_parser('hooks', help='Git钩子管理')
    p_hooks.add_argument('action', choices=['install', 'uninstall', 'status'], help='操作')
    p_hooks.set_defaults(func=cmd_hooks)
    
 # ==================== 模型管理命令 ====================
    # models 命令
    p_models.add_argument('action', choices=['show', 'list', 'check-updates', 'upgrade', 'strategy', 'lock', 'unlock'], help='操作')
    p_models.add_argument('--agent', '-a', help='查看特定Agent的模型')
    p_models.add_argument('--target', help='升级目标版本')
    p_models.add_argument('--dry-run', '-d', action='store_true', help='预览变更')
    p_models.add_argument('--force', '-f', action='store_true', help='强制执行')
    p_models.add_argument('--strategy-name', dest='strategy_name', help='策略名称')
    p_models.add_argument('--model', dest='model_name', help='模型名称')
    p_models.add_argument('model_name', nargs='?', help='模型名称')
    p_models.set_defaults(func=cmd_models)


if __name__ == '__main__':
    main()
