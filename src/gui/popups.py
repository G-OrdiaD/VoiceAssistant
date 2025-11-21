import re
import logging
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from kivy.uix.button import Button

logger = logging.getLogger(__name__)


class BasePopup(Popup):
    """
    Base class for popups with common font behaviour.

    - font_family and font_size come from app defaults.
    - on_open applies font family everywhere and font size to non-button text.
    """
    font_family = StringProperty('Rubik')
    font_size = NumericProperty(18)

    def on_open(self):
        """
        Apply global fonts to popup contents when opened.
        """
        try:
            from kivy.app import App

            app = App.get_running_app()
            if app:
                self.font_family = getattr(app, "font_family", "Rubik")
                self.font_size = getattr(app, "font_size", 18)
        except Exception:
            pass

        # Propagate font settings
        if hasattr(self, 'walk'):
            for child in self.walk():
                if hasattr(child, 'font_name') and self.font_family:
                    child.font_name = self.font_family

                if (
                    hasattr(child, 'font_size')
                    and hasattr(child, 'text')
                    and not isinstance(child, Button)
                ):
                    child.font_size = dp(self.font_size)


class AddTaskPopup(BasePopup):
    """Popup to add a new task manually."""
    def __init__(self, save_callback, **kwargs):
        super().__init__(**kwargs)
        self.save_callback = save_callback 
        self.app = None                   

    def save_task(self):
        """
        Save the task and time input.
        """
        task_text = self.ids.task_input.text.strip()
        time_text = self.ids.time_input.text.strip()
        am_pm = self.ids.am_pm_spinner.text

        if task_text and time_text:
            full_time = f"{time_text} {am_pm}"
            self.save_callback(task_text, full_time)
            self.dismiss()

    def _validate_time(self, time_str):
        """Validate time format HH:MM (kept for future use if needed)."""
        pattern = r'^([0-1]?[-9]|2[0-3]):([0-5][0-9])$'
        return re.match(pattern, time_str) is not None


class ConfirmationPopup(BasePopup):
    """Popup to confirm task addition or show messages."""
    confirmation_text = StringProperty("")
    popup_title = StringProperty("Confirmation")

    def __init__(self, confirmation_text="", **kwargs):
        super().__init__(**kwargs)
        self.confirmation_text = confirmation_text
        if "title" in kwargs:
            self.popup_title = kwargs["title"]


class ListeningPopup(BasePopup):
    """Popup indicating listening state."""
    def __init__(self, dismiss_callback, **kwargs):
        super().__init__(**kwargs)
        self.dismiss_callback = dismiss_callback

    def on_dismiss(self):
        if self.dismiss_callback:
            self.dismiss_callback()


class SettingsConfirmationPopup(BasePopup):
    """Popup to confirm settings saved."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class DefaultSettingsPopup(BasePopup):
    """Popup to confirm default settings restored."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class AlarmPopup(BasePopup):
    """
    Popup for active alarms.
    """
    task = ObjectProperty(None)
    alarm_key = StringProperty("")
    
    def __init__(self, task, alarm_key, alarm_manager, **kwargs):
        self.task = task
        self.alarm_key = alarm_key
        self.alarm_manager = alarm_manager
        super().__init__(**kwargs)

    def dismiss_alarm(self):
        """
        User has acknowledged the reminder.
        """
        if hasattr(self.alarm_manager, 'handle_alarm_dismiss'):
            self.alarm_manager.handle_alarm_dismiss(self.task, self.alarm_key)
        self.dismiss()