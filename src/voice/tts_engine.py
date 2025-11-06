import logging
import sys
import subprocess
import shlex
import pyttsx3
import threading

logger = logging.getLogger(__name__)


class TextToSpeechEngine:
    def __init__(self):
        self.engine = None
        self.rate = 200
        self.current_voice = 0
        self.voice_ids = []
        self._init_engine()

    def _init_engine(self):
        """Initialize TTS engine with accessibility settings (macOS-friendly)."""
        # Default to a safe silent engine; upgrade if pyttsx3 init succeeds
        self.engine = _SilentTTS()

        try:
            # On macOS, prefer the native NSSpeechSynthesizer driver
            driver = 'nsss' if sys.platform == 'darwin' else None
            tts = pyttsx3.init(driverName=driver)

            voices = tts.getProperty('voices') or []

            # Preferred voices (first available wins)
            preferred_voices = [
                'com.apple.eloquence.en-GB.Eddy',
                'com.apple.eloquence.en-GB.Grandpa',
                'com.apple.speech.synthesis.voice.Alex',
                'com.apple.speech.synthesis.voice.Karen',
                'com.apple.speech.synthesis.voice.Tessa'
            ]

            self.voice_ids = []
            for pref in preferred_voices:
                match = next((v.id for v in voices if pref in v.id), None)
                if match:
                    self.voice_ids.append(match)

            # Set default voice if found
            if self.voice_ids:
                tts.setProperty('voice', self.voice_ids[0])
                logger.info("Set default TTS voice to: Eddy")

            # Configure rate/volume
            tts.setProperty('rate', self.rate)
            tts.setProperty('volume', 1.0)

            self.engine = tts
            logger.info("TTS engine initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing TTS engine: {e}")
            # Use macOS 'say' fallback if available, else stay silent
            if sys.platform == 'darwin':
                self.engine = _MacSayTTS(rate_wpm=self.rate)
                logger.info("Using macOS 'say' as TTS fallback")
            else:
                self.engine = _SilentTTS()
                logger.info("Using silent TTS fallback")

    def set_voice(self, voice_index: int):
        """Set TTS voice by index into preferred list (if available)."""
        try:
            if not hasattr(self.engine, "setProperty"):
                logger.warning("Current TTS engine does not support voice switching.")
                return
            if 0 <= voice_index < len(self.voice_ids):
                self.engine.setProperty('voice', self.voice_ids[voice_index])
                self.current_voice = voice_index
                logger.info(f"TTS voice changed to index: {voice_index}")
            else:
                logger.warning(f"Voice index {voice_index} not available")
        except Exception as e:
            logger.error(f"Error setting voice: {e}")

    def set_rate(self, rate: int):
        """Set speech rate (approx. words per minute)."""
        self.rate = rate
        try:
            if hasattr(self.engine, "setProperty"):
                self.engine.setProperty('rate', rate)
            logger.info(f"TTS rate set to: {rate}")
        except Exception as e:
            logger.error(f"Error setting speech rate: {e}")

    def speak(self, text: str):
        """Convert text to speech - non-blocking."""
        try:
            if hasattr(self.engine, "say") and hasattr(self.engine, "runAndWait"):
                def _speak_in_thread():
                    try:
                        self.engine.say(text)
                        self.engine.runAndWait()
                    except Exception as e:
                        logger.error(f"TTS thread error: {e}")
                
                thread = threading.Thread(target=_speak_in_thread, daemon=True)
                thread.start()
            else:
                self.engine.speak(text)
        except Exception as e:
            logger.error(f"Error in TTS speak: {e}")

    def stop(self):
        try:
            if hasattr(self.engine, "stop"):
                self.engine.stop()
        except Exception as e:
            logger.error(f"Error stopping TTS: {e}")