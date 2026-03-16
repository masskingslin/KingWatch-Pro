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
        self.fps_monitor = FPSMonitor()

        self.update_stats()
        Clock.schedule_interval(self.update_stats, 2)

    def update_stats(self, *args):
        threading.Thread(target=self.collect_stats, daemon=True).start()

    def collect_stats(self):

        try:
            cpu = float(get_cpu())
        except:
            cpu = 0

        try:
            ram_pct, ram_detail = get_ram()
        except:
            ram_pct, ram_detail = 0, "N/A"

        try:
            storage_pct, storage_detail = get_storage()
        except:
            storage_pct, storage_detail = 0, "N/A"

        try:
            battery = get_battery()
        except:
            battery = {"pct": 0, "status": "Unknown"}

        try:
            network = get_network()
        except:
            network = {"dl": "N/A", "ul": "N/A", "ping": "N/A", "signal": "N/A"}

        try:
            temp_max, temp_cpu, temp_detail = get_thermal()
        except:
            temp_max, temp_cpu, temp_detail = 0, 0, "N/A"

        try:
            fps = self.fps_monitor.get_fps()
            gpu = self.fps_monitor.get_gpu()
            drops = self.fps_monitor.get_frame_drops()
            lag = self.fps_monitor.get_lag()
            refresh = self.fps_monitor.get_refresh_rate()
        except:
            fps, gpu, drops, lag, refresh = 0, "0%", 0, 0, 60

        Clock.schedule_once(lambda dt:
            self.apply_stats(
                cpu,
                ram_pct, ram_detail,
                storage_pct, storage_detail,
                battery,
                network,
                temp_max, temp_cpu, temp_detail,
                fps, gpu, drops, lag, refresh
            )
        )

    def apply_stats(
        self,
        cpu,
        ram_pct, ram_detail,
        storage_pct, storage_detail,
        battery,
        network,
        temp_max, temp_cpu, temp_detail,
        fps, gpu, drops, lag, refresh
    ):

        # CPU
        if "cpu_card" in self.ids:
            c = self.ids.cpu_card
            c.value = f"{cpu:.1f}%"
            c.bar_pct = cpu

        # RAM
        if "ram_card" in self.ids:
            c = self.ids.ram_card
            c.value = f"{ram_pct:.1f}%"
            c.bar_pct = ram_pct
            c.detail1 = ram_detail

        # STORAGE
        if "storage_card" in self.ids:
            c = self.ids.storage_card
            c.value = f"{storage_pct:.1f}%"
            c.bar_pct = storage_pct
            c.detail1 = storage_detail

        # BATTERY
        if "battery_card" in self.ids:
            c = self.ids.battery_card
            pct = battery.get("pct", 0)

            c.value = f"{pct:.0f}%"
            c.subtitle = battery.get("status", "")
            c.bar_pct = pct

        # NETWORK
        if "network_card" in self.ids:
            c = self.ids.network_card

            c.value = network.get("dl", "N/A")
            c.subtitle = network.get("ping", "N/A")
            c.detail1 = f"UL {network.get('ul','N/A')}"
            c.detail2 = network.get("signal", "N/A")

        # THERMAL
        if "thermal_card" in self.ids:
            c = self.ids.thermal_card

            pct = min((temp_max / 100) * 100, 100)

            c.value = f"{temp_max:.1f}°C"
            c.subtitle = f"CPU {temp_cpu:.1f}°C"
            c.bar_pct = pct
            c.detail1 = temp_detail

        # FPS
        if "fps_card" in self.ids:
            c = self.ids.fps_card

            pct = min((fps / refresh) * 100, 100)

            c.value = str(fps)
            c.subtitle = f"{refresh}Hz"
            c.bar_pct = pct

            c.detail1 = f"GPU {gpu}"
            c.detail2 = f"Drops {drops} Lag {lag}"


class KingWatchApp(App):

    def build(self):
        Builder.load_file("kingwatch.kv")
        return RootWidget()


if __name__ == "__main__":
    KingWatchApp().run()