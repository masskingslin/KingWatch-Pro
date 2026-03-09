import time
from jnius import autoclass

TrafficStats = autoclass('android.net.TrafficStats')

last_rx = TrafficStats.getTotalRxBytes()
last_tx = TrafficStats.getTotalTxBytes()
last_time = time.time()

def get_network_speed():

    global last_rx, last_tx, last_time

    now_rx = TrafficStats.getTotalRxBytes()
    now_tx = TrafficStats.getTotalTxBytes()

    now = time.time()
    delta = now - last_time

    rx = (now_rx - last_rx) / delta
    tx = (now_tx - last_tx) / delta

    last_rx = now_rx
    last_tx = now_tx
    last_time = now

    return rx, tx
