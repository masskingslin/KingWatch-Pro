[app]
title = KingWatch Pro
package.name = kingwatchpro
package.domain = com.kingwatch
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf
source.exclude_dirs = tests,bin,.buildozer,.git,__pycache__
version = 1.0.0
requirements = python3,kivy==2.3.0,plyer,psutil,pillow
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,READ_PHONE_STATE,BATTERY_STATS,FOREGROUND_SERVICE,RECEIVE_BOOT_COMPLETED,WAKE_LOCK,VIBRATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.sdk = 33
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
android.enable_androidx = True

[buildozer]
log_level = 2
warn_on_root = 1