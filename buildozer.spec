[app]

# ── Identity ──────────────────────────────────────────────────────────────
title           = KingWatch Pro
package.name    = kingwatchpro
package.domain  = org.kingai
version         = 15.0

# ── Source ────────────────────────────────────────────────────────────────
source.dir              = .
source.include_exts     = py,kv,png,jpg,atlas,json
source.include_patterns = assets/*

# ── Requirements ──────────────────────────────────────────────────────────
# python3      : CPython 3.11 bundled by p4a
# kivy         : 2.3.0 — stable, Play-safe
# pyjnius      : Android Java bridge (needed for all android.* calls)
# android      : python-for-android permissions helper
requirements = python3==3.11.0,kivy==2.3.0,pyjnius,android

# ── API Levels ────────────────────────────────────────────────────────────
# minapi 21 = Android 5.0  (covers 99%+ active devices globally)
# api    35 = Android 15   (latest stable as of 2026)
android.api    = 35
android.minapi = 21
android.ndk    = 25b
android.sdk    = 35

# ── Architectures ─────────────────────────────────────────────────────────
# arm64-v8a   : All modern phones (2017+)
# armeabi-v7a : Older / budget devices (Android 5-7 era)
android.archs = arm64-v8a, armeabi-v7a

# ── Permissions (Google Play Policy Compliant) ────────────────────────────
#
# WAKE_LOCK
#   Type    : Normal (auto-granted at install)
#   Reason  : Prevents CPU sleep during 1-second monitoring cycles
#
# FOREGROUND_SERVICE
#   Type    : Normal (auto-granted)
#   Reason  : Run persistent monitoring service when app is in background
#
# FOREGROUND_SERVICE_DATA_SYNC
#   Type    : Normal (auto-granted), API 34+ only
#   Reason  : Mandatory service type declaration for Android 14+
#             DATA_SYNC = periodic data collection — correct for monitors
#
# POST_NOTIFICATIONS
#   Type    : Runtime (user prompted once on first launch), API 33+ only
#   Reason  : Show persistent monitoring notification on Android 13+
#
# PACKAGE_USAGE_STATS
#   Type    : Special (user grants in Settings > Usage Access)
#   Reason  : Enhanced system-wide CPU tracking on Android 9+
#             Falls back to /proc/stat or /proc/self/stat if not granted
#             Declared here — does NOT violate Play Store policy
#
# REQUEST_IGNORE_BATTERY_OPTIMIZATIONS
#   Type    : Normal — shows one system dialog
#   Reason  : Exempt app from Doze mode & OEM battery killers (MIUI/EMUI)
#             Play policy allows this for background monitoring apps
#
# RECEIVE_BOOT_COMPLETED
#   Type    : Normal (auto-granted)
#   Reason  : Restart monitoring service after device reboot
#
# ACCESS_NETWORK_STATE
#   Type    : Normal (auto-granted)
#   Reason  : Used by TrafficStats context; no data is transmitted
#
android.permissions = \
    android.permission.WAKE_LOCK, \
    android.permission.FOREGROUND_SERVICE, \
    android.permission.FOREGROUND_SERVICE_DATA_SYNC, \
    android.permission.POST_NOTIFICATIONS, \
    android.permission.PACKAGE_USAGE_STATS, \
    android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, \
    android.permission.RECEIVE_BOOT_COMPLETED, \
    android.permission.ACCESS_NETWORK_STATE

# ── AndroidX ──────────────────────────────────────────────────────────────
android.enable_androidx       = True
android.gradle_dependencies   = \
    androidx.appcompat:appcompat:1.7.0, \
    androidx.core:core:1.13.1

# ── Java version ──────────────────────────────────────────────────────────
android.java_version = 17

# ── Foreground service type (Android 14+) ─────────────────────────────────
# Required: android:foregroundServiceType="dataSync" in generated manifest
# p4a injects this via the meta-data entry below
android.meta_data = \
    android.max_aspect=2.4, \
    org.kivy.android.foreground_service_type=dataSync

# ── Display ───────────────────────────────────────────────────────────────
orientation = portrait
fullscreen  = 0

# ── Icons / splash ────────────────────────────────────────────────────────
# icon.filename    = %(source.dir)s/assets/icon.png
# presplash.filename = %(source.dir)s/assets/splash.png
presplash.color  = #0D0D12

# ── Build log ─────────────────────────────────────────────────────────────
log_level = 2

[buildozer]
log_level   = 2
warn_on_root = 1
