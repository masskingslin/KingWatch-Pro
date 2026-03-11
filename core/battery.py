from jnius import autoclass

PythonActivity = autoclass('org.kivy.android.PythonActivity')
BatteryManager = autoclass('android.os.BatteryManager')

class BatteryMonitor:

    def read(self):

        activity = PythonActivity.mActivity
        bm = activity.getSystemService(activity.BATTERY_SERVICE)

        level = bm.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)

        return level
