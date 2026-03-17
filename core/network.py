"""
KingWatch Pro v17 - core/network.py
Reads bytes from /sys/class/net/<iface>/statistics/ — more reliable than
/proc/net/dev on modern Android kernels.
"""
import os
import time

_prev_rx   = 0
_prev_tx   = 0
_prev_time = 0.0
_band_cache = "N/A"
_band_age   = 0


def _iface_bytes():
    """Sum RX/TX from all active non-loopback interfaces via sysfs."""
    rx = tx = 0
    active = []
    base = "/sys/class/net"
    try:
        ifaces = os.listdir(base)
    except Exception:
        return 0, 0, []

    for iface in ifaces:
        if iface == "lo":
            continue
        try:
            # Check if interface is up
            with open(f"{base}/{iface}/operstate") as f:
                state = f.read().strip()
            if state not in ("up", "unknown"):
                continue
            with open(f"{base}/{iface}/statistics/rx_bytes") as f:
                r = int(f.read().strip())
            with open(f"{base}/{iface}/statistics/tx_bytes") as f:
                t = int(f.read().strip())
            if r > 0 or t > 0:
                rx += r
                tx += t
                active.append(iface)
        except Exception:
            continue
    return rx, tx, active


def _human(bps: float) -> str:
    if bps >= 1_048_576:
        return f"{bps/1_048_576:.1f}MB/s"
    if bps >= 1024:
        return f"{bps/1024:.0f}KB/s"
    return f"{int(bps)}B/s"


def _ping() -> str:
    for path in ("/proc/net/tcp6", "/proc/net/tcp"):
        try:
            with open(path) as f:
                lines = f.readlines()[1:12]
            vals = []
            for ln in lines:
                p = ln.split()
                if len(p) >= 13 and p[3] == "01":
                    try:
                        v = int(p[12], 16) * 4
                        if 2 < v < 2000:
                            vals.append(v)
                    except Exception:
                        pass
            if vals:
                return f"{min(vals)}ms"
        except Exception:
            continue
    return "N/A"


def _wifi_dbm() -> str:
    try:
        with open("/proc/net/wireless") as f:
            for i, ln in enumerate(f):
                if i < 2:
                    continue
                p = ln.split()
                if len(p) >= 4:
                    v = p[3].rstrip(".")
                    dbm = int(float(v))
                    if dbm > 0:
                        dbm -= 256
                    return f"WiFi {dbm}dBm"
    except Exception:
        pass
    return ""


def _mobile_band() -> str:
    try:
        from jnius import autoclass  # type: ignore
        ctx = autoclass("org.kivy.android.PythonActivity").mActivity
        tm  = ctx.getSystemService(
              autoclass("android.content.Context").TELEPHONY_SERVICE)
        nt  = tm.getNetworkType()
        M = {
            1:"2G GPRS",  2:"2G EDGE",   3:"3G UMTS",
            4:"2G CDMA",  5:"3G EVDO-0", 6:"3G EVDO-A",
            7:"2G 1xRTT", 8:"3G HSDPA",  9:"3G HSUPA",
            10:"3G HSPA", 11:"2G iDEN",  12:"3G EVDO-B",
            13:"4G LTE",  14:"3G eHRPD", 15:"4G HSPA+",
            16:"2G GSM",  17:"4G TDD",   18:"WiFi Call",
            19:"4G LTE-CA", 20:"5G NR",
        }
        return M.get(nt, f"Net#{nt}")
    except Exception:
        pass
    return ""


def _detect_band(active_ifaces) -> str:
    # WiFi signal first
    wifi = _wifi_dbm()
    if wifi:
        return wifi
    # Mobile interface names
    mobile_prefixes = ("rmnet", "ccmni", "seth", "usb", "wwan", "ppp", "qmi")
    for iface in active_ifaces:
        if any(iface.startswith(p) for p in mobile_prefixes):
            b = _mobile_band()
            return b if b else "Mobile"
        if iface.startswith(("wlan", "wlp", "wifi")):
            return _wifi_dbm() or "WiFi"
    # Try TelephonyManager directly
    b = _mobile_band()
    return b if b else "N/A"


def get_network() -> dict:
    global _prev_rx, _prev_tx, _prev_time, _band_cache, _band_age

    now = time.monotonic()
    rx, tx, active = _iface_bytes()

    elapsed = max(0.1, now - _prev_time) if _prev_time > 0 else 1.0
    dl = max(0.0, (rx - _prev_rx) / elapsed) if _prev_rx > 0 else 0.0
    ul = max(0.0, (tx - _prev_tx) / elapsed) if _prev_tx > 0 else 0.0

    _prev_rx   = rx
    _prev_tx   = tx
    _prev_time = now

    _band_age += 1
    if _band_age >= 5 or _band_cache == "N/A":
        _band_cache = _detect_band(active)
        _band_age   = 0

    return {
        "dl":     _human(dl),
        "ul":     _human(ul),
        "ping":   _ping(),
        "signal": _band_cache,
    }
