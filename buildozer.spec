[app]

title = KingWatch Pro
package.name = kingwatchpro
package.domain = org.kingai

source.dir = .
source.include_exts = py,kv,png,jpg,json

version = 1.0

# ── Dependencies ────────────────────────────────────────────────────────────
# python3 is implicit — do NOT list it alone, causes recipe conflicts
# kivy pinned to last stable; pyjnius needed for Java bridge
requirements = python3,kivy==2.2.1,pyjnius

# ── Orientation / UI ────────────────────────────────────────────────────────
orientation = portrait
fullscreen = 0

# ── Android SDK / NDK ───────────────────────────────────────────────────────
android.api = 33
android.minapi = 21

# NDK 25b does NOT exist — 25c is the correct release tag
android.ndk = 25c

# android.sdk is DEPRECATED and breaks newer buildozer — removed
# android.sdk = 31   ← DO NOT USE

# Accept SDK licenses automatically (build hangs forever without this)
android.accept_sdk_license = True

# androidx.* deps require this flag — omitting it causes R8/D8 crashes
android.enable_androidx = True

# Build one arch first for CI speed; add armeabi-v7a after first success
android.archs = arm64-v8a

# ── Permissions ─────────────────────────────────────────────────────────────
android.permissions = \
    INTERNET, \
    ACCESS_NETWORK_STATE, \
    WAKE_LOCK, \
    FOREGROUND_SERVICE, \
    POST_NOTIFICATIONS

# ── Gradle dependencies ─────────────────────────────────────────────────────
# 1.7.0 has a broken transitive dep on some NDK25c toolchains — use 1.6.1
android.gradle_dependencies = \
    androidx.appcompat:appcompat:1.6.1, \
    androidx.core:core:1.12.0

# ── Assets (create blank files if you don't have custom ones yet) ────────────
# Uncomment when you add real assets:
# icon.filename      = %(source.dir)s/assets/icon.png
# presplash.filename = %(source.dir)s/assets/presplash.png

# ── Logging ─────────────────────────────────────────────────────────────────
log_level = 2

# ── p4a bootstrap ───────────────────────────────────────────────────────────
# sdl2 is correct for Kivy; do not change to webview or service_only
p4a.bootstrap = sdl2

[buildozer]
warn_on_root = 1