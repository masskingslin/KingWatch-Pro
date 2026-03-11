[app]

# ─────────────────────────────────────────
# App Identity
# ─────────────────────────────────────────
title = KingWatch Pro
package.name = kingwatchpro
package.domain = org.kingai

source.dir = .
source.include_exts = py,kv,png,jpg,atlas,json
source.include_patterns = assets/*

version = 16.0

# ─────────────────────────────────────────
# Requirements
# ─────────────────────────────────────────
requirements = python3,kivy==2.2.1,pyjnius

# ─────────────────────────────────────────
# Orientation / UI
# ─────────────────────────────────────────
orientation = portrait
fullscreen = 0

# ─────────────────────────────────────────
# Android API Levels
# ─────────────────────────────────────────
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a

# Automatically accept licenses (CI builds)
android.accept_sdk_license = True

# ─────────────────────────────────────────
# Architectures
# ─────────────────────────────────────────
android.archs = arm64-v8a, armeabi-v7a

# ─────────────────────────────────────────
# Permissions (Play Store Safe)
# ─────────────────────────────────────────
android.permissions = \
    INTERNET, \
    ACCESS_NETWORK_STATE, \
    WAKE_LOCK, \
    FOREGROUND_SERVICE, \
    POST_NOTIFICATIONS

# ─────────────────────────────────────────
# AndroidX Support
# ─────────────────────────────────────────
android.enable_androidx = True

android.gradle_dependencies = \
    androidx.appcompat:appcompat:1.7.0, \
    androidx.core:core:1.13.1

# ─────────────────────────────────────────
# Java Version
# ─────────────────────────────────────────
android.java_version = 17

# ─────────────────────────────────────────
# App Appearance
# ─────────────────────────────────────────
presplash.color = #0D0F18

android.meta_data = \
    android.max_aspect=2.4

# ─────────────────────────────────────────
# Logging
# ─────────────────────────────────────────
log_level = 2


# =================================================
# Buildozer Settings
# =================================================
[buildozer]

log_level = 2
warn_on_root = 1