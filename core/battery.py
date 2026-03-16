import glob

def read(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except:
        return None

def get_battery():

    base="/sys/class/power_supply"

    for b in glob.glob(base+"/*"):
        if "battery" in b.lower():

            cap=read(b+"/capacity")
            status=read(b+"/status")
            volt=read(b+"/voltage_now")
            curr=read(b+"/current_now")
            temp=read(b+"/temp")

            if volt: volt=str(round(int(volt)/1e6,2))
            else: volt="?"

            if curr: curr=str(int(curr)/1000)
            else: curr="?"

            if temp: temp=str(int(temp)/10)
            else: temp="?"

            return {
                "pct":cap,
                "status":status,
                "volt":volt,
                "current":curr,
                "temp":temp
            }

    return {"pct":0,"status":"Unknown","volt":"?","current":"?","temp":"?"}