import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))
from voice.command_parser import CommandParser

class TestCommandParser:
    @pytest.fixture
    def parser(self):
        return CommandParser()

    @pytest.mark.voice
    def test_parse_add_task(self, parser):
        result = parser.parse_task_command("remind me to walk the dog at 3 PM")
        assert result["type"] == "ADD_TASK"
        assert "walk" in result["task"].lower()
        assert "3" in result["time"]

    @pytest.mark.voice
    def test_parse_delete_task(self, parser):
        result = parser.parse_task_command("delete my meeting task")
        assert result["type"] == "DELETE_TASK"
        assert "meeting" in result["task"].lower()

    @pytest.mark.voice
    def test_parse_mark_done(self, parser):
        result = parser.parse_task_command("mark medicine as done")
        assert result["type"] == "MARK_DONE"
        assert "medicine" in result["task"]

    @pytest.mark.voice
    def test_parse_list_tasks(self, parser):
        result = parser.parse_task_command("show my tasks")
        assert result["type"] == "LIST_TASKS"

    @pytest.mark.voice
    def test_parse_unknown_command(self, parser):
        result = parser.parse_task_command("random text about nothing")
        assert result is None

    @pytest.mark.voice
    def test_format_task_text(self, parser):
        formatted = parser.format_task_text("  walk dog  ")
        assert formatted == "Walk dog"

    @pytest.mark.security
    def test_no_sensitive_data_leakage(self, parser, caplog):
        """Verify command parsing doesn't log sensitive voice data"""
        with caplog.at_level('INFO'):
            parser.parse_task_command("private meeting with boss at 5 PM")
        
        log_text = caplog.text
        sensitive_terms = ["private", "boss", "meeting"]
        for term in sensitive_terms:
            assert term not in log_text