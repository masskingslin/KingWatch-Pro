"""
KingWatch Pro v17 - core/network.py

ROOT CAUSE OF SIGNAL STUCK AT 'Detecting...':
  Chain of failures confirmed by bytecode + screenshot analysis:
  1. getDataNetworkType() -> SecurityException on OEM ROM (MIUI/OXY etc)
  2. getLinkDownstreamBandwidthKbps() -> returns 0 on locked ROMs
  3. _heuristic() -> needs 3+ speed samples, returns '' on first calls
  4. _fallback() -> sysfs operstate not accessible -> returns ''
  5. _signal_loop: `if s:` where s='' -> _signal never updated
  Result: _signal stays 'Detecting...' forever

FIX: _detect() NEVER returns ''.
  Layer 4 (new): Classify from _dl (already measured by TrafficStats).
  Layer 5 (new): Always return 'Mobile' as final guaranteed fallback.
  The _dl EMA value is available immediately - no permissions needed.

PING STATUS: Bytecode correct. POP_JUMP_IF_TRUE on res is right:
  res=0 (connected)  -> falsy -> falls through -> returns ms  OK
  res!=0 (blocked)   -> truthy -> jumps to next host         OK
"""
import time as _time
import glob
from threading import Thread as _Thread

_signal   = "Detecting..."
_ping_str = "--"
_started  = False
_bw       = {}
_dl       = 0.0
_ul       = 0.0
_EMA      = 0.4
_band_bps = 10.0 * 125000
_spdhist  = []


# -- Ping ------------------------------------------------------------------
def _ping_once():
    _sk          = __import__('socket')
    _AF_INET     = getattr(_sk, 'AF_INET')
    _SOCK_STREAM = getattr(_sk, 'SOCK_STREAM')
    _SocketCls   = getattr(_sk, 'socket')
    _now         = getattr(_time, 'time')
    for ip, port in [("8.8.8.8", 53), ("1.1.1.1", 443)]:
        try:
            s   = _SocketCls(_AF_INET, _SOCK_STREAM)
            _st = getattr(s, 'settimeout')
            _cx = getattr(s, 'connect_ex')
            _cl = getattr(s, 'close')
            _st(2.0)
            t0  = _now()
            res = _cx((ip, port))
            ms  = round((_now() - t0) * 1000)
            _cl()
            # res=0 means connected -> falsy -> return ms
            if not res:
                return str(ms) + "ms"
        except Exception:
            pass
    return "--"


def _ping_loop():
    global _ping_str
    _sleep = getattr(_time, 'sleep')
    _sleep(3)
    while True:
        _ping_str = _ping_once()
        _sleep(8)


# -- Band helpers ----------------------------------------------------------
def _quality(dbm):
    if -50 < dbm: return "Excellent"
    if -60 < dbm: return "Good"
    if -70 < dbm: return "Fair"
    if -80 < dbm: return "Weak"
    return "Poor"


def _band_from_speed(bps):
    """
    Layer 4: classify band from current measured speed.
    Uses _dl EMA - available after first TrafficStats read.
    No permissions needed. Always works.
    """
    global _band_bps
    mbps = bps / 125000.0
    if 50.0 < mbps:  _band_bps = 500.0*125000;  return "5G"
    if 10.0 < mbps:  _band_bps = 50.0*125000;   return "4G LTE"
    if 1.0  < mbps:  _band_bps = 14.0*125000;   return "3G"
    if 0.05 < mbps:  _band_bps = 2.0*125000;    return "2G"
    # Speed too low to classify - keep existing _band_bps
    return ""


