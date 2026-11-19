"""Check the DWM battery parser without opening a display or reading hardware."""
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
DRIVER = r'''
#define main dwm_program_main
#include "dwm.c"
#undef main
int main(int argc, char **argv) {
    if (argc != 2) return 1;
    int charging = -1;
    int percent = batterypercent(argv[1], &charging);
    printf("%d %d\n", percent, charging);
    return 0;
}
'''


class BatteryPanelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which('cc') or not shutil.which('pkg-config'):
            raise unittest.SkipTest('requires a C compiler and X11/Xft headers')
        flags = subprocess.run(['pkg-config', '--cflags', '--libs', 'xft', 'x11', 'fontconfig'],
                               capture_output=True, text=True)
        if flags.returncode:
            raise unittest.SkipTest('requires X11/Xft development files')
        cls.work = tempfile.TemporaryDirectory(prefix='skynet-battery-test-')
        cls.addClassCleanup(cls.work.cleanup)
        source = Path(cls.work.name) / 'parse.c'
        source.write_text(DRIVER)
        cls.binary = Path(cls.work.name) / 'parse'
        dwm = ROOT / 'sources/dwm'
        subprocess.run(['cc', '-std=c99', '-D_DEFAULT_SOURCE', '-D_XOPEN_SOURCE=700',
                        '-DVERSION="test"', '-Wall', '-Wno-deprecated-declarations',
                        '-I' + str(dwm), str(source), str(dwm / 'drw.c'), str(dwm / 'util.c'),
                        '-o', str(cls.binary), *shlex.split(flags.stdout), '-lm'],
                       check=True, capture_output=True)

    def parse(self, text):
        result = subprocess.run([str(self.binary), text], check=True,
                                capture_output=True, text=True, timeout=3)
        return tuple(map(int, result.stdout.split()))

    def test_levels_and_power_states_are_independent(self):
        for percent in (0, 1, 9, 10, 11, 20, 49, 80, 100):
            for marker in ('↑', '↓', '•', '?'):
                with self.subTest(percent=percent, marker=marker):
                    self.assertEqual(self.parse(f'BAT [▰▰▰▱▱]  {percent:3}% {marker}'),
                                     (percent, {'↑': 1, '•': 2}.get(marker, 0)))

    def test_invalid_or_missing_data_is_not_shown_as_zero(self):
        for text in ('', 'CPU 20%', 'BAT 30% ↑', 'BAT [▱▱▱▱▱]   --% ?',
                     'BAT [x] -1% ↑', 'BAT [x] 101% ↑', 'BAT [x] 50.5% ↑',
                     'BAT [x] 999999999999999999999999999% ↑',
                     'BAT [x] 80 ↑', 'BAT [x] 80%', 'BAT [x] 80% ↑ garbage'):
            with self.subTest(text=text):
                self.assertEqual(self.parse(text), (-1, 0))


if __name__ == '__main__':
    unittest.main()
