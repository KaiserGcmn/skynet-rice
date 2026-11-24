"""Shared SKYNET globe (lock screen and greeter): geometry, map, timing, layout."""
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
STYLE = ROOT / 'sources/xsecurelock-style'
DRIVER = r'''
#include <X11/Xlib.h>
#include <stdio.h>
#include <time.h>
#include "skynet-logo.h"

static double now(void) {
    struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec * 1e3 + t.tv_nsec / 1e6;
}
static double land_at(const SkyGlobe *g, double lat, double lon) {
    int x = (int)((lon + 180) / 360 * SKYGLOBE_MAP_W), y = (int)((90 - lat) / 180 * SKYGLOBE_MAP_H);
    return g->map[y * SKYGLOBE_MAP_W + x] / 255.0;
}
int main(void) {
    SkyGlobe g = {0};
    if (!skyglobe_init(&g, 290)) return 10;
    /* Land mask: plausible share and known places. */
    long land = 0;
    for (int i = 0; i < SKYGLOBE_MAP_W * SKYGLOBE_MAP_H; ++i) land += g.map[i] != 0;
    double share = (double)land / (SKYGLOBE_MAP_W * SKYGLOBE_MAP_H);
    if (share < 0.28 || share > 0.40) { fprintf(stderr, "land share %f\n", share); return 11; }
    if (land_at(&g, 23, 10) < 1 || land_at(&g, -15, -55) < 1 || land_at(&g, 60, 90) < 1) return 12;
    if (land_at(&g, 0, -30) > 0 || land_at(&g, -30, 80) > 0 || land_at(&g, 30, -150) > 0) return 13;
    /* Centre of the disc looks at the tilt latitude on the base meridian. */
    double lat, lon;
    skyglobe_project(0, 0, 0, &lat, &lon);
    if (fabs(lat - SKYGLOBE_TILT_DEG) > 1e-6 || fabs(lon) > 1e-6) return 14;
    /* Right of centre is east. The axis leans left (north is up-left), so
     * straight up from the centre lies north and slightly east. */
    double la2, lo2;
    skyglobe_project(0.3, 0, 0, &la2, &lo2);
    if (lo2 <= 0) return 15;
    skyglobe_project(0, -0.3, 0, &la2, &lo2);
    if (la2 <= lat || lo2 <= 0) return 16;
    /* One full turn per period: identical pixels after exactly one period. */
    skyglobe_render(&g, 1234);
    size_t bytes = (size_t)cairo_image_surface_get_stride(g.surface) * g.size;
    unsigned char *a = malloc(bytes);
    memcpy(a, cairo_image_surface_get_data(g.surface), bytes);
    skyglobe_render(&g, 1234 + SKYGLOBE_PERIOD_MS);
    if (memcmp(a, cairo_image_surface_get_data(g.surface), bytes)) return 17;
    skyglobe_render(&g, 1234 + 1000);
    if (!memcmp(a, cairo_image_surface_get_data(g.surface), bytes)) return 18;
    free(a);
    /* Cheap enough for 30 fps on one core with a wide margin. */
    double t0 = now();
    for (int i = 0; i < 60; ++i) skyglobe_render(&g, i * 33.0);
    double per = (now() - t0) / 60;
    if (per > 12) { fprintf(stderr, "%.2f ms per frame\n", per); return 19; }
    skyglobe_free(&g);

    /* Lock layout: the globe and its halo stay above the caption strip and
     * inside the 480x260 area; the caption strip shows only the caption. */
    Logo logo = {0};
    logo.frame = cairo_image_surface_create(CAIRO_FORMAT_RGB24, LOGO_WIDTH, LOGO_HEIGHT);
    logo.font = cairo_toy_font_face_create("monospace", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_BOLD);
    if (!skyglobe_init(&logo.globe, LOGO_GLOBE_DIAMETER)) return 20;
    if (LOGO_GLOBE_CY + LOGO_GLOBE_DIAMETER / 2 + SKYGLOBE_GLOW > LOGO_STRIP_Y) return 21;
    if (LOGO_GLOBE_CY - LOGO_GLOBE_DIAMETER / 2 < 0) return 22;
    if ((LOGO_WIDTH - logo.globe.size) / 2 < 0) return 23;
    logo_render(&logo, 0);
    int stride = cairo_image_surface_get_stride(logo.frame);
    unsigned char *f0 = malloc((size_t)stride * LOGO_HEIGHT);
    memcpy(f0, cairo_image_surface_get_data(logo.frame), (size_t)stride * LOGO_HEIGHT);
    logo_render_globe(&logo, 5000);
    cairo_surface_flush(logo.frame);
    unsigned char *f1 = cairo_image_surface_get_data(logo.frame);
    if (memcmp(f0 + (size_t)LOGO_STRIP_Y * stride, f1 + (size_t)LOGO_STRIP_Y * stride,
               (size_t)stride * (LOGO_HEIGHT - LOGO_STRIP_Y))) return 24;
    if (!memcmp(f0, f1, (size_t)stride * LOGO_STRIP_Y)) return 25;
    free(f0);
    return 0;
}
'''


class SkynetGlobeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which('cc') or not shutil.which('pkg-config'):
            raise unittest.SkipTest('requires a C compiler')
        flags = subprocess.run(['pkg-config', '--cflags', '--libs', 'cairo', 'x11', 'xext'],
                               capture_output=True, text=True)
        if flags.returncode:
            raise unittest.SkipTest('requires cairo and X11 development files')
        cls.work = tempfile.TemporaryDirectory(prefix='skynet-globe-test-')
        cls.addClassCleanup(cls.work.cleanup)
        source = Path(cls.work.name) / 'globe.c'
        source.write_text(DRIVER)
        cls.binary = Path(cls.work.name) / 'globe'
        subprocess.run(['cc', '-O2', '-Wall', '-Wextra', '-Werror', '-Wno-unused-function',
                        str(source), '-I' + str(STYLE), '-o', str(cls.binary),
                        *shlex.split(flags.stdout), '-lm'],
                       check=True, capture_output=True)

    def test_map_projection_period_speed_and_lock_layout(self):
        result = subprocess.run([str(self.binary)], capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_land_header_matches_its_generator_format(self):
        header = (STYLE / 'skynet-globe-land.h').read_text()
        self.assertIn('Natural Earth', header)
        self.assertIn('#define SKYGLOBE_MAP_W 1024', header)
        runs = header[header.index('{') + 1:header.rindex('}')]
        values = [int(v) for v in runs.replace('\n', '').split(',') if v.strip()]
        self.assertEqual(values.count(0xFFFF), 512)
        row = []
        for value in values:
            if value == 0xFFFF:
                self.assertEqual(sum(row), 1024)
                row = []
            else:
                row.append(value)

    def test_no_server_side_logo_drawing_and_greeter_shares_the_globe(self):
        lock = (STYLE / 'skynet-logo.h').read_text()
        greeter = (ROOT / 'sources/gtkgreet-hud/skynet-logo.h').read_text()
        self.assertIn('#include "skynet-globe.h"', lock)
        self.assertIn('XShmPutImage', lock)
        self.assertNotIn('XFillPolygon', lock)
        self.assertNotIn('XRenderComposite', lock)
        self.assertIn('#include "../xsecurelock-style/skynet-globe.h"', greeter)
        self.assertNotIn('logo_plates', greeter)


if __name__ == '__main__':
    unittest.main()
