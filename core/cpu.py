import time

_prev = None

def _read_stat():
    with open("/proc/stat") as f:
        parts = f.readline().split()[1:]
    vals  = [int(x) for x in parts]
    idle  = vals[3] + vals[4]
    total = sum(vals)
    return idle, total

def get_cpu_freq():
    """CPU frequency in MHz."""
    try:
        with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq") as f:
            return "%.0f MHz" % (int(f.read().strip()) / 1000)
    except Exception:
        pass
    try:
        with open("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_cur_freq") as f:
            return "%.0f MHz" % (int(f.read().strip()) / 1000)
    except Exception:
        return "N/A"

def get_cpu_cores():
    import os
    return str(os.cpu_count() or 1)

def get_cpu_procs():
    import os
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
        return f"{h}h {m}m"
    except Exception:
        return "--"

def get_cpu():
    """Returns CPU usage % via /proc/stat delta."""
    global _prev
    try:
        idle, total = _read_stat()

        # First call — do a quick 0.3s real sample
        if _prev is None:
            _prev = (idle, total)
            time.sleep(0.3)
            idle2, total2 = _read_stat()
            d_idle  = idle2 - idle
            d_total = total2 - total
            _prev = (idle2, total2)
            if d_total == 0:
                return 0.0
            return round((1.0 - d_idle / d_total) * 100, 1)

        d_idle  = idle  - _prev[0]
        d_total = total - _prev[1]
        _prev = (idle, total)
        if d_total == 0:
            return 0.0
        return round((1.0 - d_idle / d_total) * 100, 1)
    except Exception:
        return 0.0
