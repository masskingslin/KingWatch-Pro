import os, sys

app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.properties import ColorProperty

# Register widget classes with KV
from ui.widgets import StatCard, ThemeChip  # noqa

from themes import THEME_NAMES, get_theme, DEFAULT_THEME
from core.cpu     import get_cpu
from core.ram     import get_ram
from core.battery import get_battery
from core.network import get_network
from core.storage import get_storage
from core.thermal import get_thermal


class RootWidget(BoxLayout):

    bg      = ColorProperty(get_color_from_hex("#0A0A0A"))
    card    = ColorProperty(get_color_from_hex("#161616"))
    card2   = ColorProperty(get_color_from_hex("#242424"))
    accent  = ColorProperty(get_color_from_hex("#00E676"))
    dim     = ColorProperty(get_color_from_hex("#555555"))
    div     = ColorProperty(get_color_from_hex("#222222"))
    btn_txt = ColorProperty(get_color_from_hex("#000000"))

    _tname = DEFAULT_THEME

    def on_kv_post(self, *a):
        self._build_chips()
        self._apply_theme(DEFAULT_THEME)
        # Warm up CPU stat (first read returns 0, second is real)
        get_cpu()
        Clock.schedule_once(self.update_stats, 1)
        Clock.schedule_interval(self.update_stats, 3)

    # ── THEME ──────────────────────────────────
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
        self.bg      = get_color_from_hex(t["BG"])
        self.card    = get_color_from_hex(t["CARD"])
        self.card2   = get_color_from_hex(t["CARD2"])
        self.accent  = get_color_from_hex(t["ACCENT"])
        self.dim     = get_color_from_hex(t["DIM"])
        self.div     = get_color_from_hex(t["CARD2"])
        self.btn_txt = get_color_from_hex(t["BTN_TEXT"])
        self._style_chips(t)

    def _style_chips(self, t):
        try:
            for chip in self.ids.chips_row.children:
                sel = (chip.label == self._tname)
                chip.selected    = sel
                chip.chip_bg     = get_color_from_hex(
                    t["ACCENT"] + "33") if sel else get_color_from_hex(t["CARD"])
                chip.chip_border = get_color_from_hex(
                    t["ACCENT"])       if sel else get_color_from_hex(t["CARD2"])
                chip.chip_text   = get_color_from_hex(
                    t["ACCENT"])       if sel else get_color_from_hex(t["DIM"])
        except Exception:
            pass

    # ── SENSORS ────────────────────────────────
    def update_stats(self, *a):
        t   = get_theme(self._tname)
        acc = t["ACCENT"]
        wrn = t["WARN"]
        dng = t["DANGER"]

        def clr(pct, lo=75, hi=90):
            if pct >= hi: return get_color_from_hex(dng)
            if pct >= lo: return get_color_from_hex(wrn)
            return get_color_from_hex(acc)

        # CPU
        try:
            v = float(get_cpu())
            c = self.ids.cpu_card
            c.value     = f"{v}%"
            c.subtitle  = "usage"
            c.bar_pct   = v
            c.bar_color = clr(v)
            c.detail1   = ""
        except Exception:
            self.ids.cpu_card.value = "ERR"

        # RAM
        try:
            v, detail = get_ram()
            c = self.ids.ram_card
            c.value     = f"{v}%"
            c.subtitle  = "used"
            c.bar_pct   = v
            c.bar_color = clr(v)
            c.detail1   = detail
        except Exception:
            self.ids.ram_card.value = "ERR"

        # Storage
        try:
            v, detail = get_storage()
            c = self.ids.storage_card
            c.value     = f"{v}%"
            c.subtitle  = "used"
            c.bar_pct   = v
            c.bar_color = clr(v)
            c.detail1   = detail
        except Exception:
            self.ids.storage_card.value = "ERR"

        # Battery — dict return
        try:
            b = get_battery()
            pct = b["pct"]
            c = self.ids.battery_card
            c.value    = f"{pct:.0f}%"
            c.subtitle = b["status"]
            c.bar_pct  = pct
            # Battery bar: low = danger, charging high = green
            if "Charg" in b["status"]:
                c.bar_color = get_color_from_hex(acc)
            else:
                c.bar_color = (get_color_from_hex(dng) if pct <= 10
                               else get_color_from_hex(wrn) if pct <= 20
                               else get_color_from_hex(acc))
            c.detail1  = f"Curr: {b['cur']}   Volt: {b['volt']}   Pwr: {b['power']}"
            c.detail2  = f"Temp: {b['temp']}   ETA: {b['eta']}"
        except Exception:
            self.ids.battery_card.value = "ERR"

        # Network — dict return, auto-refreshes (no button needed)
        try:
            n = get_network()
            c = self.ids.network_card
            c.value    = n["dl"]
            c.subtitle = n["ping"]
            c.detail1  = f"DL: {n['dl']}   UL: {n['ul']}"
            c.detail2  = f"Ping: {n['ping']}   {n['iface']}"
        except Exception:
            self.ids.network_card.value = "ERR"

        # Thermal
        try:
            max_t, cpu_t, detail = get_thermal()
            c = self.ids.thermal_card
            c.value    = f"{max_t}°C"
            c.subtitle = f"CPU {cpu_t}°C"
            bar        = min(max_t / 120.0 * 100, 100)
            c.bar_pct  = bar
            c.bar_color = clr(bar, lo=54, hi=75)  # 65°C warn, 90°C danger
            c.detail1  = detail
        except Exception:
            self.ids.thermal_card.value = "ERR"


# ── APP — renamed to MonitorApp to prevent Kivy auto-loading kingwatch.kv ──
class MonitorApp(App):
    def build(self):
        Window.clearcolor = (0, 0, 0, 1)
        # Manual load — no double load since class name != kv file name
        Builder.load_file(os.path.join(app_dir, "kingwatch.kv"))
        return RootWidget()


if __name__ == "__main__":
    MonitorApp().run()
