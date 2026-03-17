"""
KingWatch Pro v17 - core/fps.py
FPS counter + GPU load (Adreno/Mali/PowerVR) + refresh rate.
"""
import time
import glob
from kivy.clock import Clock


class PerformanceMonitor:
    WINDOW = 30

    def __init__(self):
        self._frames   = []
        self._last     = time.perf_counter()
        self._refresh  = self._detect_refresh()
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
        if len(self._frames) < 2:
            return 0
        avg = sum(self._frames) / len(self._frames)
        return int(round(1.0 / avg)) if avg > 0 else 0

    def get_gpu(self) -> str:
        # Qualcomm Adreno
        for p in ("/sys/class/kgsl/kgsl-3d0/gpu_busy_percentage",
                  "/sys/class/kgsl/kgsl-3d0/devfreq/gpu_load"):
            try:
                with open(p) as f:
                    v = f.read().strip().split()[0]
                    return f"{v}%"
            except Exception:
                continue
        # ARM Mali
        for p in glob.glob("/sys/devices/platform/*/utilization") + \
                 glob.glob("/sys/kernel/gpu/gpu_busy") + \
                 glob.glob("/sys/class/misc/mali*/device/utilization"):
            try:
                with open(p) as f:
                    v = f.read().strip()
                    return f"{v}%"
            except Exception:
                continue
        # MediaTek GPU
        for p in ("/proc/gpufreq/gpufreq_var_dump",
                  "/sys/kernel/ged/hal/gpu_utilization"):
            try:
                with open(p) as f:
                    for line in f:
                        if "util" in line.lower() or "loading" in line.lower():
                            parts = line.split()
                            for part in parts:
                                try:
                                    v = int(part.strip("%"))
                                    if 0 <= v <= 100:
                                        return f"{v}%"
                                except Exception:
                                    pass
            except Exception:
                continue
        return "N/A"

    def get_refresh_rate(self) -> int:
        return self._refresh

    def _detect_refresh(self) -> int:
        # 1. Android WindowManager (most accurate)
        try:
            from jnius import autoclass
            act  = autoclass("org.kivy.android.PythonActivity").mActivity
            disp = act.getWindowManager().getDefaultDisplay()
            return int(round(disp.getRefreshRate()))
        except Exception:
            pass
        # 2. /sys/class/graphics/fb0/modes
        try:
            with open("/sys/class/graphics/fb0/modes") as f:
                r = int(f.readline().strip().rsplit("-", 1)[-1])
                if 20 <= r <= 240:
                    return r
        except Exception:
            pass
        # 3. DRM modes
        try:
            for path in glob.glob("/sys/class/drm/card*/*/modes"):
                with open(path) as f:
                    for line in f:
                        try:
                            r = int(line.strip().split("@")[1].split(".")[0])
                            if 20 <= r <= 240:
                                return r
                        except Exception:
                            pass
        except Exception:
            pass
        return 60
