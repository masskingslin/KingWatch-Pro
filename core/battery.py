import glob, os

def _r(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except Exception:
        return None

def _fmt_time(mins):
    if not mins or mins <= 0:
        return "N/A"
    h, m = divmod(int(mins), 60)
    return "%dh %02dm" % (h, m) if h else "%dm" % m

def _get_android_battery():
    result = {}
    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Context        = autoclass("android.content.Context")
        BatteryManager = autoclass("android.os.BatteryManager")
        IntentFilter   = autoclass("android.content.IntentFilter")

        activity = PythonActivity.mActivity
        bm = activity.getSystemService(Context.BATTERY_SERVICE)

        # Current in uA (negative = discharging, positive = charging)
        cur_ua = bm.getIntProperty(1)  # PROPERTY_CURRENT_NOW
        if cur_ua != 0 and cur_ua != -2147483648:
            result["cur_ma"]  = abs(cur_ua) / 1000.0
            result["cur_raw"] = cur_ua  # keep sign for charging detection

        # Capacity remaining in uAh
        charge_uah = bm.getIntProperty(2)  # PROPERTY_CHARGE_COUNTER
        if charge_uah > 1000:
            result["charge_uah"] = charge_uah

        # Voltage + temp + pct + status from sticky broadcast
        ifilter = IntentFilter("android.intent.action.BATTERY_CHANGED")
        intent  = activity.registerReceiver(None, ifilter)
        if intent:
            pct = intent.getIntExtra("level", -1)
            if pct >= 0:
                result["pct"] = float(pct)

            volt_mv = intent.getIntExtra("voltage", -1)
            if volt_mv > 0:
                result["volt_v"] = volt_mv / 1000.0

            temp_10 = intent.getIntExtra("temperature", -1)
            if temp_10 > 0:
                result["temp_c"] = temp_10 / 10.0

            # status: 2=CHARGING 3=DISCHARGING 4=NOT_CHARGING 5=FULL
            status = intent.getIntExtra("status", 3)
            result["charging"] = status in (2, 5)

            # capacity in mAh from health extras (API 28+)
            try:
                cap = intent.getIntExtra("max_charging_current", -1)
                if cap > 100:
                    result["capacity_mah"] = cap
            except Exception:
                pass

    except Exception:
        pass
    return result


def _get_capacity_mah():
    """Try to read full battery capacity from sysfs for ETA."""
    for name in ["battery", "Battery", "BAT0", "BAT1", "bms"]:
        base = "/sys/class/power_supply/%s" % name
        for key in ["charge_full", "charge_full_design"]:
            v = _r(os.path.join(base, key))
            if v and int(v) > 100000:  # must be in uAh (> 100 mAh)
                return int(v) / 1000.0  # uAh -> mAh
    for g in glob.glob("/sys/class/power_supply/*"):
        for key in ["charge_full", "charge_full_design"]:
            v = _r(os.path.join(g, key))
            if v:
                try:
                    val = int(v)
                    if val > 100000:
                        return val / 1000.0
                except Exception:
                    pass
    return None


def get_battery():
    result = {
        "pct": 0.0, "status": "Unknown",
        "cur": "N/A", "volt": "N/A",
        "power": "N/A", "temp": "N/A",
        "eta": "N/A", "eta_label": "ETA"
    }

    pct      = 0.0
    charging = False

    # plyer
    try:
        from plyer import battery as pb
        info = pb.status
        if info and info.get("percentage") is not None:
            pct      = float(info["percentage"])
            charging = bool(info.get("isCharging"))
            result["pct"]    = pct
            result["status"] = "Charging" if charging else "Discharging"
    except Exception:
        pass

    # Android BatteryManager API
    bm = _get_android_battery()

    if bm.get("pct", 0) > 0:
        pct = bm["pct"]
        result["pct"] = pct

    if "charging" in bm:
        charging = bm["charging"]
        result["status"] = "Charging" if charging else "Discharging"

    cur_ma = bm.get("cur_ma")
    if cur_ma and cur_ma > 10:
        sign = "+" if charging else "-"
        result["cur"] = "%s%.0f mA" % (sign, cur_ma)

    volt_v = bm.get("volt_v")
    if volt_v:
        result["volt"] = "%.2f V" % volt_v

    if cur_ma and volt_v:
        result["power"] = "%.2f W" % (cur_ma * volt_v / 1000.0)

    if bm.get("temp_c"):
        result["temp"] = "%.1fC" % bm["temp_c"]

    charging = charging or "Charg" in result["status"]
    result["eta_label"] = "Until full" if charging else "Until empty"

    # ETA calculation - 3 methods in order of accuracy
    eta_mins = None

    # Method 1: charge_counter uAh / current mA = hours -> minutes
    charge_uah = bm.get("charge_uah", 0)
    if cur_ma and cur_ma > 10 and charge_uah > 1000:
        try:
            remaining_mah = charge_uah / 1000.0
            if charging:
                cap_mah = _get_capacity_mah() or (pct / 100.0 * 5000)
                eta_mins = max(0, (cap_mah - remaining_mah) / cur_ma * 60)
            else:
                eta_mins = remaining_mah / cur_ma * 60
        except Exception:
            pass

    # Method 2: sysfs capacity / current
    if not eta_mins and cur_ma and cur_ma > 10:
        try:
            cap_mah = _get_capacity_mah()
            if cap_mah and cap_mah > 500:
                if charging:
                    eta_mins = (100 - pct) / 100.0 * cap_mah / cur_ma * 60
                else:
                    eta_mins = pct / 100.0 * cap_mah / cur_ma * 60
        except Exception:
            pass

    # Method 3: assume 4500 mAh typical phone battery
    if not eta_mins and cur_ma and cur_ma > 10:
        try:
            cap_mah = 4500.0
            if charging:
                eta_mins = (100 - pct) / 100.0 * cap_mah / cur_ma * 60
            else:
                eta_mins = pct / 100.0 * cap_mah / cur_ma * 60
        except Exception:
            pass

    # Method 4: rough estimate 8 min per percent
    if not eta_mins:
        eta_mins = (100 - pct) * 8 if charging else pct * 8

    result["eta"] = _fmt_time(eta_mins)
    return result
