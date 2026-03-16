from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout

from core.fps import PerformanceMonitor
from core.cpu import get_cpu
from core.ram import get_ram
from core.battery import get_battery
from core.network import get_network
from core.storage import get_storage
from core.thermal import get_thermal

KV = Builder.load_file("kingwatch.kv")


class Root(BoxLayout):
    pass


class KingWatchApp(App):

    def build(self):
        self.monitor = PerformanceMonitor()
        self.root = Root()

        Clock.schedule_interval(self.update_stats, 1)

        return self.root

    def update_stats(self, dt):

        fps = self.monitor.get_fps()
        gpu = self.monitor.get_gpu()

        cpu = get_cpu()
        ram_pct, ram_str = get_ram()

        batt = get_battery()

        net = get_network()

        storage = get_storage()

        therm = get_thermal()

        r = self.root

        r.ids.fps_value.text = str(fps)
        r.ids.gpu_value.text = gpu

        r.ids.cpu_value.text = cpu
        r.ids.ram_value.text = ram_str

        r.ids.battery_value.text = batt["percent"]
        r.ids.battery_detail.text = batt["detail"]

        r.ids.net_value.text = net["dl"]
        r.ids.net_detail.text = f'{net["ul"]} {net["ping"]}'

        r.ids.storage_value.text = storage

        r.ids.temp_value.text = str(therm[0])


if __name__ == "__main__":
    KingWatchApp().run()