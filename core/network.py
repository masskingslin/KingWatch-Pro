"""
KingWatch Pro v17 - core/network.py

FINAL CONFIRMED BUGS from bytecode (APK10):

BUG 1: Thread.start() broken
  _Thread(...).start() → STORE_SUBSCR (assigns thread as dict key)
  The chained `.start()` call gets corrupted.
  FIX: Split into two statements:
    t = _Thread(target=fn, daemon=True)
    getattr(t, 'start')()

BUG 2: not (result == "") inverted to result < ""
  `not (result == "")` → COMPARE_OP `<` → always False for strings
  FIX: Use `if result:` — truthiness check, no comparison operator at all.

BUG 3: All `not (x == y)` patterns also compile wrong
  FIX: Use `if x:` / `if not x:` wherever possible.
"""
import time as _time_mod
import os
import glob
import re as _re_mod
from threading import Thread as _Thread

_ping_ms    = None
_signal_str = "Detecting..."
_rssi_str   = ""
_band_mbps  = 10.0
_bg_started = False
_bw         = {}
_EMA        = 0.4
_dl_ema     = 0.0
_ul_ema     = 0.0


def _bars(dbm, wifi=False):
    if wifi:
        if -50 < dbm: return "▂▄▆█"
        if -60 < dbm: return "▂▄▆░"
        if -70 < dbm: return "▂▄░░"
        if -80 < dbm: return "▂░░░"
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

    # Java InetAddress fallback
    try:
        from jnius import autoclass as _jac  # type: ignore
        _IA   = _jac("java.net.InetAddress")
        addr  = getattr(_IA, 'getByName')("8.8.8.8")
        t0    = _time()
        ok    = getattr(addr, 'isReachable')(3000)
        ms    = round((_time() - t0) * 1000, 1)
        if ok:
            if 0 < ms:
                return ms
    except Exception:
        pass

    # TCP socket fallback
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
                if 0 < ms:
                    return ms
            except Exception:
                continue
    except Exception:
        pass
    return None


def _ping_worker():
    global _ping_ms
    _sleep = getattr(_time_mod, 'sleep')
    _sleep(2)
    while True:
        ms = _do_ping()
        _ping_ms = ms
        _sleep(5)


