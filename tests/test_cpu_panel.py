"""CPU readouts reject invalid samples rather than displaying fictitious load."""
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
                                         'xft', 'x11', 'fontconfig'], text=True)
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

    def test_invalid_data_is_not_zero_load(self):
        invalid = ['CPU --%', 'CPU -1%', 'CPU 101%', 'CPU 8.5%', 'CPU 10%garbage',
                   'CPU ' + '9' * 100, 'BAT 80%', '', 'CPU 7% ']
        self.assertEqual(self.parse(invalid), [-1] * len(invalid))
