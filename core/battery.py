"""
KingWatch Pro - core/battery.py
Battery stats via Android BatteryManager (pyjnius) with plyer fallback.
No psutil.
"""


def _read_sys_battery(key: str, default=None):
    """Read a value from /sys/class/power_supply/battery/<key>."""
    paths = [
        f"/sys/class/power_supply/battery/{key}",
        f"/sys/class/power_supply/BAT0/{key}",
        f"/sys/class/power_supply/BAT1/{key}",
    ]
    for p in paths:
        try:
            with open(p) as f:
                return f.read().strip()
        except Exception:
            continue
    return default


def get_battery() -> dict:
    # ---- percentage ----
    pct = 0
    try:
        pct = int(_read_sys_battery("capacity", "0"))
    except Exception:
        pass

    # ---- temperature (tenths of degC) ----
    temp_str = "N/A"
    try:
        raw = int(_read_sys_battery("temp", "0"))
        temp_str = f"{raw / 10:.1f}C"
    except Exception:
        pass

    # ---- voltage (uV -> mV) ----
    volt_str = "N/A"
    try:
        raw = int(_read_sys_battery("voltage_now", "0"))
        volt_str = f"{raw // 1000} mV"
    except Exception:
        pass

    # ---- current (uA -> mA, negative = discharging) ----
    current_str = "N/A"
    power_str   = "N/A"
    try:
        cur_ua  = int(_read_sys_battery("current_now", "0"))
        cur_ma  = abs(cur_ua) // 1000
        current_str = f"{cur_ma} mA"
        # Power = V * I  (mW)
        if volt_str != "N/A":
            v_mv = int(_read_sys_battery("voltage_now", "0")) // 1000
            power_mw = (v_mv * cur_ma) // 1000
            power_str = f"{power_mw} mW"
    except Exception:
        pass

    # ---- status / ETA ----
    status = _read_sys_battery("status", "Unknown")
    eta    = status if status else "Unknown"

    return {
        "pct":     pct,
        "temp":    temp_str,
        "volt":    volt_str,
        "current": current_str,
        "power":   power_str,
        "eta":     eta,
    }