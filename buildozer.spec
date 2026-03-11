[app]

# App metadata
title = KingWatch Pro
package.name = kingwatchpro
package.domain = com.kingwatch

# Source
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,ttf,otf,wav,mp3,ogg
source.exclude_dirs = tests, bin, .buildozer, .git, __pycache__, venv, .venv

# Entry point — must match your actual filename
source.main = main.py

# Version
version = 1.0.0

# Requirements — keep minimal; psutil must be compiled via recipe
requirements = python3,kivy==2.3.0,plyer,psutil

# Orientation
orientation = portrait

# Fullscreen
fullscreen = 0

# Android configuration
android.permissions = INTERNET,READ_PHONE_STATE,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,BATTERY_STATS,FOREGROUND_SERVICE,RECEIVE_BOOT_COMPLETED,WAKE_LOCK,VIBRATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.ndk_api = 21

# Architecture — build both for wide compatibility
android.archs = arm64-v8a, armeabi-v7a

# Accept SDK licenses automatically
android.accept_sdk_license = True

# Gradle
android.gradle_dependencies = 

# Enable AndroidX
android.enable_androidx = True

# Release / debug
android.release_artifact = apk
android.debug_artifact = apk

# logcat filters
android.logcat_filters = *:S python:D

# Copy libs
android.add_libs_armeabi_v7a = 

# Wakelock
android.wakelock = False

# Activity launch mode
android.activity_launch_mode = standard

# Allow backup
android.allow_backup = True

# Icons — optional; comment out if you don't have icon.png
# icon.filename = %(source.dir)s/icon.png
# presplash.filename = %(source.dir)s/presplash.png

[buildozer]

# Log level: 0=error, 1=info, 2=debug
log_level = 2

# Warn on root
warn_on_root = 1

# Build directory
build_dir = ./.buildozer

# Bin dir
bin_dir = ./bin