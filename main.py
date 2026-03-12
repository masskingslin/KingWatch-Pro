import os, sys, threading, math

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
from kivy.graphics import Color, Line, Ellipse, RoundedRectangle

from ui.widgets import StatCard, ThemeChip  # noqa - register with Kivy

from themes import THEME_NAMES, get_theme, DEFAULT_THEME
from core.cpu     import get_cpu, get_cpu_freq, get_cpu_cores, get_cpu_procs, get_cpu_uptime
from core.ram     import get_ram
from core.battery import get_battery
from core.network import get_network
from core.storage import get_storage
from core.thermal import get_thermal


def _draw_arc(widget, pct, arc_col, bg_col):
    """Draw circular arc gauge on a plain Widget canvas."""
    widget.canvas.clear()
    cx = widget.center_x
    cy = widget.center_y
    r  = min(widget.width, widget.height) / 2.0 - 5
    if r < 4:
        return
    start = -225
    span  = (max(0.0, min(100.0, pct)) / 100.0) * 270.0
    with widget.canvas:
        Color(*bg_col[:3], 0.5)
        Line(ellipse=(cx-r, cy-r, r*2, r*2, start, start+270), width=5, cap="round")
        if span > 0:
            Color(*arc_col[:3], 1.0)
            Line(ellipse=(cx-r, cy-r, r*2, r*2, start, start+span), width=5, cap="round")
            ang = math.radians(start + span)
            tx  = cx + r * math.cos(ang)
            ty  = cy + r * math.sin(ang)
            d   = 5
            Color(*arc_col[:3], 0.5)
            Ellipse(pos=(tx-d*1.5, ty-d*1.5), size=(d*3, d*3))
            Color(*arc_col[:3], 1.0)
            Ellipse(pos=(tx-d, ty-d), size=(d*2, d*2))


