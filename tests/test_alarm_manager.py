import pytest
import sys
import os
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

class TestAlarmManager:
    @pytest.fixture
    def alarm_manager(self):
        # Import main and get AlarmManager from it
        import src.main
        mock_app = Mock()
        return main.AlarmManager(mock_app)  # Access from main module

    @pytest.fixture
    def sample_task(self):
        task = Mock()
        task.id = 1
        task.title = "Take medicine"
        task.due_time = "10:00 AM"
        task.is_completed = False
        return task

    @pytest.mark.integration
    def test_should_trigger_alarm(self, alarm_manager, sample_task):
        sample_task.due_time = "10:00 AM"
        assert alarm_manager._should_trigger_alarm(sample_task, "10:00 AM") is True

    @pytest.mark.integration
    def test_should_not_trigger_wrong_time(self, alarm_manager, sample_task):
        sample_task.due_time = "10:00 AM"
        assert alarm_manager._should_trigger_alarm(sample_task, "11:00 AM") is False

    @pytest.mark.integration
    def test_should_not_trigger_completed_task(self, alarm_manager, sample_task):
        sample_task.due_time = "10:00 AM"
        sample_task.is_completed = True
        assert alarm_manager._should_trigger_alarm(sample_task, "10:00 AM") is False

    @pytest.mark.slow
    @pytest.mark.integration
    def test_alarm_timing_accuracy(self, alarm_manager, sample_task):
        """Test alarm timing logic (marked as slow)"""
        # Test various time formats
        test_cases = [
            ("10:00 AM", "10:00 AM", True),
            ("10:00 AM", "10:01 AM", False),
            ("2:00 PM", "2:00 PM", True),
            ("2:00 PM", "14:00", True),
        ]
        
        for task_time, current_time, should_trigger in test_cases:
            sample_task.due_time = task_time
            result = alarm_manager._should_trigger_alarm(sample_task, current_time)
            assert result == should_trigger, f"Failed for {task_time} vs {current_time}"

    @pytest.mark.integration
    def test_handle_alarm_dismiss(self, alarm_manager, sample_task):
        alarm_manager.active_alarms = {"1_10:00 AM": True}
        alarm_manager.handle_alarm_dismiss(sample_task, "1_10:00 AM")
        alarm_manager.app.db_manager.mark_done.assert_called_once_with(1)
        assert "1_10:00 AM" not in alarm_manager.active_alarms

    @pytest.mark.security
    def test_alarm_content_encrypted_in_logs(self, alarm_manager, sample_task, caplog):
        """Verify alarm content isn't logged in plain text"""
        sample_task.title = "Private meeting with client"
        
        with caplog.at_level('INFO'):
            alarm_manager._trigger_alarm(sample_task)
        
        log_text = caplog.text
        assert "Private" not in log_text
        assert "client" not in log_text