import glob

_ZONE_TYPES = {}

def _load_zone_types():
    global _ZONE_TYPES
    _ZONE_TYPES = {}
    for zone in glob.glob("/sys/class/thermal/thermal_zone*"):
        try:
            with open(f"{zone}/type") as f:
                ztype = f.read().strip()
            with open(f"{zone}/temp") as f:
                raw = int(f.read().strip())
            temp = raw / 1000.0 if raw > 1000 else float(raw)
            if 10 < temp < 150:
                _ZONE_TYPES[ztype] = round(temp, 1)
        except Exception:
            continue

def get_thermal():
    """Returns (max_temp, cpu_temp, detail_str)"""
    _load_zone_types()
    if not _ZONE_TYPES:
        return 0.0, 0.0, "No sensors"

    # Try to find CPU zone
    cpu_temp = None
    for key in ["cpu", "cpu-thermal", "cpu0", "soc", "tsens_tz_sensor0"]:
        for zname, t in _ZONE_TYPES.items():
            if key in zname.lower():
                cpu_temp = t
                break
        if cpu_temp:
            break

    max_temp  = max(_ZONE_TYPES.values())
    cpu_temp  = cpu_temp or max_temp

    # Build compact detail: top 3 zones
    top3 = sorted(_ZONE_TYPES.items(), key=lambda x: -x[1])[:3]
    detail = "  ".join(f"{k[:8]}:{v}°" for k, v in top3)

    return max_temp, cpu_temp, detail
