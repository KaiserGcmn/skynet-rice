"""Known sensor feedback must not relabel unrelated/password PAM messages."""
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BiometricNoticeTest(unittest.TestCase):
    def test_sensor_messages_and_unknown_fallback(self):
        if not shutil.which('cc') or not shutil.which('pkg-config'):
            self.skipTest('requires C compiler and Cairo development files')
        flags = subprocess.run(['pkg-config', '--cflags', '--libs', 'cairo'],
                               capture_output=True, text=True)
        if flags.returncode:
            self.skipTest('requires Cairo development files')
        with tempfile.TemporaryDirectory(prefix='skynet-biometric-test-') as work:
            source = Path(work) / 'check.c'
            source.write_text(r'''
#include "skynet-biometric.h"
#include <assert.h>
int main(void) {
    assert(skynet_biometric_notice("Failed to match fingerprint") == BIOMETRIC_NO_MATCH);
    assert(skynet_biometric_notice("Verification timed out") == BIOMETRIC_TIMEOUT);
    assert(skynet_biometric_notice("Your finger was not centered, try touching the sensor again") == BIOMETRIC_RETRY);
    assert(skynet_biometric_notice("An unexpected error happened during finger verification") == BIOMETRIC_READER_ERROR);
    const char *plain[] = {NULL, "", "Authentication failure", "Password:",
        "Failed to match fingerprint: unsupported variant", "verify-match",
        "Place your right index finger on the fingerprint reader", "Success"};
    for (size_t i = 0; i < sizeof(plain)/sizeof(plain[0]); ++i)
        assert(skynet_biometric_notice(plain[i]) == BIOMETRIC_NONE);
    cairo_surface_t *surface = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, 520, 184);
    cairo_t *cr = cairo_create(surface);
    for (int notice = BIOMETRIC_NONE; notice <= BIOMETRIC_READER_ERROR; ++notice) {
        skynet_biometric_draw(cr, 520, 184, 0, 10, notice);
        skynet_biometric_draw(cr, 260, 92, -1, 0, notice);
        assert(cairo_status(cr) == CAIRO_STATUS_SUCCESS);
    }
    cairo_destroy(cr); cairo_surface_destroy(surface);
    return 0;
}
''')
            binary = Path(work) / 'check'
            subprocess.run(['cc', '-Wall', '-Wextra', '-Werror', '-I',
                            str(ROOT / 'sources/xsecurelock-power'), str(source),
                            '-o', str(binary), *shlex.split(flags.stdout)], check=True)
            subprocess.run([str(binary)], check=True)


def compile_and_run(test, program):
    if not shutil.which('cc') or not shutil.which('pkg-config'):
        test.skipTest('requires C compiler and Cairo development files')
    flags = subprocess.run(['pkg-config', '--cflags', '--libs', 'cairo'],
                           capture_output=True, text=True)
    if flags.returncode:
        test.skipTest('requires Cairo development files')
    with tempfile.TemporaryDirectory(prefix='skynet-biometric-test-') as work:
        source = Path(work) / 'check.c'
        source.write_text(program)
        binary = Path(work) / 'check'
        # No -lm: auth_x11 links the panel without libm.
        subprocess.run(['cc', '-Wall', '-Wextra', '-Werror', '-I',
                        str(ROOT / 'sources/xsecurelock-power'), str(source),
                        '-o', str(binary), *shlex.split(flags.stdout)], check=True)
        subprocess.run([str(binary)], check=True)


class BiometricPanelTest(unittest.TestCase):
    """22 Nov 2026 scanner redesign: timeline, alerts and stable repaints."""

    def test_header_needs_no_libm(self):
        header = (ROOT / 'sources/xsecurelock-power/skynet-biometric.h').read_text()
        self.assertNotIn('<math.h>', header)
        for call in ('sin(', 'cos(', 'fmod(', 'sqrt(', 'floor('):
            self.assertNotIn(' ' + call, header)

    def test_timeline_tracks_remaining_time_and_alerts_are_static(self):
        compile_and_run(self, r'''
#include "skynet-biometric.h"
#include <assert.h>
#include <stdlib.h>
#include <unistd.h>
static cairo_surface_t *surface;
static unsigned pixel(int x, int y) {
    cairo_surface_flush(surface);
    unsigned char *data = cairo_image_surface_get_data(surface);
    int stride = cairo_image_surface_get_stride(surface);
    return *(unsigned *)(data + y * stride + x * 4) & 0xffffff;
}
static void draw(int seconds, enum biometric_notice notice) {
    cairo_t *cr = cairo_create(surface);
    skynet_biometric_draw(cr, 520, 184, seconds, 10, notice);
    assert(cairo_status(cr) == CAIRO_STATUS_SUCCESS);
    cairo_destroy(cr);
}
static int red(unsigned c) { return (c >> 16) > 0xb0 && ((c >> 8) & 255) < 0x60; }
int main(void) {
    assert(skynet_biometric_notice("Verification timed out") == BIOMETRIC_TIMEOUT);
    surface = cairo_image_surface_create(CAIRO_FORMAT_RGB24, 520, 184);
    const int first = 20, last = 16 + 39 * 12.2 + 4, y = 150;
    draw(10, BIOMETRIC_NONE);            /* full time: every cell lit */
    assert(red(pixel(first, y)) && red(pixel(last, y)));
    unsigned calm = pixel(first, y);
    draw(5, BIOMETRIC_NONE);             /* half time: right half dark */
    assert(red(pixel(first, y)) && !red(pixel(last, y)));
    draw(2, BIOMETRIC_NONE);             /* last seconds: brighter red */
    assert(red(pixel(first, y)) && pixel(first, y) != calm);
    draw(0, BIOMETRIC_NONE);             /* awaiting result: nothing lit */
    assert(!red(pixel(first, y)) && !red(pixel(last, y)));
    /* Only the armed scanner animates; result/alert frames never change
     * between repaints, so nothing flickers. */
    for (int notice = BIOMETRIC_NONE; notice <= BIOMETRIC_READER_ERROR; ++notice) {
        draw(0, notice);
        size_t size = cairo_image_surface_get_stride(surface) * 184;
        unsigned char *before = malloc(size);
        cairo_surface_flush(surface);
        memcpy(before, cairo_image_surface_get_data(surface), size);
        usleep(300000);
        draw(0, notice);
        cairo_surface_flush(surface);
        assert(!memcmp(before, cairo_image_surface_get_data(surface), size));
        free(before);
    }
    cairo_surface_destroy(surface);
    return 0;
}
''')


if __name__ == '__main__':
    unittest.main()
