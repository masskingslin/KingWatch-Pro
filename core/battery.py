import glob, os

def _find_base():
    for b in ["/sys/class/power_supply/battery",
              "/sys/class/power_supply/Battery"]:
        if os.path.isdir(b):
            return b
    for g in glob.glob("/sys/class/power_supply/*"):
        if os.path.exists(os.path.join(g, "capacity")):
            return g
    return None

def _read(base, key):
    try:
        with open(os.path.join(base, key)) as f:
            return f.read().strip()
    except Exception:
        return None

def _fmt_time(mins):
    if not mins or mins <= 0:
        return "N/A"
    h, m = int(mins) // 60, int(mins) % 60
    return f"{h}h {m}m" if h else f"{m}m"

def get_battery():
    """
    Returns dict:
      pct, status, cur_ma, volt_v, power_w, temp_c, eta
    """
    result = {
        "pct": 0.0, "status": "Unknown",
        "cur": "N/A", "volt": "N/A",
        "power": "N/A", "temp": "N/A", "eta": "N/A"
    }
    base = _find_base()
    if not base:
        try:
            from plyer import battery as pb
            info = pb.status
            if info:
                result["pct"]    = float(info.get("percentage", 0))
                result["status"] = "Charging" if info.get("isCharging") else "Discharging"
        except Exception:
            pass
        return result

    # Capacity
    cap_raw = _read(base, "capacity")
    if cap_raw:
        try:
            result["pct"] = float(cap_raw)
        except Exception:
            pass

    # Status
    result["status"] = _read(base, "status") or "Unknown"

    # Current µA → mA
    cur_raw = _read(base, "current_now")
    cur_ma  = None
    if cur_raw:
        try:
            cur_ma = abs(int(cur_raw)) / 1000.0
            sign   = "+" if "Charg" in result["status"] else "-"
            result["cur"] = f"{sign}{cur_ma:.0f} mA"
        except Exception:
            pass

    # Voltage µV → V
    volt_raw = _read(base, "voltage_now")
    volt_v   = None
    if volt_raw:
        try:
            volt_v = int(volt_raw) / 1_000_000.0
            result["volt"] = f"{volt_v:.2f} V"
        except Exception:
            pass

    # Power W
    if cur_ma and volt_v:
        pw = cur_ma * volt_v / 1000.0
        result["power"] = f"{pw:.2f} W"

    # Temperature
    temp_raw = _read(base, "temp")
    if temp_raw:
        try:
            result["temp"] = f"{int(temp_raw)/10.0:.1f}°C"
        except Exception:
            pass

    # ETA
    full_raw = _read(base, "charge_full") or _read(base, "charge_full_design")
    if cur_ma and cur_ma > 0 and full_raw:
        try:
            full_mah = int(full_raw) / 1000.0
            pct = result["pct"]
            if "Charg" in result["status"]:
                eta_min = (100 - pct) / 100 * full_mah / cur_ma * 60
            else:
                eta_min = pct / 100 * full_mah / cur_ma * 60
            result["eta"] = _fmt_time(eta_min)
        except Exception:
            pass

    return result