import time, os, threading, glob

_cpu_pct    = 0.0
_cpu_lock   = threading.Lock()
_cpu_started = False

# -- Method 1: /proc/stat delta ---------------------------
def _read_stat():
    with open("/proc/stat") as f:
        parts = f.readline().split()[1:]
    vals  = [int(x) for x in parts]
    idle  = vals[3] + vals[4]
    total = sum(vals)
    return idle, total

# -- Method 2: freq x cores estimation -------------------
def _get_all_freqs():
    """Read current freq of every online CPU core."""
    freqs = []
    for i in range(32):
        for fname in ["scaling_cur_freq", "cpuinfo_cur_freq"]:
            p = f"/sys/devices/system/cpu/cpu{i}/cpufreq/{fname}"
            try:
                with open(p) as f:
                    freqs.append(int(f.read().strip()))
                break
            except Exception:
                continue
        else:
            break  # no more cores
    return freqs

def _get_max_freqs():
    maxf = []
    for i in range(32):
        p = f"/sys/devices/system/cpu/cpu{i}/cpufreq/cpuinfo_max_freq"
        try:
            with open(p) as f:
                maxf.append(int(f.read().strip()))
        except Exception:
            break
    return maxf

def _cpu_via_freq():
    """Estimate CPU load as avg(cur_freq / max_freq) across all cores."""
    try:
        cur  = _get_all_freqs()
        maxf = _get_max_freqs()
        if not cur or not maxf:
            return None
        pairs = list(zip(cur, maxf))
        loads = [c / m * 100 for c, m in pairs if m > 0]
        if loads:
            return round(sum(loads) / len(loads), 1)
    except Exception:
        pass
    return None

def _cpu_worker():
    global _cpu_pct
    prev = None
    while True:
        try:
            # Try /proc/stat first
            idle, total = _read_stat()
            if prev is not None:
                d_idle  = idle  - prev[0]
                d_total = total - prev[1]
                if d_total > 0:
                    pct = round((1.0 - d_idle / d_total) * 100, 1)
                    with _cpu_lock:
                        _cpu_pct = pct
                    prev = (idle, total)
                    time.sleep(2)
                    continue
            prev = (idle, total)
        except Exception:
            pass

        # Fallback: freq x cores
        try:
            pct = _cpu_via_freq()
            if pct is not None:
                with _cpu_lock:
                    _cpu_pct = pct
        except Exception:
            pass
        time.sleep(2)

def _ensure_started():
    global _cpu_started
    if not _cpu_started:
        _cpu_started = True
        threading.Thread(target=_cpu_worker, daemon=True).start()

def get_cpu():
    _ensure_started()
    with _cpu_lock:
        return _cpu_pct

def get_cpu_freq():
    try:
        freqs = _get_all_freqs()
        if freqs:
            max_mhz = max(freqs) // 1000
            avg_mhz = sum(freqs) // len(freqs) // 1000
            return f"{max_mhz} MHz"
    except Exception:
        pass
    return "N/A"

def get_cpu_cores():
    try:
        online = []
        for i in range(32):
            p = f"/sys/devices/system/cpu/cpu{i}/online"
            try:
                with open(p) as f:
                    if f.read().strip() == "1":
                        online.append(i)
            except Exception:
                break
        total = os.cpu_count() or 1
        if online:
            return f"{len(online)}/{total}"
        return str(total)
    except Exception:
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
        return f"{h}h {rem//60:02d}m"
    except Exception:
        pass
    try:
        from jnius import autoclass
        sc = autoclass("android.os.SystemClock")
        secs = int(sc.elapsedRealtime() / 1000)
        h, rem = divmod(secs, 3600)
        return f"{h}h {rem//60:02d}m"
    except Exception:
        return "--"
