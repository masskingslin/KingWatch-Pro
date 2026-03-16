from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ColorProperty
from kivy.utils import get_color_from_hex

from ui.theme import get_theme

from core.cpu import get_cpu
from core.ram import get_ram
from core.storage import get_storage
from core.battery import get_battery
from core.network import get_network
from core.thermal import get_thermal
from core.fps import FPSMonitor


class RootWidget(BoxLayout):

    bg = ColorProperty([0,0,0,1])
    card = ColorProperty([0,0,0,1])
    card2 = ColorProperty([0,0,0,1])
    text = ColorProperty([1,1,1,1])
    dim = ColorProperty([0.5,0.5,0.5,1])
    accent = ColorProperty([0,1,0,1])

    def on_kv_post(self, base_widget):

        theme = get_theme()

        self.bg = get_color_from_hex(theme["BG"])
        self.card = get_color_from_hex(theme["CARD"])
        self.card2 = get_color_from_hex(theme["CARD2"])
        self.text = get_color_from_hex(theme["TEXT"])
        self.dim = get_color_from_hex(theme["DIM"])
        self.accent = get_color_from_hex(theme["ACCENT"])

        self.fps_monitor = FPSMonitor()

        Clock.schedule_interval(self.update_stats, 2)

    def update_stats(self, dt):

        cpu = get_cpu()
        ram = get_ram()
        storage = get_storage()
        battery = get_battery()
        network = get_network()
        thermal = get_thermal()

        fps = self.fps_monitor.get_fps()
        refresh = self.fps_monitor.get_refresh_rate()

        refresh = max(refresh, 60)

        self.ids.cpu_card.value = f"{cpu['usage']:.1f}%"
        self.ids.cpu_card.bar_pct = cpu["usage"]

        self.ids.ram_card.value = f"{ram['pct']:.1f}%"
        self.ids.ram_card.bar_pct = ram["pct"]

        self.ids.storage_card.value = f"{storage['pct']:.1f}%"
        self.ids.storage_card.bar_pct = storage["pct"]

        self.ids.battery_card.value = f"{battery['pct']}%"
        self.ids.battery_card.bar_pct = battery["pct"]

        self.ids.network_card.value = network["dl"]
        self.ids.network_card.subtitle = network["ping"]

        self.ids.thermal_card.value = f"{thermal['max']}°C"
        self.ids.thermal_card.bar_pct = thermal["max"]

        self.ids.fps_card.value = str(fps)
        self.ids.fps_card.subtitle = f"{refresh} Hz"
        self.ids.fps_card.bar_pct = min((fps / refresh) * 100, 100)


class KingWatchApp(App):

    def build(self):
        return Builder.load_file("kingwatch.kv")


if __name__ == "__main__":
    KingWatchApp().run()