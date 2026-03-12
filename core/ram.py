def get_ram():
    try:
        mem = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split()[0].rstrip(":"), line.split()[1]
                mem[k] = int(v)
        total     = mem.get("MemTotal", 1)
        available = mem.get("MemAvailable", mem.get("MemFree", 0))
        return round((total - available) / total * 100, 1)
    except Exception:
        return 0.0