import logging
from kivy.uix.screenmanager import Screen
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.button import Button  # for font-size exclusion
from .popups import SettingsConfirmationPopup, DefaultSettingsPopup


class SettingsScreen(Screen):
    # App-facing properties
    font_size = NumericProperty()
    font_family = StringProperty()
    high_contrast = BooleanProperty(False)
    current_voice = NumericProperty(0)
    voice_speed = StringProperty('Normal')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        Clock.schedule_once(self._post_init, 0.1)

    # ----- Lifecycle / Sync -----
    def set_app_instance(self, app_instance):
        self.app = app_instance
        if self.app:
            self._sync_from_app()

    def _post_init(self, _dt):
        if self.app:
            self._sync_from_app()

    def _sync_from_app(self):
        """Pull current settings from the app object."""
        self.font_size = getattr(self.app, 'font_size', 20)
        self.font_family = getattr(self.app, 'font_family', 'Rubik')
        self.high_contrast = getattr(self.app, 'high_contrast', False)
        self.current_voice = getattr(self.app, 'current_voice', 0)
        self.voice_speed = getattr(self.app, 'voice_speed', 'Normal')

        if hasattr(self, 'ids'):
            if 'font_size_slider' in self.ids:
                self.ids.font_size_slider.value = self.font_size
            if 'voice_speed_slider' in self.ids:
                self.ids.voice_speed_slider.value = 1 if self.voice_speed == 'Normal' else (
                    0 if self.voice_speed == 'Slow' else 2
                )
            if 'contrast_btn' in self.ids:
                self.ids.contrast_btn.text = 'ON' if self.high_contrast else 'OFF'
            if 'font_size_label' in self.ids:
                self.ids.font_size_label.text = f'{int(self.font_size)} Px'

        # Apply preview to this screen only
        self.apply_font_preview()

    # ----- Handlers (KV binds to these) -----
    def on_font_size_change(self, _slider, value):
        """Change font size with live preview."""
        self.font_size = int(value)
        if hasattr(self, 'ids') and 'font_size_label' in self.ids:
            self.ids.font_size_label.text = f'{int(value)} Px'
        self.apply_font_preview()

    def on_font_family_change(self, _btn, text):
        """Change font family with live preview."""
        self.font_family = text
        self.apply_font_preview()

    def _apply_font_to_children(self):
        """
        Apply current font family + size to all child widgets on this screen.
        """
        if not self.app:
            return

        if not hasattr(self, 'walk'):
            return

        for child in self.walk():
            if hasattr(child, 'font_name') and self.font_family:
                child.font_name = self.font_family

            if (
                hasattr(child, 'font_size')
                and hasattr(child, 'text')
                and not isinstance(child, Button)
            ):
                child.font_size = dp(self.font_size)

    def apply_font_preview(self):
        """Live preview of font settings within SettingsScreen."""
        self._apply_font_to_children()

    def on_contrast_toggle(self, btn):
        """Toggle high contrast mode with toggle button."""
        self.high_contrast = (btn.state == 'down')
        btn.text = 'Enabled' if self.high_contrast else 'Disabled'

    def on_contrast_button(self, btn):
        """Toggle high contrast mode with simple ON/OFF button."""
        self.high_contrast = not self.high_contrast
        btn.text = 'ON' if self.high_contrast else 'OFF'

    def get_voice_labels(self):
        """Get dynamic voice labels based on available TTS voices."""
        from kivy.app import App

        try:
            app = App.get_running_app()
            if hasattr(app, 'tts_engine'):
                result = ["Eddy", "Karen", "Tessa", "GrandPa"]
                return result
            else:
                print("DEBUG: No tts_engine found")
        except Exception as e:
            print(f"DEBUG: Error in get_voice_labels: {e}")

        fallback = ["Eddy", "Karen", "Tessa", "GrandPa"]
        return fallback

    def on_voice_change(self, _btn, voice_index: int):
        """Voice changed - use index directly, with live preview."""
        self.current_voice = voice_index

        voice_names = self.get_voice_labels()
        voice_name = voice_names[voice_index] if voice_index < len(voice_names) else f"Voice {voice_index + 1}"

        if self.app and hasattr(self.app, 'tts_engine'):
            try:
                self.app.tts_engine.set_voice(voice_index)
                Clock.schedule_once(lambda dt: self.app.tts_engine.speak(f"This is {voice_name}"), 0.1)
            except Exception as e:
                logging.debug(f"Voice preview failed: {e}")

    def _preview_voice(self, voice_name):
        """Preview selected voice (kept for backward compatibility)."""
        try:
            self.app.tts_engine.set_voice(self.current_voice)
            self.app.tts_engine.speak(f"This is voice {voice_name}")
        except Exception as e:
            logging.debug(f"Voice preview failed: {e}")

    def on_voice_speed_change(self, _spinner, text):
        """Backward-compat if Spinner is used."""
        self.voice_speed = text
        self._preview_speed(text)

    def on_voice_speed_slider(self, _slider, position: int):
        """Map 0/1/2 slider -> Slow/Normal/Fast."""
        mapped = {0: 'Slow', 1: 'Normal', 2: 'Fast'}.get(position, 'Normal')
        self.voice_speed = mapped
        self._preview_speed(mapped)

    def _preview_speed(self, speed_label: str):
        """
        Preview the selected speed, without permanently altering base rate.
        """
        if not (self.app and hasattr(self.app, 'tts_engine')):
            return
        engine = self.app.tts_engine
        original_rate = getattr(engine, 'rate', 200)
        try:
            if speed_label == 'Slow':
                engine.set_rate(150)
            elif speed_label == 'Fast':
                engine.set_rate(250)
            else:
                engine.set_rate(200)
            engine.speak(f"This is {speed_label} speed")
        except Exception:
            pass
        finally:
            try:
                engine.set_rate(original_rate)
            except Exception:
                pass

    # ----- Actions -----
    def reset_to_default(self):
        """Reset all settings to their defaults and show a confirmation popup."""
        self.font_size = 20
        self.font_family = 'Rubik'
        self.high_contrast = False
        self.current_voice = 0
        self.voice_speed = 'Normal'

        if hasattr(self, 'ids'):
            if 'font_size_slider' in self.ids:
                self.ids.font_size_slider.value = self.font_size
            if 'voice_speed_slider' in self.ids:
                self.ids.voice_speed_slider.value = 1
            if 'contrast_btn' in self.ids:
                self.ids.contrast_btn.text = 'OFF'
            if 'font_size_label' in self.ids:
                self.ids.font_size_label.text = f'{self.font_size} Px'

        self.apply_font_preview()

        popup = DefaultSettingsPopup()
        popup.title = 'Default Settings'
        popup.confirmation_text = 'Default settings saved'
        popup.open()

        if self.app and getattr(self.app, 'tts_engine', None):
            self.app.tts_engine.speak("Default settings restored")

    def save_settings(self):
        """Persist settings to the app and apply globally."""
        if self.app:
            self.app.font_size = self.font_size
            self.app.font_family = self.font_family
            self.app.high_contrast = self.high_contrast
            self.app.current_voice = self.current_voice
            self.app.voice_speed = self.voice_speed

            try:
                self.app.apply_settings_globally()
            except Exception as e:
                logging.error(f"Error applying global settings: {e}")

            popup = SettingsConfirmationPopup()
            popup.open()

            if getattr(self.app, "tts_engine", None):
                self.app.tts_engine.speak("Settings saved")

        logging.info(
            f"Settings saved - Font: {self.font_family} {self.font_size}px, "
            f"Contrast: {self.high_contrast}, Voice: {self.current_voice}, "
            f"Speed: {self.voice_speed}"
        )

    def apply_settings(self, font_family, font_size, high_contrast):
        """
        Called from app.apply_settings_globally() to propagate settings
        back into this screen.
        """
        self.font_family = font_family
        self.font_size = font_size
        self.high_contrast = high_contrast
        self.apply_font_preview()

    def refresh_with_settings(self, font_family, font_size, high_contrast):
        self.apply_settings(font_family, font_size, high_contrast)

    def go_back(self):
        if self.app and hasattr(self.app, 'show_main_screen'):
            self.app.show_main_screen()