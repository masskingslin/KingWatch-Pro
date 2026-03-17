"""
KingWatch Pro v17 - core/network.py
Network speeds, ping estimate, signal strength, band detection (2G/3G/4G/5G).
No psutil - uses /proc/net/dev + Android TelephonyManager via pyjnius.
"""
import time
import subprocess

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
        return f"{bps/1_000_000:.1f} MB/s"
    if bps >= 1_000:
        return f"{bps/1_000:.1f} KB/s"
    return f"{int(bps)} B/s"


def _ping_ms() -> str:
    """RTT from /proc/net/snmp RetransSegs ratio as rough proxy, else N/A."""
    try:
        # Use kernel TCP RTT estimate from /proc/net/tcp if available
        with open("/proc/net/tcp") as f:
            lines = f.readlines()[1:6]   # first 5 connections
        rtts = []
        for ln in lines:
            parts = ln.split()
            if len(parts) >= 14:
                # timeout field in jiffies (rough proxy at 250Hz = 4ms/jiffy)
                rto = int(parts[12], 16)
                ms  = rto * 4
                if 4 < ms < 2000:
                    rtts.append(ms)
        if rtts:
            return f"{min(rtts)} ms"
    except Exception:
        pass
    return "N/A"


def _wifi_signal() -> str:
    """WiFi signal level from /proc/net/wireless."""
    try:
        with open("/proc/net/wireless") as f:
            lines = f.readlines()
        for ln in lines[2:]:
            parts = ln.split()
            if len(parts) >= 4:
                lvl = parts[3].rstrip(".")
                try:
                    dbm = int(float(lvl))
                    return f"WiFi {dbm} dBm"
                except Exception:
                    pass
    except Exception:
        pass
    return ""


def _mobile_band() -> str:
    """
    Detect mobile network type via Android TelephonyManager (pyjnius).
    Falls back to reading /sys/class/net interface names.
    Returns: 5G / 4G LTE / 3G / 2G / WiFi / Unknown
    """
    try:
        from jnius import autoclass  # type: ignore
        PythonActivity  = autoclass("org.kivy.android.PythonActivity")
        Context         = autoclass("android.content.Context")
        TelephonyManager = autoclass("android.telephony.TelephonyManager")

        ctx = PythonActivity.mActivity
        tm  = ctx.getSystemService(Context.TELEPHONY_SERVICE)
        nt  = tm.getNetworkType()

        # Android network type constants
        NR         = 20   # 5G NR
        LTE        = 13
        LTE_CA     = 19
        HSPA_PLUS  = 15
        HSPA       = 10
        HSDPA      = 8
        HSUPA      = 9
        UMTS       = 3
        EDGE       = 2
        GPRS       = 1
        CDMA       = 4
        EVDO_0     = 5
        EVDO_A     = 6
        EVDO_B     = 12
        EHRPD      = 14
        IDEN       = 11
        GSM        = 16
        IWLAN      = 18

        if nt == NR:            return "5G NR"
        if nt in (LTE,LTE_CA): return "4G LTE"
        if nt in (HSPA_PLUS,):  return "4G HSPA+"
        if nt in (HSPA,HSDPA,HSUPA,UMTS): return "3G HSPA"
        if nt in (EDGE,GPRS,CDMA,IDEN,GSM): return "2G"
        if nt in (EVDO_0,EVDO_A,EVDO_B,EHRPD): return "3G EVDO"
        if nt == IWLAN:         return "WiFi Call"
        return f"Net#{nt}"
    except Exception:
        pass

    # Fallback: check interface names
    try:
        import os
        ifaces = os.listdir("/sys/class/net")
        for iface in ifaces:
            if iface.startswith("wlan"):
                return _wifi_signal() or "WiFi"
            if iface.startswith(("rmnet", "ccmni", "seth")):
                return "Mobile"
    except Exception:
        pass

    return _wifi_signal() or "Unknown"


def get_network() -> dict:
    global _prev_rx, _prev_tx, _prev_time

    now     = time.monotonic()
    rx, tx  = _read_net_bytes()
    elapsed = now - _prev_time if _prev_time > 0 else 1.0

    dl = max(0, (rx - _prev_rx) / elapsed) if _prev_rx else 0
    ul = max(0, (tx - _prev_tx) / elapsed) if _prev_tx else 0

    _prev_rx   = rx
    _prev_tx   = tx
    _prev_time = now

    return {
        "dl":     _human(dl),
        "ul":     _human(ul),
        "ping":   _ping_ms(),
        "signal": _mobile_band(),
    }
