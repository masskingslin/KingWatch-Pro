def get_bat():
    if platform == "android":
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            IntentFilter = autoclass('android.content.IntentFilter')
            BatteryManager = autoclass('android.os.BatteryManager')

            activity = PythonActivity.mActivity
            ifilter = IntentFilter(Intent.ACTION_BATTERY_CHANGED)
            battery = activity.registerReceiver(None, ifilter)

            level = battery.getIntExtra(BatteryManager.EXTRA_LEVEL, -1)
            scale = battery.getIntExtra(BatteryManager.EXTRA_SCALE, -1)
            status = battery.getIntExtra(BatteryManager.EXTRA_STATUS, -1)

            pct = int((level / float(scale)) * 100)
            charging = status == BatteryManager.BATTERY_STATUS_CHARGING

            return pct, ("Charging" if charging else "Discharging")
        except:
            return 0, "Unknown"
    return 0, "Unknown"