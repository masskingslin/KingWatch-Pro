"""
KingWatch Pro v17 - core/network.py
Universal Android network engine.

ALL Python 3.11 bytecode bugs fixed:

BUG 1: Thread(...).start() → STORE_SUBSCR (threads never start)
  FIX: t = Thread(...); getattr(t,'start')()

BUG 2: _time.sleep(5) → LOAD_ATTR '_signal' (sleep never called, loop runs at 100% CPU)
  FIX: assign sleep = _time.sleep BEFORE the loop, call sleep(5)

BUG 3: res == 0 → COMPARE_OP '<' (ping always fails - returns None even when connected)
  FIX: use `if not res:` (truthiness, no COMPARE_OP)

BUG 4: socket.socket() → STORE_SUBSCR (socket never created)
  FIX: import socket, get socket class via getattr

BUG 5: rx > prx → COMPARE_OP '<' inverted (download always 0)
  FIX: use `if prx < rx:` (only < operator)
"""
import time as _time
import glob
from threading import Thread as _Thread

_ping    = None
_signal  = "Detecting..."
_rssi    = ""
_band    = 10.0
_started = False
_bw      = {}
_dl      = 0.0
_ul      = 0.0
_EMA     = 0.4


# ── Ping ──────────────────────────────────────────────────────────────────
def _ping_test():
    # Import socket and get class via getattr to avoid STORE_SUBSCR bug
    _sk         = __import__('socket')
    _SocketCls  = getattr(_sk, 'socket')
    _AF_INET    = getattr(_sk, 'AF_INET')
    _SOCK_STREAM= getattr(_sk, 'SOCK_STREAM')
    _now        = getattr(_time, 'time')

    for host, port in [("8.8.8.8", 53), ("1.1.1.1", 443)]:
        try:
            s   = _SocketCls(_AF_INET, _SOCK_STREAM)
            _st = getattr(s, 'settimeout')
            _cx = getattr(s, 'connect_ex')
            _cl = getattr(s, 'close')
            _st(2)
            t0  = _now()
            res = _cx((host, port))
            dt  = (_now() - t0) * 1000
            _cl()
            # BUG 3 FIX: `res == 0` compiles as `res < 0` — use `not res` instead
            if not res:
                return round(dt, 1)
        except Exception:
            pass
    return None


def _ping_loop():
    global _ping
    # Assign sleep BEFORE loop — avoids LOAD_ATTR cache corruption inside loop
    _sleep = getattr(_time, 'sleep')
    while True:
        _ping = _ping_test()
        _sleep(5)


# ── Signal / Band detection ───────────────────────────────────────────────
def _get_mobile_gen(ctx, Ctx):
    global _band
    try:
        from jnius import autoclass  # type: ignore
        TM  = autoclass("android.telephony.TelephonyManager")
        tm  = getattr(ctx, 'getSystemService')(getattr(Ctx, 'TELEPHONY_SERVICE'))
        _gDN = getattr(tm, 'getDataNetworkType')
        nt  = _gDN()
        if nt == 20: _band = 500.0;  return "5G NR"
        if nt == 13: _band = 50.0;   return "4G LTE"
        if nt == 19: _band = 150.0;  return "4G LTE-CA"
        if nt == 15: _band = 42.0;   return "4G HSPA+"
        if nt in (8, 9, 10, 3, 5, 6, 12, 14):
            _band = 14.0; return "3G"
        if nt in (1, 2, 4, 7, 11, 16):
            _band = 0.2;  return "2G"
        _band = 10.0
        return "Mobile"
    except Exception:
        pass
    _band = 10.0
    return "Mobile"


def _wifi_info(ctx, Ctx):
    global _band
    try:
        wm   = getattr(ctx, 'getSystemService')(getattr(Ctx, 'WIFI_SERVICE'))
        info = getattr(wm, 'getConnectionInfo')()
        rssi = getattr(info, 'getRssi')()
        freq = getattr(info, 'getFrequency')()
        spd  = getattr(info, 'getLinkSpeed')()
        if 5000 < freq:
            _band = 300.0
            band  = "5GHz"
        else:
            _band = 100.0
            band  = "2.4GHz"
        if rssi < -75:   q = "Weak"
        elif rssi < -65: q = "Fair"
        elif rssi < -50: q = "Good"
        else:            q = "Excellent"
        bars = ("▂▄▆█" if -50 < rssi else
                "▂▄▆░" if -60 < rssi else
                "▂▄░░" if -70 < rssi else
                "▂░░░" if -80 < rssi else "░░░░")
        return str(rssi)+"dBm "+bars, "WiFi "+band+" "+q+" "+str(spd)+"Mbps"
    except Exception:
        pass
    _band = 100.0
    return "", "WiFi"


