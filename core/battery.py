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
    """
    Use Android BatteryManager Java API directly via jnius.
    BATTERY_PROPERTY_CURRENT_NOW = microamps (API 21+)
    EXTRA_VOLTAGE = millivolts
    EXTRA_TEMPERATURE = tenths of C
    """
    result = {}
    try:
        from jnius import autoclass
        PythonActivity  = autoclass("org.kivy.android.PythonActivity")
        Context         = autoclass("android.content.Context")
        BatteryManager  = autoclass("android.os.BatteryManager")
        Intent          = autoclass("android.content.Intent")
        IntentFilter    = autoclass("android.content.IntentFilter")

        activity = PythonActivity.mActivity
        bm = activity.getSystemService(Context.BATTERY_SERVICE)

        # Current in microamps (negative = discharging)
        PROPERTY_CURRENT_NOW = 1
        cur_ua = bm.getIntProperty(PROPERTY_CURRENT_NOW)
        if cur_ua != 0 and cur_ua != -2147483648:
            result["cur_ma"] = abs(cur_ua) / 1000.0
            result["charging"] = cur_ua > 0

        # Voltage and temperature from sticky broadcast
        ifilter = IntentFilter("android.intent.action.BATTERY_CHANGED")
        intent  = activity.registerReceiver(None, ifilter)
        if intent:
            volt_mv = intent.getIntExtra("voltage", -1)
            if volt_mv > 0:
                result["volt_v"] = volt_mv / 1000.0

            temp_10 = intent.getIntExtra("temperature", -1)
            if temp_10 > 0:
                result["temp_c"] = temp_10 / 10.0

            pct = intent.getIntExtra("level", -1)
            if pct >= 0:
                result["pct"] = float(pct)

            status = intent.getIntExtra("status", -1)
            # 2=CHARGING, 3=DISCHARGING, 4=NOT_CHARGING, 5=FULL
            result["charging"] = status in (2, 5)

        # Capacity in mAh for ETA
        PROPERTY_CHARGE_COUNTER = 2
        charge_uah = bm.getIntProperty(PROPERTY_CHARGE_COUNTER)
        if charge_uah > 0:
            result["charge_uah"] = charge_uah

    except Exception:
        pass
    return result


def _find_battery_base():
    for name in ["battery", "Battery", "BAT0", "BAT1", "bms", "main-battery"]:
        p = "/sys/class/power_supply/%s" % name
        if os.path.exists(os.path.join(p, "capacity")):
            return p
    for g in glob.glob("/sys/class/power_supply/*"):
        t = _r(os.path.join(g, "type")) or ""
        if "battery" in t.lower():
            if os.path.exists(os.path.join(g, "capacity")):
                return g
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

    # 1. plyer
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

    # 2. Android BatteryManager Java API (most complete)
    bm = _get_android_battery()
    if bm.get("pct", 0) > 0 and result["pct"] == 0.0:
        pct = bm["pct"]
        result["pct"] = pct
    if "charging" in bm:
        charging = bm["charging"]
        result["status"] = "Charging" if charging else "Discharging"

    cur_ma = bm.get("cur_ma")
    if cur_ma and cur_ma > 0:
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

    # ETA from charge counter
    charge_uah = bm.get("charge_uah", 0)
    if cur_ma and cur_ma > 0 and charge_uah > 0:
        try:
            if charging:
                # estimate full capacity from sysfs
                base = _find_battery_base()
                full_raw = None
                if base:
                    for k in ["charge_full", "charge_full_design"]:
                        v = _r(os.path.join(base, k))
                        if v and v != "0":
                            full_raw = v
                            break
                if full_raw:
                    full_mah = int(full_raw) / 1000.0
                    mins = (full_mah - charge_uah / 1000.0) / cur_ma * 60
                else:
                    mins = (100 - pct) * 8
            else:
                mins = (charge_uah / 1000.0) / cur_ma * 60
            result["eta"] = _fmt_time(mins)
        except Exception:
            result["eta"] = _fmt_time((100 - pct) * 8 if charging else pct * 8)
    else:
        result["eta"] = _fmt_time((100 - pct) * 8 if charging else pct * 8)

    return result
