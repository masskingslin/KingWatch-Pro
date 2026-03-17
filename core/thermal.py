"""
KingWatch Pro v17 - core/thermal.py
Returns CPU, GPU, Battery temps + max across all zones.
Correctly normalises millidegree vs degree raw values.
"""
import glob, os

_CPU_K  = ("cpu","soc","tsens","cpuss","cluster","core","msm","bcl","cpu-")
_GPU_K  = ("gpu","kgsl","mali")
_BATT_K = ("battery","bms","bat-")


def _label(zt):
    zt = zt.lower()
    for k in ("cpu","gpu","soc","battery","bms","skin","board","modem","npu","ddr"):
        if k in zt:
            return k.upper()
    return zt[:6].upper()


def _read_zones():
    zones = []
    for zd in sorted(glob.glob("/sys/class/thermal/thermal_zone*")):
        try:
            with open(os.path.join(zd,"type")) as f: zt = f.read().strip()
            with open(os.path.join(zd,"temp")) as f: raw = int(f.read().strip())
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
        return {"cpu":0,"gpu":0,"batt":0,"max":0,"detail":"No sensors"}

    cpu_t  = _pick(zones, _CPU_K)  or (zones[0][1] if zones else 0)
    gpu_t  = _pick(zones, _GPU_K)
    batt_t = _pick(zones, _BATT_K)
    max_t  = max(t for _,t in zones)

    parts = [f"CPU {cpu_t}C"]
    if gpu_t:  parts.append(f"GPU {gpu_t}C")
    if batt_t: parts.append(f"Bat {batt_t}C")

    return {
        "cpu":    round(cpu_t, 1),
        "gpu":    round(gpu_t, 1),
        "batt":   round(batt_t, 1),
        "max":    round(max_t, 1),
        "detail": "  ".join(parts),
    }
