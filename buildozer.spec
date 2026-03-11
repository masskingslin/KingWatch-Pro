[app]

title = KingWatch Pro
package.name = kingwatchpro
package.domain = org.kingai

source.dir = .
source.include_exts = py,kv,png,jpg,json

version = 1.0

# Dependencies
requirements = python3,kivy==2.2.1,pyjnius

# UI
orientation = portrait
fullscreen = 0

# Android configuration
android.api = 33
android.minapi = 21
android.ndk = 25c
android.accept_sdk_license = True
android.enable_androidx = True

# Build architectures
android.archs = arm64-v8a,armeabi-v7a

# Permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK,FOREGROUND_SERVICE,POST_NOTIFICATIONS

# AndroidX dependencies
android.gradle_dependencies = androidx.appcompat:appcompat:1.6.1,androidx.core:core:1.12.0

# Logging
log_level = 2

# Kivy bootstrap
p4a.bootstrap = sdl2


[buildozer]
warn_on_root = 1