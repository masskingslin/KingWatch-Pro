import glob, os, time

def _sysfs_base():
    for b in ["/sys/class/power_supply/battery",
              "/sys/class/power_supply/Battery",
              "/sys/class/power_supply/BAT0",
              "/sys/class/power_supply/BAT1"]:
        if os.path.isdir(b):
            return b
    for g in glob.glob("/sys/class/power_supply/*"):
        if os.path.exists(os.path.join(g, "capacity")):
            try:
                with open(os.path.join(g, "type")) as f:
                    if "battery" in f.read().strip().lower():
                        return g
            except Exception:
                return g
    return None

def _read(base, *keys):
    for key in keys:
        try:
            with open(os.path.join(base, key)) as f:
                v = f.read().strip()
                if v:
                    return v
        except Exception:
            continue
    return None

def _fmt_time(mins):
    if not mins or mins <= 0:
        return "N/A"
    h, m = divmod(int(mins), 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"

def _eta_from_current(base, pct, charging):
    """Calculate ETA using actual current draw from sysfs."""
    full_raw = _read(base, "charge_full", "charge_full_design")
    cur_raw  = _read(base, "current_now", "current_avg")
    if not cur_raw or not full_raw:
        return None, None
    try:
        cur_ua  = abs(int(cur_raw))
        cur_ma  = cur_ua / 1000.0 if cur_ua > 100000 else float(cur_ua)
        full_mah = int(full_raw) / 1000.0
        if cur_ma <= 0:
            return None, cur_ma
        if charging:
            mins = (100 - pct) / 100.0 * full_mah / cur_ma * 60
        else:
            mins = pct / 100.0 * full_mah / cur_ma * 60
        return _fmt_time(mins), cur_ma
    except Exception:
        return None, None

def _eta_simple(pct, charging):
    """Fallback ETA: ~8 min per % (typical phone)."""
    mins = (100 - pct) * 8 if charging else pct * 8
    return _fmt_time(mins)

def get_battery():
    result = {
        "pct": 0.0, "status": "Unknown",
        "cur": "N/A", "volt": "N/A",
        "power": "N/A", "temp": "N/A",
        "eta": "N/A", "eta_label": "Until full" 
    }

    base     = _sysfs_base()
    pct      = 0.0
    charging = False

    # ── Capacity + Status ────────────────────────────────────
    # Try plyer first (most reliable on Android)
    try:
        from plyer import battery as pb
        info = pb.status
        if info:
            pct      = float(info.get("percentage") or 0)
            charging = bool(info.get("isCharging"))
            result["pct"]    = pct
            result["status"] = "Charging" if charging else "Discharging"
    except Exception:
        if base:
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

    # ETA label changes based on state
    result["eta_label"] = "Until full" if charging else "Until empty"

    if not base:
        result["eta"] = _eta_simple(pct, charging)
        return result

    # ── Current (µA → mA) ────────────────────────────────────
    cur_ma = None
    cur_raw = _read(base, "current_now", "current_avg")
    if cur_raw:
        try:
            v = abs(int(cur_raw))
            cur_ma = v / 1000.0 if v > 100000 else float(v)
            if cur_ma > 0:
                sign = "+" if charging else "-"
                result["cur"] = f"{sign}{cur_ma:.0f} mA"
        except Exception:
            pass

    # ── Voltage (µV → V) ─────────────────────────────────────
    volt_v = None
    volt_raw = _read(base, "voltage_now")
    if volt_raw:
        try:
            v = int(volt_raw)
            volt_v = v / 1_000_000.0 if v > 10000 else v / 1000.0
            result["volt"] = f"{volt_v:.2f} V"
        except Exception:
            pass

    # ── Power ────────────────────────────────────────────────
    if cur_ma and volt_v and cur_ma > 0:
        result["power"] = f"{cur_ma * volt_v / 1000:.2f} W"

    # ── Temperature ──────────────────────────────────────────
    temp_raw = _read(base, "temp")
    if temp_raw:
        try:
            t = int(temp_raw)
            result["temp"] = f"{t/10.0:.1f}°C" if abs(t) > 100 else f"{float(t):.1f}°C"
        except Exception:
            pass

    # ── ETA — precise if current available, else simple ──────
    if cur_ma and cur_ma > 0:
        full_raw = _read(base, "charge_full", "charge_full_design")
        if full_raw:
            try:
                full_mah = int(full_raw) / 1000.0
                if charging:
                    mins = (100 - pct) / 100.0 * full_mah / cur_ma * 60
                else:
                    mins = pct / 100.0 * full_mah / cur_ma * 60
                result["eta"] = _fmt_time(mins)
            except Exception:
                result["eta"] = _eta_simple(pct, charging)
        else:
            result["eta"] = _eta_simple(pct, charging)
    else:
        result["eta"] = _eta_simple(pct, charging)

    return result
