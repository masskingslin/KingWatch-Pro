from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ListProperty, NumericProperty, BooleanProperty


class StatCard(BoxLayout):
    """Custom stat card widget with progress bar and details"""
    
    # Basic properties
    title = StringProperty("STAT")
    value = StringProperty("--")
    subtitle = StringProperty("")
    
    # Detail rows
    detail1 = StringProperty("")
    detail2 = StringProperty("")
    
    # Colors
    bg_color = ListProperty([0.09, 0.09, 0.09, 1])
    title_color = ListProperty([0.33, 0.33, 0.33, 1])
    value_color = ListProperty([0.0, 0.90, 0.46, 1])
    sub_color = ListProperty([0.5, 0.5, 0.5, 1])
    detail_color = ListProperty([0.5, 0.5, 0.5, 1])
    
    # Progress bar
    show_bar = BooleanProperty(True)
    bar_pct = NumericProperty(0)
    bar_color = ListProperty([0.0, 0.90, 0.46, 1])
    bar_bg = ListProperty([0.15, 0.15, 0.15, 1])