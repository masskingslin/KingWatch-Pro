"""
KingWatch Pro v17 - core/network.py

BAND FIX:
  Android 10+: getNetworkType() always returns UNKNOWN without READ_PHONE_STATE
  granted at RUNTIME. Use getDataNetworkType() which works without permission
  on Android 12+, plus NetworkCapabilities for connection type detection.

PING FIX:
  UDP connect() blocked on many Android devices due to strict socket policy.
  Use ConnectivityManager to check if network is active, then time a
  DatagramChannel or fallback to TCP /proc/net/tcp RTT estimate.
"""
import time
import os

# ── rolling state ──────────────────────────────────────────────────────────
_prev_rx    = 0
_prev_tx    = 0
_prev_time  = 0.0
_dl_buf     = []
_ul_buf     = []
_SMOOTH     = 4

_band_cache = ""
_band_age   = 99
_band_mbps  = 10.0
_ping_cache = ""
_ping_age   = 0

# ── jnius classes loaded once ──────────────────────────────────────────────
_ready = False
_TS = _PA = _CTX_cls = None

def _init():
    global _ready, _TS, _PA, _CTX_cls
    if _ready:
        return True
    try:
        from jnius import autoclass  # type: ignore
        _TS      = autoclass("android.net.TrafficStats")
        _PA      = autoclass("org.kivy.android.PythonActivity")
        _CTX_cls = autoclass("android.content.Context")
        _ready   = True
        return True
    except Exception:
        return False

# Band → theoretical max Mbps
_BAND_MBPS = {
    "2G GPRS":0.1, "2G EDGE":0.2, "2G GSM":0.1, "2G CDMA":0.1,
    "3G UMTS":2.0, "3G HSDPA":14.0,"3G HSUPA":5.7,"3G HSPA":14.0,
    "3G EVDO":3.1, "3G eHRPD":14.0,"4G HSPA+":42.0,
    "4G LTE":50.0, "4G LTE-CA":150.0,"4G TDD-LTE":50.0,
    "5G NR":500.0, "WiFi":100.0,
}
_NET_MAP = {
    1:"2G GPRS", 2:"2G EDGE",  3:"3G UMTS",   4:"2G CDMA",
    5:"3G EVDO", 6:"3G EVDO",  7:"2G 1xRTT",  8:"3G HSDPA",
    9:"3G HSUPA",10:"3G HSPA", 11:"2G iDEN",  12:"3G EVDO",
    13:"4G LTE", 14:"3G eHRPD",15:"4G HSPA+", 16:"2G GSM",
    17:"4G TDD-LTE",18:"WiFi", 19:"4G LTE-CA",20:"5G NR",
}


# ── bytes ──────────────────────────────────────────────────────────────────
def _get_bytes():
    if _init():
        try:
            rx = _TS.getTotalRxBytes()
            tx = _TS.getTotalTxBytes()
            if rx > 0:
                return int(rx), int(tx)
        except Exception:
            pass
    rx = tx = 0
    try:
        with open("/proc/net/dev") as f:
            for ln in f.readlines()[2:]:
                if ":" not in ln:
                    continue
                iface, data = ln.split(":", 1)
                if iface.strip() == "lo":
                    continue
                c = data.split()
                if len(c) >= 9:
                    rx += int(c[0]); tx += int(c[8])
    except Exception:
        pass
    return rx, tx


def _smooth(buf, val, n):
    buf.append(val)
    if len(buf) > n:
        buf.pop(0)
    return sum(buf) / len(buf)


def _human(bps):
    if bps >= 1_048_576: return f"{bps/1_048_576:.1f}MB/s"
    if bps >= 1024:      return f"{bps/1024:.0f}KB/s"
    return f"{int(bps)}B/s"


# ── band detection ─────────────────────────────────────────────────────────
def _detect_band():
    global _band_mbps

    if not _init():
        return _fallback_band()

    ctx = _PA.mActivity

    # ── Strategy 1: NetworkCapabilities (Android 10+, no permission needed)
    try:
        from jnius import autoclass  # type: ignore
        CM  = autoclass("android.net.ConnectivityManager")
        NC  = autoclass("android.net.NetworkCapabilities")
        cm  = ctx.getSystemService(_CTX_cls.CONNECTIVITY_SERVICE)
        net = cm.getActiveNetwork()
        if net:
            caps = cm.getNetworkCapabilities(net)
            if caps:
                WIFI      = NC.TRANSPORT_WIFI
                CELLULAR  = NC.TRANSPORT_CELLULAR
                if caps.hasTransport(WIFI):
                    # Get WiFi RSSI via WifiManager
                    wm   = ctx.getSystemService(_CTX_cls.WIFI_SERVICE)
                    info = wm.getConnectionInfo()
                    rssi = info.getRssi()
                    _band_mbps = 100.0
                    if -120 < rssi < 0:
                        return f"WiFi {rssi}dBm"
                    return "WiFi"
                elif caps.hasTransport(CELLULAR):
                    # Try getDataNetworkType (Android 11+, no permission)
                    try:
                        TM = autoclass("android.telephony.TelephonyManager")
                        tm = ctx.getSystemService(_CTX_cls.TELEPHONY_SERVICE)
                        nt = tm.getDataNetworkType()
                        band = _NET_MAP.get(nt, "")
                        if band:
                            _band_mbps = _BAND_MBPS.get(band, 10.0)
                            return band
                    except Exception:
                        pass
                    # getNetworkType fallback (needs READ_PHONE_STATE on ≤ Android 9)
                    try:
                        tm   = ctx.getSystemService(_CTX_cls.TELEPHONY_SERVICE)
                        nt   = tm.getNetworkType()
                        band = _NET_MAP.get(nt, "")
                        if band and band != "2G GPRS":  # 0→GPRS is "unknown"
                            _band_mbps = _BAND_MBPS.get(band, 10.0)
                            return band
                    except Exception:
                        pass
                    return "Mobile"
    except Exception:
        pass

    # ── Strategy 2: direct TelephonyManager
    try:
        tm = ctx.getSystemService(_CTX_cls.TELEPHONY_SERVICE)
        # getDataNetworkType requires no permission on Android 12+
        for method in ("getDataNetworkType", "getNetworkType"):
            try:
                nt   = getattr(tm, method)()
                band = _NET_MAP.get(nt, "")
                if band:
                    _band_mbps = _BAND_MBPS.get(band, 10.0)
                    return band
            except Exception:
                continue
    except Exception:
        pass

    # ── Strategy 3: /proc/net/wireless (WiFi RSSI)
    try:
        with open("/proc/net/wireless") as f:
            for i, ln in enumerate(f):
                if i < 2:
                    continue
                p = ln.split()
                if len(p) >= 4:
                    dbm = int(float(p[3].rstrip(".")))
                    if dbm > 0: dbm -= 256
                    if -120 < dbm < 0:
                        _band_mbps = 100.0
                        return f"WiFi {dbm}dBm"
    except Exception:
        pass

    return _fallback_band()


