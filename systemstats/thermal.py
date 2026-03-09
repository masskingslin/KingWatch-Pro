"""
Thermal Monitor — KingWatch Pro v15
Strategy:
  1. ACTION_BATTERY_CHANGED  — battery temp, always accessible
  2. /sys/class/thermal/thermal_zone*/temp — sysfs (Android 5-8, some OEMs)
NEVER uses HardwarePropertiesManager (requires DEVICE_POWER — system-only).
"""

import glob

IS_ANDROID = False
try:
    from jnius import autoclass as _ac
    IS_ANDROID = True
except ImportError:
    pass

_cached_sysfs = None
_sysfs_done   = False


class ThermalMonitor:

    def __init__(self):
        self._last_temp = 30.0
        self._activity  = None
        if IS_ANDROID:
            try:
                PythonActivity = _ac("org.kivy.android.PythonActivity")
                self._activity = PythonActivity.mActivity
            except Exception:
                pass

    def read(self) -> float:
        # Strategy 1: battery broadcast
        t = self._battery_temp()
        if t is not None:
            self._last_temp = t
            return round(t, 1)

        # Strategy 2: sysfs thermal zone
        t = self._sysfs_temp()
        if t is not None:
            self._last_temp = t
            return round(t, 1)

        return round(self._last_temp, 1)

    def _battery_temp(self):
        if not self._activity:
            return None
        try:
            Intent       = _ac("android.content.Intent")
            IntentFilter = _ac("android.content.IntentFilter")
            ifilter      = IntentFilter(Intent.ACTION_BATTERY_CHANGED)
            intent       = self._activity.registerReceiver(None, ifilter)
            raw = intent.getIntExtra("temperature", 0) if intent else 0
            return raw / 10.0 if raw > 0 else None
        except Exception:
            return None

    def _sysfs_temp(self):
        global _cached_sysfs, _sysfs_done
        if _sysfs_done and _cached_sysfs is None:
            return None

        if _cached_sysfs:
            try:
                raw = int(open(_cached_sysfs).read().strip())
                t   = raw / 1000.0 if raw > 1000 else float(raw)
                if 1 < t < 150:
                    return t
            except Exception:
                _cached_sysfs = None

        patterns = [
            "/sys/class/thermal/thermal_zone*/temp",
            "/sys/devices/virtual/thermal/thermal_zone*/temp",
        ]
        for pat in patterns:
            for path in glob.glob(pat):
                try:
                    raw = int(open(path).read().strip())
                    t   = raw / 1000.0 if raw > 1000 else float(raw)
                    if 1 < t < 150:
                        _cached_sysfs = path
                        return t
                except Exception:
                    continue

        _sysfs_done   = True
        _cached_sysfs = None
        return None
