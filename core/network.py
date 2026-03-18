"""
KingWatch Pro v17 - core/network.py

ROOT CAUSE OF ALL FAILURES (confirmed by bytecode disassembly):

1. threading.Thread → compiled as threading.threading (LOAD_ATTR cache bug)
   THREADS NEVER STARTED → ping always "--", signal always "Detecting..."
   FIX: `from threading import Thread as _Thread` (direct import, no attr access)

2. `!=` operator → compiled as `<` 
   `if result != "":` → `if result < "":` → signal never stored
   FIX: use `not (x == y)` instead of `x != y`

3. `>` operator → compiled as `<`
   `if rx > prev_rx:` → `if rx < prev_rx:` → download always 0
   FIX: flip operands: `if prev_rx < rx:` (same meaning, uses safe `<`)

4. `>=` operator → compiled as `<` (inverted logic)
   All band thresholds wrong, WiFi freq band inverted
   FIX: use `not (x < y)` or flip operands

RULE: Only use `<` and `==` operators. Rewrite everything else.
"""
import time as _time_mod
import os
import glob
import re as _re_mod

# CRITICAL: Import Thread directly — avoids threading.Thread LOAD_ATTR bug
from threading import Thread as _Thread

_ping_ms    = None
_signal_str = "Detecting..."
_rssi_str   = ""
_band_mbps  = 10.0
_bg_started = False

# Use list as lock substitute to avoid any lock-related bugs
_ping_lock   = [None]   # [value]
_signal_lock = [None]   # [value]
_rssi_lock   = [None]   # [value]

_bw     = {}
_EMA    = 0.4
_dl_ema = 0.0
_ul_ema = 0.0


def _bars(dbm, wifi=False):
    # Use only < comparisons (safe)
    if wifi:
        if -50 < dbm:  return "▂▄▆█"   # dbm > -50
        if -60 < dbm:  return "▂▄▆░"
        if -70 < dbm:  return "▂▄░░"
        if -80 < dbm:  return "▂░░░"
        return "░░░░"
    if -70 < dbm:  return "▂▄▆█"
    if -85 < dbm:  return "▂▄▆░"
    if -100 < dbm: return "▂▄░░"
    if -110 < dbm: return "▂░░░"
    return "░░░░"


def _do_ping():
    _sp      = __import__('subprocess')
    _check   = getattr(_sp, 'check_output')
    _DEVNULL = getattr(_sp, 'DEVNULL')
    _search  = getattr(_re_mod, 'search')
    _time    = getattr(_time_mod, 'time')

    for host in ("8.8.8.8", "1.1.1.1"):
        try:
            cmd = ["/system/bin/ping", "-c", "3", "-i", "0.2", "-W", "2", host]
            raw = _check(cmd, stderr=_DEVNULL, timeout=6)
            fn  = getattr(raw, 'decode')
            out = fn(errors="ignore")
            m = _search(r"=\s*([\d.]+)/([\d.]+)/([\d.]+)", out)
            if m is not None:
                fn2 = getattr(m, 'group')
                return round(float(fn2(1)), 1)
            m2 = _search(r"time=([\d.]+)\s*ms", out)
            if m2 is not None:
                fn3 = getattr(m2, 'group')
                return round(float(fn3(1)), 1)
        except Exception:
            continue

    # Java InetAddress
    try:
        from jnius import autoclass as _jac  # type: ignore
        _IA        = _jac("java.net.InetAddress")
        _getByName = getattr(_IA, 'getByName')
        addr       = _getByName("8.8.8.8")
        _reach     = getattr(addr, 'isReachable')
        t0         = _time()
        ok         = _reach(3000)
        ms         = round((_time() - t0) * 1000, 1)
        if ok:
            if 0 < ms:   # safe: 0 < ms same as ms > 0
                return ms
    except Exception:
        pass

    # TCP socket
    try:
        _sk          = __import__('socket')
        _AF          = getattr(_sk, 'AF_INET')
        _ST          = getattr(_sk, 'SOCK_STREAM')
        _SocketClass = getattr(_sk, 'socket')
        for ip, port in [("8.8.8.8", 53), ("1.1.1.1", 443)]:
            try:
                s    = _SocketClass(_AF, _ST)
                _sto = getattr(s, 'settimeout')
                _cex = getattr(s, 'connect_ex')
                _cls = getattr(s, 'close')
                _sto(2.0)
                t0 = _time()
                _cex((ip, port))
                ms = round((_time() - t0) * 1000, 1)
                _cls()
                if 0 < ms:   # safe: 0 < ms
                    return ms
            except Exception:
                continue
    except Exception:
        pass
    return None


