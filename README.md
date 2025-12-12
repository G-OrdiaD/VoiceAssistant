
```markdown
# Voice Assistant

An **offline-first, privacy-focused** voice assistant for daily task management, designed with simplicity and accessibility in mind. Built to run completely locally. Developed as a research project and validated with the target demographic.

---

## ✨ Features

*   🎤 **Offline Voice Recognition**: Powered by Vosk for completely local speech-to-text.
*   🔐 **Full Database Encryption**: All user data (tasks, reminders) is encrypted at rest using `cryptography`.
*   👵 **Accessible GUI**: Built with Kivy, featuring a high-contrast, clear interface.
*   📢 **Voice & Visual Reminders**: Get spoken and on-screen alerts for your tasks.
*   🧪 **User-Validated**: Functionality and design tested and validated with the target user demographic.
*   🧩 **Modular & Tested**: Clean separation of concerns with a dedicated test suite.
*   💻 **Cross-Platform Desktop**: Runs on Windows, macOS, and Linux desktop environments.


## 🗄️ Database Architecture

The application uses a securely encrypted SQLite database to store all user reminders. The architecture ensures privacy by keeping data encrypted at all times on disk, with minimal, focused decryption for application function.

```mermaid
graph TD
    subgraph User_Input
        A[User Voice Command<br/>e.g., &quot;Remind me to...&quot;] --> B[Command Parser]
    end

    subgraph Secure_Storage
        C{User Passphrase} --> D[Key Derivation<br/>PBKDF2/Argon2]
        D --> E[Encryption Key]
        
        B --> F[Create Reminder Task & Time]
        F --> G[Encrypt Task & Time Fields]
        G --> H[(Encrypted SQLite Database<br/>tasks.db)]
    end

    subgraph Application_Runtime
        H -- Encrypted Query --> I[Alarm Manager / Scheduler]
        I -- Decrypts Only Time --> J{Check if Time <= Now}
        J -- Yes --> K[Decrypt Full Task]
        K --> L[Trigger Alert<br/>GUI/TTS Notification]
    end

    style H fill:#f9f,stroke:#333,stroke-width:2px
    style D fill:#ccf,stroke:#333




Key Security Principles:

Encryption at Rest: The tasks.db file and its critical fields (task, time) are encrypted on disk.
Focused Decryption: The background scheduler only decrypts the reminder time to check for due alerts. The task description remains encrypted until the moment it needs to be displayed or spoken.
Key Derivation: The encryption key is derived from a user-provided passphrase using a secure algorithm (e.g., PBKDF2), ensuring the key itself is not stored

---

## 📁 Project Structure

```
offVA/
├── src/                    # Main source code
│   ├── data/              # Data handling and encryption
│   │   ├── database.py    # Encrypted SQLite operations
│   │   ├── models.py      # Data models
│   │   └── encryption.py  # Core encryption/decryption logic
│   ├── gui/               # Kivy-based user interface
│   │   ├── main_screen.py
│   │   ├── tasks_screen.py
│   │   └── ... (.kv files)
│   ├── voice/             # Voice processing
│   │   ├── stt_engine.py  # Speech-to-Text (Vosk)
│   │   ├── tts_engine.py  # Text-to-Speech
│   │   └── command_parser.py
│   ├── core/              # Core application logic
│   │   └── alarm_manager.py # Background reminder scheduler
│   ├── security.py        # Security configuration & utilities
│   └── main.py            # Application entry point
├── tests/                 # Test suite
│   ├── integration/
│   ├── test_database.py
│   ├── test_security.py
│   └── ...
├── assets/                # Fonts and icons
├── tasks.db               # Encrypted SQLite database (user data)
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

---

## ⚙️ Installation & Setup

### 1. Prerequisites
*   Python 3.9 or higher
*   `pip` (Python package manager)

### 2. Clone and Set Up
```bash
# 1. Clone the repository
git clone <your-repo-url>
cd offVA

# 2. Create and activate a virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download the Vosk language model
python download_model.py
```

### 3. Running the Application
```bash
python src/main.py

#or 

python -m src.main
```

---

## 🗣️ How to Use

### Voice Commands
Speak naturally to manage tasks:
*   `"Remind me to take my medication at 8 PM"`
*   `"What are my reminders for today?"`
*   `"Clear all reminders"`

### Manual Task Management
Use the **Tasks** screen in the GUI to view, add, edit, or delete reminders manually.

---

## 🔬 Research & Future Directions

This project was developed as a research initiative focused on creating accessible, privacy-preserving technology for older adults. The desktop application has been functionally tested and its design validated by users from the target demographic.

**Future development and collaboration are welcome**, particularly in exploring:
*   Porting the application to **mobile platforms** (iOS/Android) and low-resource device like Raspberry Pi to increase accessibility and convenience.
*   Extending the voice model and natural language processing for more complex commands.
*   Integrating with other local smart home or health devices in a secure, offline manner.

---

## 🔒 Security Model

*   **Encryption at Rest**: The entire `tasks.db` SQLite file is encrypted using the Fernet symmetric encryption from the `cryptography` library.
*   **On-Device Only**: All processing happens on your device. No data is sent to any server.
*   **Focused Data Access**: The background scheduler only decrypts the minimal data necessary (reminder times) to check for alerts.

---

## 🧪 Running Tests

The project includes unit and integration tests. Run them with `pytest`:

```bash
# Run all tests
pytest

# Run a specific test file (e.g., security tests)
pytest tests/test_security.py -v
```

---

## 📝 License

This project is licensed under the MIT License. See the LICENSE file for details.

---

## 🙏 Acknowledgments

*   [Vosk](https://alphacephei.com/vosk/) for the offline speech recognition toolkit.
*   [Kivy](https://kivy.org/) for the cross-platform GUI framework.
*   [Cryptography](https://cryptography.io/) for the robust encryption primitives.
```