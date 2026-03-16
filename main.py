from kivy.app import App

from kivy.clock import Clock

from kivy.lang import Builder

from kivy.uix.boxlayout import BoxLayout

from kivy.properties import ListProperty, BooleanProperty

from core.fps import PerformanceMonitor

from core.cpu import get_cpu

from core.ram import get_ram

from core.battery import get_battery

from core.network import get_network"

from core.storage import get_storage

from core.thermal import get_thermal

from themes import THEME_NAMES, get_theme

Builder.load_file("kingwatch.kv")

class RootWidget(BoxLayout):
    bg        = ListProperty([0.04, 0.04, 0.04, 1])
    card_bg   = ListProperty([0.09, 0.09, 0.09, 1])
    accent    = ListProperty([0.0, 0.90, 0.46, 1])
    warn      = ListProperty([1.0, 0.57, 0.0,  1])
    danger    = ListProperty([1.0, 0.09, 0.27, 1])
    text_col  = ListProperty([1,   1,   1,    1])
    dim_col   = ListProperty([0.33,0.33,0.33, 1])
    collapsed = BooleanProperty(False)

    theme_index = 0

    def apply_theme(self, name):
        t = get_theme(name)

        def h(hex_str):
            h = hex_str.lstrip("#")
            return [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)] + [1]

        self.bg       = h(t["BG"])
        self.card_bg  = h(t["CARD"])
        self.accent   = h(t["ACCENT"])
        self.warn     = h(t["WARN"])
        self.danger   = h(t["DANGER"])
        self.text_col = h(t["TEXT"])
        self.dim_col  = h(t["DIM"])

    def cycle_theme(self):
        self.theme_index = (self.theme_index + 1) % len(THEME_NAMES)
        self.apply_theme(THEME_NAMES[self.theme_index])

    def toggle_collapse(self):
        self.collapsed = not self.collapsed


class KingWatchApp(App):

    def build(self):
        self.monitor = PerformanceMonitor()
        self.root_widget = RootWidget()
        self.root_widget.apply_theme("Dark Pro")
        Clock.schedule_interval(self.update_stats, 1)
        return self.root_widget

    def update_stats(self, dt):
        r = self.root_widget

        # ── FPS / GPU ──────────────────────────────────
        fps = self.monitor.get_fps()
        gpu = self.monitor.get_gpu()
        r.ids.fps_card.value    = str(fps)
        r.ids.fps_card.subtitle = f"GPU Load: {gpu}"
        r.ids.fps_card.bar_pct  = min(100, (fps / 60) * 100)

        # ── CPU ────────────────────────────────────────
        cpu = get_cpu()
        r.ids.cpu_card.value    = f"{cpu['usage']:.1f}%"
        r.ids.cpu_card.subtitle = f"{cpu['freq']} MHz  |  {cpu['cores']} Cores"
        r.ids.cpu_card.detail1  = f"Processes: {cpu['procs']}"
        r.ids.cpu_card.detail2  = "[sys-wide]"
        r.ids.cpu_card.bar_pct  = cpu['usage']

        # ── RAM ────────────────────────────────────────
        ram_pct, ram_str = get_ram()
        r.ids.ram_card.value    = f"{ram_pct:.1f}%"
        r.ids.ram_card.subtitle = ram_str
        r.ids.ram_card.bar_pct  = ram_pct

        # ── Battery ────────────────────────────────────
        batt = get_battery()
        r.ids.battery_card.value    = f"{batt['pct']}%"
        r.ids.battery_card.subtitle = batt['eta']
        r.ids.battery_card.detail1  = f"{batt['current']}  {batt['volt']}  {batt['power']}"
        r.ids.battery_card.detail2  = f"Temp: {batt['temp']}"
        r.ids.battery_card.bar_pct  = batt['pct']

        # ── Network ────────────────────────────────────
        net = get_network()
        r.ids.network_card.value    = f"↓ {net['dl']}"
        r.ids.network_card.subtitle = f"↑ {net['ul']}"
        r.ids.network_card.detail1  = f"Ping: {net['ping']}   {net['signal']}"
        r.ids.network_card.show_bar = False

        # ── Storage ────────────────────────────────────
        storage = get_storage()
        r.ids.storage_card.value    = f"{storage['pct']:.1f}%"
        r.ids.storage_card.subtitle = f"{storage['used']} / {storage['total']}"
        r.ids.storage_card.bar_pct  = storage['pct']

        # ── Thermal ────────────────────────────────────
        therm = get_thermal()
        r.ids.thermal_card.value    = f"{therm['cpu']}°C"
        r.ids.thermal_card.subtitle = f"Max: {therm['max']}°C"
        r.ids.thermal_card.detail1  = therm['detail']
        r.ids.thermal_card.bar_pct  = min(100, (therm['max'] / 90) * 100)


