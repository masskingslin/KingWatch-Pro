import time

_last_idle = None
_last_total = None


def get_cpu():
    global _last_idle, _last_total

    try:
        with open("/proc/stat") as f:
            line = f.readline().split()[1:]

        values = list(map(int, line))

        idle = values[3]
        total = sum(values)

        if _last_idle is None:
            _last_idle = idle
            _last_total = total
            return 0.0

        idle_diff = idle - _last_idle
        total_diff = total - _last_total

        _last_idle = idle
        _last_total = total

        if total_diff == 0:
            return 0.0

        cpu = 100 * (1 - idle_diff / total_diff)

        return round(cpu, 1)

    except Exception:
        return 0.0