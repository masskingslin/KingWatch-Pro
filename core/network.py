"""
KingWatch Pro v17 - core/network.py
Adds real cellular signal strength (dBm + bars) like status bar.
Uses TelephonyManager.getSignalStrength() — no permission needed on API 28+.
"""
import time, threading, os, glob, subprocess, re

_ping_ms    = None
_signal_str = "Detecting..."
_rssi_str   = ""          # e.g. "-85 dBm ▂▄▆░"
_band_mbps  = 10.0
_bg_started = False
_lock       = threading.Lock()

_bw     = {}
_EMA    = 0.4
_dl_ema = 0.0
_ul_ema = 0.0


# ── Signal bars from dBm ─────────────────────────────────────────────────────
def _bars(dbm, is_wifi=False):
    """Return bar string based on dBm value."""
    if is_wifi:
        # WiFi: -50 excellent → -80 poor
        if dbm >= -50: return "▂▄▆█"
        if dbm >= -60: return "▂▄▆░"
        if dbm >= -70: return "▂▄░░"
        if dbm >= -80: return "▂░░░"
        return "░░░░"
    else:
        # Cellular: -70 excellent → -110 poor (ASU-based)
        if dbm >= -70:  return "▂▄▆█"
        if dbm >= -85:  return "▂▄▆░"
        if dbm >= -100: return "▂▄░░"
        if dbm >= -110: return "▂░░░"
        return "░░░░"


# ── Cellular signal strength ─────────────────────────────────────────────────
def _cellular_signal(ctx, Context):
    """
    Get actual cellular dBm using TelephonyManager.getSignalStrength().
    Returns (dbm_int, bars_str) or (None, "").
    No permission needed on Android 10+ (API 29+).
    """
    try:
        from jnius import autoclass  # type: ignore
        tm = ctx.getSystemService(Context.TELEPHONY_SERVICE)
        ss = tm.getSignalStrength()
        if ss is None:
            return None, ""

        # Try getCellSignalStrengths() — returns list of all cell signals
        try:
            cells = ss.getCellSignalStrengths()
            best_dbm = None
            for cell in cells:
                try:
                    dbm = cell.getDbm()
                    if dbm < 0 and dbm > -200:
                        if best_dbm is None or dbm > best_dbm:
                            best_dbm = dbm
                except Exception:
                    pass
            if best_dbm is not None:
                return best_dbm, _bars(best_dbm, is_wifi=False)
        except Exception:
            pass

        # Fallback: getGsmSignalStrength() (older API)
        try:
            asu = ss.getGsmSignalStrength()   # 0-31, 99=unknown
            if 0 < asu < 99:
                dbm = (asu * 2) - 113         # ASU → dBm formula
                return dbm, _bars(dbm, is_wifi=False)
        except Exception:
            pass

        # Fallback: getLevel() — 0 to 4
        try:
            level = ss.getLevel()
            bar_map = {0:"░░░░", 1:"▂░░░", 2:"▂▄░░", 3:"▂▄▆░", 4:"▂▄▆█"}
            return None, bar_map.get(level, "░░░░")
        except Exception:
            pass

    except Exception:
        pass
    return None, ""


