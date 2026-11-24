"""The login screen shares the lock HUD without its X11 parts."""
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GREETER = ROOT / 'sources/gtkgreet-hud'
STYLE = ROOT / 'sources/xsecurelock-style'
GENERATOR = STYLE / 'render-cyberpunk.py'
INSTALLED = ROOT / 'runtime/usr/local/share/hud-greeter/hud-background.png'


def pkg_flags(*libs):
    if not shutil.which('cc') or not shutil.which('pkg-config'):
        return None
    result = subprocess.run(['pkg-config', '--cflags', '--libs', *libs],
                            capture_output=True, text=True)
    return None if result.returncode else shlex.split(result.stdout)


# Uses the greeter's header exactly as the greeter does. The X11 include
# guards are pre-defined so any leftover Xlib use fails to compile.
DRIVER = r'''
#include "skynet-hud.h"

int main(void) {
    Hud *hud = &skynet_hud.hud;
    hud_layout(hud);
    if (!hud_assets(hud)) return 2;
    stats_init(&hud->stats, "/nonexistent");
    for (int i = 0; i < 4; ++i) hud->subsys[i] = -1;
    for (int i = 0; i < STATS_T_COUNT; ++i) hud->therm[i] = hud->therm_peak[i] = -1;
    hud->bat_pct = hud->bat_watts = -1;
    hud->hex_key = -1;
    hud->ready = 1;
    hud->power = (HudPowerUi){.version = 2, .pressed = -1, .hover = -1};
    /* GTK owns the power buttons: no HUD region for them. */
    if (hud->region[HUD_BUTTONS_REGION].w) return 3;
    for (int i = 0; i < HUD_REGIONS; ++i)
        if (i != HUD_BUTTONS_REGION && !hud->region[i].w) return 4;
    /* Scaling keeps the artwork aspect and centres it. */
    double s, ox, oy;
    skynet_hud_transform(1920, 1080, &s, &ox, &oy);
    if (s != .9 || oy != 0 || ox != (1920 - 1728) / 2.) return 5;
    skynet_hud_transform(1920, 1200, &s, &ox, &oy);
    if (s != 1 || ox != 0 || oy != 0) return 5;
    /* Every region, clipped as the window draw does, over several moments. */
    cairo_surface_t *art = cairo_image_surface_create(CAIRO_FORMAT_RGB24, 1920, 1200);
    cairo_t *cr = cairo_create(art);
    for (int k = 0; k < 6; ++k) {
        double t = 1000 + k * 777;
        hud_update(hud, t);
        for (int i = 0; i < HUD_REGIONS; ++i) {
            const HudRegion *g = &hud->region[i];
            if (!g->w) continue;
            cairo_save(cr);
            cairo_rectangle(cr, g->ax, g->ay, g->w, g->h);
            cairo_clip(cr);
            hud_paint(hud, i, cr, t);
            cairo_restore(cr);
        }
    }
    if (cairo_status(cr)) return 6;
    /* Power buttons: idle, hovered, pending and refused, inside 240x54. */
    cairo_surface_t *button = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, 260, 74);
    cairo_t *bc = cairo_create(button);
    cairo_translate(bc, 10, 10);
    for (int state = 0; state < 4; ++state)
        for (int a = 0; a < 2; ++a) {
            hud->power.hover = state == 1 ? a : -1;
            hud->power.status[a] = state >= 2 ? state - 1 : 0;
            cairo_set_operator(bc, CAIRO_OPERATOR_CLEAR);
            cairo_paint(bc);
            cairo_set_operator(bc, CAIRO_OPERATOR_OVER);
            hud_button(hud, bc, 5000, a, 0, 0, 240, 54);
            cairo_surface_flush(button);
            const unsigned char *p = cairo_image_surface_get_data(button);
            int stride = cairo_image_surface_get_stride(button);
            for (int y = 0; y < 74; ++y)
                for (int x = 0; x < 260; ++x)
                    if (p[y * stride + x * 4 + 3] &&
                        (x < 10 || x >= 250 || y < 10 || y >= 64)) {
                        printf("button %d state %d outside at %d,%d\n", a, state, x, y);
                        return 7;
                    }
        }
    printf("ok\n");
    return 0;
}
'''


