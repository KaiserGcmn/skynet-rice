"""Exercise the decoration's DPMS decisions without a display or authentication."""
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
DRIVER = r'''
#define DPMSInfo fake_dpms_info
#define main saver_program_main
#include "saver-lock-style.c"
#undef main
static int query_ok, enabled, level;
Status fake_dpms_info(Display *dpy, CARD16 *power, BOOL *on) {
    (void)dpy; *power = level; *on = enabled; return query_ok;
}
int main(int argc, char **argv) {
    if (argc != 5) return 1;
    int available = atoi(argv[1]); query_ok = atoi(argv[2]);
    enabled = atoi(argv[3]); level = atoi(argv[4]);
    printf("%d\n", screen_is_dark(NULL, available));
    return 0;
}
'''


class LockDisplayPowerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which('cc') or not shutil.which('pkg-config'):
            raise unittest.SkipTest('requires a C compiler and X11 development files')
        flags = subprocess.run(['pkg-config', '--cflags', '--libs',
                                'xft', 'xrender', 'libpng', 'cairo'],
                               capture_output=True, text=True)
        if flags.returncode:
            raise unittest.SkipTest('requires Xft, XRender, libpng and Cairo development files')
        cls.work = tempfile.TemporaryDirectory(prefix='dwm-lock-power-test-')
        cls.addClassCleanup(cls.work.cleanup)
        source = Path(cls.work.name) / 'power.c'
        source.write_text(DRIVER)
        cls.binary = Path(cls.work.name) / 'power'
        subprocess.run(['cc', '-O2', '-Wall', '-Wextra', '-Werror',
                        '-I' + str(ROOT / 'sources/xsecurelock-style'), str(source),
                        '-o', str(cls.binary), *shlex.split(flags.stdout),
                        '-lXext', '-lm'], check=True, capture_output=True)

    def dark(self, available=1, query_ok=1, enabled=1, level=0):
        result = subprocess.run([str(self.binary), *map(str, (
            available, query_ok, enabled, level))],
            check=True, capture_output=True, text=True, timeout=3)
        return int(result.stdout.strip())

    def test_powered_on_display_keeps_animation(self):
        self.assertEqual(self.dark(level=0), 0)

    def test_standby_suspend_and_off_pause_animation(self):
        for level in (1, 2, 3):
            with self.subTest(level=level):
                self.assertEqual(self.dark(level=level), 1)

    def test_missing_disabled_or_failed_dpms_does_not_freeze_visible_logo(self):
        self.assertEqual(self.dark(available=0, level=3), 0)
        self.assertEqual(self.dark(query_ok=0, level=3), 0)
        self.assertEqual(self.dark(enabled=0, level=3), 0)


if __name__ == '__main__':
    unittest.main()
