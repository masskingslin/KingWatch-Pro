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

from ui.widgets import StatCard, ThemeChip  # noqa

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
        # Warm up CPU in background — won't freeze UI
        threading.Thread(target=self._warmup_cpu, daemon=True).start()
        # Update all sensors immediately (CPU may show 0 on first call — normal)
        self.update_stats()
        # Then every 3 seconds
        Clock.schedule_interval(self.update_stats, 3)

    def _warmup_cpu(self):
        """Pre-warm CPU worker so first real reading is ready fast."""
        from core.cpu import _ensure_started
        _ensure_started()

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

    def update_stats(self, *a):
        # Run sensor reads in background, update UI when done
        threading.Thread(target=self._collect_and_update, daemon=True).start()

    def _collect_and_update(self):
        """Collect all sensor data in background thread, then update UI."""
        t   = get_theme(self._tname)
        acc = t["ACCENT"]
        wrn = t["WARN"]
        dng = t["DANGER"]

        def clr(pct, lo=75, hi=90):
            if pct >= hi: return get_color_from_hex(dng)
            if pct >= lo: return get_color_from_hex(wrn)
            return get_color_from_hex(acc)

        # ── Collect all data ──────────────────────────────────
        try:    cpu_v   = float(get_cpu())
        except: cpu_v   = 0.0
        cpu_freq   = get_cpu_freq()
        cpu_cores  = get_cpu_cores()
        cpu_procs  = get_cpu_procs()
        cpu_uptime = get_cpu_uptime()

        try:    ram_v, ram_d   = get_ram()
        except: ram_v, ram_d   = 0.0, "N/A"

        try:    sto_v, sto_d   = get_storage()
        except: sto_v, sto_d   = 0.0, "N/A"

        try:    bat = get_battery()
        except: bat = {"pct":0,"status":"ERR","cur":"N/A","volt":"N/A",
                        "power":"N/A","temp":"N/A","eta":"N/A","eta_label":""}

        try:    net = get_network()
        except: net = {"dl":"ERR","ul":"ERR","ping":"N/A","signal":"N/A"}

        try:    th_max, th_cpu, th_det = get_thermal()
        except: th_max, th_cpu, th_det = 0.0, 0.0, "N/A"

        # ── Push to UI on main thread ─────────────────────────
        def apply(dt):
            # CPU
            c = self.ids.cpu_card
            c.value    = f"{cpu_v}%"
            c.subtitle = "usage"
            c.bar_pct  = cpu_v
            c.bar_color = clr(cpu_v)
            c.detail1  = f"Freq: {cpu_freq}   Cores: {cpu_cores}"
            c.detail2  = f"Procs: {cpu_procs}   Up: {cpu_uptime}"

            # RAM
            c = self.ids.ram_card
            c.value    = f"{ram_v}%"
            c.subtitle = "used"
            c.bar_pct  = ram_v
            c.bar_color = clr(ram_v)
            c.detail1  = ram_d

            # Storage
            c = self.ids.storage_card
            c.value    = f"{sto_v}%"
            c.subtitle = "used"
            c.bar_pct  = sto_v
            c.bar_color = clr(sto_v)
            c.detail1  = sto_d

            # Battery
            pct = bat["pct"]
            c   = self.ids.battery_card
            c.value    = f"{pct:.0f}%"
            c.subtitle = bat["status"]
            c.bar_pct  = pct
            c.bar_color = (
                get_color_from_hex(acc) if "Charg" in bat["status"]
                else get_color_from_hex(dng) if pct <= 10
                else get_color_from_hex(wrn) if pct <= 20
                else get_color_from_hex(acc)
            )
            c.detail1 = f"Curr: {bat['cur']}   Volt: {bat['volt']}   Pwr: {bat['power']}"
            # Show ETA with context label: "Until full: 1h 20m" or "Until empty: 5h 30m"
            eta_label = bat.get("eta_label", "ETA")
            c.detail2 = f"Temp: {bat['temp']}   {eta_label}: {bat['eta']}"

            # Network
            c = self.ids.network_card
            c.value   = net["dl"]
            c.subtitle = net["ping"]
            c.detail1 = f"↓ {net['dl']}   ↑ {net['ul']}"
            c.detail2 = f"{net['signal']}   Ping: {net['ping']}"

            # Thermal
            c = self.ids.thermal_card
            c.value    = f"{th_max}°C"
            c.subtitle = f"CPU {th_cpu}°C"
            bar        = min(th_max / 120.0 * 100, 100)
            c.bar_pct  = bar
            c.bar_color = clr(bar, lo=54, hi=75)
            c.detail1  = th_det

        Clock.schedule_once(apply, 0)


class MonitorApp(App):
    def build(self):
        Window.clearcolor = (0, 0, 0, 1)
        Builder.load_file(os.path.join(app_dir, "kingwatch.kv"))
        return RootWidget()


if __name__ == "__main__":
    MonitorApp().run()