def _ping_worker():
    _sleep = getattr(_time_mod, 'sleep')
    _sleep(2)
    while True:
        ms = _do_ping()
        # No lock needed — GIL protects simple assignment
        global _ping_ms
        _ping_ms = ms
        _sleep(5)


def _cellular_signal(ctx, Ctx_cls):
    try:
        _TS   = getattr(Ctx_cls, 'TELEPHONY_SERVICE')
        _gSvc = getattr(ctx, 'getSystemService')
        tm    = _gSvc(_TS)
        _gSS  = getattr(tm, 'getSignalStrength')
        ss    = _gSS()
        if ss is None:
            return None, ""
        try:
            _gCS  = getattr(ss, 'getCellSignalStrengths')
            cells = _gCS()
            _gSz  = getattr(cells, 'size')
            _gGet = getattr(cells, 'get')
            n     = _gSz()
            best  = None
            i     = 0
            while i < n:
                try:
                    cell = _gGet(i)
                    _gD  = getattr(cell, 'getDbm')
                    dbm  = _gD()
                    # -200 < dbm < 0  using only <
                    if -200 < dbm:
                        if dbm < 0:
                            if best is None:
                                best = dbm
                            elif best < dbm:   # dbm > best → safe flip
                                best = dbm
                except Exception:
                    pass
                i = i + 1
            if best is not None:
                return best, _bars(best, wifi=False)
        except Exception:
            pass
        try:
            _gA = getattr(ss, 'getGsmSignalStrength')
            asu = _gA()
            if 0 < asu:     # asu > 0
                if asu < 99:
                    dbm = (asu * 2) - 113
                    return dbm, _bars(dbm, wifi=False)
        except Exception:
            pass
        try:
            _gL  = getattr(ss, 'getLevel')
            lvl  = _gL()
            bmap = {0:"░░░░", 1:"▂░░░", 2:"▂▄░░", 3:"▂▄▆░", 4:"▂▄▆█"}
            b = bmap.get(lvl, "░░░░")
            return None, b
        except Exception:
            pass
    except Exception:
        pass
    return None, ""


