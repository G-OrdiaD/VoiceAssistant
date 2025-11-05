import logging
import re
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.properties import ListProperty, StringProperty, NumericProperty, BooleanProperty
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.animation import Animation
from .popups import AddTaskPopup, ConfirmationPopup, ListeningPopup

class TaskItem(BoxLayout):
    __events__ = ('on_delete', 'on_complete')
    text = StringProperty("")
    task_id = NumericProperty(0)
    font_family = StringProperty('Rubik')  
    font_size = NumericProperty(20)    

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def delete_task(self):
        self.dispatch('on_delete', self.task_id)

    def on_delete(self, *args):
        pass

    def mark_complete_task(self):
        self.dispatch('on_complete', self.task_id)

    def on_complete(self, *args):
        pass

class MainScreen(Screen):
    tasks = ListProperty([])
    font_size = NumericProperty(20)  
    font_family = StringProperty('Rubik')  
    high_contrast = BooleanProperty(False) 

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        self.listening_popup = None
        Clock.schedule_once(self._post_init, 0.1)
        self.pending_task = None
        self.speak_animation = None

    def set_app_instance(self, app_instance):
        self.app = app_instance

    def _post_init(self, dt):
        if self.app:
            self.load_tasks()
        Clock.schedule_once(lambda dt: self.animate_speak_button(), 0.5)

    def animate_speak_button(self):
        if not hasattr(self, 'ids') or 'speak_button' not in self.ids:
            return

        speak_button = self.ids.speak_button
        if self.speak_animation:
            self.speak_animation.cancel(speak_button)

        self.speak_animation = (
            Animation(size=(dp(160), dp(160)), duration=1.5, t='out_elastic') +
            Animation(size=(dp(140), dp(140)), duration=1.5, t='out_elastic')
        )
        self.speak_animation.repeat = True
        self.speak_animation.start(speak_button)

    def load_tasks(self):
        if not self.app:
            return
        try:
            tasks = self.app.db_manager.get_all_tasks()
            self.tasks = self.sort_tasks_by_time(tasks)
            self.update_tasks_display()
        except Exception as e:
            logging.error(f"Error loading tasks: {e}")

    def sort_tasks_by_time(self, tasks):
        def time_to_minutes(time_str):
            try:
                time_str = time_str.upper().replace(' ', '')
                if 'AM' in time_str or 'PM' in time_str:
                    time_part = time_str.replace('AM', '').replace('PM', '')
                    hours, minutes = map(int, time_part.split(':'))
                    if 'PM' in time_str and hours != 12:
                        hours += 12
                    if 'AM' in time_str and hours == 12:
                        hours = 0
                    return hours * 60 + minutes
                else:
                    hours, minutes = map(int, time_str.split(':'))
                    return hours * 60 + minutes
            except:
                return 0
        
        return sorted(tasks, key=lambda x: time_to_minutes(x.due_time))

    def show_settings(self):
        if self.app:
            self.app.show_settings_screen()

    def apply_settings(self, font_family, font_size, high_contrast):
        print(f"🔧 MainScreen: Applying settings - {font_family} {font_size}px, Contrast: {high_contrast}")
       
        self.font_family = font_family
        self.font_size = font_size
        self.high_contrast = high_contrast
        self.load_tasks()

    def refresh_with_settings(self, font_family, font_size, high_contrast):
        self.apply_settings(font_family, font_size, high_contrast)

    def update_tasks_display(self):
        if not hasattr(self, 'ids') or 'tasks_grid' not in self.ids:
            return

        self.ids.tasks_grid.clear_widgets()

        if not self.tasks:
            empty_label = Label(
                text="No tasks yet\nPress the microphone or 'Add Task' to create one",
                font_size=dp(self.font_size),  
                font_name=self.font_family,  
                color=(0.5, 0.5, 0.5, 1),
                size_hint_y=None,
                height=dp(100),
                text_size=(None, None),
                halign='center'
            )
            self.ids.tasks_grid.add_widget(empty_label)
            return

        for task in self.tasks[:3]:  # Show only first 3 tasks on main screen
            task_item = TaskItem(
                text=f"{task.title}\nAt: {task.due_time}",
                task_id=task.id
            )
            task_item.bind(on_delete=self.delete_task)
            task_item.bind(on_complete=self.mark_complete_task)
            self.ids.tasks_grid.add_widget(task_item)

    def mark_complete_task(self, instance, task_id):
        if not self.app:
            return
        try:
            if self.app.db_manager.mark_done(task_id):
                self.load_tasks()
                if getattr(self.app, "tts_engine", None):
                    self.app.tts_engine.speak("Task Done")
            else:
                if getattr(self.app, "tts_engine", None):
                    self.app.tts_engine.speak("Error completing task")
        except Exception as e:
            logging.error(f"Error completing task: {e}")
            if getattr(self.app, "tts_engine", None):
                self.app.tts_engine.speak("Could not complete task")

    def start_voice_command(self):
        if not self.app:
            return
        self.listening_popup = ListeningPopup(dismiss_callback=self.cancel_listening)
        self.listening_popup.open()
        self.app.stt_engine.start_listening(self.on_voice_command)

    def cancel_listening(self):
        if self.app and self.app.stt_engine:
            self.app.stt_engine.stop_listening()
        self.listening_popup = None

    def on_voice_command(self, text):
        Clock.schedule_once(lambda dt: self._process_voice_command(text), 0)

    def _process_voice_command(self, text):
        if self.listening_popup:
            self.listening_popup.dismiss()
            self.listening_popup = None

        if not text or not text.strip():
            logging.warning("Empty voice command received")
            return

        logging.info(f"Processing voice command: '{text}'")

        if not self.app:
            return

        result = self.app.command_parser.parse_task_command(text)

        if result:
            command_type, data = result

            if command_type == "LIST_TASKS":
                self._handle_list_tasks_command()
            elif command_type == "DELETE_TASK":
                self._handle_delete_task_command(data)
            else:
                task, time = result
                self.create_task(task, time, text)
        else:
            error_popup = ConfirmationPopup(
                confirmation_text=f"I didn't understand: '{text}'\n\nTry: 'Take a Walk by 10 AM'"
            )
            error_popup.title = 'Not Understood'
            error_popup.open()
            self.app.tts_engine.speak("Sorry, I didn't understand. Please try again.")

    def _handle_list_tasks_command(self):
        if not self.app:
            return

        tasks = self.app.db_manager.get_all_tasks()
        if not tasks:
            self.app.tts_engine.speak("You have no tasks.")
            return

        task_text = "Here are your tasks: "
        for i, task in enumerate(tasks, 1):
            task_text += f"Task {i}: {task.title} at {task.due_time}. "

        self.app.tts_engine.speak(task_text)

    def _handle_delete_task_command(self, task_to_delete):
        if not self.app:
            return

        tasks = self.app.db_manager.get_all_tasks()
        found_task = None

        task_to_delete_lower = task_to_delete.lower()
        for task in tasks:
            if task_to_delete_lower in task.title.lower():
                found_task = task
                break

        if found_task:
            if self.app.db_manager.delete_task(found_task.id):
                self.app.tts_engine.speak(f"Deleted task for {found_task.title}")
                self.load_tasks()
            else:
                self.app.tts_engine.speak("Error deleting task")
        else:
            self.app.tts_engine.speak(f"Could not find a task for {task_to_delete}")

    def create_task(self, task, time, original_text=""):
        if not self.app:
            return
        try:
            if self.app.db_manager.add_task(task, time):
                confirmation_text = f"Task added!\n\n{task}\nAt: {time}"
                confirmation_popup = ConfirmationPopup(confirmation_text=confirmation_text)
                confirmation_popup.open()

                speak_text = f"Task added: {task} at {time}"
                self.app.tts_engine.speak(speak_text)

                self.load_tasks()
                logging.info(f"Task created: {task} at {time}")
            else:
                error_popup = ConfirmationPopup(confirmation_text="Could not save task. Please try again.")
                error_popup.title = 'Error'
                error_popup.open()
                self.app.tts_engine.speak("Error saving task")

        except Exception as e:
            logging.error(f"Error creating task: {e}")
            error_popup = ConfirmationPopup(confirmation_text="There was an error creating your task.")
            error_popup.title = 'Error'
            error_popup.open()
            self.app.tts_engine.speak("Error creating task")

    def delete_task(self, instance, task_id):
        if not self.app:
            return
        try:
            if self.app.db_manager.delete_task(task_id):
                self.load_tasks()
                self.app.tts_engine.speak("Task deleted")
            else:
                self.app.tts_engine.speak("Error deleting task")
        except Exception as e:
            logging.error(f"Error deleting task: {e}")
            self.app.tts_engine.speak("Could not delete task")

    def show_all_tasks(self):
        if self.app:
            self.app.show_tasks_screen()

    def add_manual_task(self):
        if not self.app:
            return

        add_task_popup = AddTaskPopup(save_callback=self.create_task)
        add_task_popup.open()