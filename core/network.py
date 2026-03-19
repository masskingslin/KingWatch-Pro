"""
KingWatch Pro - core/network.py
Single global name: _bw_label (consistent everywhere).
Signal thread starts correctly. Band + receiver max shown.
No unicode, no emoji, no ascii art.
"""
import time as _time
import glob
from threading import Thread as _Thread

_signal  = "Detecting..."
_rssi    = ""
_band    = 10.0
_bw_label = ""
_started = False
_bw      = {}
_dl      = 0.0
_ul      = 0.0
_EMA     = 0.4


def _quality(dbm, wifi=False):
    if wifi:
        if -50 < dbm: return "Excellent"
        if -60 < dbm: return "Good"
        if -70 < dbm: return "Fair"
        if -80 < dbm: return "Weak"
        return "Poor"
    if -70 < dbm:  return "Excellent"
    if -85 < dbm:  return "Good"
    if -100 < dbm: return "Fair"
    if -110 < dbm: return "Weak"
    return "Poor"


def _get_mobile_gen(ctx, Ctx):
    global _band, _bw_label
    try:
        from jnius import autoclass  # type: ignore
        TM   = autoclass("android.telephony.TelephonyManager")
        tm   = getattr(ctx, 'getSystemService')(getattr(Ctx, 'TELEPHONY_SERVICE'))
        _gDN = getattr(tm, 'getDataNetworkType')
        nt   = _gDN()
        if nt in (20,): _band=500.0;  _bw_label="Max 500Mbps"; return "5G NR"
        if nt in (13,): _band=50.0;   _bw_label="Max 50Mbps";  return "4G LTE"
        if nt in (19,): _band=150.0;  _bw_label="Max 150Mbps"; return "4G LTE-CA"
        if nt in (15,): _band=42.0;   _bw_label="Max 42Mbps";  return "4G HSPA+"
        if nt in (8,9,10,3,5,6,12,14):
            _band=14.0; _bw_label="Max 14Mbps"; return "3G"
        if nt in (1,2,4,7,11,16):
            _band=0.2;  _bw_label="Max 0.2Mbps"; return "2G"
        _band=10.0; _bw_label=""; return "Mobile"
    except Exception:
        pass
    _band=10.0; _bw_label=""; return "Mobile"


def _wifi_info(ctx, Ctx):
    global _band, _bw_label
    try:
        wm   = getattr(ctx, 'getSystemService')(getattr(Ctx, 'WIFI_SERVICE'))
        info = getattr(wm, 'getConnectionInfo')()
        rssi = getattr(info, 'getRssi')()
        freq = getattr(info, 'getFrequency')()
        spd  = getattr(info, 'getLinkSpeed')()
        if 5000 < freq:
            _band=300.0; band="5GHz"; _bw_label="Max 300Mbps"
        else:
            _band=100.0; band="2.4GHz"; _bw_label="Max 100Mbps"
        qual     = _quality(rssi, wifi=True)
        rssi_str = str(rssi) + "dBm " + qual
        label    = "WiFi " + band + " " + str(spd) + "Mbps"
        return rssi_str, label
    except Exception:
        pass
    _band=100.0; _bw_label="Max 100Mbps"
    return "", "WiFi"


def _fallback():
    global _band, _bw_label
    for p in glob.glob("/sys/class/net/wlan*/operstate"):
        try:
            with open(p) as f:
                if f.read().strip() == "up":
                    _band=100.0; _bw_label="Max 100Mbps"; return "WiFi"
        except Exception:
            pass
    for p in glob.glob("/sys/class/net/rmnet*/operstate"):
        try:
            with open(p) as f:
                if f.read().strip() == "up":
                    _band=10.0; _bw_label=""; return "Mobile"
        except Exception:
            pass
    try:
        with open("/proc/net/wireless") as f:
            for line in f.readlines()[2:]:
                p = line.split()
                if len(p) < 4: continue
                try:
                    dbm = int(float(p[2].rstrip(".")))
                    if dbm < 0:
                        _band=100.0; _bw_label="Max 100Mbps"
                        return "WiFi " + str(dbm) + "dBm"
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
            _rssi = ""; return _fallback()
        caps = getattr(cm, 'getNetworkCapabilities')(net)
        if caps is None:
            _rssi = ""; return _fallback()
        _hT = getattr(caps, 'hasTransport')
        if _hT(1):
            rssi_str, label = _wifi_info(ctx, Ctx)
            _rssi = rssi_str
            return label
        if _hT(0):
            _rssi = ""
            return _get_mobile_gen(ctx, Ctx)
        if _hT(3):
            global _band, _bw_label
            _band=1000.0; _bw_label="Max 1000Mbps"; _rssi=""; return "Ethernet"
        _rssi = ""; return "Connected"
    except Exception:
        pass
    _rssi = ""; return _fallback()


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
    if not (kb < 1024): return str(round(kb/1024,1)) + " MB/s"
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

    # Read globals directly - safest access pattern
    sig   = _signal
    rssi  = _rssi
    bwlbl = _bw_label

    if not _bw:
        _bw.update({"rx": rx, "tx": tx, "t": now})
        return {"dl":"0 KB/s", "ul":"0 KB/s",
                "signal":sig, "rssi":rssi, "bw_label":bwlbl, "arc_pct":0.0}

    dt = now - _bw["t"]
    if dt < 0.3:
        if 0 < _band:
            arc = min(100.0, _dl / (_band * 125000))
        else:
            arc = 0.0
        return {"dl":_fmt(_dl), "ul":_fmt(_ul),
                "signal":sig, "rssi":rssi, "bw_label":bwlbl, "arc_pct":arc}

    prx = _bw["rx"]
    ptx = _bw["tx"]
    _bw.update({"rx":rx, "tx":tx, "t":now})

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

    return {"dl":_fmt(_dl), "ul":_fmt(_ul),
            "signal":sig, "rssi":rssi, "bw_label":bwlbl, "arc_pct":arc}
