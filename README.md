⚡ KingWatch Pro v15
Real-time Android system monitor built with Python + Kivy
CPU · RAM · Network · Battery · Temperature · Storage
Android 5.0 → 15 · Google Play Policy Compliant · No Root Required
📱 Screenshots
Dashboard
Themes
Collapsed
Arc gauges auto-color Green→Amber→Red
8 themes: DARK CYBER OCEAN LAVA AMOLED PURPLE GOLD MINT
Tap _ to collapse to title bar
✨ Features
Arc Gauges — CPU, RAM, Battery as circular canvas widgets with dynamic color
1-Second Updates — all stats refresh every second via Clock.schedule_interval
8 Color Themes — tap ◑ to cycle: DARK · CYBER · OCEAN · LAVA · AMOLED · PURPLE · GOLD · MINT
Collapse Mode — tap _ to shrink to a floating title bar
Background Monitoring — foreground service keeps stats alive when screen is off
Boot Restart — monitoring resumes automatically after device reboot
OEM Compatible — tested strategy chains for Samsung, Xiaomi, OnePlus, Oppo, Vivo, Huawei
🏗️ Project Structure
KingWatchPro/
├── main.py                    # App entry point, Dashboard widget, update loop
├── kingwatch.kv               # Kivy UI layout (gauges, theme button, collapse)
├── android_service.py         # Foreground service (Android 8–15)
├── buildozer.spec             # Build config + all permissions declared
├── requirements.txt           # kivy, pyjnius, android
├── systemstats/
│   ├── __init__.py
│   ├── cpu.py                 # Triple-strategy: /proc/stat → UsageStats → /proc/self/stat
│   ├── ram.py                 # ActivityManager.MemoryInfo
│   ├── network.py             # TrafficStats + /proc/net/dev fallback
│   ├── battery.py             # BatteryManager + OEM current normalization
│   └── thermal.py             # Battery broadcast + sysfs fallback
├── ui/
│   ├── __init__.py
│   ├── gauges.py              # ArcGauge Kivy canvas widget
│   └── themes.py              # 8 theme color definitions
└── .github/
    └── workflows/
        └── build.yml          # GitHub Actions CI → builds APK automatically
📊 Android Compatibility
Android Version
API
CPU
RAM
Network
Battery
Background
5.0 Lollipop
21
✅ /proc/stat
✅
✅
✅
✅
6.0 Marshmallow
23
✅ /proc/stat
✅
✅
✅
✅
7.0 Nougat
24
✅ /proc/stat
✅
✅
✅
✅
8.0 Oreo
26
✅ /proc/stat
✅
✅
✅
✅ Notif Channel
9.0 Pie
28
⚠️ Needs Usage Access
✅
✅
✅
✅
10 – 13
29–33
⚠️ Needs Usage Access
✅
✅
✅
✅ POST_NOTIF
14 (Upside Down Cake)
34
⚠️ Needs Usage Access
✅
✅
✅
✅ DATA_SYNC type
15 (Vanilla Ice Cream)
35
⚠️ Needs Usage Access
✅
✅
✅
✅
⚠️ = Falls back automatically to /proc/self/stat (app-process CPU) if Usage Access not granted. Tap Grant CPU Access in the dashboard to enable full system-wide tracking.
🔐 Permissions
Permission
Type
Reason
WAKE_LOCK
Normal — auto granted
Prevent CPU sleep during monitoring cycles
FOREGROUND_SERVICE
Normal — auto granted
Background monitoring service
FOREGROUND_SERVICE_DATA_SYNC
Normal — auto granted
Android 14+ mandatory service type
POST_NOTIFICATIONS
Runtime — user prompted
Show persistent notification on Android 13+
PACKAGE_USAGE_STATS
Special — user grants in Settings
Enhanced CPU monitoring on Android 9+
REQUEST_IGNORE_BATTERY_OPTIMIZATIONS
Normal — system dialog
Survive OEM battery killers (MIUI, EMUI)
RECEIVE_BOOT_COMPLETED
Normal — auto granted
Restart service after reboot
ACCESS_NETWORK_STATE
Normal — auto granted
Network context for TrafficStats
All permissions are Google Play Store policy compliant. No root, no private APIs, no data collection.
🔄 CPU Monitoring Strategy Chain
KingWatch Pro uses a 3-level fallback to maximize accuracy across all Android versions:
1. /proc/stat          → Full system-wide CPU (Android 5–8 + most OEM Android 9+)
        ↓ (blocked by SELinux on stock Android 9+)
