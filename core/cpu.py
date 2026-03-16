import os
import time

_prev_total = 0
_prev_idle  = 0


def _cpu_usage_pct():
    global _prev_total, _prev_idle
    try:
        with open("/proc/stat") as f:
            line = f.readline()
        parts = list(map(int, line.split()[1:]))
        idle  = parts[3]
        total = sum(parts)
        if _prev_total == 0:
            _prev_total, _prev_idle = total, idle
            return 0.0
        diff_total = total - _prev_total
        diff_idle  = idle  - _prev_idle
        _prev_total, _prev_idle = total, idle
        return round((1 - diff_idle / diff_total) * 100, 1) if diff_total else 0.0
    except Exception:
        return 0.0


def _cpu_freq_mhz():
    try:
        with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq") as f:
            return int(f.read().strip()) // 1000
    except Exception:
        return 0


def _proc_count():
    try:
        return len([p for p in os.listdir("/proc") if p.isdigit()])
    except Exception:
        return 0


def get_cpu():
    """
    Returns dict:
        usage  – CPU usage %  (float)
        freq   – current freq in MHz (int)
        cores  – logical CPU count   (int)
        procs  – running process count (int)
    """
    return {
        "usage": _cpu_usage_pct(),
        "freq":  _cpu_freq_mhz(),
        "cores": os.cpu_count() or 0,
        "procs": _proc_count(),
    }
