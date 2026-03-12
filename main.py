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
from kivy.properties import ColorProperty, StringProperty

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
    card2   = ColorProperty(get_color_from_hex("#1E1E1E"))
    accent  = ColorProperty(get_color_from_hex("#00E676"))
    dim     = ColorProperty(get_color_from_hex("#555555"))
    div     = ColorProperty(get_color_from_hex("#222222"))
    btn_txt = ColorProperty(get_color_from_hex("#000000"))

    _tname = DEFAULT_THEME

    def on_kv_post(self, *a):
        self._build_chips()
        self._apply_theme(DEFAULT_THEME)
        self.update_stats()
        Clock.schedule_interval(self.update_stats, 3)

    # ── THEME CHIPS ─────────────────────────────
    def _build_chips(self):
        row = self.ids.chips_row
        row.clear_widgets()
        for name in THEME_NAMES:
            chip = ThemeChip(label=name)
            # Use Button-style: wrap in a real touch handler
            chip._kw_name = name
            chip.bind(on_touch_up=self._chip_touched)
            row.add_widget(chip)

    def _chip_touched(self, chip, touch):
        if chip.collide_point(*touch.pos):
            self._apply_theme(chip._kw_name)
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
        # DON'T call update_stats here — avoid blocking call on theme tap

    def _style_chips(self, t):
        try:
            for chip in self.ids.chips_row.children:
                sel = chip.label == self._tname
                chip.selected   = sel
                chip.chip_bg    = get_color_from_hex(
                    t["ACCENT"] + "44") if sel else get_color_from_hex(t["CARD2"])
                chip.chip_border = get_color_from_hex(
                    t["ACCENT"]) if sel else get_color_from_hex(t["CARD2"])
                chip.chip_text  = get_color_from_hex(
                    t["ACCENT"]) if sel else get_color_from_hex(t["DIM"])
        except Exception:
            pass

    # ── SENSORS ─────────────────────────────────
    def update_stats(self, *a):
        t   = get_theme(self._tname)
        acc = t["ACCENT"]
        wrn = t["WARN"]
        dng = t["DANGER"]

        def bar_clr(pct):
            if pct >= 90: return get_color_from_hex(dng)
            if pct >= 75: return get_color_from_hex(wrn)
            return get_color_from_hex(acc)

        # CPU
        try:
            v = float(get_cpu())
            c = self.ids.cpu_card
            c.value     = f"{v}%"
            c.subtitle  = "of total"
            c.bar_pct   = v
            c.bar_color = bar_clr(v)
        except Exception:
            self.ids.cpu_card.value = "N/A"

        # RAM
        try:
            v, detail = get_ram()
            c = self.ids.ram_card
            c.value     = f"{v}%"
            c.subtitle  = "used"
            c.bar_pct   = v
            c.bar_color = bar_clr(v)
            c.detail1   = detail
        except Exception:
            self.ids.ram_card.value = "N/A"

        # Storage
        try:
            v, detail = get_storage()
            c = self.ids.storage_card
            c.value     = f"{v}%"
            c.subtitle  = "used"
            c.bar_pct   = v
            c.bar_color = bar_clr(v)
            c.detail1   = detail
        except Exception:
            self.ids.storage_card.value = "N/A"

        # Battery
        try:
            cap, status, cur_str, volt_str, power_str, temp_str, eta_str = get_battery()
            c = self.ids.battery_card
            c.value     = f"{cap:.0f}%"
            c.subtitle  = status
            c.bar_pct   = cap
            c.bar_color = (
                get_color_from_hex(dng) if cap <= 10
                else get_color_from_hex(wrn) if cap <= 20
                else get_color_from_hex(acc)
            )
            c.detail1 = f"Curr: {cur_str}   Volt: {volt_str}   Pwr: {power_str}"
            c.detail2 = f"Temp: {temp_str}   ETA: {eta_str}"
        except Exception:
            self.ids.battery_card.value = "N/A"

        # Network
        try:
            total, dl, ul, ping_str, signal_str = get_network()
            c = self.ids.network_card
            c.value   = total
            c.subtitle = ping_str
            c.detail1 = f"DL: {dl}   UL: {ul}"
            c.detail2 = f"Signal: {signal_str}"
        except Exception:
            self.ids.network_card.value = "N/A"

        # Thermal
        try:
            max_t, cpu_t, detail = get_thermal()
            c = self.ids.thermal_card
            c.value     = f"{max_t}°C"
            c.subtitle  = f"CPU {cpu_t}°C"
            bar         = min(max_t / 120.0 * 100, 100)
            c.bar_pct   = bar
            c.bar_color = bar_clr(bar)
            c.detail1   = detail
        except Exception:
            self.ids.thermal_card.value = "N/A"


class KingWatchApp(App):
    def build(self):
        Window.clearcolor = (0, 0, 0, 1)
        Builder.load_file(os.path.join(app_dir, "kingwatch.kv"))
        return RootWidget()


if __name__ == "__main__":
    KingWatchApp().run()
