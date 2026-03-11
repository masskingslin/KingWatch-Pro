class RAMMonitor:

    def read(self):
        mem = {}

        with open("/proc/meminfo") as f:
            for line in f:
                parts = line.split()
                mem[parts[0].rstrip(":")] = int(parts[1])

        total = mem["MemTotal"]
        free = mem["MemAvailable"]

        used = total - free

        percent = used / total * 100

        return percent, used, total
