import glob
import os

try:
    import plyer as _plyer
    _PLYER_OK = True
except Exception:
    _plyer = None
    _PLYER_OK = False


def _find_all_supply_paths():
    battery_paths = []
    other_paths = []
    for g in glob.glob('/sys/class/power_supply/*'):
        cap = os.path.join(g, 'capacity')
        if not os.path.exists(cap):
            continue
        tfile = os.path.join(g, 'type')
        try:
            t = open(tfile).read().strip().lower()
        except Exception:
            t = ''
        if t == 'battery':
            battery_paths.insert(0, g)
        else:
            other_paths.append(g)
    return battery_paths + other_paths


def _r(path):
    try:
        return open(path).read().strip()
    except Exception:
        return ''


def _read(base, *keys):
    return {k: _r(os.path.join(base, k)) for k in keys}


def _fmt_time(mins):
    if mins == 0:
        return 'N/A'
    h, m = divmod(int(mins), 60)
    if h:
        return '%dh %02dm' % (h, m)
    return '%dm' % m


def _parse_current(raw):
    try:
        return round(abs(int(raw)) / 1000.0, 1)
    except Exception:
        return 0


def _parse_voltage(raw):
    try:
        return round(int(raw) / 1000000.0, 3)
    except Exception:
        return 0


def _parse_temp(raw):
    try:
        return round(int(raw) / 10.0, 1)
    except Exception:
        return 0


def get_battery():
    result = {
        'pct':       0.0,
        'status':    'Unknown',
        'eta_label': 'ETA',
        'eta':       'N/A',
        'cur':       'N/A',
        'volt':      'N/A',
        'power':     'N/A',
        'temp':      'N/A',
        'Charg':     False,
    }

    if _PLYER_OK:
        try:
            _plyer.battery.enable()
            status = _plyer.battery.status or {}
            result['pct']   = float(status.get('percentage', 0) or 0)
            result['Charg'] = bool(status.get('isCharging', False))
            result['status'] = 'Charging' if result['Charg'] else 'Discharging'
        except Exception:
            pass

    if result['pct'] == 0.0:
        for base in _find_all_supply_paths():
            raw = _read(base,
                        'capacity', 'status', 'current_now',
                        'voltage_now', 'voltage_ocv',
                        'temp', 'charge_full', 'charge_full_design')
            try:
                result['pct'] = float(raw.get('capacity', 0))
            except Exception:
                pass

            status_raw = raw.get('status', 'Unknown')
            result['status'] = status_raw
            result['Charg']  = 'Charg' in status_raw

            cur_ma = _parse_current(raw.get('current_now', ''))
            if cur_ma > 0:
                try:
                    cap_raw  = raw.get('charge_full') or raw.get('charge_full_design', '')
                    full_mah = int(cap_raw) / 1000
                    if result['Charg']:
                        mins = (full_mah - full_mah * result['pct'] / 100) / cur_ma * 60
                        result['eta_label'] = 'Until full'
                    else:
                        mins = (full_mah * result['pct'] / 100) / cur_ma * 60
                        result['eta_label'] = 'Until empty'
                    result['eta'] = _fmt_time(int(mins))
                except Exception:
                    pass

            sign = '+' if result['Charg'] else '-'
            result['cur'] = '%s%.0f mA' % (sign, cur_ma) if cur_ma else 'N/A'

            volt = _parse_voltage(raw.get('voltage_now') or raw.get('voltage_ocv', ''))
            result['volt'] = '%.2f V' % volt if volt else 'N/A'

            if cur_ma and volt:
                result['power'] = '%.2f W' % (cur_ma / 1000.0 * volt)

            temp = _parse_temp(raw.get('temp', ''))
            result['temp'] = '%.1f C' % temp if temp else 'N/A'

            if result['pct'] > 0:
                break

    return result
