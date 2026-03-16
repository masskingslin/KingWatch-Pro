import os
import time

prev_total = 0
prev_idle = 0

boot = None

def uptime():
    global boot
    if boot is None:
        with open("/proc/stat") as f:
            for line in f:
                if line.startswith("btime"):
                    boot = int(line.split()[1])
    s=int(time.time()-boot)
    h=s//3600
    m=(s%3600)//60
    return f"{h}h {m}m"

def cpu_usage():

    global prev_total, prev_idle

    with open("/proc/stat") as f:
        line=f.readline()

    parts=list(map(int,line.split()[1:]))

    idle=parts[3]
    total=sum(parts)

    if prev_total==0:
        prev_total=total
        prev_idle=idle
        return 0

    diff_total=total-prev_total
    diff_idle=idle-prev_idle

    prev_total=total
    prev_idle=idle

    usage=(1-diff_idle/diff_total)*100
    return usage


def cpu_freq():
    try:
        with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq") as f:
            return int(f.read())//1000
    except:
        return 0


def process_count():
    return len([p for p in os.listdir("/proc") if p.isdigit()])


def get_cpu():

    return {
        "usage":cpu_usage(),
        "freq":cpu_freq(),
        "cores":os.cpu_count(),
        "procs":process_count(),
        "uptime":uptime()
    }