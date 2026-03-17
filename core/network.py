"""
KingWatch Pro v17 - core/network.py
Upload/download speeds from /proc/net/dev.
Band detection: tries TelephonyManager via jnius, falls back to sysfs.
Ping from /proc/net/tcp RTT estimate.
"""
import time
import os

_prev_rx    = 0
_prev_tx    = 0
_prev_time  = 0.0
_band_cache = ""
_band_time  = 0.0


def _read_net_bytes():
    rx = tx = 0
    try:
        with open("/proc/net/dev") as f:
            for line in f:
                if ":" not in line:
                    continue
                iface, data = line.split(":", 1)
                iface = iface.strip()
                if iface == "lo":
                    continue
                parts = data.split()
                if len(parts) >= 9:
                    rx += int(parts[0])
                    tx += int(parts[8])
    except Exception:
        pass
    return rx, tx


def _human(bps: float) -> str:
    if bps >= 1_000_000:
        return f"{bps/1_000_000:.1f}MB/s"
    if bps >= 1_000:
        return f"{bps/1_000:.0f}KB/s"
    return f"{int(bps)}B/s"


def _ping() -> str:
    # Use /proc/net/tcp6 or tcp to estimate round-trip
    for path in ("/proc/net/tcp6", "/proc/net/tcp"):
        try:
            with open(path) as f:
                lines = f.readlines()[1:10]
            rtts = []
            for ln in lines:
                p = ln.split()
                if len(p) >= 13:
                    # column 12 = retransmit timeout in jiffies (250Hz kernel → 4ms each)
                    try:
                        rto = int(p[12], 16) * 4
                        if 4 < rto < 3000:
                            rtts.append(rto)
                    except Exception:
                        pass
            if rtts:
                return f"{min(rtts)}ms"
        except Exception:
            continue
    return "N/A"


def _band() -> str:
    """Network band - cached for 10s to avoid pyjnius overhead."""
    global _band_cache, _band_time
    now = time.monotonic()
    if _band_cache and now - _band_time < 10:
        return _band_cache

    result = _detect_band()
    _band_cache = result
    _band_time  = now
    return result


def _detect_band() -> str:
    # 1. Android TelephonyManager
    try:
        from jnius import autoclass  # type: ignore
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Context        = autoclass("android.content.Context")
        ctx = PythonActivity.mActivity
        tm  = ctx.getSystemService(Context.TELEPHONY_SERVICE)
        nt  = tm.getNetworkType()
        _MAP = {
            0:  "Unknown",  1:  "2G GPRS",  2:  "2G EDGE",
            3:  "3G UMTS",  4:  "2G CDMA",  5:  "3G EVDO-0",
            6:  "3G EVDO-A",7:  "2G 1xRTT", 8:  "3G HSDPA",
            9:  "3G HSUPA", 10: "3G HSPA",  11: "2G iDEN",
            12: "3G EVDO-B",13: "4G LTE",   14: "3G eHRPD",
            15: "4G HSPA+", 16: "2G GSM",   17: "4G TD-LTE",
            18: "WiFi Call",19: "4G LTE-CA",20: "5G NR",
        }
        band = _MAP.get(nt, f"Net#{nt}")
        if band != "Unknown":
            return band
    except Exception:
        pass

    # 2. WiFi signal from /proc/net/wireless
    try:
        with open("/proc/net/wireless") as f:
            lines = f.readlines()
        for ln in lines[2:]:
            parts = ln.split()
            if len(parts) >= 4:
                try:
                    dbm = int(float(parts[3].rstrip(".")))
                    return f"WiFi {dbm}dBm"
                except Exception:
                    pass
    except Exception:
        pass

    # 3. Check active interface names
    try:
        for iface in sorted(os.listdir("/sys/class/net")):
            op = f"/sys/class/net/{iface}/operstate"
            try:
                with open(op) as f:
                    state = f.read().strip()
            except Exception:
                state = ""
            if state != "up":
                continue
            if iface.startswith("wlan") or iface.startswith("wlp"):
                return "WiFi"
            if iface.startswith(("rmnet", "ccmni", "seth", "usb")):
                return "Mobile"
    except Exception:
        pass

    return "N/A"


def get_network() -> dict:
    global _prev_rx, _prev_tx, _prev_time

    now    = time.monotonic()
    rx, tx = _read_net_bytes()

    elapsed = now - _prev_time if _prev_time > 0 else 1.0
    dl = max(0.0, (rx - _prev_rx) / elapsed) if _prev_rx > 0 else 0.0
    ul = max(0.0, (tx - _prev_tx) / elapsed) if _prev_tx > 0 else 0.0

    _prev_rx   = rx
    _prev_tx   = tx
    _prev_time = now

    return {
        "dl":     _human(dl),
        "ul":     _human(ul),
        "ping":   _ping(),
        "signal": _band(),
    }
