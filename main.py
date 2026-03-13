from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock

# IMPORTANT: load widgets first
from ui.widgets import *
from ui.themes import THEMES

# load UI
KV = Builder.load_file("kingwatch.kv")


class KingWatchApp(App):

    def build(self):
        self.theme = THEMES["dark_pro"]

        Clock.schedule_interval(self.update_stats, 1)

        return KV

    def update_stats(self, dt):

        root = self.root

        # demo values (replace with core later)
        root.ids.cpu_card.value = "12%"
        root.ids.cpu_card.percent = 12

        root.ids.ram_card.value = "68%"
        root.ids.ram_card.percent = 68

        root.ids.storage_card.value = "64%"
        root.ids.storage_card.percent = 64

        root.ids.battery_card.value = "100%"
        root.ids.battery_card.percent = 100

        root.ids.network_card.value = "0.5 KB/s"
        root.ids.network_card.subtitle = "Ping 50 ms"

        root.ids.thermal_card.value = "46°C"
        root.ids.thermal_card.percent = 46


if __name__ == "__main__":
    KingWatchApp().run()