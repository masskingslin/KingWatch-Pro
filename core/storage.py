import os


def get_storage():

    try:
        s = os.statvfs("/")

        total = s.f_blocks * s.f_frsize
        free = s.f_bavail * s.f_frsize
        used = total - free

        pct = (used / total) * 100

        return {
            "pct": pct,
            "used": f"{used//(1024**3)}GB",
            "total": f"{total//(1024**3)}GB"
        }

    except:
        return {"pct": 0, "used": "0", "total": "0"}