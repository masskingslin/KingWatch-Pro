from kivy.uix.boxlayout import BoxLayout
from kivy.properties import (
    StringProperty, ColorProperty,
    NumericProperty, BooleanProperty
)
from kivy.utils import get_color_from_hex


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
