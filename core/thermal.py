"""
KingWatch Pro - core/thermal.py
Thermal zone temperatures from /sys/class/thermal. No psutil.
"""
import glob
import os


def _read_zones() -> list:
    """Return list of (zone_type, temp_celsius) tuples."""
    zones = []
    try:
        for zone_dir in sorted(glob.glob("/sys/class/thermal/thermal_zone*")):
            try:
                type_path = os.path.join(zone_dir, "type")
                temp_path = os.path.join(zone_dir, "temp")
                with open(type_path) as f:
                    zone_type = f.read().strip()
                with open(temp_path) as f:
                    raw = int(f.read().strip())
                # Most zones report in millidegrees
                temp_c = raw / 1000 if raw > 1000 else float(raw)
                if 0 < temp_c < 150:   # sanity check
                    zones.append((zone_type, temp_c))
            except Exception:
                continue
    except Exception:
        pass
    return zones


def get_thermal() -> dict:
    zones = _read_zones()

    if not zones:
        return {
            "cpu":    0,
            "max":    0,
            "detail": "No thermal data",
        }

    # Pick CPU zone first (common names)
    cpu_keywords = ("cpu", "soc", "tsens", "bcl", "core")
    cpu_temp = 0.0
    for ztype, temp in zones:
        if any(k in ztype.lower() for k in cpu_keywords):
            cpu_temp = temp
            break
    if cpu_temp == 0.0 and zones:
        cpu_temp = zones[0][1]

    max_temp = max(t for _, t in zones)

    # Build detail string from top zones (limit to 3)
    detail_parts = [f"{zt}: {t:.0f}C" for zt, t in zones[:3]]
    detail = "  ".join(detail_parts)

    return {
        "cpu":    round(cpu_temp, 1),
        "max":    round(max_temp, 1),
        "detail": detail,
    }