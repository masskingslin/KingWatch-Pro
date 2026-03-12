import time, socket, threading, os, glob

# Background ping state
_ping_ms      = None
_ping_started = False

def _ping_worker():
    global _ping_ms
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            t0 = time.time()
            s.connect(("8.8.8.8", 53))
            s.close()
            _ping_ms = round((time.time() - t0) * 1000, 1)
        except Exception:
            _ping_ms = None
        time.sleep(5)

_bw_state = {}

def _read_bytes():
    rx = tx = 0
    try:
        with open("/proc/net/dev") as f:
            for line in f.readlines()[2:]:
                p = line.split()
                if len(p) < 10 or p[0].rstrip(":") == "lo":
                    continue
                rx += int(p[1])
                tx += int(p[9])
    except Exception:
        pass
    return rx, tx

def _fmt(bps):
    kbps = bps / 1024
    if kbps >= 1024:
        return f"{kbps/1024:.1f} MB/s"
    if kbps < 0.1:
        return "0 KB/s"
    return f"{kbps:.1f} KB/s"

def _iface_name():
    try:
        with open("/proc/net/wireless") as f:
            lines = f.readlines()
        for line in lines[2:]:
            p = line.split()
            if p:
                return f"WiFi ({p[0].rstrip(':')})"
    except Exception:
        pass
    # Check active non-lo interfaces
    for iface_path in glob.glob("/sys/class/net/*"):
        iface = os.path.basename(iface_path)
        if iface == "lo":
            continue
        try:
            with open(f"{iface_path}/carrier") as f:
                if f.read().strip() == "1":
                    return iface
        except Exception:
            continue
    return "Mobile"

def get_network():
    global _ping_started
    if not _ping_started:
        th = threading.Thread(target=_ping_worker, daemon=True)
        th.start()
        _ping_started = True

    rx, tx = _read_bytes()
    now    = time.time()

    if not _bw_state:
        _bw_state.update({"rx": rx, "tx": tx, "t": now})
        return {
            "dl": "0 KB/s", "ul": "0 KB/s",
            "ping": "Pinging...", "iface": _iface_name()
        }

    dt     = max(now - _bw_state["t"], 0.1)
    dl_bps = (rx - _bw_state["rx"]) / dt
    ul_bps = (tx - _bw_state["tx"]) / dt
    _bw_state.update({"rx": rx, "tx": tx, "t": now})

    return {
        "dl":    _fmt(dl_bps),
        "ul":    _fmt(ul_bps),
        "ping":  f"{_ping_ms} ms" if _ping_ms is not None else "N/A",
        "iface": _iface_name()
    }
