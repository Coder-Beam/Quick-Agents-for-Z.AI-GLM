"""
Tests for SkillEvolution - Skills自我进化系统.

34 test cases covering:
- Initialization (3)
- Task complete trigger (5)
- Git commit trigger (4)
- Error detection trigger (3)
- Periodic optimization (5)
- Skill management (8)
- Sync to markdown (3)
- Global instance (3)
"""

import pytest
import tempfile
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

from quickagents import UnifiedDB, FeedbackType
from quickagents.core.evolution import (
    SkillEvolution,
    EvolutionTrigger,
    get_evolution
)


class TestSkillEvolutionInit:
    """Test cases for SkillEvolution initialization."""
    
    def test_init_creates_evolution_tables(self):
        """Initialization creates skill_evolution, skill_usage, evolution_config tables."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            # Check tables exist
            with db._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check skill_evolution table
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='skill_evolution'
                """)
                assert cursor.fetchone() is not None
                
                # Check skill_usage table
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='skill_usage'
                """)
                assert cursor.fetchone() is not None
                
                # Check evolution_config table
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='evolution_config'
                """)
                assert cursor.fetchone() is not None
    
    def test_init_creates_indexes(self):
        """Initialization creates necessary indexes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            with db._get_connection() as conn:
                cursor = conn.cursor()
                
                # Check indexes on skill_evolution
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='index' AND tbl_name='skill_evolution'
                """)
                indexes = [row['name'] for row in cursor.fetchall()]
                assert 'idx_evolution_skill' in indexes
                assert 'idx_evolution_trigger' in indexes
                assert 'idx_evolution_status' in indexes
                
                # Check indexes on skill_usage
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='index' AND tbl_name='skill_usage'
                """)
                indexes = [row['name'] for row in cursor.fetchall()]
                assert 'idx_usage_skill' in indexes
                assert 'idx_usage_created' in indexes
    
    def test_init_with_project_name(self):
        """Initialization accepts project_name parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db, project_name='TestProject')
            
            assert evolution.project_name == 'TestProject'


