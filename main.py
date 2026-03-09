from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout

from systemstats.cpu import get_cpu_usage
from systemstats.ram import get_ram_usage
from systemstats.network import get_network_speed
from systemstats.battery import get_battery
from systemstats.thermal import get_temperature


class Dashboard(BoxLayout):

    def update_stats(self, dt):

        cpu = get_cpu_usage()
        ram = get_ram_usage()
        rx, tx = get_network_speed()
        batt, current = get_battery()
        temp = get_temperature()

        self.ids.cpu_label.text = f"CPU {cpu:.1f}%"
        self.ids.ram_label.text = f"RAM {ram:.1f}%"
        self.ids.net_label.text = f"▲ {tx/1024:.1f} KB/s ▼ {rx/1024:.1f} KB/s"
        self.ids.battery_label.text = f"{batt}% {current}mA"
        self.ids.temp_label.text = f"{temp}°C"


class KingWatchApp(App):

    def build(self):
        dash = Dashboard()
        Clock.schedule_interval(dash.update_stats, 1)
        return dash


if __name__ == "__main__":
    KingWatchApp().run()
