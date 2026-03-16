import os


def get_storage():
    """
    Returns dict:
        pct   – used % (float)
        used  – e.g. "42GB"
        total – e.g. "128GB"
    """
    try:
        s     = os.statvfs("/")
        total = s.f_blocks * s.f_frsize
        free  = s.f_bavail * s.f_frsize
        used  = total - free
        pct   = round((used / total) * 100, 1) if total else 0

        def _gb(b):
            return f"{b // (1024 ** 3)}GB"

        return {"pct": pct, "used": _gb(used), "total": _gb(total)}

    except Exception:
        return {"pct": 0, "used": "0GB", "total": "0GB"}
