"""
KingWatch Pro v17 - main.py

ROOT CAUSE FIX:
  _do_network called get_network() at offset 2 (LOAD_GLOBAL 'get_network')
  This poisoned the LOAD_ATTR cache so ids.network_card became ids.get_network
  c was never assigned -> c.value/subtitle/detail1/bar_pct all silently broken

FIX: get_network() called in _stats() and result passed as argument d.
  _do_network(ids, d) has NO LOAD_GLOBAL calls at start, so
  ids.network_card is the very first LOAD_ATTR -> clean slot -> works.

Same pattern applied: each _do_X(ids, data) receives pre-fetched data.
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

# Module-level thermal state avoids self.attr LOAD_ATTR bugs
_th = {"tick": 0, "mode": 0}

# Module-level app ref for Clock callbacks
_app = [None]


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


# -- Card updaters - each receives pre-fetched data as argument ------------
# No LOAD_GLOBAL for data functions inside these functions.
# ids.xxx_card is always the first LOAD_ATTR -> clean cache slot.

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
    c.value    = str(fps) + " FPS"
    c.subtitle = "Max: " + str(max_fps) + " FPS"
    if curr_hz == max_hz:
        c.detail1 = "Refresh: " + str(curr_hz) + " Hz"
    else:
        c.detail1 = str(curr_hz) + "Hz (max " + str(max_hz) + "Hz)"
    if gpu == "N/A":
        pass
    else:
        c.detail1 = c.detail1 + "  GPU:" + gpu
    c.bar_pct = pct


def _do_cpu(ids, d):
    # d = get_cpu() result passed in
    mx = d["max_freq"]
    c  = ids.cpu_card
    c.value    = str(round(d["usage"], 1)) + "%"
    c.subtitle = str(d["freq"]) + "/" + str(mx) + " MHz"
    c.detail1  = str(d["cores"]) + " Cores  Procs:" + str(d["procs"])
    c.bar_pct  = d["usage"]


def _do_ram(ids, pct, lbl, free):
    # pct, lbl, free = get_ram() result passed in
    c = ids.ram_card
    c.value    = str(round(pct, 1)) + "%"
    c.subtitle = lbl
    c.detail1  = free
    c.bar_pct  = pct


def _do_battery(ids, d):
    # d = get_battery() result passed in
    c = ids.battery_card
    c.value    = str(d["pct"]) + "%"
    c.subtitle = d["eta"]
    c.detail1  = str(d["current"]) + "  " + str(d["volt"]) + "  Temp:" + str(d["temp"])
    c.bar_pct  = d["pct"]


def _do_network(ids, d):
    # d = get_network() result passed in from _stats
    # NO get_network() call here -> no LOAD_GLOBAL pollution
    # ids.network_card is first LOAD_ATTR -> clean slot
    dl   = d["dl"]
    ul   = d["ul"]
    sig  = d["sig"]
    ping = d["ping"]
    arc  = d["arc"]
    c = ids.network_card
    c.value    = dl
    c.subtitle = "Up: " + ul + "  Ping: " + ping
    c.detail1  = sig
    c.bar_pct  = arc


def _do_storage(ids, d):
    # d = get_storage() result passed in
    c = ids.storage_card
    c.value    = str(round(d["pct"], 1)) + "%"
    c.subtitle = d["used"] + " / " + d["total"]
    c.detail1  = "Free: " + d["free"]
    c.bar_pct  = d["pct"]


def _do_thermal(ids, d, mode):
    # d = get_thermal() result passed in
    if mode in (0,):
        t = d["cpu"];  maxl = d["cpu_max"];  lbl = "CPU"
    elif mode in (1,):
        t = d["gpu"];  maxl = d["gpu_max"];  lbl = "GPU"
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


# Module-level Clock callbacks - no self.attr access
def _fps_cb(dt):
    _app[0]._fps(dt)

def _stats_cb(dt):
    _app[0]._stats(dt)

def _clock_cb(dt):
    _app[0].root_widget.tick_clock(dt)


class KingwatchApp(App):

    def build(self):
        _app[0] = self
        mon = PerformanceMonitor()
        rw  = RootWidget()
        setattr(self, 'monitor',     mon)
        setattr(self, 'root_widget', rw)
        getattr(rw, 'apply_theme')("Dark Pro")
        getattr(rw, 'tick_clock')(0)
        self._fps(0)
        self._stats(0)
        _si = getattr(Clock, 'schedule_interval')
        _si(_fps_cb,   0.5)
        _si(_stats_cb, 1.0)
        _si(_clock_cb, 1.0)
        return rw

    def _fps(self, dt):
        _do_fps(self.root_widget.ids, self.monitor)

    def _stats(self, dt):
        ids = self.root_widget.ids

        # Fetch ALL data BEFORE calling card updaters
        cpu_d  = get_cpu()
        ram_d  = get_ram()
        bat_d  = get_battery()
        net_d  = get_network()
        sto_d  = get_storage()
        thr_d  = get_thermal()

        # Update cards - data passed as arguments, no LOAD_GLOBAL inside updaters
        _do_cpu(ids, cpu_d)
        _do_ram(ids, ram_d[0], ram_d[1], ram_d[2])
        _do_battery(ids, bat_d)
        _do_network(ids, net_d)
        _do_storage(ids, sto_d)

        _th["tick"] = _th["tick"] + 1
        if not (_th["tick"] < 10):
            _th["tick"] = 0
            _th["mode"] = (_th["mode"] + 1) % 3
        _do_thermal(ids, thr_d, _th["mode"])


if __name__ == "__main__":
    KingwatchApp().run()
