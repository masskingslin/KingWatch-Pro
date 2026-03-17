
import time
import socket

_prev_rx = None
_prev_tx = None
_prev_time = None

_band_cache = "N/A"
_band_tick = 0


# ----------------------------
# READ NETWORK BYTES
# ----------------------------
def _read_net_bytes():
    rx = tx = 0
    active = []

    try:
        with open("/proc/net/dev") as f:
            lines = f.readlines()[2:]

        for line in lines:
            if ":" not in line:
                continue

            iface, stats = line.split(":", 1)
            iface = iface.strip()

            # FILTER ONLY REAL INTERFACES
            if iface == "lo":
                continue

            if not iface.startswith((
                "rmnet", "ccmni", "wlan", "wlp", "eth"
            )):
                continue

            cols = stats.split()
            if len(cols) < 9:
                continue

            r = int(cols[0])
            t = int(cols[8])

            if r > 0 or t > 0:
                active.append(iface)

            rx += r
            tx += t

    except Exception:
        return 0, 0, []

    return rx, tx, active


# ----------------------------
# HUMAN FORMAT
# ----------------------------
def _human(bps):
    if bps >= 1_048_576:
        return f"{bps/1_048_576:.1f} MB/s"
    if bps >= 1024:
        return f"{bps/1024:.0f} KB/s"
    return f"{int(bps)} B/s"


# ----------------------------
# REAL LATENCY (FAST SOCKET)
# ----------------------------
def _ping():
    try:
        start = time.time()
        sock = socket.create_connection(("8.8.8.8", 53), timeout=0.3)
        sock.close()
        return f"{int((time.time() - start) * 1000)} ms"
    except Exception:
        return "N/A"


# ----------------------------
# WIFI SIGNAL
# ----------------------------
def _wifi_dbm():
    try:
        with open("/proc/net/wireless") as f:
            lines = f.readlines()[2:]

        for line in lines:
            parts = line.split()
            if len(parts) >= 4:
                val = float(parts[3])
                dbm = int(val if val < 0 else val - 256)
                return f"WiFi {dbm} dBm"

    except Exception:
        pass

    return ""


# ----------------------------
# MOBILE NETWORK TYPE
# ----------------------------
def _mobile_band():
    try:
        from jnius import autoclass

        Context = autoclass("android.content.Context")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")

        ctx = PythonActivity.mActivity
        tm = ctx.getSystemService(Context.TELEPHONY_SERVICE)

        nt = tm.getNetworkType()

        MAP = {
            1:"2G", 2:"2G", 3:"3G", 4:"2G",
            5:"3G", 6:"3G", 7:"2G", 8:"3G",
            9:"3G", 10:"3G", 11:"2G", 12:"3G",
            13:"4G LTE", 15:"4G", 18:"WiFi",
            19:"4G+", 20:"5G"
        }

        return MAP.get(nt, f"Net#{nt}")

    except Exception:
        return ""


# ----------------------------
# DETECT ACTIVE NETWORK
# ----------------------------
def _detect_band(ifaces):
    wifi = _wifi_dbm()
    if wifi:
        return wifi

    for iface in ifaces:
        if iface.startswith(("rmnet", "ccmni")):
            return _mobile_band() or "Mobile"

        if iface.startswith(("wlan",)):
            return "WiFi"

    return _mobile_band() or "N/A"


# ----------------------------
# MAIN API
# ----------------------------
def get_network():
    global _prev_rx, _prev_tx, _prev_time
    global _band_cache, _band_tick

    now = time.monotonic()
    rx, tx, ifaces = _read_net_bytes()

    # FIRST RUN
    if _prev_time is None:
        _prev_rx = rx
        _prev_tx = tx
        _prev_time = now
        return {
            "dl": "0 B/s",
            "ul": "0 B/s",
            "ping": "Detecting...",
            "signal": "Detecting...",
        }

    elapsed = max(0.5, now - _prev_time)

    dl = max(0, (rx - _prev_rx) / elapsed)
    ul = max(0, (tx - _prev_tx) / elapsed)

    _prev_rx = rx
    _prev_tx = tx
    _prev_time = now

    # refresh band
    _band_tick += 1
    if _band_tick >= 3 or _band_cache == "N/A":
        _band_cache = _detect_band(ifaces)
        _band_tick = 0

    return {
        "dl": _human(dl),
        "ul": _human(ul),
        "ping": _ping(),
        "signal": _band_cache,
    }