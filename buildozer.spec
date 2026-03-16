[app]
title = KingWatch Pro
package.name = kingwatchpro
package.domain = com.kingwatch
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf
source.exclude_dirs = tests,bin,.buildozer,.git,__pycache__,python-apk-source
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
