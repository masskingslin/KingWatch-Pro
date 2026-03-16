import shutil


def get_storage():

    total, used, free = shutil.disk_usage("/")

    pct = used / total * 100

    total_gb = total / (1024**3)
    used_gb = used / (1024**3)

    detail = f"{used_gb:.1f} GB / {total_gb:.1f} GB"

    return pct, detail