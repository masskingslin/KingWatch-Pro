from jnius import autoclass

Context = autoclass('android.content.Context')
BatteryManager = autoclass('android.os.BatteryManager')
PythonActivity = autoclass('org.kivy.android.PythonActivity')

activity = PythonActivity.mActivity

def get_battery():

    bm = activity.getSystemService(Context.BATTERY_SERVICE)

    level = bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
    current = bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CURRENT_NOW)

    current = current / 1000

    return level, int(current)
