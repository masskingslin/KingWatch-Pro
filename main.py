from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ListProperty, BooleanProperty

from core.fps import PerformanceMonitor
from core.cpu import get_cpu
from core.ram import get_ram
from core.battery import get_battery
from core.network import get_network
from core.storage import get_storage
from core.thermal import get_thermal
from themes import THEME_NAMES, get_theme

Builder.load_file("kingwatch.kv")


class RootWidget(BoxLayout):
    bg        = ListProperty([0.04, 0.04, 0.04, 1])
    card_bg   = ListProperty([0.09, 0.09, 0.09, 1])
    accent    = ListProperty([0.0, 0.90, 0.46, 1])
    warn      = ListProperty([1.0, 0.57, 0.0,  1])
    danger    = ListProperty([1.0, 0.09, 0.27, 1])
