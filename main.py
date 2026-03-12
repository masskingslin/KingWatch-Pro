import os
import sys

# Fix import paths for Android
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

# Import widgets
from ui.widgets import CircularGauge, InfoCard

# Import core modules
from core.cpu import get_cpu
from core.ram import get_ram
from core.battery import get_battery
from core.network import get_network
from core.storage import get_storage
from core.thermal import get_temp


class RootWidget(BoxLayout):

    def update_stats(self, *args):
        try:
            self.ids.cpu_widget.value = str(get_cpu()) + "%"
        except Exception as e:
            self.ids.cpu_widget.value = "N/A"
        try:
            self.ids.ram_widget.value = str(get_ram()) + "%"
        except Exception as e:
            self.ids.ram_widget.value = "N/A"
        try:
            self.ids.battery_widget.value = str(get_battery()) + "%"
        except Exception as e:
            self.ids.battery_widget.value = "N/A"
        try:
            self.ids.network_widget.value = str(get_network())
        except Exception as e:
            self.ids.network_widget.value = "N/A"
        try:
            self.ids.storage_widget.value = str(get_storage()) + "%"
        except Exception as e:
            self.ids.storage_widget.value = "N/A"
        try:
            self.ids.temp_widget.value = str(get_temp()) + "°C"
        except Exception as e:
            self.ids.temp_widget.value = "N/A"


class KingWatchApp(App):

    def build(self):
        # Android-safe KV file loading
        kv_path = os.path.join(app_dir, "kingwatch.kv")
        root = Builder.load_file(kv_path)
        Clock.schedule_interval(root.update_stats, 3)
        return root


if __name__ == "__main__":
    KingWatchApp().run()