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
    base = _find_base()
    if not base:
        try:
            from plyer import battery
            info = battery.status
            if info:
                pct    = float(info.get("percentage", 0))
                charge = info.get("isCharging", False)
                status = "Charging" if charge else "Discharging"
                return pct, status, "N/A", "N/A", "N/A", "N/A", "N/A"
        except Exception:
            pass
        return 0.0, "Unknown", "N/A", "N/A", "N/A", "N/A", "N/A"

    # Capacity
    cap   = float(_read(base, "capacity") or 0)
    # Status
    status = _read(base, "status") or "Unknown"
    # Current µA → mA
    cur_raw = _read(base, "current_now")
    cur_ma  = round(abs(int(cur_raw)) / 1000, 1) if cur_raw else None
    cur_sign = "+" if "Charg" in status else "-"
    cur_str  = f"{cur_sign}{cur_ma} mA" if cur_ma else "N/A"
    # Voltage µV → V
    volt_raw = _read(base, "voltage_now")
    volt_v   = round(int(volt_raw) / 1_000_000, 2) if volt_raw else None
    volt_str = f"{volt_v} V" if volt_v else "N/A"
    # Power = V × I (mW)
    power_str = "N/A"
    if cur_ma and volt_v:
        mw = round(cur_ma * volt_v / 1000, 2)
        power_str = f"{mw} W"
    # Temperature
    temp_raw = _read(base, "temp")
    temp_c   = round(int(temp_raw) / 10, 1) if temp_raw else None
    temp_str = f"{temp_c}°C" if temp_c else "N/A"
    # ETA
    full_raw = _read(base, "charge_full") or _read(base, "charge_full_design")
    eta_str  = "N/A"
    if cur_ma and cur_ma > 0 and full_raw:
        full_mah = int(full_raw) / 1000
        if "Charg" in status:
            eta_str = _fmt_time((100 - cap) / 100 * full_mah / cur_ma * 60)
        else:
            eta_str = _fmt_time(cap / 100 * full_mah / cur_ma * 60)

    return cap, status, cur_str, volt_str, power_str, temp_str, eta_str
