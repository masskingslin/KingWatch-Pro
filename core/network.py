"""
Network module — reads TrafficStats on Android, falls back to /proc/net on Linux.
Returns human-readable speed strings (KB/s, MB/s).
"""
import time
import socket
import threading

# ── Ping worker ────────────────────────────────────────────────────────────
_ping_ms  = None
_signal   = "Detecting..."
_started  = False

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

# ── Android setup ─────────────────────────────────────────────────────────
try:
    from jnius import autoclass
    _TrafficStats = autoclass("android.net.TrafficStats")
    _Context      = autoclass("android.content.Context")
    _PythonActivity = autoclass("org.kivy.android.PythonActivity")
    _ANDROID      = True
except Exception:
    _TrafficStats = None
    _ANDROID      = False

# ── Speed tracking ─────────────────────────────────────────────────────────
_prev_rx   = 0
_prev_tx   = 0
_prev_time = time.time()


def _fmt_speed(bps):
    """Format bytes/sec into a human-readable string."""
    if bps >= 1_048_576:
        return f"{bps / 1_048_576:.2f} MB/s"
    if bps >= 1024:
        return f"{bps / 1024:.1f} KB/s"
    return f"{bps:.0f} B/s"


def _get_bytes_android():
    rx = _TrafficStats.getTotalRxBytes()
    tx = _TrafficStats.getTotalTxBytes()
    # getTotalRxBytes returns -1 if unsupported
    return max(0, rx), max(0, tx)


def _get_bytes_proc():
    """Fallback: read /proc/net/dev."""
    rx = tx = 0
    try:
        with open("/proc/net/dev") as f:
            for line in f.readlines()[2:]:
                parts = line.split()
                if parts[0].startswith("lo"):
                    continue
                rx += int(parts[1])
                tx += int(parts[9])
    except Exception:
        pass
    return rx, tx


def _detect_signal():
    if not _ANDROID:
        return "Unknown"
    try:
        ConnectivityManager = autoclass("android.net.ConnectivityManager")
        cm  = _PythonActivity.mActivity.getSystemService(_Context.CONNECTIVITY_SERVICE)
        net = cm.getActiveNetwork()
        if net is None:
            return "No Network"
        caps = cm.getNetworkCapabilities(net)
        if caps.hasTransport(1): return "WiFi"
        if caps.hasTransport(0): return "Mobile"
        if caps.hasTransport(3): return "Ethernet"
        return "Connected"
    except Exception:
        return "Unknown"


def get_network():
    """
    Returns dict:
        dl     – download speed string  e.g. "1.24 MB/s"
        ul     – upload speed string    e.g. "320 KB/s"
        ping   – ping string            e.g. "18 ms"
        signal – connection type        e.g. "WiFi"
    """
    global _prev_rx, _prev_tx, _prev_time, _started, _signal

    if not _started:
        _started = True
        threading.Thread(target=_ping_worker, daemon=True).start()

    now = time.time()
    elapsed = now - _prev_time
    _prev_time = now

    rx, tx = _get_bytes_android() if _ANDROID else _get_bytes_proc()

    dl_bps = max(0, (rx - _prev_rx) / elapsed) if (elapsed > 0 and _prev_rx) else 0
    ul_bps = max(0, (tx - _prev_tx) / elapsed) if (elapsed > 0 and _prev_tx) else 0

    _prev_rx = rx
    _prev_tx = tx

    _signal = _detect_signal()
    ping_str = f"{_ping_ms} ms" if _ping_ms is not None else "Pinging..."

    return {
        "dl":     _fmt_speed(dl_bps),
        "ul":     _fmt_speed(ul_bps),
        "ping":   ping_str,
        "signal": _signal,
    }
