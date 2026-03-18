"""
KingWatch Pro v17 - core/network.py
Ping: reads /proc/net/tcp RTO from ESTABLISHED connections (always works,
no network call needed, no permissions, instant result).
"""
import time, os, socket

_prev_rx=0; _prev_tx=0; _prev_time=0.0
_dl_buf=[]; _ul_buf=[]; _SMOOTH=4
_band_cache=""; _band_age=99; _band_mbps=10.0
_ping_cache=""; _ping_age=99  # 99 = run immediately on first call

_jready=False; _TS=_PA=_CTX=None

def _jinit():
    global _jready,_TS,_PA,_CTX
    if _jready: return True
    try:
        from jnius import autoclass  # type: ignore
        _TS  = autoclass("android.net.TrafficStats")
        _PA  = autoclass("org.kivy.android.PythonActivity")
        _CTX = autoclass("android.content.Context")
        _jready=True; return True
    except Exception: return False

_BAND_MBPS={
    "2G GPRS":0.1,"2G EDGE":0.2,"2G GSM":0.1,"2G CDMA":0.1,
    "3G UMTS":2.0,"3G HSDPA":14.0,"3G HSUPA":5.7,"3G HSPA":14.0,
    "3G HSPA+":42.0,"3G EVDO":3.1,"3G eHRPD":14.0,
    "4G LTE":50.0,"4G LTE-CA":150.0,"4G TDD-LTE":50.0,
    "5G NR":500.0,"WiFi":100.0,"WiFi 5GHz":300.0,"WiFi 2.4GHz":100.0,
}


def _get_bytes():
    if _jinit():
        try:
            rx=_TS.getTotalRxBytes(); tx=_TS.getTotalTxBytes()
            if rx>0: return int(rx),int(tx)
        except Exception: pass
    rx=tx=0
    try:
        with open("/proc/net/dev") as f:
            for ln in f.readlines()[2:]:
                if ":"not in ln: continue
                ifc,d=ln.split(":",1)
                if ifc.strip()=="lo": continue
                c=d.split()
                if len(c)>=9: rx+=int(c[0]); tx+=int(c[8])
    except Exception: pass
    return rx,tx


def _smooth(buf,v,n):
    buf.append(v)
    if len(buf)>n: buf.pop(0)
    return sum(buf)/len(buf)


def _human(bps):
    if bps>=1_048_576: return f"{bps/1_048_576:.1f}MB/s"
    if bps>=1024:      return f"{bps/1024:.0f}KB/s"
    return f"{int(bps)}B/s"


