import os
import sys
import threading

app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, app_dir)

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.properties import ColorProperty

from ui.widgets import StatCard, ThemeChip
from themes import THEME_NAMES, get_theme, DEFAULT_THEME
from core.cpu import (get_cpu, get_cpu_freq, get_cpu_cores,
                      get_cpu_procs, get_cpu_uptime)
from core.ram import get_ram
from core.battery import get_battery
from core.network import get_network
from core.storage import get_storage
from core.thermal import get_thermal


class RootWidget(BoxLayout):

    bg      = ColorProperty(get_color_from_hex('#0A0A0A'))
    card    = ColorProperty(get_color_from_hex('#161616'))
    card2   = ColorProperty(get_color_from_hex('#242424'))
    accent  = ColorProperty(get_color_from_hex('#00E676'))
    dim     = ColorProperty(get_color_from_hex('#555555'))
    div     = ColorProperty(get_color_from_hex('#222222'))
    btn_txt = ColorProperty(get_color_from_hex('#000000'))

    _tname = DEFAULT_THEME

    def on_kv_post(self, a):
        self._build_chips()
        self._apply_theme(DEFAULT_THEME)
        threading.Thread(target=self._start_cpu, daemon=True).start()
        Clock.schedule_interval(self.update_stats, 3)

    def _start_cpu(self):
        try:
            from core.cpu import _ensure_started
            _ensure_started()
        except Exception:
            pass

    def _build_chips(self):
        row = self.ids.chips_row
        row.clear_widgets()
        for name in THEME_NAMES:
            chip = ThemeChip(_name=name)
            chip.bind(on_touch_up=self._on_chip)
            row.add_widget(chip)

    def _on_chip(self, chip, touch):
        if chip.collide_point(*touch.pos):
            self._apply_theme(chip._name)
            return True

    def _apply_theme(self, name):
        self._tname = name
        t = get_theme(name)
        self.bg      = get_color_from_hex(t['BG'])
        self.card    = get_color_from_hex(t['CARD'])
        self.card2   = get_color_from_hex(t['CARD2'])
        self.accent  = get_color_from_hex(t['ACCENT'])
        self.dim     = get_color_from_hex(t['DIM'])
        self.div     = get_color_from_hex(t['DIV'])
        self.btn_txt = get_color_from_hex(t['BTN_TEXT'])
        self._style_chips()

    def _style_chips(self):
        t = get_theme(self._tname)
        try:
            for chip in self.ids.chips_row.children:
                sel = getattr(chip, '_name', None) == self._tname
                chip.selected = sel
                if sel:
                    chip.chip_bg     = get_color_from_hex(t['ACCENT'] + '33')
                    chip.chip_border = get_color_from_hex(t['ACCENT'])
                    chip.chip_text   = get_color_from_hex(t['CARD'])
                else:
                    chip.chip_bg     = get_color_from_hex(t['CARD'])
                    chip.chip_border = get_color_from_hex(t['CARD2'])
                    chip.chip_text   = get_color_from_hex(t['DIM'])
        except Exception:
            pass

    def update_stats(self, a):
        threading.Thread(target=self._collect, daemon=True).start()

    def _collect(self):
        t = get_theme(self._tname)

        def clr(pct, lo=75, hi=90):
            if pct >= hi:
                return get_color_from_hex(t.get('DANGER', '#FF1744'))
            if pct >= lo:
                return get_color_from_hex(t.get('WARN', '#FFC107'))
            return get_color_from_hex(t['ACCENT'])

        cpu_pct   = get_cpu()
        cpu_freq  = get_cpu_freq()
        cpu_cores = get_cpu_cores()
        cpu_procs = get_cpu_procs()
        cpu_up    = get_cpu_uptime()

        ram     = get_ram()
        storage = get_storage()

        try:
            batt = get_battery()
        except Exception:
            batt = {
                'pct': 0.0, 'status': 'ERR', 'eta_label': 'ETA',
                'eta': 'N/A', 'cur': 'N/A', 'volt': 'N/A',
                'power': 'N/A', 'temp': 'N/A', 'Charg': False,
            }

        try:
            net = get_network()
        except Exception:
            net = {'ping': '--', 'dl': '0 KB/s', 'ul': '0 KB/s', 'signal': 'N/A'}

        thermal = get_thermal()

        def apply(dt):
            try:
                ids = self.ids

                c = clr(cpu_pct)
                ids.cpu_card.value    = '%.1f%%' % cpu_pct
                ids.cpu_card.subtitle = cpu_freq
                ids.cpu_card.bar_pct  = float(cpu_pct)
                ids.cpu_card.bar_color = c
                ids.cpu_card.detail1  = 'Freq: %s  Cores: %s' % (cpu_freq, cpu_cores)
                ids.cpu_card.detail2  = 'Procs: %s  Up: %s' % (cpu_procs, cpu_up)

                pct = ram.get('pct', 0)
                ids.ram_card.value    = '%.0f%%' % pct
                ids.ram_card.subtitle = ram.get('subtitle', '')
                ids.ram_card.bar_pct  = float(pct)
                ids.ram_card.bar_color = clr(pct)
                ids.ram_card.detail1  = ram.get('detail1', '')

                pct = storage.get('pct', 0)
                ids.storage_card.value    = '%.0f%%' % pct
                ids.storage_card.subtitle = storage.get('subtitle', 'used')
                ids.storage_card.bar_pct  = float(pct)
                ids.storage_card.bar_color = clr(pct, 80, 95)
                ids.storage_card.detail1  = storage.get('detail1', '')

                bpct = float(batt.get('pct', 0))
                is_charg = batt.get('Charg', False)
                ids.battery_card.value    = '%.0f%%' % bpct
                ids.battery_card.subtitle = batt.get('status', '?')
                ids.battery_card.bar_pct  = bpct
                bar_c = get_color_from_hex(
                    t['ACCENT'] if (is_charg or bpct > 20) else t.get('DANGER', '#FF1744'))
                ids.battery_card.bar_color = bar_c
                ids.battery_card.detail1 = 'Curr: %s  Volt: %s' % (
                    batt.get('cur', '--'), batt.get('volt', '--'))
                ids.battery_card.detail2 = '%s: %s  Pwr: %s' % (
                    batt.get('eta_label', 'ETA'),
                    batt.get('eta', '--'),
                    batt.get('power', '--'))

                ids.network_card.value    = net.get('ping', '--')
                ids.network_card.subtitle = net.get('signal', '')
                ids.network_card.detail1  = 'DL: %s  UL: %s' % (
                    net.get('dl', '--'), net.get('ul', '--'))

                tpct = thermal.get('pct', 0)
                ids.thermal_card.value     = thermal.get('value', 'N/A')
                ids.thermal_card.subtitle  = thermal.get('subtitle', '')
                ids.thermal_card.bar_pct   = min(float(tpct), 100)
                ids.thermal_card.bar_color = clr(tpct, 54, 75)
                ids.thermal_card.detail1   = thermal.get('detail1', '')

            except Exception:
                pass

        Clock.schedule_once(apply)


class MonitorApp(App):
    def build(self):
        Window.clearcolor = get_color_from_hex('#0A0A0A')
        Builder.load_file(os.path.join(app_dir, 'kingwatch.kv'))
        return RootWidget()


if __name__ == '__main__':
    MonitorApp().run()
