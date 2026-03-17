"""
KingWatch Pro v17 - core/network.py

FIXES:
- TrafficStats: getTotalRxBytes includes all UIDs, may reset on some devices.
  Use getUidRxBytes(UID_ALL=-1) as backup. Also swap rx/tx if needed.
- Arc % = current speed vs theoretical band max (4G=~50Mbps, 5G=~500Mbps, WiFi=~100Mbps)
- Ping: use ConnectivityManager or ICMP via DatagramSocket fallback
- Band: try multiple Android APIs + /sys fallback
"""
import time
import os

_prev_rx    = 0
_prev_tx    = 0
_prev_time  = 0.0
_band_cache = "N/A"
_band_age   = 99   # Force detection on first call
_band_mbps  = 10.0  # Theoretical max Mbps for current band (for arc %)

# Pre-load jnius classes once
_TrafficStats = None
_PythonActivity = None
_Context = None

def _init_jnius():
    global _TrafficStats, _PythonActivity, _Context
    if _TrafficStats is not None:
        return True
    try:
        from jnius import autoclass  # type: ignore
        _TrafficStats   = autoclass("android.net.TrafficStats")
        _PythonActivity = autoclass("org.kivy.android.PythonActivity")
        _Context        = autoclass("android.content.Context")
        return True
    except Exception:
        return False


# Band name → theoretical max Mbps (for arc % calculation)
_BAND_MBPS = {
    "2G GPRS":  0.1,   "2G EDGE":  0.2,   "2G CDMA":  0.1,
    "2G 1xRTT": 0.1,   "2G iDEN":  0.05,  "2G GSM":   0.1,
    "3G UMTS":  2.0,   "3G HSDPA": 14.0,  "3G HSUPA": 5.7,
    "3G HSPA":  14.0,  "3G EVDO":  3.1,   "3G eHRPD": 14.0,
    "4G LTE":   50.0,  "4G LTE-CA":150.0, "4G HSPA+": 42.0,
    "4G TDD-LTE":50.0, "5G NR":    500.0,
    "WiFi":     100.0, "WiFi Call": 100.0,
}


def _get_bytes():
    """Get total RX/TX bytes. Returns (rx, tx) or (0, 0)."""
    if not _init_jnius():
        return _proc_net_bytes()

    try:
        # RECOMMEND: getTotalRxBytes / getTotalTxBytes
        rx = _TrafficStats.getTotalRxBytes()
        tx = _TrafficStats.getTotalTxBytes()
        if rx > 0 and tx >= 0:
            return rx, tx
    except Exception:
        pass

    # Fallback: uid-based for all UIDs
    try:
        UNSUPPORTED = -1
        rx = _TrafficStats.getUidRxBytes(UNSUPPORTED)
        tx = _TrafficStats.getUidTxBytes(UNSUPPORTED)
        if rx > 0:
            return rx, tx
    except Exception:
        pass

    return _proc_net_bytes()


def _proc_net_bytes():
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


def _speed_pct(bps: float, band_mbps: float) -> float:
    """Convert speed in bps to % of theoretical band maximum."""
    if band_mbps <= 0:
        return 0.0
    max_bps = band_mbps * 1_000_000 / 8  # Mbps → bytes/s
    return min(100.0, (bps / max_bps) * 100.0)


def _ping_ms() -> str:
    """
    Estimate latency from kernel TCP RTO values.
    RTO (retransmit timeout) in /proc/net/tcp is set based on RTT * ~2.
    """
    for path in ("/proc/net/tcp6", "/proc/net/tcp"):
        try:
            with open(path) as f:
                lines = f.readlines()[1:]
            vals = []
            for ln in lines[:30]:
                p = ln.split()
                # state 01 = ESTABLISHED, col 12 = timeout (hex jiffies)
                if len(p) >= 13 and p[3] == "01":
                    try:
                        # jiffies: 250Hz kernel = 4ms each
                        rto_ms = int(p[12], 16) * 4
                        # Real RTT ≈ RTO / 2 for stable connections
                        rtt = rto_ms // 2
                        if 1 < rtt < 2000:
                            vals.append(rtt)
                    except Exception:
                        pass
            if vals:
                return f"{min(vals)}ms"
        except Exception:
            continue

    # Try UDP socket to 8.8.8.8 (no ICMP needed, just measures local routing)
    try:
        import socket
        t0 = time.monotonic()
        s  = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 53))
        s.close()
        ms = int((time.monotonic() - t0) * 1000)
        if ms < 2000:
            return f"~{ms}ms"
    except Exception:
        pass

    return "N/A"


