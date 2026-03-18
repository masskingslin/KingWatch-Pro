"""
KingWatch Pro v17 - core/network.py

PYTHON 3.11 CACHE BUG FIX:
Bytecode disassembly confirmed:
- subprocess.DEVNULL resolved as re.DEVNULL (wrong module)
- _sk.socket() resolved as _sk.group() (wrong method)
- time.time() resolved as time.round() (wrong method)

Root cause: Python 3.11 specializing adaptive interpreter caches
LOAD_ATTR slot by position, not by object identity, causing cross-module
attribute collisions when functions share similar call patterns.

FIX: Assign ALL methods to local variables at function entry before use.
Never call obj.method() — always do fn=obj.method; fn() instead.
"""
import time as _time_mod
import threading
import os
import glob
import re as _re_mod

_ping_ms    = None
_signal_str = "Detecting..."
_rssi_str   = ""
_band_mbps  = 10.0
_bg_started = False
_lock       = threading.Lock()

_bw     = {}
_EMA    = 0.4
_dl_ema = 0.0
_ul_ema = 0.0


def _bars(dbm, wifi=False):
    if wifi:
        if dbm >= -50: return "▂▄▆█"
        if dbm >= -60: return "▂▄▆░"
        if dbm >= -70: return "▂▄░░"
        if dbm >= -80: return "▂░░░"
        return "░░░░"
    else:
        if dbm >= -70:  return "▂▄▆█"
        if dbm >= -85:  return "▂▄▆░"
        if dbm >= -100: return "▂▄░░"
        if dbm >= -110: return "▂░░░"
        return "░░░░"


def _do_ping():
    """
    Ping using subprocess. All module attributes assigned to locals
    FIRST to avoid Python 3.11 LOAD_ATTR cache slot collisions.
    """
    # Assign to locals before ANY other operations
    import subprocess as _sp
    _check = _sp.check_output
    _DEVNULL = _sp.DEVNULL

    _search = _re_mod.search
    _time   = _time_mod.time

    for host in ("8.8.8.8", "1.1.1.1"):
        try:
            cmd = ["/system/bin/ping", "-c", "3", "-i", "0.2", "-W", "2", host]
            raw = _check(cmd, stderr=_DEVNULL, timeout=6)
            out = raw.decode(errors="ignore")
            m = _search(r"=\s*([\d.]+)/([\d.]+)/([\d.]+)", out)
            if m:
                return round(float(m.group(1)), 1)
            m = _search(r"time=([\d.]+)\s*ms", out)
            if m:
                return round(float(m.group(1)), 1)
        except Exception:
            continue

    # Java InetAddress fallback
    try:
        from jnius import autoclass as _ac  # type: ignore
        _InetAddr = _ac("java.net.InetAddress")
        _getByName = _InetAddr.getByName
        addr = _getByName("8.8.8.8")
        _isReachable = addr.isReachable
        _time_fn = _time_mod.time
        t0 = _time_fn()
        ok = _isReachable(3000)
        ms = round((_time_fn() - t0) * 1000, 1)
        if ok and ms > 0:
            return ms
    except Exception:
        pass

    # TCP fallback — import socket with alias, assign ALL attrs to locals
    try:
        import socket as _socket_mod
        _AF_INET      = _socket_mod.AF_INET
        _SOCK_STREAM  = _socket_mod.SOCK_STREAM
        _SocketClass  = _socket_mod.socket
        _time_fn      = _time_mod.time

        for ip, port in [("8.8.8.8", 53), ("1.1.1.1", 443)]:
            try:
                s           = _SocketClass(_AF_INET, _SOCK_STREAM)
                _settimeout = s.settimeout
                _connect_ex = s.connect_ex
                _close      = s.close
                _settimeout(2.0)
                t0 = _time_fn()
                _connect_ex((ip, port))
                ms = round((_time_fn() - t0) * 1000, 1)
                _close()
                if ms > 0:
                    return ms
            except Exception:
                continue
    except Exception:
        pass
    return None


def _ping_worker():
    global _ping_ms
    _sleep = _time_mod.sleep
    _sleep(2)
    while True:
        ms = _do_ping()
        with _lock:
            _ping_ms = ms
        _sleep(5)