if __name__ == "__main__":
    KingWatchApp().run()

#:import StatCard ui.widgets.StatCard
#:import dp kivy.metrics.dp

# ── StatCard template ──────────────────────────────────────────────────────
<StatCard>:
    orientation: "vertical"
    size_hint_y: None
    height: self.minimum_height
    padding: dp(10)
    spacing: dp(6)

    canvas.before:
        Color:
            rgba: self.bg_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]

    # Title row
    BoxLayout:
        size_hint_y: None
        height: dp(22)
        Label:
            text: root.title.upper()
            font_size: dp(11)
            color: root.title_color
            halign: "left"
            valign: "middle"
            text_size: self.size
            bold: True

    # Value + subtitle
    BoxLayout:
        size_hint_y: None
        height: dp(44)
        orientation: "vertical"
        Label:
            id: value_label
            text: root.value
            font_size: dp(26)
            bold: True
            color: root.value_color
            halign: "left"
            valign: "bottom"
            text_size: self.size
        Label:
            id: subtitle_label
            text: root.subtitle
            font_size: dp(11)
            color: root.sub_color
            halign: "left"
            valign: "top"
            text_size: self.size

    # Progress bar (optional)
    BoxLayout:
        size_hint_y: None
        height: dp(8) if root.show_bar else 0
        opacity: 1 if root.show_bar else 0
        canvas.before:
            Color:
                rgba: root.bar_bg
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(4)]
            Color:
                rgba: root.bar_color
            RoundedRectangle:
                pos: self.pos
                size: (self.width * min(1, root.bar_pct / 100), self.height)
                radius: [dp(4)]

    # Detail rows
    Label:
        size_hint_y: None
        height: dp(16) if root.detail1 else 0
        opacity: 1 if root.detail1 else 0
        text: root.detail1
        font_size: dp(10)
        color: root.detail_color
        halign: "left"
        valign: "middle"
        text_size: self.size
    Label:
        size_hint_y: None
        height: dp(16) if root.detail2 else 0
        opacity: 1 if root.detail2 else 0
        text: root.detail2
        font_size: dp(10)
        color: root.detail_color
        halign: "left"
        valign: "middle"
        text_size: self.size


# ── Root layout ────────────────────────────────────────────────────────────
<RootWidget>:
    orientation: "vertical"

    canvas.before:
        Color:
            rgba: root.bg
        Rectangle:
            pos: self.pos
            size: self.size

    # ── Header bar ──────────────────────────────────────────────────────
    BoxLayout:
        size_hint_y: None
        height: dp(52)
        padding: [dp(12), dp(8)]
        spacing: dp(8)

        canvas.before:
            Color:
                rgba: root.card_bg
            Rectangle:
                pos: self.pos
                size: self.size

        Label:
            text: "⚡ KingWatch Pro v15"
            font_size: dp(15)
            bold: True
            color: root.text_col
            halign: "left"
            valign: "middle"
            text_size: self.size
            size_hint_x: 1

        # Theme cycle button ◑
        Button:
            text: "◑"
            size_hint: None, None
            size: dp(36), dp(36)
            font_size: dp(18)
            background_color: root.accent
            color: 0, 0, 0, 1
            on_release: root.cycle_theme()

        # Collapse toggle _
        Button:
            text: "_"
            size_hint: None, None
            size: dp(36), dp(36)
            font_size: dp(18)
            background_color: root.dim_col
            color: root.text_col
            on_release: root.toggle_collapse()

    # ── Stat cards (hidden when collapsed) ──────────────────────────────
    ScrollView:
        opacity: 0 if root.collapsed else 1
        size_hint_y: 0 if root.collapsed else 1

        GridLayout:
            cols: 1
            size_hint_y: None
            height: self.minimum_height
            spacing: dp(10)
            padding: dp(10)

            StatCard:
                id: cpu_card
                title: "CPU"
                bg_color: root.card_bg
                title_color: root.dim_col
                bar_color: root.accent
                value_color: root.accent

            StatCard:
                id: ram_card
                title: "RAM"
                bg_color: root.card_bg
                title_color: root.dim_col
                bar_color: root.accent
                value_color: root.accent

            StatCard:
                id: storage_card
                title: "Storage"
                bg_color: root.card_bg
                title_color: root.dim_col
                bar_color: root.warn
                value_color: root.warn

            StatCard:
                id: battery_card
                title: "Battery"
                bg_color: root.card_bg
                title_color: root.dim_col
                bar_color: root.accent
                value_color: root.accent

            StatCard:
                id: network_card
                title: "Network"
                bg_color: root.card_bg
                title_color: root.dim_col
                show_bar: False
                value_color: root.accent

            StatCard:
                id: thermal_card
                title: "Thermal"
                bg_color: root.card_bg
                title_color: root.dim_col
                bar_color: root.danger
                value_color: root.danger

            StatCard:
                id: fps_card
                title: "FPS"
                bg_color: root.card_bg
                title_color: root.dim_col
                bar_color: root.accent
                value_color: root.accent

