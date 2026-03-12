import os


class StorageMonitor:

    def get(self):
        try:
            st = os.statvfs("/")
            total = st.f_blocks * st.f_frsize
            free = st.f_bfree * st.f_frsize

            used = total - free

            return int((used / total) * 100)

        except:
            return 60