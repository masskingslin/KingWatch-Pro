from kivy.clock import Clock


class FPSMonitor:

    def get_fps(self):
        return int(Clock.get_fps())

    def get_gpu(self):

        fps = self.get_fps()

        if fps >= 55:
            return "40%"
        elif fps >= 40:
            return "65%"
        elif fps >= 25:
            return "80%"
        else:
            return "95%"

    def get_frame_drops(self):
        return max(0, 60 - self.get_fps())

    def get_lag(self):
        return 1 if self.get_fps() < 30 else 0