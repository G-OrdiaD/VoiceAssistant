import pytest
import sqlite3
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from src.data.database import DatabaseManager

class TestDatabaseManager:
    @pytest.fixture
    def test_db_manager(self):
        return DatabaseManager(test_mode=True)

    @pytest.mark.integration
    def test_add_task(self, test_db_manager):
        success = test_db_manager.add_task("Test task", "10:00 AM")
        assert success is True

    @pytest.mark.integration
    def test_get_all_tasks(self, test_db_manager):
        test_db_manager.add_task("Test task", "10:00 AM")
        tasks = test_db_manager.get_all_tasks()
        assert len(tasks) == 1
        assert tasks[0].title == "Test task"

    @pytest.mark.integration
    def test_task_encryption(self, test_db_manager):
        """Verify tasks are stored encrypted"""
        test_db_manager.add_task("Secret meeting", "2:00 PM")
        
        # Check raw database content is encrypted
        conn = sqlite3.connect(test_db_manager.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT title_encrypted FROM tasks")
        encrypted_title = cursor.fetchone()[0]
        conn.close()
        
        # Should not contain plain text
        assert "Secret" not in encrypted_title
        assert "meeting" not in encrypted_title

    @pytest.mark.security
    def test_encryption_decryption_consistency(self, test_db_manager):
        original_text = "Private task"
        encrypted = test_db_manager.security.encrypt_data(original_text)
        decrypted = test_db_manager.security.decrypt_data(encrypted)
        assert decrypted == original_text

    @pytest.mark.integration
    def test_delete_task(self, test_db_manager):
        test_db_manager.add_task("Delete me", "11:00 AM")
        tasks_before = test_db_manager.get_all_tasks()
        success = test_db_manager.delete_task(tasks_before[0].id)
        assert success is True
        tasks_after = test_db_manager.get_all_tasks()
        assert len(tasks_after) == 0

    @pytest.mark.integration
    def test_mark_done(self, test_db_manager):
        test_db_manager.add_task("Complete me", "12:00 PM")
        tasks = test_db_manager.get_all_tasks()
        success = test_db_manager.mark_done(tasks[0].id)
        assert success is True
        updated_tasks = test_db_manager.get_all_tasks()
        assert updated_tasks[0].is_completed is True