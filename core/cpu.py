import time
import os
import threading
import glob

_cpu_pct     = 0.0
_cpu_lock    = threading.Lock()
_cpu_started = False


def _read_stat():
    with open('/proc/stat') as f:
        parts = f.readline().split()
    vals  = [int(x) for x in parts[1:]]
    idle  = vals[3]
    total = sum(vals)
    return idle, total


def _get_all_freqs():
    freqs = []
    for i in range(32):
        base = '/sys/devices/system/cpu/cpu%d/cpufreq/' % i
        for name in ('scaling_cur_freq', 'cpuinfo_cur_freq'):
            try:
                freqs.append(int(open(base + name).read().strip()))
                break
            except Exception:
                pass
    return freqs


def _get_max_freqs():
    maxf = []
    for i in range(32):
        p = '/sys/devices/system/cpu/cpu%d/cpufreq/cpuinfo_max_freq' % i
        try:
            maxf.append(int(open(p).read().strip()))
        except Exception:
            pass
    return maxf


def _cpu_via_freq():
    try:
        cur  = _get_all_freqs()
        maxf = _get_max_freqs()
        loads = [min(100, max(0, round(c / m * 100, 1)))
                 for c, m in zip(cur, maxf) if m > 0]
        return round(sum(loads) / len(loads), 1) if loads else 0.0
    except Exception:
        return 0.0


def _cpu_worker():
    global _cpu_pct
    try:
        prev_idle, prev_total = _read_stat()
    except Exception:
        prev_idle, prev_total = 0, 1

    while True:
        time.sleep(1.0)
        try:
            idle, total = _read_stat()
            d_idle  = idle  - prev_idle
            d_total = total - prev_total
            pct = round(100 * (1 - d_idle / d_total), 2) if d_total > 0 else _cpu_via_freq()
            prev_idle, prev_total = idle, total
            with _cpu_lock:
                _cpu_pct = max(0.0, min(100.0, pct))
        except Exception:
            with _cpu_lock:
                _cpu_pct = _cpu_via_freq()


def _ensure_started():
    global _cpu_started
    if not _cpu_started:
        _cpu_started = True
        threading.Thread(target=_cpu_worker, daemon=True).start()


def get_cpu():
    _ensure_started()
    with _cpu_lock:
        return _cpu_pct


def get_cpu_freq():
    try:
        freqs = _get_all_freqs()
        return '%d MHz' % (sum(freqs) // len(freqs) // 1000)
    except Exception:
        return 'N/A'


def get_cpu_cores():
    online = []
    for i in range(32):
        p = '/sys/devices/system/cpu/cpu%d/online' % i
        try:
            if open(p).read().strip() == '1':
                online.append(i)
        except Exception:
            pass
    total = os.cpu_count() or len(online) or 1
    return '%d/%d' % (len(online), total)


def get_cpu_procs():
    try:
        return str(len([d for d in os.listdir('/proc') if d.isdigit()]))
    except Exception:
        return '--'


def get_cpu_uptime():
    try:
        secs = float(open('/proc/uptime').read().split()[0])
        h, rem = divmod(int(secs), 3600)
        return '%dh %02dm' % (h, rem // 60)
    except Exception:
        pass
    try:
        from jnius import autoclass
        ms = autoclass('android.os.SystemClock').elapsedRealtime()
        h, rem = divmod(ms // 1000, 3600)
        return '%dh %02dm' % (h, rem // 60)
    except Exception:
        return '--'
