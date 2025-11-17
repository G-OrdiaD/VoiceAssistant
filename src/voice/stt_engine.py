import json
import audioop
import logging
import threading
from typing import Callable
import os
import pyaudio
import vosk
import kivy


logger = logging.getLogger(__name__)


class SpeechToTextEngine:
    """
    Handles microphone input and speech-to-text using Vosk.
    """

    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self.recognizer = None
        self.is_listening = False
        self.audio_stream = None
        self.callback: Callable[[str], None] = None
        self._load_model()

    def _load_model(self):
        """
        Load Vosk model with robust error handling.
        """
        try:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Vosk model not found at: {self.model_path}")

            logger.info(f"Loading Vosk model from: {self.model_path}")

            self.model = vosk.Model(self.model_path)
            self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
            self.recognizer.SetWords(True)
            self.recognizer.SetPartialWords(True)
            logger.info("Vosk model loaded successfully")

        except ImportError:
            logger.error("Vosk library not installed. Run: pip install vosk")
            raise
        except FileNotFoundError as e:
            logger.error(f"Model file error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading Vosk model: {e}")
            raise

    def start_listening(self, callback: Callable[[str], None]):
        """
        Start listening for speech and call `callback(transcript)` when done.

        - Uses a background thread to avoid blocking UI.
        - Filters background noise and ignores tiny, unreliable outputs.
        """
        if self.is_listening:
            logger.warning("Already listening, ignoring start request")
            return

        if not self.model:
            logger.error("Cannot start listening: model not loaded")
            return

        self.callback = callback
        self.is_listening = True

        def listen_thread():
            try:
                audio = pyaudio.PyAudio()
                self.audio_stream = audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=4096,
                    input_device_index=None
                )

                logger.info("🎤 Listening for commands")

                # --- Tuning parameters for older adults / home environments ---
                RMS_THRESHOLD = 700       # Ignore frames quieter than this at start
                GAIN_FACTOR = 1.5         # Gentle microphone gain
                MAX_SILENCE_FRAMES = 25   # End-of-speech after this many quiet frames
                MIN_SPEECH_FRAMES = 5     # Require some speech before we accept silence

                silence_count = 0
                speech_frames = 0
                processed_frames = 0  # ADDED: Frame counter for reset

                while self.is_listening:
                    try:
                        data = self.audio_stream.read(4096, exception_on_overflow=False)
                        if not data:
                            continue

                        # ---- Noise filtering (RMS threshold) ----
                        try:
                            rms = audioop.rms(data, 2)
                        except Exception:
                            rms = 0

                        if rms < RMS_THRESHOLD and speech_frames == 0:
                            # Initial quiet noise: skip until we hear something meaningful
                            continue

                        if rms < RMS_THRESHOLD:
                            silence_count += 1
                            # If we already heard enough speech and now see a block of silence,
                            # treat it as end-of-utterance.
                            if speech_frames > MIN_SPEECH_FRAMES and silence_count > MAX_SILENCE_FRAMES:
                                break
                        else:
                            # We heard speech
                            silence_count = 0
                            speech_frames += 1

                        # ---- Microphone gain control ----
                        try:
                            boosted = audioop.mul(data, 2, GAIN_FACTOR)
                        except Exception:
                            boosted = data  # Fallback if gain fails

                        # ADDED: Reset recognizer every 10000 frames to prevent crashes
                        processed_frames += 1
                        if processed_frames > 10000:
                            logger.info("Resetting Vosk recognizer to prevent state corruption")
                            self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
                            self.recognizer.SetWords(True)
                            self.recognizer.SetPartialWords(True)
                            processed_frames = 0

                        if self.recognizer.AcceptWaveform(boosted):
                            result = json.loads(self.recognizer.Result())
                            text = result.get('text', '').strip()

                            # ---- Junk / confidence rejection ----
                            # For very short utterances (< 2 words, very few chars),
                            # treat them as unreliable and ignore.
                            if not text or (len(text.split()) <= 1 and len(text) <= 3):
                                logger.info(f"Ignoring short/uncertain utterance: '{text}'")
                                text = ""

                            if text:
                                logger.info(f"Recognized: {text}")
                                if threading.current_thread() != threading.main_thread():
                                    kivy.clock.Clock.schedule_once(
                                        lambda dt: self.callback(text), 0
                                    )
                                else:
                                    self.callback(text)
                                break  # Stop listening after a valid recognition

                        # Partial results (used only for debug logging)
                        partial = json.loads(self.recognizer.PartialResult())
                        partial_text = partial.get('partial', '').strip()
                        if partial_text:
                            logger.debug(f"Partial: {partial_text}")

                    except Exception as e:
                        logger.error(f"Error in speech recognition loop: {e}")
                        # ADDED: Reset recognizer on error
                        try:
                            self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
                            self.recognizer.SetWords(True)
                            self.recognizer.SetPartialWords(True)
                            processed_frames = 0
                        except:
                            pass
                        break

            except ImportError:
                logger.error("PyAudio not installed. Run: pip install pyaudio")
                kivy.clock.Clock.schedule_once(lambda dt: self.callback(""), 0)
            except Exception as e:
                logger.error(f"Error in listen thread: {e}")
                kivy.clock.Clock.schedule_once(lambda dt: self.callback(""), 0)
            finally:
                self._cleanup_audio()
                logger.info("Stopped listening")

        thread = threading.Thread(target=listen_thread, daemon=True)
        thread.start()

    def _cleanup_audio(self):
        """
        Clean up audio resources safely.
        """
        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            except Exception:
                pass
            self.audio_stream = None

    def stop_listening(self):
        """Public method to stop listening and clean up."""
        self.is_listening = False
        self._cleanup_audio()