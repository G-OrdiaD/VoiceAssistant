import pytest
import sys
import os
from unittest.mock import Mock, MagicMock

# Add src to path for all tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

@pytest.fixture
def mock_app():
    app = Mock()
    app.db_manager = Mock()
    app.tts_engine = Mock()
    app.stt_engine = Mock() 
    app.command_parser = Mock()
    app.screen_manager = Mock()
    return app

@pytest.fixture
def sample_task():
    task = Mock()
    task.id = 1
    task.title = "Take medicine"
    task.due_time = "10:00 AM" 
    task.is_completed = False
    return task

@pytest.fixture
def test_db_manager():
    from src.data.database import DatabaseManager
    return DatabaseManager(test_mode=True)