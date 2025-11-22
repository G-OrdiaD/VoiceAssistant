import os
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import appdirs


class SecurityManager:
    def __init__(self):
        self._init_encryption_key()
        
    def _init_encryption_key(self):
        """Initialize or load encryption key securely"""
        key_dir = appdirs.user_data_dir("OfflineVoiceAssistant", "EchoBravo")
        os.makedirs(key_dir, mode=0o700, exist_ok=True)
        key_file = os.path.join(key_dir, ".encryption_key")
        
        if os.path.exists(key_file):
            try:
                with open(key_file, 'rb') as f:
                    self.cipher_key = f.read()
            except Exception as e:
                logging.error(f"Error loading encryption key: {e}")
                self._generate_new_key(key_file)
        else:
            self._generate_new_key(key_file)
        
        self.fernet = Fernet(self.cipher_key)
    
    def _generate_new_key(self, key_file):
        """Generate a new encryption key and save it securely"""
        self.cipher_key = Fernet.generate_key()
        try:
            with open(key_file, 'wb') as f:
                os.chmod(key_file, 0o600)  # Only owner can read/write
                f.write(self.cipher_key)
            logging.info("New encryption key generated and saved")
        except Exception as e:
            logging.error(f"Error saving encryption key: {e}")
            raise
    
    def encrypt_data(self, data):
        """Encrypt sensitive data"""
        if not data:
            return data
        try:
            encrypted_bytes = self.fernet.encrypt(data.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            logging.error(f"Error encrypting data: {e}")
            return data  # Fallback to plain text if encryption fails
    
    def decrypt_data(self, encrypted_data):
        """Decrypt sensitive data"""
        if not encrypted_data:
            return encrypted_data
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logging.error(f"Error decrypting data: {e}")
            return "[Decryption Error]"  # Safe fallback
    
    def get_secure_db_path(self):
        """Get secure database path in user data directory"""
        db_dir = appdirs.user_data_dir("OfflineVoiceAssistant", "EchoBravo")
        os.makedirs(db_dir, mode=0o700, exist_ok=True)
        db_path = os.path.join(db_dir, "voice_tasks.db")
        
        # Set secure permissions on directory and file
        try:
            if os.path.exists(db_path):
                os.chmod(db_path, 0o600)
        except Exception as e:
            logging.warning(f"Could not set permissions on database: {e}")
            
        return db_path
    
    def secure_erase(self, data):
        """Securely erase sensitive data from memory (simplified)"""
        # This is a simplified version for demonstration
        if isinstance(data, str):
            return "█" * len(data)  # Visual indication of erased data
        elif isinstance(data, bytes):
            return b"\x00" * len(data)  # Zero out bytes
        return data
    
    def validate_key_integrity(self):
        """Validate that the encryption key is working properly"""
        try:
            test_data = "test_validation"
            encrypted = self.encrypt_data(test_data)
            decrypted = self.decrypt_data(encrypted)
            return decrypted == test_data
        except Exception as e:
            logging.error(f"Encryption key validation failed: {e}")
            return False
        
    # For testing
if __name__ == "__main__":
    security = SecurityManager()
    print("Security Manager Test:")
    print("Key validation:", security.validate_key_integrity())
    
    test_text = "Secret meeting at 3PM"
    encrypted = security.encrypt_data(test_text)
    decrypted = security.decrypt_data(encrypted)
    
    print("Original:", test_text)
    print("Encrypted:", encrypted)
    print("Decrypted:", decrypted)
    print("Success:", test_text == decrypted)
    print("DB path:", security.get_secure_db_path())