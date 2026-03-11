from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout

# Import system monitors
from core import (
    CPUMonitor,
    RAMMonitor,
    BatteryMonitor,
    NetworkMonitor,
    StorageMonitor,
    ThermalMonitor
)

KV_FILE = "kingwatch.kv"


class RootLayout(BoxLayout):
    pass


class KingWatchApp(App):

    def build(self):

        Builder.load_file(KV_FILE)

        self.cpu = CPUMonitor()
        self.ram = RAMMonitor()
        self.battery = BatteryMonitor()
        self.network = NetworkMonitor()
        self.storage = StorageMonitor()
        self.thermal = ThermalMonitor()

        self.root_layout = RootLayout()

        # Update system stats every second
        Clock.schedule_interval(self.update_stats, 1)

        return self.root_layout


    def update_stats(self, dt):

        try:
            cpu = round(self.cpu.read(), 1)
        except:
            cpu = 0

        try:
            ram_percent, ram_used, ram_total = self.ram.read()
        except:
            ram_percent, ram_used, ram_total = 0, 0, 0

        try:
            battery = self.battery.read()
        except:
            battery = 0

        try:
            rx, tx = self.network.read()
        except:
            rx, tx = 0, 0

        try:
            storage_percent = self.storage.read()
        except:
            storage_percent = 0

        try:
            temp = self.thermal.read()
        except:
            temp = 0

        # Print values (for debugging)
        print("CPU:", cpu)
        print("RAM:", ram_percent)
        print("Battery:", battery)
        print("Network RX:", rx, "TX:", tx)
        print("Storage:", storage_percent)
        print("Temp:", temp)


if __name__ == "__main__":
    KingWatchApp().run()