class GreeterHudTests(unittest.TestCase):
    def test_shared_hud_builds_without_x11_and_stays_in_place(self):
        flags = pkg_flags('gtk+-3.0')
        if flags is None:
            self.skipTest('GTK 3 development files are not installed')
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp, 'driver.c')
            source.write_text(DRIVER)
            binary = Path(temp, 'driver')
            subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                            '-Wno-unused-function', '-Wno-unused-parameter',
                            '-D_X11_XLIB_H_', '-D_XSHM_H_', '-D_X11_XUTIL_H_',
                            '-I', str(GREETER), str(source), '-o', str(binary),
                            *flags, '-lm'], check=True)
            result = subprocess.run([str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_lock_header_keeps_x11_parts_behind_one_switch(self):
        text = (STYLE / 'cyber-hud.h').read_text()
        lines = text.splitlines()
        depth = []
        for number, line in enumerate(lines, 1):
            if line.startswith('#if'):
                depth.append(line)
            elif line.startswith('#endif'):
                depth.pop()
            elif re.search(r'\b(Display|XImage|XShm\w*|XPutImage|XChangeProperty|Window)\b', line) \
                    and not line.lstrip().startswith(('*', '/*')):
                self.assertIn('#ifndef HUD_NO_X11', depth,
                              f'X11 use outside the guard at line {number}')

    def test_window_and_buttons_use_hud(self):
        window = (GREETER / 'window.c').read_text()
        ui = (GREETER / 'skynet-ui.h').read_text()
        self.assertIn('skynet_hud_attach(w->window)', window)
        self.assertIn('gtk_widget_set_halign(logo,GTK_ALIGN_CENTER)', window)
        self.assertIn('skynet_hud_panel_draw', window)
        # Fullscreen only after mapping (no wlroots configure error), never
        # with a title bar or close button.
        self.assertIn('gtk_window_set_decorated(GTK_WINDOW(w->window), FALSE)', window)
        self.assertIn('"map", G_CALLBACK(window_fullscreen_on_map)', window)
        self.assertNotIn('gtk_window_fullscreen(GTK_WINDOW(w->window))', window)
        self.assertIn('skynet_hud_button_draw', ui)
        self.assertIn('gtk_widget_set_size_request(button,240,54)', ui)
        # Test mode returns before any power command is started.
        power = ui[ui.index('static void skynet_power(GtkWidget'):]
        self.assertLess(power.index('SKYNET_GREETER_POWER_TEST'),
                        power.index('g_subprocess_new'))
        # A modal dialog no longer covers the login screen on refusal.
        self.assertNotIn('gtk_message_dialog_new', ui)

    def test_emblem_and_hud_share_frame_slots(self):
        logo = (GREETER / 'skynet-logo.h').read_text()
        hud = (GREETER / 'skynet-hud.h').read_text()
        self.assertIn('/SKYNET_FRAME_SLOT_US', logo)
        self.assertIn('now / SKYNET_FRAME_SLOT_US', hud)
        self.assertIn('gtk_widget_add_tick_callback(window, skynet_hud_tick', hud)
        self.assertNotIn('g_timeout_add(16', hud)

    def test_blank_artwork_leaves_the_centre_to_the_greeter(self):
        try:
            import cairo  # noqa: F401
            import gi
            gi.require_version('PangoCairo', '1.0')
        except (ImportError, ValueError):
            self.skipTest('pycairo/PangoCairo not available')
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp, 'hud.png')
            subprocess.run([sys.executable, '-I', str(GENERATOR), '--blank', str(out)],
                           check=True)
            import cairo
            image = cairo.ImageSurface.create_from_png(str(out))
            self.assertEqual((image.get_width(), image.get_height()), (1920, 1200))
            data, stride = image.get_data(), image.get_stride()

            def lit(x0, y0, x1, y1):
                return sum(1 for y in range(y0, y1, 2) for x in range(x0, x1, 2)
                           if any(data[y * stride + x * 4:y * stride + x * 4 + 3]))
            self.assertEqual(lit(700, 60, 1220, 1100), 0)   # emblem and login box
            self.assertEqual(lit(1392, 1108, 1898, 1180), 0)  # power buttons
            self.assertGreater(lit(48, 96, 500, 870), 1000)  # left panels
            self.assertGreater(lit(1420, 96, 1872, 900), 1000)  # right panels
            # The shipped image is this generator's output.
            installed = cairo.ImageSurface.create_from_png(str(INSTALLED))
            self.assertEqual(bytes(installed.get_data()), bytes(data))


if __name__ == '__main__':
    unittest.main()
