from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, NumericProperty


class StatCard(BoxLayout):

    title = StringProperty("")
    value = StringProperty("")
    subtitle = StringProperty("")
    percent = NumericProperty(0)


class CpuWidget(StatCard):
    pass


class RamWidget(StatCard):
    pass


class StorageWidget(StatCard):
    pass


class BatteryWidget(StatCard):
    pass


class NetworkWidget(StatCard):
    pass


class ThermalWidget(StatCard):
    pass