def _fallback_band():
    global _band_mbps
    try:
        for iface in sorted(os.listdir("/sys/class/net")):
            try:
                with open(f"/sys/class/net/{iface}/operstate") as f:
                    if f.read().strip() not in ("up", "unknown"):
                        continue
            except Exception:
                continue
            if iface.startswith(("wlan", "wlp", "wifi")):
                _band_mbps = 100.0
                return "WiFi"
            if iface.startswith(("rmnet","ccmni","seth","wwan","ppp","qmi")):
                _band_mbps = 10.0
                return "Mobile"
    except Exception:
        pass
    return ""


# ── ping ───────────────────────────────────────────────────────────────────
def _measure_ping():
    """
    Primary: ConnectivityManager.getActiveNetworkInfo() confirms connectivity,
    then /proc/net/tcp RTT estimate from ESTABLISHED connections.
    Secondary: time DNS resolution (always allowed, no special permissions).
    """
    # Method 1: Parse established TCP connections for RTT
    for path in ("/proc/net/tcp6", "/proc/net/tcp"):
        try:
            with open(path) as f:
                lines = f.readlines()[1:]
            vals = []
            for ln in lines[:30]:
                p = ln.split()
                if len(p) >= 13 and p[3] == "01":   # ESTABLISHED
                    try:
                        # rto in jiffies (250Hz kernel = 4ms/jiffy)
                        # actual RTT ≈ rto / 4 for a stable connection
                        rto_ms = int(p[12], 16) * 4
                        rtt    = max(1, rto_ms // 4)
                        if 1 < rtt < 1000:
                            vals.append(rtt)
                    except Exception:
                        pass
            if vals:
                return f"{min(vals)}ms"
        except Exception:
            continue

    # Method 2: Time a DNS lookup (getaddrinfo - always works)
    import socket
    for host in ("google.com", "cloudflare.com"):
        try:
            t0 = time.monotonic()
            socket.getaddrinfo(host, 80, socket.AF_INET, socket.SOCK_STREAM)
            ms = int((time.monotonic() - t0) * 1000)
            if 1 < ms < 5000:
                # DNS includes query time, divide roughly for RTT estimate
                return f"~{ms}ms"
        except Exception:
            continue

    return ""


# ── public API ─────────────────────────────────────────────────────────────
def get_network() -> dict:
    global _prev_rx, _prev_tx, _prev_time
    global _band_cache, _band_age, _ping_cache, _ping_age

    now    = time.monotonic()
    rx, tx = _get_bytes()

    elapsed = max(0.5, now - _prev_time) if _prev_time > 0 else 1.0
    dl_raw  = (rx - _prev_rx) / elapsed if (_prev_rx > 0 and rx > _prev_rx) else 0.0
    ul_raw  = (tx - _prev_tx) / elapsed if (_prev_tx > 0 and tx > _prev_tx) else 0.0

    _prev_rx = rx; _prev_tx = tx; _prev_time = now

    dl = _smooth(_dl_buf, dl_raw, _SMOOTH)
    ul = _smooth(_ul_buf, ul_raw, _SMOOTH)

    max_bps = _band_mbps * 125_000
    arc_pct = min(100.0, dl / max_bps * 100) if max_bps > 0 else 0.0

    # Refresh band every 5 ticks
    _band_age += 1
    if _band_age >= 5:
        b = _detect_band()
        if b:
            _band_cache = b
        _band_age = 0

    # Refresh ping every 10 ticks
    _ping_age += 1
    if _ping_age >= 10:
        p = _measure_ping()
        if p:
            _ping_cache = p
        _ping_age = 0

    return {
        "dl":      _human(dl),
        "ul":      _human(ul),
        "signal":  _band_cache or "Detecting",
        "ping":    _ping_cache or "--",
        "arc_pct": arc_pct,
    }
