"""
KingWatch Pro v17 - core/network.py
Stabilization Patch - Production Fix

FIXES APPLIED:
1. ICMP ping via /system/bin/ping as primary (bypasses VPN routing)
2. TCP connect() fallback (not connect_ex - avoids EINPROGRESS/115 bug)
3. Signal heuristic works with 1+ speed samples (not 3+)
4. Thread race fixed - init flag set AFTER threads started
5. Safe subprocess decode for Android 13+ (errors='replace')
6. Socket close in finally block - prevents resource leak crash
7. _signal always assigned - no 'if s:' gate that caused Detecting...
8. Ping and signal on separate threads - ping never blocks bandwidth
"""
import time as _time
import glob
import re as _re
from threading import Thread as _Thread

_signal   = "Detecting..."
_ping_str = "--"
_started  = False
_init_lock = [False]
_bw       = {}
_dl       = 0.0
_ul       = 0.0
_EMA      = 0.4
_band_bps = 10.0 * 125000
_spdhist  = []


def _ping_icmp():
    """
    Primary: /system/bin/ping (ICMP).
    ICMP bypasses Android VPN routing on most devices.
    All attrs via getattr - avoids Python 3.11 LOAD_ATTR cache bug.
    decode(errors='replace') - safe for Android 13+ non-UTF output.
    """
    _sp   = __import__('subprocess')
    _run  = getattr(_sp, 'run')
    _PIPE = getattr(_sp, 'PIPE')
    _sch  = getattr(_re, 'search')
    _now  = getattr(_time, 'time')
    for host in ("8.8.8.8", "1.1.1.1"):
        try:
            t0  = _now()
            ret = _run(
                ["/system/bin/ping", "-c", "1", "-W", "2", host],
                stdout=_PIPE, stderr=_PIPE, timeout=4
            )
            rc  = getattr(ret, 'returncode')
            ms  = round((_now() - t0) * 1000)
            if not rc:
                out = getattr(ret, 'stdout')
                txt = getattr(out, 'decode')(errors='replace')
                m   = _sch(r"time=([\d.]+)\s*ms", txt)
                if m is not None:
                    _grp = getattr(m, 'group')
                    ms   = round(float(_grp(1)))
                if 0 < ms:
                    return str(ms) + "ms"
        except Exception:
            pass
    return None


def _ping_tcp():
    """
    Fallback: TCP connect() - blocks properly unlike connect_ex().
    connect_ex() returns EINPROGRESS(115) immediately on non-blocking
    socket, making every attempt look like a failure.
    Socket closed in finally block to prevent resource leak.
    """
    _sk   = __import__('socket')
    _AF   = getattr(_sk, 'AF_INET')
    _ST   = getattr(_sk, 'SOCK_STREAM')
    _SC   = getattr(_sk, 'socket')
    _now  = getattr(_time, 'time')
    for ip, port in [("8.8.8.8", 53), ("1.1.1.1", 443), ("8.8.4.4", 53)]:
        s = None
        try:
            s    = _SC(_AF, _ST)
            _st  = getattr(s, 'settimeout')
            _cn  = getattr(s, 'connect')
            _cl  = getattr(s, 'close')
            _st(1.5)
            t0   = _now()
            _cn((ip, port))
            ms   = round((_now() - t0) * 1000)
            if 0 < ms:
                return str(ms) + "ms"
        except Exception:
            pass
        finally:
            if s is not None:
                try:
                    getattr(s, 'close')()
                except Exception:
                    pass
    return None


def _ping_once():
    r = _ping_icmp()
    if r is not None:
        return r
    r = _ping_tcp()
    if r is not None:
        return r
    return "--"


def _ping_loop():
    global _ping_str
    _sleep = getattr(_time, 'sleep')
    _sleep(2)
    while True:
        _ping_str = _ping_once()
        _sleep(8)


def _quality(dbm):
    if -50 < dbm: return "Excellent"
    if -60 < dbm: return "Good"
    if -70 < dbm: return "Fair"
    if -80 < dbm: return "Weak"
    return "Poor"


def _fmt_speed(bps):
    kb = bps / 1024
    if not (kb < 1024): return str(round(kb / 1024, 1)) + " MB/s"
    if not (kb < 1):    return str(int(kb)) + " KB/s"
    return "0 KB/s"


def _band_from_speed(dl_bps):
    """Classify band from live speed. Returns label + actual rate."""
    global _band_bps
    spd  = _fmt_speed(dl_bps)
    mbps = dl_bps / 125000.0
    if 50.0 < mbps:  _band_bps = 500.0*125000; return "5G  " + spd
    if 10.0 < mbps:  _band_bps = 50.0*125000;  return "4G LTE  " + spd
    if 1.0  < mbps:  _band_bps = 14.0*125000;  return "3G  " + spd
    if 0.05 < mbps:  _band_bps = 2.0*125000;   return "2G  " + spd
    return ""


