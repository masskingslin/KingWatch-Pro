class RAMMonitor:

    def get(self):
        try:
            with open("/proc/meminfo") as f:
                lines = f.readlines()

            total = int(lines[0].split()[1])
            free = int(lines[1].split()[1])

            used = total - free

            return int((used / total) * 100)

        except:
            return 40