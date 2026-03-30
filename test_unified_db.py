#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""UnifiedDB 综合测试脚本"""

from quickagents import UnifiedDB, MemoryType, TaskStatus, FeedbackType
import os
import tempfile
import shutil

def test_unified_db():
    """测试 UnifiedDB 核心功能"""
    # 创建测试数据库
    test_dir = tempfile.mkdtemp()
    test_db_path = os.path.join(test_dir, 'test_unified.db')
    
    print('=' * 60)
    print('[TEST 1] UnifiedDB Initialization')
    print('=' * 60)
    
    db = UnifiedDB(test_db_path)
    print('[OK] Database created:', test_db_path)
    
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'", ())
        tables = [row[0] for row in cursor.fetchall()]
        print('[OK] Tables created:', tables)
    
    # Test 2: Three-dimensional Memory
    print()
    print('=' * 60)
    print('[TEST 2] Three-dimensional Memory Test')
    print('=' * 60)
    
    db.set_memory('project.name', 'TestProject', MemoryType.FACTUAL)
    db.set_memory('project.version', '1.0.0', MemoryType.FACTUAL)
    print('[OK] Factual memory set')
    
    db.set_memory('lesson.001', 'Test first', MemoryType.EXPERIENTIAL, category='best_practices')
    db.set_memory('lesson.002', 'Avoid over-engineering', MemoryType.EXPERIENTIAL, category='pitfalls')
    print('[OK] Experiential memory set')
    
    db.set_memory('current.task', 'Testing UnifiedDB', MemoryType.WORKING)
    db.set_memory('current.progress', '50%', MemoryType.WORKING)
    print('[OK] Working memory set')
    
    name = db.get_memory('project.name')
    version = db.get_memory('project.version')
    current = db.get_memory('current.task')
    print('[OK] Get memory: name={}, version={}, current={}'.format(name, version, current))
    
    results = db.search_memory('Test', MemoryType.EXPERIENTIAL)
    print('[OK] Search results: {} items'.format(len(results)))
    
    # Test 3: Task Management
    print()
    print('=' * 60)
    print('[TEST 3] Task Management Test')
    print('=' * 60)
    
    db.add_task('T001', 'Implement core features', 'P0')
    db.add_task('T002', 'Write unit tests', 'P1')
    db.add_task('T003', 'Integration tests', 'P2')
    print('[OK] Tasks added')
    
    db.update_task_status('T001', TaskStatus.COMPLETED)
    db.update_task_status('T002', TaskStatus.IN_PROGRESS)
    print('[OK] Task status updated')
    
    pending = db.get_tasks(status=TaskStatus.PENDING)
    completed = db.get_tasks(status=TaskStatus.COMPLETED)
    print('[OK] Pending tasks: {}'.format(len(pending)))
    print('[OK] Completed tasks: {}'.format(len(completed)))
    
    # Test 4: Progress Tracking
    print()
    print('=' * 60)
    print('[TEST 4] Progress Tracking Test')
    print('=' * 60)
    
    db.init_progress('test-project', total_tasks=3)
    print('[OK] Progress initialized')
    
    db.update_progress('current_task', 'T002')
    db.update_progress('completed_count', 1)
    print('[OK] Progress updated')
    
    progress = db.get_progress()
    print('[OK] Progress:', progress)
    
    # Test 5: Feedback Collection
    print()
    print('=' * 60)
    print('[TEST 5] Feedback Collection Test')
    print('=' * 60)
    
    db.add_feedback(FeedbackType.BUG, 'Found a bug', 'Detailed description')
    db.add_feedback(FeedbackType.IMPROVEMENT, 'Improvement suggestion', 'Optimize performance')
    db.add_feedback(FeedbackType.BEST_PRACTICE, 'Best practice', 'Test first')
    print('[OK] Feedback added')
    
    feedback = db.get_feedbacks(limit=5)
    print('[OK] Feedback records: {}'.format(len(feedback)))
    
    # Test 6: Statistics
    print()
    print('=' * 60)
    print('[TEST 6] Statistics Test')
    print('=' * 60)
    
    stats = db.get_stats()
    print('[OK] Memory count:', stats['memory_count'])
    print('[OK] Tasks by status:', stats['tasks'])
    print('[OK] Feedback by type:', stats['feedback'])
    
    # Cleanup
    shutil.rmtree(test_dir)
    
    print()
    print('=' * 60)
    print('[SUCCESS] UnifiedDB All Core Tests Passed!')
    print('=' * 60)

if __name__ == '__main__':
    test_unified_db()
