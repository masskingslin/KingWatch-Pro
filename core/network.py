def get_network():
    global _ping_started

    if not _ping_started:
        _ping_started = True
        threading.Thread(target=_ping_worker, daemon=True).start()

    rx, tx = _read_bytes()
    now = time.time()

    ping_str = f"{_ping_ms} ms" if _ping_ms else "Pinging..."
    iface = _active_iface()

    if not _bw:
        _bw.update({"rx": rx, "tx": tx, "t": now})
        return {"dl": "--", "ul": "--", "ping": ping_str, "iface": iface}

    dt = now - _bw["t"]
    if dt <= 0:
        return {"dl": "--", "ul": "--", "ping": ping_str, "iface": iface}

    dl_bps = max(0, (rx - _bw["rx"]) / dt)
    ul_bps = max(0, (tx - _bw["tx"]) / dt)

    dl_str = _fmt(dl_bps)
    ul_str = _fmt(ul_bps)

    _bw.update({"rx": rx, "tx": tx, "t": now})

    return {
        "dl": dl_str,
        "ul": ul_str,
        "ping": ping_str,
        "iface": iface
    }