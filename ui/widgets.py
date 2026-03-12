from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.properties import (
    StringProperty, ColorProperty,
    NumericProperty, BooleanProperty, ListProperty
)
from kivy.utils import get_color_from_hex


class StatCard(BoxLayout):
    """Full sensor card: title, value, progress bar, 2 detail rows."""
    title        = StringProperty("--")
    value        = StringProperty("...")
    subtitle     = StringProperty("")     # line below value
    detail1      = StringProperty("")     # detail row 1
    detail2      = StringProperty("")     # detail row 2
    bar_pct      = NumericProperty(0)     # 0–100
    show_bar     = BooleanProperty(False)
    bg_color     = ColorProperty(get_color_from_hex("#161616"))
    title_color  = ColorProperty(get_color_from_hex("#555555"))
    value_color  = ColorProperty(get_color_from_hex("#00E676"))
    bar_color    = ColorProperty(get_color_from_hex("#00E676"))
    bar_bg       = ColorProperty(get_color_from_hex("#2A2A2A"))
    sub_color    = ColorProperty(get_color_from_hex("#888888"))
    detail_color = ColorProperty(get_color_from_hex("#555555"))


class ThemeChip(BoxLayout):
    """Selectable theme chip."""
    label        = StringProperty("Theme")
    selected     = BooleanProperty(False)
    chip_bg      = ColorProperty(get_color_from_hex("#1E1E1E"))
    chip_border  = ColorProperty(get_color_from_hex("#333333"))
    chip_text    = ColorProperty(get_color_from_hex("#AAAAAA"))
