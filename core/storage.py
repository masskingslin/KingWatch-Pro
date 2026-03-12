import os

def get_storage():
    for path in ["/sdcard", "/storage/emulated/0", "/data", "/"]:
        try:
            st     = os.statvfs(path)
            total  = st.f_blocks * st.f_frsize
            free   = st.f_bfree  * st.f_frsize
            if total > 0:
                used_pct = round((1 - free / total) * 100, 1)
                used_gb  = round((total - free) / 1024**3, 1)
                total_gb = round(total / 1024**3, 1)
                detail   = f"Used: {used_gb} GB / {total_gb} GB"
                return used_pct, detail
        except Exception:
            continue
    return 0.0, ""
