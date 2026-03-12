import time, socket, threading, os, glob

# ── Background ping ──────────────────────────────────────
_ping_ms      = None
_ping_started = False

def _ping_worker():
    global _ping_ms
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1)
            s.connect(("8.8.8.8", 80))
            s.close()
            # TCP latency
            s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s2.settimeout(2)
            t0 = time.time()
            s2.connect(("8.8.8.8", 53))
            s2.close()
            _ping_ms = round((time.time() - t0) * 1000, 1)
        except Exception:
            _ping_ms = None
        time.sleep(5)

# ── Bandwidth state ──────────────────────────────────────
_bw = {}

def _fmt(bps):
    if bps < 0: bps = 0
    kbps = bps / 1024.0
    if kbps >= 1024:
        return f"{kbps/1024:.1f} MB/s"
    return f"{kbps:.1f} KB/s"

def _read_bytes_android():
    """Use Android TrafficStats via jnius — most accurate on Android."""
    try:
        from jnius import autoclass
        TrafficStats = autoclass("android.net.TrafficStats")
        tx = TrafficStats.getTotalTxBytes()
        rx = TrafficStats.getTotalRxBytes()
        if tx >= 0 and rx >= 0:
            return rx, tx, True
    except Exception:
        pass
    return 0, 0, False

def _read_bytes_proc():
    """Fallback: read /proc/net/dev."""
    rx = tx = 0
    try:
        with open("/proc/net/dev") as f:
            for line in f.readlines()[2:]:
                p = line.split()
                if len(p) < 10 or p[0].rstrip(":") == "lo":
                    continue
                rx += int(p[1])
                tx += int(p[9])
        return rx, tx, True
    except Exception:
        pass
    # /sys/class/net fallback
    for iface_path in glob.glob("/sys/class/net/*"):
        iface = os.path.basename(iface_path)
        if iface == "lo":
            continue
        try:
            with open(f"{iface_path}/statistics/rx_bytes") as f:
                rx += int(f.read().strip())
            with open(f"{iface_path}/statistics/tx_bytes") as f:
                tx += int(f.read().strip())
        except Exception:
            continue
    return rx, tx, rx > 0 or tx > 0

def _read_bytes():
    rx, tx, ok = _read_bytes_android()
    if not ok:
        rx, tx, ok = _read_bytes_proc()
    return rx, tx

def _active_iface():
    try:
        with open("/proc/net/wireless") as f:
            for line in f.readlines()[2:]:
                p = line.split()
                if p:
                    return f"WiFi ({p[0].rstrip(':')}) "
    except Exception:
        pass
    for iface_path in sorted(glob.glob("/sys/class/net/*")):
        iface = os.path.basename(iface_path)
        if iface == "lo":
            continue
        try:
            with open(f"{iface_path}/operstate") as f:
                if f.read().strip() == "up":
                    return iface
        except Exception:
            continue
    return "Mobile"

def get_network():
    global _ping_started
    if not _ping_started:
        threading.Thread(target=_ping_worker, daemon=True).start()
        _ping_started = True

    rx, tx   = _read_bytes()
    now      = time.time()
    ping_str = f"{_ping_ms} ms" if _ping_ms is not None else "Pinging..."
    iface    = _active_iface()

    if not _bw:
        _bw.update({"rx": rx, "tx": tx, "t": now,
                    "last_dl": "0 KB/s", "last_ul": "0 KB/s"})
        return {"dl": "0 KB/s", "ul": "0 KB/s",
                "ping": ping_str, "iface": iface}

    dt = now - _bw["t"]
    if dt < 0.5:
        return {"dl": _bw["last_dl"], "ul": _bw["last_ul"],
                "ping": ping_str, "iface": iface}

    dl_bps = (rx - _bw["rx"]) / dt
    ul_bps = (tx - _bw["tx"]) / dt
    dl_str, ul_str = _fmt(dl_bps), _fmt(ul_bps)
    _bw.update({"rx": rx, "tx": tx, "t": now,
                "last_dl": dl_str, "last_ul": ul_str})

    return {"dl": dl_str, "ul": ul_str,
            "ping": ping_str, "iface": iface}