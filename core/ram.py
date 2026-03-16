def get_ram():
    """
    Returns (pct: float, display_str: str)
    e.g.  (72.4, "2980MB / 4096MB")
    """
    try:
        mem = {}
        with open("/proc/meminfo") as f:
            for line in f:
                p = line.split()
                if len(p) >= 2:
                    mem[p[0].rstrip(":")] = int(p[1])

        total = mem["MemTotal"]
        avail = mem.get("MemAvailable", mem.get("MemFree", 0))
        used  = total - avail

        pct      = round(used / total * 100, 1) if total else 0
        used_mb  = used  // 1024
        total_mb = total // 1024

        return pct, f"{used_mb}MB / {total_mb}MB"

    except Exception:
        return 0.0, "N/A"
