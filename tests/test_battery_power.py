"""Keep a connected, idle battery distinct from charging and peripheral power."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
DRIVER = r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
static const char *power_root, *percent, *state;
static char output[256];
#define SKYNET_POWER_SUPPLY_ROOT power_root
struct arg { const char *(*func)(const char *); const char *fmt; const char *args; };
const char *battery_perc(const char *unused) { (void)unused; return percent; }
const char *battery_state(const char *unused) { (void)unused; return state; }
const char *cpu_perc(const char *unused) { (void)unused; return "0"; }
const char *datetime(const char *unused) { (void)unused; return ""; }
const char *bprintf(const char *fmt, ...) {
    va_list ap; va_start(ap, fmt);
    vsnprintf(output, sizeof(output), fmt, ap); va_end(ap); return output;
}
#include "config.h"
int main(int argc, char **argv) {
    if (argc != 4) return 1;
    power_root = argv[1]; state = argv[2]; percent = argv[3];
    printf("%d %s\n", battery_mains_online(power_root), battery_visual("BAT0"));
    return 0;
}
'''


class BatteryPowerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which('cc'):
            raise unittest.SkipTest('requires a C compiler')
        cls.work = tempfile.TemporaryDirectory(prefix='skynet-battery-power-test-')
        cls.addClassCleanup(cls.work.cleanup)
        source = Path(cls.work.name) / 'power.c'
        source.write_text(DRIVER)
        cls.binary = Path(cls.work.name) / 'power'
        subprocess.run(['cc', '-std=c99', '-D_DEFAULT_SOURCE',
                        '-I' + str(ROOT / 'sources/slstatus'), str(source),
                        '-o', str(cls.binary)], check=True, capture_output=True)

    def check_power(self, devices, state='o', percent='78'):
        with tempfile.TemporaryDirectory(prefix='skynet-power-sysfs-') as folder:
            for name, fields in devices.items():
                device = Path(folder) / name
                device.mkdir()
                for field, value in fields.items():
                    (device / field).write_text(value + '\n')
            result = subprocess.run([str(self.binary), folder, state, percent],
                                    capture_output=True, text=True, check=True, timeout=3)
        online, visual = result.stdout.strip().split(' ', 1)
        return int(online), visual.split()[-1]

    def test_limit_waiting_and_active_charging_are_distinct(self):
        devices = {'ADP1': {'type': 'Mains', 'online': '1'}}
        self.assertEqual(self.check_power(devices), (1, '•'))
        self.assertEqual(self.check_power(devices, '+'), (1, '↑'))
        self.assertEqual(self.check_power(devices, '-'), (1, '↓'))
        self.assertEqual(self.check_power(devices, '?'), (1, '?'))

    def test_peripherals_do_not_make_an_unplugged_laptop_look_connected(self):
        devices = {'ADP1': {'type': 'Mains', 'online': '0'},
                   'mouse': {'type': 'Battery', 'online': '1'},
                   'usb': {'type': 'USB', 'online': '1'}}
        self.assertEqual(self.check_power(devices), (0, '↓'))
        del devices['ADP1']
        self.assertEqual(self.check_power(devices), (-1, '?'))

    def test_missing_or_bad_adapter_data_does_not_claim_connection(self):
        for value in (None, '', 'garbage', '2', '-1', '1 junk'):
            with self.subTest(value=value):
                fields = {'type': 'Mains'}
                if value is not None:
                    fields['online'] = value
                self.assertEqual(self.check_power({'AC': fields}), (-1, '?'))
        self.assertEqual(self.check_power({}), (-1, '?'))

    def test_multiple_adapters_and_other_names(self):
        devices = {'AC0': {'type': 'Mains', 'online': '0'},
                   'ACAD': {'type': 'Mains', 'online': '1'}}
        self.assertEqual(self.check_power(devices), (1, '•'))


if __name__ == '__main__':
    unittest.main()
