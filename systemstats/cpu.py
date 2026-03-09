import time

last = None

def get_cpu_usage():
    global last

    with open("/proc/stat") as f:
        values = f.readline().split()[1:]

    values = list(map(int, values))

    idle = values[3]
    total = sum(values)

    if last is None:
        last = (idle, total)
        return 0.0

    prev_idle, prev_total = last
    last = (idle, total)

    idle_delta = idle - prev_idle
    total_delta = total - prev_total

    if total_delta == 0:
        return 0

    return (1 - idle_delta / total_delta) * 100
