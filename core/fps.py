import time
from kivy.clock import Clock
from kivy.core.window import Window


class FPSMonitor:

    def __init__(self):

        # Detect refresh rate
        try:
            rr = Window.refresh_rate
            if rr and rr > 0:
                self.refresh = int(rr)
            else:
                self.refresh = 60
        except:
            self.refresh = 60

        self.last_frame = time.time()
        self.frame_times = []
        self.frame_drops = 0
        self.lag_spikes = 0

        Clock.schedule_interval(self._track_frame, 0)

    # --------------------------------------------------

    def _track_frame(self, dt):

        now = time.time()
        frame_time = now - self.last_frame
        self.last_frame = now

        self.frame_times.append(frame_time)

        if len(self.frame_times) > 120:
            self.frame_times.pop(0)

        # frame drop detection
        ideal = 1.0 / self.refresh
        if frame_time > ideal * 1.5:
            self.frame_drops += 1

        # lag spike detection
        if frame_time > 0.1:
            self.lag_spikes += 1

    # --------------------------------------------------

    def get_fps(self):

        try:
            fps = int(Clock.get_fps())
        except:
            fps = 0

        return fps

    # --------------------------------------------------

    def get_refresh_rate(self):
        return self.refresh

    # --------------------------------------------------

    def get_frame_drops(self):

        drops = self.frame_drops
        self.frame_drops = 0
        return drops

    # --------------------------------------------------

    def get_lag(self):

        lag = self.lag_spikes
        self.lag_spikes = 0
        return lag

    # --------------------------------------------------

    def get_frame_time(self):

        if not self.frame_times:
            return 0

        avg = sum(self.frame_times) / len(self.frame_times)

        return round(avg * 1000, 2)

    # --------------------------------------------------

    def get_gpu(self):

        fps = self.get_fps()

        load = (fps / self.refresh) * 100

        if load > 100:
            load = 100

        return f"{int(load)}%"

    # --------------------------------------------------

    def get_stability(self):

        if len(self.frame_times) < 10:
            return 100

        avg = sum(self.frame_times) / len(self.frame_times)

        variance = sum((t - avg) ** 2 for t in self.frame_times) / len(self.frame_times)

        stability = max(0, 100 - (variance * 10000))

        return int(stability)