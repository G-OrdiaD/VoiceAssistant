import json
import logging
import threading
from typing import Optional, Callable
import os
import pyaudio
import vosk
import kivy


logger = logging.getLogger(__name__)


class SpeechToTextEngine:
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self.recognizer = None
        self.is_listening = False
        self.audio_stream = None
        self.callback = None
        self._load_model()

    def _load_model(self):
        """Load Vosk model with better error handling"""
        try:
            # Check if model path exists
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Vosk model not found at: {self.model_path}")

            logger.info(f"Loading Vosk model from: {self.model_path}")

            self.model = vosk.Model(self.model_path)
            self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
            self.recognizer.SetWords(True)
            self.recognizer.SetPartialWords(True)
            logger.info("Vosk model loaded successfully")

        except ImportError as e:
            logger.error("Vosk library not installed. Run: pip install vosk")
            raise
        except FileNotFoundError as e:
            logger.error(f"Model file error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading Vosk model: {e}")
            raise

    def start_listening(self, callback: Callable[[str], None]):
        """Start listening for speech with callback for results"""
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

                logger.info("Started listening for speech...")


                while self.is_listening:
                    try:
                        data = self.audio_stream.read(4096, exception_on_overflow=False)

                        if self.recognizer.AcceptWaveform(data):
                            result = json.loads(self.recognizer.Result())
                            text = result.get('text', '').strip()
                            if text:
                                logger.info(f"Recognized: {text}")
                                # Schedule callback on main thread to avoid recursion
                                if threading.current_thread() != threading.main_thread():
                                    kivy.clock.Clock.schedule_once(lambda dt: self.callback(text), 0)
                                else:
                                    self.callback(text)
                                break  # Stop listening after successful recognition

                        # Partial results for real-time feedback (optional)
                        partial = json.loads(self.recognizer.PartialResult())
                        partial_text = partial.get('partial', '').strip()
                        if partial_text:
                            logger.debug(f"Partial: {partial_text}")

                    except Exception as e:
                        logger.error(f"Error in speech recognition loop: {e}")
                        break

            except ImportError:
                logger.error("PyAudio not installed. Run: pip install pyaudio")
                # Schedule empty callback to continue flow
                kivy.clock.Clock.schedule_once(lambda dt: self.callback(""), 0)
            except Exception as e:
                logger.error(f"Error in listen thread: {e}")
                # Schedule empty callback to continue flow
                kivy.clock.Clock.schedule_once(lambda dt: self.callback(""), 0)
            finally:
                # Cleanup
                self._cleanup_audio()
                logger.info("Stopped listening")

        thread = threading.Thread(target=listen_thread, daemon=True)
        thread.start()

    def _cleanup_audio(self):
        """Clean up audio resources"""
        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            except:
                pass
            self.audio_stream = None

        # Note: I didn't terminate PyAudio here as it might be used again
        # This prevents the "PortAudio not initialized" error

    def stop_listening(self):
        """Stop listening for speech"""
        self.is_listening = False
        self._cleanup_audio()