[app]

title = KingWatch Pro
package.name = kingwatchpro
package.domain = org.kingai

source.dir = .
source.include_exts = py,kv,png,jpg,json

version = 1.0

requirements = python3,kivy,pyjnius

orientation = portrait
fullscreen = 0

android.api = 31
android.minapi = 21
android.sdk = 31
android.ndk = 25b
android.archs = arm64-v8a,armeabi-v7a

android.permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK,FOREGROUND_SERVICE,POST_NOTIFICATIONS

log_level = 2

android.gradle_dependencies = androidx.appcompat:appcompat:1.7.0,androidx.core:core:1.13.1

[buildozer]
warn_on_root = 1