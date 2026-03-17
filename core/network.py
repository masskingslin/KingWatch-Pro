"""
KingWatch Pro v17 - core/network.py
- Smoothed speeds (3-sample rolling avg) → no blink
- Band via TelephonyManager + WifiManager
- Ping via UDP socket connect timing (no ICMP/root needed)
- Never shows N/A inline — hides gracefully
"""
import time, os, socket

# ── rolling state ──────────────────────────────────────────────────────────
_prev_rx    = 0
_prev_tx    = 0
_prev_time  = 0.0
_dl_samples = []
_ul_samples = []
_SMOOTH     = 3          # samples to average

_band_cache = ""
_band_age   = 99
_band_mbps  = 10.0

# ── jnius classes (loaded once) ────────────────────────────────────────────
_TS  = None   # TrafficStats
_PA  = None   # PythonActivity
_CTX = None   # Context class

def _jnius_init():
    global _TS, _PA, _CTX
    if _TS is not None:
        return True
    try:
        from jnius import autoclass  # type: ignore
        _TS  = autoclass("android.net.TrafficStats")
        _PA  = autoclass("org.kivy.android.PythonActivity")
        _CTX = autoclass("android.content.Context")
        return True
    except Exception:
        return False

# Band → theoretical max Mbps
_BAND_MBPS = {
    "2G GPRS":0.1,  "2G EDGE":0.2,   "2G CDMA":0.1,  "2G 1xRTT":0.1,
    "2G iDEN":0.05, "2G GSM":0.1,    "3G UMTS":2.0,  "3G HSDPA":14.0,
    "3G HSUPA":5.7, "3G HSPA":14.0,  "3G EVDO":3.1,  "3G eHRPD":14.0,
    "4G LTE":50.0,  "4G LTE-CA":150.0,"4G HSPA+":42.0,"4G TDD-LTE":50.0,
    "5G NR":500.0,  "WiFi":100.0,
}

_NET_TYPE = {
    0:"",         1:"2G GPRS",   2:"2G EDGE",    3:"3G UMTS",
    4:"2G CDMA",  5:"3G EVDO",   6:"3G EVDO",    7:"2G 1xRTT",
    8:"3G HSDPA", 9:"3G HSUPA",  10:"3G HSPA",   11:"2G iDEN",
    12:"3G EVDO", 13:"4G LTE",   14:"3G eHRPD",  15:"4G HSPA+",
    16:"2G GSM",  17:"4G TDD-LTE",18:"WiFi",     19:"4G LTE-CA",
    20:"5G NR",
}


def _get_bytes():
    if _jnius_init():
        try:
            rx = _TS.getTotalRxBytes()
            tx = _TS.getTotalTxBytes()
            if rx > 0 and tx >= 0:
                return int(rx), int(tx)
        except Exception:
            pass
    # /proc/net/dev fallback
    rx = tx = 0
    try:
        with open("/proc/net/dev") as f:
            for line in f.readlines()[2:]:
                if ":" not in line:
                    continue
                iface, data = line.split(":", 1)
                if iface.strip() == "lo":
                    continue
                c = data.split()
                if len(c) >= 9:
                    rx += int(c[0]); tx += int(c[8])
    except Exception:
        pass
    return rx, tx


def _smooth(samples, val, n):
    samples.append(val)
    if len(samples) > n:
        samples.pop(0)
    return sum(samples) / len(samples)


def _human(bps):
    if bps >= 1_048_576: return f"{bps/1_048_576:.1f}MB/s"
    if bps >= 1024:      return f"{bps/1024:.0f}KB/s"
    return f"{int(bps)}B/s"


