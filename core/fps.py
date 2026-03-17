"""
KingWatch Pro v17 - core/fps.py
FPS + GPU load + refresh rate (re-detected every 5s for dynamic rate changes).
"""
import time
import glob
from kivy.clock import Clock


class PerformanceMonitor:
    WINDOW = 20

    def __init__(self):
        self._frames   = []
        self._last     = time.perf_counter()
        self._refresh  = self._detect_refresh()
        self._ref_tick = 0
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

    def get_refresh_rate(self) -> int:
        # Re-detect every 10 calls (~5s) to pick up 60/90/120Hz changes
        self._ref_tick += 1
        if self._ref_tick >= 10:
            self._refresh  = self._detect_refresh()
            self._ref_tick = 0
        return self._refresh

    def get_gpu(self) -> str:
        # 1. Qualcomm Adreno
        for p in (
            "/sys/class/kgsl/kgsl-3d0/gpu_busy_percentage",
            "/sys/class/kgsl/kgsl-3d0/devfreq/gpu_load",
            "/sys/kernel/debug/kgsl/kgsl-3d0/gpu_busy_percentage",
        ):
            try:
                with open(p) as f:
                    v = f.read().strip().split()[0].rstrip("%")
                    return f"{int(float(v))}%"
            except Exception:
                continue

        # 2. ARM Mali — search all possible paths
        mali_paths = (
            glob.glob("/sys/devices/platform/*/mali/utilization") +
            glob.glob("/sys/devices/platform/mali*/utilization") +
            glob.glob("/sys/class/misc/mali0/device/utilization") +
            glob.glob("/sys/devices/*/gpu/utilization") +
            ["/sys/kernel/gpu/gpu_busy",
             "/sys/devices/platform/gpu/utilization"]
        )
        for p in mali_paths:
            try:
                with open(p) as f:
                    v = f.read().strip().split()[0].rstrip("%")
                    return f"{int(float(v))}%"
            except Exception:
                continue

        # 3. MediaTek GED
        for p in (
            "/sys/kernel/ged/hal/gpu_utilization",
            "/sys/kernel/ged/hal/gpu_freq_loading",
            "/proc/gpufreq/gpufreq_var_dump",
        ):
            try:
                with open(p) as f:
                    for line in f:
                        ll = line.lower()
                        for kw in ("utilization", "loading", "busy"):
                            if kw in ll:
                                for tok in line.split():
                                    try:
                                        v = int(tok.strip(":%,()"))
                                        if 0 <= v <= 100:
                                            return f"{v}%"
                                    except Exception:
                                        pass
            except Exception:
                continue

        # 4. GPU freq ratio (works on most SoCs)
        cur_paths = glob.glob("/sys/class/devfreq/*/cur_freq")
        max_paths = glob.glob("/sys/class/devfreq/*/max_freq")
        for cp in cur_paths:
            mp = cp.replace("cur_freq", "max_freq")
            try:
                with open(cp) as f:
                    cur = int(f.read().strip())
                with open(mp) as f:
                    mx  = int(f.read().strip())
                if mx > 0 and cur > 0:
                    # Only use GPU devfreq nodes (not CPU)
                    node = cp.lower()
                    if any(k in node for k in ("gpu", "mali", "kgsl", "pvr", "ge8")):
                        return f"{int(cur/mx*100)}%"
            except Exception:
                continue

        return "N/A"

    def _detect_refresh(self) -> int:
        # 1. Android WindowManager — most accurate, handles 120Hz setting
        try:
            from jnius import autoclass
            act  = autoclass("org.kivy.android.PythonActivity").mActivity
            disp = act.getWindowManager().getDefaultDisplay()
            # getRefreshRate() returns current active rate (respects user setting)
            rate = disp.getRefreshRate()
            if rate > 0:
                return int(round(rate))
        except Exception:
            pass
        # 2. /sys fb0 modes
        try:
            with open("/sys/class/graphics/fb0/modes") as f:
                line = f.readline().strip()
            r = int(line.rsplit("-", 1)[-1])
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