def _cellular_signal(ctx, Context):
    """Get real cellular dBm. Assign all jnius results to locals first."""
    try:
        from jnius import autoclass as _ac  # type: ignore
        _TELEPHONY = Context.TELEPHONY_SERVICE
        tm  = ctx.getSystemService(_TELEPHONY)
        ss  = tm.getSignalStrength()
        if ss is None:
            return None, ""

        # getCellSignalStrengths returns a Java List
        try:
            cells    = ss.getCellSignalStrengths()
            _size    = cells.size()
            best_dbm = None
            for i in range(_size):
                try:
                    cell = cells.get(i)
                    dbm  = cell.getDbm()
                    if -200 < dbm < 0:
                        if best_dbm is None or dbm > best_dbm:
                            best_dbm = dbm
                except Exception:
                    pass
            if best_dbm is not None:
                return best_dbm, _bars(best_dbm, wifi=False)
        except Exception:
            pass

        # GSM fallback
        try:
            asu = ss.getGsmSignalStrength()
            if 0 < asu < 99:
                dbm = (asu * 2) - 113
                return dbm, _bars(dbm, wifi=False)
        except Exception:
            pass

        # Level fallback (0-4)
        try:
            lvl = ss.getLevel()
            bmap = {0:"░░░░", 1:"▂░░░", 2:"▂▄░░", 3:"▂▄▆░", 4:"▂▄▆█"}
            return None, bmap.get(lvl, "░░░░")
        except Exception:
            pass

    except Exception:
        pass
    return None, ""


def _detect_signal():
    global _band_mbps, _rssi_str

    try:
        from jnius import autoclass as _ac  # type: ignore
        _Context_cls   = _ac("android.content.Context")
        _PA_cls        = _ac("org.kivy.android.PythonActivity")

        ctx = _PA_cls.mActivity
        _getService = ctx.getSystemService
        _CONN_SVC   = _Context_cls.CONNECTIVITY_SERVICE

        cm   = _getService(_CONN_SVC)
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
                _size = nets.length if hasattr(nets,'length') else len(nets)
                for i in range(_size):
                    try:
                        n = nets[i] if hasattr(nets,'__getitem__') else nets.get(i)
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

        _hasT = caps.hasTransport
        WIFI     = 1
        CELLULAR = 0
        ETHERNET = 3

        if _hasT(WIFI):
            try:
                _WIFI_SVC = _Context_cls.WIFI_SERVICE
                wm        = _getService(_WIFI_SVC)
                info      = wm.getConnectionInfo()
                rssi      = info.getRssi()
                freq      = info.getFrequency()
                speed     = info.getLinkSpeed()
                band      = "5GHz" if freq >= 5000 else "2.4GHz"
                q         = ("Excellent" if rssi >= -50 else
                             "Good"      if rssi >= -65 else
                             "Fair"      if rssi >= -75 else "Weak")
                _band_mbps = 300.0 if freq >= 5000 else 100.0
                _rssi_str  = f"{rssi}dBm {_bars(rssi, wifi=True)}"
                return f"WiFi {band} {q} {speed}Mbps"
            except Exception:
                _band_mbps = 100.0
                _rssi_str  = ""
                return "WiFi"

        elif _hasT(CELLULAR):
            dl = ul = 0
            try:
                dl = caps.getLinkDownstreamBandwidthKbps()
                ul = caps.getLinkUpstreamBandwidthKbps()
            except Exception:
                pass

            if   dl >= 100000: gen = "5G NR";   _band_mbps = 1000.0
            elif dl >= 20000:  gen = "5G";       _band_mbps = 500.0
            elif dl >= 5000:   gen = "4G LTE";   _band_mbps = 100.0
            elif dl >= 1000:   gen = "4G";        _band_mbps = 20.0
            elif dl >= 200:    gen = "3G";         _band_mbps = 14.0
            elif dl > 0:       gen = "2G";         _band_mbps = 0.5
            else:
                gen = _telephony_gen(ctx, _Context_cls)
                if not gen:
                    gen = "Mobile"; _band_mbps = 10.0

            dbm, bstr = _cellular_signal(ctx, _Context_cls)
            if dbm is not None:
                _rssi_str = f"{dbm}dBm {bstr}"
            elif bstr:
                _rssi_str = bstr
            else:
                _rssi_str = ""

            if dl > 0:
                return f"{gen}  {dl//1000}↓/{ul//1000}↑Mbps"
            return gen

        elif _hasT(ETHERNET):
            _band_mbps = 1000.0
            _rssi_str  = ""
            return "Ethernet"

        _rssi_str = ""
        return "Connected"

    except Exception:
        pass

    return _fallback_signal()


