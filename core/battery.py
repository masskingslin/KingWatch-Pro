"""
KingWatch Pro v17 - core/battery.py
Multi-strategy battery reader:
  1. Android BatteryManager via pyjnius (most accurate)
  2. /sys/class/power_supply fallback
ETA calculated from % drain rate over time.
"""
import time

_prev_pct  = -1
_prev_time = 0.0
_eta_cache = ""

# All known power_supply node names on Android
_PS_NAMES = ["battery", "BAT0", "BAT1", "bms", "main-battery",
             "Battery", "BATTERY"]


def _sys(key):
    for name in _PS_NAMES:
        for base in ["/sys/class/power_supply", "/sys/bus/platform/drivers"]:
            try:
                with open(f"{base}/{name}/{key}") as f:
                    v = f.read().strip()
                    if v:
                        return v
            except Exception:
                continue
    return None


def _int(v, default=0):
    try:
        return int(str(v).strip())
    except Exception:
        return default


def _pyjnius_battery():
    """Read battery via Android BatteryManager broadcast."""
    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Intent         = autoclass("android.content.Intent")
        IntentFilter   = autoclass("android.content.IntentFilter")
        BatteryManager = autoclass("android.os.BatteryManager")
        ctx            = PythonActivity.mActivity

        ifilter = IntentFilter(Intent.ACTION_BATTERY_CHANGED)
        intent  = ctx.registerReceiver(None, ifilter)

        pct     = intent.getIntExtra(BatteryManager.EXTRA_LEVEL, -1)
        scale   = intent.getIntExtra(BatteryManager.EXTRA_SCALE, 100)
        status  = intent.getIntExtra(BatteryManager.EXTRA_STATUS, -1)
        temp    = intent.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, 0)
        volt    = intent.getIntExtra(BatteryManager.EXTRA_VOLTAGE, 0)  # mV

        STATUS_CHARGING    = 2
        STATUS_DISCHARGING = 3
        STATUS_FULL        = 5
        STATUS_NOT_CHARGING = 4

        if status == STATUS_CHARGING:
            status_str = "Charging"
        elif status == STATUS_FULL:
            status_str = "Full"
        elif status == STATUS_NOT_CHARGING:
            status_str = "Not Charging"
        else:
            status_str = "Discharging"

        real_pct = int(pct * 100 / scale) if scale > 0 else pct
        temp_c   = temp / 10.0

        # Current from BatteryManager property
        cur_ma = 0
        try:
            bm = ctx.getSystemService("batterymanager")
            BATTERY_PROPERTY_CURRENT_NOW = 1
            cur_ua = bm.getLongProperty(BATTERY_PROPERTY_CURRENT_NOW)
            cur_ma = abs(cur_ua) // 1000
        except Exception:
            pass

        sign = "+" if status_str == "Charging" else "-"

        return {
            "pct":     real_pct,
            "temp":    f"{temp_c:.1f}C",
            "volt":    f"{volt} mV",
            "current": f"{sign}{cur_ma} mA",
            "power":   f"{volt * cur_ma // 1000} mW" if volt > 0 and cur_ma > 0 else "N/A",
            "status":  status_str,
            "_ok":     True,
        }
    except Exception:
        return {"_ok": False}


def _sys_battery():
    """Fallback: read from /sys/class/power_supply."""
    pct    = _int(_sys("capacity"), 0)
    status = _sys("status") or "Unknown"

    temp_c = 0.0
    try:
        temp_c = _int(_sys("temp"), 0) / 10.0
    except Exception:
        pass

    v_mv = 0
    try:
        raw  = _int(_sys("voltage_now"), 0)
        v_mv = raw // 1000 if raw > 10000 else raw   # uV or mV
    except Exception:
        pass

    cur_ma = 0
    try:
        raw    = _int(_sys("current_now"), 0)
        cur_ma = abs(raw) // 1000 if abs(raw) > 10000 else abs(raw)
    except Exception:
        pass

    sign = "+" if "charg" in status.lower() else "-"
    power = f"{v_mv * cur_ma // 1000} mW" if v_mv > 0 and cur_ma > 0 else "N/A"

    return {
        "pct":     pct,
        "temp":    f"{temp_c:.1f}C",
        "volt":    f"{v_mv} mV" if v_mv else "N/A",
        "current": f"{sign}{cur_ma} mA" if cur_ma else "N/A",
        "power":   power,
        "status":  status,
        "_ok":     True,
    }


def _calc_eta(pct, status):
    global _prev_pct, _prev_time, _eta_cache
    now = time.monotonic()

    if _prev_pct < 0:
        _prev_pct  = pct
        _prev_time = now
        return status

    elapsed = now - _prev_time
    delta   = pct - _prev_pct

    if elapsed >= 60 and delta != 0:
        rate = abs(delta) / (elapsed / 60.0)   # % per minute
        if rate > 0:
            if delta > 0:
                mins = (100 - pct) / rate
                h, m = divmod(int(mins), 60)
                _eta_cache = f"Full ~{h}h{m:02d}m" if h else f"Full ~{m}m"
            else:
                mins = pct / rate
                h, m = divmod(int(mins), 60)
                _eta_cache = f"Empty ~{h}h{m:02d}m" if h else f"Empty ~{m}m"
        _prev_pct  = pct
        _prev_time = now

    return _eta_cache if _eta_cache else status


def get_battery() -> dict:
    d = _pyjnius_battery()
    if not d.get("_ok"):
        d = _sys_battery()

    d["eta"] = _calc_eta(d["pct"], d["status"])
    return d
