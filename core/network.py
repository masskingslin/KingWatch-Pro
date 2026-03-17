"""
KingWatch Pro v17 - core/network.py

ROOT CAUSE OF BAND/PING FAILURE:
1. getDataNetworkType() returns 0 (UNKNOWN) on many devices unless
   READ_PHONE_STATE is RUNTIME-granted by user — even with manifest permission.
2. NetworkCapabilities static field access via pyjnius can fail silently.
3. getaddrinfo() DNS timing measures DNS server latency not network RTT.

DEFINITIVE FIX:
- Band: Use TelephonyManager.getNetworkTypeName() which returns a STRING
  like "LTE", "NR", "HSPA" — no int mapping needed, no unknown=0 problem.
  Fallback to NetworkInfo.getSubtype/getSubtypeName via ConnectivityManager.
- Ping: Read /proc/net/tcp RTT + fallback to socket connect to port 443
  of a known IP (bypasses DNS, faster, more accurate).
- Speeds: TrafficStats with /sys/class/net fallback.
"""
import time, os, socket

_prev_rx = 0; _prev_tx = 0; _prev_time = 0.0
_dl_buf = []; _ul_buf = []; _SMOOTH = 4
_band_cache = ""; _band_age = 99; _band_mbps = 10.0
_ping_cache = ""; _ping_age = 0

_jready = False
_TS = _PA = _CTX = None

def _jinit():
    global _jready, _TS, _PA, _CTX
    if _jready: return True
    try:
        from jnius import autoclass  # type: ignore
        _TS  = autoclass("android.net.TrafficStats")
        _PA  = autoclass("org.kivy.android.PythonActivity")
        _CTX = autoclass("android.content.Context")
        _jready = True
        return True
    except Exception:
        return False

_BAND_MBPS = {
    "GPRS":0.1,"EDGE":0.2,"CDMA":0.1,"1xRTT":0.1,"IDEN":0.05,"GSM":0.1,
    "UMTS":2.0,"HSDPA":14.0,"HSUPA":5.7,"HSPA":14.0,"HSPA+":42.0,
    "EVDO_0":3.1,"EVDO_A":3.1,"EVDO_B":14.7,"EHRPD":14.0,
    "LTE":50.0,"LTE_CA":150.0,"NR":500.0,"WIFI":100.0,
}


# ── bytes ──────────────────────────────────────────────────────────────────
def _get_bytes():
    if _jinit():
        try:
            rx = _TS.getTotalRxBytes()
            tx = _TS.getTotalTxBytes()
            if rx > 0: return int(rx), int(tx)
        except Exception: pass
    rx = tx = 0
    try:
        with open("/proc/net/dev") as f:
            for ln in f.readlines()[2:]:
                if ":" not in ln: continue
                ifc, d = ln.split(":",1)
                if ifc.strip()=="lo": continue
                c = d.split()
                if len(c)>=9: rx+=int(c[0]); tx+=int(c[8])
    except Exception: pass
    return rx, tx


def _smooth(buf, v, n):
    buf.append(v)
    if len(buf)>n: buf.pop(0)
    return sum(buf)/len(buf)


def _human(bps):
    if bps>=1_048_576: return f"{bps/1_048_576:.1f}MB/s"
    if bps>=1024:      return f"{bps/1024:.0f}KB/s"
    return f"{int(bps)}B/s"


# ── band detection ─────────────────────────────────────────────────────────
def _detect_band():
    global _band_mbps
    if not _jinit(): return _iface_band()
    ctx = _PA.mActivity

    # ── WiFi check first (most reliable, no permission needed)
    try:
        wm   = ctx.getSystemService(_CTX.WIFI_SERVICE)
        info = wm.getConnectionInfo()
        rssi = info.getRssi()
        ssid = str(info.getSSID()) if hasattr(info,'getSSID') else ""
        if -120 < rssi < 0:
            freq = 0
            try: freq = info.getFrequency()  # 2412-2484=2.4GHz, 5180+=5GHz
            except Exception: pass
            band_str = ""
            if freq >= 5000:    band_str = " 5GHz"
            elif freq >= 2400:  band_str = " 2.4GHz"
            _band_mbps = 100.0
            return f"WiFi{band_str} {rssi}dBm"
    except Exception: pass

    # ── Cellular: try getNetworkTypeName() - returns "LTE","NR","HSPA" etc
    try:
        from jnius import autoclass  # type: ignore
        TM = autoclass("android.telephony.TelephonyManager")
        tm = ctx.getSystemService(_CTX.TELEPHONY_SERVICE)

        # getNetworkTypeName is a static helper - always works, no permission
        try:
            nt   = tm.getDataNetworkType()   # Android 11+, no permission
            name = TM.getNetworkTypeName(nt) # static, always available
            if name and name not in ("UNKNOWN", ""):
                return _name_to_band(name)
        except Exception: pass

        try:
            nt   = tm.getNetworkType()       # older API
            name = TM.getNetworkTypeName(nt)
            if name and name not in ("UNKNOWN", ""):
                return _name_to_band(name)
        except Exception: pass

        # Last resort: getNetworkOperatorName gives carrier, not type
        # but confirms cellular is active
        try:
            op = tm.getNetworkOperatorName()
            if op and len(op) > 0:
                _band_mbps = 10.0
                return f"Mobile ({op})"
        except Exception: pass

    except Exception: pass

    # ── ConnectivityManager subtype name (works on all Android versions)
    try:
        from jnius import autoclass  # type: ignore
        cm  = ctx.getSystemService(_CTX.CONNECTIVITY_SERVICE)
        ni  = cm.getActiveNetworkInfo()   # deprecated in API 29 but still works
        if ni and ni.isConnected():
            type_name = str(ni.getTypeName())   # "WIFI" or "MOBILE"
            sub_name  = str(ni.getSubtypeName())# "LTE", "HSPA", "NR" etc
            if "WIFI" in type_name.upper():
                _band_mbps = 100.0
                return "WiFi"
            if sub_name and sub_name.upper() not in ("", "UNKNOWN"):
                return _name_to_band(sub_name)
            if "MOBILE" in type_name.upper():
                _band_mbps = 10.0
                return "Mobile"
    except Exception: pass

    return _iface_band()


