import time
import socket
import threading
import os
import glob

try:
    from jnius import autoclass as _autoclass
    _JNIUS_OK = True
except Exception:
    _autoclass = None
    _JNIUS_OK = False

_ping_ms    = 0
_signal_str = 'Detecting...'
_bg_started = False
_bw         = {'last_dl': 0, 'last_ul': 0, 'rx': 0, 'tx': 0, 't': 0}
_lock       = threading.Lock()


def _r(path):
    try:
        return open(path).read().strip()
    except Exception:
        return ''


def _ping_worker():
    global _ping_ms
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            t0 = time.time()
            s.connect(('8.8.8.8', 53))
            s.close()
            _ping_ms = round((time.time() - t0) * 1000)
        except Exception:
            _ping_ms = 0
        time.sleep(5)


def _signal_worker():
    global _signal_str
    while True:
        try:
            _signal_str = _detect_signal_safe()
        except Exception:
            _signal_str = 'Unknown'
        time.sleep(8)


def _detect_signal_safe():
    if _JNIUS_OK:
        try:
            Context             = _autoclass('android.content.Context')
            PythonActivity      = _autoclass('org.kivy.android.PythonActivity')
            ConnectivityManager = _autoclass('android.net.ConnectivityManager')
            NetworkCapabilities = _autoclass('android.net.NetworkCapabilities')

            ctx  = PythonActivity.mActivity
            cm   = ctx.getSystemService(Context.CONNECTIVITY_SERVICE)
            net  = cm.getActiveNetwork()
            if not net:
                return 'No Connection'
            caps = cm.getNetworkCapabilities(net)
            if not caps:
                return 'Unknown'

            TW = NetworkCapabilities.TRANSPORT_WIFI
            TC = NetworkCapabilities.TRANSPORT_CELLULAR
            TE = NetworkCapabilities.TRANSPORT_ETHERNET

            if caps.hasTransport(TW):
                try:
                    WifiManager = _autoclass('android.net.wifi.WifiManager')
                    wm   = ctx.getSystemService(Context.WIFI_SERVICE)
                    info = wm.getConnectionInfo()
                    rssi = info.getRssi()
                    speed = info.getLinkSpeed()
                    if rssi >= -50:   q = 'Excellent'
                    elif rssi >= -65: q = 'Good'
                    elif rssi >= -75: q = 'Fair'
                    else:             q = 'Weak'
                    return 'WiFi %s %ddBm %dMbps' % (q, rssi, speed)
                except Exception:
                    return 'WiFi Connected'

            elif caps.hasTransport(TC):
                try:
                    dl = caps.getLinkDownstreamBandwidthKbps()
                    ul = caps.getLinkUpstreamBandwidthKbps()
                    if dl >= 20000:   gen = '5G'
                    elif dl >= 1000:  gen = '4G LTE'
                    elif dl >= 200:   gen = '3G'
                    else:             gen = '2G'
                    return 'Mobile %s (%.0f/%.0f Mbps)' % (gen, dl/1000, ul/1000)
                except Exception:
                    return 'Mobile Data'

            elif caps.hasTransport(TE):
                return 'Ethernet'

            return 'Connected'

        except Exception:
            pass

    try:
        with open('/proc/net/wireless') as f:
            lines = f.readlines()
        if len(lines) > 2:
            p = lines[2].split()
            if len(p) >= 4:
                dbm = float(p[3].rstrip('.'))
                if dbm >= -50:   q = 'Excellent'
                elif dbm >= -65: q = 'Good'
                elif dbm >= -75: q = 'Fair'
                else:            q = 'Weak'
                return 'WiFi %s' % q
    except Exception:
        pass

    for wlan in glob.glob('/sys/class/net/wlan*/operstate'):
        if _r(wlan) == 'up':
            return 'WiFi'

    for rmnet in glob.glob('/sys/class/net/rmnet*/operstate'):
        if _r(rmnet) == 'up':
            return 'Mobile Data'

    return 'No Network'


def _fmt(bps):
    if bps <= 0:
        return '0 KB/s'
    kbps = bps / 1024.0
    if kbps >= 1024:
        return '%.1f MB/s' % (kbps / 1024)
    return '%.0f KB/s' % kbps


def _read_bytes():
    if _JNIUS_OK:
        try:
            TrafficStats = _autoclass('android.net.TrafficStats')
            return TrafficStats.getTotalRxBytes(), TrafficStats.getTotalTxBytes()
        except Exception:
            pass
    try:
        rx = tx = 0
        with open('/proc/net/dev') as f:
            for line in f.readlines()[2:]:
                p = line.split()
                if len(p) < 10 or p[0].rstrip(':') == 'lo':
                    continue
                rx += int(p[1])
                tx += int(p[9])
        return rx, tx
    except Exception:
        return 0, 0


def get_network():
    global _bg_started
    if not _bg_started:
        _bg_started = True
        threading.Thread(target=_ping_worker, daemon=True).start()
        threading.Thread(target=_signal_worker, daemon=True).start()

    rx, tx = _read_bytes()
    now = time.time()

    with _lock:
        dt     = now - _bw.get('t', now)
        dl_bps = (rx  - _bw.get('rx', rx)) / max(dt, 0.5)
        ul_bps = (tx  - _bw.get('tx', tx)) / max(dt, 0.5)
        _bw.update({'rx': rx, 'tx': tx, 't': now})

    return {
        'ping':   ('%d ms' % _ping_ms) if _ping_ms else 'Pinging...',
        'dl':     _fmt(dl_bps),
        'ul':     _fmt(ul_bps),
        'signal': _signal_str,
    }
