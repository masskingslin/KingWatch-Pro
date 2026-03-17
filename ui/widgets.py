"""
KingWatch Pro v17 - ui/widgets.py
ArcGauge with AUTO COLOR: green→orange→red based on pct.
StatCard widget.
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.properties import (
    StringProperty, ListProperty,
    NumericProperty, BooleanProperty
)
from kivy.graphics import Color, Line
from kivy.graphics import Rectangle as KvRect
from kivy.core.text import Label as CoreLabel


# Colour thresholds for auto-color mode
_GREEN  = [0.0,  0.88, 0.44, 1]   # < 60 %
_ORANGE = [1.0,  0.57, 0.0,  1]   # 60–80 %
_RED    = [1.0,  0.13, 0.27, 1]   # > 80 %


def _auto_color(pct):
    if pct >= 80:
        return _RED
    if pct >= 60:
        return _ORANGE
    return _GREEN


class ArcGauge(Widget):
    """
    270-degree sweep arc gauge.
    auto_color=True  → arc & label color set automatically by pct threshold.
    auto_color=False → uses arc_color / label_color as supplied.
    """
    pct         = NumericProperty(0)
    arc_color   = ListProperty([0, 0.88, 0.44, 1])
    arc_bg      = ListProperty([0.15, 0.15, 0.15, 1])
    label_text  = StringProperty("--")
    label_color = ListProperty([1, 1, 1, 1])
    thickness   = NumericProperty(10)
    auto_color  = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pct=self._draw, arc_color=self._draw, arc_bg=self._draw,
            label_text=self._draw, size=self._draw, pos=self._draw,
            auto_color=self._draw
        )

    def _draw(self, *_):
        self.canvas.clear()
        cx = self.x + self.width  / 2
        cy = self.y + self.height / 2
        r  = min(self.width, self.height) / 2 - self.thickness
        if r <= 2:
            return

        col   = _auto_color(self.pct) if self.auto_color else self.arc_color
        lcol  = col if self.auto_color else self.label_color
        d     = r * 2
        bx, by = cx - r, cy - r
        sweep = max(0.0, min(270.0, (self.pct / 100.0) * 270.0))

        with self.canvas:
            # Background ring
            Color(*self.arc_bg)
            Line(ellipse=(bx, by, d, d, 225, 495),
                 width=self.thickness, cap="round")
            # Progress arc
            if sweep > 0:
                Color(*col)
                Line(ellipse=(bx, by, d, d, 225, 225 + sweep),
                     width=self.thickness, cap="round")

        # Centre value label
        fs  = max(10, int(r * 0.38))
        lbl = CoreLabel(text=self.label_text, font_size=fs,
                        bold=True, color=lcol)
        lbl.refresh()
        t = lbl.texture
        with self.canvas:
            Color(1, 1, 1, 1)
            KvRect(texture=t,
                   pos=(cx - t.width/2, cy - t.height/2),
                   size=t.size)


class StatCard(BoxLayout):
    title        = StringProperty("")
    value        = StringProperty("--")
    subtitle     = StringProperty("")
    detail1      = StringProperty("")

    bg_color     = ListProperty([0.09, 0.09, 0.09, 1])
    title_color  = ListProperty([0.33, 0.33, 0.33, 1])
    value_color  = ListProperty([0.0,  0.88, 0.44, 1])
    sub_color    = ListProperty([1,    1,    1,    1])
    detail_color = ListProperty([0.55, 0.55, 0.55, 1])
    bar_color    = ListProperty([0.0,  0.88, 0.44, 1])
    bar_bg       = ListProperty([0.15, 0.15, 0.15, 1])
    bar_pct      = NumericProperty(0)
    auto_color   = BooleanProperty(True)
