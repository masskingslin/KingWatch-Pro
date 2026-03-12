from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty


class InfoCard(BoxLayout):
    icon  = StringProperty("●")
    title = StringProperty("--")
    value = StringProperty("...")