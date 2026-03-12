import os
import sys

app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.properties import ColorProperty, StringProperty

from ui.widgets import InfoCard  # noqa

from themes import THEME_NAMES, get_theme, DEFAULT_THEME
from core.cpu import get_cpu
from core.ram import get_ram
from core.battery import get_battery
from core.network import get_network
from core.storage import get_storage
from core.thermal import get_temp


class RootWidget(BoxLayout):

    # Theme-driven properties — KV binds to these directly
    bg_color      = ColorProperty(get_color_from_hex("#000000"))
    card_color    = ColorProperty(get_color_from_hex("#1E1E1E"))
    text_color    = ColorProperty(get_color_from_hex("#FFFFFF"))
    accent_color  = ColorProperty(get_color_from_hex("#00C853"))
    btn_text_color = ColorProperty(get_color_from_hex("#000000"))

    _theme_index = 0

    def on_kv_post(self, base_widget):
        self._apply_theme(DEFAULT_THEME)
        self.update_stats()
        Clock.schedule_interval(self.update_stats, 3)

    def _apply_theme(self, name):
        t = get_theme(name)
        self.bg_color       = get_color_from_hex(t["BG"])
        self.card_color     = get_color_from_hex(t["CARD"])
        self.text_color     = get_color_from_hex(t["TEXT"])
        self.accent_color   = get_color_from_hex(t["ACCENT"])
        self.btn_text_color = get_color_from_hex(t["BTN_TEXT"])
        self.ids.theme_btn.text = f"Theme: {name}"

    def cycle_theme(self, *args):
        self._theme_index = (self._theme_index + 1) % len(THEME_NAMES)
        self._apply_theme(THEME_NAMES[self._theme_index])

    def update_stats(self, *args):
        sensors = [
            ("cpu_widget",     get_cpu,     "%"),
            ("ram_widget",     get_ram,     "%"),
            ("battery_widget", get_battery, "%"),
            ("network_widget", get_network, ""),
            ("storage_widget", get_storage, "%"),
            ("temp_widget",    get_temp,    "°C"),
        ]
        for wid, func, unit in sensors:
            try:
                val = func()
                self.ids[wid].value = f"{val}{unit}"
            except Exception:
                self.ids[wid].value = "N/A"


class KingWatchApp(App):

    def build(self):
        Window.clearcolor = (0, 0, 0, 1)
        # Load KV rules only — RootWidget() instantiation happens here
        Builder.load_file(os.path.join(app_dir, "kingwatch.kv"))
        return RootWidget()


if __name__ == "__main__":
    KingWatchApp().run()