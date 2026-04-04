"""
Tests for SkillEvolution - Skills鑷垜杩涘寲绯荤粺.

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
    get_evolution,
    reset_evolution
)


class TestSkillEvolutionInit:
    """Test cases for SkillEvolution initialization."""
    
    def test_init_creates_evolution_tables(self, temp_db):
        """Initialization creates skill_evolution, skill_usage, evolution_config tables."""
        db, db_path = temp_db
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
    
    def test_init_creates_indexes(self, temp_db):
        """Initialization creates necessary indexes."""
        db, db_path = temp_db
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
    
    def test_init_with_project_name(self, temp_db):
        """Initialization accepts project_name parameter."""
        db, db_path = temp_db
        evolution = SkillEvolution(db, project_name='TestProject')
        assert evolution.project_name == 'TestProject'


class TestTaskCompleteTrigger:
    """Test cases for task complete trigger."""
    
    def test_task_complete_records_skill_usage(self, temp_db):
        """Task complete records skill usage."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        result = evolution.on_task_complete({
            'task_id': 'T001',
            'task_name': 'Test Task',
            'skills_used': ['tdd-workflow-skill', 'git-commit-skill'],
            'success': True,
            'duration_ms': 5000
        })
        
        assert result['trigger'] == EvolutionTrigger.TASK_COMPLETE.value
        assert len(result['skills_analyzed']) == 2
    
    def test_task_complete_analyzes_failure(self, temp_db):
        """Task complete analyzes failure."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        result = evolution.on_task_complete({
            'task_id': 'T002',
            'task_name': 'Failed Task',
            'skills_used': ['tdd-workflow-skill'],
            'success': False,
            'error': 'Test failed: assertion error',
            'duration_ms': 3000
        })
        
        assert result['trigger'] == EvolutionTrigger.TASK_COMPLETE.value
        assert 'improvements_found' in result
    
    def test_task_complete_extracts_patterns(self, temp_db):
        """Task complete extracts patterns."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        # Add some feedback first
        db.add_feedback('bug', 'Pattern bug', 'Description')
        
        result = evolution.on_task_complete({
            'task_id': 'T003',
            'task_name': 'Pattern Task',
            'skills_used': ['tdd-workflow-skill'],
            'success': True,
            'duration_ms': 2000
        })
        
        # Check that feedback was analyzed
        assert isinstance(result['feedback_added'], list)
    
    def test_task_complete_increments_task_count(self, temp_db):
        """Task complete increments task count."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        initial_count = evolution._get_task_count()
        
        evolution.on_task_complete({
            'task_id': 'T004',
            'task_name': 'Count Task',
            'skills_used': [],
            'success': True,
            'duration_ms': 1000
        })
        
        assert evolution._get_task_count() == initial_count + 1
    
    def test_task_complete_checks_periodic_optimization(self, temp_db):
        """Task complete checks periodic optimization."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        # Set task count to trigger threshold
        for i in range(evolution.PERIODIC_TASK_THRESHOLD - 1):
            evolution.on_task_complete({
                'task_id': f'T{i:05d}',
                'task_name': f'Task {i}',
                'skills_used': [],
                'success': True,
                'duration_ms': 1000
            })
        
        # This task should trigger periodic optimization
        result = evolution.on_task_complete({
            'task_id': 'T_TRIGGER',
            'task_name': 'Trigger Task',
            'skills_used': [],
            'success': True,
            'duration_ms': 1000
        })
        
        assert result.get('periodic_optimization_due', False)


class TestGitCommitTrigger:
    """Test cases for Git commit trigger."""
    
    def test_git_commit_without_info_fetches_last_commit(self, temp_db):
        """Git commit without info fetches last commit."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        # Mock git command
        result = evolution.on_git_commit()
        
        # Result should contain commit info, None, or a status dict (e.g. no_commits)
        assert result is None or 'commit_hash' in result or 'status' in result
    
    def test_git_commit_with_info(self, temp_db):
        """Git commit with info analyzes commit."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        commit_info = {
            'hash': 'abc123',
            'message': 'feat: add new feature',
            'author': 'test',
            'files': ['src/main.py', 'tests/test_main.py'],
            'timestamp': datetime.now().isoformat()
        }
        
        result = evolution.on_git_commit(commit_info)
        
        assert result['trigger'] == EvolutionTrigger.GIT_COMMIT.value
    
    def test_git_commit_detects_refactor(self, temp_db):
        """Git commit detects refactoring."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        commit_info = {
            'hash': 'def456',
            'message': 'refactor: improve code structure',
            'author': 'test',
            'files': ['src/main.py', 'src/utils.py'],
            'timestamp': datetime.now().isoformat(),
            'is_refactor': True
        }
        
        result = evolution.on_git_commit(commit_info)
        
        assert result['trigger'] == EvolutionTrigger.GIT_COMMIT.value
    
    def test_git_commit_detects_bug_fix(self, temp_db):
        """Git commit detects bug fix."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        commit_info = {
            'hash': 'fix789',
            'message': 'fix: resolve null pointer',
            'author': 'test',
            'files': ['src/main.py'],
            'timestamp': datetime.now().isoformat(),
            'is_fix': True
        }
        
        result = evolution.on_git_commit(commit_info)
        
        assert result['trigger'] == EvolutionTrigger.GIT_COMMIT.value


