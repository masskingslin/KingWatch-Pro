"""
KingWatch Pro v17 - core/fps.py
FPS counter + GPU load (Adreno/Mali/MediaTek/PowerVR) + display refresh rate.
"""
import time
import glob
from kivy.clock import Clock


class PerformanceMonitor:
    WINDOW = 20

    def __init__(self):
        self._frames  = []
        self._last    = time.perf_counter()
        self._refresh = self._detect_refresh()
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
        # ── Qualcomm Adreno ──────────────────────────────────────────────
        for p in (
            "/sys/class/kgsl/kgsl-3d0/gpu_busy_percentage",
            "/sys/class/kgsl/kgsl-3d0/devfreq/gpu_load",
            "/sys/kernel/debug/kgsl/kgsl-3d0/gpu_busy",
        ):
            try:
                with open(p) as f:
                    v = f.read().strip().split()[0].rstrip("%")
                    return f"{int(float(v))}%"
            except Exception:
                continue

        # ── ARM Mali ─────────────────────────────────────────────────────
        for p in (
            glob.glob("/sys/devices/platform/*/mali/utilization") +
            glob.glob("/sys/devices/platform/mali*/utilization") +
            glob.glob("/sys/class/misc/mali0/device/utilization") +
            ["/sys/kernel/gpu/gpu_busy"]
        ):
            try:
                plist = [p] if isinstance(p, str) else p
                for pp in plist:
                    with open(pp) as f:
                        v = f.read().strip().split()[0].rstrip("%")
                        return f"{int(float(v))}%"
            except Exception:
                continue

        # ── MediaTek GED ─────────────────────────────────────────────────
        for p in (
            "/sys/kernel/ged/hal/gpu_utilization",
            "/proc/gpufreq/gpufreq_var_dump",
        ):
            try:
                with open(p) as f:
                    for line in f:
                        for kw in ("utilization", "loading", "busy"):
                            if kw in line.lower():
                                for tok in line.split():
                                    try:
                                        v = int(tok.strip(":%,"))
                                        if 0 <= v <= 100:
                                            return f"{v}%"
                                    except Exception:
                                        pass
            except Exception:
                continue

        # ── Try pyjnius for GPU freq ratio ────────────────────────────────
        try:
            from jnius import autoclass  # type: ignore
            ctx = autoclass(
                "org.kivy.android.PythonActivity").mActivity
            pm  = ctx.getSystemService("power")
            # If we get here without exception, GPU info not directly available
        except Exception:
            pass

        return "N/A"

    def get_refresh_rate(self) -> int:
        return self._refresh

    def _detect_refresh(self) -> int:
        # 1. Android WindowManager
        try:
            from jnius import autoclass
            act  = autoclass(
                "org.kivy.android.PythonActivity").mActivity
            disp = act.getWindowManager().getDefaultDisplay()
            return int(round(disp.getRefreshRate()))
        except Exception:
            pass
        # 2. /sys/class/graphics/fb0/modes
        try:
            with open("/sys/class/graphics/fb0/modes") as f:
                line = f.readline().strip()
            r = int(line.rsplit("-", 1)[-1])
            if 20 <= r <= 240:
                return r
        except Exception:
            pass
        # 3. DRM
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
