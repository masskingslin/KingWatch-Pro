"""
KingWatch Pro v17 - core/network.py

HYBRID BAND DETECTION MATRIX:
  Layer 1: TelephonyManager.getDataNetworkType()  (primary, most accurate)
  Layer 2: NetworkCapabilities.getLinkDownstreamBandwidthKbps() (no permission)
  Layer 3: Heuristic from actual measured speed (always works)
  Layer 4: sysfs interface name fallback

Band is determined by best available source, updated every 5s.
Returns keys: dl, ul, sig, arc
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

# Speed history for heuristic (last 10 samples in bytes/s)
_speed_hist = []


def _quality(dbm):
    if -50 < dbm: return "Excellent"
    if -60 < dbm: return "Good"
    if -70 < dbm: return "Fair"
    if -80 < dbm: return "Weak"
    return "Poor"


def _heuristic_band(dl_bps):
    """
    Layer 3: Classify band from actual measured speed.
    Uses median of recent speed history for stability.
    """
    global _band_bps
    if len(_speed_hist) < 3:
        return ""
    samples = sorted(_speed_hist)
    med = samples[len(samples) // 2]
    mbps = med / 125000.0
    if 50.0 < mbps:  _band_bps = 500.0*125000; return "5G (speed)"
    if 10.0 < mbps:  _band_bps = 50.0*125000;  return "4G LTE (speed)"
    if 1.0  < mbps:  _band_bps = 14.0*125000;  return "3G (speed)"
    if 0.05 < mbps:  _band_bps = 2.0*125000;   return "2G (speed)"
    return ""


def _telephony_band(ctx, Ctx):
    """Layer 1: TelephonyManager - most accurate when available."""
    global _band_bps
    try:
        from jnius import autoclass  # type: ignore
        TM = autoclass("android.telephony.TelephonyManager")
        tm = getattr(ctx, 'getSystemService')(getattr(Ctx, 'TELEPHONY_SERVICE'))
        nt = getattr(tm, 'getDataNetworkType')()
        if nt in (0,):   return ""  # UNKNOWN - try next layer
        if nt in (20,):  _band_bps=500.0*125000;  return "5G NR  Max 500Mbps"
        if nt in (13,):  _band_bps=50.0*125000;   return "4G LTE  Max 50Mbps"
        if nt in (19,):  _band_bps=150.0*125000;  return "4G LTE-CA  Max 150Mbps"
        if nt in (15,):  _band_bps=42.0*125000;   return "4G HSPA+  Max 42Mbps"
        if nt in (8,9,10,3,5,6,12,14):
            _band_bps=14.0*125000; return "3G  Max 14Mbps"
        if nt in (1,2,4,7,11,16):
            _band_bps=0.2*125000;  return "2G  Max 0.2Mbps"
        _band_bps=10.0*125000; return "Mobile"
    except Exception:
        pass
    return ""


def _caps_band(caps):
    """Layer 2: NetworkCapabilities bandwidth estimate - no permission needed."""
    global _band_bps
    try:
        _gDL = getattr(caps, 'getLinkDownstreamBandwidthKbps')
        dl   = _gDL()
        if 0 < dl:
            if 50000 < dl:   _band_bps=500.0*125000;  return "5G  ~" + str(dl//1000) + "Mbps"
            if 5000  < dl:   _band_bps=50.0*125000;   return "4G LTE  ~" + str(dl//1000) + "Mbps"
            if 1000  < dl:   _band_bps=20.0*125000;   return "4G  ~" + str(dl//1000) + "Mbps"
            if 200   < dl:   _band_bps=14.0*125000;   return "3G  ~" + str(dl//1000) + "Mbps"
            _band_bps=0.2*125000;  return "2G  ~" + str(dl) + "Kbps"
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
            return _fallback()
        caps = getattr(cm, 'getNetworkCapabilities')(net)
        if caps is None:
            return _fallback()
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
                _band_bps = 100.0*125000; return "WiFi"

        # Cellular - hybrid matrix
        if _hT(0):
            # Layer 1: TelephonyManager
            result = _telephony_band(ctx, Ctx)
            if result:
                return result
            # Layer 2: NetworkCapabilities bandwidth
            result = _caps_band(caps)
            if result:
                return result
            # Layer 3: Heuristic from speed history
            result = _heuristic_band(_dl)
            if result:
                return result
            # All failed - show Mobile
            _band_bps = 10.0*125000
            return "Mobile"

        if _hT(3):
            _band_bps = 1000.0*125000
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
                    _band_bps = 100.0*125000; return "WiFi"
        except Exception:
            pass
    for p in glob.glob("/sys/class/net/rmnet*/operstate"):
        try:
            with open(p) as f:
                if f.read().strip() == "up":
                    _band_bps = 10.0*125000; return "Mobile"
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


def get_network():
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

    # Feed speed history for heuristic
    if 0 < dl_raw:
        _speed_hist.append(dl_raw)
        if not (len(_speed_hist) < 11):
            _speed_hist.pop(0)

    if 0 < _band_bps:
        arc = min(100.0, _dl / _band_bps * 100)
    else:
        arc = 0.0

    return {"dl": _fmt(_dl), "ul": _fmt(_ul), "sig": sig, "arc": arc}
