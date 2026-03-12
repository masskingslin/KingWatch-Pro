import os


class ThermalMonitor:

    def get(self):

        try:
            path = "/sys/class/thermal/thermal_zone0/temp"

            if os.path.exists(path):
                with open(path) as f:
                    return int(int(f.read()) / 1000)

        except:
            pass

        return 35