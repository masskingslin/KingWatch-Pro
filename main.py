import os
import sys

app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.properties import ColorProperty

from ui.widgets import InfoCard, ThemeChip  # noqa

from themes import THEME_NAMES, get_theme, DEFAULT_THEME
from core.cpu import get_cpu
from core.ram import get_ram
from core.battery import get_battery
from core.network import get_network
from core.storage import get_storage
from core.thermal import get_temp

# Danger thresholds for bar color
_WARN  = get_color_from_hex("#FF9100")
_DANGER= get_color_from_hex("#FF1744")


def _bar_color(pct, accent):
    if pct >= 90:
        return _DANGER
    if pct >= 75:
        return _WARN
    return accent


class RootWidget(BoxLayout):

    bg_color       = ColorProperty(get_color_from_hex("#000000"))
    card_color     = ColorProperty(get_color_from_hex("#141414"))
    text_color     = ColorProperty(get_color_from_hex("#FFFFFF"))
    accent_color   = ColorProperty(get_color_from_hex("#00C853"))
    btn_text_color = ColorProperty(get_color_from_hex("#000000"))
    dim_color      = ColorProperty(get_color_from_hex("#555555"))

    _theme_index = 0
    _current_theme = DEFAULT_THEME

    def on_kv_post(self, base_widget):
        self._build_theme_chips()
        self._apply_theme(DEFAULT_THEME)
        self.update_stats()
        Clock.schedule_interval(self.update_stats, 3)

    # ── THEME CHIPS ──────────────────────────────────
    def _build_theme_chips(self):
        row = self.ids.theme_chips_row
        row.clear_widgets()
        for name in THEME_NAMES:
            chip = ThemeChip(theme_name=name)
            chip.bind(on_touch_down=self._on_chip_touch)
            row.add_widget(chip)
        self._refresh_chip_styles()

    def _on_chip_touch(self, chip, touch):
        if chip.collide_point(*touch.pos):
            self._apply_theme(chip.theme_name)

    def _refresh_chip_styles(self):
        row = self.ids.theme_chips_row
        t = get_theme(self._current_theme)
        for chip in row.children:
            selected = chip.theme_name == self._current_theme
            chip.is_selected  = selected
            chip.border_color = get_color_from_hex(t["ACCENT"]) if selected else get_color_from_hex("#333333")
            chip.chip_color   = get_color_from_hex(t["ACCENT"] + "33") if selected else get_color_from_hex(t["CARD"])
            chip.text_color   = get_color_from_hex(t["ACCENT"]) if selected else get_color_from_hex(t["TEXT"])

    def _apply_theme(self, name):
        self._current_theme = name
        t = get_theme(name)
        self.bg_color       = get_color_from_hex(t["BG"])
        self.card_color     = get_color_from_hex(t["CARD"])
        self.text_color     = get_color_from_hex(t["TEXT"])
        self.accent_color   = get_color_from_hex(t["ACCENT"])
        self.btn_text_color = get_color_from_hex(t["BTN_TEXT"])
        # dim = muted version of text
        self.dim_color = get_color_from_hex("#555555")
        self._refresh_chip_styles()
        # Re-color bar cards
        self.update_stats()

    # ── SENSOR UPDATE ─────────────────────────────────
    def update_stats(self, *args):
        accent = self.accent_color

        # CPU
        try:
            v = float(get_cpu())
            self.ids.cpu_widget.value    = f"{v}%"
            self.ids.cpu_widget.bar_value = v
            self.ids.cpu_widget.bar_color = _bar_color(v, accent)
            self.ids.cpu_widget.detail   = ""
        except Exception:
            self.ids.cpu_widget.value = "N/A"

        # RAM
        try:
            v = float(get_ram())
            self.ids.ram_widget.value     = f"{v}%"
            self.ids.ram_widget.bar_value  = v
            self.ids.ram_widget.bar_color  = _bar_color(v, accent)
            self.ids.ram_widget.detail    = ""
        except Exception:
            self.ids.ram_widget.value = "N/A"

        # Storage
        try:
            v = float(get_storage())
            self.ids.storage_widget.value     = f"{v}%"
            self.ids.storage_widget.bar_value  = v
            self.ids.storage_widget.bar_color  = _bar_color(v, accent)
            self.ids.storage_widget.detail    = ""
        except Exception:
            self.ids.storage_widget.value = "N/A"

        # Temperature
        try:
            v = float(get_temp())
            self.ids.temp_widget.value     = f"{v}°C"
            self.ids.temp_widget.bar_value  = min(v / 120.0 * 100, 100)
            self.ids.temp_widget.bar_color  = _bar_color(v / 120.0 * 100, accent)
            self.ids.temp_widget.detail    = ""
        except Exception:
            self.ids.temp_widget.value = "N/A"

        # Battery (returns tuple)
        try:
            bv, bd = get_battery()
            # Extract numeric % for bar
            pct = 0.0
            try:
                pct = float(bv.split("%")[0].split()[-1])
            except Exception:
                pass
            self.ids.battery_widget.value     = bv
            self.ids.battery_widget.detail    = bd
            self.ids.battery_widget.bar_value  = pct
            # Battery bar green when > 20, orange > 10, red <= 10
            if pct <= 10:
                self.ids.battery_widget.bar_color = _DANGER
            elif pct <= 20:
                self.ids.battery_widget.bar_color = _WARN
            else:
                self.ids.battery_widget.bar_color = accent
        except Exception:
            self.ids.battery_widget.value  = "N/A"
            self.ids.battery_widget.detail = ""

        # Network (returns tuple)
        try:
            nv, nd = get_network()
            self.ids.network_widget.value  = nv
            self.ids.network_widget.detail = nd
        except Exception:
            self.ids.network_widget.value  = "N/A"
            self.ids.network_widget.detail = ""


class KingWatchApp(App):

    def build(self):
        Window.clearcolor = (0, 0, 0, 1)
        Builder.load_file(os.path.join(app_dir, "kingwatch.kv"))
        return RootWidget()


if __name__ == "__main__":
    KingWatchApp().run()