def _heuristic():
    """Works from 1 sample. Median of recent speed history."""
    global _band_bps
    if len(_spdhist) < 1:
        return ""
    med  = sorted(_spdhist)[len(_spdhist) // 2]
    mbps = med / 125000.0
    if 50.0 < mbps:  _band_bps = 500.0*125000; return "5G"
    if 10.0 < mbps:  _band_bps = 50.0*125000;  return "4G LTE"
    if 1.0  < mbps:  _band_bps = 14.0*125000;  return "3G"
    if 0.05 < mbps:  _band_bps = 2.0*125000;   return "2G"
    return ""


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

        # Cellular - 4 layers
        if _hT(0):
            # L1: TelephonyManager (may need READ_PHONE_STATE on some ROMs)
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
                pass

            # L2: NetworkCapabilities bandwidth (no permission needed)
            try:
                dl_k = getattr(caps, 'getLinkDownstreamBandwidthKbps')()
                if 0 < dl_k:
                    if 50000 < dl_k: _band_bps=500.0*125000; return "5G ~" + str(dl_k//1000) + "Mbps"
                    if 5000  < dl_k: _band_bps=50.0*125000;  return "4G LTE ~" + str(dl_k//1000) + "Mbps"
                    if 1000  < dl_k: _band_bps=20.0*125000;  return "4G ~" + str(dl_k//1000) + "Mbps"
                    if 200   < dl_k: _band_bps=14.0*125000;  return "3G ~" + str(dl_k//1000) + "Mbps"
                    _band_bps = 0.2*125000; return "2G ~" + str(dl_k) + "Kbps"
            except Exception:
                pass

            # L3: speed history heuristic (1+ samples)
            h = _heuristic()
            if h:
                return h

            # L4: live _dl EMA - always available after first read
            b = _band_from_speed(_dl)
            if b:
                return b

            # L5: absolute guaranteed fallback
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
    """Always returns non-empty string. Last resort before 'Mobile'."""
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
    b = _band_from_speed(_dl)
    if b:
        return b
    return "Mobile"


def _signal_loop():
    """
    Runs on separate thread. Polls every 10s (reduced battery usage).
    First detection after 1s to populate signal quickly.
    _signal always assigned - no conditional guard.
    """
    global _signal
    _sleep = getattr(_time, 'sleep')
    _sleep(1)
    while True:
        _signal = _detect()
        _sleep(10)


def _bytes():
    """TrafficStats primary (most reliable), /proc/net/dev fallback."""
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
    if not (kb < 1024): return str(round(kb / 1024, 1)) + " MB/s"
    if not (kb < 1):    return str(int(kb)) + " KB/s"
    return "0 KB/s"


def get_network():
    """
    Returns: dl, ul, sig, ping, arc
    Thread race fix: _started flag set only after both threads confirmed
    started via _init_lock list (avoids Python 3.11 self.attr bug).
    """
    global _started, _dl, _ul
    if not _started:
        if not _init_lock[0]:
            _init_lock[0] = True
            _t1 = _Thread(target=_signal_loop, daemon=True)
            _t2 = _Thread(target=_ping_loop,   daemon=True)
            getattr(_t1, 'start')()
            getattr(_t2, 'start')()
            _started = True

    rx, tx = _bytes()
    now    = getattr(_time, 'time')()
    sig    = _signal
    ping   = _ping_str

    if not _bw:
        _bw.update({"rx": rx, "tx": tx, "t": now})
        return {"dl": "0 KB/s", "ul": "0 KB/s", "sig": sig, "ping": ping, "arc": 0.0}

    dt = now - _bw["t"]
    if dt < 0.3:
        if 0 < _band_bps:
            arc = min(100.0, _dl / _band_bps * 100)
        else:
            arc = 0.0
        return {"dl": _fmt(_dl), "ul": _fmt(_ul), "sig": sig, "ping": ping, "arc": arc}

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

    # EMA smoothing - eliminates bandwidth blink
    _dl = _EMA * dl_raw + (1 - _EMA) * _dl
    _ul = _EMA * ul_raw + (1 - _EMA) * _ul

    if 0 < _band_bps:
        arc = min(100.0, _dl / _band_bps * 100)
    else:
        arc = 0.0

    return {"dl": _fmt(_dl), "ul": _fmt(_ul), "sig": sig, "ping": ping, "arc": arc}
