```markdown
# Voice Assistant

An **offline-first, privacy-focused** voice assistant for daily task management. Built for simplicity and accessibility, running completely locally without internet. Developed as a research project and validated with the target demographic.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎤 **Offline Voice Recognition** | Powered by Vosk for completely local speech-to-text |
| 🔐 **Full Database Encryption** | All user data encrypted at rest using `cryptography` |
| 👵 **Accessible GUI** | High-contrast Kivy interface designed for clarity |
| 📢 **Voice & Visual Reminders** | Spoken and on-screen alerts for tasks |
| 🧪 **User-Validated** | Tested and validated with target demographic |
| 🧩 **Modular & Tested** | Clean architecture with dedicated test suite |
| 💻 **Cross-Platform** | Runs on Windows, macOS, and Linux |

---

## 🗄️ Database Architecture

The application uses a securely encrypted SQLite database. Data remains encrypted on disk with minimal, focused decryption during runtime.

```mermaid
graph TD
    subgraph User_Input
        A[User Voice Command<br/>e.g., "Remind me to..."] --> B[Command Parser]
    end

    subgraph Secure_Storage
        C{User Passphrase} --> D[Key Derivation<br/>PBKDF2/Argon2]
        D --> E[Encryption Key]
        
        B --> F[Create Reminder Task & Time]
        F --> G[Encrypt Task & Time Fields]
        G --> H[(Encrypted SQLite Database<br/>tasks.db)]
    end

    subgraph Application_Runtime
        H -- Encrypted Query --> I[Alarm Manager]
        I -- Decrypts Only Time --> J{Check if Time ≤ Now}
        J -- Yes --> K[Decrypt Full Task]
        K --> L[Trigger Alert<br/>GUI/TTS Notification]
    end

    style H fill:#f9f,stroke:#333,stroke-width:2px
    style D fill:#ccf,stroke:#333
```

**Key Security Principles:**
1. **Encryption at Rest**: The `tasks.db` file and critical fields are encrypted on disk
2. **Focused Decryption**: Scheduler decrypts only reminder times for checking alerts
3. **Key Derivation**: Encryption key derived from user passphrase (not stored)

---

## 📁 Project Structure

```
offVA/
├── src/                    # Main source code
│   ├── data/              # Data handling and encryption
│   │   ├── database.py    # Encrypted SQLite operations
│   │   ├── models.py      # Data models
│   │   └── encryption.py  # Core encryption logic
│   ├── gui/               # Kivy user interface
│   │   ├── main_screen.py
│   │   ├── tasks_screen.py
│   │   └── *.kv           # UI layout files
│   ├── voice/             # Voice processing
│   │   ├── stt_engine.py  # Speech-to-Text (Vosk)
│   │   ├── tts_engine.py  # Text-to-Speech
│   │   └── command_parser.py
│   ├── core/              # Core application logic
│   │   └── alarm_manager.py # Background scheduler
│   └── main.py            # Application entry point
├── tests/                 # Test suite
├── assets/                # Fonts and icons
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

---

## ⚡ Quick Start

```bash
# Clone and setup
git clone https://github.com/G-OrdiaD/VoiceAssistant.git
cd VoiceAssistant

# Install dependencies
pip install -r requirements.txt

# Download voice model
python download_model.py

# Run application
python src/main.py

#or 

python -m src.main
```

---

## 🗣️ Usage Examples

**Voice Commands:**
- `"Remind me to take medication at 8 PM"`
- `"What are my reminders for today?"`
- `"Delete all reminders"`
- `"Completed take medication at 8 PM"`

**Manual Control:** Use the Tasks screen in the GUI to manage reminders.

---

## 🔬 Research & Future Work

This research project focuses on accessible, privacy-preserving technology for older adults.

**Future directions:**
- Mobile platform ports (iOS/Android)
- Extended voice command recognition
- Low-resource device optimization (Raspberry Pi)
- Secure local smart home integration

**Collaboration welcome.**

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_security.py -v
```

---

## 📄 License

MIT License. See LICENSE file for details.

---

## 🙏 Acknowledgments

- [Vosk](https://alphacephei.com/vosk/) - Offline speech recognition
- [Kivy](https://kivy.org/) - Cross-platform GUI framework
- [Cryptography](https://cryptography.io/) - Encryption library
```