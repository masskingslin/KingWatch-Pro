import time, socket, threading, os, glob, re

# ── Background workers ───────────────────────────────────
_ping_ms      = None
_signal_info  = "Detecting..."
_bg_started   = False

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

def _detect_signal():
    """
    Detect connection type + signal strength.
    Returns string like: "WiFi -65 dBm" / "4G LTE" / "5G" / "Mobile"
    """
    global _signal_info

    while True:
        info = _get_signal_once()
        _signal_info = info
        time.sleep(8)

def _get_signal_once():
    # ── WiFi signal from /proc/net/wireless ─────────────────
    try:
        with open("/proc/net/wireless") as f:
            lines = f.readlines()
        for line in lines[2:]:
            p = line.split()
            if len(p) >= 4:
                iface = p[0].rstrip(":")
                level = p[2].rstrip(".")
                try:
                    dbm = int(float(level))
                    if dbm < 0:
                        quality = "Excellent" if dbm >= -50 else \
                                  "Good"      if dbm >= -65 else \
                                  "Fair"      if dbm >= -75 else "Weak"
                        return f"WiFi {dbm} dBm ({quality})"
                    elif dbm > 0:
                        # Some drivers report 0-100 quality
                        return f"WiFi {dbm}% signal"
                except Exception:
                    pass
    except Exception:
        pass

    # ── Check for WiFi via sysfs ─────────────────────────────
    for path in glob.glob("/sys/class/net/wlan*/"):
        try:
            with open(os.path.join(path, "operstate")) as f:
                if f.read().strip() == "up":
                    return "WiFi Connected"
        except Exception:
            pass

    # ── Mobile data: detect 5G / 4G / 3G via sysfs ──────────
    # Check rmnet (mobile data) interfaces
    rmnet_up = False
    for path in glob.glob("/sys/class/net/rmnet*/"):
        try:
            with open(os.path.join(path, "operstate")) as f:
                if f.read().strip() == "up":
                    rmnet_up = True
                    break
        except Exception:
            pass

    # Try to determine generation from bandwidth
    try:
        with open("/proc/net/dev") as f:
            for line in f.readlines()[2:]:
                p = line.split()
                if "rmnet" in p[0] or "ccmni" in p[0]:
                    rmnet_up = True
                    break
    except Exception:
        pass

    # Read NR (5G) state
    try:
        for p in glob.glob("/sys/class/net/*/type"):
            pass  # probe existence
        # Check for 5G NR indicator files
        nr_paths = glob.glob("/sys/class/telephony/*/nr_state") + \
                   glob.glob("/dev/socket/rild*")
        if nr_paths:
            return "5G NR"
    except Exception:
        pass

    if rmnet_up:
        # Try to guess from speed
        try:
            for path in glob.glob("/sys/class/net/rmnet*/speed"):
                with open(path) as f:
                    speed_mbps = int(f.read().strip())
                if speed_mbps >= 100:
                    return "4G LTE ▲"
                elif speed_mbps >= 10:
                    return "4G"
                elif speed_mbps > 0:
                    return "3G"
        except Exception:
            pass
        return "4G LTE"

    return "Mobile"

# ── Bandwidth ────────────────────────────────────────────
_bw = {}

def _fmt(bps):
    if bps < 0: bps = 0
    kbps = bps / 1024.0
    if kbps >= 1024:
        return f"{kbps/1024:.1f} MB/s"
    return f"{kbps:.1f} KB/s"

def _read_bytes():
    # Android TrafficStats via jnius (best accuracy)
    try:
        from jnius import autoclass
        ts = autoclass("android.net.TrafficStats")
        tx = ts.getTotalTxBytes()
        rx = ts.getTotalRxBytes()
        if tx >= 0 and rx >= 0:
            return rx, tx
    except Exception:
        pass

    # /proc/net/dev fallback
    rx = tx = 0
    try:
        with open("/proc/net/dev") as f:
            for line in f.readlines()[2:]:
                p = line.split()
                if len(p) < 10 or p[0].rstrip(":") == "lo":
                    continue
                rx += int(p[1])
                tx += int(p[9])
        return rx, tx
    except Exception:
        pass

    # /sys/class/net/*/statistics fallback
    for iface_path in glob.glob("/sys/class/net/*"):
        if os.path.basename(iface_path) == "lo":
            continue
        try:
            with open(f"{iface_path}/statistics/rx_bytes") as f:
                rx += int(f.read().strip())
            with open(f"{iface_path}/statistics/tx_bytes") as f:
                tx += int(f.read().strip())
        except Exception:
            continue
    return rx, tx

def get_network():
    global _bg_started
    if not _bg_started:
        _bg_started = True
        threading.Thread(target=_ping_worker, daemon=True).start()
        threading.Thread(target=_detect_signal, daemon=True).start()

    rx, tx   = _read_bytes()
    now      = time.time()
    ping_str = f"{_ping_ms} ms" if _ping_ms is not None else "Pinging..."

    if not _bw:
        _bw.update({"rx": rx, "tx": tx, "t": now,
                    "last_dl": "0 KB/s", "last_ul": "0 KB/s"})
        return {"dl": "0 KB/s", "ul": "0 KB/s",
                "ping": ping_str, "signal": _signal_info}

    dt = now - _bw["t"]
    if dt < 0.5:
        return {"dl": _bw["last_dl"], "ul": _bw["last_ul"],
                "ping": ping_str, "signal": _signal_info}

    dl_bps  = (rx - _bw["rx"]) / dt
    ul_bps  = (tx - _bw["tx"]) / dt
    dl_str  = _fmt(dl_bps)
    ul_str  = _fmt(ul_bps)
    _bw.update({"rx": rx, "tx": tx, "t": now,
                "last_dl": dl_str, "last_ul": ul_str})

    return {"dl": dl_str, "ul": ul_str,
            "ping": ping_str, "signal": _signal_info}
