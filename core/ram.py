def get_ram():
    try:
        mem = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split()[0].rstrip(":"), int(line.split()[1])
                mem[k] = v
        total     = mem.get("MemTotal", 1)
        available = mem.get("MemAvailable", mem.get("MemFree", 0))
        used_pct  = round((total - available) / total * 100, 1)
        used_mb   = round((total - available) / 1024)
        total_mb  = round(total / 1024)
        detail    = f"Used: {used_mb} MB / {total_mb} MB"
        return used_pct, detail
    except Exception:
        return 0.0, ""
