import glob


def get_thermal():
    zones = {}
    max_t = 0.0
    cpu_t = 0.0

    for zone in glob.glob('/sys/class/thermal/thermal_zone*'):
        try:
            ztype = open(zone + '/type').read().strip()
            raw   = open(zone + '/temp').read().strip()
            temp  = round(int(raw) / 1000.0, 1)
            if temp < 1 or temp > 150:
                continue
            zones[ztype] = temp
            if temp > max_t:
                max_t = temp
            if 'cpu' in ztype.lower() and temp > cpu_t:
                cpu_t = temp
        except Exception:
            continue

    top3   = sorted(zones.items(), key=lambda x: x[1], reverse=True)[:3]
    detail = '  '.join('%s:%.0fC' % (k[:9], v) for k, v in top3)

    display = cpu_t if cpu_t > 0 else max_t
    return {
        'pct':      min(100, int(display / 75 * 100)) if display else 0,
        'value':    '%.1f C' % display if display else 'N/A',
        'subtitle': 'CPU %.1f C' % cpu_t if cpu_t else '',
        'detail1':  detail,
    }
