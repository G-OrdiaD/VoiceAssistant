# VoiceAssistant

**A Privacy-First, Accessible Voice Interface for Older Adults.**  
This project was developed as a research initiative to address digital isolation and technological barriers faced by older adults in rural and low-connectivity areas. OffVA delivers a fully local, intuitive task management system that prioritizes user dignity, cognitive economy, and absolute data privacy.

---

## 📜 Research Context & Problem Statement

This project investigates a critical gap in assistive technology: the lack of **truly private, offline-first, and cognitively accessible** digital aides for older adult populations.

| Research Challenge | OffVA's Investigative Approach |
| :--- | :--- |
| **Digital Isolation & Complex GUIs**  | Replaces complex menus with a structured, natural voice command interface (`"Remind me to..."`) to reduce cognitive load. |
| **Cloud Dependency & Privacy Risks** | Implements a fully offline stack (Vosk STT, local SQLite DB) to eliminate data exposure and ensure functionality without internet. |
| **Cognitive Economy for Older Adults**  | Employs a high-contrast, decluttered Kivy GUI and linear task flows to support aging-in-place. |
| **Robustness in Assistive Systems**  | Features a dual-interaction model (voice + manual GUI input) to maintain utility when voice recognition fails. |

The system was functionally tested and its interaction model validated with users from the target demographic to ensure real-world usability.

---

## ✨ Features & Technical Response

| Feature | Implementation | Research Rationale |
| :--- | :--- | :--- |
| **🔐 Full Offline Operation** | Vosk STT engine; PyAudio; local SQLite DB. | **Privacy-by-design:** Eliminates cloud dependency, ensuring no user data leaves the device. |
| **🗄️ Encrypted Data-At-Rest** | `cryptography` (Fernet) for full-database encryption. | **Investigates on-device security models** for sensitive personal data (health reminders, schedules). |
| **🎤 Structured Voice Parsing** | Rule-based NLP parser using regex for `Remind me to [task] at [time]`. | **Validates a "cognitive economy" hypothesis:** Structured commands are more reliable and less mentally taxing than open-ended dialogue for task management. |
| **🔄 Dual-Modal Interaction** | Synchronized Kivy GUI (manual task entry) and voice channel. | **Addresses robustness:** Provides a fallback interaction channel, ensuring system resilience. |
| **🧪 Modular Test Suite** | `pytest` unit/integration tests for core modules (security, parser, DB). | **Promotes research reproducibility** and system reliability for longitudinal study. |

---

## 🗄️ System Architecture & Security Model

The architecture is built on the principle of **Minimal, Focused Decryption** to maximize privacy while maintaining functionality.

### Secure Data Flow
```
┌─────────────────────┐    ┌─────────────────────────────────────┐
│   User Interaction  │    │         Secure Storage Layer        │
├─────────────────────┤    ├─────────────────────────────────────┤
│  Voice: "Remind me  │───▶│ 1. Parse → [task], [time]           │
│  to X at Y"         │    │ 2. Derive Key ← User Passphrase     │
│  or                 │    │ 3. Encrypt Fields → Write to        │
│  Manual GUI Entry   │    │    ┌────────────────────────────┐   │
└─────────────────────┘    │    │   🔒 ENCRYPTED SQLITE DB   │   │
                           │    │   tasks.db                 │   │
┌─────────────────────┐    │    └────────────────────────────┘   │
│   Runtime Scheduler │    └───────────────────┬─────────────────┘
├─────────────────────┤                        │ (Encrypted Query)
│ 4. Periodic Check ──┼────────────────────────┘                  │
│ 5. Decrypt *Time*   │                                           │
│    Field Only       │    ┌─────────────────────────────────────┐│
│ 6. If time ≤ now ───┼───▶│     Trigger Alert Layer            ││
└─────────────────────┘    │├─────────────────────────────────────┤│
                           ││ - Decrypt *Full Task*               ││
                           ││ - TTS Audio Alert                   ││
                           ││ - GUI Notification Popup            ││
                           │└─────────────────────────────────────┘│
                           └───────────────────────────────────────┘
```

