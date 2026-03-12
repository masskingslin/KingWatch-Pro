[app]
title = KingWatch Pro
package.name = kingwatchpro
package.domain = com.kingwatch

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf
source.exclude_dirs = tests,bin,.buildozer,.git,__pycache__

version = 1.0.1

requirements = python3,kivy==2.3.0,plyer,pillow

orientation = portrait
fullscreen = 0

# Safe Android permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,FOREGROUND_SERVICE,RECEIVE_BOOT_COMPLETED,WAKE_LOCK,VIBRATE

# Android SDK versions (Play Protect safe)
android.api = 33
android.minapi = 23
android.ndk = 25b
android.ndk_api = 23

# Architectures
android.archs = arm64-v8a, armeabi-v7a

# Play Store compatibility
android.accept_sdk_license = True
android.enable_androidx = True

# Gradle + Play Protect compatibility
android.gradle_dependencies = com.android.tools.build:gradle:7.4.2

# App behaviour
android.allow_backup = True

# Metadata
android.manifest.intent_filters = android.intent.action.MAIN,android.intent.category.LAUNCHER


[buildozer]
log_level = 2
warn_on_root = 1