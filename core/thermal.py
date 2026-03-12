import glob

def get_thermal():
    zones = {}
    for zone in glob.glob("/sys/class/thermal/thermal_zone*"):
        try:
            with open(f"{zone}/type") as f:
                ztype = f.read().strip()
            with open(f"{zone}/temp") as f:
                raw = int(f.read().strip())
            temp = raw / 1000.0 if raw > 1000 else float(raw)
            if 10 < temp < 150:
                zones[ztype] = round(temp, 1)
        except Exception:
            continue
    if not zones:
        return 0.0, 0.0, "No sensors"
    max_t = max(zones.values())
    cpu_t = max_t
    for key in ["cpu", "cpu-thermal", "cpu0", "soc", "tsens_tz_sensor0"]:
        for zname, t in zones.items():
            if key in zname.lower():
                cpu_t = t
                break
    top3   = sorted(zones.items(), key=lambda x: -x[1])[:3]
    detail = "  ".join(f"{k[:9]}:{v}°" for k, v in top3)
    return max_t, cpu_t, detail
