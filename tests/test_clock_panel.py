"""Validate clock input before using it for the bar's decorative dial."""
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
    int h = -1, m = -1, s = -1, valid;
    if (argc == 4) {
        XPoint hand = clockhand(atoi(argv[1]), atoi(argv[2]), atoi(argv[3]));
        printf("%d %d\n", hand.x, hand.y);
        return 0;
    }
    if (argc != 2) return 1;
    valid = clocktime(argv[1], &h, &m, &s);
    printf("%d %d %d %d\n", valid, h, m, s);
    return 0;
}
'''


class ClockPanelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.TemporaryDirectory(prefix='skynet-clock-test-')
        cls.addClassCleanup(cls.work.cleanup)
        source = Path(cls.work.name) / 'clock.c'
        source.write_text(DRIVER)
        cls.binary = Path(cls.work.name) / 'clock'
        flags = subprocess.check_output(['pkg-config', '--cflags', '--libs',
                                         'xft', 'xrender', 'x11', 'fontconfig'], text=True)
        dwm = ROOT / 'sources/dwm'
        subprocess.run(['cc', '-std=c99', '-D_DEFAULT_SOURCE', '-D_XOPEN_SOURCE=700',
                        '-DVERSION="test"', '-Wno-deprecated-declarations',
                        '-I' + str(dwm), str(source), str(dwm / 'drw.c'),
                        str(dwm / 'util.c'), '-o', str(cls.binary),
                        *shlex.split(flags), '-lm'], check=True, capture_output=True)

    def parse(self, text):
        return tuple(map(int, subprocess.check_output([str(self.binary), text],
                                                     text=True, timeout=3).split()))

    def test_day_boundaries_and_leap_second(self):
        for text, expected in [('00:00:00', (0, 0, 0)), ('12:30:45', (12, 30, 45)),
                               ('23:59:59', (23, 59, 59)), ('23:59:60', (23, 59, 60))]:
            with self.subTest(text=text):
                self.assertEqual(self.parse(text), (1, *expected))

    def test_malformed_values_remain_plain_text(self):
        for text in ['', '--:--:--', '9:03:04', '24:00:00', '12:60:00', '12:00:61',
                     '12-30-00', '12:3x:00', '12:30:00 extra', '１２:３０:００']:
            with self.subTest(text=text):
                self.assertEqual(self.parse(text), (0, -1, -1, -1))

    def hand(self, elapsed, period, radius):
        return tuple(map(int, subprocess.check_output(
            [str(self.binary), str(elapsed), str(period), str(radius)],
            text=True, timeout=3).split()))

    def test_clockwise_quarter_positions(self):
        for elapsed, expected in [(0, (0, -5)), (900, (5, 0)),
                                  (1800, (0, 5)), (2700, (-5, 0))]:
            with self.subTest(elapsed=elapsed):
                self.assertEqual(self.hand(elapsed, 3600, 5), expected)

    def test_minute_hand_uses_minutes_and_seconds(self):
        self.assertEqual(self.hand(120, 3600, 5), (1, -5))
        self.assertEqual(self.hand(59, 3600, 5), (1, -5))
        self.assertEqual(self.hand(57 * 60, 3600, 5), (-2, -5))

    def test_hour_hand_moves_between_hour_marks_without_half_hour_jump(self):
        self.assertEqual(self.hand(1800, 43200, 3), (1, -3))
        self.assertEqual(self.hand(3 * 3600 + 1800, 43200, 3), (3, 1))
        self.assertEqual(self.hand(11 * 3600 + 1800, 43200, 3), (-1, -3))
        self.assertEqual(self.hand(1799, 43200, 3), self.hand(1800, 43200, 3))

    def test_noon_midnight_and_leap_second_wrap(self):
        for elapsed in (0, 43200, 86400):
            self.assertEqual(self.hand(elapsed, 43200, 3), (0, -3))
            self.assertEqual(self.hand(elapsed, 3600, 5), (0, -5))
