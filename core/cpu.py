"""
KingWatch Pro v17 - core/cpu.py
CPU usage: dual strategy
  1. /proc/stat delta (system-wide, most accurate)
  2. Frequency-based estimate: current_freq / max_freq * 100 (fallback)
CPU arc uses REAL usage%, not frequency%.
Frequency shown as text info only.
"""
import os
import time
import glob

_prev_idle   = 0
_prev_total  = 0
_last_usage  = 0.0
_max_freq    = 0


def _get_max_freq() -> int:
    global _max_freq
    if _max_freq > 0:
        return _max_freq
    for p in glob.glob("/sys/devices/system/cpu/cpu*/cpufreq/cpuinfo_max_freq"):
        try:
            with open(p) as f:
                freq = int(f.read().strip()) // 1000
                if freq > _max_freq:
                    _max_freq = freq
        except Exception:
            continue
    return _max_freq or 3000  # fallback 3GHz


def _get_cur_freq() -> int:
    max_cur = 0
    for p in glob.glob("/sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq"):
        try:
            with open(p) as f:
                freq = int(f.read().strip()) // 1000
                if freq > max_cur:
                    max_cur = freq
        except Exception:
            continue
    if max_cur > 0:
        return max_cur
    for p in ("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq",
              "/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_cur_freq"):
        try:
            with open(p) as f:
                return int(f.read().strip()) // 1000
        except Exception:
            continue
    return 0


def _proc_stat_usage() -> float:
    """Delta-based CPU usage from /proc/stat."""
    global _prev_idle, _prev_total, _last_usage
    try:
        with open("/proc/stat") as f:
            parts = f.readline().split()
        vals   = [int(x) for x in parts[1:]]
        idle   = vals[3] + (vals[4] if len(vals) > 4 else 0)
        total  = sum(vals)
        d_idle  = idle  - _prev_idle
        d_total = total - _prev_total
        _prev_idle  = idle
        _prev_total = total
        if d_total <= 0:
            return _last_usage
        usage = max(0.0, min(99.9, (1.0 - d_idle / d_total) * 100.0))
        # Sanity: reject 100% on first call (delta from 0)
        if _last_usage == 0.0 and usage > 95.0:
            _last_usage = 0.0
            return 0.0
        _last_usage = usage
        return usage
    except Exception:
        return _last_usage


def _freq_based_usage(cur: int) -> float:
    """Frequency-proportional estimate as fallback."""
    mx = _get_max_freq()
    if mx <= 0 or cur <= 0:
        return 0.0
    return min(99.9, (cur / mx) * 100.0)


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
    cur_freq = _get_cur_freq()
    usage    = _proc_stat_usage()

    # If /proc/stat gives 0 but we have frequency, use freq-based
    if usage == 0.0 and cur_freq > 0:
        usage = _freq_based_usage(cur_freq)

    return {
        "usage": usage,
        "freq":  cur_freq,
        "cores": _cores(),
        "procs": _procs(),
        "max_freq": _get_max_freq(),
    }
