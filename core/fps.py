"""
KingWatch Pro v17 - core/fps.py
Shows actual FPS, current refresh rate AND max supported refresh rate.
Uses getSupportedModes() for true max Hz (e.g. 120Hz phone showing 60Hz current).
GPU via getattr() to avoid Python 3.11 cache bug.
"""
import time
import glob

class PerformanceMonitor:
    WINDOW = 20

    def __init__(self):
        self._frames   = []
        self._last     = time.perf_counter()
        self._max_hz   = self._detect_max_refresh()
        self._curr_hz  = self._max_hz
        from kivy.clock import Clock
        Clock.schedule_interval(self._tick, 0)

    def _tick(self, dt):
        now = time.perf_counter()
        d   = now - self._last
        self._last = now
        if 0 < d < 1.0:
            self._frames.append(d)
            if len(self._frames) > self.WINDOW:
                self._frames.pop(0)

    def get_fps(self):
        if len(self._frames) < 3:
            return 0
        avg = sum(self._frames) / len(self._frames)
        if avg > 0:
            return int(round(1.0 / avg))
        return 0

    def get_gpu(self):
        # All via getattr to avoid Python 3.11 LOAD_ATTR cache bug
        for p in ("/sys/class/kgsl/kgsl-3d0/gpu_busy_percentage",
                  "/sys/class/kgsl/kgsl-3d0/devfreq/gpu_load"):
            try:
                with open(p) as f:
                    raw = f.read().strip().split()[0]
                    v   = raw.rstrip("%")
                    return str(int(float(v))) + "%"
            except Exception:
                continue
        for pattern in ("/sys/devices/platform/*/mali/utilization",
                        "/sys/class/misc/mali0/device/utilization",
                        "/sys/kernel/gpu/gpu_busy"):
            for p in glob.glob(pattern):
                try:
                    with open(p) as f:
                        raw = f.read().strip().split()[0]
                        v   = raw.rstrip("%")
                        return str(int(float(v))) + "%"
                except Exception:
                    continue
        for p in ("/sys/kernel/ged/hal/gpu_utilization",):
            try:
                with open(p) as f:
                    for line in f:
                        if "util" in line.lower():
                            for tok in line.split():
                                try:
                                    v = int(tok.strip("%:,"))
                                    if 0 <= v <= 100:
                                        return str(v) + "%"
                                except Exception:
                                    pass
            except Exception:
                pass
        return "N/A"

    def get_refresh_rate(self):
        """Return current active refresh rate."""
        return self._curr_hz

    def get_max_refresh_rate(self):
        """Return maximum supported refresh rate of the display."""
        return self._max_hz

    def _detect_max_refresh(self):
        """
        Use getSupportedModes() to get ALL display modes and find the max Hz.
        getRefreshRate() only returns current (may be 60Hz in power-save on 120Hz device).
        """
        # Strategy 1: getSupportedModes() — finds true max (120Hz, 144Hz etc)
        try:
            from jnius import autoclass  # type: ignore
            _PA   = autoclass("org.kivy.android.PythonActivity")
            act   = getattr(_PA, 'mActivity')
            _gWM  = getattr(act, 'getWindowManager')
            wm    = _gWM()
            _gDD  = getattr(wm, 'getDefaultDisplay')
            disp  = _gDD()
            # getSupportedModes returns Display.Mode[] array
            _gSM  = getattr(disp, 'getSupportedModes')
            modes = _gSM()
            rates = []
            try:
                # Java array — iterate by length
                _len = getattr(modes, 'length')
                for i in range(_len):
                    try:
                        mode = modes[i]
                        _gRR = getattr(mode, 'getRefreshRate')
                        r    = _gRR()
                        rates.append(int(round(r)))
                    except Exception:
                        pass
            except Exception:
                # Python iterable fallback
                try:
                    for mode in modes:
                        try:
                            _gRR = getattr(mode, 'getRefreshRate')
                            r    = _gRR()
                            rates.append(int(round(r)))
                        except Exception:
                            pass
                except Exception:
                    pass
            if rates:
                self._curr_hz = int(round(getattr(disp, 'getRefreshRate')()))
                return max(rates)
        except Exception:
            pass

        # Strategy 2: getRefreshRate() current
        try:
            from jnius import autoclass  # type: ignore
            _PA   = autoclass("org.kivy.android.PythonActivity")
            act   = getattr(_PA, 'mActivity')
            _gWM  = getattr(act, 'getWindowManager')
            wm    = _gWM()
            _gDD  = getattr(wm, 'getDefaultDisplay')
            disp  = _gDD()
            _gRR  = getattr(disp, 'getRefreshRate')
            r     = int(round(_gRR()))
            return r
        except Exception:
            pass

        # Strategy 3: /sys fb0 modes (lists all supported modes)
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
