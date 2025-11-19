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
        self.app = None  # will be set from caller

    def save_task(self):
        """
        Save the task and time input.

        - Uses app.command_parser.format_task_text to keep titles consistent.
        """
        task_text = self.ids.task_input.text.strip()
        time_text = self.ids.time_input.text.strip()
        am_pm = self.ids.am_pm_spinner.text

        if task_text and time_text:
            if self.app and hasattr(self.app, 'command_parser'):
                formatted_task = self.app.command_parser.format_task_text(task_text)
            else:
                formatted_task = task_text

            full_time = f"{time_text} {am_pm}"
            self.save_callback(formatted_task, full_time)
            self.dismiss()

    def _validate_time(self, time_str):
        """Validate time format HH:MM (kept for future use if needed)."""
        pattern = r'^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$'
        return re.match(pattern, time_str) is not None


class ConfirmationPopup(BasePopup):
    """Popup to confirm task addition or show messages."""
    confirmation_text = StringProperty("")
    popup_title = StringProperty("Task Added!")

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
    confirmation_text = StringProperty("Your settings successfully saved!")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Settings Saved'
        self.size_hint = (0.6, 0.4)


class DefaultSettingsPopup(BasePopup):
    """Popup to confirm default settings restored."""
    confirmation_text = StringProperty("All settings reset to default values!")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Default Settings'
        self.size_hint = (0.6, 0.4)

class AlarmPopup(BasePopup):
    """
    Popup for active alarms.
    """
    task = ObjectProperty(None)
    alarm_key = StringProperty("")
    alarm_manager = ObjectProperty(None)

    def __init__(self, task, alarm_key, alarm_manager, **kwargs):
        self.task = task
        self.alarm_key = alarm_key
        self.alarm_manager = alarm_manager
        super().__init__(**kwargs)

    def dismiss_alarm(self):
        """
        User has acknowledged the reminder:
        - Mark task as done in DB
        - Refresh main and tasks screens
        - Remove from active alarms so it stops re-triggering
        - Dismiss popup
        """
        try:
            app = getattr(self.alarm_manager, 'app', None)

            if app and getattr(app, 'db_manager', None):
                # Mark completed
                app.db_manager.mark_done(self.task.id)

                # Refresh main screen
                try:
                    main_screen = app.screen_manager.get_screen('main')
                    if hasattr(main_screen, 'load_tasks'):
                        main_screen.load_tasks()
                except Exception:
                    pass

                # Refresh tasks screen
                try:
                    tasks_screen = app.screen_manager.get_screen('tasks')
                    if hasattr(tasks_screen, 'load_all_tasks'):
                        tasks_screen.load_all_tasks()
                except Exception:
                    pass

        except Exception as e:
            logging.error(f"Error in dismiss_alarm while marking done: {e}")

        # Remove from active alarms and dismiss
        try:
            if self.alarm_key in self.alarm_manager.active_alarms:
                del self.alarm_manager.active_alarms[self.alarm_key]
        except Exception as e:
            logging.error(f"Error cleaning active_alarms: {e}")

        self.dismiss()