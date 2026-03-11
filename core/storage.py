from jnius import autoclass

StatFs = autoclass('android.os.StatFs')
Environment = autoclass('android.os.Environment')

class StorageMonitor:

    def read(self):

        path = Environment.getDataDirectory().getPath()
        stat = StatFs(path)

        total = stat.getBlockCountLong() * stat.getBlockSizeLong()
        free = stat.getAvailableBlocksLong() * stat.getBlockSizeLong()

        used = total - free

        percent = used / total * 100

        return percent, used, total
