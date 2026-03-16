import os
import sys
import threading
import io

app_dir = os.path.dirname(os.path.abspath(__file__))

if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.properties import ColorProperty
from kivy.utils import get_color_from_hex

from ui.widgets import StatCard, ThemeChip
from ui.gauge import draw_gauge

from themes import THEME_NAMES, get_theme, DEFAULT_THEME

from core.cpu import get_cpu, get_cpu_freq, get_cpu_cores, get_cpu_procs, get_cpu_uptime
from core.ram import get_ram
from core.battery import get_battery
from core.network import get_network
from core.storage import get_storage
from core.thermal import get_thermal
from core.fps import FPSMonitor


def set_gauge(card, pct, color):

    try:
        fg = tuple(int(c * 255) for c in color[:3]) + (255,)
        bg = (40, 40, 40, 255)

        png = draw_gauge(pct, size=110, fg=fg, bg=bg, thick=12)

        buf = io.BytesIO(png)

        img = CoreImage(buf, ext="png", nocache=True)

        card.ids.gauge_img.texture = img.texture

    except Exception:
        pass


class RootWidget(BoxLayout):

    bg = ColorProperty(get_color_from_hex("#0A0A0A"))
    card = ColorProperty(get_color_from_hex("#161616"))
    card2 = ColorProperty(get_color_from_hex("#242424"))
    accent = ColorProperty(get_color_from_hex("#00E676"))
    dim = ColorProperty(get_color_from_hex("#555555"))
    div = ColorProperty(get_color_from_hex("#222222"))
    btn_txt = ColorProperty(get_color_from_hex("#000000"))

    _theme_name = DEFAULT_THEME

    def on_kv_post(self, *args):

        self.perf = FPSMonitor()

        self.build_theme_chips()

        self.apply_theme(DEFAULT_THEME)

        threading.Thread(target=self.start_cpu_monitor, daemon=True).start()

        self.update_stats()

        Clock.schedule_interval(self.update_stats, 3)

    def start_cpu_monitor(self):

        try:
            from core.cpu import _ensure_started
            _ensure_started()
        except:
            pass

    def build_theme_chips(self):

        row = self.ids.chips_row
        row.clear_widgets()

        for name in THEME_NAMES:

            chip = ThemeChip(label=name)

            chip._name = name

            chip.bind(on_touch_up=self.select_theme)

            row.add_widget(chip)

    def select_theme(self, chip, touch):

        if chip.collide_point(*touch.pos):

            self.apply_theme(chip._name)

            return True

    def apply_theme(self, name):

        self._theme_name = name

        t = get_theme(name)

        self.bg = get_color_from_hex(t["BG"])
        self.card = get_color_from_hex(t["CARD"])
        self.card2 = get_color_from_hex(t["CARD2"])
        self.accent = get_color_from_hex(t["ACCENT"])
        self.dim = get_color_from_hex(t["DIM"])
        self.div = get_color_from_hex(t["CARD2"])
        self.btn_txt = get_color_from_hex(t["BTN_TEXT"])

        self.style_chips(t)

    def style_chips(self, theme):

        try:

            for chip in self.ids.chips_row.children:

                selected = chip.label == self._theme_name

                chip.selected = selected

                chip.chip_bg = get_color_from_hex(
                    theme["ACCENT"] + "33") if selected else get_color_from_hex(theme["CARD"])

                chip.chip_border = get_color_from_hex(
                    theme["ACCENT"]) if selected else get_color_from_hex(theme["CARD2"])

                chip.chip_text = get_color_from_hex(
                    theme["ACCENT"]) if selected else get_color_from_hex(theme["DIM"])

        except:
            pass

    def update_stats(self, *args):

        threading.Thread(target=self.collect_stats, daemon=True).start()

    def collect_stats(self):

        theme = get_theme(self._theme_name)

        accent = theme["ACCENT"]
        warn = theme["WARN"]
        danger = theme["DANGER"]

        def color_logic(value, lo=75, hi=90):

            if value >= hi:
                return get_color_from_hex(danger)

            if value >= lo:
                return get_color_from_hex(warn)

            return get_color_from_hex(accent)

        try:
            cpu_val = float(get_cpu())
        except:
            cpu_val = 0

        try:
            ram_val, ram_detail = get_ram()
        except:
            ram_val, ram_detail = 0, "N/A"

        try:
            storage_val, storage_detail = get_storage()
        except:
            storage_val, storage_detail = 0, "N/A"

        try:
            net = get_network()
        except:
            net = {"dl": "ERR", "ul": "ERR", "ping": "N/A", "signal": "N/A"}

        try:
            thermal_max, thermal_cpu, thermal_detail = get_thermal()
        except:
            thermal_max, thermal_cpu, thermal_detail = 0, 0, "N/A"

        try:
            fps_val = self.perf.get_fps()
            gpu_val = self.perf.get_gpu()
            drops = self.perf.get_frame_drops()
            lag = self.perf.get_lag()
        except:
            fps_val, gpu_val, drops, lag = 0, "0%", 0, 0

        def apply_ui(dt):

            try:

                card = self.ids.cpu_card

                col = color_logic(cpu_val)

                card.value = f"{cpu_val:.1f}%"
                card.subtitle = "usage"

                card.bar_pct = cpu_val
                card.bar_color = col

                set_gauge(card, cpu_val, list(col))

            except:
                pass

            try:

                card = self.ids.ram_card

                col = color_logic(ram_val)

                card.value = f"{ram_val:.1f}%"
                card.subtitle = "used"

                card.bar_pct = ram_val
                card.bar_color = col

                card.detail1 = ram_detail

                set_gauge(card, ram_val, list(col))

            except:
                pass

            try:

                card = self.ids.fps_card

                pct = min(fps_val / 60 * 100, 100)

                col = color_logic(pct)

                card.value = str(fps_val)
                card.subtitle = "FPS"

                card.bar_pct = pct
                card.bar_color = col

                card.detail1 = f"GPU Load: {gpu_val}"
                card.detail2 = f"Drops: {drops}  Lag: {lag}"

                set_gauge(card, pct, list(col))

            except:
                pass

        Clock.schedule_once(apply_ui, 0)


class MonitorApp(App):

    def build(self):

        Window.clearcolor = (0, 0, 0, 1)

        Builder.load_file(os.path.join(app_dir, "kingwatch.kv"))

        return RootWidget()


if __name__ == "__main__":

    MonitorApp().run()