import glob, os

def _fmt_eta(pct, charging):
    """Simple ETA estimate when sysfs current is unavailable."""
    if charging:
        mins = (100 - pct) * 8   # ~8 min per %
    else:
        mins = pct * 8
    if mins <= 0:
        return "N/A"
    h, m = divmod(int(mins), 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"

def _sysfs_base():
    for b in ["/sys/class/power_supply/battery",
              "/sys/class/power_supply/Battery",
              "/sys/class/power_supply/BAT0",
              "/sys/class/power_supply/BAT1"]:
        if os.path.isdir(b):
            return b
    for g in glob.glob("/sys/class/power_supply/*"):
        cap = os.path.join(g, "capacity")
        typ = os.path.join(g, "type")
        if os.path.exists(cap):
            try:
                with open(typ) as f:
                    if "battery" in f.read().strip().lower():
                        return g
            except Exception:
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
    h, m = divmod(int(mins), 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"

def get_battery():
    result = {
        "pct": 0.0, "status": "Unknown",
        "cur": "N/A", "volt": "N/A",
        "power": "N/A", "temp": "N/A", "eta": "N/A"
    }

    # ── Method 1: plyer (most reliable on Android) ──────────
    try:
        from plyer import battery as pb
        info = pb.status
        if info:
            pct     = float(info.get("percentage") or 0)
            charging = bool(info.get("isCharging"))
            result["pct"]    = pct
            result["status"] = "Charging" if charging else "Discharging"
            result["eta"]    = _fmt_eta(pct, charging)
            # Try to enrich from sysfs even if plyer worked
            base = _sysfs_base()
            if base:
                _enrich(result, base)
            return result
    except Exception:
        pass

    # ── Method 2: sysfs direct ──────────────────────────────
    base = _sysfs_base()
    if not base:
        return result

    # Capacity
    cap_raw = _read(base, "capacity")
    if cap_raw:
        try:
            result["pct"] = round(float(cap_raw), 1)
        except Exception:
            pass

    # Status
    status_raw = _read(base, "status")
    if status_raw:
        result["status"] = status_raw

    # Estimate ETA from capacity alone if sysfs current unavailable
    charging = "Charg" in result["status"]
    result["eta"] = _fmt_eta(result["pct"], charging)

    _enrich(result, base)
    return result


def _enrich(result, base):
    """Add current, voltage, power, temp, precise ETA from sysfs."""
    charging = "Charg" in result["status"]

    # Current (µA or mA)
    cur_ma = None
    for key in ["current_now", "current_avg"]:
        raw = _read(base, key)
        if raw:
            try:
                v = abs(int(raw))
                cur_ma = v / 1000.0 if v > 100000 else float(v)
                sign = "+" if charging else "-"
                result["cur"] = f"{sign}{cur_ma:.0f} mA"
                break
            except Exception:
                continue

    # Voltage (µV → V)
    volt_v = None
    raw = _read(base, "voltage_now")
    if raw:
        try:
            v = int(raw)
            volt_v = v / 1_000_000.0 if v > 10000 else v / 1000.0
            result["volt"] = f"{volt_v:.2f} V"
        except Exception:
            pass

    # Power
    if cur_ma and volt_v:
        result["power"] = f"{cur_ma * volt_v / 1000:.2f} W"

    # Temperature
    raw = _read(base, "temp")
    if raw:
        try:
            t = int(raw)
            result["temp"] = f"{t/10.0:.1f}°C" if abs(t) > 100 else f"{float(t):.1f}°C"
        except Exception:
            pass

    # Precise ETA using current + full capacity
    full_raw = _read(base, "charge_full") or _read(base, "charge_full_design")
    if cur_ma and cur_ma > 0 and full_raw:
        try:
            full_mah = int(full_raw) / 1000.0
            pct = result["pct"]
            if charging:
                result["eta"] = _fmt_time((100 - pct) / 100 * full_mah / cur_ma * 60)
            else:
                result["eta"] = _fmt_time(pct / 100 * full_mah / cur_ma * 60)
        except Exception:
            pass