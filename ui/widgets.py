from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, NumericProperty


class CircularGauge(BoxLayout):

    label = StringProperty("")
    value = StringProperty("")
    percent = NumericProperty(0)


class InfoCard(BoxLayout):

    title = StringProperty("")
    value = StringProperty("")
    subtitle = StringProperty("")


class MonitorWidget(BoxLayout):
    pass