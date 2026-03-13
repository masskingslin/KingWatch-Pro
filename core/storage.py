import os


def get_storage():
    try:
        path = '/sdcard' if os.path.exists('/sdcard') else '/'
        st    = os.statvfs(path)
        total = st.f_blocks * st.f_frsize
        free  = st.f_bfree  * st.f_frsize
        used  = total - free
        pct   = round(used / total * 100) if total else 0
        totgb = round(total / 1073741824, 1)
        usgb  = round(used  / 1073741824, 1)
        return {
            'pct':      pct,
            'value':    '%.0f%%' % pct,
            'subtitle': '%.1f GB' % usgb,
            'detail1':  '%.1f GB / %.1f GB' % (usgb, totgb),
        }
    except Exception:
        return {'pct': 0, 'value': 'N/A', 'subtitle': '', 'detail1': ''}
