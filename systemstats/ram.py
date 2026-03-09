"""
RAM Monitor — KingWatch Pro v15
Uses android.app.ActivityManager.MemoryInfo — official Google API.
No special permissions required. Works Android 5–15.
Falls back to /proc/meminfo when not on Android.
"""

IS_ANDROID = False
try:
    from jnius import autoclass as _ac
    IS_ANDROID = True
except ImportError:
    pass


class RamMonitor:

    def __init__(self):
        self._am = None
        self._MemInfo = None
        if IS_ANDROID:
            try:
                PythonActivity = _ac("org.kivy.android.PythonActivity")
                Context        = _ac("android.content.Context")
                ActivityManager = _ac("android.app.ActivityManager")
                self._MemInfo  = _ac("android.app.ActivityManager$MemoryInfo")
                activity = PythonActivity.mActivity
                self._am = activity.getSystemService(Context.ACTIVITY_SERVICE)
            except Exception:
                self._am = None

    def read(self):
        """Returns (usage_percent, used_mb, total_mb)"""
        if self._am is not None:
            return self._read_android()
        return self._read_proc()

    def _read_android(self):
        try:
            mi = self._MemInfo()
            self._am.getMemoryInfo(mi)
            total = mi.totalMem
            avail = mi.availMem
            used  = total - avail
            pct   = (used / total * 100) if total > 0 else 0
            return (
                round(pct, 1),
                int(used  / 1_048_576),
                int(total / 1_048_576),
            )
        except Exception:
            return self._read_proc()

    def _read_proc(self):
        info = {}
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    k, v = line.split(":")
                    info[k.strip()] = int(v.split()[0])
            total = info.get("MemTotal", 1) * 1024
            avail = info.get("MemAvailable",
                    info.get("MemFree", 0) + info.get("Buffers", 0)
                    + info.get("Cached", 0)) * 1024
            used  = total - avail
            pct   = (used / total * 100) if total > 0 else 0
            return (
                round(pct, 1),
                int(used  / 1_048_576),
                int(total / 1_048_576),
            )
        except Exception:
            return 0.0, 0, 1
