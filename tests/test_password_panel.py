"""The lock password panel draws only masked state and stays inside its box."""
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HEADER = ROOT / 'sources/xsecurelock-power/skynet-password.h'


class PasswordPanelTest(unittest.TestCase):
    def test_header_receives_no_password_text(self):
        # The drawing API takes a count and cursor state, never input bytes.
        source = HEADER.read_text()
        signature = re.search(r'static void skynet_password_draw\((.*?)\)\s*\{',
                              source, re.S).group(1)
        self.assertIn('size_t count', signature)
        self.assertNotRegex(signature, r'pwbuf|password\b|response|input')

    def test_draws_masked_states_within_bounds(self):
        if not shutil.which('cc') or not shutil.which('pkg-config'):
            self.skipTest('requires C compiler and Cairo development files')
        flags = subprocess.run(['pkg-config', '--cflags', '--libs', 'cairo'],
                               capture_output=True, text=True)
        if flags.returncode:
            self.skipTest('requires Cairo development files')
        with tempfile.TemporaryDirectory(prefix='skynet-password-test-') as work:
            source = Path(work) / 'check.c'
            source.write_text(r'''
#include "skynet-password.h"
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>

/* Render into the middle of a larger transparent surface; nothing may land
 * outside the panel rectangle. */
static unsigned char *render(size_t count, int cursor, int warning,
                             const char *name, const char *prompt,
                             const char *datetime) {
    const int pad = 40, w = SKYNET_PASSWORD_WIDTH + 2 * pad;
    const int h = SKYNET_PASSWORD_HEIGHT + 2 * pad;
    cairo_surface_t *s = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, w, h);
    cairo_t *cr = cairo_create(s);
    cairo_translate(cr, pad, pad);
    skynet_password_draw(cr, name, prompt, datetime, count, cursor, warning);
    assert(cairo_status(cr) == CAIRO_STATUS_SUCCESS);
    cairo_surface_flush(s);
    int stride = cairo_image_surface_get_stride(s);
    unsigned char *data = cairo_image_surface_get_data(s);
    for (int y = 0; y < h; ++y)
        for (int x = 0; x < w; ++x) {
            int inside = x >= pad && x < pad + SKYNET_PASSWORD_WIDTH &&
                         y >= pad && y < pad + SKYNET_PASSWORD_HEIGHT;
            uint32_t px = *(uint32_t *)(data + y * stride + 4 * x);
            if (!inside) assert(px == 0);
        }
    unsigned char *copy = malloc((size_t)stride * h);
    memcpy(copy, data, (size_t)stride * h);
    cairo_destroy(cr); cairo_surface_destroy(s);
    return copy;
}

int main(void) {
    const char *longtext =
        "AN-EXTREMELY-LONG-OPERATOR-NAME-THAT-WOULD-OTHERWISE-OVERFLOW-THE-PANEL-BOX";
    size_t counts[] = {0, 1, 7, 21, 22, 23, 28, 29, 255, (size_t)-1};
    size_t size = (size_t)cairo_format_stride_for_width(
        CAIRO_FORMAT_ARGB32, SKYNET_PASSWORD_WIDTH + 80) * (SKYNET_PASSWORD_HEIGHT + 80);
    for (size_t i = 0; i < sizeof(counts) / sizeof(counts[0]); ++i) {
        free(render(counts[i], 1, 0, "operator", "Password:", "12:00  |  01.01.2026"));
        free(render(counts[i], 0, 1, longtext, longtext, longtext));
        free(render(counts[i], 1, 0, NULL, NULL, NULL));
        free(render(counts[i], 0, 0, "", "", ""));
    }
    /* Same masked state gives the same image; typed length and cursor change it. */
    unsigned char *a = render(5, 1, 0, "op", "Password:", "");
    unsigned char *b = render(5, 1, 0, "op", "Password:", "");
    unsigned char *c = render(6, 1, 0, "op", "Password:", "");
    unsigned char *d = render(5, 0, 0, "op", "Password:", "");
    assert(!memcmp(a, b, size));
    assert(memcmp(a, c, size));
    assert(memcmp(a, d, size));
    free(a); free(b); free(c); free(d);
    return 0;
}
''')
            binary = Path(work) / 'check'
            subprocess.run(['cc', '-Wall', '-Wextra', '-Werror', '-I',
                            str(HEADER.parent), str(source),
                            '-o', str(binary), *shlex.split(flags.stdout)], check=True)
            subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    unittest.main()