2. UsageStatsManager   → Requires "Usage Access" permission in Settings
        ↓ (permission not granted)
3. /proc/self/stat     → Own-process CPU — ALWAYS works on all Android 5–15
The active strategy is shown as a label in the CPU card: [sys-wide] · [usage-stats] · [app-proc]
🏃 Building the APK
Method 1: GitHub Actions (Recommended — no PC needed)
Push all files to the main branch of this repo
Go to Actions tab → watch Build KingWatch Pro v15 APK run
Wait ~10–15 min (first run) · ~4–6 min (cached)
Click the green ✅ run → scroll to Artifacts → download KingWatchPro-v15-debug-N.zip
Extract → install kingwatchpro-debug.apk on your phone
Method 2: Local (Linux/macOS PC with Android Studio installed)
# Install buildozer
pip install buildozer==1.5.0 cython==3.0.11

# Clone repo
git clone https://github.com/YOUR_USERNAME/KingWatchPro.git
cd KingWatchPro

# Build
buildozer android debug

# APK will be at:
# bin/kingwatchpro-15.0-arm64-v8a_armeabi-v7a-debug.apk
⚙️ Build Configuration
Key values in buildozer.spec:
android.api              = 35          # Target Android 15
android.minapi           = 21          # Support Android 5.0+
android.ndk              = 25b         # NDK version
android.build_tools_version = 34.0.0   # Pinned stable (not rc2)
android.archs            = arm64-v8a, armeabi-v7a
android.java_version     = 17
Note: android.sdk key was removed — it is deprecated in buildozer 1.5 and causes a warning. Use android.api only.
📲 Installation & First Launch
Enable Install unknown apps in Settings → Apps → Special app access
Tap the APK file → Install → Open
Grant permissions in order:
① Notifications → tap Allow (Android 13+)
② Battery optimization → tap Allow
③ CPU Access → tap Grant → enable Usage Access for KingWatch Pro
🔧 Known Build Issues & Fixes
Error
Cause
Fix Applied
sdkmanager path .../tools/bin/sdkmanager does not exist
Google removed old tools/ path
CI manually installs cmdline-tools and symlinks to old path
build-tools;37.0.0-rc2 license not accepted
buildozer defaults to rc2 which can't be silently accepted
android.build_tools_version = 34.0.0 pinned in spec
AIDL not found, please install it
Caused by build-tools not installed (above)
Resolved by build-tools pin + CI pre-install
android.sdk is deprecated and ignored
Old config key removed in buildozer 1.5
Removed android.sdk key, using android.api only
No files found: bin/*.apk
APK not built due to above errors
All above fixes together resolve this
🎨 Theme Reference
Theme
Background
Arc Color
Best For
DARK
#0D0D14
Green
Default, easy on eyes
CYBER
#050D1A
Cyan
High contrast
OCEAN
#051220
Sky Blue
Calm monitoring
LAVA
#1A0505
Orange-Red
Heat alerts
AMOLED
#000000
White
True black OLED phones
PURPLE
#0F0520
Violet
Night use
GOLD
#141000
Gold
Premium feel
MINT
#051A14
Mint Green
Low eye strain
📱 OEM Background Monitoring Tips
If monitoring stops when screen turns off:
Phone Brand
Steps
Xiaomi / Redmi / Poco
Settings → Apps → KingWatch → Autostart: ON · Battery Saver → No Restrictions
Samsung
Settings → Apps → KingWatch → Battery → Unrestricted
Huawei / Honor
Phone Manager → Protected Apps → Add KingWatch
Oppo / Realme
Settings → Apps → Power Consumption → Allow Background
Vivo
Settings → Battery → High Background Power → Add KingWatch
OnePlus
Settings → Battery → Don't Optimize → KingWatch
Pixel / Motorola / Nothing
No extra steps needed ✅
🛠️ Tech Stack
Component
Technology
Language
Python 3.11
UI Framework
Kivy 2.3.0
Android Bridge
PyJNIus
Build Tool
Buildozer 1.5.0
CI/CD
GitHub Actions (ubuntu-22.04)
Java
OpenJDK 17 (Temurin)
NDK
Android NDK r25b
Target SDK
Android 35 (Android 15)
Min SDK
Android 21 (Android 5.0)
📄 License
Personal / private use. Not for redistribution without permission.
Built by King AI · Tamil Nadu, India · 2026
