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
    text_col  = ListProperty([1,   1,   1,    1])
    dim_col   = ListProperty([0.33,0.33,0.33, 1])
    collapsed = BooleanProperty(False)

    theme_index = 0

    def apply_theme(self, name):
        t = get_theme(name)

        def h(hex_str):
            hx = hex_str.lstrip("#")
            return [int(hx[i:i+2], 16) / 255 for i in (0, 2, 4)] + [1]

        self.bg       = h(t["BG"])
        self.card_bg  = h(t["CARD"])
        self.accent   = h(t["ACCENT"])
        self.warn     = h(t["WARN"])
        self.danger   = h(t["DANGER"])
        self.text_col = h(t["TEXT"])
        self.dim_col  = h(t["DIM"])

    def cycle_theme(self):
        self.theme_index = (self.theme_index + 1) % len(THEME_NAMES)
        self.apply_theme(THEME_NAMES[self.theme_index])

    def toggle_collapse(self):
        self.collapsed = not self.collapsed


class KingWatchApp(App):

    def build(self):
        self.monitor = PerformanceMonitor()
        self.root_widget = RootWidget()
        self.root_widget.apply_theme("Dark Pro")
        Clock.schedule_interval(self.update_stats, 1)
        return self.root_widget

    def update_stats(self, dt):
        r = self.root_widget

        # â”€â”€ FPS / GPU â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        fps = self.monitor.get_fps()
        gpu = self.monitor.get_gpu()
        r.ids.fps_card.value    = str(fps)
        r.ids.fps_card.subtitle = f"GPU Load: {gpu}"
        r.ids.fps_card.bar_pct  = min(100, (fps / 60) * 100)

        # â”€â”€ CPU â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        cpu = get_cpu()
        r.ids.cpu_card.value    = f"{cpu['usage']:.1f}%"
        r.ids.cpu_card.subtitle = f"{cpu['freq']} MHz  |  {cpu['cores']} Cores"
        r.ids.cpu_card.detail1  = f"Processes: {cpu['procs']}"
        r.ids.cpu_card.detail2  = "[sys-wide]"
        r.ids.cpu_card.bar_pct  = cpu['usage']

        # â”€â”€ RAM â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        ram_pct, ram_str = get_ram()
        r.ids.ram_card.value    = f"{ram_pct:.1f}%"
        r.ids.ram_card.subtitle = ram_str
        r.ids.ram_card.bar_pct  = ram_pct

        # â”€â”€ Battery â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        batt = get_battery()
        r.ids.battery_card.value    = f"{batt['pct']}%"
        r.ids.battery_card.subtitle = batt['eta']
        r.ids.battery_card.detail1  = f"{batt['current']}  {batt['volt']}  {batt['power']}"
        r.ids.battery_card.detail2  = f"Temp: {batt['temp']}"
        r.ids.battery_card.bar_pct  = batt['pct']

        # â”€â”€ Network â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        net = get_network()
        r.ids.network_card.value    = f"â†“ {net['dl']}"
        r.ids.network_card.subtitle = f"â†‘ {net['ul']}"
        r.ids.network_card.detail1  = f"Ping: {net['ping']}   {net['signal']}"
        r.ids.network_card.show_bar = False

        # â”€â”€ Storage â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        storage = get_storage()
        r.ids.storage_card.value    = f"{storage['pct']:.1f}%"
        r.ids.storage_card.subtitle = f"{storage['used']} / {storage['total']}"
        r.ids.storage_card.bar_pct  = storage['pct']

        # â”€â”€ Thermal â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        therm = get_thermal()
        r.ids.thermal_card.value    = f"{therm['cpu']}Â°C"
        r.ids.thermal_card.subtitle = f"Max: {therm['max']}Â°C"
        r.ids.thermal_card.detail1  = therm['detail']
        r.ids.thermal_card.bar_pct  = min(100, (therm['max'] / 90) * 100)


if __name__ == "__main__":
    KingWatchApp().run()