import os


class BatteryMonitor:

    def get(self):
        try:
            path = "/sys/class/power_supply/battery/capacity"
            if os.path.exists(path):
                with open(path) as f:
                    return int(f.read().strip())
        except:
            pass

        return 50