from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image as KivyImage
from kivy.core.image import Image as CoreImage
from kivy.properties import (
    StringProperty, ColorProperty,
    NumericProperty, BooleanProperty
)
from kivy.utils import get_color_from_hex
import io

from ui.gauge import draw_gauge, pct_to_color


class GaugeImage(KivyImage):
    """Kivy Image that renders a Pillow arc gauge."""

    pct       = NumericProperty(0)
    arc_color = ColorProperty(get_color_from_hex("#00E676"))
    bg_color  = ColorProperty(get_color_from_hex("#282828"))

    def __init__(self, **kw):
        super().__init__(**kw)
        self.nocache = True
        self.allow_stretch = True
        self.keep_ratio = True
        self.bind(pct=self._redraw,
                  arc_color=self._redraw,
                  bg_color=self._redraw,
                  size=self._redraw)

    def _redraw(self, *a):
        try:
            fg = tuple(int(c * 255) for c in self.arc_color[:3]) + (255,)
            bg = tuple(int(c * 255) for c in self.bg_color[:3])  + (255,)
            sz = max(int(min(self.width, self.height)), 60)
            png = draw_gauge(self.pct, size=sz, fg=fg, bg=bg,
                             thick=max(sz // 10, 7))
            buf = io.BytesIO(png)
            ci  = CoreImage(buf, ext="png", nocache=True)
            self.texture = ci.texture
        except Exception:
            pass


class StatCard(BoxLayout):
    title        = StringProperty("")
    value        = StringProperty("...")
    subtitle     = StringProperty("")
    detail1      = StringProperty("")
    detail2      = StringProperty("")
    bar_pct      = NumericProperty(0)
    show_bar     = BooleanProperty(True)
    bg_color     = ColorProperty(get_color_from_hex("#161616"))
    title_color  = ColorProperty(get_color_from_hex("#555555"))
    value_color  = ColorProperty(get_color_from_hex("#00E676"))
    sub_color    = ColorProperty(get_color_from_hex("#555555"))
    bar_color    = ColorProperty(get_color_from_hex("#00E676"))
    bar_bg       = ColorProperty(get_color_from_hex("#242424"))
    detail_color = ColorProperty(get_color_from_hex("#555555"))


class ThemeChip(BoxLayout):
    label       = StringProperty("Theme")
    selected    = BooleanProperty(False)
    chip_bg     = ColorProperty(get_color_from_hex("#1A1A1A"))
    chip_border = ColorProperty(get_color_from_hex("#333333"))
    chip_text   = ColorProperty(get_color_from_hex("#888888"))
