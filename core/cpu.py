_prev = None

def get_cpu():
    global _prev
    try:
        with open("/proc/stat") as f:
            line = f.readline()
        vals = [int(x) for x in line.split()[1:]]
        idle  = vals[3]
        total = sum(vals)
        if _prev is None:
            _prev = (idle, total)
            return 0.0
        d_idle  = idle  - _prev[0]
        d_total = total - _prev[1]
        _prev = (idle, total)
        if d_total == 0:
            return 0.0
        return round((1 - d_idle / d_total) * 100, 1)
    except Exception:
        return 0.0