def _cellular_signal(ctx, Ctx_cls):
    try:
        _TS   = getattr(Ctx_cls, 'TELEPHONY_SERVICE')
        tm    = getattr(ctx, 'getSystemService')(_TS)
        ss    = getattr(tm, 'getSignalStrength')()
        if ss is None:
            return None, ""
        try:
            cells = getattr(ss, 'getCellSignalStrengths')()
            n     = getattr(cells, 'size')()
            best  = None
            i     = 0
            while i < n:
                try:
                    dbm = getattr(getattr(cells, 'get')(i), 'getDbm')()
                    if -200 < dbm:
                        if dbm < 0:
                            if best is None:
                                best = dbm
                            elif best < dbm:
                                best = dbm
                except Exception:
                    pass
                i = i + 1
            if best is not None:
                return best, _bars(best, wifi=False)
        except Exception:
            pass
        try:
            asu = getattr(ss, 'getGsmSignalStrength')()
            if 0 < asu:
                if asu < 99:
                    dbm = (asu * 2) - 113
                    return dbm, _bars(dbm, wifi=False)
        except Exception:
            pass
        try:
            lvl  = getattr(ss, 'getLevel')()
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
        from jnius import autoclass as _jac  # type: ignore
        _Ctx = _jac("android.content.Context")
        _PA  = _jac("org.kivy.android.PythonActivity")
        ctx  = getattr(_PA, 'mActivity')
        _gS  = getattr(ctx, 'getSystemService')
        cm   = _gS(getattr(_Ctx, 'CONNECTIVITY_SERVICE'))

        caps = None
        try:
            net = getattr(cm, 'getActiveNetwork')()
            if net is not None:
                caps = getattr(cm, 'getNetworkCapabilities')(net)
        except Exception:
            pass

        if caps is None:
            try:
                nets  = getattr(cm, 'getAllNetworks')()
                _gNC2 = getattr(cm, 'getNetworkCapabilities')
                try:
                    n = getattr(nets, 'length')
                except Exception:
                    n = len(nets)
                i = 0
                while i < n:
                    try:
                        c = _gNC2(nets[i])
                        if c is not None:
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

        # WiFi = 1
        if _hT(1):
            try:
                wm    = _gS(getattr(_Ctx, 'WIFI_SERVICE'))
                info  = getattr(wm, 'getConnectionInfo')()
                rssi  = getattr(info, 'getRssi')()
                freq  = getattr(info, 'getFrequency')()
                speed = getattr(info, 'getLinkSpeed')()
                if 5000 < freq:
                    band = "5GHz"
                    _band_mbps = 300.0
                else:
                    band = "2.4GHz"
                    _band_mbps = 100.0
                if rssi < -75:    q = "Weak"
                elif rssi < -65:  q = "Fair"
                elif rssi < -50:  q = "Good"
                else:             q = "Excellent"
                _rssi_str = str(rssi) + "dBm " + _bars(rssi, wifi=True)
                return "WiFi " + band + " " + q + " " + str(speed) + "Mbps"
            except Exception:
                _band_mbps = 100.0
                _rssi_str  = ""
                return "WiFi"

        # Cellular = 0
        if _hT(0):
            dl = 0
            ul = 0
            try:
                dl = getattr(caps, 'getLinkDownstreamBandwidthKbps')()
                ul = getattr(caps, 'getLinkUpstreamBandwidthKbps')()
            except Exception:
                pass

            if 100000 < dl:      gen = "5G NR";  _band_mbps = 1000.0
            elif 20000 < dl:     gen = "5G";     _band_mbps = 500.0
            elif 5000 < dl:      gen = "4G LTE"; _band_mbps = 100.0
            elif 1000 < dl:      gen = "4G";     _band_mbps = 20.0
            elif 200 < dl:       gen = "3G";     _band_mbps = 14.0
            elif 0 < dl:         gen = "2G";     _band_mbps = 0.5
            else:
                gen = _telephony_gen(ctx, _Ctx)
                if not gen:
                    gen = "Mobile"
                    _band_mbps = 10.0

            dbm, bstr = _cellular_signal(ctx, _Ctx)
            if dbm is not None:
                _rssi_str = str(dbm) + "dBm " + bstr
            elif bstr:
                _rssi_str = bstr
            else:
                _rssi_str = ""

            if 0 < dl:
                return gen + " " + str(dl // 1000) + "↓/" + str(ul // 1000) + "↑Mbps"
            return gen

        # Ethernet = 3
        if _hT(3):
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
        tm   = getattr(ctx, 'getSystemService')(getattr(Ctx_cls, 'TELEPHONY_SERVICE'))
        _NTN = getattr(TM, 'getNetworkTypeName')
        for mn in ("getDataNetworkType", "getNetworkType"):
            try:
                nt   = getattr(tm, mn)()
                name = str(_NTN(nt)).upper()
                if name == "UNKNOWN": continue
                if not name:          continue
                if "NR"   in name: _band_mbps=500.0;  return "5G NR"
                if "LTE"  in name: _band_mbps=50.0;   return "4G LTE"
                if "HSPA" in name: _band_mbps=42.0;   return "3G HSPA+"
                if "UMTS" in name: _band_mbps=2.0;    return "3G"
                if "EDGE" in name: _band_mbps=0.2;    return "2G EDGE"
                if "GPRS" in name: _band_mbps=0.1;    return "2G"
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
            if len(p) < 4:
                continue
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
                    _band_mbps = 100.0
                    _rssi_str  = ""
                    return "WiFi"
        except Exception:
            pass
    for p in glob.glob("/sys/class/net/rmnet*/operstate"):
        try:
            with open(p) as f:
                if f.read().strip() == "up":
                    _band_mbps = 10.0
                    _rssi_str  = ""
                    return "Mobile"
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
        # CRITICAL: use `if result:` — truthiness, no comparison operator
        if result:
            _signal_str = result
        _sleep(8)


def _read_bytes():
    try:
        from jnius import autoclass as _jac  # type: ignore
        ts = _jac("android.net.TrafficStats")
        rx = getattr(ts, 'getTotalRxBytes')()
        tx = getattr(ts, 'getTotalTxBytes')()
        if not (rx < 0):
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
                if len(p) < 10:
                    continue
                if p[0].rstrip(":") == "lo":
                    continue
                rx = rx + int(p[1])
                tx = tx + int(p[9])
    except Exception:
        pass
    return rx, tx


def _fmt(bps):
    if bps < 0:
        bps = 0
    kbps = bps / 1024.0
    if not (kbps < 1024):
        return str(round(kbps / 1024, 1)) + " MB/s"
    if not (kbps < 1):
        return str(int(kbps)) + " KB/s"
    return "0 KB/s"


def get_network() -> dict:
    global _bg_started, _dl_ema, _ul_ema

    if not _bg_started:
        _bg_started = True
        # CRITICAL: Split Thread creation and .start() — chained call breaks
        _t1 = _Thread(target=_ping_worker,   daemon=True)
        getattr(_t1, 'start')()
        _t2 = _Thread(target=_signal_worker, daemon=True)
        getattr(_t2, 'start')()

    rx, tx = _read_bytes()
    now    = getattr(_time_mod, 'time')()

    ping_str = "--"
    if _ping_ms is not None:
        ping_str = str(_ping_ms) + "ms"

    signal_str = _signal_str
    rssi_str   = _rssi_str

    if not _bw:
        _bw.update({"rx": rx, "tx": tx, "t": now})
        return {"dl":"0 KB/s","ul":"0 KB/s","ping":ping_str,
                "signal":signal_str,"rssi":rssi_str,"arc_pct":0.0}

    dt = now - _bw["t"]
    if dt < 0.3:
        if 0 < _band_mbps:
            arc = min(100.0, _dl_ema / (_band_mbps * 125000) * 100)
        else:
            arc = 0.0
        return {"dl":_fmt(_dl_ema),"ul":_fmt(_ul_ema),"ping":ping_str,
                "signal":signal_str,"rssi":rssi_str,"arc_pct":arc}

    prev_rx = _bw["rx"]
    prev_tx = _bw["tx"]
    _bw.update({"rx": rx, "tx": tx, "t": now})

    # SAFE: use prev < curr (only < operator)
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