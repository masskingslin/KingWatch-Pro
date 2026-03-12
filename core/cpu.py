import time, os, threading

# Background CPU sampling - never blocks main thread
_cpu_pct   = 0.0
_cpu_lock  = threading.Lock()
_cpu_started = False

def _read_stat():
    with open("/proc/stat") as f:
        parts = f.readline().split()[1:]
    vals  = [int(x) for x in parts]
    idle  = vals[3] + vals[4]
    total = sum(vals)
    return idle, total

def _cpu_worker():
    """Background thread: sample CPU every 2s, store result."""
    global _cpu_pct
    prev = None
    while True:
        try:
            idle, total = _read_stat()
            if prev is not None:
                d_idle  = idle  - prev[0]
                d_total = total - prev[1]
                if d_total > 0:
                    pct = round((1.0 - d_idle / d_total) * 100, 1)
                    with _cpu_lock:
                        _cpu_pct = pct
            prev = (idle, total)
        except Exception:
            pass
        time.sleep(2)

def _ensure_started():
    global _cpu_started
    if not _cpu_started:
        _cpu_started = True
        th = threading.Thread(target=_cpu_worker, daemon=True)
        th.start()
        # Wait one cycle for first real reading
        time.sleep(2.1)

def get_cpu():
    _ensure_started()
    with _cpu_lock:
        return _cpu_pct

def get_cpu_freq():
    paths = [
        "/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq",
        "/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_cur_freq",
        "/sys/devices/system/cpu/cpu4/cpufreq/scaling_cur_freq",  # big core
    ]
    for p in paths:
        try:
            with open(p) as f:
                mhz = int(f.read().strip()) // 1000
                return f"{mhz} MHz"
        except Exception:
            continue
    return "N/A"

def get_cpu_cores():
    return str(os.cpu_count() or 1)

def get_cpu_procs():
    try:
        return str(len([d for d in os.listdir("/proc") if d.isdigit()]))
    except Exception:
        return "--"

def get_cpu_uptime():
    try:
        with open("/proc/uptime") as f:
            secs = float(f.read().split()[0])
        h, rem = divmod(int(secs), 3600)
        m = rem // 60
        return f"{h}h {m:02d}m"
    except Exception:
        pass
    # Android SystemClock fallback via jnius
    try:
        from jnius import autoclass
        sc = autoclass("android.os.SystemClock")
        secs = int(sc.elapsedRealtime() / 1000)
        h, rem = divmod(secs, 3600)
        return f"{h}h {rem//60:02d}m"
    except Exception:
        return "--"