def _draw_spark(widget, data, line_col):
    """Draw sparkline trend on a plain Widget canvas."""
    widget.canvas.clear()
    if len(data) < 2:
        return
    w, h   = widget.width, widget.height
    x0, y0 = widget.x, widget.y
    mn, mx  = min(data), max(data)
    rng     = max(mx - mn, 1.0)

    def px(i):
        return x0 + i / (len(data) - 1.0) * w

    def py(v):
        return y0 + ((v - mn) / rng) * (h - 4) + 2

    pts = []
    for i, v in enumerate(data):
        pts += [px(i), py(v)]

    with widget.canvas:
        Color(*line_col[:3], 0.85)
        Line(points=pts, width=1.5, cap="round", joint="round")
        lx, ly = pts[-2], pts[-1]
        d = 3
        Color(*line_col[:3], 1.0)
        Ellipse(pos=(lx-d, ly-d), size=(d*2, d*2))


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
        # Bind spark widget redraws on size changes
        self._bind_sparks()
        # Start CPU worker in background (non-blocking)
        threading.Thread(target=self._start_cpu, daemon=True).start()
        # First stats update
        self.update_stats()
        Clock.schedule_interval(self.update_stats, 3)

    def _start_cpu(self):
        from core.cpu import _ensure_started
        _ensure_started()

    def _bind_sparks(self):
        """Bind size events so arcs/sparks redraw on layout."""
        for cid in ["cpu_card", "ram_card", "storage_card",
                    "battery_card", "network_card", "thermal_card"]:
            try:
                card = self.ids[cid]
                sw   = card.ids.spark_widget
                sw.bind(size=lambda w, v, c=card: self._redraw_spark(c))
                sw.bind(pos=lambda w, v, c=card: self._redraw_spark(c))
            except Exception:
                pass

    def _redraw_spark(self, card):
        try:
            acc = list(self.accent)
            sw  = card.ids.spark_widget
            _draw_spark(sw, card.spark_data, acc)
        except Exception:
            pass

    # -- THEME -----------------------------------------------------------
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

    # -- SENSORS ---------------------------------------------------------
    def update_stats(self, *a):
        threading.Thread(target=self._collect, daemon=True).start()

    def _collect(self):
        t   = get_theme(self._tname)
        acc = t["ACCENT"]
        wrn = t["WARN"]
        dng = t["DANGER"]

        def clr(pct, lo=75, hi=90):
            if pct >= hi: return get_color_from_hex(dng)
            if pct >= lo: return get_color_from_hex(wrn)
            return get_color_from_hex(acc)

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
        except: bat = {"pct":0.0,"status":"ERR","cur":"N/A","volt":"N/A",
                        "power":"N/A","temp":"N/A","eta":"N/A","eta_label":"ETA"}

        try:    net = get_network()
        except: net = {"dl":"ERR","ul":"ERR","ping":"N/A","signal":"N/A"}

        try:    th_max, th_cpu, th_det = get_thermal()
        except: th_max, th_cpu, th_det = 0.0, 0.0, "N/A"

        def apply(dt):
            bg2 = list(self.card2)

            # CPU
            c = self.ids.cpu_card
            cc = clr(cpu_v)
            c.value     = "%.1f%%" % cpu_v
            c.subtitle  = "usage"
            c.bar_pct   = cpu_v
            c.bar_color = cc
            c.detail1   = "Freq: %s   Cores: %s" % (cpu_freq, cpu_cores)
            c.detail2   = "Procs: %s   Up: %s" % (cpu_procs, cpu_up)
            c.push_spark(cpu_v)
            try:
                _draw_spark(c.ids.spark_widget, c.spark_data, list(cc))
            except Exception:
                pass

            # RAM
            c = self.ids.ram_card
            cc = clr(ram_v)
            c.value     = "%.1f%%" % ram_v
            c.subtitle  = "used"
            c.bar_pct   = ram_v
            c.bar_color = cc
            c.detail1   = ram_d
            c.push_spark(ram_v)
            try:
                _draw_spark(c.ids.spark_widget, c.spark_data, list(cc))
            except Exception:
                pass

            # Storage
            c = self.ids.storage_card
            cc = clr(sto_v)
            c.value     = "%.1f%%" % sto_v
            c.subtitle  = "used"
            c.bar_pct   = sto_v
            c.bar_color = cc
            c.detail1   = sto_d
            c.push_spark(sto_v)
            try:
                _draw_spark(c.ids.spark_widget, c.spark_data, list(cc))
            except Exception:
                pass

            # Battery
            pct = bat["pct"]
            c   = self.ids.battery_card
            bat_clr = (get_color_from_hex(acc) if "Charg" in bat["status"]
                       else get_color_from_hex(dng) if pct <= 10
                       else get_color_from_hex(wrn) if pct <= 20
                       else get_color_from_hex(acc))
            c.value     = "%.0f%%" % pct
            c.subtitle  = bat["status"]
            c.bar_pct   = pct
            c.bar_color = bat_clr
            c.detail1   = "Curr: %s   Volt: %s   Pwr: %s" % (bat["cur"], bat["volt"], bat["power"])
            c.detail2   = "Temp: %s   %s: %s" % (bat["temp"], bat.get("eta_label","ETA"), bat["eta"])
            c.push_spark(pct)
            try:
                _draw_spark(c.ids.spark_widget, c.spark_data, list(bat_clr))
            except Exception:
                pass

            # Network
            c = self.ids.network_card
            cc = get_color_from_hex(acc)
            c.value     = net["dl"]
            c.subtitle  = net["ping"]
            c.bar_pct   = 0
            c.bar_color = cc
            c.detail1   = "DL: %s   UL: %s" % (net["dl"], net["ul"])
            c.detail2   = "%s   %s" % (net["signal"], net["ping"])
            try:
                ping_val = float(net["ping"].split()[0])
                cc = (get_color_from_hex(dng) if ping_val > 200
                      else get_color_from_hex(wrn) if ping_val > 80
                      else get_color_from_hex(acc))
                c.bar_pct = min(ping_val / 5.0, 100)
                c.push_spark(min(ping_val, 500))
                _draw_spark(c.ids.spark_widget, c.spark_data, list(cc))
            except Exception:
                pass

            # Thermal
            c = self.ids.thermal_card
            bar = min(th_max / 120.0 * 100, 100)
            cc  = clr(bar, lo=54, hi=75)
            c.value     = "%.1fdeg" % th_max
            c.subtitle  = "CPU %.1fdeg" % th_cpu
            c.bar_pct   = bar
            c.bar_color = cc
            c.detail1   = th_det
            c.push_spark(float(th_max))
            try:
                _draw_spark(c.ids.spark_widget, c.spark_data, list(cc))
            except Exception:
                pass

        Clock.schedule_once(apply, 0)


class MonitorApp(App):
    def build(self):
        Window.clearcolor = (0, 0, 0, 1)
        Builder.load_file(os.path.join(app_dir, "kingwatch.kv"))
        return RootWidget()


if __name__ == "__main__":
    MonitorApp().run()
