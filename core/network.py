"""
KingWatch Pro v17 - core/network.py
Upload/Download speeds, ping, signal strength, 2G/3G/4G/5G band detection.
"""
import time
import os

_prev_rx   = 0
_prev_tx   = 0
_prev_time = 0.0


def _read_net_bytes():
    rx = tx = 0
    try:
        with open("/proc/net/dev") as f:
            for line in f:
                if ":" not in line:
                    continue
                iface, data = line.split(":", 1)
                if iface.strip() in ("lo",):
                    continue
                parts = data.split()
                if len(parts) >= 9:
                    rx += int(parts[0])
                    tx += int(parts[8])
    except Exception:
        pass
    return rx, tx


def _human(bps):
    if bps >= 1_000_000:
        return f"{bps/1_000_000:.1f}MB/s"
    if bps >= 1_000:
        return f"{bps/1_000:.0f}KB/s"
    return f"{int(bps)}B/s"


def _ping() -> str:
    try:
        with open("/proc/net/tcp") as f:
            lines = f.readlines()[1:8]
        rtts = []
        for ln in lines:
            p = ln.split()
            if len(p) >= 13:
                rto = int(p[12], 16) * 4   # jiffies at ~250Hz → ms
                if 4 < rto < 2000:
                    rtts.append(rto)
        if rtts:
            return f"{min(rtts)}ms"
    except Exception:
        pass
    return "N/A"


def _band() -> str:
    """Detect mobile network type via Android TelephonyManager."""
    try:
        from jnius import autoclass
        PythonActivity   = autoclass("org.kivy.android.PythonActivity")
        Context          = autoclass("android.content.Context")
        ctx              = PythonActivity.mActivity
        tm               = ctx.getSystemService(Context.TELEPHONY_SERVICE)
        nt               = tm.getNetworkType()

        _MAP = {
            1:  "2G GPRS",   2:  "2G EDGE",   3:  "3G UMTS",
            4:  "2G CDMA",   5:  "3G EVDO-0", 6:  "3G EVDO-A",
            7:  "2G 1xRTT",  8:  "3G HSDPA",  9:  "3G HSUPA",
            10: "3G HSPA",   11: "2G iDEN",   12: "3G EVDO-B",
            13: "4G LTE",    14: "3G eHRPD",  15: "4G HSPA+",
            16: "2G GSM",    17: "4G TDLTE",  18: "WiFi",
            19: "4G LTE-CA", 20: "5G NR",
        }
        return _MAP.get(nt, f"Net#{nt}")
    except Exception:
        pass

    # Fallback: check /proc/net/wireless for WiFi
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

    # Check interface names
    try:
        for iface in os.listdir("/sys/class/net"):
            if iface.startswith("wlan"):
                return "WiFi"
            if iface.startswith(("rmnet", "ccmni", "seth_lte")):
                return "Mobile"
    except Exception:
        pass

    return "N/A"


def get_network() -> dict:
    global _prev_rx, _prev_tx, _prev_time

    now    = time.monotonic()
    rx, tx = _read_net_bytes()
    elapsed = now - _prev_time if _prev_time > 0 else 1.0

    dl = max(0, (rx - _prev_rx) / elapsed) if _prev_rx else 0
    ul = max(0, (tx - _prev_tx) / elapsed) if _prev_tx else 0

    _prev_rx   = rx
    _prev_tx   = tx
    _prev_time = now

    return {
        "dl":     _human(dl),
        "ul":     _human(ul),
        "ping":   _ping(),
        "signal": _band(),
    }
