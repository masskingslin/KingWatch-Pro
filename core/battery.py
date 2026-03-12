# coding: utf-8
import glob, os

def _find_all_supply_paths():
    battery_paths = []
    other_paths   = []
    for g in glob.glob("/sys/class/power_supply/*"):
        cap = os.path.join(g, "capacity")
        if not os.path.exists(cap):
            continue
        try:
            with open(os.path.join(g, "type")) as f:
                t = f.read().strip().lower()
            if "battery" in t:
                battery_paths.insert(0, g)
            else:
                other_paths.append(g)
        except Exception:
            battery_paths.append(g)
    return battery_paths + other_paths

def _r(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except Exception:
        return None

def _read(base, *keys):
    for k in keys:
        v = _r(os.path.join(base, k))
        if v:
            return v
    return None

def _fmt_time(mins):
    if not mins or mins <= 0:
        return "N/A"
    h, m = divmod(int(mins), 60)
    return "%dh %02dm" % (h, m) if h else "%dm" % m

def _parse_current(raw):
    # Android reports in uA (microamps). Divide by 1000 to get mA.
    if not raw:
        return None
    try:
        ua = abs(int(raw))
        if ua == 0:
            return None
        return round(ua / 1000.0, 1)
    except Exception:
        return None

def _parse_voltage(raw):
    # Android reports in uV (microvolts). Divide by 1000000 to get V.
    if not raw:
        return None
    try:
        uv = int(raw)
        return round(uv / 1000000.0, 3)
    except Exception:
        return None

def _parse_temp(raw):
    # Android reports in tenths of degrees C. Divide by 10.
    if not raw:
        return None
    try:
        return round(int(raw) / 10.0, 1)
    except Exception:
        return None

def get_battery():
    result = {
        "pct": 0.0, "status": "Unknown",
        "cur": "N/A", "volt": "N/A",
        "power": "N/A", "temp": "N/A",
        "eta": "N/A", "eta_label": "ETA"
    }

    pct      = 0.0
    charging = False

    # plyer (Android BatteryManager API)
    try:
        from plyer import battery as pb
        info = pb.status
        if info and info.get("percentage") is not None:
            pct      = float(info["percentage"])
            charging = bool(info.get("isCharging"))
            result["pct"]    = pct
            result["status"] = "Charging" if charging else "Discharging"
    except Exception:
        pass

    # sysfs paths
    paths = _find_all_supply_paths()
    base  = paths[0] if paths else None

    if base and result["pct"] == 0.0:
        raw = _read(base, "capacity")
        if raw:
            try:
                pct = float(raw)
                result["pct"] = pct
            except Exception:
                pass
        status_raw = _read(base, "status")
        if status_raw:
            result["status"] = status_raw
            charging = "Charg" in status_raw

    charging = charging or "Charg" in result["status"]
    result["eta_label"] = "Until full" if charging else "Until empty"

    if not base:
        mins = (100 - pct) * 8 if charging else pct * 8
        result["eta"] = _fmt_time(mins)
        return result

    # Current: uA to mA
    cur_ma = None
    for key in ["current_now", "current_avg"]:
        cur_ma = _parse_current(_read(base, key))
        if cur_ma and cur_ma > 0:
            sign = "+" if charging else "-"
            result["cur"] = "%s%.0f mA" % (sign, cur_ma)
            break

    # Voltage: uV to V
    volt_v = _parse_voltage(_read(base, "voltage_now", "voltage_ocv"))
    if volt_v:
        result["volt"] = "%.2f V" % volt_v

    # Power: mA * V / 1000 = W
    if cur_ma and volt_v:
        result["power"] = "%.2f W" % (cur_ma * volt_v / 1000.0)

    # Temperature: tenths of C to C
    temp = _parse_temp(_read(base, "temp"))
    if temp:
        result["temp"] = "%.1fC" % temp

    # ETA
    full_raw = _read(base, "charge_full", "charge_full_design")
    if cur_ma and cur_ma > 0 and full_raw:
        try:
            full_mah = int(full_raw) / 1000.0
            if charging:
                mins = (100 - pct) / 100.0 * full_mah / cur_ma * 60
            else:
                mins = pct / 100.0 * full_mah / cur_ma * 60
            result["eta"] = _fmt_time(mins)
        except Exception:
            result["eta"] = _fmt_time((100 - pct) * 8 if charging else pct * 8)
    else:
        result["eta"] = _fmt_time((100 - pct) * 8 if charging else pct * 8)

    return result
