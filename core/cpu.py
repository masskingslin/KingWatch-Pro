"""
KingWatch Pro - core/cpu.py
CPU usage, frequency, core count, process count.
No psutil - reads /proc directly (works on all Android).
"""
import os
import time

# Module-level state for delta calculation
_prev_idle  = 0
_prev_total = 0
_last_read  = 0.0


def _read_proc_stat():
    """Read first line of /proc/stat -> (idle, total)."""
    try:
        with open("/proc/stat") as f:
            parts = f.readline().split()
        # parts: cpu user nice system idle iowait irq softirq ...
        values = [int(x) for x in parts[1:]]
        idle  = values[3] + (values[4] if len(values) > 4 else 0)  # idle + iowait
        total = sum(values)
        return idle, total
    except Exception:
        return 0, 1


def _cpu_usage_pct() -> float:
    global _prev_idle, _prev_total, _last_read
    now = time.monotonic()
    # Throttle reads to once per 0.8s to reduce overhead
    if now - _last_read < 0.8:
        return 0.0
    _last_read = now

    idle, total = _read_proc_stat()
    d_idle  = idle  - _prev_idle
    d_total = total - _prev_total
    _prev_idle  = idle
    _prev_total = total

    if d_total == 0:
        return 0.0
    return max(0.0, min(100.0, (1.0 - d_idle / d_total) * 100.0))


def _cpu_freq_mhz() -> int:
    """Read current CPU frequency from /sys (scaling_cur_freq or cpuinfo_cur_freq)."""
    paths = [
        "/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq",
        "/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_cur_freq",
    ]
    for p in paths:
        try:
            with open(p) as f:
                return int(f.read().strip()) // 1000  # kHz -> MHz
        except Exception:
            continue
    return 0


def _cpu_core_count() -> int:
    try:
        with open("/proc/cpuinfo") as f:
            return sum(1 for line in f if line.startswith("processor"))
    except Exception:
        return os.cpu_count() or 1


def _process_count() -> int:
    try:
        return len([
            d for d in os.listdir("/proc")
            if d.isdigit()
        ])
    except Exception:
        return 0


def get_cpu() -> dict:
    return {
        "usage": _cpu_usage_pct(),
        "freq":  _cpu_freq_mhz(),
        "cores": _cpu_core_count(),
        "procs": _process_count(),
    }