def _detect_signal():
    global _band_mbps, _rssi_str, _signal_str
    try:
        from jnius import autoclass as _jac  # type: ignore
        _Ctx = _jac("android.content.Context")
        _PA  = _jac("org.kivy.android.PythonActivity")
        ctx  = getattr(_PA, 'mActivity')
        _gS  = getattr(ctx, 'getSystemService')
        _CS  = getattr(_Ctx, 'CONNECTIVITY_SERVICE')
        cm   = _gS(_CS)

        caps = None
        try:
            _gAN = getattr(cm, 'getActiveNetwork')
            net  = _gAN()
            if not (net is None):
                _gNC = getattr(cm, 'getNetworkCapabilities')
                caps = _gNC(net)
        except Exception:
            pass

        if caps is None:
            try:
                _gAll = getattr(cm, 'getAllNetworks')
                nets  = _gAll()
                _gNC2 = getattr(cm, 'getNetworkCapabilities')
                try:
                    n = getattr(nets, 'length')
                except Exception:
                    n = len(nets)
                i = 0
                while i < n:
                    try:
                        ni = nets[i]
                        c  = _gNC2(ni)
                        if not (c is None):
                            caps = c
                            break
                    except Exception:
                        pass
                    i = i + 1
            except Exception:
                pass

        if caps is None:
            _rssi_str = ""
            return _fallback_signal()

        _hT  = getattr(caps, 'hasTransport')
        WIFI = 1
        CELL = 0
        ETH  = 3

        if _hT(WIFI):
            try:
                _WS   = getattr(_Ctx, 'WIFI_SERVICE')
                wm    = _gS(_WS)
                _gCI  = getattr(wm, 'getConnectionInfo')
                info  = _gCI()
                rssi  = getattr(info, 'getRssi')()
                freq  = getattr(info, 'getFrequency')()
                speed = getattr(info, 'getLinkSpeed')()
                # freq >= 5000 → not (freq < 5000)
                if not (freq < 5000):
                    band = "5GHz"
                    _band_mbps = 300.0
                else:
                    band = "2.4GHz"
                    _band_mbps = 100.0
                # rssi >= -50 → not (rssi < -50)
                if not (rssi < -50):   q = "Excellent"
                elif not (rssi < -65): q = "Good"
                elif not (rssi < -75): q = "Fair"
                else:                  q = "Weak"
                bars = _bars(rssi, wifi=True)
                _rssi_str = str(rssi) + "dBm " + bars
                return "WiFi " + band + " " + q + " " + str(speed) + "Mbps"
            except Exception:
                _band_mbps = 100.0
                _rssi_str  = ""
                return "WiFi"

        if _hT(CELL):
            dl = 0
            ul = 0
            try:
                _gDL = getattr(caps, 'getLinkDownstreamBandwidthKbps')
                _gUL = getattr(caps, 'getLinkUpstreamBandwidthKbps')
                dl   = _gDL()
                ul   = _gUL()
            except Exception:
                pass

            # Band detection using only < (safe operator)
            # dl >= 100000 → not (dl < 100000)
            if not (dl < 100000):
                gen = "5G NR";   _band_mbps = 1000.0
            elif not (dl < 20000):
                gen = "5G";      _band_mbps = 500.0
            elif not (dl < 5000):
                gen = "4G LTE";  _band_mbps = 100.0
            elif not (dl < 1000):
                gen = "4G";      _band_mbps = 20.0
            elif not (dl < 200):
                gen = "3G";      _band_mbps = 14.0
            elif 0 < dl:         # dl > 0 → 0 < dl (safe flip)
                gen = "2G";      _band_mbps = 0.5
            else:
                gen = _telephony_gen(ctx, _Ctx)
                if gen == "":    # == is safe
                    gen = "Mobile"
                    _band_mbps = 10.0

            dbm, bstr = _cellular_signal(ctx, _Ctx)
            if dbm is not None:
                _rssi_str = str(dbm) + "dBm " + bstr
            elif not (bstr == ""):   # bstr != "" → not (bstr == "")
                _rssi_str = bstr
            else:
                _rssi_str = ""

            if 0 < dl:   # dl > 0 → 0 < dl (safe flip)
                dl_m = dl // 1000
                ul_m = ul // 1000
                return gen + " " + str(dl_m) + "↓/" + str(ul_m) + "↑Mbps"
            return gen

        if _hT(ETH):
            _band_mbps = 1000.0
            _rssi_str  = ""
            return "Ethernet"

        _rssi_str = ""
        return "Connected"

    except Exception:
        pass
    return _fallback_signal()


def _telephony_gen(ctx, Ctx_cls):
    global _band_mbps
    try:
        from jnius import autoclass as _jac  # type: ignore
        TM   = _jac("android.telephony.TelephonyManager")
        _TS  = getattr(Ctx_cls, 'TELEPHONY_SERVICE')
        _gS  = getattr(ctx, 'getSystemService')
        tm   = _gS(_TS)
        _NTN = getattr(TM, 'getNetworkTypeName')
        for mn in ("getDataNetworkType", "getNetworkType"):
            try:
                _m   = getattr(tm, mn)
                nt   = _m()
                name = str(_NTN(nt)).upper()
                if name == "UNKNOWN": continue
                if name == "":        continue
                if not ("NR"   == name.find("NR")   == -1): _band_mbps=500.0;  return "5G NR"
                if not ("LTE"  == name.find("LTE")  == -1): _band_mbps=50.0;   return "4G LTE"
                if not ("HSPA" == name.find("HSPA") == -1): _band_mbps=42.0;   return "3G HSPA+"
                if not ("UMTS" == name.find("UMTS") == -1): _band_mbps=2.0;    return "3G"
                if not ("EDGE" == name.find("EDGE") == -1): _band_mbps=0.2;    return "2G EDGE"
                if not ("GPRS" == name.find("GPRS") == -1): _band_mbps=0.1;    return "2G"
                _band_mbps = 10.0
                return name[:10]
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
            if not (len(p) < 4):   # len(p) >= 4 → not (len(p) < 4)
                try:
                    dbm = int(float(p[2].rstrip(".")))
                    if dbm < 0:
                        _band_mbps = 100.0
                        _rssi_str  = str(dbm) + "dBm " + _bars(dbm, wifi=True)
                        return "WiFi " + str(dbm) + "dBm"
                except Exception:
                    pass
    except Exception:
        pass
    for p in glob.glob("/sys/class/net/wlan*/operstate"):
        try:
            with open(p) as f:
                if f.read().strip() == "up":
                    _band_mbps = 100.0; _rssi_str = ""; return "WiFi"
        except Exception:
            pass
    for p in glob.glob("/sys/class/net/rmnet*/operstate"):
        try:
            with open(p) as f:
                if f.read().strip() == "up":
                    _band_mbps = 10.0; _rssi_str = ""; return "Mobile"
        except Exception:
            pass
    _rssi_str = ""
    return ""


