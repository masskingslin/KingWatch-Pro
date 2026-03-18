"""KingWatch Pro v17 - core/ram.py"""

def _parse_meminfo():
    info = {}
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    info[parts[0].rstrip(":")] = int(parts[1])
    except Exception:
        pass
    return info

def _kb_to_human(kb):
    if kb >= 1024 * 1024:
        return f"{kb/(1024*1024):.1f} GB"
    return f"{kb/1024:.0f} MB"

def get_ram() -> tuple:
    """Return (used_pct, used_label, free_label)."""
    info     = _parse_meminfo()
    total    = info.get("MemTotal",    0)
    free     = info.get("MemFree",     0)
    buffers  = info.get("Buffers",     0)
    cached   = info.get("Cached",      0)
    sreclm   = info.get("SReclaimable",0)
    avail    = info.get("MemAvailable",0)

    used = max(0, total - free - buffers - cached - sreclm)
    pct  = (used / total * 100) if total > 0 else 0.0

    # Use MemAvailable if present (more accurate on Android)
    free_kb = avail if avail > 0 else max(0, free + cached + sreclm)

    label      = f"{_kb_to_human(used)} / {_kb_to_human(total)}"
    free_label = f"Free: {_kb_to_human(free_kb)}"
    return pct, label, free_label
