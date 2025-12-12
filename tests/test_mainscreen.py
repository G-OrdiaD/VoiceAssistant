import pytest
import sys
import os
from unittest.mock import Mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))
from src.gui.mainscreen import MainScreen

class TestMainScreen:
    @pytest.fixture
    def main_screen(self, mock_app):
        screen = MainScreen()
        screen.set_app_instance(mock_app)
        return screen

    @pytest.mark.ui
    def test_create_task(self, main_screen):
        main_screen.app.db_manager.add_task.return_value = True
        main_screen.create_task("Test task", "2:00 PM")
        main_screen.app.db_manager.add_task.assert_called_once()

    @pytest.mark.ui
    def test_mark_done(self, main_screen):
        main_screen.app.db_manager.mark_done.return_value = True
        main_screen.mark_done(None, 1)
        main_screen.app.db_manager.mark_done.assert_called_once_with(1)

    @pytest.mark.ui
    def test_delete_task(self, main_screen):
        main_screen.app.db_manager.delete_task.return_value = True
        main_screen.delete_task(None, 1)
        main_screen.app.db_manager.delete_task.assert_called_once_with(1)

    @pytest.mark.security
    def test_no_plain_text_logging(self, main_screen, caplog):
        """Verify sensitive data isn't logged in plain text"""
        with caplog.at_level('INFO'):
            main_screen.create_task("Secret task", "3:00 PM")
        
        # Check logs don't contain sensitive data
        log_text = caplog.text
        assert "Secret" not in log_text