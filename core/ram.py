from kivy.app import App
from kivy.clock import Clock
from kivy.uix.label import Label
from time import time

class PerformanceMonitor:
    def __init__(self):
        # FPS Tracking
        self.frames = 0
        self.last_time = time()
        self.fps = 0

        # Performance Metrics
        self.frame_drops = 0
        self.lag_events = 0
        self.gpu_load = 0
        
        # RAM Tracking
        self.ram_pct = 0.0
        self.ram_usage_str = "N/A"

        # Schedule the update loop (0 means every frame)
        Clock.schedule_interval(self.update, 0)

    def update(self, dt):
        # 1. Increment frame count
        self.frames += 1
        now = time()

        # 2. Update stats once per second
        if now - self.last_time >= 1:
            self.fps = self.frames
            self.frames = 0
            self.last_time = now

            # Update RAM statistics (Linux/Android specific)
            self.ram_pct, self.ram_usage_str = self._calculate_ram()

            # GPU load estimation based on FPS
            if self.fps >= 55:
                self.gpu_load = 40
            elif self.fps >= 40:
                self.gpu_load = 65
            elif self.fps >= 25:
                self.gpu_load = 80
            else:
                self.gpu_load = 95

        # 3. Frame drop detection (threshold: 50ms)
        if dt > 0.05:
            self.frame_drops += 1

        # 4. Lag detection (threshold: 100ms)
        if dt > 0.1:
            self.lag_events += 1

    def _calculate_ram(self):
        """Parses /proc/meminfo for RAM usage."""
        try:
            mem = {}
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    p = line.split()
                    if len(p) >= 2:
                        mem[p[0].rstrip(":")] = int(p[1])
            
            total = mem.get("MemTotal", 1)
            # MemAvailable is preferred; fallback to MemFree
            avail = mem.get("MemAvailable", mem.get("MemFree", 0))
            
            pct = round((total - avail) / total * 100, 1)
            used = round((total - avail) / 1024)
            tot = round(total / 1024)
            
            return pct, f"{used} MB / {tot} MB"
        except Exception:
            # Fallback for non-Linux systems (Windows/macOS)
            return 0.0, "N/A (Linux Only)"

    # --- Getters ---
    def get_fps(self):
        return self.fps

    def get_gpu(self):
        return f"{self.gpu_load}%"

    def get_frame_drops(self):
        return self.frame_drops

    def get_lag(self):
        return self.lag_events

    def get_ram(self):
        """Returns tuple: (float percentage, string 'Used/Total')"""
        return self.ram_pct, self.ram_usage_str


# --- Example Usage (Run this file to test) ---
class TestApp(App):
    def build(self):
        self.monitor = PerformanceMonitor()
        self.label = Label(text="Initializing stats...", font_size='20sp')
        
        # Update the UI Label every 0.5 seconds
        Clock.schedule_interval(self.refresh_ui, 0.5)
        return self.label

    def refresh_ui(self, dt):
        ram_pct, ram_str = self.monitor.get_ram()
        
        self.label.text = (
            f"FPS: {self.monitor.get_fps()}\n"
            f"Est. GPU Load: {self.monitor.get_gpu()}\n"
            f"RAM: {ram_str} ({ram_pct}%)\n"
            f"Drops: {self.monitor.get_frame_drops()} | Lag: {self.monitor.get_lag()}"
        )

if __name__ == "__main__":
    TestApp().run()