# ── Detect full signal info ───────────────────────────────────────────────────
def _detect_signal():
    global _band_mbps, _rssi_str

    try:
        from jnius import autoclass  # type: ignore
        Context        = autoclass("android.content.Context")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        ctx = PythonActivity.mActivity
        cm  = ctx.getSystemService(Context.CONNECTIVITY_SERVICE)

        # Get active network caps
        caps = None
        try:
            net = cm.getActiveNetwork()
            if net:
                caps = cm.getNetworkCapabilities(net)
        except Exception:
            pass
        if caps is None:
            try:
                nets = cm.getAllNetworks()
                for n in nets:
                    try:
                        c = cm.getNetworkCapabilities(n)
                        if c:
                            caps = c; break
                    except Exception:
                        pass
            except Exception:
                pass

        if caps is None:
            _rssi_str = ""
            return _fallback_signal()

        TRANSPORT_WIFI     = 1
        TRANSPORT_CELLULAR = 0
        TRANSPORT_ETHERNET = 3

        # ── WiFi ──────────────────────────────────────────────────────────
        if caps.hasTransport(TRANSPORT_WIFI):
            try:
                wm    = ctx.getSystemService(Context.WIFI_SERVICE)
                info  = wm.getConnectionInfo()
                rssi  = info.getRssi()
                freq  = info.getFrequency()
                speed = info.getLinkSpeed()
                band  = "5GHz" if freq >= 5000 else "2.4GHz"
                bars  = _bars(rssi, is_wifi=True)
                q     = ("Excellent" if rssi >= -50 else
                         "Good"      if rssi >= -65 else
                         "Fair"      if rssi >= -75 else "Weak")
                _band_mbps = 300.0 if freq >= 5000 else 100.0
                _rssi_str  = f"{rssi}dBm {bars}"
                return f"WiFi {band} {q} {speed}Mbps"
            except Exception:
                _band_mbps = 100.0
                _rssi_str  = ""
                return "WiFi"

        # ── Cellular ──────────────────────────────────────────────────────
        elif caps.hasTransport(TRANSPORT_CELLULAR):
            dl = ul = 0
            try:
                dl = caps.getLinkDownstreamBandwidthKbps()
                ul = caps.getLinkUpstreamBandwidthKbps()
            except Exception:
                pass

            # Generation from bandwidth
            if   dl >= 100000: gen = "5G NR";   _band_mbps = 1000.0
            elif dl >= 20000:  gen = "5G";       _band_mbps = 500.0
            elif dl >= 5000:   gen = "4G LTE";   _band_mbps = 100.0
            elif dl >= 1000:   gen = "4G";        _band_mbps = 20.0
            elif dl >= 200:    gen = "3G";         _band_mbps = 14.0
            elif dl > 0:       gen = "2G";         _band_mbps = 0.5
            else:
                gen = _telephony_gen(ctx, Context)
                if not gen:
                    gen = "Mobile"; _band_mbps = 10.0

            # Real signal dBm
            dbm, bars = _cellular_signal(ctx, Context)
            if dbm is not None:
                _rssi_str = f"{dbm}dBm {bars}"
            elif bars:
                _rssi_str = bars
            else:
                _rssi_str = ""

            if dl > 0:
                return f"{gen}  {dl//1000}↓/{ul//1000}↑Mbps"
            return gen

        elif caps.hasTransport(TRANSPORT_ETHERNET):
            _band_mbps = 1000.0
            _rssi_str  = ""
            return "Ethernet"

        _rssi_str = ""
        return "Connected"

    except Exception:
        pass

    return _fallback_signal()


def _telephony_gen(ctx, Context):
    global _band_mbps
    try:
        from jnius import autoclass  # type: ignore
        TM = autoclass("android.telephony.TelephonyManager")
        tm = ctx.getSystemService(Context.TELEPHONY_SERVICE)
        for method in ("getDataNetworkType", "getNetworkType"):
            try:
                nt   = getattr(tm, method)()
                name = TM.getNetworkTypeName(nt).upper()
                if name in ("UNKNOWN", ""): continue
                if   "NR"   in name: _band_mbps=500.0;  return "5G NR"
                elif "LTE"  in name: _band_mbps=50.0;   return "4G LTE"
                elif "HSPA" in name: _band_mbps=42.0;   return "3G HSPA+"
                elif "UMTS" in name: _band_mbps=2.0;    return "3G"
                elif "EDGE" in name: _band_mbps=0.2;    return "2G EDGE"
                elif "GPRS" in name: _band_mbps=0.1;    return "2G"
                else:                _band_mbps=10.0;   return name[:10]
            except Exception: continue
    except Exception: pass
    return ""


def _fallback_signal():
    global _band_mbps, _rssi_str
    try:
        with open("/proc/net/wireless") as f:
            lines = f.readlines()
        for line in lines[2:]:
            p = line.split()
            if len(p) >= 4:
                try:
                    dbm = int(float(p[2].rstrip(".")))
                    if dbm < 0:
                        _band_mbps = 100.0
                        _rssi_str  = f"{dbm}dBm {_bars(dbm, is_wifi=True)}"
                        return f"WiFi {dbm}dBm"
                except Exception: pass
    except Exception: pass
    for p in glob.glob("/sys/class/net/wlan*/operstate"):
        try:
            with open(p) as f:
                if f.read().strip() == "up":
                    _band_mbps=100.0; _rssi_str=""; return "WiFi"
        except Exception: pass
    for p in glob.glob("/sys/class/net/rmnet*/operstate"):
        try:
            with open(p) as f:
                if f.read().strip() == "up":
                    _band_mbps=10.0; _rssi_str=""; return "Mobile"
        except Exception: pass
    _rssi_str = ""
    return "No Signal"


def _signal_worker():
    global _signal_str
    time.sleep(1)
    while True:
        result = _detect_signal()
        if result and result not in ("No Signal", "Detecting..."):
            with _lock:
                _signal_str = result
        elif result == "No Signal" and _signal_str == "Detecting...":
            with _lock:
                _signal_str = "No Signal"
        time.sleep(8)


