#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MemoryManager 综合测试脚本"""

from quickagents.core.memory import MemoryManager
import os
import tempfile
import shutil

def test_memory_manager():
    """测试 MemoryManager 核心功能"""
    # 创建测试目录
    test_dir = tempfile.mkdtemp()
    memory_path = os.path.join(test_dir, 'MEMORY.md')
    
    print('=' * 60)
    print('[TEST 1] MemoryManager Initialization')
    print('=' * 60)
    
    memory = MemoryManager(memory_path)
    print('[OK] MemoryManager created:', memory_path)
    print('[OK] Initial state - loaded:', memory._loaded)
    
    # Test 2: Factual Memory
    print()
    print('=' * 60)
    print('[TEST 2] Factual Memory Test')
    print('=' * 60)
    
    memory.set_factual('project.name', 'QuickAgents')
    memory.set_factual('project.version', '1.0.0')
    memory.set_factual('project.tech_stack', ['Python', 'TypeScript'])
    memory.set_factual('author', 'TestUser')
    print('[OK] Factual memory set')
    
    name = memory.get('project.name')
    version = memory.get('project.version')
    tech = memory.get('project.tech_stack')
    author = memory.get('author')
    print('[OK] Get factual: name={}, version={}, tech={}, author={}'.format(
        name, version, tech, author))
    
    # Test nested key
    nested = memory.get('project')
    print('[OK] Get nested key "project":', nested)
    
    # Test 3: Working Memory
    print()
    print('=' * 60)
    print('[TEST 3] Working Memory Test')
    print('=' * 60)
    
    memory.set_working('current_task', 'Testing MemoryManager')
    memory.set_working('progress', '30%')
    memory.set_working('blockers', 'None')
    print('[OK] Working memory set')
    
    task = memory.get('current_task')
    progress = memory.get('progress')
    blockers = memory.get('blockers')
    print('[OK] Get working: task={}, progress={}, blockers={}'.format(
        task, progress, blockers))
    
    # Test priority: working memory should be checked first
    memory.set_factual('test_key', 'factual_value')
    memory.set_working('test_key', 'working_value')
    result = memory.get('test_key')
    print('[OK] Priority test (working first): {}'.format(result))
    assert result == 'working_value', 'Working memory should take priority'
    
    # Test 4: Experiential Memory
    print()
    print('=' * 60)
    print('[TEST 4] Experiential Memory Test')
    print('=' * 60)
    
    memory.add_experiential('pitfall', 'Windows换行符问题')
    memory.add_experiential('best_practice', 'TDD开发方式', tags=['testing', 'tdd'])
    memory.add_experiential('lesson', '先测试后编码')
    print('[OK] Experiential memory added')
    
    print('[OK] Experiential entries: {}'.format(len(memory.experiential)))
    for entry in memory.experiential:
        print('  - {}: {}'.format(entry.get('category'), entry.get('content')))
    
    # Test 5: Save and Load
    print()
    print('=' * 60)
    print('[TEST 5] Save and Load Test')
    print('=' * 60)
    
    # Save
    success = memory.save()
    print('[OK] Save result:', success)
    print('[OK] File exists:', os.path.exists(memory_path))
    
    # Read file content
    with open(memory_path, 'r', encoding='utf-8') as f:
        content = f.read()
    print('[OK] File content preview (first 500 chars):')
    print(content[:500])
    
    # Load into new instance
    memory2 = MemoryManager(memory_path)
    success = memory2.load()
    print('[OK] Load result:', success)
    
    # Verify data
    name2 = memory2.get('project.name')
    task2 = memory2.get('current_task')
    print('[OK] Loaded factual: {}'.format(name2))
    print('[OK] Loaded working: {}'.format(task2))
    assert name2 == 'QuickAgents', 'Factual memory should persist'
    assert task2 == 'Testing MemoryManager', 'Working memory should persist'
    
    # Test 6: Search Function
    print()
    print('=' * 60)
    print('[TEST 6] Search Function Test')
    print('=' * 60)
    
    # Search in factual
    results = memory.search('QuickAgents')
    print('[OK] Search "QuickAgents": {} results'.format(len(results)))
    for r in results:
        print('  - {}: {} = {}'.format(r['type'], r.get('key'), r.get('value')))
    
    # Search in experiential
    results = memory.search('TDD')
    print('[OK] Search "TDD": {} results'.format(len(results)))
    
    results = memory.search('Windows')
    print('[OK] Search "Windows": {} results'.format(len(results)))
    
    # Test 7: Clear Working Memory
    print()
    print('=' * 60)
    print('[TEST 7] Clear Working Memory Test')
    print('=' * 60)
    
    memory.clear_working()
    print('[OK] Working memory cleared')
    print('[OK] Working memory count: {}'.format(len(memory.working)))
    
    task = memory.get('current_task')
    print('[OK] Get cleared task: {}'.format(task))
    assert task is None, 'Working memory should be cleared'
    
    # Factual should still exist
    name = memory.get('project.name')
    print('[OK] Factual still exists: {}'.format(name))
    assert name == 'QuickAgents', 'Factual memory should not be affected'
    
    # Test 8: Default Value
    print()
    print('=' * 60)
    print('[TEST 8] Default Value Test')
    print('=' * 60)
    
    result = memory.get('non_existent_key')
    print('[OK] Get non-existent (no default): {}'.format(result))
    
    result = memory.get('non_existent_key', default='default_value')
    print('[OK] Get non-existent (with default): {}'.format(result))
    assert result == 'default_value', 'Should return default value'
    
    # Test 9: Special Characters
    print()
    print('=' * 60)
    print('[TEST 9] Special Characters Test')
    print('=' * 60)
    
    memory3 = MemoryManager(os.path.join(test_dir, 'SPECIAL.md'))
    memory3.set_factual('chinese', '中文测试 🎉')
    memory3.set_factual('emoji', 'Test with emoji 🚀💻')
    memory3.set_factual('math', 'Math symbols: ∑ ∫ √ ∞')
    memory3.set_working('special', '特殊字符: <>&"\'')
    memory3.save()
    
    memory4 = MemoryManager(os.path.join(test_dir, 'SPECIAL.md'))
    memory4.load()
    
    chinese = memory4.get('chinese')
    emoji = memory4.get('emoji')
    math = memory4.get('math')
    special = memory4.get('special')
    print('[OK] Chinese: {}'.format(chinese))
    print('[OK] Emoji: {}'.format(emoji))
    print('[OK] Math: {}'.format(math))
    print('[OK] Special: {}'.format(special))
    
    assert '中文测试' in chinese, 'Chinese characters should be preserved'
    assert '🚀' in emoji, 'Emoji should be preserved'
    assert '∑' in math, 'Math symbols should be preserved'
    
    # Test 10: Non-existent File
    print()
    print('=' * 60)
    print('[TEST 10] Non-existent File Test')
    print('=' * 60)
    
    memory5 = MemoryManager(os.path.join(test_dir, 'NOT_EXIST.md'))
    success = memory5.load()
    print('[OK] Load non-existent file: {}'.format(success))
    assert success == False, 'Should return False for non-existent file'
    
    # Should still be able to set and save
    memory5.set_factual('test', 'value')
    success = memory5.save()
    print('[OK] Save new file: {}'.format(success))
    print('[OK] File created:', os.path.exists(os.path.join(test_dir, 'NOT_EXIST.md')))
    
    # Cleanup
    shutil.rmtree(test_dir)
    
    print()
    print('=' * 60)
    print('[SUCCESS] MemoryManager All Core Tests Passed!')
    print('=' * 60)

if __name__ == '__main__':
    test_memory_manager()
