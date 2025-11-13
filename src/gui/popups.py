import re
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.properties import StringProperty, NumericProperty


class BasePopup(Popup): # Base class for popups with common properties
    font_family = StringProperty('Rubik')
    font_size = NumericProperty(18)

class AddTaskPopup(BasePopup): # Popup to add a new task
    def __init__(self, save_callback, **kwargs):
        super().__init__(**kwargs)
        self.save_callback = save_callback
        self.app = None  # Will be set when popup opens

    def save_task(self): # Save the task and time input
        task_text = self.ids.task_input.text.strip()
        time_text = self.ids.time_input.text.strip()
        am_pm = self.ids.am_pm_spinner.text
        
        if task_text and time_text:
            if self.app and hasattr(self.app, 'command_parser'):
                formatted_task = self.app.command_parser.format_task_text(task_text)
            else:
                formatted_task = task_text  # Fallback if app not available
            full_time = f"{time_text} {am_pm}"
            self.save_callback(formatted_task, full_time)
            self.dismiss()

    def _validate_time(self, time_str): # Validate time format HH:MM
        pattern = r'^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$'
        return re.match(pattern, time_str) is not None


class ConfirmationPopup(BasePopup): # Popup to confirm task addition
    confirmation_text = StringProperty("")
    popup_title = StringProperty("Task Added!")
    
    def __init__(self, confirmation_text="", **kwargs):
        super().__init__(**kwargs)
        self.confirmation_text = confirmation_text
        if "title" in kwargs:
            self.popup_title = kwargs["title"]

class ListeningPopup(BasePopup): # Popup indicating listening state
    def __init__(self, dismiss_callback, **kwargs):
        super().__init__(**kwargs)
        self.dismiss_callback = dismiss_callback

    def on_dismiss(self):
        if self.dismiss_callback:
            self.dismiss_callback()


class SettingsConfirmationPopup(BasePopup): # Popup to confirm settings saved
    confirmation_text = StringProperty("Your settings successfully saved!")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Settings Saved'
        self.size_hint = (0.6, 0.4)


class DefaultSettingsPopup(BasePopup):
    confirmation_text = StringProperty("All settings reset to default values!")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Default Settings'
        self.size_hint = (0.6, 0.4)

class AlarmPopup(BasePopup): # Popup for active alarms
    def __init__(self, task, alarm_key, alarm_manager, **kwargs):
        
        self.task = task
        self.alarm_key = alarm_key
        self.alarm_manager = alarm_manager

        super().__init__(**kwargs)
        
    def dismiss_alarm(self):
        """Remove from active alarms and dismiss"""
        if self.alarm_key in self.alarm_manager.active_alarms:
            del self.alarm_manager.active_alarms[self.alarm_key]
        self.dismiss()