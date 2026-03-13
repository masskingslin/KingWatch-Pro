import glob

def get_temp():

    zones = glob.glob("/sys/class/thermal/thermal_zone*/temp")

    temps = []

    for z in zones:
        try:
            with open(z) as f:
                t = int(f.read())/1000
                temps.append(t)
        except:
            pass

    if temps:
        return max(temps)

    return 0