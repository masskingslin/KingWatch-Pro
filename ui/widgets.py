"""
KingWatch Pro - ui/widgets.py
StatCard widget definition. No emoji.
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import (
    StringProperty, ListProperty,
    NumericProperty, BooleanProperty
)


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