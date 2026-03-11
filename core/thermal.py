import os

class ThermalMonitor:

    def read(self):

        temps = []

        base = "/sys/class/thermal"

        for item in os.listdir(base):
            if "thermal_zone" in item:

                try:
                    with open(f"{base}/{item}/temp") as f:
                        t = int(f.read().strip())/1000
                        temps.append(t)
                except:
                    pass

        if temps:
            return max(temps)

        return 0
