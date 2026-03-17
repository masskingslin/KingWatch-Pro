"""
KingWatch Pro v17 - core/thermal.py
Thermal zone temperatures - correctly identifies CPU, GPU, battery zones.
Handles both millidegree (>1000) and degree (<= 1000) raw values.
"""
import glob
import os

# Zone name → display label mapping
_LABELS = {
    "cpu":          "CPU",
    "soc":          "SoC",
    "tsens":        "CPU",
    "cpu-1-0":      "CPU0",
    "cpu-1-1":      "CPU1",
    "cpuss":        "CPU",
    "cluster":      "CPU",
    "core":         "Core",
    "gpu":          "GPU",
    "kgsl":         "GPU",
    "mali":         "GPU",
    "battery":      "Batt",
    "bms":          "Batt",
    "charger":      "Chrg",
    "skin":         "Skin",
    "board":        "Board",
    "msm":          "SoC",
    "bcl":          "BCL",
    "pa":           "PA",
    "modem":        "Modem",
    "npu":          "NPU",
    "ddr":          "RAM",
}

_CPU_KEYS  = ("cpu", "soc", "tsens", "cpuss", "cluster", "core", "msm", "bcl")
_GPU_KEYS  = ("gpu", "kgsl", "mali")
_BATT_KEYS = ("battery", "bms")


def _label(zone_type: str) -> str:
    zt = zone_type.lower()
    for key, label in _LABELS.items():
        if key in zt:
            return label
    return zone_type[:8]


def _read_zones():
    zones = []
    for zone_dir in sorted(glob.glob("/sys/class/thermal/thermal_zone*")):
        try:
            with open(os.path.join(zone_dir, "type")) as f:
                zt = f.read().strip()
            with open(os.path.join(zone_dir, "temp")) as f:
                raw = int(f.read().strip())
            # Normalise: millidegrees if > 1000, else raw degrees
            temp_c = raw / 1000.0 if raw > 1000 else float(raw)
            if 0 < temp_c < 150:
                zones.append((zt, temp_c))
        except Exception:
            continue
    return zones


def _pick(zones, keywords):
    for zt, t in zones:
        if any(k in zt.lower() for k in keywords):
            return round(t, 1)
    return None


def get_thermal() -> dict:
    zones = _read_zones()

    if not zones:
        return {"cpu": 0, "gpu": 0, "max": 0, "detail": "No sensors"}

    cpu_t  = _pick(zones, _CPU_KEYS)  or round(zones[0][1], 1)
    gpu_t  = _pick(zones, _GPU_KEYS)
    batt_t = _pick(zones, _BATT_KEYS)
    max_t  = round(max(t for _, t in zones), 1)

    # Build detail line: CPU / GPU / Battery / max
    parts = [f"CPU {cpu_t}C"]
    if gpu_t:
        parts.append(f"GPU {gpu_t}C")
    if batt_t:
        parts.append(f"Batt {batt_t}C")
    parts.append(f"Max {max_t}C")
    detail = "  ".join(parts)

    return {
        "cpu":    cpu_t,
        "gpu":    gpu_t or 0,
        "max":    max_t,
        "detail": detail,
    }
