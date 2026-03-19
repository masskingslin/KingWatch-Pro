"""
KingWatch Pro v17 - core/network.py
Keys: dl, ul, sig, arc  (matches main.py exactly)
"""
import time as _time
import glob
from threading import Thread as _Thread

_signal   = "Detecting..."
_started  = False
_bw       = {}
_dl       = 0.0
_ul       = 0.0
_EMA      = 0.4
_band_bps = 10.0 * 125000


def _quality(dbm):
    if -50 < dbm: return "Excellent"
    if -60 < dbm: return "Good"
    if -70 < dbm: return "Fair"
    if -80 < dbm: return "Weak"
    return "Poor"


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
            return _fallback()
        caps = getattr(cm, 'getNetworkCapabilities')(net)
        if caps is None:
            return _fallback()
        _hT = getattr(caps, 'hasTransport')

        if _hT(1):  # WiFi
            try:
                wm   = getattr(ctx, 'getSystemService')(getattr(Ctx, 'WIFI_SERVICE'))
                info = getattr(wm, 'getConnectionInfo')()
                rssi = getattr(info, 'getRssi')()
                freq = getattr(info, 'getFrequency')()
                spd  = getattr(info, 'getLinkSpeed')()
                if 5000 < freq:
                    band = "5GHz"
                    _band_bps = 300.0 * 125000
                else:
                    band = "2.4GHz"
                    _band_bps = 100.0 * 125000
                q = _quality(rssi)
                return "WiFi " + band + " " + q + " " + str(rssi) + "dBm " + str(spd) + "Mbps"
            except Exception:
                _band_bps = 100.0 * 125000
                return "WiFi"

        if _hT(0):  # Cellular
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
                _band_bps = 10.0*125000; return "Mobile"
            except Exception:
                _band_bps = 10.0*125000; return "Mobile"

        if _hT(3):  # Ethernet
            _band_bps = 1000.0 * 125000
            return "Ethernet  Max 1000Mbps"

        return "Connected"
    except Exception:
        pass
    return _fallback()


def _fallback():
    global _band_bps
    for p in glob.glob("/sys/class/net/wlan*/operstate"):
        try:
            with open(p) as f:
                if f.read().strip() == "up":
                    _band_bps = 100.0 * 125000
                    return "WiFi"
        except Exception:
            pass
    for p in glob.glob("/sys/class/net/rmnet*/operstate"):
        try:
            with open(p) as f:
                if f.read().strip() == "up":
                    _band_bps = 10.0 * 125000
                    return "Mobile"
        except Exception:
            pass
    return ""


def _signal_loop():
    global _signal
    _sleep = getattr(_time, 'sleep')
    while True:
        s = _detect()
        if s:
            _signal = s
        _sleep(5)


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


def get_network():
    # Returns exactly 4 keys: dl, ul, sig, arc
    global _started, _dl, _ul
    if not _started:
        _started = True
        _t1 = _Thread(target=_signal_loop, daemon=True)
        getattr(_t1, 'start')()

    rx, tx = _bytes()
    now    = getattr(_time, 'time')()
    sig    = _signal

    if not _bw:
        _bw.update({"rx": rx, "tx": tx, "t": now})
        return {"dl": "0 KB/s", "ul": "0 KB/s", "sig": sig, "arc": 0.0}

    dt = now - _bw["t"]
    if dt < 0.3:
        if 0 < _band_bps:
            arc = min(100.0, _dl / _band_bps * 100)
        else:
            arc = 0.0
        return {"dl": _fmt(_dl), "ul": _fmt(_ul), "sig": sig, "arc": arc}

    prx = _bw["rx"]
    ptx = _bw["tx"]
    _bw.update({"rx": rx, "tx": tx, "t": now})

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

    if 0 < _band_bps:
        arc = min(100.0, _dl / _band_bps * 100)
    else:
        arc = 0.0

    return {"dl": _fmt(_dl), "ul": _fmt(_ul), "sig": sig, "arc": arc}
