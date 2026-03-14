def update(self, dt):

    # FPS from Kivy engine
    self.fps = int(Clock.get_fps())

    now = time()

    if now - self.last_time >= 1:

        self.last_time = now

        # RAM stats
        self.ram_pct, self.ram_usage_str = self._calculate_ram()

        # GPU load estimation
        if self.fps >= 55:
            self.gpu_load = 40
        elif self.fps >= 40:
            self.gpu_load = 65
        elif self.fps >= 25:
            self.gpu_load = 80
        else:
            self.gpu_load = 95

    # frame drop
    if dt > 0.05:
        self.frame_drops += 1

    # lag detection
    if dt > 0.1:
        self.lag_events += 1