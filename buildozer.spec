[app]

# App Info
title = KingWatch Pro
package.name = kingwatchpro
package.domain = org.kingai

source.dir = .
source.include_exts = py,kv,png,jpg,atlas,json

version = 1.0

# Python / Kivy requirements
requirements = python3,kivy==2.2.1,pyjnius

# Screen orientation
orientation = portrait

fullscreen = 0

# Android API
android.api = 34
android.minapi = 21

# Android NDK
android.ndk = 25b

# Architectures
android.archs = arm64-v8a, armeabi-v7a

# Accept licenses
android.accept_sdk_license = True

# Permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WAKE_LOCK,FOREGROUND_SERVICE,POST_NOTIFICATIONS

# AndroidX
android.enable_androidx = True

# Gradle dependencies
android.gradle_dependencies = androidx.appcompat:appcompat:1.7.0,androidx.core:core:1.13.1

# Java
android.java_version = 17

# App appearance
presplash.color = #0D0F18

# Logging
log_level = 2


[buildozer]

log_level = 2
warn_on_root = 1