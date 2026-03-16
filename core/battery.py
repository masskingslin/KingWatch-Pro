"""
Battery module — works on Android (via pyjnius) and falls back gracefully
on desktop / emulators.
"""

ASSUMED_CAPACITY_MAH = 4500   # fallback if charge_counter unavailable

# ── Android setup (only runs on device) ───────────────────────────────────
try:
    from jnius import autoclass
    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    BatteryManager = autoclass("android.os.BatteryManager")
    _bm = PythonActivity.mActivity.getSystemService(
        PythonActivity.mActivity.BATTERY_SERVICE
    )
    _ANDROID = True
except Exception:
    _bm = None
    BatteryManager = None
    _ANDROID = False


def _fmt_eta(minutes):
    if minutes <= 0:
        return "Calculating..."
    h = int(minutes // 60)
    m = int(minutes % 60)
    return f"{h}h {m}m" if h > 0 else f"{m}m"


def _android_battery():
    try:
        pct  = _bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
        cur  = _bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CURRENT_NOW)
        volt = _bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_VOLTAGE)

        cur_ma  = abs(cur)  / 1000 if cur  else 0
        volt_v  = volt / 1000      if volt else 0
        power_w = cur_ma * volt_v / 1000 if (cur_ma and volt_v) else 0

        # ETA
        charge_counter = _bm.getIntProperty(
            BatteryManager.BATTERY_PROPERTY_CHARGE_COUNTER
        )
        if charge_counter > 0 and cur_ma > 0:
            eta_min = (charge_counter / 1000) / cur_ma * 60
        elif cur_ma > 0:
            eta_min = (ASSUMED_CAPACITY_MAH * pct / 100) / cur_ma * 60
        else:
            eta_min = pct * 8   # rough fallback

        # Temperature via broadcast receiver intent
        temp_str = "N/A"
        try:
            Intent     = autoclass("android.content.Intent")
            context    = PythonActivity.mActivity
            intent     = context.registerReceiver(
                None,
                autoclass("android.content.IntentFilter")(
                    Intent.ACTION_BATTERY_CHANGED
                )
            )
            temp_raw   = intent.getIntExtra("temperature", 0)
            temp_str   = f"{temp_raw / 10:.1f}°C"
        except Exception:
            pass

        return {
            "pct":     pct,
            "current": f"{cur_ma:.0f} mA",
            "volt":    f"{volt_v:.2f} V",
            "power":   f"{power_w:.2f} W",
            "temp":    temp_str,
            "eta":     _fmt_eta(eta_min),
        }
    except Exception:
        return _fallback()


def _fallback():
    """Desktop / emulator fallback — reads /sys if available."""
    pct = 0
    try:
        import glob
        paths = glob.glob("/sys/class/power_supply/BAT*/capacity")
        if paths:
            with open(paths[0]) as f:
                pct = int(f.read().strip())
    except Exception:
        pass
    return {
        "pct":     pct,
        "current": "N/A",
        "volt":    "N/A",
        "power":   "N/A",
        "temp":    "N/A",
        "eta":     _fmt_eta(pct * 8),
    }


def get_battery():
    """
    Returns dict:
        pct     – battery level 0-100 (int)
        current – e.g. "1450 mA"
        volt    – e.g. "3.94 V"
        power   – e.g. "5.72 W"
        temp    – e.g. "36.5°C"
        eta     – e.g. "4h 32m" or "Charging" or "Calculating..."
    """
    if _ANDROID:
        return _android_battery()
    return _fallback()
