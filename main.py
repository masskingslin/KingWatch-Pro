"""
KingWatch Pro v17 - main.py
KingwatchApp -> auto-loads kingwatch.kv. No Builder.load_file.
Each card in its own function to avoid Python 3.11 LOAD_ATTR cache collisions.
No unicode, no emoji.
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
        dim = h(t["DIM"])
        txt = h(t["TEXT"])
        self.sub_col = [(dim[i] + txt[i]) / 2 for i in range(4)]

    def cycle_theme(self):
        self.theme_idx = (self.theme_idx + 1) % len(THEME_NAMES)
        self.apply_theme(THEME_NAMES[self.theme_idx])

    def toggle_collapse(self):
        self.collapsed = not self.collapsed

    def tick_clock(self, dt):
        self.clock_str = _time.strftime("%H:%M:%S")


# Each card update in its own function.
# Prevents Python 3.11 specializing interpreter from reusing
# LOAD_ATTR cache slots across different card references.

def _do_fps(ids, monitor):
    fps     = monitor.get_fps()
    max_fps = monitor.get_max_fps()
    gpu     = monitor.get_gpu()
    curr_hz = monitor.get_refresh_rate()
    max_hz  = monitor.get_max_refresh_rate()
    if 0 < max_hz:
        pct = min(100, fps * 100 // max_hz)
    else:
        pct = 0
    c = ids.fps_card
    c.value   = str(fps) + " FPS"
    c.subtitle = "Max: " + str(max_fps) + " FPS"
    if curr_hz == max_hz:
        hz = "Refresh: " + str(curr_hz) + " Hz"
    else:
        hz = str(curr_hz) + "Hz (max " + str(max_hz) + "Hz)"
    if gpu == "N/A":
        c.detail1 = hz
    else:
        c.detail1 = hz + "  GPU:" + gpu
    c.bar_pct = pct


def _do_cpu(ids):
    d  = get_cpu()
    mx = d["max_freq"]
    c  = ids.cpu_card
    c.value    = str(round(d["usage"], 1)) + "%"
    c.subtitle = str(d["freq"]) + "/" + str(mx) + " MHz"
    c.detail1  = str(d["cores"]) + " Cores  Procs:" + str(d["procs"])
    c.bar_pct  = d["usage"]


def _do_ram(ids):
    pct, lbl, free = get_ram()
    c = ids.ram_card
    c.value    = str(round(pct, 1)) + "%"
    c.subtitle = lbl
    c.detail1  = free
    c.bar_pct  = pct


def _do_battery(ids):
    d = get_battery()
    c = ids.battery_card
    c.value    = str(d["pct"]) + "%"
    c.subtitle = d["eta"]
    c.detail1  = str(d["current"]) + "  " + str(d["volt"]) + "  Temp:" + str(d["temp"])
    c.bar_pct  = d["pct"]


def _do_network(ids):
    # get_network returns only 4 simple keys: dl, ul, sig, arc
    d   = get_network()
    dl  = d["dl"]
    ul  = d["ul"]
    sig = d["sig"]
    arc = d["arc"]
    c = ids.network_card
    c.value    = dl
    c.subtitle = "Up: " + ul
    c.detail1  = sig
    c.bar_pct  = arc


def _do_storage(ids):
    d = get_storage()
    c = ids.storage_card
    c.value    = str(round(d["pct"], 1)) + "%"
    c.subtitle = d["used"] + " / " + d["total"]
    c.detail1  = "Free: " + d["free"]
    c.bar_pct  = d["pct"]


def _do_thermal(ids, mode):
    d = get_thermal()
    if mode in (0,):
        t = d["cpu"]; maxl = d["cpu_max"]; lbl = "CPU"
    elif mode in (1,):
        t = d["gpu"]; maxl = d["gpu_max"]; lbl = "GPU"
    else:
        t = d["batt"]; maxl = d["batt_max"]; lbl = "Battery"
    if 0 < maxl:
        pct = min(100, t / maxl * 100)
    else:
        pct = 0
    if not (d["cpu"] < 80):
        warn = "  THROTTLE!"
    else:
        warn = ""
    c = ids.thermal_card
    c.value    = str(t) + "C"
    c.subtitle = lbl + ": " + str(t) + "C / " + str(maxl) + "C" + warn
    c.detail1  = d["detail"]
    c.bar_pct  = pct


class KingwatchApp(App):

    _thermal_tick = 0
    _thermal_mode = 0

    def build(self):
        self.monitor     = PerformanceMonitor()
        self.root_widget = RootWidget()
        self.root_widget.apply_theme("Dark Pro")
        self.root_widget.tick_clock(0)
        self._fps(0)
        self._stats(0)
        Clock.schedule_interval(self._fps,   0.5)
        Clock.schedule_interval(self._stats, 1.0)
        Clock.schedule_interval(self.root_widget.tick_clock, 1.0)
        return self.root_widget

    def _fps(self, dt):
        _do_fps(self.root_widget.ids, self.monitor)

    def _stats(self, dt):
        ids = self.root_widget.ids
        _do_cpu(ids)
        _do_ram(ids)
        _do_battery(ids)
        _do_network(ids)
        _do_storage(ids)
        self._thermal_tick = self._thermal_tick + 1
        if not (self._thermal_tick < 10):
            self._thermal_tick = 0
            self._thermal_mode = (self._thermal_mode + 1) % 3
        _do_thermal(ids, self._thermal_mode)


if __name__ == "__main__":
    KingwatchApp().run()
