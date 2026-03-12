"""
network.py -- Android restriction-safe version
-----------------------------------------------
Android 10+ blocks /proc/net/dev and /proc/net/wireless
TelephonyManager requires READ_PHONE_STATE (dangerous permission, Play flags it)

SAFE alternatives used:
  - android.net.TrafficStats      -> TX/RX bytes (no permission, API 8+)
  - android.net.ConnectivityManager + NetworkCapabilities -> connection type (no permission, API 21+)
  - No TelephonyManager at all    -> avoids READ_PHONE_STATE
"""

import time, socket, threading, os, glob

_ping_ms    = None
_signal_str = "Detecting..."
_bg_started = False

# -- Ping worker ------------------------------------------
def _ping_worker():
    global _ping_ms
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            t0 = time.time()
            s.connect(("8.8.8.8", 53))
            s.close()
            _ping_ms = round((time.time() - t0) * 1000, 1)
        except Exception:
            _ping_ms = None
        time.sleep(5)

# -- Signal worker -- NO READ_PHONE_STATE ------------------
def _signal_worker():
    global _signal_str
    while True:
        _signal_str = _detect_signal_safe()
        time.sleep(8)

def _detect_signal_safe():
    """
    Detect connection type WITHOUT READ_PHONE_STATE.
    Uses ConnectivityManager.NetworkCapabilities -- no dangerous permission.
    """
    # -- Method 1: ConnectivityManager (API 21+, no permission needed) ---
    try:
        from jnius import autoclass
        Context             = autoclass("android.content.Context")
        PythonActivity      = autoclass("org.kivy.android.PythonActivity")
        ConnectivityManager = autoclass("android.net.ConnectivityManager")
        NetworkCapabilities = autoclass("android.net.NetworkCapabilities")

        cm = PythonActivity.mActivity.getSystemService(Context.CONNECTIVITY_SERVICE)
        net = cm.getActiveNetwork()
        if net is None:
            return "No Connection"

        caps = cm.getNetworkCapabilities(net)
        if caps is None:
            return "Unknown"

        # Transport type
        TRANSPORT_WIFI      = 1
        TRANSPORT_CELLULAR  = 0
        TRANSPORT_ETHERNET  = 3

        if caps.hasTransport(TRANSPORT_WIFI):
            # WiFi -- get RSSI from WifiManager (needs ACCESS_WIFI_STATE, already declared)
            try:
                WifiManager = autoclass("android.net.wifi.WifiManager")
                wm   = PythonActivity.mActivity.getSystemService(Context.WIFI_SERVICE)
                info = wm.getConnectionInfo()
                rssi = info.getRssi()
                # RSSI to quality
                if rssi >= -50:
                    q = "Excellent"
                elif rssi >= -65:
                    q = "Good"
                elif rssi >= -75:
                    q = "Fair"
                else:
                    q = "Weak"
                speed = info.getLinkSpeed()   # Mbps
                return f"WiFi {rssi}dBm {q} {speed}Mbps"
            except Exception:
                return "WiFi Connected"

        elif caps.hasTransport(TRANSPORT_CELLULAR):
            # Cellular -- detect generation from downlink bandwidth (no permission)
            try:
                # API 29+: getLinkDownstreamBandwidthKbps
                dl_kbps = caps.getLinkDownstreamBandwidthKbps()
                if dl_kbps >= 20000:
                    gen = "5G"
                elif dl_kbps >= 1000:
                    gen = "4G LTE"
                elif dl_kbps >= 200:
                    gen = "3G"
                elif dl_kbps > 0:
                    gen = "2G"
                else:
                    gen = "Mobile"
                ul_kbps = caps.getLinkUpstreamBandwidthKbps()
                return f"{gen} ({dl_kbps//1000}v/{ul_kbps//1000}^ Mbps)"
            except Exception:
                return "Mobile Data"

        elif caps.hasTransport(TRANSPORT_ETHERNET):
            return "Ethernet"

        return "Connected"

    except Exception:
        pass

    # -- Method 2: /proc/net/wireless (works Android 9 and below) --------
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
                        return f"WiFi {dbm}dBm {q}"
                except Exception:
                    pass
    except Exception:
        pass

    # -- Method 3: sysfs operstate ----------------------------------------
    for p in glob.glob("/sys/class/net/wlan*/operstate"):
        try:
            with open(p) as f:
                if f.read().strip() == "up":
                    return "WiFi"
        except Exception:
            pass
    for p in glob.glob("/sys/class/net/rmnet*/operstate"):
        try:
            with open(p) as f:
                if f.read().strip() == "up":
                    return "Mobile"
        except Exception:
            pass

    return "No Network"

# -- Bandwidth -- TrafficStats (safe, no permission) -------
_bw = {}

def _fmt(bps):
    if bps < 0: bps = 0
    kbps = bps / 1024.0
    if kbps >= 1024:
        return f"{kbps/1024:.1f} MB/s"
    return f"{kbps:.1f} KB/s"

def _read_bytes():
    # Android TrafficStats -- no permission, counts ALL app traffic
    try:
        from jnius import autoclass
        ts = autoclass("android.net.TrafficStats")
        tx = ts.getTotalTxBytes()
        rx = ts.getTotalRxBytes()
        if tx >= 0 and rx >= 0:
            return rx, tx
    except Exception:
        pass

    # Fallback for non-Android
    rx = tx = 0
    try:
        with open("/proc/net/dev") as f:
            for line in f.readlines()[2:]:
                p = line.split()
                if len(p) < 10 or p[0].rstrip(":") == "lo":
                    continue
                rx += int(p[1])
                tx += int(p[9])
        return rx, tx
    except Exception:
        pass
    return 0, 0

def get_network():
    global _bg_started
    if not _bg_started:
        _bg_started = True
        threading.Thread(target=_ping_worker,   daemon=True).start()
        threading.Thread(target=_signal_worker, daemon=True).start()

    rx, tx   = _read_bytes()
    now      = time.time()
    ping_str = f"{_ping_ms} ms" if _ping_ms is not None else "Pinging..."

    if not _bw:
        _bw.update({"rx": rx, "tx": tx, "t": now,
                    "last_dl": "0 KB/s", "last_ul": "0 KB/s"})
        return {"dl": "0 KB/s", "ul": "0 KB/s",
                "ping": ping_str, "signal": _signal_str}

    dt = now - _bw["t"]
    if dt < 0.5:
        return {"dl": _bw["last_dl"], "ul": _bw["last_ul"],
                "ping": ping_str, "signal": _signal_str}

    dl_bps = (rx - _bw["rx"]) / dt
    ul_bps = (tx - _bw["tx"]) / dt
    dl_str, ul_str = _fmt(dl_bps), _fmt(ul_bps)
    _bw.update({"rx": rx, "tx": tx, "t": now,
                "last_dl": dl_str, "last_ul": ul_str})

    return {"dl": dl_str, "ul": ul_str,
            "ping": ping_str, "signal": _signal_str}
