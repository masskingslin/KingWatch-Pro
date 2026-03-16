from kivy.uix.boxlayout import BoxLayout
from kivy.properties import (
    StringProperty,
    NumericProperty,
    BooleanProperty,
    ColorProperty
)
from kivy.utils import get_color_from_hex


class StatCard(BoxLayout):

    title = StringProperty("")
    value = StringProperty("")
    subtitle = StringProperty("")

    detail1 = StringProperty("")
    detail2 = StringProperty("")

    bar_pct = NumericProperty(0)
    show_bar = BooleanProperty(True)

    bg_color = ColorProperty(get_color_from_hex("#161616"))
    title_color = ColorProperty(get_color_from_hex("#666666"))
    value_color = ColorProperty(get_color_from_hex("#00E676"))
    sub_color = ColorProperty(get_color_from_hex("#666666"))

    bar_color = ColorProperty(get_color_from_hex("#00E676"))
    bar_bg = ColorProperty(get_color_from_hex("#333333"))

    detail_color = ColorProperty(get_color_from_hex("#777777"))