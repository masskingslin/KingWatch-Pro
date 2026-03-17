"""
KingWatch Pro - core/fps.py
Native FPS counter and display refresh rate detector.
No psutil. Uses Kivy Clock + Android WindowManager via pyjnius.
"""
import time
from kivy.clock import Clock


class PerformanceMonitor:
    """
    Tracks Kivy-rendered FPS using a rolling frame-time window,
    and reads the display refresh rate from Android WindowManager.
    """

    WINDOW_SIZE = 30  # frames to average

    def __init__(self):
        self._frame_times = []
        self._last_time   = time.perf_counter()
        self._cached_refresh = self._detect_refresh_rate()
        # Hook into every Kivy frame
        Clock.schedule_interval(self._tick, 0)

    # ------------------------------------------------------------------ #
    #  Internal frame ticker                                               #
    # ------------------------------------------------------------------ #
    def _tick(self, dt):
        now = time.perf_counter()
        delta = now - self._last_time
        self._last_time = now
        if delta > 0:
            self._frame_times.append(delta)
            if len(self._frame_times) > self.WINDOW_SIZE:
                self._frame_times.pop(0)

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #
    def get_fps(self) -> int:
        """Return smoothed FPS as integer."""
        if len(self._frame_times) < 2:
            return 0
        avg_dt = sum(self._frame_times) / len(self._frame_times)
        return int(round(1.0 / avg_dt)) if avg_dt > 0 else 0

    def get_gpu(self) -> str:
        """
        Return GPU load string.
        On Android, /sys/class/kgsl/kgsl-3d0/gpu_busy_percentage gives
        Adreno load. Falls back to 'N/A' on other devices.
        """
        paths = [
            "/sys/class/kgsl/kgsl-3d0/gpu_busy_percentage",   # Qualcomm Adreno
            "/sys/kernel/gpu/gpu_busy",                        # some Mali
            "/sys/devices/platform/mali/utilization",          # older Mali
        ]
        for p in paths:
            try:
                with open(p) as f:
                    val = f.read().strip().split()[0]
                    return f"{val}%"
            except Exception:
                continue
        return "N/A"

    def get_refresh_rate(self) -> int:
        """Return display refresh rate in Hz (cached, re-reads every 30s)."""
        return self._cached_refresh

    # ------------------------------------------------------------------ #
    #  Refresh rate detection (Android WindowManager / /sys fallback)     #
    # ------------------------------------------------------------------ #
    def _detect_refresh_rate(self) -> int:
        # 1. Try pyjnius -> Android WindowManager (most accurate)
        try:
            from jnius import autoclass  # type: ignore
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            activity = PythonActivity.mActivity
            wm = activity.getWindowManager()
            display = wm.getDefaultDisplay()
            rate = display.getRefreshRate()
            return int(round(rate))
        except Exception:
            pass

        # 2. Try /sys/class/graphics/fb0/modes  (e.g. "U:1080x2340p-90")
        try:
            with open("/sys/class/graphics/fb0/modes") as f:
                line = f.readline().strip()
                # last token after '-' is refresh rate
                rate = int(line.rsplit("-", 1)[-1])
                if 20 <= rate <= 240:
                    return rate
        except Exception:
            pass

        # 3. Try /sys/class/drm/card0-DSI-1/modes
        try:
            import glob
            for path in glob.glob("/sys/class/drm/card*/*/modes"):
                with open(path) as f:
                    for line in f:
                        parts = line.strip().split("x")
                        if len(parts) == 2:
                            try:
                                rate = int(parts[1].split("@")[1].split(".")[0])
                                if 20 <= rate <= 240:
                                    return rate
                            except Exception:
                                continue
        except Exception:
            pass

        # 4. Default fallback
        return 60