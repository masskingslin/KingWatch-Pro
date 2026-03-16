def get_ram():

    mem = {}

    try:
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":")
                mem[k] = int(v.split()[0])

        total = mem["MemTotal"]
        free = mem["MemAvailable"]

        used = total - free

        pct = (used / total) * 100

        return {
            "pct": pct,
            "used": f"{used//1024}MB",
            "total": f"{total//1024}MB"
        }

    except:
        return {"pct": 0, "used": "0", "total": "0"}