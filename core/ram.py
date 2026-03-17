"""
KingWatch Pro - core/ram.py
RAM usage from /proc/meminfo. No psutil.
"""


def _parse_meminfo() -> dict:
    info = {}
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0].rstrip(":")
                    info[key] = int(parts[1])  # values in kB
    except Exception:
        pass
    return info


def _kb_to_human(kb: int) -> str:
    if kb >= 1024 * 1024:
        return f"{kb / (1024 * 1024):.1f} GB"
    return f"{kb / 1024:.0f} MB"


def get_ram() -> tuple:
    """Return (used_pct: float, label: str)."""
    info = _parse_meminfo()
    total    = info.get("MemTotal", 0)
    free     = info.get("MemFree", 0)
    buffers  = info.get("Buffers", 0)
    cached   = info.get("Cached", 0)
    s_reclm  = info.get("SReclaimable", 0)

    used = total - free - buffers - cached - s_reclm
    used = max(0, used)

    pct = (used / total * 100) if total > 0 else 0.0
    label = f"{_kb_to_human(used)} / {_kb_to_human(total)}"
    return pct, label