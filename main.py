"""
KingWatch Pro v15 — Kivy Android System Monitor
Author  : King AI
Target  : Android 5.0 (API 21) → Android 15 (API 35)
Policy  : Google Play Store compliant — no root, no private APIs
Build   : Buildozer + GitHub Actions
"""

import os
import sys

# ── Platform detection ─────────────────────────────────────────────────────
IS_ANDROID = False
try:
    from android import activity  # noqa
    IS_ANDROID = True
except ImportError:
    pass

# ── Kivy config BEFORE any kivy import ────────────────────────────────────
os.environ.setdefault("KIVY_WINDOW", "android" if IS_ANDROID else "sdl2")

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.logger import Logger

# ── Sub-modules ────────────────────────────────────────────────────────────
from systemstats.cpu     import CpuMonitor
from systemstats.ram     import RamMonitor
from systemstats.network import NetworkMonitor
from systemstats.battery import BatteryMonitor
from systemstats.thermal import ThermalMonitor
from ui.gauges           import ArcGauge          # noqa — registered in KV
from ui.themes           import ThemeManager

if IS_ANDROID:
    from android.permissions import (
        request_permissions,
        check_permission,
        Permission,
    )
    from android_service import start_foreground_service

# ── KV file ────────────────────────────────────────────────────────────────
KV = Builder.load_file("kingwatch.kv")


# ════════════════════════════════════════════════════════════════════════════
class Dashboard(BoxLayout):

    THEMES = ["DARK", "CYBER", "OCEAN", "LAVA", "AMOLED", "PURPLE", "GOLD", "MINT"]
    _theme_idx = 0
    _collapsed  = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._cpu     = CpuMonitor()
        self._ram     = RamMonitor()
        self._net     = NetworkMonitor()
        self._bat     = BatteryMonitor()
        self._thermal = ThermalMonitor()
        self._themes  = ThemeManager()

    # ── Permission request (Android) ──────────────────────────────────────
    def request_android_permissions(self):
        if not IS_ANDROID:
            return
        perms = [
            Permission.POST_NOTIFICATIONS,     # Android 13+
        ]
        request_permissions(perms, self._on_permissions)

    def _on_permissions(self, permissions, grant_results):
        Logger.info("KingWatch: Permissions result: %s", list(zip(permissions, grant_results)))

    # ── Foreground service ────────────────────────────────────────────────
    def start_service(self):
        if IS_ANDROID:
            try:
                start_foreground_service()
                Logger.info("KingWatch: Foreground service started")
            except Exception as exc:
                Logger.warning("KingWatch: Service start failed: %s", exc)

    # ── Main update loop (1-second tick) ──────────────────────────────────
    def update(self, dt):
        try:
            # ── CPU ──
            cpu = self._cpu.read()
            self.ids.gauge_cpu.value   = cpu
            self.ids.lbl_cpu.text      = f"CPU\n{cpu:.0f}%"
            self.ids.lbl_cpu_detail.text = f"[{self._cpu.strategy}]"

            # ── RAM ──
            ram_pct, used_mb, total_mb = self._ram.read()
            self.ids.gauge_ram.value   = ram_pct
            self.ids.lbl_ram.text      = f"RAM\n{ram_pct:.0f}%"
            self.ids.lbl_ram_detail.text = f"{used_mb}M / {total_mb}M"

            # ── Network ──
            rx, tx = self._net.read()
            self.ids.lbl_rx.text = f"▼ {_fmt(rx)}"
            self.ids.lbl_tx.text = f"▲ {_fmt(tx)}"

            # ── Battery ──
            lvl, mA, mV, status, health = self._bat.read()
            self.ids.gauge_bat.value      = lvl
            self.ids.lbl_bat.text         = f"BAT\n{lvl}%"
            self.ids.lbl_bat_detail.text  = f"{abs(mA)}mA · {mV}mV"
            self.ids.lbl_bat_status.text  = f"{status} · {health}"

            # ── Temperature ──
            temp = self._thermal.read()
            self.ids.lbl_temp.text = f"{temp:.1f}°C"
            self.ids.lbl_temp.color = _temp_color(temp)

        except Exception as exc:
            Logger.error("KingWatch: Update error: %s", exc)

    # ── Theme cycle ───────────────────────────────────────────────────────
    def cycle_theme(self):
        self._theme_idx = (self._theme_idx + 1) % len(self.THEMES)
        name = self.THEMES[self._theme_idx]
        colors = self._themes.get(name)
        self.ids.lbl_theme.text = name
        # Apply background
        self.ids.root_layout.canvas.before.clear()
        with self.ids.root_layout.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(*colors["bg"])
            self._bg_rect = Rectangle(pos=self.pos, size=self.size)
        # Push to gauges
        for gid in ("gauge_cpu", "gauge_ram", "gauge_bat"):
            self.ids[gid].arc_color = colors["arc"]
        # Text colors
        for lid in ("lbl_cpu", "lbl_ram", "lbl_bat", "lbl_rx", "lbl_tx", "lbl_temp"):
            self.ids[lid].color = colors["text"]

    # ── Collapse toggle ───────────────────────────────────────────────────
    def toggle_collapse(self):
        self._collapsed = not self._collapsed
        self.ids.content_area.opacity = 0 if self._collapsed else 1
        self.ids.content_area.height  = 0 if self._collapsed else self.ids.content_area.minimum_height
        self.ids.btn_collapse.text = "▢" if self._collapsed else "_"


# ════════════════════════════════════════════════════════════════════════════
def _fmt(bps: float) -> str:
    if bps >= 1_048_576:
        return f"{bps/1_048_576:.1f}M/s"
    if bps >= 1_024:
        return f"{bps/1_024:.1f}K/s"
    return f"{int(bps)}B/s"


def _temp_color(t: float):
    if t < 35:
        return (0.24, 0.86, 0.51, 1)
    if t < 45:
        return (0.98, 0.80, 0.10, 1)
    return (0.97, 0.25, 0.25, 1)


# ════════════════════════════════════════════════════════════════════════════
class KingWatchApp(App):

    def build(self):
        Window.clearcolor = (0.05, 0.05, 0.08, 1)
        self.dash = Dashboard()
        return self.dash

    def on_start(self):
        self.dash.request_android_permissions()
        self.dash.start_service()
        Clock.schedule_interval(self.dash.update, 1.0)

    def on_stop(self):
        Clock.unschedule(self.dash.update)


# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    KingWatchApp().run()
