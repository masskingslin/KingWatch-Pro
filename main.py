"""
KingWatch Pro v17 - main.py
KingwatchApp → auto-loads kingwatch.kv. No Builder.load_file.
"""
import time as _time
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ListProperty, BooleanProperty, StringProperty

from core.fps import PerformanceMonitor
from core.cpu import get_cpu
from core.ram import get_ram
from core.battery import get_battery
from core.network import get_network
from core.storage import get_storage
from core.thermal import get_thermal
from themes import THEME_NAMES, get_theme


class RootWidget(BoxLayout):
    bg        = ListProperty([0.04, 0.04, 0.04, 1])
    card_bg   = ListProperty([0.09, 0.09, 0.09, 1])
    accent    = ListProperty([0.0,  0.88, 0.44, 1])
    warn      = ListProperty([1.0,  0.57, 0.0,  1])
    danger    = ListProperty([1.0,  0.13, 0.27, 1])
    text_col  = ListProperty([1,    1,    1,    1])
    dim_col   = ListProperty([0.33, 0.33, 0.33, 1])
    sub_col   = ListProperty([0.55, 0.55, 0.55, 1])
    bar_bg    = ListProperty([0.13, 0.13, 0.13, 1])
    collapsed = BooleanProperty(False)
    clock_str = StringProperty("00:00:00")
    theme_idx = 0

    def apply_theme(self, name):
        t = get_theme(name)
        def h(hx):
            hx = hx.lstrip("#")
            return [int(hx[i:i+2], 16) / 255 for i in (0, 2, 4)] + [1]
        self.bg       = h(t["BG"])
        self.card_bg  = h(t["CARD"])
        self.accent   = h(t["ACCENT"])
        self.warn     = h(t["WARN"])
        self.danger   = h(t["DANGER"])
        self.text_col = h(t["TEXT"])
        self.dim_col  = h(t["DIM"])

    def cycle_theme(self):
        self.theme_idx = (self.theme_idx + 1) % len(THEME_NAMES)
        self.apply_theme(THEME_NAMES[self.theme_idx])

    def toggle_collapse(self):
        self.collapsed = not self.collapsed

    def tick_clock(self, dt):
        self.clock_str = _time.strftime("%H:%M:%S")


class KingwatchApp(App):

    # Thermal state — cycles every 10 seconds
    _thermal_tick = 0   # counts seconds
    _thermal_mode = 0   # 0=CPU  1=GPU  2=Battery

    def build(self):
        self.monitor     = PerformanceMonitor()
        self.root_widget = RootWidget()
        self.root_widget.apply_theme("Dark Pro")
        self.root_widget.tick_clock(0)
        self._update_fps(0)
        self._update_stats(0)
        Clock.schedule_interval(self._update_fps,            0.5)
        Clock.schedule_interval(self._update_stats,          1.0)
        Clock.schedule_interval(self.root_widget.tick_clock, 1.0)
        return self.root_widget

    def _update_fps(self, dt):
        r   = self.root_widget
        fps = self.monitor.get_fps()
        gpu = self.monitor.get_gpu()
        ref = self.monitor.get_refresh_rate()
        pct = min(100, fps / ref * 100) if ref > 0 else 0
        r.ids.fps_card.value    = f"{fps} FPS"
        r.ids.fps_card.subtitle = f"Refresh: {ref} Hz"
        r.ids.fps_card.detail1  = f"GPU: {gpu}" if gpu != "N/A" else ""
        r.ids.fps_card.bar_pct  = pct

    def _update_stats(self, dt):
        r = self.root_widget

        # ── CPU ──────────────────────────────────────────────────────────
        cpu = get_cpu()
        mx  = cpu.get("max_freq", 0)
        r.ids.cpu_card.value    = f"{cpu['usage']:.1f}%"
        r.ids.cpu_card.subtitle = f"{cpu['freq']}/{mx} MHz"
        r.ids.cpu_card.detail1  = f"{cpu['cores']} Cores  Procs:{cpu['procs']}"
        r.ids.cpu_card.bar_pct  = cpu['usage']

        # ── RAM ──────────────────────────────────────────────────────────
        ram_pct, ram_str = get_ram()
        r.ids.ram_card.value    = f"{ram_pct:.1f}%"
        r.ids.ram_card.subtitle = ram_str
        r.ids.ram_card.detail1  = ""
        r.ids.ram_card.bar_pct  = ram_pct

        # ── Battery ──────────────────────────────────────────────────────
        b = get_battery()
        r.ids.battery_card.value    = f"{b['pct']}%"
        r.ids.battery_card.subtitle = b['eta']
        r.ids.battery_card.detail1  = (
            f"{b['current']}  {b['volt']}  Temp:{b['temp']}"
        )
        r.ids.battery_card.bar_pct  = b['pct']

        # ── Network — Google speed-test style ────────────────────────────
        net = get_network()
        # Network card — Google speed-test style
        # Arc value  = download speed
        # Subtitle   = upload speed
        # Detail     = Band (4G/5G/WiFi) + dBm bars + ping
        rssi = net.get('rssi', '')
        sig  = net['signal']
        rssi_part = f"  {rssi}" if rssi else ""
        r.ids.network_card.value    = net['dl']
        r.ids.network_card.subtitle = f"Up: {net['ul']}"
        r.ids.network_card.detail1  = f"{sig}{rssi_part}  Ping:{net['ping']}"
        r.ids.network_card.bar_pct  = net['arc_pct']

        # ── Storage ──────────────────────────────────────────────────────
        s = get_storage()
        r.ids.storage_card.value    = f"{s['pct']:.1f}%"
        r.ids.storage_card.subtitle = f"{s['used']} / {s['total']}"
        r.ids.storage_card.detail1  = f"Free: {s['free']}"
        r.ids.storage_card.bar_pct  = s['pct']

        # ── Thermal — cycles CPU→GPU→Battery every 10 seconds ────────────
        th = get_thermal()
        self._thermal_tick += 1
        if self._thermal_tick >= 10:
            self._thermal_tick = 0
            self._thermal_mode = (self._thermal_mode + 1) % 3

        mode = self._thermal_mode
        if mode == 0:
            t    = th['cpu']
            maxl = th['cpu_max']   # 90°C
            lbl  = "CPU"
        elif mode == 1:
            t    = th['gpu']
            maxl = th['gpu_max']   # 85°C
            lbl  = "GPU"
        else:
            t    = th['batt']
            maxl = th['batt_max']  # 45°C
            lbl  = "Battery"

        pct_of_max = min(100, (t / maxl * 100)) if maxl > 0 else 0
        warn = "  ⚠ THROTTLE" if th['cpu'] >= 80 else ""

        r.ids.thermal_card.value    = f"{t}C"
        r.ids.thermal_card.subtitle = (
            f"{lbl}: {t}C / {maxl}C{warn}"
        )
        r.ids.thermal_card.detail1  = th['detail']
        r.ids.thermal_card.bar_pct  = pct_of_max


if __name__ == "__main__":
    KingwatchApp().run()
