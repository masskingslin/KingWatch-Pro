from jnius import autoclass

IntentFilter = autoclass('android.content.IntentFilter')
PythonActivity = autoclass('org.kivy.android.PythonActivity')
Intent = autoclass('android.content.Intent')

activity = PythonActivity.mActivity

def get_temperature():

    filter = IntentFilter(Intent.ACTION_BATTERY_CHANGED)

    battery = activity.registerReceiver(None, filter)

    temp = battery.getIntExtra("temperature", 0)

    return temp / 10