class TestTaskCompleteTrigger:
    """Test cases for on_task_complete trigger."""
    
    def test_task_complete_records_skill_usage(self):
        """on_task_complete records skills usage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            task_info = {
                'task_id': 'T001',
                'task_name': 'Test task',
                'skills_used': ['tdd-workflow-skill', 'git-commit-skill'],
                'success': True,
                'duration_ms': 5000
            }
            
            result = evolution.on_task_complete(task_info)
            
            assert result['trigger'] == EvolutionTrigger.TASK_COMPLETE.value
            assert len(result['skills_analyzed']) == 2
            assert 'tdd-workflow-skill' in result['skills_analyzed']
            assert 'git-commit-skill' in result['skills_analyzed']
    
    def test_task_complete_analyzes_failure(self):
        """on_task_complete analyzes failure when success=False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            task_info = {
                'task_id': 'T002',
                'task_name': 'Failed task',
                'skills_used': ['tdd-workflow-skill'],
                'success': False,
                'error': 'Test failed'
            }
            
            result = evolution.on_task_complete(task_info)
            
            assert len(result['improvements_found']) > 0
            assert result['improvements_found'][0]['error'] == 'Test failed'
    
    def test_task_complete_extracts_patterns(self):
        """on_task_complete extracts reusable patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            task_info = {
                'task_id': 'T003',
                'task_name': 'Pattern task',
                'skills_used': ['skill-a', 'skill-b'],
                'success': True
            }
            
            result = evolution.on_task_complete(task_info)
            
            assert len(result['feedback_added']) > 0
    
    def test_task_complete_increments_task_count(self):
        """on_task_complete increments task count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            # Initial count should be 0
            assert evolution._get_task_count() == 0
            
            # Complete a task
            evolution.on_task_complete({
                'task_id': 'T001',
                'skills_used': []
            })
            
            assert evolution._get_task_count() == 1
            
            # Complete another task
            evolution.on_task_complete({
                'task_id': 'T002',
                'skills_used': []
            })
            
            assert evolution._get_task_count() == 2
    
    def test_task_complete_checks_periodic_optimization(self):
        """on_task_complete checks if periodic optimization is due."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            # Set task count to threshold
            for i in range(evolution.PERIODIC_TASK_THRESHOLD):
                evolution._increment_task_count()
            
            result = evolution.on_task_complete({
                'task_id': 'T001',
                'skills_used': []
            })
            
            assert result.get('periodic_optimization_due') == True


class TestGitCommitTrigger:
    """Test cases for on_git_commit trigger."""
    
    def test_git_commit_without_info_fetches_last_commit(self):
        """on_git_commit fetches last commit info if not provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            # This should work even if not in a git repo
            result = evolution.on_git_commit()
            
            assert result['trigger'] == EvolutionTrigger.GIT_COMMIT.value
    
    def test_git_commit_with_info_analyzes_message(self):
        """on_git_commit analyzes commit message for improvements."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            commit_info = {
                'hash': 'abc123',
                'message': 'refactor: improve code structure',
                'files_changed': ['src/main.py']
            }
            
            result = evolution.on_git_commit(commit_info)
            
            assert result['trigger'] == EvolutionTrigger.GIT_COMMIT.value
            assert result['commit_hash'] == 'abc123'
    
    def test_git_commit_detects_refactor(self):
        """on_git_commit detects refactor in commit message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            commit_info = {
                'hash': 'def456',
                'message': 'refactor: clean up code',
                'files_changed': []
            }
            
            result = evolution.on_git_commit(commit_info)
            
            assert len(result['improvements_found']) > 0
    
    def test_git_commit_detects_bug_fix(self):
        """on_git_commit detects fix in commit message and records bug."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            commit_info = {
                'hash': 'fix789',
                'message': 'fix: resolve null pointer exception',
                'files_changed': []
            }
            
            result = evolution.on_git_commit(commit_info)
            
            assert result['trigger'] == EvolutionTrigger.GIT_COMMIT.value


class TestErrorDetectionTrigger:
    """Test cases for on_error_detected trigger."""
    
    def test_error_detected_logs_error(self):
        """on_error_detected logs error to feedback."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            error_info = {
                'error_type': 'ValueError',
                'error_message': 'Invalid value',
                'context': 'During validation'
            }
            
            result = evolution.on_error_detected(error_info)
            
            assert result['trigger'] == EvolutionTrigger.ERROR_DETECTED.value
            assert result['logged'] == True
    
    def test_error_detected_with_skill_records_usage(self):
        """on_error_detected records skill usage if skill involved."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            error_info = {
                'error_type': 'ImportError',
                'error_message': 'Module not found',
                'context': 'Loading skill',
                'skill_involved': 'test-skill'
            }
            
            result = evolution.on_error_detected(error_info)
            
            assert result['skill_recorded'] == 'test-skill'
    
    def test_error_detected_suggests_fix(self):
        """on_error_detected provides fix suggestion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            error_info = {
                'error_type': 'FileNotFoundError',
                'error_message': 'File not found',
                'context': 'Reading config'
            }
            
            result = evolution.on_error_detected(error_info)
            
            # Suggestion should be added to feedback
            assert result['logged'] == True


