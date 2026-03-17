"""
KingWatch Pro v17 - main.py
"""
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ListProperty, BooleanProperty, StringProperty
import time as _time

from core.fps import PerformanceMonitor
from core.cpu import get_cpu
from core.ram import get_ram
from core.battery import get_battery
from core.network import get_network
from core.storage import get_storage
from core.thermal import get_thermal
from themes import THEME_NAMES, get_theme

Builder.load_file("kingwatch.kv")


class RootWidget(BoxLayout):
    bg        = ListProperty([0.04, 0.04, 0.04, 1])
    card_bg   = ListProperty([0.09, 0.09, 0.09, 1])
    accent    = ListProperty([0.0,  0.90, 0.46, 1])
    warn      = ListProperty([1.0,  0.57, 0.0,  1])
    danger    = ListProperty([1.0,  0.09, 0.27, 1])
    text_col  = ListProperty([1,    1,    1,    1])
    dim_col   = ListProperty([0.33, 0.33, 0.33, 1])
    sub_col   = ListProperty([0.55, 0.55, 0.55, 1])
    bar_bg    = ListProperty([0.18, 0.18, 0.18, 1])
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


class KingWatchApp(App):

    def build(self):
        self.monitor = PerformanceMonitor()
        self.root_widget = RootWidget()
        self.root_widget.apply_theme("Dark Pro")
        Clock.schedule_once(self._populate, 0)
        Clock.schedule_interval(self._update_fps,   0.5)
        Clock.schedule_interval(self._update_stats, 1.0)
        Clock.schedule_interval(self.root_widget.tick_clock, 1.0)
        return self.root_widget

    def _populate(self, dt):
        self.root_widget.tick_clock(0)
        self._update_fps(0)
        self._update_stats(0)

    def _update_fps(self, dt):
        r   = self.root_widget
        fps = self.monitor.get_fps()
        gpu = self.monitor.get_gpu()
        ref = self.monitor.get_refresh_rate()
        pct = min(100, fps / ref * 100) if ref > 0 else 0
        r.ids.fps_card.value    = f"{fps} FPS"
        r.ids.fps_card.subtitle = f"Refresh: {ref} Hz"
        r.ids.fps_card.detail1  = f"GPU Load: {gpu}"
        r.ids.fps_card.bar_pct  = pct

    def _update_stats(self, dt):
        r = self.root_widget

        cpu = get_cpu()
        r.ids.cpu_card.value    = f"{cpu['usage']:.1f}%"
        r.ids.cpu_card.subtitle = f"{cpu['freq']} MHz  |  {cpu['cores']} Cores"
        r.ids.cpu_card.detail1  = f"Processes: {cpu['procs']}"
        r.ids.cpu_card.bar_pct  = cpu['usage']

        ram_pct, ram_str = get_ram()
        r.ids.ram_card.value    = f"{ram_pct:.1f}%"
        r.ids.ram_card.subtitle = ram_str
        r.ids.ram_card.bar_pct  = ram_pct

        b = get_battery()
        r.ids.battery_card.value    = f"{b['pct']}%"
        r.ids.battery_card.subtitle = b['eta']
        r.ids.battery_card.detail1  = f"{b['current']}  {b['volt']}  {b['power']}"
        r.ids.battery_card.detail2  = f"Temp: {b['temp']}  [{b['status']}]"
        r.ids.battery_card.bar_pct  = b['pct']

        net = get_network()
        r.ids.network_card.value    = f"D:{net['dl']}"
        r.ids.network_card.subtitle = f"U:{net['ul']}"
        r.ids.network_card.detail1  = f"Ping: {net['ping']}   Band: {net['signal']}"
        r.ids.network_card.bar_pct  = 0

        s = get_storage()
        r.ids.storage_card.value    = f"{s['pct']:.1f}%"
        r.ids.storage_card.subtitle = f"{s['used']} / {s['total']}"
        r.ids.storage_card.detail1  = f"Free: {s['free']}"
        r.ids.storage_card.bar_pct  = s['pct']

        th = get_thermal()
        r.ids.thermal_card.value    = f"{th['cpu']}C"
        r.ids.thermal_card.subtitle = f"GPU: {th['gpu']}C  Max: {th['max']}C"
        r.ids.thermal_card.detail1  = th['detail']
        r.ids.thermal_card.bar_pct  = min(100, (th['max'] / 90) * 100)


if __name__ == "__main__":
    KingWatchApp().run()
