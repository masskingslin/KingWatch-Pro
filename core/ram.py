def get_ram():
    mem = {}
    try:
        with open('/proc/meminfo') as f:
            for line in f:
                p = line.split()
                if len(p) >= 2:
                    mem[p[0].rstrip(':')] = int(p[1])
    except Exception:
        return {'pct': 0, 'value': 'N/A', 'subtitle': '', 'detail1': ''}

    total = mem.get('MemTotal', 0)
    avail = mem.get('MemAvailable', mem.get('MemFree', 0))

    if total == 0:
        return {'pct': 0, 'value': 'N/A', 'subtitle': '', 'detail1': ''}

    used = total - avail
    pct  = round(used / total * 100)
    usd  = round(used  / 1024)
    tot  = round(total / 1024)

    return {
        'pct':      pct,
        'value':    '%.0f%%' % pct,
        'subtitle': '%d MB' % usd,
        'detail1':  '%d MB / %d MB' % (usd, tot),
    }
