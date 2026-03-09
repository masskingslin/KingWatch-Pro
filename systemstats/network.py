"""
Network Monitor — KingWatch Pro v15
Primary  : android.net.TrafficStats  (no permissions, Android 2-15)
Fallback : /proc/net/dev             (Linux, Android 5-8)
Smoothing: 3-sample rolling average to prevent display spikes.
"""

import time
from collections import deque

IS_ANDROID = False
try:
    from jnius import autoclass as _ac
    _TrafficStats = _ac("android.net.TrafficStats")
    IS_ANDROID = True
except Exception:
    _TrafficStats = None


class NetworkMonitor:

    def __init__(self):
        self._last_rx  = -1
        self._last_tx  = -1
        self._last_ts  = 0.0
        self._rx_hist  = deque(maxlen=3)
        self._tx_hist  = deque(maxlen=3)

    def read(self):
        """Returns (rx_bytes_per_sec, tx_bytes_per_sec)."""
        rx, tx = self._get_bytes()
        now    = time.monotonic()

        if self._last_rx < 0:
            self._last_rx = rx
            self._last_tx = tx
            self._last_ts = now
            return 0.0, 0.0

        dt = now - self._last_ts
        if dt <= 0:
            return 0.0, 0.0

        rx_speed = max(0.0, (rx - self._last_rx) / dt)
        tx_speed = max(0.0, (tx - self._last_tx) / dt)

        self._last_rx = rx
        self._last_tx = tx
        self._last_ts = now

        self._rx_hist.append(rx_speed)
        self._tx_hist.append(tx_speed)

        return sum(self._rx_hist) / len(self._rx_hist), \
               sum(self._tx_hist) / len(self._tx_hist)

    def _get_bytes(self):
        # Android TrafficStats
        if _TrafficStats is not None:
            try:
                rx = _TrafficStats.getTotalRxBytes()
                tx = _TrafficStats.getTotalTxBytes()
                if rx != -1 and tx != -1:
                    return rx, tx
            except Exception:
                pass

        # Fallback: /proc/net/dev
        return self._proc_net_dev()

    def _proc_net_dev(self):
        rx = tx = 0
        try:
            with open("/proc/net/dev") as f:
                lines = f.readlines()[2:]
            for line in lines:
                parts = line.split()
                iface = parts[0].rstrip(":")
                if iface == "lo":
                    continue
                rx += int(parts[1])
                tx += int(parts[9])
        except Exception:
            pass
        return rx, tx