# ── Ping ─────────────────────────────────────────────────────────────────────
def _do_ping():
    for host in ("8.8.8.8", "1.1.1.1"):
        try:
            out = subprocess.check_output(
                ["/system/bin/ping", "-c", "3", "-i", "0.2", "-W", "2", host],
                stderr=subprocess.DEVNULL, timeout=6
            ).decode(errors="ignore")
            m = re.search(r"=\s*([\d.]+)/([\d.]+)/([\d.]+)", out)
            if m: return round(float(m.group(1)), 1)
            m = re.search(r"time=([\d.]+)\s*ms", out)
            if m: return round(float(m.group(1)), 1)
        except Exception: continue
    try:
        from jnius import autoclass  # type: ignore
        addr = autoclass("java.net.InetAddress").getByName("8.8.8.8")
        t0 = time.time()
        ok = addr.isReachable(3000)
        ms = round((time.time()-t0)*1000, 1)
        if ok and ms > 0: return ms
    except Exception: pass
    import socket as _sk
    for ip, port in [("8.8.8.8", 53), ("1.1.1.1", 443)]:
        try:
            s = _sk.socket(_sk.AF_INET, _sk.SOCK_STREAM)
            s.settimeout(2.0)
            t0 = time.time()
            s.connect_ex((ip, port))
            ms = round((time.time()-t0)*1000, 1)
            s.close()
            if ms > 0: return ms
        except Exception: continue
    return None


def _ping_worker():
    global _ping_ms
    time.sleep(2)
    while True:
        ms = _do_ping()
        with _lock:
            _ping_ms = ms
        time.sleep(5)


# ── Traffic bytes ─────────────────────────────────────────────────────────────
def _read_bytes():
    try:
        from jnius import autoclass  # type: ignore
        ts = autoclass("android.net.TrafficStats")
        rx = ts.getTotalRxBytes()
        tx = ts.getTotalTxBytes()
        if rx >= 0 and tx >= 0:
            return int(rx), int(tx)
    except Exception: pass
    rx = tx = 0
    try:
        with open("/proc/net/dev") as f:
            for line in f.readlines()[2:]:
                p = line.split()
                if len(p) < 10 or p[0].rstrip(":") == "lo": continue
                rx += int(p[1]); tx += int(p[9])
    except Exception: pass
    return rx, tx


def _fmt(bps):
    if bps < 0: bps = 0
    kbps = bps / 1024.0
    if kbps >= 1024: return f"{kbps/1024:.1f} MB/s"
    if kbps >= 1:    return f"{kbps:.0f} KB/s"
    return "0 KB/s"


# ── Public API ────────────────────────────────────────────────────────────────
def get_network() -> dict:
    global _bg_started, _dl_ema, _ul_ema

    if not _bg_started:
        _bg_started = True
        threading.Thread(target=_ping_worker,   daemon=True).start()
        threading.Thread(target=_signal_worker, daemon=True).start()

    rx, tx = _read_bytes()
    now    = time.time()

    with _lock:
        ping_str   = f"{_ping_ms}ms" if _ping_ms is not None else "--"
        signal_str = _signal_str
        rssi_str   = _rssi_str

    if not _bw:
        _bw.update({"rx": rx, "tx": tx, "t": now})
        return {"dl": "0 KB/s", "ul": "0 KB/s", "ping": ping_str,
                "signal": signal_str, "rssi": rssi_str, "arc_pct": 0.0}

    dt = now - _bw["t"]
    if dt < 0.3:
        arc = min(100.0, _dl_ema / (_band_mbps*125_000)*100) if _band_mbps>0 else 0.0
        return {"dl": _fmt(_dl_ema), "ul": _fmt(_ul_ema), "ping": ping_str,
                "signal": signal_str, "rssi": rssi_str, "arc_pct": arc}

    dl_raw = max(0.0, (rx - _bw["rx"]) / dt)
    ul_raw = max(0.0, (tx - _bw["tx"]) / dt)
    _bw.update({"rx": rx, "tx": tx, "t": now})

    _dl_ema = _EMA * dl_raw + (1 - _EMA) * _dl_ema
    _ul_ema = _EMA * ul_raw + (1 - _EMA) * _ul_ema

    max_bps = _band_mbps * 125_000
    arc_pct = min(100.0, _dl_ema / max_bps * 100) if max_bps > 0 else 0.0

    return {"dl": _fmt(_dl_ema), "ul": _fmt(_ul_ema), "ping": ping_str,
            "signal": signal_str, "rssi": rssi_str, "arc_pct": arc_pct}
