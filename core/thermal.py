import glob


def get_thermal():

    zones = {}

    for z in glob.glob("/sys/class/thermal/thermal_zone*"):
        try:
            with open(f"{z}/type") as f:
                name = f.read().strip()

            with open(f"{z}/temp") as f:
                raw = int(f.read().strip())

            temp = raw / 1000 if raw > 1000 else raw

            if 10 < temp < 150:
                zones[name] = round(temp, 1)

        except Exception:
            continue

    if not zones:
        return {"max": 0, "cpu": 0, "detail": "No sensors"}

    max_t = max(zones.values())

    cpu_t = max_t
    for k, v in zones.items():
        if "cpu" in k.lower():
            cpu_t = v
            break

    top = sorted(zones.items(), key=lambda x: -x[1])[:3]
    detail = "  ".join(f"{k}:{v}°C" for k, v in top)

    return {
        "max": max_t,
        "cpu": cpu_t,
        "detail": detail,
    }