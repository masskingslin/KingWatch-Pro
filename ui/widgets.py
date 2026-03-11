from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.properties import NumericProperty, StringProperty


class CircularGauge(BoxLayout):

    value = NumericProperty(0)
    label = StringProperty("")


class InfoCard(BoxLayout):

    title = StringProperty("")
    value = StringProperty("")