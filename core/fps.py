from kivy.clock import Clock
from time import time


class PerformanceMonitor:

    def __init__(self):

        self.frames = 0
        self.last = time()
        self.fps = 0

        self.frame_drops = 0
        self.lag_events = 0

        Clock.schedule_interval(self.update, 0)

    def update(self, dt):

        self.frames += 1

        if dt > 0.05:
            self.frame_drops += 1

        if dt > 0.1:
            self.lag_events += 1

        now = time()

        if now - self.last >= 1:
            self.fps = self.frames
            self.frames = 0
            self.last = now

    def get_fps(self):
        return self.fps

    def get_gpu(self):

        if self.fps >= 55:
            return "Low"

        if self.fps >= 40:
            return "Medium"

        if self.fps >= 25:
            return "High"

        return "Max"