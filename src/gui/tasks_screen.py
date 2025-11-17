import logging
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.clock import Clock
from kivy.metrics import dp

logger = logging.getLogger(__name__)


class TaskListItem(BoxLayout):
    __events__ = ('on_delete', 'on_complete')
    text = StringProperty("")
    task_id = NumericProperty(0)
    font_size = NumericProperty()
    font_family = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def delete_task(self):
        self.dispatch('on_delete', self.task_id)

    def on_delete(self, *args):
        pass

    def mark_done(self):
        self.dispatch('on_complete', self.task_id)

    def on_complete(self, *args):
        pass


class TasksScreen(Screen):
    font_size = NumericProperty()
    font_family = StringProperty()
    high_contrast = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        Clock.schedule_once(self._post_init, 0.1)

    def set_app_instance(self, app_instance):
        self.app = app_instance
        if self.app:
            self.font_family = self.app.font_family
            self.font_size = self.app.font_size
            self.high_contrast = self.app.high_contrast

    def _post_init(self, dt):
        if self.app:
            self.load_all_tasks()
        Clock.schedule_once(lambda _dt: self._apply_font_to_children(), 0.2)

    def _apply_font_to_children(self):
        """
        Apply font family and size across TasksScreen.
        - font_family applies everywhere
        - font_size does not affect Buttons or labels inside Buttons
        """
        if not hasattr(self, 'walk'):
            return

        for child in self.walk():
            # Apply font family everywhere
            if hasattr(child, 'font_name') and self.font_family:
                child.font_name = self.font_family

            # Apply font size except on Buttons and their direct child labels
            if (
                hasattr(child, 'font_size')
                and hasattr(child, 'text')
                and not isinstance(child, Button)
                and not isinstance(getattr(child, 'parent', None), Button)
            ):
                child.font_size = dp(self.font_size)

    def load_all_tasks(self):
        if not self.app:
            return
        try:
            tasks = self.app.db_manager.get_all_tasks()
            tasks = self.sort_tasks_by_time(tasks)
            # Only display non-completed tasks
            tasks = [t for t in tasks if not t.is_completed]
            self.update_tasks_display(tasks)
        except Exception as e:
            logging.error(f"Error loading tasks: {e}")

    def sort_tasks_by_time(self, tasks):
        def time_to_minutes(time_str: str) -> int:
            try:
                t = time_str.upper().replace(' ', '')
                if 'AM' in t or 'PM' in t:
                    part = t.replace('AM', '').replace('PM', '')
                    hours, minutes = map(int, part.split(':'))
                    if 'PM' in t and hours != 12:
                        hours += 12
                    if 'AM' in t and hours == 12:
                        hours = 0
                    return hours * 60 + minutes
                else:
                    hours, minutes = map(int, t.split(':'))
                    return hours * 60 + minutes
            except Exception:
                return 0

        return sorted(tasks, key=lambda x: time_to_minutes(x.due_time))

    def update_tasks_display(self, tasks):
        if not hasattr(self, 'ids') or 'all_tasks_grid' not in self.ids:
            return

        grid = self.ids.all_tasks_grid
        grid.clear_widgets()

        if not tasks:
            empty_label = Label(
                text="No tasks yet",
                font_size=dp(self.font_size),
                font_name=self.font_family,
                color=(0.5, 0.5, 0.5, 1),
                size_hint_y=None,
                height=dp(100),
                halign='center'
            )
            grid.add_widget(empty_label)
            return

        for task in tasks:
            item = TaskListItem(
                text=f"{task.title}\nAt: {task.due_time}",
                task_id=task.id,
                font_family=self.font_family,
                font_size=self.font_size
            )
            item.bind(on_delete=self.delete_task)
            item.bind(on_complete=self.mark_done)
            grid.add_widget(item)

    def delete_task(self, instance, task_id):
        if not self.app:
            return
        try:
            if self.app.db_manager.delete_task(task_id):
                self.load_all_tasks()

                # Keep MainScreen in sync
                try:
                    main_screen = self.app.screen_manager.get_screen('main')
                    if hasattr(main_screen, 'load_tasks'):
                        main_screen.load_tasks()
                except Exception:
                    pass

                if getattr(self.app, "tts_engine", None):
                    self.app.tts_engine.speak("Task deleted")
            else:
                if getattr(self.app, "tts_engine", None):
                    self.app.tts_engine.speak("Error deleting task")
        except Exception as e:
            logging.error(f"Error deleting task: {e}")
            if getattr(self.app, "tts_engine", None):
                self.app.tts_engine.speak("Could not delete task")

    def mark_done(self, instance, task_id):
        """Mark a task as completed from the all-tasks screen."""
        if not self.app:
            return
        try:
            if self.app.db_manager.mark_done(task_id):
                self.load_all_tasks()

                # Keep MainScreen in sync
                try:
                    main_screen = self.app.screen_manager.get_screen('main')
                    if hasattr(main_screen, 'load_tasks'):
                        main_screen.load_tasks()
                except Exception:
                    pass

                if getattr(self.app, "tts_engine", None):
                    self.app.tts_engine.speak("Task Done")
            else:
                if getattr(self.app, "tts_engine", None):
                    self.app.tts_engine.speak("Error completing task")
        except Exception as e:
            logging.error(f"Error completing task: {e}")
            if getattr(self.app, "tts_engine", None):
                self.app.tts_engine.speak("Could not complete task")

    def go_to_settings(self):
        if hasattr(self, 'manager'):
            self.manager.current = 'settings'

    def apply_settings(self, font_family, font_size, high_contrast):
        """Apply settings to TasksScreen."""
        print(f"🔧 TasksScreen: Applying settings - {font_family} {font_size}px, Contrast: {high_contrast}")
        self.font_family = font_family
        self.font_size = font_size
        self.high_contrast = high_contrast
        self._apply_font_to_children()
        self.load_all_tasks()

    def refresh_with_settings(self, font_family, font_size, high_contrast):
        self.apply_settings(font_family, font_size, high_contrast)

    def go_back(self):
        if self.app:
            self.app.show_main_screen()

    def on_enter(self):
        self.load_all_tasks()
