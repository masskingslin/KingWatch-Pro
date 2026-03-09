from jnius import autoclass

ActivityManager = autoclass('android.app.ActivityManager')
Context = autoclass('android.content.Context')
PythonActivity = autoclass('org.kivy.android.PythonActivity')

activity = PythonActivity.mActivity

def get_ram_usage():

    am = activity.getSystemService(Context.ACTIVITY_SERVICE)

    MemoryInfo = autoclass('android.app.ActivityManager$MemoryInfo')
    mem = MemoryInfo()

    am.getMemoryInfo(mem)

    total = mem.totalMem
    avail = mem.availMem

    used = total - avail

    return (used / total) * 100
