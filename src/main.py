import logging
import sys
import os
import threading
import time
from datetime import datetime, timedelta

# import from our packages
from voice.stt_engine import SpeechToTextEngine
from gui.main_screen import MainScreen
from gui.tasks_screen import TasksScreen
from gui.settings_screen import SettingsScreen
from voice.tts_engine import TextToSpeechEngine
from voice.command_parser import CommandParser
from data.database import DatabaseManager

# Kivy imports
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.core.window import Window

# Set minimum window size
Window.size = (550, 800)
Window.minimum_width, Window.minimum_height = 550, 800

# Setup and Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('voice_assistant.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Ensure local packages are discoverable
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data'))
current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)


def register_application_fonts():
    try:
        abs_current_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(os.path.dirname(abs_current_dir), 'assets')

        rubik_dir = os.path.join(assets_dir, 'fonts', 'Rubik', 'static')
        rubik_regular = os.path.join(rubik_dir, 'Rubik-Regular.ttf')
        rubik_bold = os.path.join(rubik_dir, 'Rubik-Bold.ttf')
        rubik_italic = os.path.join(rubik_dir, 'Rubik-Italic.ttf')
        rubik_bolditalic = os.path.join(rubik_dir, 'Rubik-BoldItalic.ttf')

        arial_dir = os.path.join(assets_dir, 'fonts', 'arial')
        arial_regular = os.path.join(arial_dir, 'arial.ttf')
        arial_bold = os.path.join(arial_dir, 'arialbd.ttf')
        arial_italic = os.path.join(arial_dir, 'arialceitalic.ttf')

        balsamiq_dir = os.path.join(assets_dir, 'fonts', 'Balsamiq_Sans')
        balsamiq_regular = os.path.join(balsamiq_dir, 'BalsamiqSans-Regular.ttf')
        balsamiq_bold = os.path.join(balsamiq_dir, 'BalsamiqSans-Bold.ttf')
        balsamiq_italic = os.path.join(balsamiq_dir, 'BalsamiqSans-Italic.ttf')
        balsamiq_bolditalic = os.path.join(balsamiq_dir, 'BalsamiqSans-BoldItalic.ttf')

        crimson_dir = os.path.join(assets_dir, 'fonts', 'Crimson_pro', 'static')
        crimson_regular = os.path.join(crimson_dir, 'CrimsonPro-Regular.ttf')
        crimson_bold = os.path.join(crimson_dir, 'CrimsonPro-Bold.ttf')
        crimson_italic = os.path.join(crimson_dir, 'CrimsonPro-Italic.ttf')
        crimson_black = os.path.join(crimson_dir, 'CrimsonPro-Black.ttf')

        print("🔍 Checking font paths:")
        print(f"Rubik Regular: {os.path.exists(rubik_regular)}")
        print(f"Arial Regular: {os.path.exists(arial_regular)}")
        print(f"Balsamiq Sans Regular: {os.path.exists(balsamiq_regular)}")
        print(f"Crimson Pro Regular: {os.path.exists(crimson_regular)}")

        LabelBase.register(
            name='Rubik',
            fn_regular=rubik_regular,
            fn_bold=rubik_bold,
            fn_italic=rubik_italic,
            fn_bolditalic=rubik_bolditalic
        )
        print("✅ Rubik font registered")

        LabelBase.register(
            name='Arial',
            fn_regular=arial_regular,
            fn_bold=arial_bold,
            fn_italic=arial_italic
        )
        print("✅ Arial font registered")

        LabelBase.register(
            name='BalsamiqSans',
            fn_regular=balsamiq_regular,
            fn_bold=balsamiq_bold,
            fn_italic=balsamiq_italic,
            fn_bolditalic=balsamiq_bolditalic
        )
        print("✅ BalsamiqSans font registered")

        LabelBase.register(
            name='CrimsonPro',
            fn_regular=crimson_regular,
            fn_bold=crimson_bold,
            fn_italic=crimson_italic,
            fn_bolditalic=crimson_black
        )
        print("✅ CrimsonPro font registered")
        return True

    except Exception as e:
        print(f"❌ Failed to register fonts: {e}")
        return False