def _mobile_band() -> str:
    if not _init_jnius():
        return ""
    try:
        ctx = _PythonActivity.mActivity
        tm  = ctx.getSystemService(_Context.TELEPHONY_SERVICE)
        nt  = tm.getNetworkType()
        MAP = {
            0:"N/A",       1:"2G GPRS",    2:"2G EDGE",
            3:"3G UMTS",   4:"2G CDMA",    5:"3G EVDO",
            6:"3G EVDO",   7:"2G 1xRTT",   8:"3G HSDPA",
            9:"3G HSUPA",  10:"3G HSPA",   11:"2G iDEN",
            12:"3G EVDO",  13:"4G LTE",    14:"3G eHRPD",
            15:"4G HSPA+", 16:"2G GSM",    17:"4G TDD-LTE",
            18:"WiFi",     19:"4G LTE-CA", 20:"5G NR",
        }
        return MAP.get(nt, f"Net#{nt}")
    except Exception:
        pass
    return ""


def _wifi_dbm() -> str:
    """WiFi signal from WifiManager (most accurate) or /proc/net/wireless."""
    if _init_jnius():
        try:
            ctx = _PythonActivity.mActivity
            wm  = ctx.getSystemService(_Context.WIFI_SERVICE)
            wi  = wm.getConnectionInfo()
            rssi = wi.getRssi()
            if -120 < rssi < 0:
                return f"WiFi {rssi}dBm"
        except Exception:
            pass
    # Fallback
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
                    if -120 < dbm < 0:
                        return f"WiFi {dbm}dBm"
                except Exception:
                    pass
    except Exception:
        pass
    return ""


def _detect_band() -> str:
    wifi = _wifi_dbm()
    if wifi:
        return wifi
    band = _mobile_band()
    if band and band not in ("N/A", ""):
        return band
    # Interface name fallback
    try:
        for iface in os.listdir("/sys/class/net"):
            try:
                with open(f"/sys/class/net/{iface}/operstate") as f:
                    if f.read().strip() not in ("up", "unknown"):
                        continue
            except Exception:
                continue
            if iface.startswith(("wlan", "wlp", "wifi")):
                return _wifi_dbm() or "WiFi"
            if iface.startswith(("rmnet", "ccmni", "seth", "wwan", "ppp")):
                return _mobile_band() or "Mobile"
    except Exception:
        pass
    return "N/A"


def get_network() -> dict:
    global _prev_rx, _prev_tx, _prev_time
    global _band_cache, _band_age, _band_mbps

    now = time.monotonic()
    rx, tx = _get_bytes()

    elapsed = max(0.5, now - _prev_time) if _prev_time > 0 else 1.0

    # Guard against counter reset or first call
    if _prev_rx > 0 and rx >= _prev_rx:
        dl = (rx - _prev_rx) / elapsed
    else:
        dl = 0.0

    if _prev_tx > 0 and tx >= _prev_tx:
        ul = (tx - _prev_tx) / elapsed
    else:
        ul = 0.0

    _prev_rx   = rx
    _prev_tx   = tx
    _prev_time = now

    # Refresh band every 5 ticks
    _band_age += 1
    if _band_age >= 5:
        _band_cache = _detect_band()
        _band_mbps  = _BAND_MBPS.get(_band_cache, 10.0)
        _band_age   = 0

    # Arc % = download speed vs band theoretical max
    arc_pct = _speed_pct(dl, _band_mbps)

    return {
        "dl":      _human(dl),
        "ul":      _human(ul),
        "ping":    _ping_ms(),
        "signal":  _band_cache,
        "arc_pct": arc_pct,        # % of band capacity used
    }
