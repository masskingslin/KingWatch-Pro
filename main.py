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

        # FPS monitor initialization
        self.fps_monitor = FPSMonitor()

        # start periodic updates
        Clock.schedule_interval(self.update_stats, 2)

    # ----------------------------------------------------

    def update_stats(self, *args):

        # run monitoring in background thread
        threading.Thread(
            target=self.collect_stats,
            daemon=True
        ).start()

    # ----------------------------------------------------

    def collect_stats(self):

        try:
            cpu = get_cpu()
        except:
            cpu = None

        try:
            ram = get_ram()
        except:
            ram = None

        try:
            storage = get_storage()
        except:
            storage = None

        try:
            battery = get_battery()
        except:
            battery = None

        try:
            network = get_network()
        except:
            network = None

        try:
            thermal = get_thermal()
        except:
            thermal = None

        # FPS metrics
        try:
            fps = self.fps_monitor.get_fps()
            refresh = self.fps_monitor.get_refresh_rate()
            gpu = self.fps_monitor.get_gpu()
            frame_time = self.fps_monitor.get_frame_time()
            drops = self.fps_monitor.get_frame_drops()
            lag = self.fps_monitor.get_lag()
            stability = self.fps_monitor.get_stability()
        except:
            fps = 0
            refresh = 60
            gpu = "0%"
            frame_time = 0
            drops = 0
            lag = 0
            stability = 0

        Clock.schedule_once(lambda dt:
            self.apply_stats(
                cpu, ram, storage,
                battery, network,
                thermal,
                fps, refresh, gpu,
                frame_time, drops,
                lag, stability
            )
        )

    # ----------------------------------------------------

    def apply_stats(self,
                    cpu, ram, storage,
                    battery, network,
                    thermal,
                    fps, refresh, gpu,
                    frame_time, drops,
                    lag, stability):

        # ---------------- CPU ----------------

        if cpu and "cpu_card" in self.ids:

            card = self.ids.cpu_card

            card.value = f"{cpu['usage']:.1f}%"
            card.bar_pct = cpu["usage"]

            card.detail1 = (
                f"Freq: {cpu['freq']} MHz  "
                f"Cores: {cpu['cores']}"
            )

            card.detail2 = (
                f"Procs: {cpu['procs']}  "
                f"Up: {cpu['uptime']}"
            )

        # ---------------- RAM ----------------

        if ram and "ram_card" in self.ids:

            card = self.ids.ram_card

            card.value = f"{ram['pct']:.1f}%"
            card.bar_pct = ram["pct"]

            card.detail1 = (
                f"{ram['used']} / "
                f"{ram['total']}"
            )

        # ---------------- STORAGE ----------------

        if storage and "storage_card" in self.ids:

            card = self.ids.storage_card

            card.value = f"{storage['pct']:.1f}%"
            card.bar_pct = storage["pct"]

            card.detail1 = (
                f"{storage['used']} / "
                f"{storage['total']}"
            )

        # ---------------- BATTERY ----------------

        if battery and "battery_card" in self.ids:

            card = self.ids.battery_card

            card.value = f"{battery['pct']}%"
            card.subtitle = battery["status"]

            try:
                pct = float(battery["pct"])
            except:
                pct = 0

            card.bar_pct = pct

            card.detail1 = (
                f"Curr: {battery['current']} mA  "
                f"Volt: {battery['volt']} V"
            )

            card.detail2 = (
                f"Temp: {battery['temp']} C"
            )

        # ---------------- NETWORK ----------------

        if network and "network_card" in self.ids:

            card = self.ids.network_card

            card.value = network["dl"]
            card.subtitle = network["ping"]

            card.bar_pct = network["pct"]

            card.detail1 = (
                f"DL {network['dl']}  "
                f"UL {network['ul']}"
            )

            card.detail2 = network["signal"]

        # ---------------- THERMAL ----------------

        if thermal and "thermal_card" in self.ids:

            card = self.ids.thermal_card

            card.value = f"{thermal['max']} C"
            card.subtitle = f"CPU {thermal['cpu']} C"

            pct = min((thermal["max"] / 100) * 100, 100)

            card.bar_pct = pct

            card.detail1 = thermal["detail"]

        # ---------------- FPS ----------------

        if "fps_card" in self.ids:

            card = self.ids.fps_card

            card.value = str(fps)

            card.subtitle = f"{refresh}Hz"

            try:
                card.bar_pct = (fps / refresh) * 100
            except:
                card.bar_pct = 0

            card.detail1 = (
                f"GPU {gpu}  "
                f"Frame {frame_time} ms"
            )

            card.detail2 = (
                f"Drops {drops}  "
                f"Lag {lag}  "
                f"Stab {stability}%"
            )


# ----------------------------------------------------


class KingWatchApp(App):

    def build(self):

        Builder.load_file("kingwatch.kv")

        return RootWidget()


# ----------------------------------------------------

if __name__ == "__main__":
    KingWatchApp().run()