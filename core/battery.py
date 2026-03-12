import glob

def get_battery():
    # /sys/class/power_supply — works on Android
    for pattern in [
        "/sys/class/power_supply/battery/capacity",
        "/sys/class/power_supply/Battery/capacity",
        "/sys/class/power_supply/*/capacity",
    ]:
        try:
            paths = glob.glob(pattern)
            for p in paths:
                with open(p) as f:
                    v = int(f.read().strip())
                if 0 <= v <= 100:
                    return float(v)
        except Exception:
            continue
    try:
        from plyer import battery
        info = battery.status
        if info and info.get("percentage") is not None:
            return round(float(info["percentage"]), 1)
    except Exception:
        pass
    return 0.0