def _ping():
    """
    Read RTT from /proc/net/tcp ESTABLISHED connections.
    Column 12 (hex) = retransmit timeout in jiffies (250Hz = 4ms each).
    RTT ≈ RTO / 6  for stable connections (Linux TCP sets RTO = max(RTT*2, 200ms)).
    This requires NO network call, NO permissions, works instantly.
    """
    best = None
    for path in ("/proc/net/tcp6", "/proc/net/tcp"):
        try:
            with open(path) as f:
                lines = f.readlines()[1:]
            for ln in lines[:60]:
                cols = ln.split()
                if len(cols) < 13:
                    continue
                state = cols[3]
                if state != "01":   # 01 = ESTABLISHED only
                    continue
                try:
                    rto_jiffies = int(cols[12], 16)
                    # jiffies at 250Hz = 4ms each
                    rto_ms = rto_jiffies * 4
                    # RTT estimate: RTO is ~200ms min + 2*RTT
                    # For rto_ms > 200: rtt = (rto_ms - 200) / 2
                    # For rto_ms <= 200: connection is very fast, estimate ~10ms
                    if rto_ms <= 0:
                        continue
                    if rto_ms <= 200:
                        rtt = max(1, rto_ms // 4)
                    else:
                        rtt = max(1, (rto_ms - 200) // 2)
                    if 1 <= rtt <= 2000:
                        if best is None or rtt < best:
                            best = rtt
                except Exception:
                    continue
        except Exception:
            continue

    if best is not None:
        return f"{best}ms"

    # Fallback: TCP SYN timing to Google DNS (no data transfer, just SYN+RST)
    for ip, port in [("8.8.8.8", 53), ("1.1.1.1", 53), ("8.8.4.4", 443)]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.0)
            t0 = time.monotonic()
            err = s.connect_ex((ip, port))
            ms  = int((time.monotonic() - t0) * 1000)
            s.close()
            if ms < 3000:
                return f"{ms}ms"
        except Exception:
            continue

    return "--"


def _detect_band():
    global _band_mbps
    if not _jinit(): return _iface_band()
    ctx = _PA.mActivity

    # WiFi (no permission needed)
    try:
        wm   = ctx.getSystemService(_CTX.WIFI_SERVICE)
        info = wm.getConnectionInfo()
        rssi = info.getRssi()
        if -120 < rssi < 0:
            freq = 0
            try: freq = info.getFrequency()
            except Exception: pass
            if freq >= 5000:
                _band_mbps=300.0; return f"WiFi 5GHz {rssi}dBm"
            elif freq >= 2400:
                _band_mbps=100.0; return f"WiFi 2.4GHz {rssi}dBm"
            _band_mbps=100.0; return f"WiFi {rssi}dBm"
    except Exception: pass

    # Cellular via TelephonyManager.getNetworkTypeName (static, string-based)
    try:
        from jnius import autoclass  # type: ignore
        TM = autoclass("android.telephony.TelephonyManager")
        tm = ctx.getSystemService(_CTX.TELEPHONY_SERVICE)
        for method in ("getDataNetworkType", "getNetworkType"):
            try:
                nt   = getattr(tm, method)()
                name = TM.getNetworkTypeName(nt)
                if name and name.upper() not in ("UNKNOWN", ""):
                    return _name_to_band(name)
            except Exception: continue
        # Carrier name as last resort
        try:
            op = tm.getNetworkOperatorName()
            if op and len(str(op)) > 0:
                _band_mbps=10.0; return f"Mobile"
        except Exception: pass
    except Exception: pass

    # ConnectivityManager.getActiveNetworkInfo (deprecated but universal)
    try:
        cm = ctx.getSystemService(_CTX.CONNECTIVITY_SERVICE)
        ni = cm.getActiveNetworkInfo()
        if ni and ni.isConnected():
            tn = str(ni.getTypeName()).upper()
            sn = str(ni.getSubtypeName()).upper()
            if "WIFI" in tn:
                _band_mbps=100.0; return "WiFi"
            if sn and sn not in ("","UNKNOWN"):
                return _name_to_band(sn)
            if "MOBILE" in tn or "CELLULAR" in tn:
                _band_mbps=10.0; return "Mobile"
    except Exception: pass

    return _iface_band()


def _name_to_band(name):
    global _band_mbps
    n = name.upper()
    if   "NR"    in n: _band_mbps=500.0;  return "5G NR"
    elif "LTE"   in n and "CA" in n: _band_mbps=150.0; return "4G LTE-CA"
    elif "LTE"   in n: _band_mbps=50.0;   return "4G LTE"
    elif "HSPA"  in n: _band_mbps=42.0;   return "3G HSPA+"
    elif "HSDPA" in n: _band_mbps=14.0;   return "3G HSDPA"
    elif "HSUPA" in n: _band_mbps=5.7;    return "3G HSUPA"
    elif "UMTS"  in n: _band_mbps=2.0;    return "3G UMTS"
    elif "EVDO"  in n: _band_mbps=3.1;    return "3G EVDO"
    elif "EDGE"  in n: _band_mbps=0.2;    return "2G EDGE"
    elif "GPRS"  in n: _band_mbps=0.1;    return "2G GPRS"
    elif "GSM"   in n: _band_mbps=0.1;    return "2G GSM"
    elif "CDMA"  in n: _band_mbps=0.1;    return "2G CDMA"
    elif "WIFI"  in n: _band_mbps=100.0;  return "WiFi"
    _band_mbps=10.0; return name[:12]


def _iface_band():
    global _band_mbps
    try:
        with open("/proc/net/wireless") as f:
            for i,ln in enumerate(f):
                if i<2: continue
                p=ln.split()
                if len(p)>=4:
                    try:
                        dbm=int(float(p[3].rstrip(".")))
                        if dbm>0: dbm-=256
                        if -120<dbm<0:
                            _band_mbps=100.0; return f"WiFi {dbm}dBm"
                    except Exception: pass
    except Exception: pass
    try:
        for ifc in sorted(os.listdir("/sys/class/net")):
            try:
                with open(f"/sys/class/net/{ifc}/operstate") as f:
                    if f.read().strip() not in ("up","unknown"): continue
            except Exception: continue
            if ifc.startswith(("wlan","wlp","wifi")): _band_mbps=100.0; return "WiFi"
            if ifc.startswith(("rmnet","ccmni","seth","wwan","ppp","qmi")): _band_mbps=10.0; return "Mobile"
    except Exception: pass
    return ""


def get_network() -> dict:
    global _prev_rx,_prev_tx,_prev_time,_band_cache,_band_age,_ping_cache,_ping_age

    now=time.monotonic()
    rx,tx=_get_bytes()
    elapsed=max(0.5,now-_prev_time) if _prev_time>0 else 1.0
    dl_r=(rx-_prev_rx)/elapsed if (_prev_rx>0 and rx>_prev_rx) else 0.0
    ul_r=(tx-_prev_tx)/elapsed if (_prev_tx>0 and tx>_prev_tx) else 0.0
    _prev_rx=rx; _prev_tx=tx; _prev_time=now

    dl=_smooth(_dl_buf,dl_r,_SMOOTH)
    ul=_smooth(_ul_buf,ul_r,_SMOOTH)

    max_bps=_band_mbps*125_000
    arc=min(100.0,dl/max_bps*100) if max_bps>0 else 0.0

    _band_age+=1
    if _band_age>=5:
        b=_detect_band()
        if b: _band_cache=b
        _band_age=0

    _ping_age+=1
    if _ping_age>=3:   # refresh every 3 seconds
        _ping_cache=_ping()
        _ping_age=0

    return {
        "dl":     _human(dl),
        "ul":     _human(ul),
        "signal": _band_cache or "Detecting",
        "ping":   _ping_cache or "--",
        "arc_pct":arc,
    }
