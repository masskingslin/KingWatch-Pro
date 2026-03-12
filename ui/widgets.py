import math
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.properties import (
    StringProperty, ColorProperty,
    NumericProperty, BooleanProperty, ListProperty
)
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, Line, Ellipse, RoundedRectangle


class ArcGauge(Widget):
    """
    Circular arc gauge -- fills clockwise from bottom-left.
    Shows percentage as a colored arc with a glowing dot at tip.
    """
    pct        = NumericProperty(0)
    arc_color  = ColorProperty(get_color_from_hex("#00E676"))
    bg_color   = ColorProperty(get_color_from_hex("#242424"))
    size_hint  = (None, None)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pct=self._draw, arc_color=self._draw,
                  bg_color=self._draw, size=self._draw, pos=self._draw)

    def _draw(self, *a):
        self.canvas.clear()
        cx, cy = self.center_x, self.center_y
        r = min(self.width, self.height) / 2.0 - 6
        if r < 4:
            return
        start_angle = -225   # bottom-left
        span        = (max(0, min(100, self.pct)) / 100.0) * 270.0

        with self.canvas:
            # Background ring
            Color(*self.bg_color[:3], 0.6)
            Line(ellipse=(cx-r, cy-r, r*2, r*2, start_angle, start_angle+270),
                 width=5, cap="round")

            # Foreground arc
            if span > 0:
                Color(*self.arc_color[:3], 1)
                Line(ellipse=(cx-r, cy-r, r*2, r*2, start_angle, start_angle+span),
                     width=5, cap="round")
                # Glowing dot at tip
                ang = math.radians(start_angle + span)
                tx  = cx + r * math.cos(ang)
                ty  = cy + r * math.sin(ang)
                d   = 5
                Color(*self.arc_color[:3], 0.6)
                Ellipse(pos=(tx-d*1.5, ty-d*1.5), size=(d*3, d*3))
                Color(*self.arc_color[:3], 1)
                Ellipse(pos=(tx-d, ty-d), size=(d*2, d*2))


class SparkLine(Widget):
    """
    Mini live trend line -- last N readings as a sparkline.
    """
    points_data = ListProperty([])
    line_color  = ColorProperty(get_color_from_hex("#00E676"))
    fill_color  = ColorProperty(get_color_from_hex("#00E67620"))

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(points_data=self._draw, size=self._draw,
                  pos=self._draw, line_color=self._draw)

    def push(self, value, max_points=20):
        pts = list(self.points_data) + [value]
        self.points_data = pts[-max_points:]

    def _draw(self, *a):
        self.canvas.clear()
        data = self.points_data
        if len(data) < 2:
            return
        w, h  = self.width, self.height
        x0, y0 = self.x, self.y
        mn, mx = min(data), max(data)
        rng    = max(mx - mn, 1)

        def px(i):
            return x0 + i / (len(data)-1) * w

        def py(v):
            return y0 + ((v - mn) / rng) * (h - 2) + 1

        pts = []
        for i, v in enumerate(data):
            pts += [px(i), py(v)]

        with self.canvas:
            Color(*self.line_color[:3], 0.9)
            Line(points=pts, width=1.4, cap="round", joint="round")
            # Dot at latest value
            lx, ly = pts[-2], pts[-1]
            Color(*self.line_color[:3], 1)
            d = 3
            Ellipse(pos=(lx-d, ly-d), size=(d*2, d*2))


class StatCard(BoxLayout):
    title        = StringProperty("--")
    value        = StringProperty("...")
    subtitle     = StringProperty("")
    detail1      = StringProperty("")
    detail2      = StringProperty("")
    bar_pct      = NumericProperty(0)
    show_bar     = BooleanProperty(False)
    bg_color     = ColorProperty(get_color_from_hex("#161616"))
    title_color  = ColorProperty(get_color_from_hex("#555555"))
    value_color  = ColorProperty(get_color_from_hex("#00E676"))
    sub_color    = ColorProperty(get_color_from_hex("#555555"))
    bar_color    = ColorProperty(get_color_from_hex("#00E676"))
    bar_bg       = ColorProperty(get_color_from_hex("#242424"))
    detail_color = ColorProperty(get_color_from_hex("#555555"))
    arc_color    = ColorProperty(get_color_from_hex("#00E676"))
    arc_bg       = ColorProperty(get_color_from_hex("#242424"))


class ThemeChip(BoxLayout):
    label        = StringProperty("Theme")
    selected     = BooleanProperty(False)
    chip_bg      = ColorProperty(get_color_from_hex("#1A1A1A"))
    chip_border  = ColorProperty(get_color_from_hex("#333333"))
    chip_text    = ColorProperty(get_color_from_hex("#888888"))
