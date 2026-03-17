"""
KingWatch Pro - core/storage.py
Internal storage stats via os.statvfs. No psutil.
"""
import os


def _bytes_to_human(b: int) -> str:
    if b >= 1_000_000_000:
        return f"{b / 1_000_000_000:.1f} GB"
    if b >= 1_000_000:
        return f"{b / 1_000_000:.1f} MB"
    return f"{b / 1_000:.0f} KB"


def get_storage() -> dict:
    paths = ["/sdcard", "/storage/emulated/0", "/data", "/"]
    for p in paths:
        try:
            stat  = os.statvfs(p)
            total = stat.f_blocks * stat.f_frsize
            free  = stat.f_bavail * stat.f_frsize
            used  = total - free
            pct   = (used / total * 100) if total > 0 else 0.0
            return {
                "pct":   pct,
                "used":  _bytes_to_human(used),
                "free":  _bytes_to_human(free),
                "total": _bytes_to_human(total),
            }
        except Exception:
            continue
    return {"pct": 0.0, "used": "N/A", "free": "N/A", "total": "N/A"}