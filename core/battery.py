from kivy.utils import platform

def get_battery():

    if platform != "android":
        return 0,"Unknown"

    try:
        from jnius import autoclass

        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        IntentFilter = autoclass('android.content.IntentFilter')
        Intent = autoclass('android.content.Intent')
        BatteryManager = autoclass('android.os.BatteryManager')

        activity = PythonActivity.mActivity

        intent = activity.registerReceiver(
            None,
            IntentFilter(Intent.ACTION_BATTERY_CHANGED)
        )

        level = intent.getIntExtra(BatteryManager.EXTRA_LEVEL,-1)
        scale = intent.getIntExtra(BatteryManager.EXTRA_SCALE,-1)

        pct = int(level*100/scale)

        return pct,"Discharging"

    except:
        return 0,"Unknown"