import time

prev=None

def read_bytes():

    rx=0
    tx=0

    with open("/proc/net/dev") as f:
        for line in f.readlines()[2:]:
            parts=line.split()
            rx+=int(parts[1])
            tx+=int(parts[9])

    return rx,tx


def get_network():

    global prev

    now=time.time()
    rx,tx=read_bytes()

    if prev is None:
        prev=(rx,tx,now)
        return {"dl":"0 KB/s","ul":"0 KB/s","ping":"--","signal":"LTE","pct":0}

    rx0,tx0,t0=prev
    dt=now-t0

    dl=(rx-rx0)/dt/1024
    ul=(tx-tx0)/dt/1024

    prev=(rx,tx,now)

    return {
        "dl":f"{dl:.1f} KB/s",
        "ul":f"{ul:.1f} KB/s",
        "ping":"--",
        "signal":"LTE",
        "pct":min(dl/200*100,100)
    }