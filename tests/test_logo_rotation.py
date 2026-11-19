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

int main(int argc, char **argv) {
    if (argc != 3) return 1;
    int width = atoi(argv[1]), height = atoi(argv[2]);
    double scale = fmin(width / 480., height / 340.);
    double left = (width - 480 * scale) / 2;
    cairo_surface_t *surface = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, width, height);
    cairo_t *cr = cairo_create(surface);
    skynet_logo_paint(cr, width, height, 0);
    cairo_surface_flush(surface);
    int stride = cairo_image_surface_get_stride(surface);
    size_t length = (size_t)stride * height;
    unsigned char *first = g_memdup2(cairo_image_surface_get_data(surface), length);
    size_t triangle_changes = 0, caption_changes = 0;
    for (int frame = 1; frame <= 64; ++frame) {
        skynet_logo_paint(cr, width, height, frame * 125.);
        cairo_surface_flush(surface);
        unsigned char *pixels = cairo_image_surface_get_data(surface);
        for (int y = 0; y < height; ++y) {
            for (int x = 0; x < width; ++x) {
                size_t offset = (size_t)y * stride + x * 4;
                if (!memcmp(pixels + offset, first + offset, 4)) continue;
                int triangle = x >= floor(left + 40 * scale) && x <= ceil(left + 440 * scale) &&
                               y >= floor(28 * scale) && y <= ceil(238 * scale);
                int caption = x >= floor(left + 40 * scale) && x <= ceil(left + 440 * scale) &&
                              y >= floor(311 * scale) && y <= ceil(331 * scale);
                if (triangle) ++triangle_changes;
                if (caption) ++caption_changes;
                /* The wordmark stays fixed; only the emblem and caption light change. */
                if (!triangle && !caption) {
                    fprintf(stderr, "Unexpected motion at %d,%d (frame %d)\n", x, y, frame);
                    return 2;
                }
                if (frame == 32 && triangle) return 3; /* Full turn: four seconds. */
            }
        }
        if (frame == 8) {
            /* At one second the triangle is edge-on, proving the faster rotation. */
            size_t front_red = 0, edge_red = 0;
            for (int y = 0; y < floor(239 * scale); ++y) {
                for (int x = 0; x < width; ++x) {
                    size_t offset = (size_t)y * stride + x * 4;
                    uint32_t front, edge;
                    memcpy(&front, first + offset, 4);
                    memcpy(&edge, pixels + offset, 4);
                    if (((front >> 16) & 255) > 100 && ((front >> 8) & 255) < 40) ++front_red;
                    if (((edge >> 16) & 255) > 100 && ((edge >> 8) & 255) < 40) ++edge_red;
                }
            }
            if (!front_red || edge_red * 20 > front_red) return 4;
        }
    }
    if (triangle_changes < 1000 || caption_changes < 20) return 5;
    skynet_logo_paint(cr, width, height, 3800.);
    cairo_surface_flush(surface);
    for (int y = floor(310 * scale); y < height; ++y)
        if (memcmp(first + y * stride, cairo_image_surface_get_data(surface) + y * stride, stride))
            return 6; /* The caption retains its independent 3.8-second cycle. */
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
                        str(source), '-I' + str(ROOT / 'sources/gtkgreet-skynet'),
                        '-o', str(cls.binary), *shlex.split(flags.stdout), '-lm'],
                       check=True, capture_output=True)

    def test_faster_triangle_caption_scan_and_fixed_wordmark(self):
        for width, height in [(480, 340), (480, 250), (240, 170)]:
            with self.subTest(size=(width, height)):
                result = subprocess.run([str(self.binary), str(width), str(height)],
                                        capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
