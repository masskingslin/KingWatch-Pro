"""
KingWatch Pro v17 - core/fps.py

REFRESH RATE FIX:
  getRefreshRate() returns CURRENT rate (may be 60Hz in power-save on 120Hz phone).
  Use getSupportedModes() to find the TRUE maximum refresh rate the display supports.

GPU: Removed — not accessible without root on most Android devices.
     Shows GPU frequency ratio as % if /sys/class/devfreq available.
"""
import time
import glob
from kivy.clock import Clock


class PerformanceMonitor:
    WINDOW = 20

    def __init__(self):
        self._frames  = []
        self._last    = time.perf_counter()
        self._refresh = self._detect_max_refresh()
        Clock.schedule_interval(self._tick, 0)

    def _tick(self, dt):
        now = time.perf_counter()
        d   = now - self._last
        self._last = now
        if 0 < d < 1.0:
            self._frames.append(d)
            if len(self._frames) > self.WINDOW:
                self._frames.pop(0)

    def get_fps(self) -> int:
        if len(self._frames) < 3:
            return 0
        avg = sum(self._frames) / len(self._frames)
        return int(round(1.0 / avg)) if avg > 0 else 0

    def get_gpu(self) -> str:
        """
        Try to get GPU utilisation. Returns percentage string or "N/A".
        Most Android devices block this without root.
        """
        # Qualcomm Adreno
        for p in (
            "/sys/class/kgsl/kgsl-3d0/gpu_busy_percentage",
            "/sys/class/kgsl/kgsl-3d0/devfreq/gpu_load",
        ):
            try:
                with open(p) as f:
                    v = f.read().strip().split()[0].rstrip("%")
                    return f"{int(float(v))}%"
            except Exception:
                continue

        # ARM Mali / generic
        for pattern in (
            "/sys/devices/platform/*/mali/utilization",
            "/sys/devices/platform/mali*/utilization",
            "/sys/class/misc/mali0/device/utilization",
            "/sys/kernel/gpu/gpu_busy",
        ):
            for p in glob.glob(pattern):
                try:
                    with open(p) as f:
                        v = f.read().strip().split()[0].rstrip("%")
                        return f"{int(float(v))}%"
                except Exception:
                    continue

        # MediaTek GED
        for p in (
            "/sys/kernel/ged/hal/gpu_utilization",
            "/proc/gpufreqv2/gpu_working_opp_table",
        ):
            try:
                with open(p) as f:
                    for line in f:
                        if any(k in line.lower() for k in ("util","load","busy")):
                            for tok in line.split():
                                try:
                                    v = int(tok.strip("%:,"))
                                    if 0 <= v <= 100:
                                        return f"{v}%"
                                except Exception:
                                    pass
            except Exception:
                continue

        # Frequency ratio fallback (cur/max)
        try:
            cur_files = glob.glob("/sys/class/devfreq/*/cur_freq")
            max_files = glob.glob("/sys/class/devfreq/*/max_freq")
            for cf in cur_files:
                mf = cf.replace("cur_freq", "max_freq")
                if os.path.exists(mf):
                    with open(cf) as f: cur = int(f.read().strip())
                    with open(mf) as f: mx  = int(f.read().strip())
                    if mx > 0:
                        return f"{int(cur/mx*100)}%"
        except Exception:
            pass

        return "N/A"

    def get_refresh_rate(self) -> int:
        return self._refresh

    def _detect_max_refresh(self) -> int:
        """
        Get the MAXIMUM refresh rate the display supports.
        Uses getSupportedModes() which returns all modes including 120/144Hz.
        getRefreshRate() only returns current (may be 60 in power-save).
        """
        # Strategy 1: getSupportedModes() — most accurate for high-refresh displays
        try:
            from jnius import autoclass  # type: ignore
            act   = autoclass("org.kivy.android.PythonActivity").mActivity
            disp  = act.getWindowManager().getDefaultDisplay()
            modes = disp.getSupportedModes()
            rates = []
            for mode in modes:
                try:
                    rates.append(int(round(mode.getRefreshRate())))
                except Exception:
                    pass
            if rates:
                return max(rates)
        except Exception:
            pass

        # Strategy 2: getRefreshRate() (current, may be lower than max)
        try:
            from jnius import autoclass  # type: ignore
            act  = autoclass("org.kivy.android.PythonActivity").mActivity
            disp = act.getWindowManager().getDefaultDisplay()
            return int(round(disp.getRefreshRate()))
        except Exception:
            pass

        # Strategy 3: /sys/class/graphics/fb0/modes
        try:
            with open("/sys/class/graphics/fb0/modes") as f:
                lines = f.readlines()
            rates = []
            for line in lines:
                try:
                    r = int(line.strip().rsplit("-", 1)[-1])
                    if 20 <= r <= 240:
                        rates.append(r)
                except Exception:
                    pass
            if rates:
                return max(rates)
        except Exception:
            pass

        # Strategy 4: DRM modes
        try:
            rates = []
            for path in glob.glob("/sys/class/drm/card*/*/modes"):
                with open(path) as f:
                    for line in f:
                        try:
                            r = int(line.strip().split("@")[1].split(".")[0])
                            if 20 <= r <= 240:
                                rates.append(r)
                        except Exception:
                            pass
            if rates:
                return max(rates)
        except Exception:
            pass

        return 60


import os  # needed for gpu freq fallback
