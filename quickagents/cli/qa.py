#!/usr/bin/env python3
"""
QuickAgents CLI Entry Point

Usage:
    qa <command> [args]

Commands:
    read <file>           # 智能读取文件（哈希检测）
    write <file> <content> # 写入文件
    edit <file> <old> <new> # 编辑文件
    hash <file>           # 获取文件哈希
    cache stats           # 查看缓存统计
    cache clear           # 清空缓存
    memory get <key>      # 获取记忆
    memory set <key> <val> # 设置记忆
    loop check            # 检查循环模式
    stats                 # 查看整体统计
"""

import sys
import os

# 添加包路径
script_dir = os.path.dirname(os.path.abspath(__file__))
package_dir = os.path.dirname(script_dir)
if package_dir not in sys.path:
    sys.path.insert(0, package_dir)

from quickagents.cli.main import main

if __name__ == '__main__':
    main()
