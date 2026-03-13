def get_ram():
    with open("/proc/meminfo") as f:
        meminfo = f.read()

    lines = meminfo.split("\n")

    total = int(lines[0].split()[1])
    free = int(lines[1].split()[1])
    buffers = int(lines[3].split()[1])
    cached = int(lines[4].split()[1])

    used = total - free - buffers - cached

    pct = used / total * 100

    return round(pct,1), used, total