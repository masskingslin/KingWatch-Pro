"""
KingWatch Pro v17 - main.py
KingwatchApp -> auto-loads kingwatch.kv. No Builder.load_file.

KEY FIX: Each card update in its OWN function.
This gives each function a fresh LOAD_ATTR cache - prevents
Python 3.11 specializing interpreter from confusing r.ids.network_card
with r.ids.cpu_card (same cache slot, different functions = no conflict).

No emoji, no unicode characters anywhere.
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
        dim = h(t["DIM"]); txt = h(t["TEXT"])
        self.sub_col  = [(dim[i]+txt[i])/2 for i in range(4)]

    def cycle_theme(self):
        self.theme_idx = (self.theme_idx + 1) % len(THEME_NAMES)
        self.apply_theme(THEME_NAMES[self.theme_idx])

    def toggle_collapse(self):
        self.collapsed = not self.collapsed

    def tick_clock(self, dt):
        self.clock_str = _time.strftime("%H:%M:%S")


# -- Isolated card update functions --
# Each in its own function = fresh LOAD_ATTR cache = no slot collision

def _update_fps_card(ids, fps, max_fps, gpu, curr_hz, max_hz):
    if 0 < max_hz:
        pct = min(100, fps * 100 // max_hz)
    else:
        pct = 0
    c = getattr(ids, 'fps_card')
    getattr(c, '__setattr__')('value',   str(fps) + " FPS")
    getattr(c, '__setattr__')('subtitle',"Max: " + str(max_fps) + " FPS")
    if curr_hz == max_hz:
        hz = "Refresh: " + str(curr_hz) + " Hz"
    else:
        hz = str(curr_hz) + "Hz (max " + str(max_hz) + "Hz)"
    if gpu == "N/A":
        getattr(c, '__setattr__')('detail1', hz)
    else:
        getattr(c, '__setattr__')('detail1', hz + "  GPU:" + gpu)
    getattr(c, '__setattr__')('bar_pct', pct)


def _update_cpu_card(ids, cpu):
    mx = 0
    try:
        mx = cpu["max_freq"]
    except Exception:
        pass
    c = getattr(ids, 'cpu_card')
    getattr(c,'__setattr__')('value',
        str(round(cpu["usage"],1)) + "%")
    getattr(c,'__setattr__')('subtitle',
        str(cpu["freq"]) + "/" + str(mx) + " MHz")
    getattr(c,'__setattr__')('detail1',
        str(cpu["cores"]) + " Cores  Procs:" + str(cpu["procs"]))
    getattr(c,'__setattr__')('bar_pct', cpu["usage"])


def _update_ram_card(ids, pct, label, free_label):
    c = getattr(ids, 'ram_card')
    getattr(c,'__setattr__')('value',    str(round(pct,1)) + "%")
    getattr(c,'__setattr__')('subtitle', label)
    getattr(c,'__setattr__')('detail1',  free_label)
    getattr(c,'__setattr__')('bar_pct',  pct)


def _update_battery_card(ids, b):
    c = getattr(ids, 'battery_card')
    getattr(c,'__setattr__')('value',    str(b["pct"]) + "%")
    getattr(c,'__setattr__')('subtitle', b["eta"])
    getattr(c,'__setattr__')('detail1',
        str(b["current"]) + "  " + str(b["volt"]) + "  Temp:" + str(b["temp"]))
    getattr(c,'__setattr__')('bar_pct',  b["pct"])


def _update_network_card(ids, net):
    # Read dict values directly - no .get() method call (compiles wrong)
    sig   = net["signal"]
    rssi  = net["rssi"]
    bwmax = net["bwmax"]
    dl    = net["dl"]
    ul    = net["ul"]
    arc   = net["arc_pct"]

    if rssi:
        detail = sig + "  " + rssi
    else:
        detail = sig
    if bwmax:
        detail = detail + "  " + bwmax

    c = getattr(ids, 'network_card')
    getattr(c,'__setattr__')('value',    dl)
    getattr(c,'__setattr__')('subtitle', "Up: " + ul)
    getattr(c,'__setattr__')('detail1',  detail)
    getattr(c,'__setattr__')('bar_pct',  arc)


def _update_storage_card(ids, s):
    c = getattr(ids, 'storage_card')
    getattr(c,'__setattr__')('value',
        str(round(s["pct"],1)) + "%")
    getattr(c,'__setattr__')('subtitle',
        s["used"] + " / " + s["total"])
    getattr(c,'__setattr__')('detail1',
        "Free: " + s["free"])
    getattr(c,'__setattr__')('bar_pct', s["pct"])


def _update_thermal_card(ids, th, mode):
    if mode in (0,):
        t = th["cpu"]; maxl = th["cpu_max"]; lbl = "CPU"
    elif mode in (1,):
        t = th["gpu"]; maxl = th["gpu_max"]; lbl = "GPU"
    else:
        t = th["batt"]; maxl = th["batt_max"]; lbl = "Battery"
    if 0 < maxl:
        pct = min(100, t / maxl * 100)
    else:
        pct = 0
    # No emoji - ASCII only
    if not (th["cpu"] < 80):
        warn = "  THROTTLE!"
    else:
        warn = ""
    c = getattr(ids, 'thermal_card')
    getattr(c,'__setattr__')('value',
        str(t) + "C")
    getattr(c,'__setattr__')('subtitle',
        lbl + ": " + str(t) + "C / " + str(maxl) + "C" + warn)
    getattr(c,'__setattr__')('detail1', th["detail"])
    getattr(c,'__setattr__')('bar_pct', pct)


class KingwatchApp(App):

    _thermal_tick = 0
    _thermal_mode = 0

    def build(self):
        self.monitor     = PerformanceMonitor()
        self.root_widget = RootWidget()
        self.root_widget.apply_theme("Dark Pro")
        self.root_widget.tick_clock(0)
        self._do_fps(0)
        self._do_stats(0)
        Clock.schedule_interval(self._do_fps,   0.5)
        Clock.schedule_interval(self._do_stats, 1.0)
        Clock.schedule_interval(self.root_widget.tick_clock, 1.0)
        return self.root_widget

    def _do_fps(self, dt):
        ids     = self.root_widget.ids
        fps     = self.monitor.get_fps()
        max_fps = self.monitor.get_max_fps()
        gpu     = self.monitor.get_gpu()
        curr_hz = self.monitor.get_refresh_rate()
        max_hz  = self.monitor.get_max_refresh_rate()
        _update_fps_card(ids, fps, max_fps, gpu, curr_hz, max_hz)

    def _do_stats(self, dt):
        ids = self.root_widget.ids

        cpu = get_cpu()
        _update_cpu_card(ids, cpu)

        ram_pct, ram_lbl, ram_free = get_ram()
        _update_ram_card(ids, ram_pct, ram_lbl, ram_free)

        b = get_battery()
        _update_battery_card(ids, b)

        net = get_network()
        _update_network_card(ids, net)

        s = get_storage()
        _update_storage_card(ids, s)

        th = get_thermal()
        self._thermal_tick = self._thermal_tick + 1
        if not (self._thermal_tick < 10):
            self._thermal_tick = 0
            self._thermal_mode = (self._thermal_mode + 1) % 3
        _update_thermal_card(ids, th, self._thermal_mode)


if __name__ == "__main__":
    KingwatchApp().run()
