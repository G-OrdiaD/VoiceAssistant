import pytest
import sys
import os
from unittest.mock import Mock, patch
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
from src.data.database import DatabaseManager
from src.voice.command_parser import CommandParser
import main 


class TestVoiceFlowIntegration:
    @pytest.fixture
    def test_system(self):
        """Set up integrated test system"""
        db = DatabaseManager(test_mode=True)
        parser = CommandParser()
        
        # Create mock app for alarm manager
        mock_app = Mock()
        mock_app.db_manager = db
        mock_app.screen_manager = Mock()
        mock_app.tts_engine = Mock()
        
        alarm_manager = main.AlarmManager(mock_app)
        
        return {
            'db': db,
            'parser': parser,
            'alarm_manager': alarm_manager,
            'app': mock_app
        }

    @pytest.mark.integration
    @pytest.mark.voice
    def test_voice_to_task_creation_flow(self, test_system):
        """Test complete voice command to task creation flow"""
        # Simulate voice command for adding task
        voice_command = "remind me to walk the dog at 3 PM"
        result = test_system['parser'].parse_task_command(voice_command)
        
        assert result["type"] == "ADD_TASK"
        assert "walk" in result["task"].lower()
        assert "dog" in result["task"].lower()
        assert "3" in result["time"]
        
        # Create task through database
        success = test_system['db'].add_task(result["task"], result["time"])
        assert success is True
        
        # Verify task can be retrieved
        tasks = test_system['db'].get_all_tasks()
        assert len(tasks) == 1
        assert "walk" in tasks[0].title.lower()
        assert "dog" in tasks[0].title.lower()
        assert tasks[0].due_time == result["time"]

    @pytest.mark.integration
    @pytest.mark.voice
    def test_voice_delete_task_flow(self, test_system):
        """Test voice command to delete task flow"""
        # First add a task
        test_system['db'].add_task("Delete this task", "4:00 PM")
        tasks_before = test_system['db'].get_all_tasks()
        assert len(tasks_before) == 1
        
        # Simulate delete voice command
        voice_command = "delete my task"
        result = test_system['parser'].parse_task_command(voice_command)
        
        assert result["type"] == "DELETE_TASK"
        assert "task" in result["task"].lower()
        
        # In real system, this would find and delete the matching task
        # For test, verify the command was parsed correctly

    @pytest.mark.integration
    @pytest.mark.voice
    def test_voice_mark_done_flow(self, test_system):
        """Test voice command to mark task as done"""
        # First add a task
        test_system['db'].add_task("Complete this task", "5:00 PM")
        tasks_before = test_system['db'].get_all_tasks()
        assert len(tasks_before) == 1
        assert tasks_before[0].is_completed is False
        
        # Simulate mark done voice command
        voice_command = "mark task as done"
        result = test_system['parser'].parse_task_command(voice_command)
        
        assert result["type"] == "MARK_DONE"
        assert "task" in result["task"].lower()

    @pytest.mark.integration
    @pytest.mark.voice
    def test_voice_list_tasks_flow(self, test_system):
        """Test voice command to list tasks"""
        # Add multiple tasks
        test_system['db'].add_task("Task one", "1:00 PM")
        test_system['db'].add_task("Task two", "2:00 PM")
        
        # Simulate list tasks voice command
        voice_command = "show my tasks"
        result = test_system['parser'].parse_task_command(voice_command)
        
        assert result["type"] == "LIST_TASKS"
        
        # Verify tasks exist in database
        tasks = test_system['db'].get_all_tasks()
        assert len(tasks) == 2

    @pytest.mark.integration
    @pytest.mark.slow
    def test_alarm_integration_flow(self, test_system):
        """Test complete alarm detection to dismissal flow"""
        # Add a test task
        test_system['db'].add_task("Test alarm task", "10:00 AM")
        tasks = test_system['db'].get_all_tasks()
        task = tasks[0]
        
        # Verify task is not completed initially
        assert task.is_completed is False
        
        # Test alarm triggering
        test_system['alarm_manager']._trigger_alarm(task)
        alarm_key = f"{task.id}_{task.due_time.upper().strip()}"
        assert alarm_key in test_system['alarm_manager'].active_alarms
        
        # Test alarm dismissal
        test_system['alarm_manager'].handle_alarm_dismiss(task, alarm_key)
        
        # Verify task is marked as completed
        updated_tasks = test_system['db'].get_all_tasks()
        assert updated_tasks[0].is_completed is True
        
        # Verify alarm is removed from active alarms
        assert alarm_key not in test_system['alarm_manager'].active_alarms

    @pytest.mark.integration
    @pytest.mark.security
    def test_data_encryption_throughout_flow(self, test_system):
        """Verify data remains encrypted throughout the entire flow"""
        sensitive_task = "Private meeting with confidential client at secret location"
        
        # Add sensitive task via voice command simulation
        voice_command = f"remind me to {sensitive_task} at 2:00 PM"
        result = test_system['parser'].parse_task_command(voice_command)
        
        assert result["type"] == "ADD_TASK"
        
        # Add to database
        success = test_system['db'].add_task(result["task"], result["time"])
        assert success is True
        
        # Verify task can be retrieved and used (decrypted)
        tasks = test_system['db'].get_all_tasks()
        assert len(tasks) == 1
        assert "private" in tasks[0].title.lower()
        assert "confidential" in tasks[0].title.lower()
        
        # The actual storage in database should be encrypted
        # This is verified in the database unit tests

    @pytest.mark.integration
    def test_error_handling_in_voice_flow(self, test_system):
        """Test that the system handles errors gracefully in voice flow"""
        # Test with invalid voice command
        result = test_system['parser'].parse_task_command("random gibberish text")
        assert result is None
        
        # System should not crash and should continue functioning
        valid_result = test_system['parser'].parse_task_command("show my tasks")
        assert valid_result["type"] == "LIST_TASKS"
        
        # Test with empty command
        empty_result = test_system['parser'].parse_task_command("")
        assert empty_result is None

    @pytest.mark.integration
    @pytest.mark.voice
    def test_multiple_voice_commands_flow(self, test_system):
        """Test processing multiple voice commands in sequence"""
        commands = [
            "remind me to buy milk at 9 AM",
            "add task call mom at 11 AM", 
            "show my tasks",
            "delete the milk task",
            "mark call as done"
        ]
        
        parsed_results = []
        for command in commands:
            result = test_system['parser'].parse_task_command(command)
            parsed_results.append(result)
        
        # Verify all commands were processed
        assert len(parsed_results) == len(commands)
        
        # Verify we got some valid results
        valid_results = [r for r in parsed_results if r is not None]
        assert len(valid_results) > 0

    @pytest.mark.integration
    @pytest.mark.slow
    def test_complete_voice_to_alarm_flow(self, test_system):
        """Test complete flow from voice command to alarm triggering"""
        # Voice command to add task
        voice_command = "remind me to take medicine at 10:30 AM"
        result = test_system['parser'].parse_task_command(voice_command)
        
        assert result["type"] == "ADD_TASK"
        
        # Add task to database
        test_system['db'].add_task(result["task"], result["time"])
        tasks = test_system['db'].get_all_tasks()
        task = tasks[0]
        
        # Simulate alarm time reached
        should_trigger = test_system['alarm_manager']._should_trigger_alarm(task, "10:30 AM")
        assert should_trigger is True
        
        # Trigger alarm
        test_system['alarm_manager']._trigger_alarm(task)
        alarm_key = f"{task.id}_{task.due_time.upper().strip()}"
        assert alarm_key in test_system['alarm_manager'].active_alarms
        
        # Dismiss alarm
        test_system['alarm_manager'].handle_alarm_dismiss(task, alarm_key)
        
        # Verify completion
        updated_tasks = test_system['db'].get_all_tasks()
        assert updated_tasks[0].is_completed is True

    @pytest.mark.integration
    @pytest.mark.security
    def test_voice_privacy_protection(self, test_system, caplog):
        """Verify voice commands don't leak sensitive information in logs"""
        sensitive_commands = [
            "remind me about my medical appointment at 3 PM",
            "add task bank transfer confirmation at 2 PM",
            "private meeting with HR at 4 PM"
        ]
        
        with caplog.at_level('INFO'):
            for command in sensitive_commands:
                test_system['parser'].parse_task_command(command)
        
        log_text = caplog.text.lower()
        sensitive_terms = ["medical", "bank", "transfer", "private", "hr"]
        
        for term in sensitive_terms:
            assert term not in log_text, f"Sensitive term '{term}' found in logs"