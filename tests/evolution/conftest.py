"""
Conftest fixtures for evolution tests.

This module provides fixtures to solve Windows temp file permission issues
when using SQLite databases in tests.
"""
import pytest
import os
import tempfile
import time
from pathlib import Path


class TempDB:
    """
    A context manager for temporary SQLite databases.
    
    Solves Windows permission issues by ensuring proper cleanup order:
    1. Close database connection first
    2. Wait for file handle release
    3. Delete the file
    
    Usage:
        with TempDB() as (db, db_path):
            # db is UnifiedDB instance
            # db_path is the path to the temp db file
            # ... use db ...
    """
    
    def __init__(self):
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(temp_dir, 'test.db')
        self.db = None
        self.db = None
    
    def __enter__(self):
        from quickagents import UnifiedDB
        self.db = UnifiedDB(self.db_path)
        return self.db, self.db_path
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 1. Close database connection first
        if self.db:
            try:
                self.db.close()
            except Exception:
                pass
        
        # 2. Wait for file handle release (Windows)
        time.sleep(0.3)

        # 3. Delete the file
        max_retries = 5
        for attempt in range(max_retries):
            try:
                if os.path.exists(self.db_path):
                    os.unlink(self.db_path)
                break
            except PermissionError:
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                continue
            except Exception:
                break


@pytest.fixture
def temp_db():
    """Fixture for temporary database."""
    with TempDB() as (db, db_path):
        yield db, db_path
