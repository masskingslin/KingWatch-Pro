import glob

def get_temp():
    readings = []
    for p in glob.glob("/sys/class/thermal/thermal_zone*/temp"):
        try:
            with open(p) as f:
                v = int(f.read().strip())
            if v > 1000:
                v = v / 1000.0
            if 10 < v < 120:
                readings.append(v)
        except Exception:
            continue
    if readings:
        return round(max(readings), 1)
    return 0.0