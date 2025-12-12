import logging
import os
import threading
import time
from datetime import datetime, timedelta

# Ensure local packages are defined early based on project structure
current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)

# import from our packages using relative imports
from .voice.stt_engine import SpeechToTextEngine
from .gui.main_screen import MainScreen
from .gui.tasks_screen import TasksScreen
from .gui.settings_screen import SettingsScreen
from .voice.tts_engine import TextToSpeechEngine
from .voice.command_parser import CommandParser
from .data.database import DatabaseManager
from .security import SecurityManager
from .gui.popups import AlarmPopup

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


# Font registration
def register_application_fonts():
    """
    Register all application fonts.
    """
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

        LabelBase.register(
            name='Arial',
            fn_regular=arial_regular,
            fn_bold=arial_bold,
            fn_italic=arial_italic
        )

        LabelBase.register(
            name='BalsamiqSans',
            fn_regular=balsamiq_regular,
            fn_bold=balsamiq_bold,
            fn_italic=balsamiq_italic,
            fn_bolditalic=balsamiq_bolditalic
        )

        LabelBase.register(
            name='CrimsonPro',
            fn_regular=crimson_regular,
            fn_bold=crimson_bold,
            fn_italic=crimson_italic,
            fn_bolditalic=crimson_black
        )
        return True

    except Exception as e:
        print(f"❌ Failed to register fonts: {e}")
        return False


# Register application fonts
font_registered = register_application_fonts()
print("✅ Registered fonts:", LabelBase._fonts.keys())

if not font_registered:
    print("⚠️ Using system fonts as fallback")



class AlarmManager:
    """
    Monitors tasks and triggers alarms at the right due_time.
    """
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
        """
        Return current time as a string like '6:35 PM'
        (no leading zero on hour, AM/PM in upper case).
        """
        now = datetime.now()
        return now.strftime("%I:%M %p").lstrip("0").upper() # '%I' gives 01–12, lstrip('0') removes leading 0 for 01–09


    def _should_trigger_alarm(self, task, current_time):
        """
        Decide whether to trigger an alarm for this task at current_time.

        Supports formats like:
        - '06:35 PM', '6:35PM', '06:35PM', '6:35 pm', '6 PM'
        """
        task_time_raw = (task.due_time or " ").upper().strip()
        current_time_raw = (current_time or " ").upper().strip()

        # Use the same alarm key style used in _trigger_alarm
        alarm_key = f"{task.id}_{task_time_raw}"

        # Already active alarm? Then don't re-trigger from here.
        if alarm_key in self.active_alarms:
            return False

        def to_minutes(t_str: str):
            """
            Convert a time string to minutes since midnight.
            Returns None if parsing fails.

            Handles:
            - '6:35 PM', '06:35 PM', '6:35PM', '06:35PM', '6:35 pm'
            - '6 PM'
            - '18:35'
            """
            if not t_str:
                return None

            s = str(t_str).strip().upper()
            s = s.replace(" ", "")  # Remove inner spaces: '6:35 PM' -> '6:35PM', '6 pm' -> '6PM'

            formats = ["%I:%M%p", "%I%p", "%H:%M", "%H"] # Try several possible formats
            for fmt in formats:
                try:
                    dt = datetime.strptime(s, fmt)
                    return dt.hour * 60 + dt.minute
                except ValueError:
                    continue

            logging.warning(f"Could not parse time string for alarm: '{t_str}' (normalized: '{s}')")
            return None

        try:
            task_minutes = to_minutes(task_time_raw)
            current_minutes = to_minutes(current_time_raw)

            if task_minutes is None or current_minutes is None:
                return False

            return task_minutes == current_minutes

        except Exception as e:
            logging.error(f"Error in _should_trigger_alarm: {e}")
            return False

    def _trigger_alarm(self, task):
        alarm_key = f"{task.id}_{task.due_time.upper().strip()}"
        self.active_alarms[alarm_key] = True

        Clock.schedule_once(lambda dt: self._show_alarm_popup(task, alarm_key))

    def _show_alarm_popup(self, task, alarm_key):
        """
        Show alarm popup and speak the reminder.
        TTS is wrapped with error handling to avoid crashing on PaMacCore issues.
        """
        try:
            from .gui.popups import AlarmPopup

            alarm_popup = AlarmPopup(task=task, alarm_key=alarm_key, alarm_manager=self)
            alarm_popup.open()

            # Auto-dismiss after 30 seconds if not acknowledged
            Clock.schedule_once(lambda dt: alarm_popup.dismiss(), 30)

            if getattr(self.app, "tts_engine", None):
                try:
                    self.app.tts_engine.speak(
                        f"Reminder. {task.title} at {task.due_time}"
                    )
                except Exception as e:
                    logging.error(f"Error in alarm TTS: {e}")

            # Re-check in 5 minutes if not acknowledged
            def retrigger_if_active(dt):
                if alarm_key in self.active_alarms:
                    logging.info(f"Re-triggering alarm for task: {task.title}")
                    self._show_alarm_popup(task, alarm_key)

            Clock.schedule_once(retrigger_if_active, 300)

        except Exception as e:
            logging.error(f"Error showing alarm popup: {e}")

 
    def handle_alarm_dismiss(self, task, alarm_key):
        """
        Handle alarm dismissal.
        """
        try:
            # Mark task as completed in database
            self.app.db_manager.mark_done(task.id)

            # Remove from active alarms
            if alarm_key in self.active_alarms:
                del self.active_alarms[alarm_key]

            # Refresh main screen
            try:
                main_screen = self.app.screen_manager.get_screen('main')
                if hasattr(main_screen, 'load_tasks'):
                    main_screen.load_tasks()
            except Exception:
                pass

            # Refresh tasks screen 
            try:
                tasks_screen = self.app.screen_manager.get_screen('tasks') 
                if hasattr(tasks_screen, 'load_all_tasks'):
                    tasks_screen.load_all_tasks()
            except Exception:
                pass
            
            # Refresh settings screen
            try:
                settings_screen = self.app.screen_manager.get_screen('settings')
                if hasattr(settings_screen, 'refresh_with_settings'):
                    settings_screen.refresh_with_settings(
                        self.app.font_family, 
                        self.app.font_size, 
                        self.app.high_contrast
                    )
            except Exception:
                pass

        except Exception as e:
            logging.error(f"Error in handle_alarm_dismiss: {e}")

