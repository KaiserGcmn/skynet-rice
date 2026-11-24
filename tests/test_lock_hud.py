"""The animated lock HUD stays in its own regions, away from protected areas."""
import importlib.util
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
STYLE = ROOT / 'sources/xsecurelock-style'
HEADER = STYLE / 'cyber-hud.h'
GENERATOR = STYLE / 'render-cyberpunk.py'
SAVER = STYLE / 'saver-lock-style.c'
LIBS = ('cairo', 'x11', 'xext', 'xft', 'xrender', 'xscrnsaver', 'libpng')


def load_generator():
    spec = importlib.util.spec_from_file_location('render_cyberpunk', GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pkg_flags(*libs):
    if not shutil.which('cc') or not shutil.which('pkg-config'):
        return None
    result = subprocess.run(['pkg-config', '--cflags', '--libs', *libs],
                            capture_output=True, text=True)
    return None if result.returncode else shlex.split(result.stdout)


# Render every widget alone on a transparent artwork-sized surface at many
# moments of its animation. The saver draws each widget into a buffer the size
# of its region, so anything outside would be cut off; it must fit entirely.
CHECK = r'''
#include "cyber-hud.h"
#include <stdint.h>

int main(void) {
    Hud hud;
    memset(&hud, 0, sizeof(hud));
    hud_layout(&hud);
    if (!hud_assets(&hud)) return 2;
    stats_init(&hud.stats, "/nonexistent");
    hud.power_on = 0;
    /* Published power-control numbers: the real layout parses (pressed is
     * sent + 1); a wrong version, size, flag, state or length does not. */
    {
        HudPowerUi ui;
        long good[11] = {2, 1400, 1118, 240, 54, 12, 1, 0, 0, 0, 2};
        if (!hud_power_parse(good, 11, &ui) || ui.pressed != -1 || ui.hover != 1 ||
            ui.x != 1400) {
            printf("power ui parse failed\n");
            return 5;
        }
        good[7] = 2;
        if (!hud_power_parse(good, 11, &ui) || ui.pressed != 1) return 5;
        long bad[][11] = {
            {1, 1400, 1118, 240, 54, 12, 1, 0, 0, 0, 0},     /* old version */
            {2, 1400, 1118, 0, 54, 12, 1, 0, 0, 0, 0},       /* width */
            {2, 1400, 1118, 240, 54, 12, 2, 0, 0, 0, 0},     /* layout flag */
            {2, 1400, 1118, 240, 54, 12, 1, 3, 0, 0, 0},     /* pressed */
            {2, 1400, 1118, 240, 54, 12, 1, 0, 3, 0, 0},     /* status */
            {2, 1400, 1118, 240, 54, 99, 1, 0, 0, 0, 0},     /* gap */
            {2, 1400, 1118, 240, 54, 12, 1, 0, 0, 0, 3},     /* hover */
        };
        for (size_t k = 0; k < sizeof(bad) / sizeof(bad[0]); ++k)
            if (hud_power_parse(bad[k], 11, &ui)) {
                printf("power ui accepted bad %zu\n", k);
                return 5;
            }
        if (hud_power_parse(good, 10, &ui)) return 5;
    }
    /* Subsystem status levels: thresholds, unknown input and hysteresis. */
    if (hud_subsys_level(-1, .50, .70, .90, .02) != 0 ||
        hud_subsys_level(-1, .80, .70, .90, .02) != 1 ||
        hud_subsys_level(-1, .95, .70, .90, .02) != 2 ||
        hud_subsys_level(1, -1, .70, .90, .02) != -1 ||
        hud_subsys_level(0, .71, .70, .90, .02) != 0 ||   /* inside the band */
        hud_subsys_level(0, .73, .70, .90, .02) != 1 ||
        hud_subsys_level(1, .69, .70, .90, .02) != 1 ||
        hud_subsys_level(1, .67, .70, .90, .02) != 0 ||
        hud_subsys_level(2, .89, .70, .90, .02) != 2 ||
        hud_subsys_level(0, .99, .70, .90, .02) != 2) {
        printf("subsystem levels wrong\n");
        return 4;
    }
    cairo_surface_t *s = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, 1920, 1200);
    int stride = cairo_image_surface_get_stride(s);
    int failures = 0;
    /* Pass 0: every live value at its extreme; pass 1: nothing known. */
    for (int pass = 0; pass < 2; ++pass) {
    double v = pass ? -1 : 1;
    hud.cpu = hud.mem = hud.swap = hud.disk = hud.net = v;
    for (int c = 0; c < 16; ++c) hud.core[c] = v;
    hud.stats.cores = pass ? 0 : 16;
    hud.stats.temp = pass ? -1 : 104;
    hud.stats.ghz = pass ? -1 : 5.9;
    hud.stats.rx = pass ? -1 : 987.6e9;
    hud.stats.tx = pass ? -1 : 999.9e6;
    snprintf(hud.stats.mode, sizeof(hud.stats.mode), "%s", pass ? "--" : "BALANCED-PERFORMANCE");
    for (int k = 0; k < 4; ++k) hud.subsys[k] = pass ? -1 : 2;
    for (int k = 0; k < STATS_T_COUNT; ++k) {
        hud.therm[k] = pass ? -1 : 149;      /* past the scale: clamped */
        hud.therm_peak[k] = pass ? -1 : 149;
    }
    hud.bat_pct = pass ? -1 : 1;
    hud.bat_watts = pass ? -1 : 245.7;
    hud.flow_phase = 0;
    hud.stats.bat_state = pass ? STATS_BAT_UNKNOWN : STATS_BAT_DISCHARGING;
    hud.stats.bat_health = pass ? -1 : 1;
    hud.stats.bat_cycles = pass ? -1 : 99999;
    /* Power controls as xsecurelock-power publishes them at 1920x1200:
     * one pressed and both busy/refused, or idle. */
    HudPowerUi ui = {2, 1400, 1118, 240, 54, 12, 1, pass ? -1 : 1,
                     {pass ? 0 : 2, pass ? 0 : 1}, pass ? -1 : 0};
    hud_buttons_set(&hud, 1400, 1118, &ui);
    /* Network history: 64 extreme samples, or none at all. */
    hud.net_count = 0;
    for (int k = 0; k < (pass ? 0 : HUD_NET_HISTORY); ++k)
        hud_net_push(&hud, -k * 1000.0, k % 2 ? 987.6e9 : 0, k % 3 ? 999.9e6 : 0);
    hud.net_scale = pass ? 0 : 5e8;   /* graph clipped at full scale */
    for (int i = 0; i < HUD_REGIONS; ++i) {
        HudRegion *g = &hud.region[i];
        if (!pass)
            printf("region %d %d %d %d %d %.0f\n", i, g->ax, g->ay, g->w, g->h, g->period);
        int samples = 0, empty = 0;
        for (double t = 0; t < 9000; t += 97.3, ++samples) {
            cairo_t *cr = cairo_create(s);
            cairo_set_operator(cr, CAIRO_OPERATOR_CLEAR);
            cairo_paint(cr);
            cairo_set_operator(cr, CAIRO_OPERATOR_OVER);
            hud_paint(&hud, i, cr, t);
            if (cairo_status(cr)) { printf("cairo error %d\n", i); return 3; }
            cairo_destroy(cr);
            cairo_surface_flush(s);
            unsigned char *data = cairo_image_surface_get_data(s);
            int outside = 0, inside = 0;
            for (int y = 0; y < 1200; ++y)
                for (int x = 0; x < 1920; ++x) {
                    if (!(*(uint32_t *)(data + (size_t)y * stride + 4 * x) >> 24)) continue;
                    if (x >= g->ax && x < g->ax + g->w && y >= g->ay && y < g->ay + g->h)
                        ++inside;
                    else
                        ++outside;
                }
            if (outside) {
                printf("outside %d pass=%d t=%.1f pixels=%d\n", i, pass, t, outside);
                ++failures;
                break;
            }
            empty += !inside;
        }
        /* Edge scanners pause briefly between passes; the rest always draw. */
        if (empty * 10 > samples) {
            printf("empty %d pass=%d in %d of %d samples\n", i, pass, empty, samples);
            ++failures;
        }
    }
    }
    cairo_surface_destroy(s);
    hud_assets_free(&hud);
    return failures ? 1 : 0;
}
'''


class LockHudTest(unittest.TestCase):
    def test_generator_reads_header_geometry(self):
        defines = dict(re.findall(r'(?m)^#define HUD_(\w+) (-?\d+)$', HEADER.read_text()))
        geometry = load_generator().hud_geometry()
        self.assertEqual(geometry, {k: int(v) for k, v in defines.items()})
        self.assertIn('CORE_CX', geometry)
        self.assertNotIn('RADAR_CX', geometry)

    def test_widgets_stay_in_regions_outside_protected_areas(self):
        flags = pkg_flags('cairo', 'x11', 'xext')
        if flags is None:
            self.skipTest('requires C compiler and Cairo/X11 development files')
        with tempfile.TemporaryDirectory(prefix='skynet-hud-test-') as work:
            source = Path(work) / 'check.c'
            source.write_text(CHECK)
            binary = Path(work) / 'check'
            subprocess.run(['cc', '-O2', '-Wall', '-Wextra', '-Werror',
                            '-Wno-unused-function', '-I', str(STYLE), str(source),
                            '-o', str(binary), *flags, '-lm'], check=True)
            result = subprocess.run([str(binary)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        regions = [tuple(map(int, m)) for m in
                   re.findall(r'region (\d+) (\d+) (\d+) (\d+) (\d+) (\d+)', result.stdout)]
        self.assertEqual(len(regions), 16)
        protected = load_generator().PROTECTED
        buttons = (1392, 1108, 1898, 1180)
        self.assertIn(buttons, protected)
        for index, x, y, w, h, period in regions:
            with self.subTest(region=index):
                self.assertTrue(0 <= x and 0 <= y and x + w <= 1920 and y + h <= 1200)
                # Smooth motion at most ~30 fps, readouts slower.
                self.assertGreaterEqual(period, 33)
                boxes = protected
                if index == 15:
                    # The power controls belong in their own protected box.
                    x0, y0, x1, y1 = buttons
                    self.assertTrue(x0 <= x and y0 <= y and x + w <= x1 and y + h <= y1)
                    boxes = [b for b in protected if b != buttons]
                for x0, y0, x1, y1 in boxes:
                    self.assertFalse(x < x1 and x + w > x0 and y < y1 and y + h > y0,
                                     f'region {index} overlaps protected {x0, y0, x1, y1}')

    def test_saver_builds_without_warnings(self):
        flags = pkg_flags(*LIBS)
        if flags is None:
            self.skipTest('requires C compiler and saver development libraries')
        with tempfile.TemporaryDirectory(prefix='skynet-saver-test-') as work:
            subprocess.run(['cc', '-Wall', '-Wextra', '-Werror', '-D_FORTIFY_SOURCE=2',
                            '-O2', str(SAVER), '-o', str(Path(work) / 'saver'),
                            *flags, '-lm'], check=True)


if __name__ == '__main__':
    unittest.main()
