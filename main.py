import os, sys, threading

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

from ui.widgets import StatCard, ThemeChip, ArcGauge, SparkLine  # noqa

from themes import THEME_NAMES, get_theme, DEFAULT_THEME
from core.cpu     import get_cpu, get_cpu_freq, get_cpu_cores, get_cpu_procs, get_cpu_uptime
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
        # Start CPU background worker (non-blocking)
        from core.cpu import _ensure_started
        threading.Thread(target=_ensure_started, daemon=True).start()
        # First read immediately, then every 3s
        self.update_stats()
        Clock.schedule_interval(self.update_stats, 3)

    # ── THEME ──────────────────────────────────────────────
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
        # Update arc colors on all cards
        self._update_card_colors(t)

    def _update_card_colors(self, t):
        acc = get_color_from_hex(t["ACCENT"])
        bg2 = get_color_from_hex(t["CARD2"])
        for card_id in ["cpu_card","ram_card","storage_card",
                        "battery_card","network_card","thermal_card"]:
            try:
                c = self.ids[card_id]
                c.arc_color = acc
                c.arc_bg    = bg2
                # Update sparkline color
                c.ids.spark.line_color = acc
            except Exception:
                pass

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

    # ── SENSORS ────────────────────────────────────────────
    def update_stats(self, *a):
        threading.Thread(target=self._collect_and_update, daemon=True).start()

    def _collect_and_update(self):
        t   = get_theme(self._tname)
        acc = t["ACCENT"]
        wrn = t["WARN"]
        dng = t["DANGER"]

        def clr(pct, lo=75, hi=90):
            if pct >= hi: return get_color_from_hex(dng)
            if pct >= lo: return get_color_from_hex(wrn)
            return get_color_from_hex(acc)

        # Collect
        try:    cpu_v  = float(get_cpu())
        except: cpu_v  = 0.0
        cpu_freq  = get_cpu_freq()
        cpu_cores = get_cpu_cores()
        cpu_procs = get_cpu_procs()
        cpu_up    = get_cpu_uptime()

        try:    ram_v, ram_d   = get_ram()
        except: ram_v, ram_d   = 0.0, "N/A"

        try:    sto_v, sto_d   = get_storage()
        except: sto_v, sto_d   = 0.0, "N/A"

        try:    bat = get_battery()
        except: bat = {"pct":0,"status":"ERR","cur":"N/A","volt":"N/A",
                        "power":"N/A","temp":"N/A","eta":"N/A","eta_label":"ETA"}

        try:    net = get_network()
        except: net = {"dl":"ERR","ul":"ERR","ping":"N/A","signal":"N/A"}

        try:    th_max, th_cpu, th_det = get_thermal()
        except: th_max, th_cpu, th_det = 0.0, 0.0, "N/A"

        # Push to UI
        def apply(dt):
            # CPU
            c = self.ids.cpu_card
            c.value     = f"{cpu_v}%"
            c.subtitle  = "usage"
            c.bar_pct   = cpu_v
            c.arc_color = clr(cpu_v)
            c.detail1   = f"Freq: {cpu_freq}   Cores: {cpu_cores}"
            c.detail2   = f"Procs: {cpu_procs}   Up: {cpu_up}"
            c.ids.spark.push(cpu_v)
            c.ids.spark.line_color = clr(cpu_v)

            # RAM
            c = self.ids.ram_card
            c.value     = f"{ram_v}%"
            c.subtitle  = "used"
            c.bar_pct   = ram_v
            c.arc_color = clr(ram_v)
            c.detail1   = ram_d
            c.ids.spark.push(ram_v)
            c.ids.spark.line_color = clr(ram_v)

            # Storage
            c = self.ids.storage_card
            c.value     = f"{sto_v}%"
            c.subtitle  = "used"
            c.bar_pct   = sto_v
            c.arc_color = clr(sto_v)
            c.detail1   = sto_d
            c.ids.spark.push(sto_v)

            # Battery
            pct = bat["pct"]
            c   = self.ids.battery_card
            c.value     = f"{pct:.0f}%"
            c.subtitle  = bat["status"]
            c.bar_pct   = pct
            bat_clr = (get_color_from_hex(acc) if "Charg" in bat["status"]
                       else get_color_from_hex(dng) if pct <= 10
                       else get_color_from_hex(wrn) if pct <= 20
                       else get_color_from_hex(acc))
            c.arc_color = bat_clr
            c.detail1   = f"Curr: {bat['cur']}   Volt: {bat['volt']}   Pwr: {bat['power']}"
            c.detail2   = f"Temp: {bat['temp']}   {bat.get('eta_label','ETA')}: {bat['eta']}"
            c.ids.spark.push(pct)
            c.ids.spark.line_color = bat_clr

            # Network (use ping ms as sparkline if numeric)
            c = self.ids.network_card
            c.value     = net["dl"]
            c.subtitle  = net["ping"]
            c.bar_pct   = 0
            c.detail1   = f"↓ {net['dl']}   ↑ {net['ul']}"
            c.detail2   = f"{net['signal']}   {net['ping']}"
            try:
                ping_val = float(net["ping"].split()[0])
                c.ids.spark.push(min(ping_val, 500))
                c.arc_color = (get_color_from_hex(dng) if ping_val > 200
                               else get_color_from_hex(wrn) if ping_val > 80
                               else get_color_from_hex(acc))
                c.bar_pct = min(ping_val / 5, 100)  # arc shows ping severity
            except Exception:
                pass

            # Thermal
            c = self.ids.thermal_card
            c.value     = f"{th_max}°C"
            c.subtitle  = f"CPU {th_cpu}°C"
            bar         = min(th_max / 120.0 * 100, 100)
            c.bar_pct   = bar
            c.arc_color = clr(bar, lo=54, hi=75)
            c.detail1   = th_det
            c.ids.spark.push(float(th_max))
            c.ids.spark.line_color = clr(bar, lo=54, hi=75)

        Clock.schedule_once(apply, 0)


class MonitorApp(App):
    def build(self):
        Window.clearcolor = (0, 0, 0, 1)
        Builder.load_file(os.path.join(app_dir, "kingwatch.kv"))
        return RootWidget()


if __name__ == "__main__":
    MonitorApp().run()
