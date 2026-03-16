import os
import sys
import threading
import io

app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.utils import get_color_from_hex
from kivy.properties import ColorProperty

from ui.widgets import StatCard, ThemeChip

from themes import THEME_NAMES, get_theme, DEFAULT_THEME
from core.cpu import get_cpu, get_cpu_freq, get_cpu_cores, get_cpu_procs, get_cpu_uptime
from core.ram import get_ram
from core.battery import get_battery
from core.network import get_network
from core.storage import get_storage
from core.thermal import get_thermal
from core.fps import FPSMonitor

from ui.gauge import draw_gauge


def _set_gauge(card, pct, color_rgba):
    try:
        fg = tuple(int(c * 255) for c in color_rgba[:3]) + (255,)
        bg = (40, 40, 40, 255)

        png = draw_gauge(pct, size=110, fg=fg, bg=bg, thick=12)

        buf = io.BytesIO(png)

        ci = CoreImage(buf, ext="png", nocache=True)

        card.ids.gauge_img.texture = ci.texture
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

    _tname = DEFAULT_THEME

    def on_kv_post(self, *a):

        self.perf = FPSMonitor()

        self._build_chips()

        self._apply_theme(DEFAULT_THEME)

        threading.Thread(target=self._start_cpu, daemon=True).start()

        self.update_stats()

        Clock.schedule_interval(self.update_stats, 3)

    def _start_cpu(self):
        try:
            from core.cpu import _ensure_started
            _ensure_started()
        except Exception:
            pass

    def _build_chips(self):
        row = self.ids.chips_row
        row.clear_widgets()

        for name in THEME_NAMES:
            chip = ThemeChip(label=name)
            chip._name = name
            chip.bind(on_touch_up=self._on_chip)
            row.add_widget(chip)

    def _on_chip(self, chip, touch):
        if chip.collide_point(*touch.pos):
            self._apply_theme(chip._name)
            return True

    def _apply_theme(self, name):
        self._tname = name
        t = get_theme(name)

        self.bg = get_color_from_hex(t["BG"])
        self.card = get_color_from_hex(t["CARD"])
        self.card2 = get_color_from_hex(t["CARD2"])
        self.accent = get_color_from_hex(t["ACCENT"])
        self.dim = get_color_from_hex(t["DIM"])
        self.div = get_color_from_hex(t["CARD2"])
        self.btn_txt = get_color_from_hex(t["BTN_TEXT"])

        self._style_chips(t)

    def _style_chips(self, t):
        try:
            for chip in self.ids.chips_row.children:

                sel = chip.label == self._tname

                chip.selected = sel

                chip.chip_bg = get_color_from_hex(
                    t["ACCENT"] + "33") if sel else get_color_from_hex(t["CARD"])

                chip.chip_border = get_color_from_hex(
                    t["ACCENT"]) if sel else get_color_from_hex(t["CARD2"])

                chip.chip_text = get_color_from_hex(
                    t["ACCENT"]) if sel else get_color_from_hex(t["DIM"])
        except Exception:
            pass

    def update_stats(self, *a):
        threading.Thread(target=self._collect, daemon=True).start()

    def _collect(self):

        t = get_theme(self._tname)

        acc = t["ACCENT"]
        wrn = t["WARN"]
        dng = t["DANGER"]

        def clr(pct, lo=75, hi=90):

            if pct >= hi:
                return get_color_from_hex(dng)

            if pct >= lo:
                return get_color_from_hex(wrn)

            return get_color_from_hex(acc)

        try:
            cpu_v = float(get_cpu())
        except:
            cpu_v = 0

        try:
            ram_v, ram_d = get_ram()
        except:
            ram_v, ram_d = 0, "N/A"

        try:
            sto_v, sto_d = get_storage()
        except:
            sto_v, sto_d = 0, "N/A"

        try:
            bat = get_battery()
        except:
            bat = {"pct": 0, "status": "ERR", "cur": "N/A", "volt": "N/A",
                   "power": "N/A", "temp": "N/A", "eta": "N/A", "eta_label": "ETA"}

        try:
            net = get_network()
        except:
            net = {"dl": "ERR", "ul": "ERR", "ping": "N/A", "signal": "N/A"}

        try:
            th_max, th_cpu, th_det = get_thermal()
        except:
            th_max, th_cpu, th_det = 0, 0, "N/A"

        try:
            fps_v = self.perf.get_fps()
            gpu_v = self.perf.get_gpu()
            drop_v = self.perf.get_frame_drops()
            lag_v = self.perf.get_lag()
        except:
            fps_v, gpu_v, drop_v, lag_v = 0, "0%", 0, 0

        def apply(dt):

            try:
                c = self.ids.cpu_card
                cc = clr(cpu_v)

                c.value = f"{cpu_v:.1f}%"
                c.subtitle = "usage"
                c.bar_pct = cpu_v
                c.bar_color = cc

                _set_gauge(c, cpu_v, list(cc))
            except:
                pass

            try:
                c = self.ids.ram_card
                cc = clr(ram_v)

                c.value = f"{ram_v:.1f}%"
                c.subtitle = "used"
                c.bar_pct = ram_v
                c.bar_color = cc
                c.detail1 = ram_d

                _set_gauge(c, ram_v, list(cc))
            except:
                pass

            try:
                c = self.ids.fps_card

                refresh = self.perf.get_refresh_rate()

pct = min(fps_v / refresh * 100, 100)

                cc = clr(pct)

                c.value = str(fps_v)
                c.subtitle = "FPS"

                c.bar_pct = pct
                c.bar_color = cc

                c.detail1 = f"GPU Load: {gpu_v}"
                c.detail2 = f"Drops: {drop_v}  Lag: {lag_v}"

                _set_gauge(c, pct, list(cc))
            except:
                pass

        Clock.schedule_once(apply, 0)


class MonitorApp(App):

    def build(self):

        Window.clearcolor = (0, 0, 0, 1)

        Builder.load_file(os.path.join(app_dir, "kingwatch.kv"))

        return RootWidget()


if __name__ == "__main__":
    MonitorApp().run()