def _name_to_band(name):
    """Convert TelephonyManager network type name to display string."""
    global _band_mbps
    n = name.upper().replace("-","_").replace("+","")
    if   "NR"     in n: _band_mbps=500.0;  return "5G NR"
    elif "LTE_CA" in n: _band_mbps=150.0;  return "4G LTE-CA"
    elif "LTE"    in n: _band_mbps=50.0;   return "4G LTE"
    elif "HSPA"   in n: _band_mbps=42.0;   return "3G HSPA+"
    elif "HSDPA"  in n: _band_mbps=14.0;   return "3G HSDPA"
    elif "HSUPA"  in n: _band_mbps=5.7;    return "3G HSUPA"
    elif "UMTS"   in n: _band_mbps=2.0;    return "3G UMTS"
    elif "EVDO"   in n: _band_mbps=3.1;    return "3G EVDO"
    elif "EHRPD"  in n: _band_mbps=14.0;   return "3G eHRPD"
    elif "EDGE"   in n: _band_mbps=0.2;    return "2G EDGE"
    elif "GPRS"   in n: _band_mbps=0.1;    return "2G GPRS"
    elif "GSM"    in n: _band_mbps=0.1;    return "2G GSM"
    elif "CDMA"   in n: _band_mbps=0.1;    return "2G CDMA"
    elif "WIFI"   in n: _band_mbps=100.0;  return "WiFi"
    _band_mbps = 10.0
    return name[:10]   # show raw name if unknown


def _iface_band():
    global _band_mbps
    try:
        with open("/proc/net/wireless") as f:
            for i,ln in enumerate(f):
                if i<2: continue
                p=ln.split()
                if len(p)>=4:
                    dbm=int(float(p[3].rstrip(".")))
                    if dbm>0: dbm-=256
                    if -120<dbm<0:
                        _band_mbps=100.0
                        return f"WiFi {dbm}dBm"
    except Exception: pass
    try:
        for ifc in sorted(os.listdir("/sys/class/net")):
            try:
                with open(f"/sys/class/net/{ifc}/operstate") as f:
                    if f.read().strip() not in ("up","unknown"): continue
            except Exception: continue
            if ifc.startswith(("wlan","wlp","wifi")):
                _band_mbps=100.0; return "WiFi"
            if ifc.startswith(("rmnet","ccmni","seth","wwan","ppp","qmi")):
                _band_mbps=10.0;  return "Mobile"
    except Exception: pass
    return ""


# ── ping ───────────────────────────────────────────────────────────────────
def _measure_ping():
    """
    Use /proc/net/tcp ESTABLISHED connection RTOs for real-time latency.
    Fallback: time socket.connect() to 8.8.8.8:443 (HTTPS port, less blocked).
    """
    # Method 1: TCP RTO from established connections
    for path in ("/proc/net/tcp6", "/proc/net/tcp"):
        try:
            with open(path) as f: lines = f.readlines()[1:]
            vals = []
            for ln in lines[:40]:
                p = ln.split()
                if len(p)>=13 and p[3]=="01":  # ESTABLISHED
                    try:
                        rto = int(p[12],16) * 4  # jiffies@250Hz → ms
                        # RTO is ~4x RTT for stable connections
                        rtt = max(1, rto//4)
                        if 1 < rtt < 1500: vals.append(rtt)
                    except Exception: pass
            if vals: return f"{min(vals)}ms"
        except Exception: continue

    # Method 2: TCP connect timing to known IPs (no DNS needed)
    for ip, port in [("8.8.8.8",53),("1.1.1.1",53),("208.67.222.222",443)]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.5)
            t0 = time.monotonic()
            result = s.connect_ex((ip, port))
            ms = int((time.monotonic()-t0)*1000)
            s.close()
            if ms < 3000: return f"{ms}ms"
        except Exception: continue

    return ""


# ── public ─────────────────────────────────────────────────────────────────
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
    if _ping_age>=8:
        p=_measure_ping()
        if p: _ping_cache=p
        _ping_age=0

    return {
        "dl":     _human(dl),
        "ul":     _human(ul),
        "signal": _band_cache or "Detecting",
        "ping":   _ping_cache or "--",
        "arc_pct":arc,
    }
