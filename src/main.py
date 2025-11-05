import logging
import sys
import os

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
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.text import LabelBase
from kivy.core.window import Window

Window.size = (550, 800) # Set default window size
Window.minimum_width, Window.minimum_height = 550, 800  # Set minimum and maximum window size at once

from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

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


# Load KV files
Builder.load_file('gui/main_screen.kv')
Builder.load_file('gui/tasks_screen.kv')
Builder.load_file('gui/settings_screen.kv')


def register_application_fonts():  # Register custom fonts for the application
    try:
        # Get absolute paths for fonts
        abs_current_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(os.path.dirname(abs_current_dir), 'assets')

        # Rubik paths (default font)
        rubik_dir = os.path.join(assets_dir, 'fonts', 'Rubik', 'static')
        rubik_regular = os.path.join(rubik_dir, 'Rubik-Regular.ttf')
        rubik_bold = os.path.join(rubik_dir, 'Rubik-Bold.ttf')
        rubik_italic = os.path.join(rubik_dir, 'Rubik-Italic.ttf')
        rubik_bolditalic = os.path.join(rubik_dir, 'Rubik-BoldItalic.ttf')

        # Arial paths
        arial_dir = os.path.join(assets_dir, 'fonts', 'arial')
        arial_regular = os.path.join(arial_dir, 'arial.ttf')
        arial_bold = os.path.join(arial_dir, 'arialbd.ttf')
        arial_italic = os.path.join(arial_dir, 'arialceitalic.ttf')

        # Balsamiq Sans paths
        balsamiq_dir = os.path.join(assets_dir, 'fonts', 'Balsamiq_Sans')
        balsamiq_regular = os.path.join(balsamiq_dir, 'BalsamiqSans-Regular.ttf')
        balsamiq_bold = os.path.join(balsamiq_dir, 'BalsamiqSans-Bold.ttf')
        balsamiq_italic = os.path.join(balsamiq_dir, 'BalsamiqSans-Italic.ttf')
        balsamiq_bolditalic = os.path.join(balsamiq_dir, 'BalsamiqSans-BoldItalic.ttf')

        # Crimson Pro paths
        crimson_dir = os.path.join(assets_dir, 'fonts', 'Crimson_pro', 'static')
        crimson_regular = os.path.join(crimson_dir, 'CrimsonPro-Regular.ttf')
        crimson_bold = os.path.join(crimson_dir, 'CrimsonPro-Bold.ttf')
        crimson_italic = os.path.join(crimson_dir, 'CrimsonPro-Italic.ttf')
        crimson_black = os.path.join(crimson_dir, 'CrimsonPro-Black.ttf')

        # Debug: Print paths to verify
        print("🔍 Checking font paths:")
        print(f"   Rubik Regular: {rubik_regular} -> {os.path.exists(rubik_regular)}")
        print(f"   Arial Regular: {arial_regular} -> {os.path.exists(arial_regular)}")
        print(f"   Balsamiq Sans Regular: {balsamiq_regular} -> {os.path.exists(balsamiq_regular)}")
        print(f"   Crimson Pro Regular: {crimson_regular} -> {os.path.exists(crimson_regular)}")

        # Register Rubik (default)
        LabelBase.register(
            name='Rubik',
            fn_regular=rubik_regular,
            fn_bold=rubik_bold,
            fn_italic=rubik_italic,
            fn_bolditalic=rubik_bolditalic
        )
        print("✅ Rubik font registered")

        # Register Arial
        LabelBase.register(
            name='Arial',
            fn_regular=arial_regular,
            fn_bold=arial_bold,
            fn_italic=arial_italic
        )
        print("✅ Arial font registered")

        # Register Balsamiq Sans
        LabelBase.register(
            name='BalsamiqSans',
            fn_regular=balsamiq_regular,
            fn_bold=balsamiq_bold,
            fn_italic=balsamiq_italic,
            fn_bolditalic=balsamiq_bolditalic
        )
        print("✅ BalsamiqSans font registered")

        # Register Crimson Pro
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


# Register fonts
font_registered = register_application_fonts()

# If fonts failed to register, use system fonts as fallback
if not font_registered:
    print("⚠️ Using system fonts as fallback")


class VoiceAssistantApp(App): # Main application class
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = None
        self.db_manager = None
        self.stt_engine = None
        self.tts_engine = None
        self.command_parser = None
        self.font_family = 'Rubik'  # Universal font
        self.font_size = 20   # Default font size
        self.high_contrast = False 
        self.current_voice = 0

    def _initialize_components(self): # Initialize application components
        """Initialize all application components"""
        try:
            self.db_manager = DatabaseManager() # Database manager
            model_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'models',
                                    'vosk-model-small-en-gb-0.15') # Vosk model path
            self.stt_engine = SpeechToTextEngine(model_path) # STT engine
            self.tts_engine = TextToSpeechEngine() # TTS engine
            self.command_parser = CommandParser() # Command parser
            logging.info("All components initialized successfully") # Log success
            return True
        except Exception as e:
            logging.error("Failed to initialize components: %s", e) # Log error
            return False # Initialization failed

    def build(self): # Build the application UI
        Window.clearcolor = (1, 1, 1, 1)

        self.screen_manager = ScreenManager()

        # Initialize components
        if not self._initialize_components():
            # Show simple error screen
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

        # Create screens
        main_screen = MainScreen(name='main')
        tasks_screen = TasksScreen(name='tasks')
        settings_screen = SettingsScreen(name='settings')

        # Set app instances
        main_screen.set_app_instance(self)
        tasks_screen.set_app_instance(self)
        settings_screen.set_app_instance(self)

        # Add screens to manager
        self.screen_manager.add_widget(main_screen)
        self.screen_manager.add_widget(tasks_screen)
        self.screen_manager.add_widget(settings_screen)

        return self.screen_manager

    def apply_settings_globally(self):  # apply settings across all screens
        """Apply current settings to all screens"""
        for screen_name in ['main', 'tasks', 'settings']:
            screen = self.screen_manager.get_screen(screen_name)
            if hasattr(screen, 'apply_settings'):
                screen.apply_settings(self.font_family, self.font_size, self.high_contrast)

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

    def on_stop(self): 
        """Cleanup when application closes"""
        if self.stt_engine:
            self.stt_engine.stop_listening()
        if self.tts_engine:
            self.tts_engine.stop()


if __name__ == '__main__': # Main entry point
    VoiceAssistantApp().run() # Run the application