import glob, os

def _find_base():
    """Try every known Android battery sysfs path."""
    candidates = [
        "/sys/class/power_supply/battery",
        "/sys/class/power_supply/Battery",
        "/sys/class/power_supply/BAT0",
        "/sys/class/power_supply/BAT1",
    ]
    for b in candidates:
        if os.path.isdir(b):
            return b

    # Glob fallback — find ANY supply with a capacity file
    for g in glob.glob("/sys/class/power_supply/*"):
        if os.path.exists(os.path.join(g, "capacity")):
            # Skip USB/AC/wireless charger nodes
            btype_path = os.path.join(g, "type")
            try:
                with open(btype_path) as f:
                    btype = f.read().strip().lower()
                if "battery" in btype:
                    return g
            except Exception:
                return g   # No type file — assume it's battery
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
    result = {
        "pct": 0.0, "status": "Unknown",
        "cur": "N/A", "volt": "N/A",
        "power": "N/A", "temp": "N/A", "eta": "N/A"
    }

    base = _find_base()

    # Fallback to plyer if no sysfs
    if not base:
        try:
            from plyer import battery as pb
            info = pb.status
            if info:
                result["pct"]    = float(info.get("percentage") or 0)
                result["status"] = "Charging" if info.get("isCharging") else "Discharging"
        except Exception:
            pass
        return result

    # Capacity — try multiple file names
    for cap_key in ["capacity", "charge_counter"]:
        cap_raw = _read(base, cap_key)
        if cap_raw:
            try:
                v = float(cap_raw)
                # charge_counter is in µAh — convert to %
                if cap_key == "charge_counter":
                    full_raw = _read(base, "charge_full") or _read(base, "charge_full_design")
                    if full_raw:
                        v = round(v / int(full_raw) * 100, 1)
                    else:
                        continue
                if 0 <= v <= 100:
                    result["pct"] = round(v, 1)
                    break
            except Exception:
                continue

    # Status
    status_raw = _read(base, "status")
    if status_raw:
        result["status"] = status_raw

    # Current — try both signs and both keys
    cur_ma = None
    for cur_key in ["current_now", "current_avg"]:
        cur_raw = _read(base, cur_key)
        if cur_raw:
            try:
                raw_val = int(cur_raw)
                # Some devices report in µA, some in mA
                if abs(raw_val) > 100000:
                    cur_ma = abs(raw_val) / 1000.0  # µA → mA
                elif abs(raw_val) > 0:
                    cur_ma = float(abs(raw_val))
                if cur_ma and cur_ma > 0:
                    sign = "+" if "Charg" in result["status"] else "-"
                    result["cur"] = f"{sign}{cur_ma:.0f} mA"
                    break
            except Exception:
                continue

    # Voltage µV → V
    volt_raw = _read(base, "voltage_now")
    volt_v = None
    if volt_raw:
        try:
            raw_v = int(volt_raw)
            volt_v = raw_v / 1_000_000.0 if raw_v > 10000 else raw_v / 1000.0
            result["volt"] = f"{volt_v:.2f} V"
        except Exception:
            pass

    # Power
    if cur_ma and volt_v:
        result["power"] = f"{cur_ma * volt_v / 1000:.2f} W"

    # Temperature (tenths of °C)
    temp_raw = _read(base, "temp")
    if temp_raw:
        try:
            t = int(temp_raw)
            result["temp"] = f"{t/10.0:.1f}°C" if abs(t) > 100 else f"{float(t):.1f}°C"
        except Exception:
            pass

    # ETA
    full_raw = _read(base, "charge_full") or _read(base, "charge_full_design")
    if cur_ma and cur_ma > 0 and full_raw:
        try:
            full_mah = int(full_raw) / 1000.0
            pct = result["pct"]
            if "Charg" in result["status"]:
                result["eta"] = _fmt_time((100 - pct) / 100 * full_mah / cur_ma * 60)
            else:
                result["eta"] = _fmt_time(pct / 100 * full_mah / cur_ma * 60)
        except Exception:
            pass

    return result
