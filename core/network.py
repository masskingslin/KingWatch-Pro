"""
KingWatch Pro v17 - core/network.py
Reads ALL interfaces from /proc/net/dev including rmnet/wlan.
Special handling for Android mobile data interfaces.
"""
import time
import os

_prev_rx    = 0
_prev_tx    = 0
_prev_time  = 0.0
_band_cache = "N/A"
_band_tick  = 0


def _read_net_bytes():
    """Read total RX/TX bytes from all non-loopback interfaces."""
    rx = tx = 0
    active_ifaces = []
    try:
        with open("/proc/net/dev") as f:
            lines = f.readlines()
        for line in lines[2:]:   # skip 2 header lines
            line = line.strip()
            if not line or ":" not in line:
                continue
            iface, stats = line.split(":", 1)
            iface = iface.strip()
            if iface == "lo":
                continue
            cols = stats.split()
            if len(cols) >= 9:
                r = int(cols[0])
                t = int(cols[8])
                if r > 0 or t > 0:
                    active_ifaces.append(iface)
                rx += r
                tx += t
    except Exception:
        pass
    return rx, tx, active_ifaces


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
            rtts = []
            for ln in lines:
                p = ln.split()
                # col 3 = state (01=ESTABLISHED), col 12 = timeout
                if len(p) >= 13 and p[3] == "01":
                    try:
                        rto = int(p[12], 16) * 4   # jiffies@250Hz → ms
                        if 1 < rto < 3000:
                            rtts.append(rto)
                    except Exception:
                        pass
            if rtts:
                return f"{min(rtts)}ms"
        except Exception:
            continue
    return "N/A"


def _wifi_dbm() -> str:
    try:
        with open("/proc/net/wireless") as f:
            for i, line in enumerate(f):
                if i < 2:
                    continue
                parts = line.split()
                if len(parts) >= 4:
                    val = parts[3].rstrip(".")
                    dbm = int(float(val))
                    # /proc/net/wireless sometimes reports in positive form
                    if dbm > 0:
                        dbm = dbm - 256
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
        _M  = {
            1:"2G GPRS", 2:"2G EDGE",  3:"3G UMTS",  4:"2G CDMA",
            5:"3G EVDO", 6:"3G EVDO",  7:"2G 1xRTT", 8:"3G HSDPA",
            9:"3G HSUPA",10:"3G HSPA", 11:"2G iDEN",  12:"3G EVDO-B",
            13:"4G LTE", 14:"3G eHRPD",15:"4G HSPA+", 16:"2G GSM",
            17:"4G TDD", 18:"WiFi",    19:"4G LTE-CA",20:"5G NR",
        }
        return _M.get(nt, f"Net#{nt}")
    except Exception:
        pass
    return ""


def _detect_band(ifaces) -> str:
    # Check WiFi first
    wifi = _wifi_dbm()
    if wifi:
        return wifi
    # Check if any mobile interface is active
    for iface in ifaces:
        if any(iface.startswith(p) for p in
               ("rmnet", "ccmni", "seth", "usb", "ppp", "wwan")):
            band = _mobile_band()
            return band if band else "Mobile"
        if iface.startswith(("wlan", "wlp")):
            return _wifi_dbm() or "WiFi"
    # Last resort: TelephonyManager
    band = _mobile_band()
    return band if band else "N/A"


def get_network() -> dict:
    global _prev_rx, _prev_tx, _prev_time, _band_cache, _band_tick

    now = time.monotonic()
    rx, tx, ifaces = _read_net_bytes()

    elapsed = now - _prev_time if _prev_time > 0 else 1.0
    dl = max(0.0, (rx - _prev_rx) / elapsed) if _prev_rx > 0 else 0.0
    ul = max(0.0, (tx - _prev_tx) / elapsed) if _prev_tx > 0 else 0.0

    _prev_rx   = rx
    _prev_tx   = tx
    _prev_time = now

    # Refresh band every 5s
    _band_tick += 1
    if _band_tick >= 5 or _band_cache == "N/A":
        _band_cache = _detect_band(ifaces)
        _band_tick  = 0

    return {
        "dl":     _human(dl),
        "ul":     _human(ul),
        "ping":   _ping(),
        "signal": _band_cache,
    }
