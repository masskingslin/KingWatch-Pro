import time
import socket
import threading

_ping_ms = None
_signal = "Detecting..."
_started = False


def _ping_worker():
    global _ping_ms
    while True:
        try:
            s = socket.socket()
            s.settimeout(2)
            t0 = time.time()
            s.connect(("8.8.8.8", 53))
            s.close()
            _ping_ms = round((time.time() - t0) * 1000, 1)
        except Exception:
            _ping_ms = None
        time.sleep(5)


def _detect_connection():
    try:
        from jnius import autoclass

        Context = autoclass("android.content.Context")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        ConnectivityManager = autoclass("android.net.ConnectivityManager")

        cm = PythonActivity.mActivity.getSystemService(
            Context.CONNECTIVITY_SERVICE
        )

        net = cm.getActiveNetwork()
        if net is None:
            return "No Network"

        caps = cm.getNetworkCapabilities(net)

        if caps.hasTransport(1):
            return "WiFi"
        if caps.hasTransport(0):
            return "Mobile"
        if caps.hasTransport(3):
            return "Ethernet"

        return "Connected"

    except Exception:
        return "Unknown"


def get_network():
    global _started, _signal

    if not _started:
        _started = True
        threading.Thread(target=_ping_worker, daemon=True).start()

    try:
        from jnius import autoclass

        ts = autoclass("android.net.TrafficStats")
        rx = ts.getTotalRxBytes()
        tx = ts.getTotalTxBytes()

    except Exception:
        rx = tx = 0

    _signal = _detect_connection()

    ping = f"{_ping_ms} ms" if _ping_ms else "Pinging..."

    return {
        "dl": str(rx),
        "ul": str(tx),
        "ping": ping,
        "signal": _signal,
    }