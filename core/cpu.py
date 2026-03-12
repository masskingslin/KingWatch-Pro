def get_cpu_usage():
    try:
        with open("/proc/stat", "r") as f:
            fields = f.readline().strip().split()[1:]
            fields = list(map(int, fields))

        idle = fields[3]
        total = sum(fields)

        if not hasattr(get_cpu_usage, "last"):
            get_cpu_usage.last = (idle, total)
            return 0.0

        last_idle, last_total = get_cpu_usage.last
        get_cpu_usage.last = (idle, total)

        diff_idle = idle - last_idle
        diff_total = total - last_total

        if diff_total == 0:
            return 0.0

        return 100.0 * (1.0 - diff_idle / diff_total)
    except:
        return 0.0