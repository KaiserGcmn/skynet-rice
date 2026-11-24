"""CPU, RAM and battery readouts reject invalid samples and share one level gauge."""
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
DRIVER = r'''
#define main dwm_program_main
#include "dwm.c"
#undef main
int main(int argc, char **argv) {
    int i;
    if (argc > 1 && !strcmp(argv[1], "--low")) {
        for (i = 2; i + 1 < argc; i += 2)
            printf("%d\n", batterylow(atoi(argv[i]), atoi(argv[i + 1])));
        return 0;
    }
    if (argc > 1 && !strcmp(argv[1], "--ram")) {
        for (i = 2; i < argc; i++) printf("%d\n", rampercent(argv[i]));
        return 0;
    }
    if (argc > 1 && !strcmp(argv[1], "--fill")) {
        for (i = 2; i < argc; i++) printf("%d\n", gaugefillpx(atoi(argv[i]), 24));
        return 0;
    }
    for (i = 1; i < argc; i++) printf("%d\n", cpupercent(argv[i]));
    return 0;
}
'''


class CPUReadoutTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.TemporaryDirectory(prefix='skynet-cpu-test-')
        cls.addClassCleanup(cls.work.cleanup)
        source = Path(cls.work.name) / 'cpu.c'
        source.write_text(DRIVER)
        cls.binary = Path(cls.work.name) / 'cpu'
        flags = subprocess.check_output(['pkg-config', '--cflags', '--libs',
                                         'xft', 'xrender', 'x11', 'fontconfig'], text=True)
        dwm = ROOT / 'sources/dwm'
        subprocess.run(['cc', '-std=c99', '-D_DEFAULT_SOURCE', '-D_XOPEN_SOURCE=700',
                        '-DVERSION="test"', '-Wno-deprecated-declarations',
                        '-I' + str(dwm), str(source), str(dwm / 'drw.c'),
                        str(dwm / 'util.c'), '-o', str(cls.binary),
                        *shlex.split(flags), '-lm'], check=True, capture_output=True)

    def parse(self, samples):
        return list(map(int, subprocess.check_output([str(self.binary), *samples],
                                                     text=True, timeout=3).split()))

    def test_percentages_and_spacing(self):
        self.assertEqual(self.parse(['CPU 0%', 'CPU   1%', 'CPU 20%', 'CPU 85%', 'CPU 100%']),
                         [0, 1, 20, 85, 100])

    def low(self, *pairs):
        args = [str(v) for pair in pairs for v in pair]
        output = subprocess.check_output([str(self.binary), '--low', *args],
                                         text=True, timeout=3)
        return list(map(int, output.split()))

    def test_battery_is_critical_from_zero_to_ten_percent_on_battery_only(self):
        # (percent, state): state 0 = battery or unknown, 1 = charging, 2 = mains idle
        self.assertEqual(self.low((-1, 0), (0, 0), (1, 0), (10, 0), (11, 0), (100, 0)),
                         [0, 1, 1, 1, 0, 0])
        self.assertEqual(self.low((0, 1), (5, 1), (10, 1), (0, 2), (5, 2), (10, 2)),
                         [0] * 6)

    def test_invalid_data_is_not_zero_load(self):
        invalid = ['CPU --%', 'CPU -1%', 'CPU 101%', 'CPU 8.5%', 'CPU 10%garbage',
                   'CPU ' + '9' * 100, 'BAT 80%', '', 'CPU 7% ']
        self.assertEqual(self.parse(invalid), [-1] * len(invalid))

    def ram(self, samples):
        return list(map(int, subprocess.check_output([str(self.binary), '--ram', *samples],
                                                     text=True, timeout=3).split()))

    def test_ram_percentages_use_their_own_prefix(self):
        self.assertEqual(self.ram(['RAM 0%', 'RAM   7%', 'RAM 38%', 'RAM 100%']),
                         [0, 7, 38, 100])
        self.assertEqual(self.ram(['CPU 38%', 'BAT 38%']), [-1, -1])
        self.assertEqual(self.parse(['RAM 38%']), [-1])

    def test_ram_invalid_data_is_not_zero_use(self):
        invalid = ['RAM --%', 'RAM n/a%', 'RAM -1%', 'RAM 101%', 'RAM 8.5%',
                   'RAM 10%garbage', 'RAM ' + '9' * 100, '', 'RAM 7% ']
        self.assertEqual(self.ram(invalid), [-1] * len(invalid))

    def test_gauge_fill_never_hides_use_or_overflows(self):
        output = subprocess.check_output([str(self.binary), '--fill', '-1', '0', '1', '11',
                                          '50', '85', '99', '100'], text=True, timeout=3)
        self.assertEqual(list(map(int, output.split())), [0, 0, 2, 3, 12, 20, 24, 24])
