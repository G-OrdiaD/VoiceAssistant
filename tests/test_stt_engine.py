import pytest
import sys
import os
from unittest.mock import Mock, patch

# sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src')) <-- REMOVED/IGNORED
from src.voice.stt_engine import SpeechToTextEngine

class TestSpeechToTextEngine:
    @pytest.fixture
    def stt(self):
        mock_app = Mock()
        return SpeechToTextEngine(mock_app)

    @pytest.mark.voice
    def test_start_listening(self, stt):
        callback = Mock()
        stt.start_listening(callback)
        assert stt.listening_callback == callback

    @pytest.mark.voice
    def test_stop_listening(self, stt):
        stt.is_listening = True
        stt.stop_listening()
        assert stt.is_listening is False

    @pytest.mark.security
    def test_voice_data_not_stored(self, stt):
        """Verify voice data isn't persistently stored"""
        assert not hasattr(stt, 'audio_storage')
        assert not hasattr(stt, 'save_audio')

    @pytest.mark.security
    def test_no_network_calls_in_listening(self, stt):
        """Verify STT doesn't make external network calls"""
        with patch('stt_engine.requests') as mock_requests:
            callback = Mock()
            stt.start_listening(callback)
            mock_requests.post.assert_not_called()