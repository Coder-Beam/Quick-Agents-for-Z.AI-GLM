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
"""

import sys
import os
import argparse
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.file_manager import FileManager
from core.memory import MemoryManager
from core.loop_detector import LoopDetector
from core.reminder import Reminder
from core.cache_db import CacheDB


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
    print(f"✅ 已写入: {args.file}")


def cmd_edit(args):
    """编辑文件命令"""
    fm = FileManager()
    result = fm.edit(args.file, args.old, args.new)
    
    if result['success']:
        print(f"✅ 编辑成功: {args.file}")
        if result['token_saved'] > 0:
            print(f"💰 节省Token: ~{result['token_saved']}")
    else:
        print(f"❌ 编辑失败: {result['message']}")


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
        print("📊 缓存统计")
        print(f"  缓存文件数: {stats['count']}")
        print(f"  总大小: {stats['total_kb']} KB")
    
    elif args.action == 'clear':
        count = db.clear_file_cache()
        print(f"✅ 已清空 {count} 个文件缓存")
    
    elif args.action == 'list':
        # 列出所有缓存文件
        with db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT path, content_hash, size, access_count FROM file_cache')
            rows = cursor.fetchall()
            
            print("📁 缓存文件列表")
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
            print(f"❌ 未找到: {args.key}")
    
    elif args.action == 'set':
        memory.set_factual(args.key, args.value)
        memory.save()
        print(f"✅ 已设置: {args.key} = {args.value}")
    
    elif args.action == 'search':
        results = memory.search(args.keyword)
        print(f"🔍 搜索结果 ({len(results)} 条)")
        print("-" * 50)
        for r in results:
            print(f"  [{r['type']}] {r.get('key', r.get('category', ''))}: {r.get('value', r.get('content', ''))}")


def cmd_loop(args):
    """循环检测命令"""
    detector = LoopDetector()
    
    if args.action == 'check':
        patterns = detector.get_loop_patterns()
        if patterns:
            print("⚠️ 检测到循环模式")
            print("-" * 50)
            for p in patterns:
                print(f"  {p['tool_name']}: {p['count']}次")
                print(f"    首次: {p['first_seen']}")
                print(f"    最后: {p['last_seen']}")
        else:
            print("✅ 未检测到循环模式")
    
    elif args.action == 'reset':
        detector.reset()
        print("✅ 已重置循环检测")
    
    elif args.action == 'stats':
        stats = detector.get_stats()
        print("📊 循环检测统计")
        print(f"  检测阈值: {stats['threshold']}")
        print(f"  窗口大小: {stats['window_size']}")
        print(f"  循环模式: {stats['total_patterns']}")


def cmd_stats(args):
    """查看整体统计"""
    db = CacheDB()
    stats = db.get_stats()
    
    print("📊 QuickAgents 统计")
    print("=" * 50)
    
    print("\n📁 文件缓存")
    print(f"  缓存文件: {stats['file_cache']['count']}")
    print(f"  总大小: {stats['file_cache']['total_kb']} KB")
    
    print("\n🧠 记忆系统")
    print(f"  记忆条目: {stats['memory']['count']}")
    
    print("\n💰 Token节省")
    print(f"  估算节省: {stats['tokens']['total_saved']} tokens")


def cmd_reminder(args):
    """提醒系统命令"""
    reminder = Reminder()
    
    if args.action == 'check':
        alerts = reminder.check_alerts()
        if alerts:
            print("⚠️ 活跃提醒")
            print("-" * 50)
            for a in alerts:
                print(f"  [{a['level']}] {a['message']}")
        else:
            print("✅ 无活跃提醒")
    
    elif args.action == 'stats':
        stats = reminder.get_stats()
        print("📊 提醒系统统计")
        print(f"  工具调用: {stats['tool_calls']}")
        print(f"  错误次数: {stats['errors']}")
        print(f"  运行时间: {int(stats['elapsed_minutes'])} 分钟")
        print(f"  上下文使用: {stats['context_usage']}%")


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
    
    # reminder 命令
    p_reminder = subparsers.add_parser('reminder', help='提醒系统')
    p_reminder.add_argument('action', choices=['check', 'stats'], help='操作')
    p_reminder.set_defaults(func=cmd_reminder)
    
    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
