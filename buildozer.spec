[app]
title = King App
package.name = kingapp
package.domain = com.kingai
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt
version = 1.0

# AdMob removed — kivmob removed — no ad dependencies
requirements = python3,kivy==2.3.0,plyer,pyjnius==1.4.2

orientation = portrait

android.permissions = INTERNET, ACCESS_NETWORK_STATE

android.minapi = 24
android.api = 34
android.ndk = 25b
android.build_tools_version = 34.0.0

android.accept_sdk_license = True
android.presplash_color = #1a1a2e

# android.meta_data REMOVED — had AdMob APPLICATION_ID
# android.gradle_dependencies REMOVED — no play-services-ads

[buildozer]
log_level = 2
warn_on_root = 1