import threading
from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout

from core.cpu import get_cpu
from core.ram import get_ram
from core.storage import get_storage
from core.battery import get_battery
from core.network import get_network
from core.thermal import get_thermal
from core.fps import FPSMonitor


class RootWidget(BoxLayout):

    def on_kv_post(self, *args):
        self.fps = FPSMonitor()
        Clock.schedule_interval(self.update_stats, 2)

    def update_stats(self, *args):
        threading.Thread(target=self.collect_stats, daemon=True).start()

    def collect_stats(self):

        cpu = get_cpu()
        ram = get_ram()
        storage = get_storage()
        battery = get_battery()
        network = get_network()
        thermal = get_thermal()

        fps = self.fps.get_fps()
        refresh = self.fps.get_refresh_rate()
        gpu = self.fps.get_gpu()
        frametime = self.fps.get_frame_time()

        Clock.schedule_once(lambda dt:
            self.apply(cpu, ram, storage, battery,
                       network, thermal,
                       fps, refresh, gpu, frametime)
        )

    def apply(self, cpu, ram, storage, battery,
              network, thermal,
              fps, refresh, gpu, frametime):

        c = self.ids.cpu_card
        c.value = f"{cpu['usage']:.1f}%"
        c.bar_pct = cpu['usage']
        c.detail1 = f"Freq {cpu['freq']}MHz  Cores {cpu['cores']}"
        c.detail2 = f"Proc {cpu['procs']}  Up {cpu['uptime']}"

        r = self.ids.ram_card
        r.value = f"{ram['pct']:.1f}%"
        r.bar_pct = ram['pct']
        r.detail1 = f"{ram['used']} / {ram['total']}"

        s = self.ids.storage_card
        s.value = f"{storage['pct']:.1f}%"
        s.bar_pct = storage['pct']
        s.detail1 = f"{storage['used']} / {storage['total']}"

        b = self.ids.battery_card
        b.value = f"{battery['pct']}%"
        b.subtitle = battery['status']
        b.bar_pct = battery['pct']
        b.detail1 = f"{battery['volt']}V {battery['current']}mA"
        b.detail2 = f"{battery['temp']}°C"

        n = self.ids.network_card
        n.value = network['dl']
        n.subtitle = network['ping']
        n.detail1 = f"DL {network['dl']} UL {network['ul']}"
        n.detail2 = network['signal']

        t = self.ids.thermal_card
        t.value = f"{thermal['max']}°C"
        t.subtitle = f"CPU {thermal['cpu']}°C"
        t.detail1 = thermal['detail']
        t.bar_pct = min(thermal['max'], 100)

        f = self.ids.fps_card
        f.value = str(fps)
        f.subtitle = f"{refresh}Hz"
        f.bar_pct = min((fps / refresh) * 100, 100)
        f.detail1 = f"GPU {gpu}"
        f.detail2 = f"{frametime} ms"


class KingWatchApp(App):

    def build(self):
        Builder.load_file("kingwatch.kv")
        return RootWidget()


if __name__ == "__main__":
    KingWatchApp().run()