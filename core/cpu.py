_prev = None

def get_cpu():
    global _prev
    try:
        with open("/proc/stat") as f:
            parts = f.readline().split()[1:]
        vals  = [int(x) for x in parts]
        idle  = vals[3] + vals[4]
        total = sum(vals)
        if _prev is None:
            _prev = (idle, total)
            return 0.0
        d_idle  = idle  - _prev[0]
        d_total = total - _prev[1]
        _prev = (idle, total)
        if d_total == 0:
            return 0.0
        return round((1.0 - d_idle / d_total) * 100, 1)
    except Exception:
        return 0.0