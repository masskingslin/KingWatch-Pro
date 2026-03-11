from jnius import autoclass
import time

TrafficStats = autoclass("android.net.TrafficStats")

class NetworkMonitor:

    def __init__(self):
        self.last_rx = TrafficStats.getTotalRxBytes()
        self.last_tx = TrafficStats.getTotalTxBytes()
        self.last_time = time.time()

    def read(self):

        rx = TrafficStats.getTotalRxBytes()
        tx = TrafficStats.getTotalTxBytes()
        now = time.time()

        dt = now - self.last_time

        rx_speed = (rx - self.last_rx)/dt
        tx_speed = (tx - self.last_tx)/dt

        self.last_rx = rx
        self.last_tx = tx
        self.last_time = now

        return rx_speed, tx_speed
