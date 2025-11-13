import logging
import pyttsx3
import threading

logger = logging.getLogger(__name__)

class TextToSpeechEngine:
    def __init__(self):
        self.engine = None
        self.rate = 200
        self.current_voice = 0
        self.voice_ids = []
        self._speak_lock = threading.Lock()
        self._init_engine()

    def _init_engine(self):
        """Initialize TTS engine with pyttsx3 only."""
        try:
            self.engine = pyttsx3.init()
            voices = self.engine.getProperty('voices') or []

            # Preferred voices
            preferred_voices = [
                'com.apple.eloquence.en-GB.Eddy',          # Index 0 - "Eddy"
                'com.apple.voice.compact.en-AU.Karen',     # Index 1 - "Karen"
                'com.apple.voice.compact.en-ZA.Tessa',     # Index 2 - "Tessa"
                'com.apple.eloquence.en-GB.Grandpa'        # Index 3 - "GrandPa"
            ]

            # Build preferred voice list without repeating logs per item
            self.voice_ids = []
            found_list, missing_list = [], []
            for pref in preferred_voices:
                match = next((v.id for v in voices if pref in v.id), None)
                if match:
                    self.voice_ids.append(match)
                    found_list.append(pref)
                else:
                    missing_list.append(pref)

            # Fallback: if we don't have all preferred voices, use available ones (first 4)
            if not self.voice_ids and voices:
                self.voice_ids = [v.id for v in voices[:4]]

            # Set default voice if available
            if self.voice_ids:
                self.engine.setProperty('voice', self.voice_ids[0])
            else:
                logger.warning("No TTS voices available")

            # Configure rate/volume
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', 1.0)

            # Single concise summary log (no per-voice spam)
            logger.info(
                f"TTS init: {len(self.voice_ids)} voices selected. "
                f"Found preferred: {len(found_list)}; Missing: {len(missing_list)}"
            )

        except Exception as e:
            logger.error(f"Error initializing TTS engine: {e}")
            self.engine = None

    def set_voice(self, voice_index: int):
        """Set TTS voice by index into preferred list."""
        try:
            if not self.engine:
                logger.warning("TTS engine not initialized")
                return

            if 0 <= voice_index < len(self.voice_ids):
                with self._speak_lock:
                    self.engine.setProperty('voice', self.voice_ids[voice_index])
                    self.current_voice = voice_index
                    # Keep this single informational line (no duplication)
                    logger.info(f"TTS voice changed to index: {voice_index}")
            else:
                logger.warning(f"Voice index {voice_index} not available. Available: 0-{len(self.voice_ids)-1}")

        except Exception as e:
            logger.error(f"Error setting voice: {e}")

    def set_rate(self, rate: int):
        """Set speech rate (approx. words per minute)."""
        self.rate = rate
        try:
            if self.engine:
                self.engine.setProperty('rate', rate)
                # Keep a single concise line; avoid repetitive logs elsewhere
                logger.info(f"TTS rate set to: {rate}")
        except Exception as e:
            logger.error(f"Error setting speech rate: {e}")

    def speak(self, text: str):
        """Convert text to speech with thread safety."""
        try:
            if not self.engine:
                logger.warning("TTS engine not available")
                return

            # Use lock to prevent concurrent audio access
            with self._speak_lock:
                # Stop any previous speech
                self._stop_safe()

                # macOS audio needs cleanup time
                import time
                time.sleep(0.3)

                # Speak with thread protection
                try:
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception as e:
                    # Handle intermittent CoreAudio / PaMacCore (-50) style errors:
                    # Re-initialize the engine once and retry the utterance.
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
        """One-time soft recovery for macOS CoreAudio (e.g., PaMacCore err=-50) or engine glitches."""
        try:
            # Stop and drop current engine if any
            self._stop_safe()
            # Re-init engine and reapply current voice/rate
            self._init_engine()
            if self.engine and self.voice_ids:
                safe_index = min(self.current_voice, max(0, len(self.voice_ids) - 1))
                self.engine.setProperty('voice', self.voice_ids[safe_index])
            if self.engine:
                self.engine.setProperty('rate', self.rate)
        except Exception as e:
            logger.error(f"Error recovering TTS engine: {e}")

    def _stop_safe(self):
        """Stop speech safely within lock context."""
        try:
            if self.engine and hasattr(self.engine, "stop"):
                self.engine.stop()
        except Exception as e:
            logger.error(f"Error stopping TTS: {e}")

    def stop(self):
        """Stop any ongoing speech - thread-safe public method."""
        with self._speak_lock:
            self._stop_safe()

    def get_voice_count(self) -> int:
        """Get number of available voices."""
        return len(self.voice_ids)