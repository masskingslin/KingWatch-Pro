import time, socket, os, glob, threading

_state   = {}
_ping_ms = None   # updated by background thread

def _ping_worker():
    """Runs in background thread — never blocks main thread."""
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
        time.sleep(5)   # ping every 5 seconds

def _start_ping():
    th = threading.Thread(target=_ping_worker, daemon=True)
    th.start()

_ping_started = False

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
    return f"{kbps:.1f} KB/s"

def _wifi_info():
    try:
        with open("/proc/net/wireless") as f:
            lines = f.readlines()
        for line in lines[2:]:
            parts = line.split()
            if len(parts) >= 4:
                return parts[0].rstrip(":"), parts[2].rstrip(".")
    except Exception:
        pass
    return None, None

def get_network():
    global _ping_started
    if not _ping_started:
        _start_ping()
        _ping_started = True

    rx, tx = _read_bytes()
    now    = time.time()

    if not _state:
        _state.update({"rx": rx, "tx": tx, "t": now})
        return "0 KB/s", "0 KB/s", "0 KB/s", "Pinging...", "Detecting..."

    dt     = max(now - _state["t"], 0.1)
    dl_bps = (rx - _state["rx"]) / dt
    ul_bps = (tx - _state["tx"]) / dt
    _state.update({"rx": rx, "tx": tx, "t": now})

    ping_str = f"{_ping_ms} ms" if _ping_ms is not None else "N/A"

    wifi_iface, wifi_link = _wifi_info()
    signal_str = f"WiFi {wifi_iface}" if wifi_iface else "Mobile/LTE"

    total_str = _fmt(dl_bps + ul_bps)
    return total_str, _fmt(dl_bps), _fmt(ul_bps), ping_str, signal_str
