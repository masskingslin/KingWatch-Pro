import time
from jnius import autoclass

PythonActivity = autoclass("org.kivy.android.PythonActivity")
BatteryManager = autoclass("android.os.BatteryManager")

context = PythonActivity.mActivity
bm = context.getSystemService(context.BATTERY_SERVICE)

ASSUMED_CAPACITY = 4500  # mAh fallback


def _format_eta(minutes):
    if minutes <= 0:
        return "Calculating..."
    h = int(minutes // 60)
    m = int(minutes % 60)
    if h > 0:
        return f"{h}h {m}m"
    return f"{m}m"


def get_battery():
    try:
        pct = bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
        cur = bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CURRENT_NOW)
        volt = bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_VOLTAGE)

        cur_ma = abs(cur) / 1000 if cur else 0
        volt_v = volt / 1000 if volt else 0
        power = cur_ma * volt_v / 1000 if cur_ma and volt_v else 0

        eta_minutes = 0

        charge_counter = bm.getIntProperty(
            BatteryManager.BATTERY_PROPERTY_CHARGE_COUNTER
        )

        if charge_counter > 0 and cur_ma > 0:
            eta_minutes = (charge_counter / 1000) / cur_ma * 60
        else:
            remaining = ASSUMED_CAPACITY * (pct / 100)
            if cur_ma > 0:
                eta_minutes = remaining / cur_ma * 60
            else:
                eta_minutes = pct * 8

        return {
            "pct": pct,
            "current": f"{cur_ma:.0f} mA",
            "volt": f"{volt_v:.2f} V",
            "power": f"{power:.2f} W",
            "temp": "N/A",
            "eta": _format_eta(eta_minutes),
        }

    except Exception:
        return {
            "pct": 0,
            "current": "N/A",
            "volt": "N/A",
            "power": "N/A",
            "temp": "N/A",
            "eta": "N/A",
        }