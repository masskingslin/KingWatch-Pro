"""
KingWatch Pro v17 - ui/widgets.py
ArcGauge  : circular canvas gauge
StatCard  : card widget using ArcGauge
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.properties import (
    StringProperty, ListProperty,
    NumericProperty, BooleanProperty
)
from kivy.graphics import Color, Line, Rectangle as KvRect
from kivy.core.text import Label as CoreLabel


class ArcGauge(Widget):
    """
    Circular arc gauge.
    - 270-degree sweep (225 start, clockwise)
    - Background ring + filled progress arc
    - Centre value label + optional sub label
    """
    pct         = NumericProperty(0)
    arc_color   = ListProperty([0, 0.9, 0.46, 1])
    arc_bg      = ListProperty([0.18, 0.18, 0.18, 1])
    label_text  = StringProperty("--")
    label_color = ListProperty([1, 1, 1, 1])
    sub_text    = StringProperty("")
    sub_color   = ListProperty([0.55, 0.55, 0.55, 1])
    thickness   = NumericProperty(10)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            pct=self._draw, arc_color=self._draw,
            arc_bg=self._draw, label_text=self._draw,
            sub_text=self._draw, size=self._draw, pos=self._draw
        )

    def _draw(self, *_):
        self.canvas.clear()
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        r  = min(self.width, self.height) / 2 - self.thickness
        if r <= 2:
            return
        d  = r * 2
        bx = cx - r
        by = cy - r

        with self.canvas:
            # Background ring
            Color(*self.arc_bg)
            Line(ellipse=(bx, by, d, d, 225, 495), width=self.thickness, cap="round")
            # Progress arc
            sweep = max(0, (min(self.pct, 100) / 100.0) * 270)
            if sweep > 0:
                Color(*self.arc_color)
                Line(ellipse=(bx, by, d, d, 225, 225 + sweep), width=self.thickness, cap="round")

        # Value label centred
        fs = max(10, int(r * 0.40))
        lbl = CoreLabel(text=self.label_text, font_size=fs, bold=True, color=self.label_color)
        lbl.refresh()
        t = lbl.texture
        vy = cy - t.height / 2 + (t.height * 0.18 if self.sub_text else 0)
        with self.canvas:
            Color(1, 1, 1, 1)
            KvRect(texture=t, pos=(cx - t.width / 2, vy), size=t.size)

        if self.sub_text:
            sfs = max(7, int(r * 0.21))
            slbl = CoreLabel(text=self.sub_text, font_size=sfs, color=self.sub_color)
            slbl.refresh()
            st = slbl.texture
            with self.canvas:
                Color(1, 1, 1, 1)
                KvRect(texture=st,
                       pos=(cx - st.width / 2, cy - t.height / 2 - st.height * 0.5),
                       size=st.size)


class StatCard(BoxLayout):
    title        = StringProperty("")
    value        = StringProperty("--")
    subtitle     = StringProperty("")
    detail1      = StringProperty("")
    detail2      = StringProperty("")

    bg_color     = ListProperty([0.09, 0.09, 0.09, 1])
    title_color  = ListProperty([0.33, 0.33, 0.33, 1])
    value_color  = ListProperty([0.0,  0.90, 0.46, 1])
    sub_color    = ListProperty([0.55, 0.55, 0.55, 1])
    detail_color = ListProperty([0.44, 0.44, 0.44, 1])
    bar_color    = ListProperty([0.0,  0.90, 0.46, 1])
    bar_bg       = ListProperty([0.18, 0.18, 0.18, 1])

    bar_pct      = NumericProperty(0)
    show_bar     = BooleanProperty(True)