[app]
title = KingWatch Pro
package.name = kingwatchpro

package.domain = com.kingwatch

source.dir = .

source.include_exts = py,png,jpg,kv,atlas,json,ttf

source.exclude_dirs = tests,bin,.buildozer,.git,pycache,python-apk-source

version = 1.5.0

requirements = python3,kivy==2.3.0,pyjnius,plyer,pillow

orientation = portrait
fullscreen = 0
android.permissions = \

    INTERNET,\
    ACCESS_NETWORK_STATE,\
    ACCESS_WIFI_STATE,\
    READ_PHONE_STATE,\
    BATTERY_STATS,\
    REQUEST_INSTALL_PACKAGES,\
    FOREGROUND_SERVICE,\
    FOREGROUND_SERVICE_DATA_SYNC,\
    POST_NOTIFICATIONS,\
    RECEIVE_BOOT_COMPLETED,\
    WAKE_LOCK,\
    VIBRATE,\
    REQUEST_IGNORE_BATTERY_OPTIMIZATIONS
android.api = 35

android.minapi = 21

android.ndk = 25b

android.ndk_api = 21

android.archs = arm64-v8a, armeabi-v7a

android.accept_sdk_license = True

android.enable_androidx = True

android.foreground_service_types = dataSync

[buildozer]
log_level = 2
warn_on_root = 1
name: Build KingWatch Pro APK

on:
  push:
    branches: [main, master]
  workflow_dispatch:

jobs:
build-apk:

    name: Build APK with Buildozer
    runs-on: ubuntu-22.04

    steps:
      # ── 1. Checkout ──────────────────────────────────────────────────────
      - name: Checkout repository
        uses: actions/checkout@v4

      # ── 2. Set up Python 3.11 ────────────────────────────────────────────
      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      # ── 3. System dependencies ───────────────────────────────────────────
      - name: Install system dependencies
        run: |
          sudo apt-get update -qq
          sudo apt-get install -y --no-install-recommends \
            git zip unzip openjdk-17-jdk \
            autoconf libtool pkg-config \
            zlib1g-dev libncurses5-dev libncursesw5-dev \
            libffi-dev libssl-dev \
            libltdl-dev libsqlite3-dev \
            python3-pip python3-setuptools python3-venv \
            ccache

      # ── 4. Cache Buildozer / Android SDK + NDK ───────────────────────────
      - name: Cache Buildozer global directory
        uses: actions/cache@v4
        with:
          path: ~/.buildozer
          key: buildozer-${{ hashFiles('buildozer.spec') }}-v1

      - name: Cache pip packages
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: pip-${{ hashFiles('buildozer.spec') }}-v1

      # ── 5. Install Buildozer + Cython ─────────────────────────────────────
      - name: Install Buildozer and Cython
        run: |
          pip install --upgrade pip
          pip install buildozer cython

      # ── 6. Build APK ──────────────────────────────────────────────────────
      - name: Build APK (debug)
        run: buildozer android debug
        env:
          JAVA_HOME: /usr/lib/jvm/java-17-openjdk-amd64

      # ── 7. Upload APK artifact ───────────────────────────────────────────
      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: KingWatchPro-debug
          path: bin/*.apk
          if-no-files-found: error
          retention-days: 30