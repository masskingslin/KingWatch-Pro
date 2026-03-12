import time

_state = {}

def get_network():
    try:
        rx = tx = 0
        with open("/proc/net/dev") as f:
            for line in f.readlines()[2:]:
                parts = line.split()
                if len(parts) < 10:
                    continue
                iface = parts[0].rstrip(":")
                if iface == "lo":
                    continue
                rx += int(parts[1])
                tx += int(parts[9])
        now = time.time()
        if not _state:
            _state["rx"] = rx
            _state["tx"] = tx
            _state["t"]  = now
            return "0 KB/s"
        dt    = now - _state["t"]
        speed = ((rx - _state["rx"]) + (tx - _state["tx"])) / max(dt, 0.1) / 1024
        _state.update({"rx": rx, "tx": tx, "t": now})
        if speed >= 1024:
            return f"{round(speed/1024,1)} MB/s"
        return f"{round(speed,1)} KB/s"
    except Exception:
        return "N/A"