def _ping():
    # UDP connect trick — measures local routing latency, no ICMP/root needed
    for host in ("8.8.8.8", "1.1.1.1", "208.67.222.222"):
        try:
            t0 = time.monotonic()
            s  = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1.0)
            s.connect((host, 53))
            s.close()
            ms = int((time.monotonic() - t0) * 1000)
            if 0 < ms < 2000:
                return f"{ms}ms"
        except Exception:
            continue
    # TCP fallback
    try:
        for path in ("/proc/net/tcp6", "/proc/net/tcp"):
            with open(path) as f:
                lines = f.readlines()[1:]
            for ln in lines[:20]:
                p = ln.split()
                if len(p) >= 13 and p[3] == "01":
                    rtt = int(p[12], 16) * 2  # jiffies/2 → rough ms
                    if 1 < rtt < 2000:
                        return f"{rtt}ms"
    except Exception:
        pass
    return ""


def _detect_band():
    global _band_mbps
    # 1. WiFi via WifiManager RSSI
    if _jnius_init():
        try:
            ctx = _PA.mActivity
            wm  = ctx.getSystemService(_CTX.WIFI_SERVICE)
            wi  = wm.getConnectionInfo()
            rssi = wi.getRssi()
            if -120 < rssi < 0:
                _band_mbps = _BAND_MBPS.get("WiFi", 100.0)
                return f"WiFi {rssi}dBm"
        except Exception:
            pass

        # 2. Mobile TelephonyManager
        try:
            ctx = _PA.mActivity
            tm  = ctx.getSystemService(_CTX.TELEPHONY_SERVICE)
            nt  = tm.getNetworkType()
            band = _NET_TYPE.get(nt, f"Net#{nt}")
            if band:
                _band_mbps = _BAND_MBPS.get(band, 10.0)
                return band
        except Exception:
            pass

    # 3. /proc/net/wireless
    try:
        with open("/proc/net/wireless") as f:
            lines = f.readlines()
        for ln in lines[2:]:
            p = ln.split()
            if len(p) >= 4:
                dbm = int(float(p[3].rstrip(".")))
                if dbm > 0: dbm -= 256
                if -120 < dbm < 0:
                    _band_mbps = 100.0
                    return f"WiFi {dbm}dBm"
    except Exception:
        pass

    # 4. Interface names
    try:
        for iface in os.listdir("/sys/class/net"):
            try:
                with open(f"/sys/class/net/{iface}/operstate") as f:
                    if f.read().strip() not in ("up","unknown"):
                        continue
            except Exception:
                continue
            if iface.startswith(("wlan","wlp","wifi")):
                _band_mbps = 100.0
                return "WiFi"
            if iface.startswith(("rmnet","ccmni","seth","wwan","ppp")):
                _band_mbps = 10.0
                return "Mobile"
    except Exception:
        pass

    return ""


def get_network() -> dict:
    global _prev_rx, _prev_tx, _prev_time, _band_cache, _band_age

    now    = time.monotonic()
    rx, tx = _get_bytes()

    elapsed = max(0.5, now - _prev_time) if _prev_time > 0 else 1.0
    dl_raw = (rx - _prev_rx) / elapsed if (_prev_rx > 0 and rx > _prev_rx) else 0.0
    ul_raw = (tx - _prev_tx) / elapsed if (_prev_tx > 0 and tx > _prev_tx) else 0.0

    _prev_rx = rx; _prev_tx = tx; _prev_time = now

    # Smooth to remove blink
    dl = _smooth(_dl_samples, dl_raw, _SMOOTH)
    ul = _smooth(_ul_samples, ul_raw, _SMOOTH)

    # Arc % = download vs band theoretical max
    max_bps  = _band_mbps * 125_000   # Mbps → bytes/s
    arc_pct  = min(100.0, dl / max_bps * 100) if max_bps > 0 else 0.0

    # Refresh band every 5 ticks
    _band_age += 1
    if _band_age >= 5:
        _band_cache = _detect_band()
        _band_age   = 0

    ping = _ping()

    # Build clean display strings — never show empty/N/A
    signal_str = _band_cache if _band_cache else "Detecting..."
    ping_str   = f"Ping: {ping}" if ping else "Ping: --"

    return {
        "dl":      _human(dl),
        "ul":      _human(ul),
        "ping":    ping_str,
        "signal":  signal_str,
        "arc_pct": arc_pct,
    }