# Register application fonts
font_registered = register_application_fonts()

print("✅ Registered fonts:", LabelBase._fonts.keys())

# If fonts failed to register, use system fonts as fallback
if not font_registered:
    print("⚠️ Using system fonts as fallback")

# Load KV files after font registration
Builder.load_file('gui/main_screen.kv')
Builder.load_file('gui/tasks_screen.kv')
Builder.load_file('gui/settings_screen.kv')
Builder.load_file('gui/popups.kv')

class VoiceAssistantApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = None
        self.db_manager = None
        self.stt_engine = None
        self.tts_engine = None
        self.command_parser = None
        self.alarm_manager = None
        self.font_family = 'Rubik'
        self.font_size = 20
        self.high_contrast = False
        self.current_voice = 0
        self.voice_speed = 'Normal'
        self._schedule_daily_reset()


    def _initialize_components(self):
        try:
            db_path = os.path.join(os.path.dirname(__file__), 'data', 'tasks.db')
            self.db_manager = DatabaseManager(db_path)
            model_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'models', 'vosk-model-small-en-gb-0.15')
            self.stt_engine = SpeechToTextEngine(model_path)
            self.tts_engine = TextToSpeechEngine()
            self.command_parser = CommandParser()
            self.alarm_manager = AlarmManager(self)
            logging.info("All components initialized successfully")
            return True
        except Exception as e:
            logging.error("Failed to initialize components: %s", e)
            return False

    def build(self): # Build the main application
        Window.clearcolor = (1, 1, 1, 1)

        self.screen_manager = ScreenManager()

        if not self._initialize_components():
            error_screen = Screen(name='error')
            error_layout = BoxLayout(orientation='vertical', padding=20)
            error_layout.add_widget(Label(
                text="Setup Error\n\nPlease check console logs",
                font_size=20,
                text_size=(400, None)
            ))
            error_screen.add_widget(error_layout)
            self.screen_manager.add_widget(error_screen)
            return self.screen_manager

        main_screen = MainScreen(name='main')
        tasks_screen = TasksScreen(name='tasks')
        settings_screen = SettingsScreen(name='settings')

        main_screen.set_app_instance(self)
        tasks_screen.set_app_instance(self)
        settings_screen.set_app_instance(self)

        self.screen_manager.add_widget(main_screen)
        self.screen_manager.add_widget(tasks_screen)
        self.screen_manager.add_widget(settings_screen)

        return self.screen_manager


    def on_start(self):
        if self.alarm_manager:
            self.alarm_manager.start()

    def show_main_screen(self):
        """Show the main screen"""
        self.screen_manager.current = 'main'
        # Refresh tasks when returning to main screen
        main_screen = self.screen_manager.get_screen('main')
        if hasattr(main_screen, 'load_tasks'):
            main_screen.load_tasks()

    def show_tasks_screen(self):
        """Show all tasks screen"""
        self.screen_manager.current = 'tasks'
        # Refresh tasks list
        tasks_screen = self.screen_manager.get_screen('tasks')
        if hasattr(tasks_screen, 'load_all_tasks'):
            tasks_screen.load_all_tasks()

    def show_settings_screen(self):
        """Show settings screen"""
        self.screen_manager.current = 'settings'


    def apply_settings_globally(self):  # apply settings across all screens
        """Apply current settings to all screens"""
        for screen_name in ['main', 'tasks', 'settings']:
            screen = self.screen_manager.get_screen(screen_name)
            if hasattr(screen, 'apply_settings'):
                screen.apply_settings(self.font_family, self.font_size, self.high_contrast)

    def _schedule_daily_reset(self):
        def reset_tasks():
            while True:
                try:
                    now = datetime.now()
                    next_midnight = (now + timedelta(days=1)).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    sleep_seconds = (next_midnight - now).total_seconds()
                    logging.info(f"Daily reset scheduled in {sleep_seconds:.0f} seconds")
                    time.sleep(sleep_seconds)

                    self._reset_all_tasks()
                    logging.info("Daily fresh start: All tasks cleared at midnight")

                except Exception as e:
                    logging.error(f"Daily reset error: {e}")
                    time.sleep(3600)

        reset_thread = threading.Thread(target=reset_tasks, daemon=True)
        reset_thread.start()

    def _reset_all_tasks(self):
        try:
            if self.db_manager:
                tasks = self.db_manager.get_all_tasks()
                tasks_cleared = len(tasks)

                for task in tasks:
                    self.db_manager.delete_task(task.id)

                Clock.schedule_once(lambda dt: self._update_ui_after_reset(tasks_cleared))
                logging.info(f"Midnight Reset: Cleared {tasks_cleared} tasks at midnight")
        except Exception as e:
            logging.error(f"Error in midnight reset: {e}")

    def _update_ui_after_reset(self, tasks_cleared):
        main_screen = self.screen_manager.get_screen('main')
        if hasattr(main_screen, 'load_tasks'):
            main_screen.load_tasks()

        if self.screen_manager.current == 'tasks':
            tasks_screen = self.screen_manager.get_screen('tasks')
            if hasattr(tasks_screen, 'load_all_tasks'):
                tasks_screen.load_all_tasks()

    def on_stop(self): # Clean up resources on app exit
        if self.stt_engine:
            self.stt_engine.stop_listening()
        if self.tts_engine:
            self.tts_engine.stop()
        if self.alarm_manager:
            self.alarm_manager.stop()


