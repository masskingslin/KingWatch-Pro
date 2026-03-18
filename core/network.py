"""
KingWatch Pro v17 - core/network.py
Google-speed-test style: stable speeds, no blink, 5G/4G band, real ping.
"""
import time, threading, os, glob, subprocess, re

# ── shared state ────────────────────────────────────────────────────────────
_ping_ms    = None
_signal_str = "Detecting..."
_band_mbps  = 10.0
_bg_started = False
_bw         = {}
_lock       = threading.Lock()


# ── Ping worker ─────────────────────────────────────────────────────────────
def _do_ping():
    # Method 1: Android system ping binary
    for host in ("8.8.8.8", "1.1.1.1"):
        try:
            out = subprocess.check_output(
                ["/system/bin/ping", "-c", "3", "-W", "2", host],
                stderr=subprocess.DEVNULL, timeout=8
            ).decode(errors="ignore")
            m = re.search(r"min/avg/max[^=]+=\s*([\d.]+)/([\d.]+)", out)
            if m:
                return round(float(m.group(1)), 1)
            m = re.search(r"time=([\d.]+)\s*ms", out)
            if m:
                return round(float(m.group(1)), 1)
        except Exception:
            continue

    # Method 2: Java InetAddress.isReachable
    try:
        from jnius import autoclass  # type: ignore
        addr = autoclass("java.net.InetAddress").getByName("8.8.8.8")
        t0   = time.time()
        ok   = addr.isReachable(3000)
        ms   = round((time.time() - t0) * 1000, 1)
        if ok:
            return ms
    except Exception:
        pass

    # Method 3: TCP connect via alias to avoid Python 3.11 cache bug
    import socket as _sock
    for ip, port in [("8.8.8.8", 53), ("1.1.1.1", 443)]:
        try:
            s   = _sock.socket(_sock.AF_INET, _sock.SOCK_STREAM)
            s.settimeout(2.0)
            t0  = time.time()
            s.connect_ex((ip, port))
            ms  = round((time.time() - t0) * 1000, 1)
            s.close()
            if ms > 0:
                return ms
        except Exception:
            continue
    return None


def _ping_worker():
    global _ping_ms
    time.sleep(1)   # let app start first
    while True:
        ms = _do_ping()
        with _lock:
            _ping_ms = ms
        time.sleep(5)


# ── Signal/band worker ──────────────────────────────────────────────────────
def _detect_signal():
    global _band_mbps

    try:
        from jnius import autoclass  # type: ignore
        Context        = autoclass("android.content.Context")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        ctx = PythonActivity.mActivity

        cm  = ctx.getSystemService(Context.CONNECTIVITY_SERVICE)
        net = cm.getActiveNetwork()

        if net is None:
            # Phone may still have signal even if getActiveNetwork() is slow
            # Try ConnectivityManager.getAllNetworks()
            try:
                nets = cm.getAllNetworks()
                if nets and len(nets) > 0:
                    net = nets[0]
            except Exception:
                pass

        if net is None:
            return "Searching..."

        caps = cm.getNetworkCapabilities(net)
        if caps is None:
            return "Connected"

        # Use integer literals — avoids pyjnius static field bugs
        TRANSPORT_WIFI     = 1
        TRANSPORT_CELLULAR = 0
        TRANSPORT_ETHERNET = 3

        if caps.hasTransport(TRANSPORT_WIFI):
            try:
                wm    = ctx.getSystemService(Context.WIFI_SERVICE)
                info  = wm.getConnectionInfo()
                rssi  = info.getRssi()
                freq  = info.getFrequency()
                speed = info.getLinkSpeed()
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
            # getLinkDownstreamBandwidthKbps — no permission needed, API 21+
            dl = 0
            ul = 0
            try:
                dl = caps.getLinkDownstreamBandwidthKbps()
                ul = caps.getLinkUpstreamBandwidthKbps()
            except Exception:
                pass

            if dl >= 100000:
                gen = "5G NR";     _band_mbps = 1000.0
            elif dl >= 20000:
                gen = "5G";        _band_mbps = 500.0
            elif dl >= 5000:
                gen = "4G LTE";    _band_mbps = 50.0
            elif dl >= 1000:
                gen = "4G";        _band_mbps = 20.0
            elif dl >= 200:
                gen = "3G";        _band_mbps = 14.0
            elif dl > 0:
                gen = "2G";        _band_mbps = 0.5
            else:
                # dl=0 means API<29 or unknown — use getNetworkType string
                gen = _cellular_gen_fallback(ctx, Context)
                if not gen:
                    gen = "Mobile"; _band_mbps = 10.0

            dl_m = dl // 1000
            ul_m = ul // 1000
            if dl_m > 0:
                return f"{gen} {dl_m}↓/{ul_m}↑Mbps"
            return gen

        elif caps.hasTransport(TRANSPORT_ETHERNET):
            _band_mbps = 1000.0
            return "Ethernet"

        return "Connected"

    except Exception:
        pass

    # /proc/net/wireless fallback
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

    # sysfs operstate fallback
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

    return "No Signal"


