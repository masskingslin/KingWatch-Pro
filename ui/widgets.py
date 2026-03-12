from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.properties import StringProperty, ColorProperty, NumericProperty, BooleanProperty
from kivy.utils import get_color_from_hex


class InfoCard(BoxLayout):
    """Standard sensor card with optional progress bar and detail line."""
    title        = StringProperty("--")
    value        = StringProperty("...")
    detail       = StringProperty("")
    bar_value    = NumericProperty(0)      # 0-100 for progress bar
    show_bar     = BooleanProperty(False)
    bg_color     = ColorProperty(get_color_from_hex("#1E1E1E"))
    title_color  = ColorProperty(get_color_from_hex("#AAAAAA"))
    value_color  = ColorProperty(get_color_from_hex("#00C853"))
    bar_color    = ColorProperty(get_color_from_hex("#00C853"))
    detail_color = ColorProperty(get_color_from_hex("#666666"))


class ThemeChip(BoxLayout):
    """Single theme chip button."""
    theme_name   = StringProperty("Dark Pro")
    is_selected  = BooleanProperty(False)
    chip_color   = ColorProperty(get_color_from_hex("#1E1E1E"))
    text_color   = ColorProperty(get_color_from_hex("#FFFFFF"))
    border_color = ColorProperty(get_color_from_hex("#333333"))