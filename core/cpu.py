import time

_last = None

def get_cpu():
    global _last

    try:
        with open("/proc/stat") as f:
            line = f.readline().split()[1:]

        vals = list(map(int, line))
        idle = vals[3]
        total = sum(vals)

        if _last is None:
            _last = (idle, total)
            return 0.0

        idle_prev, total_prev = _last
        _last = (idle, total)

        diff_idle = idle - idle_prev
        diff_total = total - total_prev

        if diff_total == 0:
            return 0.0

        cpu = 100 * (1 - diff_idle / diff_total)
        return round(cpu, 1)

    except:
        return 0.0