### Key Investigated Security Principles
1.  **Encryption at Rest**: The entire `tasks.db` file is encrypted. Investigates practical usability of transparent encryption for non-technical users.
2.  **Focused Decryption**: The background scheduler decrypts only the *reminder time* for checking. The *task description* remains encrypted until alert time. This explores a model of **least-privilege data access** in local applications.
3.  **Key Derivation**: The encryption key is derived from a user-provided passphrase via `PBKDF2`. The key itself is **never stored**, testing a balance between security and recoverability.

---

## 📁 Project Structure

```
offva/
├── src/
│   ├── data/                 # Data & Encryption Layer
│   │   ├── database.py       # Encrypted SQLite interface
│   │   ├── encryption.py     # Key derivation & cipher functions
│   │   └── models.py         # Data models
│   ├── voice/                # Voice Processing Layer
│   │   ├── stt_engine.py     # Vosk speech-to-text
│   │   ├── tts_engine.py     # Text-to-speech output
│   │   └── command_parser.py # Rule-based NLP parser
│   ├── gui/                  # Kivy UI Layer
│   │   ├── main_screen.py
│   │   ├── tasks_screen.py
│   │   └── *.kv              # UI layout files
│   ├── core/                 # Application Logic
│   │   └── alarm_manager.py  # Background scheduler
│   └── main.py               # Application entry point
├── tests/                    # Test Suite
│   ├── integration/
│   ├── test_database.py
│   ├── test_security.py      # Critical encryption tests
│   └── test_command_parser.py
├── assets/                   # Fonts & Icons
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

---

## 🚀 Installation & Quick Start

### Prerequisites
- Python 3.9+
- Microphone

### Setup
```bash
# 1. Clone repository
git clone https://github.com/G-OrdiaD/VoiceAssistant.git
cd VoiceAssistant

# 2. Create virtual environment & install dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Download offline voice model
python download_model.py

# 4. Launch application
python src/main.py

#or
python -m src.main
```

### Basic Usage
- **Voice Command**: Say `"Remind me to take my medication at 8 PM"`.
- **Manual Entry**: Use the 'Tasks' screen in the GUI.
- **View Reminders**: Ask `"What are my reminders for today?"`

---

## 🔬 Research Findings & Future Directions

### Validated Outcomes
1.  **Structured voice commands** were successfully adopted by test users for routine task creation.
2.  The **dual-modal (voice+GUI) interface** proved essential for handling recognition errors and user preference.
3.  **Local, encrypted storage** was implemented without compromising the application's responsiveness.

### Open Challenges & Future Work
| Research Direction | Description |
| :--- | :--- |
| **Mobile & Low-Resource Port** | Extending accessibility by porting to Android/iOS and Raspberry Pi. |
| **Enhanced NLP for Complexity** | Moving beyond regex to a lightweight local model for parsing more complex command structures. |
| **Longitudinal Usability Study** | Deploying OffVA in a multi-month study to measure its impact on daily routine adherence and digital confidence. |
| **Secure Local Device Integration** | Exploring standards like Matter for offline, encrypted integration with smart home devices. |

**Collaboration is welcome** on any of these fronts, particularly in conducting formal user studies or porting efforts.

---

## 🧪 Testing & Reproducibility

To ensure the integrity of the research implementation:
```bash
# Run the complete test suite
pytest

# Run security-critical tests individually
pytest tests/test_security.py -v
pytest tests/test_database.py -v
```
Test coverage includes encryption/decryption fidelity, voice command parsing accuracy, and database integrity.

---

## 📄 License

This research prototype is released under the **MIT License**. See the `LICENSE` file for details. The use of this software in user studies is encouraged with proper attribution.

---

## 🙏 Acknowledgments

This project stands on the shoulders of pivotal open-source work:
-   [**Vosk**](https://alphacephei.com/vosk/): Enabling accurate, offline speech recognition.
-   [**Kivy**](https://kivy.org/): Providing a cross-platform Python UI framework accessible to older adults.
-   [**Cryptography.io**](https://cryptography.io/): Delivering robust, auditable encryption primitives.


---
*VoiceAssistant represents an ongoing inquiry into dignified, private, and accessible personal technology.*
```