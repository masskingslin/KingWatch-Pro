import glob

def get_thermal():

    temps=[]

    for f in glob.glob("/sys/class/thermal/thermal_zone*/temp"):
        try:
            with open(f) as fd:
                t=int(fd.read())
                if t>1000: t/=1000
                temps.append(t)
        except:
            pass

    if not temps:
        return {"max":0,"cpu":0,"detail":"No sensors"}

    return {
        "max":round(max(temps),1),
        "cpu":round(temps[0],1),
        "detail":" ".join([f"{round(t,1)}C" for t in temps[:3]])
    }