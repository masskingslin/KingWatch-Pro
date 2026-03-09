"""
Battery Monitor — KingWatch Pro v15
Uses ACTION_BATTERY_CHANGED broadcast + BatteryManager API.
No permissions required. Works Android 5–15.

OEM current normalization:
  |raw| > 100,000 → microamperes → divide by 1000 = mA
  |raw| ≤ 100,000 → already milliamperes
"""

IS_ANDROID = False
try:
    from jnius import autoclass as _ac
    IS_ANDROID = True
except ImportError:
    pass


class BatteryMonitor:

    _STATUS = {1: "Unknown", 2: "Charging", 3: "Discharging", 4: "Not charging", 5: "Full"}
    _HEALTH  = {1: "Unknown", 2: "Good", 3: "Overheat", 4: "Dead", 5: "Over voltage",
                6: "Failure", 7: "Cold"}

    def __init__(self):
        self._bm       = None
        self._activity = None
        self._BM_CLASS = None
        if IS_ANDROID:
            try:
                PythonActivity = _ac("org.kivy.android.PythonActivity")
                Context        = _ac("android.content.Context")
                self._BM_CLASS = _ac("android.os.BatteryManager")
                self._activity = PythonActivity.mActivity
                self._bm       = self._activity.getSystemService(Context.BATTERY_SERVICE)
            except Exception:
                pass

    def read(self):
        """Returns (level, current_mA, voltage_mV, status_str, health_str)"""
        if self._activity:
            return self._read_android()
        return 0, 0, 0, "Unknown", "Unknown"

    def _read_android(self):
        try:
            Intent       = _ac("android.content.Intent")
            IntentFilter = _ac("android.content.IntentFilter")

            ifilter = IntentFilter(Intent.ACTION_BATTERY_CHANGED)
            intent  = self._activity.registerReceiver(None, ifilter)

            # Level
            level = intent.getIntExtra("level", -1)
            scale = intent.getIntExtra("scale", 100)
            level = int(level * 100 / scale) if scale > 0 else level

            # Voltage (already mV in Android)
            voltage_mv = intent.getIntExtra("voltage", 0)

            # Status & health
            status_code = intent.getIntExtra("status", 1)
            health_code = intent.getIntExtra("health", 1)
            is_charging = status_code in (2, 5)

            # Current — via BatteryManager property
            current_ma = self._read_current(is_charging)

            return (
                int(level),
                current_ma,
                int(voltage_mv),
                self._STATUS.get(status_code, "Unknown"),
                self._HEALTH.get(health_code, "Unknown"),
            )
        except Exception:
            return 0, 0, 0, "Unknown", "Unknown"

    def _read_current(self, is_charging):
        if not self._bm or not self._BM_CLASS:
            return 0
        try:
            raw = self._bm.getIntProperty(
                self._BM_CLASS.BATTERY_PROPERTY_CURRENT_NOW
            )
            if raw == -2147483648 or raw == 0:   # Integer.MIN_VALUE = unsupported
                return 0
            abs_val = abs(raw)
            mA = abs_val // 1000 if abs_val > 100_000 else abs_val
            # Normalize sign: positive = discharging, negative = charging
            if is_charging and raw > 0:
                mA = -mA
            elif not is_charging and raw < 0:
                mA = abs(mA)
            return int(mA)
        except Exception:
            return 0
