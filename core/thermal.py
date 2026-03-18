"""
KingWatch Pro v17 - core/thermal.py
Returns CPU, GPU, Battery temps + their individual safe max limits.
"""
import glob, os

_CPU_K  = ("cpu","soc","tsens","cpuss","cluster","core","msm","bcl")
_GPU_K  = ("gpu","kgsl","mali","pvr")
_BATT_K = ("battery","bms","bat-")

# Safe max temperatures per sensor type
CPU_MAX  = 90.0   # CPU throttles at ~80-90°C
GPU_MAX  = 85.0   # GPU thermal limit
BATT_MAX = 45.0   # Battery safe limit (warn above 45°C)


def _read_zones():
    zones = []
    for zd in sorted(glob.glob("/sys/class/thermal/thermal_zone*")):
        try:
            with open(os.path.join(zd, "type")) as f:
                zt = f.read().strip()
            with open(os.path.join(zd, "temp")) as f:
                raw = int(f.read().strip())
            t = raw / 1000.0 if raw > 1000 else float(raw)
            if 0 < t < 150:
                zones.append((zt, round(t, 1)))
        except Exception:
            continue
    return zones


def _pick(zones, keys):
    for zt, t in zones:
        if any(k in zt.lower() for k in keys):
            return t
    return 0.0


def get_thermal() -> dict:
    zones = _read_zones()
    if not zones:
        return {
            "cpu": 0, "gpu": 0, "batt": 0, "max": 0,
            "cpu_max": CPU_MAX, "gpu_max": GPU_MAX, "batt_max": BATT_MAX,
            "detail": "No sensors"
        }

    cpu_t  = _pick(zones, _CPU_K) or (zones[0][1] if zones else 0)
    gpu_t  = _pick(zones, _GPU_K)
    batt_t = _pick(zones, _BATT_K)
    max_t  = max(t for _, t in zones)

    parts = [f"CPU {cpu_t}C"]
    if gpu_t:  parts.append(f"GPU {gpu_t}C")
    if batt_t: parts.append(f"Bat {batt_t}C")

    return {
        "cpu":      round(cpu_t, 1),
        "gpu":      round(gpu_t, 1),
        "batt":     round(batt_t, 1),
        "max":      round(max_t, 1),
        "cpu_max":  CPU_MAX,
        "gpu_max":  GPU_MAX,
        "batt_max": BATT_MAX,
        "detail":   "  ".join(parts),
    }
