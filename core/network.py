"""
KingWatch Pro v17 - core/network.py
PRIMARY: Android TrafficStats API via pyjnius — works on ALL Android versions,
         no permissions needed, most reliable method.
FALLBACK: /proc/net/dev byte counting.
"""
import time
import os

_prev_rx   = 0
_prev_tx   = 0
_prev_time = 0.0
_band_cache = "N/A"
_band_age   = 0

# Try to get TrafficStats class once at module load
_TrafficStats = None
try:
    from jnius import autoclass  # type: ignore
    _TrafficStats = autoclass("android.net.TrafficStats")
except Exception:
    pass


def _traffic_stats_bytes():
    """Use Android TrafficStats — most reliable, works on all Android."""
    if _TrafficStats is None:
        return None, None
    try:
        rx = _TrafficStats.getTotalRxBytes()
        tx = _TrafficStats.getTotalTxBytes()
        # Returns -1 if unsupported
        if rx < 0 or tx < 0:
            return None, None
        return rx, tx
    except Exception:
        return None, None


def _proc_net_bytes():
    """Fallback: read /proc/net/dev."""
    rx = tx = 0
    try:
        with open("/proc/net/dev") as f:
            lines = f.readlines()
        for line in lines[2:]:
            if ":" not in line:
                continue
            iface, data = line.split(":", 1)
            if iface.strip() == "lo":
                continue
            cols = data.split()
            if len(cols) >= 9:
                rx += int(cols[0])
                tx += int(cols[8])
    except Exception:
        pass
    return rx, tx


def _human(bps: float) -> str:
    if bps >= 1_048_576:
        return f"{bps/1_048_576:.1f}MB/s"
    if bps >= 1024:
        return f"{bps/1024:.0f}KB/s"
    return f"{int(bps)}B/s"


def _ping() -> str:
    """Estimate from established TCP connections in /proc/net/tcp."""
    for path in ("/proc/net/tcp6", "/proc/net/tcp"):
        try:
            with open(path) as f:
                lines = f.readlines()[1:]
            vals = []
            for ln in lines[:20]:
                p = ln.split()
                if len(p) >= 13 and p[3] == "01":  # ESTABLISHED
                    try:
                        rto = int(p[12], 16) * 4   # jiffies@250Hz → ms
                        if 2 < rto < 3000:
                            vals.append(rto)
                    except Exception:
                        pass
            if vals:
                return f"{min(vals)}ms"
        except Exception:
            continue
    return "N/A"


def _mobile_band() -> str:
    """Android TelephonyManager network type → band string."""
    try:
        from jnius import autoclass  # type: ignore
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Context        = autoclass("android.content.Context")
        ctx = PythonActivity.mActivity
        tm  = ctx.getSystemService(Context.TELEPHONY_SERVICE)
        nt  = tm.getNetworkType()
        MAP = {
            0:"N/A",      1:"2G GPRS",   2:"2G EDGE",
            3:"3G UMTS",  4:"2G CDMA",   5:"3G EVDO",
            6:"3G EVDO",  7:"2G 1xRTT",  8:"3G HSDPA",
            9:"3G HSUPA", 10:"3G HSPA",  11:"2G iDEN",
            12:"3G EVDO", 13:"4G LTE",   14:"3G eHRPD",
            15:"4G HSPA+",16:"2G GSM",   17:"4G TDD-LTE",
            18:"WiFi",    19:"4G LTE-CA",20:"5G NR",
        }
        return MAP.get(nt, f"Net#{nt}")
    except Exception:
        pass
    return ""


def _wifi_signal() -> str:
    """WiFi signal from /proc/net/wireless."""
    try:
        with open("/proc/net/wireless") as f:
            lines = f.readlines()
        for ln in lines[2:]:
            p = ln.split()
            if len(p) >= 4:
                try:
                    dbm = int(float(p[3].rstrip(".")))
                    if dbm > 0:
                        dbm -= 256
                    return f"WiFi {dbm}dBm"
                except Exception:
                    pass
    except Exception:
        pass
    return ""


def _detect_band() -> str:
    wifi = _wifi_signal()
    if wifi:
        return wifi
    band = _mobile_band()
    if band and band != "N/A":
        return band
    # Check active interface names
    try:
        for iface in os.listdir("/sys/class/net"):
            try:
                with open(f"/sys/class/net/{iface}/operstate") as f:
                    if f.read().strip() != "up":
                        continue
            except Exception:
                continue
            if iface.startswith(("wlan", "wlp")):
                return _wifi_signal() or "WiFi"
            if iface.startswith(("rmnet", "ccmni", "seth", "wwan", "ppp")):
                return _mobile_band() or "Mobile"
    except Exception:
        pass
    return "N/A"


def get_network() -> dict:
    global _prev_rx, _prev_tx, _prev_time, _band_cache, _band_age

    now = time.monotonic()

    # Try TrafficStats first, fall back to /proc/net/dev
    rx, tx = _traffic_stats_bytes()
    if rx is None:
        rx, tx = _proc_net_bytes()

    elapsed = max(0.5, now - _prev_time) if _prev_time > 0 else 1.0
    dl = max(0.0, (rx - _prev_rx) / elapsed) if (_prev_rx > 0 and rx > _prev_rx) else 0.0
    ul = max(0.0, (tx - _prev_tx) / elapsed) if (_prev_tx > 0 and tx > _prev_tx) else 0.0

    _prev_rx   = rx
    _prev_tx   = tx
    _prev_time = now

    _band_age += 1
    if _band_age >= 5 or _band_cache == "N/A":
        _band_cache = _detect_band()
        _band_age   = 0

    return {
        "dl":     _human(dl),
        "ul":     _human(ul),
        "ping":   _ping(),
        "signal": _band_cache,
    }