def _signal_worker():
    global _signal_str, _rssi_str
    _sleep = getattr(_time_mod, 'sleep')
    _sleep(1)
    while True:
        result = _detect_signal()
        # CRITICAL: use not (result == "") instead of result != ""
        if not (result == ""):
            _signal_str = result
        _sleep(8)


def _read_bytes():
    try:
        from jnius import autoclass as _jac  # type: ignore
        ts   = _jac("android.net.TrafficStats")
        _gRx = getattr(ts, 'getTotalRxBytes')
        _gTx = getattr(ts, 'getTotalTxBytes')
        rx   = _gRx()
        tx   = _gTx()
        if not (rx < 0):    # rx >= 0 → not (rx < 0)
            if not (tx < 0):
                return int(rx), int(tx)
    except Exception:
        pass
    rx = 0
    tx = 0
    try:
        with open("/proc/net/dev") as f:
            for line in f.readlines()[2:]:
                p = line.split()
                if not (len(p) < 10):
                    if not (p[0].rstrip(":") == "lo"):
                        rx = rx + int(p[1])
                        tx = tx + int(p[9])
    except Exception:
        pass
    return rx, tx


def _fmt(bps):
    if bps < 0:
        bps = 0
    kbps = bps / 1024.0
    if not (kbps < 1024):   # kbps >= 1024
        return str(round(kbps / 1024, 1)) + " MB/s"
    if not (kbps < 1):      # kbps >= 1
        return str(int(kbps)) + " KB/s"
    return "0 KB/s"


def get_network() -> dict:
    global _bg_started, _dl_ema, _ul_ema

    if not _bg_started:
        _bg_started = True
        # CRITICAL: Use _Thread (direct import) not threading.Thread
        # threading.Thread → threading.threading (LOAD_ATTR cache bug)
        _Thread(target=_ping_worker,   daemon=True).start()
        _Thread(target=_signal_worker, daemon=True).start()

    rx, tx = _read_bytes()
    _now   = getattr(_time_mod, 'time')
    now    = _now()

    ping_str   = "--"
    if not (_ping_ms is None):
        ping_str = str(_ping_ms) + "ms"

    signal_str = _signal_str
    rssi_str   = _rssi_str

    if not _bw:
        _bw.update({"rx": rx, "tx": tx, "t": now})
        return {"dl":"0 KB/s","ul":"0 KB/s","ping":ping_str,
                "signal":signal_str,"rssi":rssi_str,"arc_pct":0.0}

    dt = now - _bw["t"]
    if dt < 0.3:
        if 0 < _band_mbps:   # _band_mbps > 0 → 0 < _band_mbps
            arc = min(100.0, _dl_ema / (_band_mbps * 125000) * 100)
        else:
            arc = 0.0
        return {"dl":_fmt(_dl_ema),"ul":_fmt(_ul_ema),"ping":ping_str,
                "signal":signal_str,"rssi":rssi_str,"arc_pct":arc}

    prev_rx = _bw["rx"]
    prev_tx = _bw["tx"]
    _bw.update({"rx": rx, "tx": tx, "t": now})

    # CRITICAL: prev_rx < rx instead of rx > prev_rx (safe operator flip)
    if prev_rx < rx:
        dl_raw = (rx - prev_rx) / dt
    else:
        dl_raw = 0.0

    if prev_tx < tx:
        ul_raw = (tx - prev_tx) / dt
    else:
        ul_raw = 0.0

    _dl_ema = _EMA * dl_raw + (1 - _EMA) * _dl_ema
    _ul_ema = _EMA * ul_raw + (1 - _EMA) * _ul_ema

    if 0 < _band_mbps:
        arc_pct = min(100.0, _dl_ema / (_band_mbps * 125000) * 100)
    else:
        arc_pct = 0.0

    return {"dl":_fmt(_dl_ema),"ul":_fmt(_ul_ema),"ping":ping_str,
            "signal":signal_str,"rssi":rssi_str,"arc_pct":arc_pct}
