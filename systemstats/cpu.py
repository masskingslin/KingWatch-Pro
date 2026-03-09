"""
CPU Monitor — KingWatch Pro v15
Strategy chain (Google Play compliant, no root):

  1. /proc/stat          — Android 5-8 + many OEM Android 9+ ROMs
  2. UsageStatsManager   — Android 5-15 with PACKAGE_USAGE_STATS permission
  3. /proc/self/stat     — Own-process CPU, ALWAYS accessible Android 5-15

SELinux on stock Android 9+ blocks /proc/stat for third-party apps.
We detect this silently and fall to strategy 2 or 3 automatically.
"""

import time

IS_ANDROID = False
try:
    from jnius import autoclass as _ac
    IS_ANDROID = True
except ImportError:
    pass


class CpuMonitor:

    def __init__(self):
        self._last_idle    = 0
        self._last_total   = 0
        self._last_self_j  = 0
        self._last_self_t  = 0.0
        self._last_ust     = 0
        self._last_ust_ms  = 0
        self._proc_blocked = False
        self._ust_ok       = False
        self.strategy      = "sys"

        if IS_ANDROID:
            self._ust_ok = self._check_ust_permission()

    # ── Public ────────────────────────────────────────────────────────────

    def read(self) -> float:
        if not self._proc_blocked:
            val = self._read_proc_stat()
            if val is not None:
                self.strategy = "sys-wide"
                return val
            self._proc_blocked = True

        if self._ust_ok:
            val = self._read_usage_stats()
            if val is not None:
                self.strategy = "usage-stats"
                return val

        val = self._read_self_proc()
        self.strategy = "app-proc"
        return val or 0.0

    # ── Strategy 1: /proc/stat ────────────────────────────────────────────

    def _read_proc_stat(self):
        try:
            with open("/proc/stat", "r") as f:
                line = f.readline()
            parts = line.split()
            if parts[0] != "cpu":
                return None
            vals  = list(map(int, parts[1:]))
            idle  = vals[3] + (vals[4] if len(vals) > 4 else 0)
            total = sum(vals[:8]) if len(vals) >= 8 else sum(vals)

            if self._last_total == 0:
                self._last_idle  = idle
                self._last_total = total
                return 0.0

            d_idle  = idle  - self._last_idle
            d_total = total - self._last_total
            self._last_idle  = idle
            self._last_total = total

            if d_total <= 0:
                return 0.0
            return round(max(0.0, min(100.0, (1 - d_idle / d_total) * 100)), 1)

        except (PermissionError, FileNotFoundError, ValueError, OSError):
            return None

    # ── Strategy 2: UsageStatsManager ─────────────────────────────────────

    def _read_usage_stats(self):
        if not IS_ANDROID:
            return None
        try:
            PythonActivity   = _ac("org.kivy.android.PythonActivity")
            Context          = _ac("android.content.Context")
            UsageStatsManager = _ac("android.app.usage.UsageStatsManager")

            activity = PythonActivity.mActivity
            usm      = activity.getSystemService(Context.USAGE_STATS_SERVICE)
            now_ms   = int(time.time() * 1000)

            stats = usm.queryUsageStats(
                UsageStatsManager.INTERVAL_BEST,
                now_ms - 2000,
                now_ms,
            )
            if stats is None or stats.size() == 0:
                return None

            total_fg = sum(stats.get(i).getTotalTimeInForeground()
                           for i in range(stats.size()))

            if self._last_ust_ms == 0:
                self._last_ust    = total_fg
                self._last_ust_ms = now_ms
                return 0.0

            d_fg = total_fg - self._last_ust
            d_ms = now_ms   - self._last_ust_ms
            self._last_ust    = total_fg
            self._last_ust_ms = now_ms

            if d_ms <= 0:
                return 0.0
            return round(min(100.0, (d_fg / d_ms) * 100.0), 1)

        except Exception:
            return None

    # ── Strategy 3: /proc/self/stat ────────────────────────────────────────

    def _read_self_proc(self):
        try:
            with open("/proc/self/stat", "r") as f:
                parts = f.read().split()
            utime = int(parts[13])
            stime = int(parts[14])
            jiffies = utime + stime
            now = time.monotonic()

            if self._last_self_t == 0.0:
                self._last_self_j = jiffies
                self._last_self_t = now
                return 0.0

            d_j = jiffies - self._last_self_j
            d_t = now - self._last_self_t
            self._last_self_j = jiffies
            self._last_self_t = now

            if d_t <= 0:
                return 0.0
            return round(min(100.0, (d_j / 100.0 / d_t) * 100.0), 1)

        except Exception:
            return 0.0

    # ── Permission check ───────────────────────────────────────────────────

    def _check_ust_permission(self):
        try:
            PythonActivity = _ac("org.kivy.android.PythonActivity")
            AppOpsManager  = _ac("android.app.AppOpsManager")
            Process        = _ac("android.os.Process")

            activity = PythonActivity.mActivity
            app_ops  = activity.getSystemService("appops")
            mode     = app_ops.checkOpNoThrow(
                AppOpsManager.OPSTR_GET_USAGE_STATS,
                Process.myUid(),
                activity.getPackageName(),
            )
            return mode == AppOpsManager.MODE_ALLOWED
        except Exception:
            return False
