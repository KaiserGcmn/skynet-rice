"""Render the greeter logo offscreen; no desktop, PAM or credentials required."""
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
DRIVER = r'''
#include <gtk/gtk.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "skynet-logo.h"

static cairo_surface_t *surface;
static cairo_t *cr;
static int width, height, stride;

static unsigned char *frame(double t) {
    skynet_logo_paint(cr, width, height, t);
    cairo_surface_flush(surface);
    return g_memdup2(cairo_image_surface_get_data(surface), (size_t)stride * height);
}

int main(int argc, char **argv) {
    if (argc != 3) return 1;
    width = atoi(argv[1]); height = atoi(argv[2]);
    double scale = fmin(width / 480., height / 340.);
    double cx = round(width / 2.), cy = round(SKYNET_GLOBE_CY * scale);
    double r = lround(SKYNET_GLOBE_D * scale) / 2.0;
    surface = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, width, height);
    cr = cairo_create(surface);
    stride = cairo_image_surface_get_stride(surface);
    unsigned char *first = frame(0);
    size_t globe_changes = 0, caption_changes = 0;
    for (int f = 1; f <= 40; ++f) {
        unsigned char *pixels = frame(f * 250.);
        for (int y = 0; y < height; ++y) {
            for (int x = 0; x < width; ++x) {
                size_t o = (size_t)y * stride + x * 4;
                if (!memcmp(pixels + o, first + o, 4)) continue;
                double d = hypot(x + .5 - cx, y + .5 - cy);
                int globe = d <= r + SKYGLOBE_GLOW + 2;
                int caption = y >= floor(310 * scale) && y <= ceil(332 * scale);
                /* The emblem and wordmark at the centre never move. */
                if (fabs(x + .5 - cx) < 0.12 * r && y > cy - 0.30 * r && y < cy - 0.10 * r) {
                    fprintf(stderr, "Emblem moved at %d,%d (frame %d)\n", x, y, f);
                    return 2;
                }
                if (!globe && !caption) {
                    fprintf(stderr, "Unexpected motion at %d,%d (frame %d)\n", x, y, f);
                    return 3;
                }
                globe_changes += globe;
                caption_changes += caption;
            }
        }
        g_free(pixels);
    }
    if (globe_changes < 2000 || caption_changes < 20) return 4;
    /* One full turn is 30 s: the globe area matches the first frame again. */
    unsigned char *turn = frame(SKYGLOBE_PERIOD_MS);
    for (int y = 0; y < floor(305 * scale); ++y)
        if (memcmp(first + (size_t)y * stride, turn + (size_t)y * stride, stride)) return 5;
    g_free(turn);
    /* The caption keeps its independent 3.8-second cycle. */
    unsigned char *scan = frame(3800.);
    for (int y = floor(310 * scale); y < height; ++y)
        if (memcmp(first + (size_t)y * stride, scan + (size_t)y * stride, stride)) return 6;
    g_free(scan);
    if (cairo_status(cr) != CAIRO_STATUS_SUCCESS) return 7;
    g_free(first);
    cairo_destroy(cr);
    cairo_surface_destroy(surface);
    return 0;
}
'''


class LogoRotationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which('cc') or not shutil.which('pkg-config'):
            raise unittest.SkipTest('requires a C compiler and GTK3 development files')
        flags = subprocess.run(['pkg-config', '--cflags', '--libs', 'gtk+-3.0'],
                               capture_output=True, text=True)
        if flags.returncode:
            raise unittest.SkipTest('requires GTK3 development files')
        cls.work = tempfile.TemporaryDirectory(prefix='skynet-logo-test-')
        cls.addClassCleanup(cls.work.cleanup)
        source = Path(cls.work.name) / 'render.c'
        source.write_text(DRIVER)
        cls.binary = Path(cls.work.name) / 'render'
        subprocess.run(['cc', '-O2', '-Wall', '-Wextra', '-Werror',
                        '-Wno-unused-function', '-Wno-unused-parameter',
                        str(source), '-I' + str(ROOT / 'sources/gtkgreet-hud'),
                        '-o', str(cls.binary), *shlex.split(flags.stdout), '-lm'],
                       check=True, capture_output=True)

    def test_globe_turns_emblem_stays_and_caption_scans(self):
        for width, height in [(480, 340), (480, 250), (240, 170)]:
            with self.subTest(size=(width, height)):
                result = subprocess.run([str(self.binary), str(width), str(height)],
                                        capture_output=True, text=True, timeout=60)
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
