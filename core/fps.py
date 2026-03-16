from kivy.clock import Clock
from time import time


class FPSMonitor:
    """
    Lightweight FPS + render performance monitor
    Works on Android and desktop Kivy.
    """

    def __init__(self):
        self.frames = 0
        self.last_time = time()

        self.fps = 0
        self.frame_drops = 0
        self.lag_events = 0
        self.gpu_load = 0

        Clock.schedule_interval(self._update, 0)

    def _update(self, dt):

        self.frames += 1
        now = time()

        # Update once per second
        if now - self.last_time >= 1:
            self.fps = self.frames
            self.frames = 0
            self.last_time = now

            # Estimated render load
            if self.fps >= 55:
                self.gpu_load = 40
            elif self.fps >= 40:
                self.gpu_load = 65
            elif self.fps >= 25:
                self.gpu_load = 80
            else:
                self.gpu_load = 95

        # frame drop detection
        if dt > 0.05:
            self.frame_drops += 1

        # UI lag detection
        if dt > 0.1:
            self.lag_events += 1

    # getters
    def get_fps(self):
        return self.fps

    def get_gpu(self):
        return f"{self.gpu_load}%"

    def get_frame_drops(self):
        return self.frame_drops

    def get_lag(self):
        return self.lag_events