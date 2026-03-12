from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock

# IMPORT WIDGETS FIRST (important for KV)
from ui.widgets import CircularGauge, InfoCard

# IMPORT CORE MODULES
from core.cpu import get_cpu
from core.ram import get_ram
from core.battery import get_battery
from core.network import get_network
from core.storage import get_storage
from core.thermal import get_temp


class RootWidget(BoxLayout):

    def update_stats(self, *args):

        self.ids.cpu_widget.value = str(get_cpu()) + "%"
        self.ids.ram_widget.value = str(get_ram()) + "%"
        self.ids.battery_widget.value = str(get_battery()) + "%"
        self.ids.network_widget.value = str(get_network())
        self.ids.storage_widget.value = str(get_storage()) + "%"
        self.ids.temp_widget.value = str(get_temp()) + "°C"


class KingWatchApp(App):

    def build(self):

        root = Builder.load_file("kingwatch.kv")

        Clock.schedule_interval(root.update_stats, 3)

        return root


if __name__ == "__main__":
    KingWatchApp().run()