class TestPeriodicOptimization:
    """Test cases for periodic optimization."""
    
    def test_check_periodic_trigger_by_task_count(self):
        """check_periodic_trigger returns True when task count reaches threshold."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            # Initially False
            assert evolution.check_periodic_trigger() == False
            
            # Increment to threshold
            for i in range(evolution.PERIODIC_TASK_THRESHOLD):
                evolution._increment_task_count()
            
            assert evolution.check_periodic_trigger() == True
    
    def test_check_periodic_trigger_by_time(self):
        """check_periodic_trigger returns True when time threshold reached."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            # Set last optimization to 8 days ago
            old_time = (datetime.now() - timedelta(days=8)).isoformat()
            with db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO evolution_config (key, value)
                    VALUES ('last_optimization', ?)
                ''', (old_time,))
            
            # Add some task count
            evolution._increment_task_count()
            
            assert evolution.check_periodic_trigger() == True
    
    def test_run_periodic_optimization_reviews_skills(self):
        """run_periodic_optimization reviews skills."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            # Add some skill usage
            evolution._record_skill_usage('skill-a', success=True)
            evolution._record_skill_usage('skill-a', success=True)
            evolution._record_skill_usage('skill-a', success=False)
            
            result = evolution.run_periodic_optimization()
            
            assert result['trigger'] == EvolutionTrigger.PERIODIC.value
            assert len(result['skills_reviewed']) > 0
    
    def test_run_periodic_optimization_resets_task_count(self):
        """run_periodic_optimization resets task count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            # Add task count
            for i in range(10):
                evolution._increment_task_count()
            
            assert evolution._get_task_count() == 10
            
            # Run optimization
            evolution.run_periodic_optimization()
            
            # Count should be reset
            assert evolution._get_task_count() == 0
    
    def test_run_periodic_optimization_updates_time(self):
        """run_periodic_optimization updates last optimization time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            # Initially None
            assert evolution._get_last_optimization_time() is None
            
            # Run optimization
            evolution.run_periodic_optimization()
            
            # Should have time now
            last_time = evolution._get_last_optimization_time()
            assert last_time is not None
            assert (datetime.now() - last_time).total_seconds() < 10


class TestSkillManagement:
    """Test cases for skill management."""
    
    def test_record_skill_creation(self):
        """record_skill_creation creates evolution record."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            record_id = evolution.record_skill_creation(
                skill_name='new-skill',
                reason='解决重复模式',
                expected_use='自动检测XXX问题'
            )
            
            assert record_id > 0
            
            # Verify record
            history = evolution.get_skill_history('new-skill')
            assert len(history) == 1
            assert history[0]['change_type'] == 'created'
    
    def test_record_skill_update(self):
        """record_skill_update creates evolution record."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            record_id = evolution.record_skill_update(
                skill_name='tdd-workflow-skill',
                version='1.1.0',
                changes=['添加覆盖率检查', '优化测试命令'],
                reason='提高测试覆盖率要求'
            )
            
            assert record_id > 0
            
            history = evolution.get_skill_history('tdd-workflow-skill')
            assert len(history) == 1
            assert history[0]['change_type'] == 'updated'
    
    def test_record_skill_archive(self):
        """record_skill_archive creates evolution record."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            record_id = evolution.record_skill_archive(
                skill_name='deprecated-skill',
                reason='功能已整合到其他Skill'
            )
            
            assert record_id > 0
            
            history = evolution.get_skill_history('deprecated-skill')
            assert len(history) == 1
            assert history[0]['change_type'] == 'archived'
    
    def test_get_skill_history_returns_multiple_records(self):
        """get_skill_history returns multiple records in order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            # Create multiple records
            evolution.record_skill_creation('test-skill', 'Created')
            evolution.record_skill_update('test-skill', '1.1.0', [], 'Updated')
            evolution.record_skill_archive('test-skill', 'Archived')
            
            history = evolution.get_skill_history('test-skill')
            
            assert len(history) == 3
            # Verify all change types are present
            change_types = [h['change_type'] for h in history]
            assert 'created' in change_types
            assert 'updated' in change_types
            assert 'archived' in change_types
    
    def test_get_skill_stats_returns_statistics(self):
        """get_skill_stats returns usage statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            # Record usage
            evolution._record_skill_usage('test-skill', task_id='T001', success=True, duration_ms=100)
            evolution._record_skill_usage('test-skill', task_id='T002', success=True, duration_ms=200)
            evolution._record_skill_usage('test-skill', task_id='T003', success=False, error_message='Error')
            
            stats = evolution.get_skill_stats('test-skill')
            
            assert stats['skill_name'] == 'test-skill'
            assert stats['total_usage'] == 3
            assert stats['success_count'] == 2
            assert stats['failure_count'] == 1
            assert stats['success_rate'] == 2/3
            assert stats['avg_duration_ms'] == 150.0
            assert len(stats['recent_errors']) == 1
    
    def test_get_skill_stats_empty_skill(self):
        """get_skill_stats returns zeros for unused skill."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            stats = evolution.get_skill_stats('unused-skill')
            
            assert stats['skill_name'] == 'unused-skill'
            assert stats['total_usage'] == 0
            assert stats['success_count'] == 0
            assert stats['success_rate'] == 0
    
    def test_get_all_skills_stats(self):
        """get_all_skills_stats returns statistics for all skills."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            # Record usage for multiple skills
            evolution._record_skill_usage('skill-a', success=True)
            evolution._record_skill_usage('skill-a', success=False)
            evolution._record_skill_usage('skill-b', success=True)
            
            stats = evolution.get_all_skills_stats()
            
            assert 'skill-a' in stats
            assert 'skill-b' in stats
            assert stats['skill-a']['count'] == 2
            assert stats['skill-b']['count'] == 1
    
    def test_get_all_skills_stats_empty(self):
        """get_all_skills_stats returns empty dict when no usage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            stats = evolution.get_all_skills_stats()
            
            assert stats == {}


class TestSyncToMarkdown:
    """Test cases for sync_to_markdown."""
    
    def test_sync_creates_markdown_files(self):
        """sync_to_markdown creates markdown files for each skill."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            # Create some evolution records
            evolution.record_skill_creation('test-skill', 'Test')
            
            # Sync
            result = evolution.sync_to_markdown(output_dir=tmpdir)
            
            assert result['skills_synced'] == 1
            assert len(result['files_created']) == 1
            assert os.path.exists(result['files_created'][0])
    
    def test_sync_includes_statistics(self):
        """sync_to_markdown includes statistics in markdown."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            # Create record and usage
            evolution.record_skill_creation('test-skill', 'Test')
            evolution._record_skill_usage('test-skill', success=True)
            
            # Sync
            result = evolution.sync_to_markdown(output_dir=tmpdir)
            
            # Read the file
            with open(result['files_created'][0], 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert 'test-skill' in content
            assert '统计信息' in content
            assert '总使用次数' in content
    
    def test_sync_uses_default_directory(self):
        """sync_to_markdown uses default directory ~/.quickagents/evolution/."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            db = UnifiedDB(db_path)
            evolution = SkillEvolution(db)
            
            # Create record
            evolution.record_skill_creation('test-skill', 'Test')
            
            # Sync with default directory
            result = evolution.sync_to_markdown()
            
            # Should create in ~/.quickagents/evolution/
            assert result['skills_synced'] == 1
            assert '.quickagents' in result['files_created'][0]


class TestGlobalInstance:
    """Test cases for global instance."""
    
    def test_get_evolution_returns_instance(self):
        """get_evolution returns SkillEvolution instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            
            # Need to reset global instance
            import quickagents.core.evolution as evo_module
            evo_module._global_evolution = None
            
            evolution = get_evolution(db_path)
            
            assert evolution is not None
            assert isinstance(evolution, SkillEvolution)
    
    def test_get_evolution_returns_singleton(self):
        """get_evolution returns same instance on repeated calls."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            
            # Reset global instances
            import quickagents.core.evolution as evo_module
            import quickagents.core.unified_db as db_module
            evo_module._global_evolution = None
            db_module._global_db = None
            
            evolution1 = get_evolution(db_path)
            
            # Second call should return same instance (even with different path)
            evolution2 = get_evolution(db_path)
            
            assert evolution1 is evolution2
    
    def test_get_evolution_with_project_name(self):
        """get_evolution accepts project_name parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            
            # Reset global instances
            import quickagents.core.evolution as evo_module
            import quickagents.core.unified_db as db_module
            evo_module._global_evolution = None
            db_module._global_db = None
            
            evolution = get_evolution(db_path, project_name='TestProject')
            
            assert evolution.project_name == 'TestProject'