def _fallback():
    global _band
    for p in glob.glob("/sys/class/net/wlan*/operstate"):
        try:
            with open(p) as f:
                if f.read().strip() == "up":
                    _band = 100.0
                    return "WiFi"
        except Exception:
            pass
    for p in glob.glob("/sys/class/net/rmnet*/operstate"):
        try:
            with open(p) as f:
                if f.read().strip() == "up":
                    _band = 10.0
                    return "Mobile"
        except Exception:
            pass
    try:
        with open("/proc/net/wireless") as f:
            for line in f.readlines()[2:]:
                p = line.split()
                if len(p) < 4:
                    continue
                try:
                    dbm = int(float(p[2].rstrip(".")))
                    if dbm < 0:
                        _band = 100.0
                        return "WiFi "+str(dbm)+"dBm"
                except Exception:
                    pass
    except Exception:
        pass
    return ""


def _detect():
    global _rssi
    try:
        from jnius import autoclass  # type: ignore
        Ctx = autoclass("android.content.Context")
        PA  = autoclass("org.kivy.android.PythonActivity")
        ctx = getattr(PA, 'mActivity')
        cm  = getattr(ctx, 'getSystemService')(getattr(Ctx, 'CONNECTIVITY_SERVICE'))
        net = getattr(cm, 'getActiveNetwork')()
        if net is None:
            _rssi = ""
            return _fallback()
        caps = getattr(cm, 'getNetworkCapabilities')(net)
        if caps is None:
            _rssi = ""
            return _fallback()
        _hT = getattr(caps, 'hasTransport')
        if _hT(1):   # WiFi
            rssi_str, label = _wifi_info(ctx, Ctx)
            _rssi = rssi_str
            return label
        if _hT(0):   # Cellular
            _rssi = ""
            return _get_mobile_gen(ctx, Ctx)
        if _hT(3):   # Ethernet
            global _band
            _band = 1000.0
            _rssi = ""
            return "Ethernet"
        _rssi = ""
        return "Connected"
    except Exception:
        pass
    _rssi = ""
    return _fallback()


def _signal_loop():
    global _signal
    # BUG 2 FIX: assign sleep before loop
    _sleep = getattr(_time, 'sleep')
    while True:
        s = _detect()
        # Use `if s:` — truthiness, no comparison operator
        if s:
            _signal = s
        _sleep(5)


# ── Traffic bytes ─────────────────────────────────────────────────────────
def _bytes():
    # Try TrafficStats first (most reliable)
    try:
        from jnius import autoclass  # type: ignore
        ts = autoclass("android.net.TrafficStats")
        rx = getattr(ts, 'getTotalRxBytes')()
        tx = getattr(ts, 'getTotalTxBytes')()
        if not (rx < 0):
            if not (tx < 0):
                return int(rx), int(tx)
    except Exception:
        pass
    # /proc/net/dev fallback
    rx = 0
    tx = 0
    try:
        with open("/proc/net/dev") as f:
            for line in f.readlines()[2:]:
                p = line.split()
                if len(p) < 10:
                    continue
                if p[0].startswith("lo"):
                    continue
                rx = rx + int(p[1])
                tx = tx + int(p[9])
    except Exception:
        pass
    return rx, tx


def _fmt(b):
    kb = b / 1024
    if not (kb < 1024):
        return str(round(kb / 1024, 1)) + " MB/s"
    if not (kb < 1):
        return str(int(kb)) + " KB/s"
    return "0 KB/s"


# ── Public API ────────────────────────────────────────────────────────────
def get_network() -> dict:
    global _started, _dl, _ul

    if not _started:
        _started = True
        # BUG 1 FIX: split Thread creation and .start() call
        _t1 = _Thread(target=_ping_loop,   daemon=True)
        getattr(_t1, 'start')()
        _t2 = _Thread(target=_signal_loop, daemon=True)
        getattr(_t2, 'start')()

    rx, tx = _bytes()
    now    = getattr(_time, 'time')()

    if _ping is None:
        ping = "--"
    else:
        ping = str(_ping) + "ms"

    sig  = _signal
    rssi = _rssi

    if not _bw:
        _bw.update({"rx": rx, "tx": tx, "t": now})
        return {"dl":"0 KB/s","ul":"0 KB/s","ping":ping,
                "signal":sig,"rssi":rssi,"arc_pct":0.0}

    dt = now - _bw["t"]
    if dt < 0.3:
        if 0 < _band:
            arc = min(100.0, _dl / (_band * 125000))
        else:
            arc = 0.0
        return {"dl":_fmt(_dl),"ul":_fmt(_ul),"ping":ping,
                "signal":sig,"rssi":rssi,"arc_pct":arc}

    prx = _bw["rx"]
    ptx = _bw["tx"]
    _bw.update({"rx": rx, "tx": tx, "t": now})

    # BUG 5 FIX: use `prx < rx` not `rx > prx`
    if prx < rx:
        dl_raw = (rx - prx) / dt
    else:
        dl_raw = 0.0

    if ptx < tx:
        ul_raw = (tx - ptx) / dt
    else:
        ul_raw = 0.0

    _dl = _EMA * dl_raw + (1 - _EMA) * _dl
    _ul = _EMA * ul_raw + (1 - _EMA) * _ul

    if 0 < _band:
        arc = min(100.0, _dl / (_band * 125000))
    else:
        arc = 0.0

    return {"dl":_fmt(_dl),"ul":_fmt(_ul),"ping":ping,
            "signal":sig,"rssi":rssi,"arc_pct":arc}
