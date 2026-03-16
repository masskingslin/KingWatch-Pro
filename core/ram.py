def get_ram():

    try:

        mem = {}

        with open("/proc/meminfo") as f:
            for line in f:
                p = line.split()
                mem[p[0].replace(":", "")] = int(p[1])

        total = mem["MemTotal"]
        avail = mem.get("MemAvailable", mem["MemFree"])

        used = total - avail

        pct = round(used / total * 100, 1)

        used_mb = used // 1024
        total_mb = total // 1024

        return pct, f"{used_mb}MB / {total_mb}MB"

    except:
        return 0, "N/A"