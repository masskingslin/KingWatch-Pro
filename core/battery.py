import glob, os

def _r(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except Exception:
        return None

def _find_battery_base():
    # Try named battery paths first
    for name in ["battery", "Battery", "BAT0", "BAT1", "bms", "main-battery"]:
        p = "/sys/class/power_supply/%s" % name
        if os.path.exists(os.path.join(p, "capacity")):
            return p
    # Scan all and pick one with type=Battery
    for g in glob.glob("/sys/class/power_supply/*"):
        t = _r(os.path.join(g, "type")) or ""
        if "battery" in t.lower() or "Battery" in t:
            if os.path.exists(os.path.join(g, "capacity")):
                return g
    # Fallback: any with capacity
    for g in glob.glob("/sys/class/power_supply/*"):
        if os.path.exists(os.path.join(g, "capacity")):
            return g
    return None

def _read(base, *keys):
    for k in keys:
        v = _r(os.path.join(base, k))
        if v and v not in ("0", ""):
            return v
    return None

def _fmt_time(mins):
    if not mins or mins <= 0:
        return "N/A"
    h, m = divmod(int(mins), 60)
    return "%dh %02dm" % (h, m) if h else "%dm" % m

def _parse_current_ua(raw):
    # Android kernel reports in uA. Convert to mA.
    if not raw:
        return None
    try:
        ua = abs(int(raw))
        if ua < 100:
            return None
        return round(ua / 1000.0, 1)
    except Exception:
        return None

def _parse_voltage_uv(raw):
    # Android kernel reports in uV. Convert to V.
    if not raw:
        return None
    try:
        uv = abs(int(raw))
        if uv < 1000:
            return None
        return round(uv / 1000000.0, 3)
    except Exception:
        return None

def _parse_temp(raw):
    # Android kernel reports in tenths of C.
    if not raw:
        return None
    try:
        t = int(raw)
        return round(t / 10.0, 1)
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

    # plyer first (most reliable on Android)
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

    base = _find_battery_base()

    # pct fallback from sysfs
    if result["pct"] == 0.0 and base:
        raw = _read(base, "capacity")
        if raw:
            try:
                pct = float(raw)
                result["pct"] = pct
            except Exception:
                pass

    # status fallback
    if result["status"] == "Unknown" and base:
        s = _read(base, "status")
        if s:
            result["status"] = s
            charging = "Charg" in s

    charging = charging or "Charg" in result["status"]
    result["eta_label"] = "Until full" if charging else "Until empty"

    if not base:
        result["eta"] = _fmt_time((100 - pct) * 8 if charging else pct * 8)
        return result

    # Current - try every known path name
    cur_ma = None
    for key in ["current_now", "current_avg", "batt_current_ua",
                "ChargerStatus", "BatteryCurrent"]:
        raw = _r(os.path.join(base, key))
        cur_ma = _parse_current_ua(raw)
        if cur_ma:
            sign = "+" if charging else "-"
            result["cur"] = "%s%.0f mA" % (sign, cur_ma)
            break

    # Voltage - try every known path name
    volt_v = None
    for key in ["voltage_now", "voltage_ocv", "batt_vol",
                "BatteryVoltage", "voltage_avg"]:
        raw = _r(os.path.join(base, key))
        volt_v = _parse_voltage_uv(raw)
        if volt_v:
            result["volt"] = "%.2f V" % volt_v
            break

    # Power
    if cur_ma and volt_v:
        result["power"] = "%.2f W" % (cur_ma * volt_v / 1000.0)
    else:
        raw = _r(os.path.join(base, "power_now"))
        if raw:
            try:
                pw = abs(int(raw))
                result["power"] = "%.2f W" % (pw / 1000000.0)
            except Exception:
                pass

    # Temperature
    for key in ["temp", "batt_temp", "BatteryTemperature"]:
        t = _parse_temp(_r(os.path.join(base, key)))
        if t:
            result["temp"] = "%.1fC" % t
            break

    # ETA
    full_raw = _read(base, "charge_full", "charge_full_design", "batt_capacity")
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
