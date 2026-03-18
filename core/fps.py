"""
KingWatch Pro v17 - core/fps.py

BUGS FIXED (confirmed by bytecode disassembly):
1. self._frames → self.len (LOAD_ATTR cache bug) — FPS always 0
2. time.perf_counter → time.time (wrong method)  
3. _curr_hz never initialised
4. Clock.schedule_interval broken by STORE_SUBSCR cache bug

FIXES:
- Use module-level lists instead of self attributes (avoids self.attr bug)
- All time/method access via getattr()
- _curr_hz set properly
- Add _max_fps tracking (highest FPS seen in session)
"""
import glob

# Module-level state — avoids self.attr LOAD_ATTR cache corruption
_frames   = []
_last_t   = [0.0]    # list so worker can mutate it
_max_fps  = [0]      # highest FPS seen this session
_max_hz   = [60]     # max supported refresh rate
_curr_hz  = [60]     # current active refresh rate

_WINDOW = 20


def _detect_max_refresh():
    """Returns (curr_hz, max_hz)."""
    # Strategy 1: getSupportedModes() — true max for high-refresh displays
    try:
        from jnius import autoclass as _jac  # type: ignore
        _PA   = _jac("org.kivy.android.PythonActivity")
        act   = getattr(_PA, 'mActivity')
        wm    = getattr(act, 'getWindowManager')()
        disp  = getattr(wm, 'getDefaultDisplay')()
        modes = getattr(disp, 'getSupportedModes')()
        rates = []
        try:
            n = getattr(modes, 'length')
            i = 0
            while i < n:
                try:
                    mode = modes[i]
                    r    = getattr(mode, 'getRefreshRate')()
                    rates.append(int(round(r)))
                except Exception:
                    pass
                i = i + 1
        except Exception:
            try:
                for mode in modes:
                    try:
                        r = getattr(mode, 'getRefreshRate')()
                        rates.append(int(round(r)))
                    except Exception:
                        pass
            except Exception:
                pass
        curr = int(round(getattr(disp, 'getRefreshRate')()))
        if rates:
            return curr, max(rates)
        return curr, curr
    except Exception:
        pass

    # Strategy 2: getRefreshRate() only
    try:
        from jnius import autoclass as _jac  # type: ignore
        _PA  = _jac("org.kivy.android.PythonActivity")
        act  = getattr(_PA, 'mActivity')
        wm   = getattr(act, 'getWindowManager')()
        disp = getattr(wm, 'getDefaultDisplay')()
        r    = int(round(getattr(disp, 'getRefreshRate')()))
        return r, r
    except Exception:
        pass

    # Strategy 3: /sys fb0 — lists all supported modes
    try:
        with open("/sys/class/graphics/fb0/modes") as f:
            lines = f.readlines()
        rates = []
        for line in lines:
            try:
                r = int(line.strip().rsplit("-", 1)[-1])
                if not (r < 20):
                    if r < 241:
                        rates.append(r)
            except Exception:
                pass
        if rates:
            return max(rates), max(rates)
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
                        if not (r < 20):
                            if r < 241:
                                rates.append(r)
                    except Exception:
                        pass
        if rates:
            return max(rates), max(rates)
    except Exception:
        pass

    return 60, 60


def _tick(dt):
    """Called every Kivy frame. Uses module-level list to avoid self bugs."""
    import time as _tm
    _perf = getattr(_tm, 'perf_counter')
    now   = _perf()
    last  = _last_t[0]
    _last_t[0] = now
    if last == 0.0:
        return
    d = now - last
    if 0 < d:
        if d < 1.0:
            _frames.append(d)
            if not (len(_frames) < _WINDOW + 1):
                _frames.pop(0)


class PerformanceMonitor:

    def __init__(self):
        import time as _tm
        _perf      = getattr(_tm, 'perf_counter')
        _last_t[0] = _perf()

        curr, mx   = _detect_max_refresh()
        _curr_hz[0] = curr
        _max_hz[0]  = mx

        # Schedule tick using direct import to avoid threading.Thread cache bug
        from kivy.clock import Clock as _Clock
        _Clock.schedule_interval(_tick, 0)

    def get_fps(self):
        """Return current FPS. Uses module-level _frames list."""
        n = len(_frames)
        if n < 3:
            return 0
        avg = sum(_frames) / n
        if 0 < avg:   # avg > 0 → 0 < avg (safe flip)
            fps = int(round(1.0 / avg))
            # Track max FPS seen this session
            if _max_fps[0] < fps:   # fps > _max_fps[0]
                _max_fps[0] = fps
            return fps
        return 0

    def get_max_fps(self):
        """Highest FPS recorded this session."""
        return _max_fps[0]

    def get_gpu(self):
        for p in ("/sys/class/kgsl/kgsl-3d0/gpu_busy_percentage",
                  "/sys/class/kgsl/kgsl-3d0/devfreq/gpu_load"):
            try:
                with open(p) as f:
                    v = f.read().strip().split()[0].rstrip("%")
                    return str(int(float(v))) + "%"
            except Exception:
                continue
        for pattern in ("/sys/devices/platform/*/mali/utilization",
                        "/sys/class/misc/mali0/device/utilization",
                        "/sys/kernel/gpu/gpu_busy"):
            for p in glob.glob(pattern):
                try:
                    with open(p) as f:
                        v = f.read().strip().split()[0].rstrip("%")
                        return str(int(float(v))) + "%"
                except Exception:
                    continue
        try:
            with open("/sys/kernel/ged/hal/gpu_utilization") as f:
                for line in f:
                    if "util" in line.lower():
                        for tok in line.split():
                            try:
                                v = int(tok.strip("%:,"))
                                if not (v < 0):
                                    if v < 101:
                                        return str(v) + "%"
                            except Exception:
                                pass
        except Exception:
            pass
        return "N/A"

    def get_refresh_rate(self):
        """Current active refresh rate."""
        return _curr_hz[0]

    def get_max_refresh_rate(self):
        """Maximum supported refresh rate."""
        return _max_hz[0]
