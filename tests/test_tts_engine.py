import pytest
import sys
import os
from unittest.mock import Mock, patch

# sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src')) <-- REMOVED/IGNORED due to successful pip install -e .
from src.voice.tts_engine import TextToSpeechEngine

class TestTextToSpeechEngine:
    @pytest.fixture
    def tts(self):
        mock_app = Mock()
        return TextToSpeechEngine(mock_app)

    @pytest.mark.voice
    def test_speak(self, tts):
        # Mock the actual TTS implementation to avoid audio output during tests
        with patch.object(tts, '_speak_implementation'):
            tts.speak("Test message")
            tts._speak_implementation.assert_called_once_with("Test message")

    @pytest.mark.voice
    def test_set_voice(self, tts):
        tts.set_voice(1)
        assert tts.current_voice == 1

    @pytest.mark.voice
    def test_set_rate(self, tts):
        tts.set_rate(200)
        assert tts.rate == 200

    @pytest.mark.security
    def test_no_network_calls(self, tts):
        """Verify TTS doesn't make external calls"""
        with patch('tts_engine.requests') as mock_requests:
            with patch.object(tts, '_speak_implementation'):
                tts.speak("Test message")
                mock_requests.post.assert_not_called()

    @pytest.mark.security
    def test_speech_data_not_logged(self, tts, caplog):
        """Verify TTS content isn't logged in plain text"""
        with caplog.at_level('INFO'):
            with patch.object(tts, '_speak_implementation'):
                tts.speak("Private reminder about meeting")
        
        assert "Private" not in caplog.text
        assert "meeting" not in caplog.text