def _cellular_gen_fallback(ctx, Context):
    """Try getNetworkTypeName without READ_PHONE_STATE — works on many devices."""
    global _band_mbps
    try:
        from jnius import autoclass  # type: ignore
        TM = autoclass("android.telephony.TelephonyManager")
        tm = ctx.getSystemService(Context.TELEPHONY_SERVICE)
        # getDataNetworkType() — no permission on Android 12+
        for method in ("getDataNetworkType", "getNetworkType"):
            try:
                nt   = getattr(tm, method)()
                name = TM.getNetworkTypeName(nt).upper()
                if name in ("UNKNOWN", ""):
                    continue
                if   "NR"   in name: _band_mbps=500.0;  return "5G NR"
                elif "LTE"  in name: _band_mbps=50.0;   return "4G LTE"
                elif "HSPA" in name: _band_mbps=42.0;   return "3G HSPA+"
                elif "UMTS" in name: _band_mbps=2.0;    return "3G"
                elif "EDGE" in name: _band_mbps=0.2;    return "2G"
                elif "GPRS" in name: _band_mbps=0.1;    return "2G"
                elif "GSM"  in name: _band_mbps=0.1;    return "2G"
                else: _band_mbps=10.0; return name[:8]
            except Exception:
                continue
    except Exception:
        pass
    return ""


def _signal_worker():
    global _signal_str
    time.sleep(0.5)
    while True:
        result = _detect_signal()
        if result:
            with _lock:
                _signal_str = result
        time.sleep(8)


# ── Traffic bytes ────────────────────────────────────────────────────────────
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
    if bps < 0: bps = 0
    kbps = bps / 1024.0
    if kbps >= 1024:
        return f"{kbps/1024:.1f} MB/s"
    if kbps >= 1:
        return f"{kbps:.0f} KB/s"
    return "0 KB/s"


# ── Public API ───────────────────────────────────────────────────────────────
def get_network() -> dict:
    global _bg_started

    if not _bg_started:
        _bg_started = True
        threading.Thread(target=_ping_worker,   daemon=True).start()
        threading.Thread(target=_signal_worker, daemon=True).start()

    rx, tx = _read_bytes()
    now    = time.time()

    with _lock:
        ping_str   = f"{_ping_ms}ms" if _ping_ms is not None else "--"
        signal_str = _signal_str

    if not _bw:
        _bw.update({"rx": rx, "tx": tx, "t": now,
                    "last_dl": "0 KB/s", "last_ul": "0 KB/s", "arc_pct": 0.0})
        return {"dl": "0 KB/s", "ul": "0 KB/s",
                "ping": ping_str, "signal": signal_str, "arc_pct": 0.0}

    dt = now - _bw["t"]
    if dt < 0.5:
        return {"dl": _bw["last_dl"], "ul": _bw["last_ul"],
                "ping": ping_str, "signal": signal_str,
                "arc_pct": _bw.get("arc_pct", 0.0)}

    dl_bps = max(0.0, (rx - _bw["rx"]) / dt)
    ul_bps = max(0.0, (tx - _bw["tx"]) / dt)

    max_bps = _band_mbps * 125_000
    arc_pct = min(100.0, dl_bps / max_bps * 100) if max_bps > 0 else 0.0

    dl_str = _fmt(dl_bps)
    ul_str = _fmt(ul_bps)
    _bw.update({"rx": rx, "tx": tx, "t": now,
                "last_dl": dl_str, "last_ul": ul_str, "arc_pct": arc_pct})

    return {"dl": dl_str, "ul": ul_str,
            "ping": ping_str, "signal": signal_str, "arc_pct": arc_pct}
