import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))
from security import SecurityManager

class TestSecurity:
    @pytest.fixture
    def security_manager(self):
        return SecurityManager()

    @pytest.mark.security
    def test_encryption_decryption(self, security_manager):
        plaintext = "Sensitive task data"
        encrypted = security_manager.encrypt_data(plaintext)
        decrypted = security_manager.decrypt_data(encrypted)
        assert decrypted == plaintext
        assert plaintext not in encrypted

    @pytest.mark.security
    def test_different_encryption(self, security_manager):
        """Verify same text encrypts differently each time"""
        text = "Same text"
        encrypted1 = security_manager.encrypt_data(text)
        encrypted2 = security_manager.encrypt_data(text)
        assert encrypted1 != encrypted2  # Different IVs

    @pytest.mark.security
    def test_secure_db_path(self, security_manager):
        path = security_manager.get_secure_db_path()
        assert "OfflineVoiceAssistant" in path
        assert not path.startswith("/tmp")  # Not in temp directory