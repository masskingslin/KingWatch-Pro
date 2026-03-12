import os

def get_storage():
    for path in ["/sdcard", "/storage/emulated/0", "/data", "/"]:
        try:
            st = os.statvfs(path)
            total = st.f_blocks * st.f_frsize
            free  = st.f_bfree  * st.f_frsize
            if total > 0:
                return round((1 - free / total) * 100, 1)
        except Exception:
            continue
    return 0.0