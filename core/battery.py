import glob, os

def _find_all_supply_paths():
    """Return ALL power supply dirs, battery first."""
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
    return f"{h}h {m:02d}m" if h else f"{m}m"

def _parse_current(raw):
    """Return mA (positive) from raw string, auto-detecting units."""
    if not raw:
        return None
    try:
        v = abs(int(raw))
        if v == 0:
            return None
        # µA (microamp) — most common on Android
        if v > 100_000:
            return v / 1000.0
        # mA direct
        if v > 50:
            return float(v)
        # Some devices report in A *1000 oddly
        return float(v)
    except Exception:
        return None

def _parse_voltage(raw):
    """Return volts from raw string."""
    if not raw:
        return None
    try:
        v = int(raw)
        if v > 1_000_000:
            return v / 1_000_000.0   # µV
        if v > 1000:
            return v / 1000.0        # mV
        return float(v)
    except Exception:
        return None

def _parse_temp(raw):
    if not raw:
        return None
    try:
        t = int(raw)
        if abs(t) > 200:
            return t / 10.0   # tenths of °C
        return float(t)
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

    # ── plyer (Android BatteryManager API) ─────────────────
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

    # ── sysfs paths ─────────────────────────────────────────
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
        # Simple ETA estimate
        mins = (100 - pct) * 8 if charging else pct * 8
        result["eta"] = _fmt_time(mins)
        return result

    # ── Current ─────────────────────────────────────────────
    cur_ma = None
    for key in ["current_now", "current_avg", "charge_counter"]:
        raw = _read(base, key)
        cur_ma = _parse_current(raw)
        if cur_ma and cur_ma > 0:
            sign = "+" if charging else "-"
            result["cur"] = f"{sign}{cur_ma:.0f} mA"
            break

    # ── Voltage ─────────────────────────────────────────────
    volt_v = None
    raw = _read(base, "voltage_now", "voltage_ocv")
    volt_v = _parse_voltage(raw)
    if volt_v:
        result["volt"] = f"{volt_v:.2f} V"

    # ── Power ───────────────────────────────────────────────
    if cur_ma and volt_v:
        result["power"] = f"{cur_ma * volt_v / 1000:.2f} W"
    else:
        # Try power_now directly
        raw = _read(base, "power_now")
        if raw:
            try:
                pw = int(raw)
                result["power"] = f"{pw/1_000_000:.2f} W" if pw > 10000 else f"{float(pw):.2f} W"
            except Exception:
                pass

    # ── Temperature ─────────────────────────────────────────
    raw = _read(base, "temp")
    t   = _parse_temp(raw)
    if t:
        result["temp"] = f"{t:.1f}°C"

    # ── ETA ─────────────────────────────────────────────────
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
            mins = (100 - pct) * 8 if charging else pct * 8
            result["eta"] = _fmt_time(mins)
    else:
        mins = (100 - pct) * 8 if charging else pct * 8
        result["eta"] = _fmt_time(mins)

    return result
