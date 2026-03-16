import time
from kivy.clock import Clock
from kivy.core.window import Window


class FPSMonitor:

    def __init__(self):

        try:
            self.refresh = int(Window.refresh_rate)
            if self.refresh <= 0:
                self.refresh = 60
        except:
            self.refresh = 60

        self.last = time.time()
        self.frames = []

        Clock.schedule_interval(self.track, 0)

    def track(self, dt):

        now = time.time()
        ft = now - self.last
        self.last = now

        self.frames.append(ft)

        if len(self.frames) > 120:
            self.frames.pop(0)

    def get_fps(self):
        try:
            return int(Clock.get_fps())
        except:
            return 0

    def get_refresh_rate(self):
        return self.refresh