/* SKYNET biometric display. Presentation only; authentication owns the timer.
 * Shared native Cairo geometry for the GTK greeter and X11 auth display.
 * SPDX-License-Identifier: MIT
 */
#ifndef SKYNET_BIOMETRIC_H
#define SKYNET_BIOMETRIC_H
#include <cairo/cairo.h>
#include <stdio.h>

static void biometric_text(cairo_t *cr, double x, double y, double size,
                           int bright, const char *text) {
    cairo_select_font_face(cr, "JetBrains Mono", CAIRO_FONT_SLANT_NORMAL,
                           size >= 30 ? CAIRO_FONT_WEIGHT_BOLD : CAIRO_FONT_WEIGHT_NORMAL);
    cairo_set_font_size(cr, size);
    if (bright) cairo_set_source_rgb(cr, .96, .91, .93);
    else cairo_set_source_rgb(cr, .65, .47, .52);
    cairo_move_to(cr, x, y);
    cairo_show_text(cr, text);
}

static void skynet_biometric_draw(cairo_t *cr, double width, double height,
                                  int seconds, int duration) {
    if (duration < 1) duration = 10;
    if (seconds < 0) seconds = 0;
    if (seconds > duration) seconds = duration;
    double scale = width / 420.0;
    if (height / 172.0 < scale) scale = height / 172.0;
    cairo_save(cr);
    cairo_translate(cr, (width - 420 * scale) / 2, (height - 172 * scale) / 2);
    cairo_scale(cr, scale, scale);
    cairo_rectangle(cr, 0, 0, 420, 172);
    cairo_clip(cr);
    cairo_set_source_rgb(cr, .035, .012, .020);
    cairo_paint(cr);
    cairo_set_line_width(cr, 1);
    cairo_set_source_rgb(cr, .31, .075, .13);
    cairo_rectangle(cr, .5, .5, 419, 171);
    cairo_stroke(cr);
    /* Short mechanical corner brackets. */
    cairo_set_source_rgb(cr, .95, .17, .29);
    cairo_set_line_width(cr, 2);
    for (int side = 0; side < 2; ++side) {
        cairo_save(cr);
        if (side) { cairo_translate(cr, 420, 172); cairo_rotate(cr, 3.141592653589793); }
        cairo_move_to(cr, 1, 19); cairo_line_to(cr, 1, 1); cairo_line_to(cr, 19, 1);
        cairo_stroke(cr);
        cairo_restore(cr);
    }
    biometric_text(cr, 20, 26, 11, 0, "BIOMETRIC / IDENTITY CHECK");
    /* Fingerprint ridges, drawn directly rather than loading an icon. */
    cairo_set_source_rgb(cr, .94, .18, .30);
    cairo_set_line_width(cr, 1.7);
    cairo_set_line_cap(cr, CAIRO_LINE_CAP_ROUND);
    for (int ridge = 0; ridge < 4; ++ridge) {
        double x = 22 + ridge * 5, y = 77, r = 19 - ridge * 5;
        cairo_move_to(cr, x, y + 17 - ridge * 2);
        cairo_line_to(cr, x, y);
        cairo_curve_to(cr, x, y - r * 1.5, x + 2*r, y - r * 1.5, x + 2*r, y);
        cairo_curve_to(cr, x + 2*r, y + 13, x + 2*r - 3, y + 19, x + 2*r - 7, y + 24);
        cairo_stroke(cr);
    }
    biometric_text(cr, 83, 68, 14, 1, seconds ? "SCAN FINGERPRINT" : "SCAN COMPLETE");
    biometric_text(cr, 83, 89, 10, 0, seconds ? "HOLD YOUR FINGER STEADY" : "AWAITING RESULT");
    char number[16];
    snprintf(number, sizeof(number), "%02d", seconds);
    biometric_text(cr, 313, 91, 52, 1, number);
    /* The final three seconds gain a red underline; no blinking. */
    cairo_set_source_rgb(cr, seconds > 0 && seconds <= 3 ? 1 : .50, .13, .23);
    cairo_rectangle(cr, 315, 101, 64, 2); cairo_fill(cr);
    biometric_text(cr, 313, 116, 9, 0, "SEC LEFT");
    for (int cell = 0; cell < 20; ++cell) {
        int lit = cell * duration < seconds * 20;
        if (lit) cairo_set_source_rgb(cr, seconds <= 3 ? 1 : .91, .16, .28);
        else cairo_set_source_rgb(cr, .16, .035, .065);
        cairo_rectangle(cr, 20 + cell * 19.2, 132, 15.2, 5);
        cairo_fill(cr);
    }
    biometric_text(cr, 20, 156, 9, 0, "SKYNET / ACCESS CONTROL");
    biometric_text(cr, 298, 156, 9, 0, "PASSWORD FOLLOWS");
    cairo_restore(cr);
}
#endif
