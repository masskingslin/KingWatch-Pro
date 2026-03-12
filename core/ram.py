def get_ram():
    try:
        mem = {}
        with open("/proc/meminfo") as f:
            for line in f:
                p = line.split()
                if len(p) >= 2:
                    mem[p[0].rstrip(":")] = int(p[1])
        total = mem.get("MemTotal", 1)
        avail = mem.get("MemAvailable", mem.get("MemFree", 0))
        pct   = round((total - avail) / total * 100, 1)
        used  = round((total - avail) / 1024)
        tot   = round(total / 1024)
        return pct, f"{used} MB / {tot} MB"
    except Exception:
        return 0.0, "N/A"
