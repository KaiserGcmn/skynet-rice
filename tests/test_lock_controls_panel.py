"""Lock-screen hardware readout (SEC 08): HUD-style Cairo cards."""
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
STYLE = ROOT / 'sources/xsecurelock-style'

PROGRAM = r'''
#include <X11/Xlib.h>
#include <X11/Xft/Xft.h>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "lock-controls.h"

static cairo_surface_t *surface;
static unsigned px(int x, int y) {
    unsigned char *d = cairo_image_surface_get_data(surface);
    return *(unsigned *)(d + y * cairo_image_surface_get_stride(surface) + x * 4) & 0xffffff;
}
static void draw(const int *values, int compact) {
    int h = compact ? 94 : 124;
    surface = cairo_image_surface_create(CAIRO_FORMAT_RGB24, 908, h + 48);
    cairo_t *cr = cairo_create(surface);
    controls_render(cr, 908, h + 48, 900, h, values, compact);
    assert(cairo_status(cr) == CAIRO_STATUS_SUCCESS);
    cairo_destroy(cr);
    cairo_surface_flush(surface);
}
/* Count pixels of one colour inside a rectangle. */
static int count(int x0, int y0, int x1, int y1, unsigned rgb) {
    int n = 0;
    for (int y = y0; y < y1; ++y)
        for (int x = x0; x < x1; ++x) n += px(x, y) == rgb;
    return n;
}
int main(void) {
    /* Audio card spans x 4..296; its meter row is y 24+8+78 .. +8. */
    int meter = 24 + 8 + 78;
    int live[5] = {80, 0, 100, 0, 50};
    draw(live, 0);
    assert(px(5, 8) == CTL_RED);                       /* header tab */
    assert(count(18, meter, 282, meter + 8, CTL_RED_MID) > 100);
    assert(count(150, 24 + 40, 296, 24 + 80, CTL_RED_MID) == 0);  /* no MUTED badge */
    cairo_surface_destroy(surface);

    int muted[5] = {80, 1, 100, 1, 50};
    draw(muted, 0);
    assert(count(150, 24 + 40, 296, 24 + 80, CTL_RED_MID) > 200);  /* MUTED badge */
    assert(count(18, meter, 282, meter + 8, CTL_RED_MID) == 0);   /* meter dimmed */
    cairo_surface_destroy(surface);

    int unknown[5] = {-1, -1, -1, -1, -1};
    draw(unknown, 0);
    for (int card = 0; card < 3; ++card) {
        int x = 4 + card * (292 + 12);
        assert(count(x + 14, meter - 3, x + 278, meter + 11, CTL_RED_MID) == 0);
        assert(count(x + 14, meter - 3, x + 278, meter + 11, CTL_RED) == 0);
    }
    cairo_surface_destroy(surface);

    draw(live, 1);                                      /* short screens */
    assert(cairo_image_surface_get_height(surface) == 94 + 48);
    cairo_surface_destroy(surface);
    return 0;
}
'''


class LockControlsPanelTest(unittest.TestCase):
    def test_states_render_in_hud_style(self):
        if not shutil.which('cc') or not shutil.which('pkg-config'):
            self.skipTest('requires a C compiler')
        flags = subprocess.run(['pkg-config', '--cflags', '--libs', 'xft', 'cairo'],
                               capture_output=True, text=True)
        if flags.returncode:
            self.skipTest('requires Xft and Cairo development files')
        with tempfile.TemporaryDirectory(prefix='skynet-controls-test-') as work:
            source = Path(work) / 'check.c'
            source.write_text(PROGRAM)
            binary = Path(work) / 'check'
            subprocess.run(['cc', '-Wall', '-Wextra', '-Werror', '-Wno-unused-function',
                            '-I', str(STYLE), str(source), '-o', str(binary),
                            *shlex.split(flags.stdout), '-lX11', '-lm'], check=True)
            subprocess.run([str(binary)], check=True)

    def test_values_are_display_only(self):
        header = (STYLE / 'lock-controls.h').read_text()
        # The readout never runs commands or touches input; it only draws.
        self.assertNotIn('system(', header)
        self.assertNotIn('XGrab', header)


if __name__ == '__main__':
    unittest.main()
