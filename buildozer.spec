# ─────────────────────────────────────────────
#  KingWatch Pro — buildozer.spec
#  Google Play Protect compliant
# ─────────────────────────────────────────────

[app]
title = KingWatch Pro
package.name = kingwatchpro
package.domain = com.kingwatch

source.dir = .
source.include_exts = py,kv
source.exclude_dirs = tests,bin,.buildozer,.git,__pycache__,*.egg-info

version = 3.0.0

# ── Requirements ───────────────────────────
# NO psutil — pure Android /proc + /sys reads
requirements = python3,kivy==2.3.0,plyer,pillow

# ── Display ────────────────────────────────
orientation = portrait
fullscreen   = 0

# ── Permissions ────────────────────────────
# ONLY 3 permissions — each justified:
# INTERNET              → ping latency check (socket to 8.8.8.8:53)
# ACCESS_NETWORK_STATE  → read /proc/net/dev for speed
# ACCESS_WIFI_STATE     → read /proc/net/wireless for signal
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE

# ── Android SDK ────────────────────────────
android.api    = 33
android.minapi = 21
android.ndk    = 25b
android.ndk_api = 21
android.archs  = arm64-v8a, armeabi-v7a

# ── Play Protect compliance ─────────────────
android.accept_sdk_license = True
android.enable_androidx    = True
android.allow_backup       = False   # no user data to backup
android.wakelock           = False   # no background CPU hold

# ── App metadata ───────────────────────────
# These help Play Store classify the app correctly
android.add_aars =

[buildozer]
log_level    = 2
warn_on_root = 1