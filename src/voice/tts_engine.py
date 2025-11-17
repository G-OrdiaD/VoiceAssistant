import logging
import pyttsx3
import threading

logger = logging.getLogger(__name__)


class TextToSpeechEngine:
    """
    Handles text-to-speech using pyttsx3.
    - Uses a threading.Lock to avoid concurrent runAndWait() calls.
    """

    def __init__(self):
        self.engine = None
        self.rate = 200
        self.current_voice = 0
        self.voice_ids = []
        self._speak_lock = threading.Lock()
        self._init_engine()

    def _init_engine(self):
        """Initialize TTS engine and pick preferred voices when available."""
        try:
            self.engine = pyttsx3.init()
            voices = self.engine.getProperty('voices') or []

            # Preferred macOS voices by ID fragment
            preferred_voices = [
                'com.apple.eloquence.en-GB.Eddy',          # Index 0 - "Eddy"
                'com.apple.voice.compact.en-AU.Karen',     # Index 1 - "Karen"
                'com.apple.voice.compact.en-ZA.Tessa',     # Index 2 - "Tessa"
                'com.apple.eloquence.en-GB.Grandpa'        # Index 3 - "GrandPa"
            ]

            self.voice_ids = []
            found_list, missing_list = [], []

            for pref in preferred_voices:
                match = next((v.id for v in voices if pref in v.id), None)
                if match:
                    self.voice_ids.append(match)
                    found_list.append(pref)
                else:
                    missing_list.append(pref)

            # Fallback: use first few available voices
            if not self.voice_ids and voices:
                self.voice_ids = [v.id for v in voices[:4]]

            if self.voice_ids:
                self.engine.setProperty('voice', self.voice_ids[0])
            else:
                logger.warning("No TTS voices available")

            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', 1.0)

            logger.info(
                f"TTS init: {len(self.voice_ids)} voices selected. "
                f"Found preferred: {len(found_list)}; Missing: {len(missing_list)}"
            )

        except Exception as e:
            logger.error(f"Error initializing TTS engine: {e}")
            self.engine = None

    def set_voice(self, voice_index: int):
        """
        Set TTS voice by index into the preferred list.
        """
        try:
            if not self.engine:
                logger.warning("TTS engine not initialized")
                return

            if 0 <= voice_index < len(self.voice_ids):
                with self._speak_lock:
                    self.engine.setProperty('voice', self.voice_ids[voice_index])
                    self.current_voice = voice_index
                    logger.info(f"TTS voice changed to index: {voice_index}")
            else:
                logger.warning(
                    f"Voice index {voice_index} not available. "
                    f"Available: 0-{len(self.voice_ids)-1}"
                )

        except Exception as e:
            logger.error(f"Error setting voice: {e}")

    def set_rate(self, rate: int):
        """Set speech rate (approx. words per minute)."""
        self.rate = rate
        try:
            if self.engine:
                self.engine.setProperty('rate', rate)
                logger.info(f"TTS rate set to: {rate}")
        except Exception as e:
            logger.error(f"Error setting speech rate: {e}")

    def speak(self, text: str):
        """
        Convert text to speech with thread safety.

        - Uses a lock to serialize access to runAndWait().
        - On error, tries a one-time engine re-init and retry.
        """
        try:
            if not self.engine:
                logger.warning("TTS engine not available")
                return

            if not text or not text.strip():
                return

            with self._speak_lock:
                # Stop any ongoing speech first
                self._stop_safe()

                # Small pause for macOS audio stability
                import time
                time.sleep(0.3)

                try:
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception as e:
                    logger.warning(f"TTS run error, attempting one-time recovery: {e}")
                    self._recover_engine()
                    try:
                        self.engine.say(text)
                        self.engine.runAndWait()
                    except Exception as e2:
                        logger.error(f"TTS speak failed after recovery: {e2}")

        except Exception as e:
            logger.error(f"Error in TTS speak: {e}")

    def _recover_engine(self):
        """
        One-time soft recovery for engine glitches, including macOS
        PaMacCore (-50) audio errors.
        """
        try:
            self._stop_safe()
            self._init_engine()
            if self.engine and self.voice_ids:
                safe_index = min(self.current_voice, max(0, len(self.voice_ids) - 1))
                self.engine.setProperty('voice', self.voice_ids[safe_index])
            if self.engine:
                self.engine.setProperty('rate', self.rate)
        except Exception as e:
            logger.error(f"Error recovering TTS engine: {e}")

    def _stop_safe(self):
        """Stop speech safely inside the lock context."""
        try:
            if self.engine and hasattr(self.engine, "stop"):
                self.engine.stop()
        except Exception as e:
            logger.error(f"Error stopping TTS: {e}")

    def stop(self):
        """Public method: stop any ongoing speech."""
        with self._speak_lock:
            self._stop_safe()

    def get_voice_count(self) -> int:
        """Get number of available voices (for diagnostics/UI)."""
        return len(self.voice_ids)