import re
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.properties import StringProperty, NumericProperty


class BasePopup(Popup):
    font_family = StringProperty('Rubik')
    font_size = NumericProperty(18)


class AddTaskPopup(BasePopup):
    def __init__(self, save_callback, **kwargs):
        super().__init__(**kwargs)
        self.save_callback = save_callback

    def save_task(self):
        task = self.ids.task_input.text.strip()
        time_part = self.ids.time_input.text.strip()
        am_pm = self.ids.am_pm_spinner.text
        
        if task and time_part:
            if self._validate_time(time_part):
                full_time = f"{time_part} {am_pm}"
                self.save_callback(task, full_time)
                self.dismiss()
            else:
                pass

    def _validate_time(self, time_str):
        pattern = r'^([0-1]?[0-9]|2[0-3]):([0-5][0-9])$'
        return re.match(pattern, time_str) is not None


class ConfirmationPopup(BasePopup):
    confirmation_text = StringProperty("")
    popup_title = StringProperty("Task Added!")
    
    def __init__(self, confirmation_text="", **kwargs):
        super().__init__(**kwargs)
        self.confirmation_text = confirmation_text
        if "title" in kwargs:
            self.popup_title = kwargs["title"]


class ListeningPopup(BasePopup):
    def __init__(self, dismiss_callback, **kwargs):
        super().__init__(**kwargs)
        self.dismiss_callback = dismiss_callback

    def on_dismiss(self):
        if self.dismiss_callback:
            self.dismiss_callback()


class SettingsConfirmationPopup(BasePopup):
    confirmation_text = StringProperty("Your settings successfully saved!")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = 'Settings Saved'
        self.size_hint = (0.6, 0.4)


class AlarmPopup(Popup):
    def __init__(self, task, alarm_key, alarm_manager, **kwargs):
        super().__init__(**kwargs)
        self.task = task
        self.alarm_key = alarm_key
        self.alarm_manager = alarm_manager
        
    def dismiss_alarm(self):
        """Remove from active alarms and dismiss"""
        if self.alarm_key in self.alarm_manager.active_alarms:
            del self.alarm_manager.active_alarms[self.alarm_key]
        self.dismiss()