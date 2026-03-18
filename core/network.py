"""
KingWatch Pro v17 - core/network.py

PING FIX: socket.connect() fails silently on Android due to bytecode
attribute cache collision in Python 3.11 packing.
Use subprocess ping binary (/system/bin/ping) — always works on Android.
Fallback: Java InetAddress.isReachable() via pyjnius.

BAND: getLinkDownstreamBandwidthKbps() via NetworkCapabilities — no permission needed.
SPEED: TrafficStats — no permission needed.
"""
import time, threading, os, glob, subprocess, re

# ── shared state ────────────────────────────────────────────────────────────
_ping_ms    = None
_signal_str = "Detecting..."
_band_mbps  = 10.0
_bg_started = False
_bw         = {}


# ── Ping via subprocess (Android /system/bin/ping) ─────────────────────────
def _ping_subprocess():
    """Run system ping binary — ICMP, most reliable on Android."""
    for host in ("8.8.8.8", "1.1.1.1"):
        try:
            out = subprocess.check_output(
                ["/system/bin/ping", "-c", "1", "-W", "2", host],
                stderr=subprocess.DEVNULL,
                timeout=4
            ).decode(errors="ignore")
            # Parse "rtt min/avg/max/mdev = 12.3/12.3/12.3/0.0 ms"
            m = re.search(r"min/avg/max[^=]*=\s*([\d.]+)", out)
            if m:
                return round(float(m.group(1)), 1)
            # Some Android versions: "time=12.3 ms"
            m = re.search(r"time=([\d.]+)\s*ms", out)
            if m:
                return round(float(m.group(1)), 1)
        except Exception:
            continue
    return None


def _ping_jnius():
    """InetAddress.isReachable() — Java ICMP/TCP fallback."""
    try:
        from jnius import autoclass  # type: ignore
        InetAddress = autoclass("java.net.InetAddress")
        addr = InetAddress.getByName("8.8.8.8")
        t0   = time.time()
        ok   = addr.isReachable(2000)
        ms   = round((time.time() - t0) * 1000, 1)
        if ok and ms > 0:
            return ms
    except Exception:
        pass
    return None


def _ping_tcp():
    """TCP SYN timing — last resort."""
    import socket as _socket
    for host, port in [("8.8.8.8", 53), ("1.1.1.1", 443)]:
        try:
            s = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
            s.settimeout(2.0)
            t0  = time.time()
            err = s.connect_ex((host, port))
            ms  = round((time.time() - t0) * 1000, 1)
            s.close()
            if ms > 0:
                return ms
        except Exception:
            continue
    return None


def _ping_worker():
    global _ping_ms
    while True:
        ms = _ping_subprocess()
        if ms is None:
            ms = _ping_jnius()
        if ms is None:
            ms = _ping_tcp()
        _ping_ms = ms
        time.sleep(5)


# ── Band/signal detection ───────────────────────────────────────────────────
def _detect_signal():
    global _band_mbps

    # ConnectivityManager + NetworkCapabilities (API 21+, NO permission)
    try:
        from jnius import autoclass  # type: ignore
        Context        = autoclass("android.content.Context")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")

        ctx  = PythonActivity.mActivity
        cm   = ctx.getSystemService(Context.CONNECTIVITY_SERVICE)
        net  = cm.getActiveNetwork()
        if net is None:
            return "No Network"

        caps = cm.getNetworkCapabilities(net)
        if caps is None:
            return "Unknown"

        # Integer literals — avoids pyjnius static field access issues
        TRANSPORT_CELLULAR = 0
        TRANSPORT_WIFI     = 1
        TRANSPORT_ETHERNET = 3

        if caps.hasTransport(TRANSPORT_WIFI):
            try:
                wm    = ctx.getSystemService(Context.WIFI_SERVICE)
                info  = wm.getConnectionInfo()
                rssi  = info.getRssi()
                speed = info.getLinkSpeed()   # Mbps
                freq  = info.getFrequency()   # MHz
                band  = "5GHz" if freq >= 5000 else "2.4GHz"
                q     = ("Excellent" if rssi >= -50 else
                         "Good"      if rssi >= -65 else
                         "Fair"      if rssi >= -75 else "Weak")
                _band_mbps = 300.0 if freq >= 5000 else 100.0
                return f"WiFi {band} {rssi}dBm {q}"
            except Exception:
                _band_mbps = 100.0
                return "WiFi"

        elif caps.hasTransport(TRANSPORT_CELLULAR):
            try:
                dl = caps.getLinkDownstreamBandwidthKbps()
                ul = caps.getLinkUpstreamBandwidthKbps()
                if dl >= 50000:
                    gen = "5G NR";  _band_mbps = 500.0
                elif dl >= 5000:
                    gen = "4G LTE"; _band_mbps = 50.0
                elif dl >= 1000:
                    gen = "4G";     _band_mbps = 20.0
                elif dl >= 200:
                    gen = "3G";     _band_mbps = 14.0
                elif dl > 0:
                    gen = "2G";     _band_mbps = 0.2
                else:
                    gen = "Mobile"; _band_mbps = 10.0
                return f"{gen} {dl//1000}↓/{ul//1000}↑ Mbps"
            except Exception:
                _band_mbps = 10.0
                return "Mobile"

        elif caps.hasTransport(TRANSPORT_ETHERNET):
            _band_mbps = 1000.0
            return "Ethernet"

        return "Connected"

    except Exception:
        pass

    # /proc/net/wireless (Android 9-)
    try:
        with open("/proc/net/wireless") as f:
            lines = f.readlines()
        for line in lines[2:]:
            p = line.split()
            if len(p) >= 4:
                try:
                    dbm = int(float(p[2].rstrip(".")))
                    if dbm < 0:
                        q = ("Excellent" if dbm >= -50 else
                             "Good"      if dbm >= -65 else
                             "Fair"      if dbm >= -75 else "Weak")
                        _band_mbps = 100.0
                        return f"WiFi {dbm}dBm {q}"
                except Exception:
                    pass
    except Exception:
        pass

    # sysfs operstate
    for p in glob.glob("/sys/class/net/wlan*/operstate"):
        try:
            with open(p) as f:
                if f.read().strip() == "up":
                    _band_mbps = 100.0
                    return "WiFi"
        except Exception:
            pass
    for p in glob.glob("/sys/class/net/rmnet*/operstate"):
        try:
            with open(p) as f:
                if f.read().strip() == "up":
                    _band_mbps = 10.0
                    return "Mobile"
        except Exception:
            pass

    return "No Network"


