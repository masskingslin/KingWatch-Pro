import shutil

def get_storage():
    total, used, free = shutil.disk_usage("/")

    pct = used / total * 100

    return round(pct,1), used, total