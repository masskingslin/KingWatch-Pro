"""
ArcGauge — KingWatch Pro v15
Circular arc progress widget drawn with Kivy canvas primitives.
Color dynamically transitions: Green → Amber → Red based on value.
No external dependencies — pure Kivy canvas.
"""

import math
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ListProperty
from kivy.graphics import Color, Line, Ellipse
from kivy.lang import Builder

Builder.load_string("""
<ArcGauge>:
    canvas:
        # Drawn in Python via _redraw
""")


class ArcGauge(Widget):
    value     = NumericProperty(0)
    arc_color = ListProperty([0.24, 0.86, 0.51, 1])

    _COLOR_TRACK = (0.15, 0.15, 0.22, 1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(
            value     = self._redraw,
            arc_color = self._redraw,
            size      = self._redraw,
            pos       = self._redraw,
        )

    def _auto_color(self):
        if self.value < 60:
            return (0.24, 0.86, 0.51, 1)
        elif self.value < 80:
            return (0.98, 0.80, 0.10, 1)
        else:
            return (0.97, 0.25, 0.25, 1)

    def _redraw(self, *_):
        self.canvas.clear()
        cx = self.x + self.width  / 2
        cy = self.y + self.height / 2
        r  = min(self.width, self.height) / 2 - 12

        if r <= 0:
            return

        sweep = min(max(self.value, 0), 100) / 100.0

        with self.canvas:
            Color(*self._COLOR_TRACK)
            Line(
                circle=(cx, cy, r, -220, 40),
                width=10,
                cap="round",
            )

            arc_color = list(self.arc_color[:3]) + [1.0]
            Color(*arc_color)

            start_angle = -220
            end_angle   = start_angle + (260 * sweep)
            if sweep > 0:
                Line(
                    circle=(cx, cy, r, start_angle, end_angle),
                    width=10,
                    cap="round",
                )

            dot_r = 5
            Color(*arc_color)
            Ellipse(
                pos=(cx - dot_r, cy - dot_r),
                size=(dot_r * 2, dot_r * 2)
            )

            Color(0.4, 0.4, 0.5, 0.7)
            for pct in (0, 50, 100):
                angle_deg = -220 + (260 * pct / 100)
                angle_rad = math.radians(angle_deg)
                x1 = cx + (r + 2) * math.cos(angle_rad)
                y1 = cy + (r + 2) * math.sin(angle_rad)
                x2 = cx + (r + 6) * math.cos(angle_rad)
                y2 = cy + (r + 6) * math.sin(angle_rad)
                Line(points=[x1, y1, x2, y2], width=1.5)
