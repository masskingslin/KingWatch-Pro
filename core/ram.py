def get_ram():

    meminfo={}
    with open("/proc/meminfo") as f:
        for line in f:
            k,v=line.split(":")
            meminfo[k]=int(v.strip().split()[0])

    total=meminfo["MemTotal"]
    free=meminfo["MemAvailable"]

    used=total-free

    pct=(used/total)*100

    return {
        "pct":pct,
        "used":f"{used//1024} MB",
        "total":f"{total//1024} MB"
    }