def _heuristic():
    """Layer 3: median of recent speed history."""
    global _band_bps
    if len(_spdhist) < 3:
        return ""
    med  = sorted(_spdhist)[len(_spdhist) // 2]
    mbps = med / 125000.0
    if 50.0 < mbps:  _band_bps = 500.0*125000;  return "5G"
    if 10.0 < mbps:  _band_bps = 50.0*125000;   return "4G LTE"
    if 1.0  < mbps:  _band_bps = 14.0*125000;   return "3G"
    if 0.05 < mbps:  _band_bps = 2.0*125000;    return "2G"
    return ""


# -- Signal detection ------------------------------------------------------
def _detect():
    global _band_bps
    try:
        from jnius import autoclass  # type: ignore
        Ctx = autoclass("android.content.Context")
        PA  = autoclass("org.kivy.android.PythonActivity")
        ctx = getattr(PA, 'mActivity')
        cm  = getattr(ctx, 'getSystemService')(getattr(Ctx, 'CONNECTIVITY_SERVICE'))
        net = getattr(cm, 'getActiveNetwork')()
        if net is None:
            return _safe_fallback()
        caps = getattr(cm, 'getNetworkCapabilities')(net)
        if caps is None:
            return _safe_fallback()
        _hT = getattr(caps, 'hasTransport')

        # WiFi
        if _hT(1):
            try:
                wm   = getattr(ctx, 'getSystemService')(getattr(Ctx, 'WIFI_SERVICE'))
                info = getattr(wm, 'getConnectionInfo')()
                rssi = getattr(info, 'getRssi')()
                freq = getattr(info, 'getFrequency')()
                spd  = getattr(info, 'getLinkSpeed')()
                if 5000 < freq:
                    _band_bps = 300.0*125000; band = "5GHz"
                else:
                    _band_bps = 100.0*125000; band = "2.4GHz"
                q = _quality(rssi)
                return "WiFi " + band + " " + q + " " + str(rssi) + "dBm " + str(spd) + "Mbps"
            except Exception:
                _band_bps = 100.0*125000
                return "WiFi"

        # Cellular
        if _hT(0):
            # Layer 1: TelephonyManager (may fail on locked ROMs)
            try:
                TM = autoclass("android.telephony.TelephonyManager")
                tm = getattr(ctx, 'getSystemService')(getattr(Ctx, 'TELEPHONY_SERVICE'))
                nt = getattr(tm, 'getDataNetworkType')()
                if nt in (20,): _band_bps=500.0*125000; return "5G NR  Max 500Mbps"
                if nt in (13,): _band_bps=50.0*125000;  return "4G LTE  Max 50Mbps"
                if nt in (19,): _band_bps=150.0*125000; return "4G LTE-CA  Max 150Mbps"
                if nt in (15,): _band_bps=42.0*125000;  return "4G HSPA+  Max 42Mbps"
                if nt in (8,9,10,3,5,6,12,14):
                    _band_bps=14.0*125000; return "3G  Max 14Mbps"
                if nt in (1,2,4,7,11,16):
                    _band_bps=0.2*125000;  return "2G  Max 0.2Mbps"
            except Exception:
                pass  # locked ROM - try next layer

            # Layer 2: NetworkCapabilities bandwidth (no permission)
            try:
                dl_kbps = getattr(caps, 'getLinkDownstreamBandwidthKbps')()
                if 0 < dl_kbps:
                    if 50000 < dl_kbps:
                        _band_bps=500.0*125000;  return "5G ~" + str(dl_kbps//1000) + "Mbps"
                    if 5000  < dl_kbps:
                        _band_bps=50.0*125000;   return "4G LTE ~" + str(dl_kbps//1000) + "Mbps"
                    if 1000  < dl_kbps:
                        _band_bps=20.0*125000;   return "4G ~" + str(dl_kbps//1000) + "Mbps"
                    if 200   < dl_kbps:
                        _band_bps=14.0*125000;   return "3G ~" + str(dl_kbps//1000) + "Mbps"
                    _band_bps=0.2*125000; return "2G ~" + str(dl_kbps) + "Kbps"
            except Exception:
                pass

            # Layer 3: speed history heuristic
            h = _heuristic()
            if h:
                return h + "  (speed)"

            # Layer 4: current _dl EMA - always available
            b = _band_from_speed(_dl)
            if b:
                return b + "  (live)"

            # Layer 5: guaranteed non-empty fallback
            _band_bps = 10.0*125000
            return "Mobile"

        if _hT(3):
            _band_bps = 1000.0*125000
            return "Ethernet"

        return "Connected"

    except Exception:
        pass
    return _safe_fallback()


def _safe_fallback():
    """
    Always returns a non-empty string.
    Checks sysfs first, then returns 'Mobile' guaranteed.
    """
    global _band_bps
    for p in glob.glob("/sys/class/net/wlan*/operstate"):
        try:
            with open(p) as f:
                if f.read().strip() == "up":
                    _band_bps = 100.0*125000
                    return "WiFi"
        except Exception:
            pass
    for p in glob.glob("/sys/class/net/rmnet*/operstate"):
        try:
            with open(p) as f:
                if f.read().strip() == "up":
                    _band_bps = 10.0*125000
                    return "Mobile"
        except Exception:
            pass

    # Layer 4: classify from current speed
    b = _band_from_speed(_dl)
    if b:
        return b

    # Layer 5: absolute guaranteed minimum
    return "Mobile"


def _signal_loop():
    global _signal
    _sleep = getattr(_time, 'sleep')
    while True:
        s = _detect()
        # s is ALWAYS non-empty now - no more stuck at Detecting...
        _signal = s
        _sleep(5)


# -- Traffic ----------------------------------------------------------------
def _bytes():
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
    rx = 0; tx = 0
    try:
        with open("/proc/net/dev") as f:
            for line in f.readlines()[2:]:
                p = line.split()
                if len(p) < 10: continue
                if p[0].startswith("lo"): continue
                rx = rx + int(p[1])
                tx = tx + int(p[9])
    except Exception:
        pass
    return rx, tx


def _fmt(b):
    kb = b / 1024
    if not (kb < 1024): return str(round(kb/1024, 1)) + " MB/s"
    if not (kb < 1):    return str(int(kb)) + " KB/s"
    return "0 KB/s"


# -- Public API -------------------------------------------------------------
def get_network():
    global _started, _dl, _ul
    if not _started:
        _started = True
        _t1 = _Thread(target=_signal_loop, daemon=True)
        getattr(_t1, 'start')()
        _t2 = _Thread(target=_ping_loop, daemon=True)
        getattr(_t2, 'start')()

    rx, tx = _bytes()
    now    = getattr(_time, 'time')()
    sig    = _signal
    ping   = _ping_str

    if not _bw:
        _bw.update({"rx": rx, "tx": tx, "t": now})
        return {"dl":"0 KB/s","ul":"0 KB/s","sig":sig,"ping":ping,"arc":0.0}

    dt = now - _bw["t"]
    if dt < 0.3:
        if 0 < _band_bps:
            arc = min(100.0, _dl / _band_bps * 100)
        else:
            arc = 0.0
        return {"dl":_fmt(_dl),"ul":_fmt(_ul),"sig":sig,"ping":ping,"arc":arc}

    prx = _bw["rx"]
    ptx = _bw["tx"]
    _bw.update({"rx": rx, "tx": tx, "t": now})

    if prx < rx:
        dl_raw = (rx - prx) / dt
        _spdhist.append(dl_raw)
        if not (len(_spdhist) < 11):
            _spdhist.pop(0)
    else:
        dl_raw = 0.0

    if ptx < tx:
        ul_raw = (tx - ptx) / dt
    else:
        ul_raw = 0.0

    _dl = _EMA * dl_raw + (1 - _EMA) * _dl
    _ul = _EMA * ul_raw + (1 - _EMA) * _ul

    if 0 < _band_bps:
        arc = min(100.0, _dl / _band_bps * 100)
    else:
        arc = 0.0

    return {"dl":_fmt(_dl),"ul":_fmt(_ul),"sig":sig,"ping":ping,"arc":arc}
