import os
import sys

# Android-safe path setup
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.core.window import Window

# Import widgets (registers InfoCard with KV)
from ui.widgets import InfoCard  # noqa

# Import core monitors
from core.cpu import get_cpu
from core.ram import get_ram
from core.battery import get_battery
from core.network import get_network
from core.storage import get_storage
from core.thermal import get_temp


class RootWidget(BoxLayout):

    def update_stats(self, *args):
        pairs = [
            ("cpu_widget",     get_cpu,     "%"),
            ("ram_widget",     get_ram,     "%"),
            ("battery_widget", get_battery, "%"),
            ("network_widget", get_network, ""),
            ("storage_widget", get_storage, "%"),
            ("temp_widget",    get_temp,    "°C"),
        ]
        for widget_id, func, unit in pairs:
            try:
                val = func()
                self.ids[widget_id].value = f"{val}{unit}"
            except Exception:
                self.ids[widget_id].value = "N/A"


class KingWatchApp(App):

    def build(self):
        Window.clearcolor = (0, 0, 0, 1)
        kv_path = os.path.join(app_dir, "kingwatch.kv")
        root = Builder.load_file(kv_path)
        root.update_stats()
        Clock.schedule_interval(root.update_stats, 3)
        return root


if __name__ == "__main__":
    KingWatchApp().run()