class VoiceAssistantApp(App):
    kv_file = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = None
        self.db_manager = None
        self.stt_engine = None
        self.tts_engine = None
        self.command_parser = None
        self.alarm_manager = None
        
        # Global UI/voice settings
        self.font_family = 'Rubik'
        self.font_size = 20
        self.high_contrast = False
        self.current_voice = 0
        self.voice_speed = 'Normal'

        # Track last reset date in-memory for safety
        self._last_reset_date = None

        self._schedule_daily_reset()

    def _initialize_components(self):
        """
        Initialize DB, STT, TTS, parser, alarms.
        """
        try:
            # 1. Initialize Security Manager
            security_manager = SecurityManager()
             
            db_path = os.path.join(project_root, 'tasks.db')
            # 2. Pass the instance to DatabaseManager
            self.db_manager = DatabaseManager(security_manager=security_manager, db_path=db_path)
            # 3.Clean old tasks on startup
            self.db_manager.clear_old_tasks()

            model_path = os.path.join(
                os.path.dirname(__file__),
                '..',
                'assets',
                'models',
                'vosk-model-small-en-gb-0.15'
            )
            self.stt_engine = SpeechToTextEngine(model_path)
            self.tts_engine = TextToSpeechEngine()
            self.command_parser = CommandParser()
            self.alarm_manager = AlarmManager(self)

            logging.info("All components initialized successfully")
            return True
        except Exception as e:
            logging.error("Failed to initialize components: %s", e)
            return False

    def build(self):
        """Build the main application."""
        Window.clearcolor = (1, 1, 1, 1)
        # Get absolute paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        print("🔍 Loading KV files manually...")
        
        # Load individual KV files in correct order
        kv_files = [
            'gui/popups.kv',      # Load first - popups might be referenced
            'gui/main_screen.kv',
            'gui/tasks_screen.kv', 
            'gui/settings_screen.kv'
        ]
        
        for kv_file in kv_files:
            full_path = os.path.join(current_dir, kv_file)
            if os.path.exists(full_path):
                Builder.load_file(full_path)
                print(f"✅ Loaded: {kv_file}")
            else:
                print(f"❌ Missing: {full_path}")
        
        
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
        # Safety: ensure reset has been run at least once today
        Clock.schedule_once(lambda dt: self._reset_if_new_day(), 5)

    def show_main_screen(self):
        """Show the main screen and refresh tasks."""
        self.screen_manager.current = 'main'
        main_screen = self.screen_manager.get_screen('main')
        if hasattr(main_screen, 'load_tasks'):
            main_screen.load_tasks()

    def show_tasks_screen(self):
        """Show all tasks screen and refresh tasks list."""
        self.screen_manager.current = 'tasks'
        tasks_screen = self.screen_manager.get_screen('tasks')
        if hasattr(tasks_screen, 'load_all_tasks'):
            tasks_screen.load_all_tasks()

    def show_settings_screen(self):
        """Show settings screen."""
        self.screen_manager.current = 'settings'

    def apply_settings_globally(self):
        """
        Apply current settings to all screens.
        """
        for screen_name in ['main', 'tasks', 'settings']:
            screen = self.screen_manager.get_screen(screen_name)
            if hasattr(screen, 'apply_settings'):
                screen.apply_settings(self.font_family, self.font_size, self.high_contrast)

    # -------- Daily reset logic --------
    def _schedule_daily_reset(self):
        """
        Background thread: waits until next midnight, then clears all tasks.
        """
        def reset_tasks():
            while True:
                try:
                    now = datetime.now()
                    today_str = now.strftime("%Y-%m-%d")
                    self._last_reset_date = today_str

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

    def _reset_if_new_day(self):
        """
        Safety check: if app runs across multiple days without closing,
        ensure that a reset has been done at least once per calendar day.
        """
        try:
            now = datetime.now()
            today_str = now.strftime("%Y-%m-%d")
            if self._last_reset_date != today_str:
                logging.info("Detected new day without recorded reset. Clearing tasks now.")
                self._reset_all_tasks()
                self._last_reset_date = today_str
        except Exception as e:
            logging.error(f"Error in _reset_if_new_day: {e}")

    def _reset_all_tasks(self):
        """Delete all tasks from DB and refresh UI."""
        try:
            if self.db_manager:
                tasks = self.db_manager.get_all_tasks()
                tasks_cleared = len(tasks)

                for task in tasks:
                    self.db_manager.delete_task(task.id)

                Clock.schedule_once(lambda dt: self._update_ui_after_reset(tasks_cleared))
                logging.info(f"Midnight Reset: Cleared {tasks_cleared} tasks at reset point")
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

    def on_stop(self):
        """Clean up resources on app exit."""
        if self.stt_engine:
            self.stt_engine.stop_listening()
        if self.tts_engine:
            self.tts_engine.stop()
        if self.alarm_manager:
            self.alarm_manager.stop()

if __name__ == '__main__':
    VoiceAssistantApp().run()