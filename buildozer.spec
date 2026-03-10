[app]

title = KingWatch Pro
package.name = kingwatchpro
package.domain = org.kingai
version = 15.0

source.dir = .
source.include_exts = py,kv,png,jpg,atlas,json
source.include_patterns = assets/*

requirements = python3,kivy==2.3.0,pyjnius

android.api = 33
android.minapi = 21
android.ndk = 25c

android.accept_sdk_license = True
android.build_tools_version = 34.0.0

android.archs = arm64-v8a, armeabi-v7a

android.permissions = \
    android.permission.WAKE_LOCK, \
    android.permission.FOREGROUND_SERVICE, \
    android.permission.FOREGROUND_SERVICE_DATA_SYNC, \
    android.permission.POST_NOTIFICATIONS, \
    android.permission.PACKAGE_USAGE_STATS, \
    android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS, \
    android.permission.RECEIVE_BOOT_COMPLETED, \
    android.permission.ACCESS_NETWORK_STATE

android.enable_androidx = True
android.gradle_dependencies = \
    androidx.appcompat:appcompat:1.7.0, \
    androidx.core:core:1.13.1

android.java_version = 17

android.meta_data = \
    android.max_aspect=2.4, \
    org.kivy.android.foreground_service_type=dataSync

orientation = portrait
fullscreen = 0

presplash.color = #0D0D12

log_level = 2

[buildozer]
log_level = 2
warn_on_root = 1
