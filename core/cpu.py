"""
KingWatch Pro v17 - core/cpu.py
CPU usage via /proc/stat delta. No throttle — called at 1s interval by main.
"""
import os

_prev_idle  = 0
_prev_total = 0


def _read_stat():
    try:
        with open("/proc/stat") as f:
            parts = f.readline().split()
        vals  = [int(x) for x in parts[1:]]
        idle  = vals[3] + (vals[4] if len(vals) > 4 else 0)
        total = sum(vals)
        return idle, total
    except Exception:
        return 0, 1


def _cpu_usage() -> float:
    global _prev_idle, _prev_total
    idle, total = _read_stat()
    d_idle  = idle  - _prev_idle
    d_total = total - _prev_total
    _prev_idle  = idle
    _prev_total = total
    if d_total <= 0:
        return 0.0
    return max(0.0, min(100.0, (1.0 - d_idle / d_total) * 100.0))


def _cpu_freq() -> int:
    for p in ("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq",
              "/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_cur_freq"):
        try:
            with open(p) as f:
                return int(f.read().strip()) // 1000
        except Exception:
            continue
    return 0


def _cores() -> int:
    try:
        with open("/proc/cpuinfo") as f:
            return sum(1 for ln in f if ln.startswith("processor"))
    except Exception:
        return os.cpu_count() or 1


def _procs() -> int:
    try:
        return len([d for d in os.listdir("/proc") if d.isdigit()])
    except Exception:
        return 0


def get_cpu() -> dict:
    return {
        "usage": _cpu_usage(),
        "freq":  _cpu_freq(),
        "cores": _cores(),
        "procs": _procs(),
    }
