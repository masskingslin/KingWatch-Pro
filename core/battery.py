"""
KingWatch Pro v17 - core/battery.py
Instant ETA from V×I calculation — no need to wait for drain rate.
Charging:    ETA = (100-pct) / charge_rate_per_min
Discharging: ETA = pct / drain_rate_per_min
Rate derived from current_mA + capacity_mAh from /sys.
"""
import time

_prev_pct  = -1
_prev_time = 0.0
_eta_cache = ""
_cap_mah   = 0   # battery capacity in mAh (cached)

_PS = ["battery","BAT0","BAT1","bms","main-battery","Battery","BATTERY"]

def _sys(key):
    for name in _PS:
        for base in ["/sys/class/power_supply","/sys/bus/platform/drivers"]:
            try:
                with open(f"{base}/{name}/{key}") as f:
                    v = f.read().strip()
                    if v: return v
            except Exception:
                continue
    return None

def _int(v, default=0):
    try: return int(str(v).strip())
    except Exception: return default

def _get_capacity_mah():
    """Read battery design capacity in mAh (cached)."""
    global _cap_mah
    if _cap_mah > 0:
        return _cap_mah
    for key in ("charge_full_design","charge_full","energy_full_design"):
        raw = _sys(key)
        if raw:
            v = _int(raw)
            if v > 100000:        # µAh → mAh
                _cap_mah = v // 1000
            elif v > 500:         # already mAh
                _cap_mah = v
            if _cap_mah > 0:
                return _cap_mah
    # Common phone batteries if not readable
    _cap_mah = 4000
    return _cap_mah

def _fmt_time(minutes):
    """Format minutes to '2h 15m' or '45m'."""
    h, m = divmod(int(minutes), 60)
    if h > 0:
        return f"{h}h {m:02d}m"
    return f"{m}m"

def _pyjnius_battery():
    try:
        from jnius import autoclass  # type: ignore
        PA     = autoclass("org.kivy.android.PythonActivity")
        Intent = autoclass("android.content.Intent")
        IF     = autoclass("android.content.IntentFilter")
        BM     = autoclass("android.os.BatteryManager")
        ctx    = PA.mActivity

        ifilter = IF(Intent.ACTION_BATTERY_CHANGED)
        intent  = ctx.registerReceiver(None, ifilter)

        pct    = intent.getIntExtra(BM.EXTRA_LEVEL, -1)
        scale  = intent.getIntExtra(BM.EXTRA_SCALE, 100)
        status = intent.getIntExtra(BM.EXTRA_STATUS, -1)
        temp   = intent.getIntExtra(BM.EXTRA_TEMPERATURE, 0)
        volt   = intent.getIntExtra(BM.EXTRA_VOLTAGE, 0)  # mV

        STATUS_CHARGING    = 2
        STATUS_FULL        = 5
        STATUS_NOT_CHARGING = 4

        if status == STATUS_CHARGING:
            status_str = "Charging"
        elif status == STATUS_FULL:
            status_str = "Full"
        elif status == STATUS_NOT_CHARGING:
            status_str = "Not Charging"
        else:
            status_str = "Discharging"

        real_pct = int(pct * 100 / scale) if scale > 0 else pct
        temp_c   = temp / 10.0

        cur_ma = 0
        try:
            bm_svc = ctx.getSystemService("batterymanager")
            cur_ua = bm_svc.getLongProperty(1)  # BATTERY_PROPERTY_CURRENT_NOW
            cur_ma = abs(cur_ua) // 1000
        except Exception:
            pass

        sign = "+" if status_str == "Charging" else "-"

        return {
            "pct":     real_pct,
            "temp":    f"{temp_c:.1f}C",
            "volt":    f"{volt} mV",
            "current": f"{sign}{cur_ma} mA",
            "cur_ma":  cur_ma,
            "volt_mv": volt,
            "status":  status_str,
            "_ok":     True,
        }
    except Exception:
        return {"_ok": False}


def _sys_battery():
    pct    = _int(_sys("capacity"), 0)
    status = _sys("status") or "Unknown"
    temp_c = 0.0
    try: temp_c = _int(_sys("temp"), 0) / 10.0
    except Exception: pass
    v_mv = 0
    try:
        raw  = _int(_sys("voltage_now"), 0)
        v_mv = raw // 1000 if raw > 10000 else raw
    except Exception: pass
    cur_ma = 0
    try:
        raw    = _int(_sys("current_now"), 0)
        cur_ma = abs(raw) // 1000 if abs(raw) > 10000 else abs(raw)
    except Exception: pass

    sign = "+" if "charg" in status.lower() else "-"
    return {
        "pct":     pct,
        "temp":    f"{temp_c:.1f}C",
        "volt":    f"{v_mv} mV" if v_mv else "N/A",
        "current": f"{sign}{cur_ma} mA" if cur_ma else "N/A",
        "cur_ma":  cur_ma,
        "volt_mv": v_mv,
        "status":  status,
        "_ok":     True,
    }


def _calc_eta(pct, status, cur_ma, volt_mv):
    """
    Calculate ETA instantly from current draw:
    - capacity_mAh × pct% = remaining charge in mAh
    - remaining_mAh / current_mA = hours remaining
    Also updates from rate tracking for better accuracy.
    """
    global _prev_pct, _prev_time, _eta_cache

    is_charging    = status == "Charging"
    is_discharging = status in ("Discharging", "Not Charging")

    # ── Instant calculation from current draw ────────────────────────────
    if cur_ma > 50:   # meaningful current reading
        cap_mah = _get_capacity_mah()
        if is_charging:
            remaining_pct = 100 - pct
            if remaining_pct <= 0:
                return "Full"
            # mAh needed = cap × remaining%/100
            mah_needed = cap_mah * remaining_pct / 100.0
            hours_left  = mah_needed / cur_ma
            mins_left   = hours_left * 60
            if 0 < mins_left < 600:
                return f"Full ~{_fmt_time(mins_left)}"

        elif is_discharging:
            mah_left   = cap_mah * pct / 100.0
            hours_left = mah_left / cur_ma
            mins_left  = hours_left * 60
            if 0 < mins_left < 1440:  # max 24h
                return f"~{_fmt_time(mins_left)} left"

    # ── Rate-based ETA (backup, needs 60s of data) ───────────────────────
    now = time.monotonic()
    if _prev_pct >= 0:
        elapsed = now - _prev_time
        delta   = pct - _prev_pct
        if elapsed >= 60 and delta != 0:
            rate_per_min = abs(delta) / (elapsed / 60.0)
            if rate_per_min > 0:
                if delta > 0:
                    mins_left = (100 - pct) / rate_per_min
                    _eta_cache = f"Full ~{_fmt_time(mins_left)}"
                else:
                    mins_left = pct / rate_per_min
                    _eta_cache = f"~{_fmt_time(mins_left)} left"
            _prev_pct  = pct
            _prev_time = now

    if _prev_pct < 0:
        _prev_pct  = pct
        _prev_time = now

    if _eta_cache:
        return _eta_cache

    return status


def get_battery() -> dict:
    d = _pyjnius_battery()
    if not d.get("_ok"):
        d = _sys_battery()

    pct    = d.get("pct", 0)
    status = d.get("status", "Unknown")
    cur_ma = d.get("cur_ma", 0)
    volt_mv = d.get("volt_mv", 0)

    power_str = "N/A"
    if volt_mv > 0 and cur_ma > 0:
        power_mw  = (volt_mv * cur_ma) // 1000
        power_str = f"{power_mw} mW"

    d["power"] = power_str
    d["eta"]   = _calc_eta(pct, status, cur_ma, volt_mv)
    return d