def _signal_worker():
    global _signal_str
    while True:
        result = _detect_signal()
        if result:
            _signal_str = result
        time.sleep(8)


# ── Traffic bytes ───────────────────────────────────────────────────────────
def _read_bytes():
    try:
        from jnius import autoclass  # type: ignore
        ts = autoclass("android.net.TrafficStats")
        rx = ts.getTotalRxBytes()
        tx = ts.getTotalTxBytes()
        if rx >= 0 and tx >= 0:
            return int(rx), int(tx)
    except Exception:
        pass
    rx = tx = 0
    try:
        with open("/proc/net/dev") as f:
            for line in f.readlines()[2:]:
                p = line.split()
                if len(p) < 10 or p[0].rstrip(":") == "lo":
                    continue
                rx += int(p[1])
                tx += int(p[9])
    except Exception:
        pass
    return rx, tx


def _fmt(bps):
    if bps < 0:
        bps = 0
    kbps = bps / 1024.0
    if kbps >= 1024:
        return f"{kbps/1024:.1f} MB/s"
    if kbps >= 1:
        return f"{kbps:.0f} KB/s"
    return "0 KB/s"


# ── Public API ──────────────────────────────────────────────────────────────
def get_network() -> dict:
    global _bg_started

    if not _bg_started:
        _bg_started = True
        threading.Thread(target=_ping_worker,   daemon=True).start()
        threading.Thread(target=_signal_worker, daemon=True).start()

    rx, tx = _read_bytes()
    now    = time.time()
    ping_str = f"{_ping_ms}ms" if _ping_ms is not None else "--"

    if not _bw:
        _bw.update({"rx": rx, "tx": tx, "t": now,
                    "last_dl": "0 KB/s", "last_ul": "0 KB/s", "arc_pct": 0.0})
        return {"dl": "0 KB/s", "ul": "0 KB/s",
                "ping": ping_str, "signal": _signal_str, "arc_pct": 0.0}

    dt = now - _bw["t"]
    if dt < 0.5:
        return {"dl":  _bw["last_dl"], "ul": _bw["last_ul"],
                "ping": ping_str, "signal": _signal_str,
                "arc_pct": _bw.get("arc_pct", 0.0)}

    dl_bps = (rx - _bw["rx"]) / dt
    ul_bps = (tx - _bw["tx"]) / dt

    max_bps = _band_mbps * 125_000
    arc_pct = min(100.0, dl_bps / max_bps * 100) if max_bps > 0 else 0.0

    dl_str = _fmt(dl_bps)
    ul_str = _fmt(ul_bps)
    _bw.update({"rx": rx, "tx": tx, "t": now,
                "last_dl": dl_str, "last_ul": ul_str, "arc_pct": arc_pct})

    return {"dl": dl_str, "ul": ul_str,
            "ping": ping_str, "signal": _signal_str, "arc_pct": arc_pct}
