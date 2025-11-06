import logging
from kivy.uix.screenmanager import Screen
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from kivy.clock import Clock
from kivy.metrics import dp
from .popups import SettingsConfirmationPopup


class SettingsScreen(Screen):
    # App-facing properties
    font_size = NumericProperty(20)
    font_family = StringProperty('Rubik')
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
        self.font_size = getattr(self.app, 'font_size', self.font_size)
        self.font_family = getattr(self.app, 'font_family', self.font_family)
        self.high_contrast = getattr(self.app, 'high_contrast', self.high_contrast)
        self.current_voice = getattr(self.app, 'current_voice', self.current_voice)
        self.voice_speed = getattr(self.app, 'voice_speed', self.voice_speed)

        # Update slider positions safely if ids exist
        if hasattr(self, 'ids'):
            if 'font_size_slider' in self.ids:
                self.ids.font_size_slider.value = self.font_size
            if 'voice_speed_slider' in self.ids:
                self.ids.voice_speed_slider.value = 1 if self.voice_speed == 'Normal' else (0 if self.voice_speed == 'Slow' else 2)
            if 'contrast_slider' in self.ids:
                self.ids.contrast_slider.value = 1 if self.high_contrast else 0
            if 'font_size_label' in self.ids:
                self.ids.font_size_label.text = f'{int(self.font_size)} Px'

    # ----- Handlers (KV binds to these) -----
    def on_font_size_change(self, _slider, value): # Change font size with live preview
        self.font_size = int(value)
        if hasattr(self, 'ids') and 'font_size_label' in self.ids:
            self.ids.font_size_label.text = f'{int(value)} Px'
        self.apply_font_preview()

    def on_font_family_change(self, _btn, text): # Change font with live preview
        self.font_family = text
        self.apply_font_preview()

    def _apply_font_preview(self): 
        """Apply font changes to settings screen for live preview"""
        if not hasattr(self, 'ids'):
            return

          # Update ALL text elements in settings screen
        for child in self.walk():
            if hasattr(child, 'font_name'):
                child.font_name = self.font_family
            if hasattr(child, 'font_size') and hasattr(child, 'text'):
                # Apply size changes to appropriate elements
                if any(keyword in child.text for keyword in ['SETTINGS', 'Font Type', 'Voice Type', 'Voice Speed', 'High-contrast']):
                    child.font_size = dp(self.font_size)

    def on_contrast_toggle(self, btn):
        """Backward-compat if you still use a ToggleButton somewhere."""
        self.high_contrast = (btn.state == 'down')
        btn.text = 'Enabled' if self.high_contrast else 'Disabled'

    def on_contrast_button(self, btn):
        """Toggle high contrast mode with button"""
        self.high_contrast = not self.high_contrast
        btn.text = 'ON' if self.high_contrast else 'OFF'

    def get_voice_labels(self):
        """Get dynamic voice labels based on available TTS voices"""
        from kivy.app import App
        try:
            app = App.get_running_app()
            if hasattr(app, 'tts_engine'):
                count = app.tts_engine.get_voice_count()
                return [f"Voice {i+1}" for i in range(count)]
        except:
            pass
        return ["Eddy", "Karen", "Tessa", "GrandPa"]

    def on_voice_change(self, _btn, voice_index: int):
        """Voice changed - use index directly"""
        self.current_voice = voice_index
        
        # Live preview with the actual voice
        if self.app and hasattr(self.app, 'tts_engine'):
            try:
                self.app.tts_engine.set_voice(voice_index)
                Clock.schedule_once(lambda dt: self.app.tts_engine.speak(f"Voice {voice_index + 1}"), 0.1)
            except Exception as e:
                logging.debug(f"Voice preview failed: {e}")

    def _preview_voice(self, voice_name):
        """Preview the selected voice after a short delay"""
        try:
            self.app.tts_engine.set_voice(self.current_voice)
            self.app.tts_engine.speak(f"This is voice {voice_name}")
        except Exception as e:
            logging.debug(f"Voice preview failed: {e}")

    def on_voice_speed_change(self, _spinner, text):
        """Backward-compat if you keep a Spinner somewhere."""
        self.voice_speed = text
        self._preview_speed(text)

    def on_voice_speed_slider(self, _slider, position: int):
        """Map 0/1/2 slider -> Slow/Normal/Fast."""
        mapped = {0: 'Slow', 1: 'Normal', 2: 'Fast'}.get(position, 'Normal')
        self.voice_speed = mapped
        self._preview_speed(mapped)

    def _preview_speed(self, speed_label: str):
        """Preview the selected speed, without permanently altering your base rate."""
        if not (self.app and hasattr(self.app, 'tts_engine')):
            return
        engine = self.app.tts_engine
        original_rate = getattr(engine, 'rate', 200)
        try:
            if speed_label == 'Slow':
                engine.set_rate(150) if hasattr(engine, 'set_rate') else setattr(engine, 'rate', 150)
            elif speed_label == 'Fast':
                engine.set_rate(250) if hasattr(engine, 'set_rate') else setattr(engine, 'rate', 250)
            else:
                engine.set_rate(200) if hasattr(engine, 'set_rate') else setattr(engine, 'rate', 200)
            engine.speak(f"This is {speed_label} speed")
        except Exception:
            pass
        finally:
            try:
                engine.set_rate(original_rate) if hasattr(engine, 'set_rate') else setattr(engine, 'rate', original_rate)
            except Exception:
                pass

    # ----- Actions -----
    def reset_to_default(self):
        self.font_size = 20
        self.font_family = 'Rubik' 
        self.high_contrast = False
        self.current_voice = 0
        self.voice_speed = 'Normal'

        # Update visible controls if present
        if hasattr(self, 'ids'):
            if 'font_size_slider' in self.ids:
                self.ids.font_size_slider.value = self.font_size
            if 'voice_speed_slider' in self.ids:
                self.ids.voice_speed_slider.value = 1
            if 'contrast_slider' in self.ids:
                self.ids.contrast_slider.value = 0
            if 'font_size_label' in self.ids:
                self.ids.font_size_label.text = f'{self.font_size} Px'

        # Confirmation popup
        popup = SettingsConfirmationPopup()
        popup.title = 'Default Settings'
        popup.confirmation_text = 'Default settings saved'
        popup.open()

    def save_settings(self):
        if self.app:
            self.app.font_size = self.font_size
            self.app.font_family = self.font_family
            self.app.high_contrast = self.high_contrast
            self.app.current_voice = self.current_voice
            self.app.voice_speed = self.voice_speed

            # Apply globally if your app exposes this
            if hasattr(self.app, 'apply_settings_globally'):
                try:
                    self.app.apply_settings_globally()
                except Exception:
                    logging.exception("apply_settings_globally failed")

            popup = SettingsConfirmationPopup()
            popup.confirmation_text = 'Settings saved'
            popup.open()

        logging.info(
            f"Settings saved - Font: {self.font_family} {self.font_size}px, "
            f"Contrast: {self.high_contrast}, Voice: {self.current_voice}, "
            f"Speed: {self.voice_speed}"
        )

    def go_back(self):
        if self.app and hasattr(self.app, 'show_main_screen'):
            self.app.show_main_screen()