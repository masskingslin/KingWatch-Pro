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
requirements = python3==3.11.0,kivy==2.3.0,pyjnius,android

# ── API Levels ────────────────────────────────────────────────────────────
android.api    = 35
android.minapi = 21
android.ndk    = 25b
android.sdk    = 35

# ── FIXED: Pin build-tools to stable 34.0.0 ──────────────────────────────
# Prevents buildozer from grabbing 37.0.0-rc2 (release candidate)
# whose license cannot be auto-accepted in CI → causes AIDL not found
android.build_tools_version = 34.0.0

# ── Architectures ─────────────────────────────────────────────────────────
android.archs = arm64-v8a, armeabi-v7a

# ── Permissions ───────────────────────────────────────────────────────────
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

# ── Foreground service type ───────────────────────────────────────────────
android.meta_data = \
    android.max_aspect=2.4, \
    org.kivy.android.foreground_service_type=dataSync

# ── Display ───────────────────────────────────────────────────────────────
orientation = portrait
fullscreen  = 0

# ── Presplash color ───────────────────────────────────────────────────────
presplash.color = #0D0D12

# ── Build log ─────────────────────────────────────────────────────────────
log_level = 2

[buildozer]
log_level    = 2
warn_on_root = 1
