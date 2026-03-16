from kivy.uix.boxlayout import BoxLayout
from kivy.properties import (
    StringProperty,
    NumericProperty,
    BooleanProperty,
    ColorProperty,
)
from kivy.utils import get_color_from_hex


class StatCard(BoxLayout):
    """
    Reusable stat card with:
      - title       – card header label
      - value       – large primary value (e.g. "72.4%")
      - subtitle    – secondary text below value (e.g. "2980MB / 4096MB")
      - detail1/2   – two small detail rows
      - bar_pct     – 0-100 for the progress bar
      - show_bar    – toggle progress bar visibility
      - bg_color    – card background
      - bar_color   – filled bar colour (set per-card to accent/warn/danger)
    """
    title        = StringProperty("")
    value        = StringProperty("—")
    subtitle     = StringProperty("")
    detail1      = StringProperty("")
    detail2      = StringProperty("")
    bar_pct      = NumericProperty(0)
    show_bar     = BooleanProperty(True)

    bg_color     = ColorProperty(get_color_from_hex("#161616"))
    title_color  = ColorProperty(get_color_from_hex("#555555"))
    value_color  = ColorProperty(get_color_from_hex("#00E676"))
    sub_color    = ColorProperty(get_color_from_hex("#777777"))
    detail_color = ColorProperty(get_color_from_hex("#555555"))
    bar_color    = ColorProperty(get_color_from_hex("#00E676"))
    bar_bg       = ColorProperty(get_color_from_hex("#2A2A2A"))