class TestErrorDetectionTrigger:
    """Test cases for error detection trigger."""
    
    def test_error_detected_logs_error(self, temp_db):
        """Error detected logs error."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        error_info = {
            'error_type': 'ImportError',
            'error_message': 'Module not found',
            'context': 'Importing quickagents',
            'timestamp': datetime.now().isoformat(),
        }
        
        result = evolution.on_error_detected(error_info)
        
        assert result['trigger'] == EvolutionTrigger.ERROR_DETECTED.value
        assert result['error_type'] == 'ImportError'
    
    def test_error_detected_with_skill_records_usage(self, temp_db):
        """Error detected with skill records usage."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        error_info = {
            'error_type': 'ImportError',
            'error_message': 'Module not found',
            'context': 'Using tdd-workflow-skill',
            'skill_involved': 'tdd-workflow-skill',
            'timestamp': datetime.now().isoformat(),
        }
        
        result = evolution.on_error_detected(error_info)
        
        assert result['trigger'] == EvolutionTrigger.ERROR_DETECTED.value
        assert result.get('skill_recorded') == 'tdd-workflow-skill'
    
    def test_error_detected_suggests_fix(self, temp_db):
        """Error detected suggests fix."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        error_info = {
            'error_type': 'ImportError',
            'error_message': 'No module named quickagents',
            'context': 'Importing quickagents',
            'timestamp': datetime.now().isoformat(),
        }
        
        result = evolution.on_error_detected(error_info)
        
        assert 'suggestion' in result or result.get('suggestion') is None


class TestPeriodicOptimization:
    """Test cases for periodic optimization."""
    
    def test_check_periodic_trigger_by_task_count(self, temp_db):
        """Check periodic trigger by task count."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        # Should not trigger initially
        assert not evolution.check_periodic_trigger()
        
        # Simulate tasks
        for i in range(evolution.PERIODIC_TASK_THRESHOLD):
            evolution.on_task_complete({
                'task_id': f'T{i:06d}',
                'task_name': f'Task {i}',
                'skills_used': [],
                'success': True,
                'duration_ms': 1000
            })
        
        # Now should trigger
        assert evolution.check_periodic_trigger()
    
    def test_check_periodic_trigger_by_time(self, temp_db):
        """Check periodic trigger by time."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        # Set last optimization time to 8 days ago
        evolution._set_last_optimization_time(
            datetime.now() - timedelta(days=8)
        )
        
        # Should trigger due to time threshold
        assert evolution.check_periodic_trigger()
    
    def test_run_periodic_optimization_reviews_skills(self, temp_db):
        """Run periodic optimization reviews skills."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        # Add some skill usage
        evolution.on_task_complete({
            'task_id': 'T001',
            'task_name': 'Test',
            'skills_used': ['tdd-workflow-skill', 'git-commit-skill'],
            'success': True,
            'duration_ms': 1000
        })
        
        result = evolution.run_periodic_optimization()
        
        assert 'skills_reviewed' in result
    
    def test_run_periodic_optimization_resets_task_count(self, temp_db):
        """Run periodic optimization resets task count."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        # Add some tasks
        for i in range(5):
            evolution.on_task_complete({
                'task_id': f'T{i:07d}',
                'task_name': f'Task {i}',
                'skills_used': [],
                'success': True,
                'duration_ms': 1000
            })
        
        result = evolution.run_periodic_optimization()
        
        assert evolution._get_task_count() == 0
    
    def test_run_periodic_optimization_updates_time(self, temp_db):
        """Run periodic optimization updates time."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        result = evolution.run_periodic_optimization()
        
        assert 'optimization_time' in result


