from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ColorProperty
from kivy.utils import get_color_from_hex


class InfoCard(BoxLayout):
    title       = StringProperty("--")
    value       = StringProperty("...")
    bg_color    = ColorProperty(get_color_from_hex("#1E1E1E"))
    title_color = ColorProperty(get_color_from_hex("#FFFFFF"))
    value_color = ColorProperty(get_color_from_hex("#00C853"))