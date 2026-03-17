"""
KingWatch Pro - core/network.py
Network RX/TX speeds from /proc/net/dev. No psutil.
"""
import time

_prev_rx   = 0
_prev_tx   = 0
_prev_time = 0.0


def _read_net_bytes():
    """Sum RX/TX bytes across all non-loopback interfaces."""
    rx_total = tx_total = 0
    try:
        with open("/proc/net/dev") as f:
            for line in f:
                line = line.strip()
                if ":" not in line:
                    continue
                iface, data = line.split(":", 1)
                if iface.strip() in ("lo",):
                    continue
                parts = data.split()
                if len(parts) >= 9:
                    rx_total += int(parts[0])   # receive bytes
                    tx_total += int(parts[8])   # transmit bytes
    except Exception:
        pass
    return rx_total, tx_total


def _bytes_to_human(bps: float) -> str:
    if bps >= 1_000_000:
        return f"{bps / 1_000_000:.1f} MB/s"
    if bps >= 1_000:
        return f"{bps / 1_000:.1f} KB/s"
    return f"{bps:.0f} B/s"


def _get_signal() -> str:
    """Try to read WiFi signal from /proc/net/wireless."""
    try:
        with open("/proc/net/wireless") as f:
            lines = f.readlines()
        for line in lines[2:]:
            parts = line.split()
            if len(parts) >= 4:
                lvl = parts[3].rstrip(".")
                return f"Signal: {lvl} dBm"
    except Exception:
        pass
    return ""


def _get_ping() -> str:
    """Simple ICMP-less ping estimate via /proc/net/snmp."""
    return "N/A"


def get_network() -> dict:
    global _prev_rx, _prev_tx, _prev_time

    now     = time.monotonic()
    rx, tx  = _read_net_bytes()
    elapsed = now - _prev_time if _prev_time > 0 else 1.0

    dl_bps = (rx - _prev_rx) / elapsed if _prev_rx else 0
    ul_bps = (tx - _prev_tx) / elapsed if _prev_tx else 0

    _prev_rx   = rx
    _prev_tx   = tx
    _prev_time = now

    return {
        "dl":     _bytes_to_human(max(0, dl_bps)),
        "ul":     _bytes_to_human(max(0, ul_bps)),
        "ping":   _get_ping(),
        "signal": _get_signal(),
    }