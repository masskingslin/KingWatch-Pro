"""
KingWatch Pro v17 - core/battery.py
Full battery stats: pct, temp, voltage, current, power,
charging/discharging ETA via capacity_level + charge_full.
"""
import time

_prev_pct  = -1
_prev_time = 0.0
_eta_cache = "Unknown"


def _sys(key, default=None):
    for prefix in ("battery", "BAT0", "BAT1", "bms", "main-battery"):
        try:
            with open(f"/sys/class/power_supply/{prefix}/{key}") as f:
                return f.read().strip()
        except Exception:
            continue
    return default


def _int(val, default=0):
    try:
        return int(val)
    except Exception:
        return default


def _eta_string(pct, status):
    """Estimate charge/discharge time from capacity drain rate."""
    global _prev_pct, _prev_time, _eta_cache
    now = time.monotonic()

    if _prev_pct < 0:
        _prev_pct  = pct
        _prev_time = now
        return status

    elapsed = now - _prev_time
    delta   = pct - _prev_pct   # positive = charging, negative = draining

    # Only update ETA every 60s
    if elapsed >= 60 and delta != 0:
        rate_per_min = abs(delta) / (elapsed / 60)
        if rate_per_min > 0:
            if delta > 0:
                mins_left = (100 - pct) / rate_per_min
                h, m = divmod(int(mins_left), 60)
                _eta_cache = f"Full in {h}h {m:02d}m" if h > 0 else f"Full in {m}m"
            else:
                mins_left = pct / rate_per_min
                h, m = divmod(int(mins_left), 60)
                _eta_cache = f"Empty in {h}h {m:02d}m" if h > 0 else f"Empty in {m}m"
        _prev_pct  = pct
        _prev_time = now

    if _eta_cache == "Unknown":
        return status
    return _eta_cache


def get_battery() -> dict:
    # Percentage
    pct = _int(_sys("capacity", "0"))

    # Status: Charging / Discharging / Full
    status = _sys("status", "Unknown") or "Unknown"

    # Temperature (tenths of °C)
    temp_str = "N/A"
    try:
        raw = _int(_sys("temp", "0"))
        temp_str = f"{raw / 10:.1f}C"
    except Exception:
        pass

    # Voltage µV → mV
    volt_str = "N/A"
    v_mv = 0
    try:
        raw  = _int(_sys("voltage_now", "0"))
        v_mv = raw // 1000
        volt_str = f"{v_mv} mV"
    except Exception:
        pass

    # Current µA → mA (may be negative when discharging)
    current_str = "N/A"
    power_str   = "N/A"
    try:
        cur_ua  = _int(_sys("current_now", "0"))
        cur_ma  = abs(cur_ua) // 1000
        sign    = "+" if status.lower() == "charging" else "-"
        current_str = f"{sign}{cur_ma} mA"
        if v_mv > 0:
            power_mw  = (v_mv * cur_ma) // 1000
            power_str = f"{power_mw} mW"
    except Exception:
        pass

    eta = _eta_string(pct, status)

    return {
        "pct":     pct,
        "temp":    temp_str,
        "volt":    volt_str,
        "current": current_str,
        "power":   power_str,
        "eta":     eta,
        "status":  status,
    }