class AlarmManager:
    def __init__(self, app):
        self.app = app
        self.running = False
        self.alarm_thread = None
        self.active_alarms = {}

    def start(self):
        if self.running:
            return

        self.running = True
        self.alarm_thread = threading.Thread(target=self._monitor_tasks, daemon=True)
        self.alarm_thread.start()
        logging.info("Alarm system started")

    def stop(self):
        self.running = False
        if self.alarm_thread:
            self.alarm_thread.join(timeout=1.0)
        logging.info("Alarm system stopped")

    def _monitor_tasks(self):
        while self.running:
            try:
                current_time = self._get_current_time()
                tasks = self.app.db_manager.get_all_tasks()

                for task in tasks:
                    if self._should_trigger_alarm(task, current_time):
                        self._trigger_alarm(task)

                time.sleep(30)

            except Exception as e:
                logging.error(f"Alarm monitor error: {e}")
                time.sleep(60)

    def _get_current_time(self):
        now = datetime.now()
        return now.strftime("%I:%M %p").upper().replace(' 0', ' ')

    def _should_trigger_alarm(self, task, current_time):
        task_time = task.due_time.upper().strip()
        current_time = current_time.strip()

        alarm_key = f"{task.id}_{task_time}"

        if alarm_key in self.active_alarms:
            return False

        task_time_clean = task_time.replace(' ', '')
        current_time_clean = current_time.replace(' ', '')

        return task_time_clean == current_time_clean

    def _trigger_alarm(self, task):
        alarm_key = f"{task.id}_{task.due_time.upper().strip()}"
        self.active_alarms[alarm_key] = True
        Clock.schedule_once(lambda dt: self._show_alarm_popup(task, alarm_key))

    def _show_alarm_popup(self, task, alarm_key):
        try:
            from gui.popups import AlarmPopup

            alarm_popup = AlarmPopup(task=task, alarm_key=alarm_key, alarm_manager=self)

            Clock.schedule_once(lambda dt: alarm_popup.dismiss_alarm(), 30)

            alarm_popup.open()

            if getattr(self.app, "tts_engine", None):
                try:
                    self.app.tts_engine.speak(
                        f"Reminder. {task.title} at {task.due_time}"
                    )
                except Exception as e:
                    logging.error(f"Error in alarm TTS: {e}")

            def retrigger_if_active(dt):
                if alarm_key in self.active_alarms:
                    logging.info(f"Re-triggering alarm for task: {task.title}")
                    self._show_alarm_popup(task, alarm_key)

            Clock.schedule_once(retrigger_if_active, 300)

        except Exception as e:
            logging.error(f"Error showing alarm popup: {e}")


if __name__ == '__main__':
    VoiceAssistantApp().run()