import os


class CPUMonitor:

    def get(self):
        try:
            load = os.getloadavg()[0]
            return min(int(load * 10), 100)
        except:
            return 25