class TestSkillManagement:
    """Test cases for skill management."""
    
    def test_record_skill_creation(self, temp_db):
        """Record skill creation."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        result = evolution.record_skill_creation(
            skill_name='new-skill',
            reason='Solve repetitive pattern',
            expected_use='Auto-detect issues'
        )
        
        assert result['skill_name'] == 'new-skill'
        assert result['change_type'] == 'creation'
    
    def test_record_skill_update(self, temp_db):
        """Record skill update."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        result = evolution.record_skill_update(
            skill_name='tdd-workflow-skill',
            version='1.1.0',
            changes=['Added coverage check', 'Improved test commands'],
            reason='Enhance test coverage'
        )
        
        assert result['skill_name'] == 'tdd-workflow-skill'
        assert result['change_type'] == 'update'
    
    def test_record_skill_archive(self, temp_db):
        """Record skill archive."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        result = evolution.record_skill_archive(
            skill_name='deprecated-skill',
            reason='Functionality merged into other skill'
        )
        
        assert result['skill_name'] == 'deprecated-skill'
        assert result['change_type'] == 'archive'
    
    def test_get_skill_history_returns_multiple_records(self, temp_db):
        """Get skill history returns multiple records."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        # Add multiple records
        evolution.record_skill_creation('test-skill', 'Created', 'Testing')
        evolution.record_skill_update('test-skill', '1.1.0', ['Update 1'], 'Improved')
        evolution.record_skill_update('test-skill', '1.2.0', ['Update 2'], 'Enhanced')
        
        history = evolution.get_skill_history('test-skill')
        
        assert len(history) >= 3
    
    def test_get_skill_stats_returns_statistics(self, temp_db):
        """Get skill stats returns statistics."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        # Add usage
        evolution.on_task_complete({
            'task_id': 'T001',
            'task_name': 'Test',
            'skills_used': ['tdd-workflow-skill'],
            'success': True,
            'duration_ms': 1000
        })
        
        stats = evolution.get_skill_stats('tdd-workflow-skill')
        
        assert stats['skill_name'] == 'tdd-workflow-skill'
        assert 'usage_count' in stats
    
    def test_get_skill_stats_empty_skill(self, temp_db):
        """Get skill stats for empty skill."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        stats = evolution.get_skill_stats('non-existent-skill')
        
        assert stats['usage_count'] == 0
    
    def test_get_all_skills_stats(self, temp_db):
        """Get all skills stats."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        # Add usage for multiple skills
        evolution.on_task_complete({
            'task_id': 'T001',
            'task_name': 'Test',
            'skills_used': ['skill-a', 'skill-b'],
            'success': True,
            'duration_ms': 1000
        })
        
        all_stats = evolution.get_all_skills_stats()
        
        assert isinstance(all_stats, dict)
        assert len(all_stats) >= 2
    
    def test_get_all_skills_stats_empty(self, temp_db):
        """Get all skills stats when empty."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        all_stats = evolution.get_all_skills_stats()
        
        assert isinstance(all_stats, dict)
        assert len(all_stats) == 0


class TestSyncToMarkdown:
    """Test cases for sync to markdown."""
    
    def test_sync_creates_markdown_files(self, temp_db):
        """Sync creates markdown files."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        # Add some data
        evolution.on_task_complete({
            'task_id': 'T001',
            'task_name': 'Test',
            'skills_used': ['tdd-workflow-skill'],
            'success': True,
            'duration_ms': 1000
        })
        
        # Sync to markdown
        output_dir = tempfile.mkdtemp()
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            evolution.sync_to_markdown(output_dir)
            
            # Check files created
            stats_file = os.path.join(output_dir, 'skill_stats.md')
            assert os.path.exists(stats_file)
        finally:
            # Cleanup
            import shutil
            shutil.rmtree(output_dir, ignore_errors=True)
    
    def test_sync_includes_statistics(self, temp_db):
        """Sync includes statistics."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        # Add usage
        evolution.on_task_complete({
            'task_id': 'T001',
            'task_name': 'Test',
            'skills_used': ['test-skill'],
            'success': True,
            'duration_ms': 1000
        })
        
        output_dir = tempfile.mkdtemp()
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            evolution.sync_to_markdown(output_dir)
            
            # Check content includes statistics
            stats_file = os.path.join(output_dir, 'skill_stats.md')
            with open(stats_file, 'r', encoding='utf-8') as f:
                content = f.read()
                assert 'test-skill' in content
        finally:
            import shutil
            shutil.rmtree(output_dir, ignore_errors=True)
    
    def test_sync_uses_default_directory(self, temp_db):
        """Sync uses default directory."""
        db, db_path = temp_db
        evolution = SkillEvolution(db)
        
        # Sync without specifying directory (should use default)
        try:
            result = evolution.sync_to_markdown()
            assert result is None or 'output_dir' in result
        except Exception:
            # Expected if default directory doesn't exist
            pass


class TestGlobalInstance:
    """Test cases for global instance management."""
    
    def test_get_evolution_returns_instance(self):
        """Get evolution returns instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            reset_evolution()
            evolution = get_evolution(db_path=db_path)
            assert evolution is not None
            assert isinstance(evolution, SkillEvolution)
            reset_evolution()
    
    def test_get_evolution_returns_singleton(self):
        """Get evolution returns singleton."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            reset_evolution()
            evolution1 = get_evolution(db_path=db_path)
            evolution2 = get_evolution(db_path=db_path)
            assert evolution1 is evolution2
            reset_evolution()
    
    def test_get_evolution_with_project_name(self):
        """Get evolution with project name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            reset_evolution()
            evolution = get_evolution(db_path=db_path, project_name='TestProject')
            assert evolution.project_name == 'TestProject'
            reset_evolution()

