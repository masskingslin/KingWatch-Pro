"""
KingWatch Pro v17 - core/network.py
Shows real SIM receiver band: 5G NR / 4G LTE / 3G / 2G

BAND DETECTION - 5-layer fallback:
  L1a: getDataNetworkType()  - accurate, needs READ_PHONE_STATE
  L1b: getNetworkType()      - deprecated but no permission on most ROMs
  L2:  getLinkDownstreamBandwidthKbps() - no permission, gives range
  L3:  speed heuristic       - from measured _dl EMA
  L4:  'Mobile'              - guaranteed non-empty

All 20 TelephonyManager network type constants mapped.
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

# All TelephonyManager NETWORK_TYPE_* constants -> (label, max_mbps)
_NT_MAP = {
    1:  ("2G GPRS",    0.1),
    2:  ("2G EDGE",    0.2),
    3:  ("3G UMTS",    2.0),
    4:  ("2G CDMA",    0.1),
    5:  ("3G EVDO",    2.4),
    6:  ("3G EVDO-A",  3.1),
    7:  ("2G 1xRTT",   0.1),
    8:  ("3G HSDPA",   7.2),
    9:  ("3G HSUPA",   5.8),
    10: ("3G HSPA",    14.0),
    11: ("2G GSM",     0.1),
    12: ("3G EVDO-B",  14.7),
    13: ("4G LTE",     100.0),
    14: ("3G EHRPD",   14.0),
    15: ("4G HSPA+",   42.0),
    16: ("2G GSM",     0.1),
    17: ("3G SCDMA",   1.0),
    18: ("4G LTE-CA",  150.0),
    19: ("4G LTE-CA",  300.0),
    20: ("5G NR",      1000.0),
}


def _nt_to_label(nt):
    """Convert network type int to display label + set _band_bps."""
    global _band_bps
    entry = _NT_MAP.get(nt, None)
    if entry is not None:
        label, mbps = entry
        _band_bps = mbps * 125000
        return label
    return ""


def _ping_icmp():
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
                    ms = round(float(getattr(m, 'group')(1)))
                if 0 < ms:
                    return str(ms) + "ms"
        except Exception:
            pass
    return None


def _ping_tcp():
    _sk  = __import__('socket')
    _AF  = getattr(_sk, 'AF_INET')
    _ST  = getattr(_sk, 'SOCK_STREAM')
    _SC  = getattr(_sk, 'socket')
    _now = getattr(_time, 'time')
    for ip, port in [("8.8.8.8", 53), ("1.1.1.1", 443), ("8.8.4.4", 53)]:
        s = None
        try:
            s   = _SC(_AF, _ST)
            _st = getattr(s, 'settimeout')
            _cn = getattr(s, 'connect')
            _st(1.5)
            t0  = _now()
            _cn((ip, port))
            ms  = round((_now() - t0) * 1000)
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
    global _band_bps
    spd  = _fmt_speed(dl_bps)
    mbps = dl_bps / 125000.0
    if 50.0 < mbps:  _band_bps = 500.0*125000; return "5G NR  " + spd
    if 10.0 < mbps:  _band_bps = 50.0*125000;  return "4G LTE  " + spd
    if 1.0  < mbps:  _band_bps = 14.0*125000;  return "3G  " + spd
    if 0.05 < mbps:  _band_bps = 2.0*125000;   return "2G  " + spd
    return ""


def _heuristic():
    global _band_bps
    if len(_spdhist) < 1:
        return ""
    med  = sorted(_spdhist)[len(_spdhist) // 2]
    mbps = med / 125000.0
    if 50.0 < mbps:  _band_bps = 500.0*125000; return "5G NR"
    if 10.0 < mbps:  _band_bps = 50.0*125000;  return "4G LTE"
    if 1.0  < mbps:  _band_bps = 14.0*125000;  return "3G"
    if 0.05 < mbps:  _band_bps = 2.0*125000;   return "2G"
    return ""


def _get_cell_band(ctx, Ctx):
    """
    Get real SIM receiver band via TelephonyManager.
    Tries getDataNetworkType() first (API 24+, needs READ_PHONE_STATE on 26+).
    Falls back to getNetworkType() (deprecated but works without permission
    on many OEMs including Samsung/Xiaomi/OnePlus).
    Returns e.g. '4G LTE', '5G NR', '3G HSPA', '2G EDGE'
    """
    global _band_bps
    try:
        from jnius import autoclass  # type: ignore
        tm = getattr(ctx, 'getSystemService')(getattr(Ctx, 'TELEPHONY_SERVICE'))

        # L1a: getDataNetworkType - most accurate
        try:
            _gDNT = getattr(tm, 'getDataNetworkType')
            nt    = _gDNT()
            label = _nt_to_label(nt)
            if label:
                return label
        except Exception:
            pass

        # L1b: getNetworkType - deprecated but no permission on many ROMs
        try:
            _gNT  = getattr(tm, 'getNetworkType')
            nt    = _gNT()
            label = _nt_to_label(nt)
            if label:
                return label
        except Exception:
            pass

    except Exception:
        pass
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

        # Cellular
        if _hT(0):
            # L1: TelephonyManager (both getDataNetworkType + getNetworkType)
            band = _get_cell_band(ctx, Ctx)
            if band:
                return band

            # L2: NetworkCapabilities bandwidth (no permission needed)
            try:
                dl_k = getattr(caps, 'getLinkDownstreamBandwidthKbps')()
                if 0 < dl_k:
                    if 50000 < dl_k: _band_bps=500.0*125000; return "5G NR ~" + str(dl_k//1000) + "Mbps"
                    if 5000  < dl_k: _band_bps=50.0*125000;  return "4G LTE ~" + str(dl_k//1000) + "Mbps"
                    if 1000  < dl_k: _band_bps=20.0*125000;  return "4G ~" + str(dl_k//1000) + "Mbps"
                    if 200   < dl_k: _band_bps=14.0*125000;  return "3G ~" + str(dl_k//1000) + "Mbps"
                    _band_bps = 0.2*125000; return "2G ~" + str(dl_k) + "Kbps"
            except Exception:
                pass

            # L3: speed history heuristic (works after 1 sample)
            h = _heuristic()
            if h:
                return h

            # L4: live _dl EMA with actual speed
            b = _band_from_speed(_dl)
            if b:
                return b

            # L5: guaranteed
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
    global _signal
    _sleep = getattr(_time, 'sleep')
    _sleep(1)
    while True:
        _signal = _detect()
        _sleep(10)


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
    if not (kb < 1024): return str(round(kb / 1024, 1)) + " MB/s"
    if not (kb < 1):    return str(int(kb)) + " KB/s"
    return "0 KB/s"


def get_network():
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

    _dl = _EMA * dl_raw + (1 - _EMA) * _dl
    _ul = _EMA * ul_raw + (1 - _EMA) * _ul

    if 0 < _band_bps:
        arc = min(100.0, _dl / _band_bps * 100)
    else:
        arc = 0.0

    return {"dl": _fmt(_dl), "ul": _fmt(_ul), "sig": sig, "ping": ping, "arc": arc}
