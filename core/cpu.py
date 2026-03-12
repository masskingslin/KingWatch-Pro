import time

_prev = None

def _read_stat():
    with open("/proc/stat") as f:
        line = f.readline()
    parts = line.split()[1:]
    vals  = [int(x) for x in parts]
    idle  = vals[3] + vals[4]   # idle + iowait
    total = sum(vals)
    return idle, total

def get_cpu():
    global _prev
    try:
        idle, total = _read_stat()

        # First call — seed and do a quick 0.3s sample for real value
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
