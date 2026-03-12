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

android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,FOREGROUND_SERVICE,WAKE_LOCK,VIBRATE

android.api = 33
android.minapi = 23

android.ndk = 25b
android.ndk_api = 23

android.archs = arm64-v8a, armeabi-v7a

android.accept_sdk_license = True
android.enable_androidx = True

android.allow_backup = False

android.gradle_dependencies = "com.google.android.play:integrity:1.3.0"

[buildozer]

log_level = 2
warn_on_root = 1