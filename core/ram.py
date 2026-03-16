import os


def get_ram():
    """
    Returns:
        (percentage_used, "used MB / total MB")
    Works on Android and Linux.
    """

    try:
        mem = {}

        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    mem[parts[0].rstrip(":")] = int(parts[1])

        total = mem.get("MemTotal", 0)

        # Android sometimes lacks MemAvailable
        available = mem.get("MemAvailable")

        if available is None:
            free = mem.get("MemFree", 0)
            buffers = mem.get("Buffers", 0)
            cached = mem.get("Cached", 0)
            available = free + buffers + cached

        used = total - available

        if total <= 0:
            return 0.0, "N/A"

        pct = round((used / total) * 100, 1)

        used_mb = int(used / 1024)
        total_mb = int(total / 1024)

        return pct, f"{used_mb} MB / {total_mb} MB"

    except Exception:
        return 0.0, "N/A"