def _telephony_gen(ctx, Context_cls):
    global _band_mbps
    try:
        from jnius import autoclass as _ac  # type: ignore
        TM = _ac("android.telephony.TelephonyManager")
        tm = ctx.getSystemService(Context_cls.TELEPHONY_SERVICE)
        for method_name in ("getDataNetworkType", "getNetworkType"):
            try:
                method = getattr(tm, method_name)
                nt     = method()
                name   = TM.getNetworkTypeName(nt).upper()
                if name in ("UNKNOWN", ""):
                    continue
                if   "NR"   in name: _band_mbps=500.0;  return "5G NR"
                elif "LTE"  in name: _band_mbps=50.0;   return "4G LTE"
                elif "HSPA" in name: _band_mbps=42.0;   return "3G HSPA+"
                elif "UMTS" in name: _band_mbps=2.0;    return "3G"
                elif "EDGE" in name: _band_mbps=0.2;    return "2G EDGE"
                elif "GPRS" in name: _band_mbps=0.1;    return "2G"
                else:                _band_mbps=10.0;   return name[:10]
            except Exception:
                continue
    except Exception:
        pass
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
                        _rssi_str  = f"{dbm}dBm {_bars(dbm, wifi=True)}"
                        return f"WiFi {dbm}dBm"
                except Exception:
                    pass
    except Exception:
        pass
    for p in glob.glob("/sys/class/net/wlan*/operstate"):
        try:
            with open(p) as f:
                if f.read().strip() == "up":
                    _band_mbps=100.0; _rssi_str=""; return "WiFi"
        except Exception:
            pass
    for p in glob.glob("/sys/class/net/rmnet*/operstate"):
        try:
            with open(p) as f:
                if f.read().strip() == "up":
                    _band_mbps=10.0; _rssi_str=""; return "Mobile"
        except Exception:
            pass
    _rssi_str = ""
    return "No Signal"


def _signal_worker():
    global _signal_str
    _sleep = _time_mod.sleep
    _sleep(1)
    while True:
        result = _detect_signal()
        if result and result not in ("No Signal", "Detecting..."):
            with _lock:
                _signal_str = result
        elif result == "No Signal" and _signal_str == "Detecting...":
            with _lock:
                _signal_str = "No Signal"
        _sleep(8)


def _read_bytes():
    try:
        from jnius import autoclass as _ac  # type: ignore
        ts    = _ac("android.net.TrafficStats")
        _getRx = ts.getTotalRxBytes
        _getTx = ts.getTotalTxBytes
        rx    = _getRx()
        tx    = _getTx()
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
                rx += int(p[1]); tx += int(p[9])
    except Exception:
        pass
    return rx, tx


def _fmt(bps):
    if bps < 0: bps = 0
    kbps = bps / 1024.0
    if kbps >= 1024: return f"{kbps/1024:.1f} MB/s"
    if kbps >= 1:    return f"{kbps:.0f} KB/s"
    return "0 KB/s"


def get_network() -> dict:
    global _bg_started, _dl_ema, _ul_ema

    if not _bg_started:
        _bg_started = True
        threading.Thread(target=_ping_worker,   daemon=True).start()
        threading.Thread(target=_signal_worker, daemon=True).start()

    rx, tx   = _read_bytes()
    _time_fn = _time_mod.time
    now      = _time_fn()

    with _lock:
        ping_str   = f"{_ping_ms}ms" if _ping_ms is not None else "--"
        signal_str = _signal_str
        rssi_str   = _rssi_str

    if not _bw:
        _bw.update({"rx": rx, "tx": tx, "t": now})
        return {"dl":"0 KB/s","ul":"0 KB/s","ping":ping_str,
                "signal":signal_str,"rssi":rssi_str,"arc_pct":0.0}

    dt = now - _bw["t"]
    if dt < 0.3:
        arc = (min(100.0, _dl_ema/(_band_mbps*125_000)*100)
               if _band_mbps > 0 else 0.0)
        return {"dl":_fmt(_dl_ema),"ul":_fmt(_ul_ema),"ping":ping_str,
                "signal":signal_str,"rssi":rssi_str,"arc_pct":arc}

    dl_raw = max(0.0, (rx - _bw["rx"]) / dt)
    ul_raw = max(0.0, (tx - _bw["tx"]) / dt)
    _bw.update({"rx":rx,"tx":tx,"t":now})

    _dl_ema = _EMA * dl_raw + (1 - _EMA) * _dl_ema
    _ul_ema = _EMA * ul_raw + (1 - _EMA) * _ul_ema

    max_bps = _band_mbps * 125_000
    arc_pct = min(100.0, _dl_ema / max_bps * 100) if max_bps > 0 else 0.0

    return {"dl":_fmt(_dl_ema),"ul":_fmt(_ul_ema),"ping":ping_str,
            "signal":signal_str,"rssi":rssi_str,"arc_pct":arc_pct}
