import time

class CPUMonitor:

    def __init__(self):
        self.last_total = 0
        self.last_idle = 0

    def read(self):
        with open("/proc/stat","r") as f:
            fields = f.readline().split()

        user,nice,system,idle,iowait,irq,softirq,steal = map(int,fields[1:9])

        idle_all = idle + iowait
        total = user+nice+system+idle+iowait+irq+softirq+steal

        diff_idle = idle_all - self.last_idle
        diff_total = total - self.last_total

        self.last_idle = idle_all
        self.last_total = total

        if diff_total == 0:
            return 0

        return (1 - diff_idle/diff_total) * 100
