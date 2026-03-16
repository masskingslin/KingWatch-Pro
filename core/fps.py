from kivy.clock import Clock
from kivy.core.window import Window


class FPSMonitor:

    def __init__(self):
        self.refresh_rate = Window.refresh_rate if Window.refresh_rate else 60

    def get_fps(self):
        return int(Clock.get_fps())

    def get_refresh_rate(self):
        return int(self.refresh_rate)

    def get_gpu(self):

        fps = self.get_fps()
        r = self.refresh_rate

        load = (fps / r) * 100

        if load >= 90:
            return "40%"
        elif load >= 70:
            return "60%"
        elif load >= 50:
            return "80%"
        else:
            return "95%"

    def get_frame_drops(self):

        fps = self.get_fps()
        r = self.refresh_rate

        return max(0, r - fps)

    def get_lag(self):

        fps = self.get_fps()
        r = self.refresh_rate

        return 1 if fps < (r * 0.5) else 0