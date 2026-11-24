/* SKYNET lock-screen password presentation. No input or authentication.
 * Receives only what the asterisk prompt already shows: the number of masked
 * characters and whether the blinking cursor is visible.
 * SPDX-License-Identifier: MIT
 */
#ifndef SKYNET_PASSWORD_H
#define SKYNET_PASSWORD_H
#include <cairo/cairo.h>
#include <stdio.h>
#include <string.h>

#define SKYNET_PASSWORD_WIDTH 520
#define SKYNET_PASSWORD_HEIGHT 168
#define SKYNET_PASSWORD_MARKS 22

static void password_color(cairo_t *cr, unsigned rgb) {
    cairo_set_source_rgb(cr, ((rgb >> 16) & 255) / 255.,
                         ((rgb >> 8) & 255) / 255., (rgb & 255) / 255.);
}

static void password_text(cairo_t *cr, double x, double y, double size,
                          unsigned color, int bold, const char *text) {
    cairo_select_font_face(cr, "JetBrains Mono", CAIRO_FONT_SLANT_NORMAL,
                           bold ? CAIRO_FONT_WEIGHT_BOLD : CAIRO_FONT_WEIGHT_NORMAL);
    cairo_set_font_size(cr, size);
    password_color(cr, color);
    cairo_move_to(cr, x, y);
    cairo_show_text(cr, text);
}

/* Draw text clipped to a maximum width so long PAM prompts or user names
 * never leave the panel. */
static void password_text_fit(cairo_t *cr, double x, double y, double size,
                              unsigned color, int bold, const char *text,
                              double max_width) {
    cairo_save(cr);
    cairo_rectangle(cr, x, y - size - 4, max_width, size + 10);
    cairo_clip(cr);
    password_text(cr, x, y, size, color, bold, text);
    cairo_restore(cr);
}

static void password_lock_icon(cairo_t *cr, size_t count) {
    const double pi = 3.141592653589793;
    /* Keystroke ring: one segment per typed character, same as the asterisks. */
    cairo_set_line_cap(cr, CAIRO_LINE_CAP_BUTT);
    cairo_set_line_width(cr, 2);
    for (int tick = 0; tick < 28; ++tick) {
        int lit = (size_t)tick < count;
        password_color(cr, lit ? 0xd02f49 : 0x36232a);
        double angle = -pi / 2 + tick * 2 * pi / 28;
        cairo_arc(cr, 69, 92, 39, angle, angle + 2 * pi / 28 - .07);
        cairo_stroke(cr);
    }
    password_color(cr, 0x21171c);
    cairo_set_line_width(cr, 1);
    cairo_arc(cr, 69, 92, 33, 0, 2 * pi);
    cairo_stroke(cr);
    /* Padlock: shackle, body and keyhole. */
    password_color(cr, 0xf04a65);
    cairo_set_line_width(cr, 2.4);
    cairo_arc(cr, 69, 86, 9, pi, 2 * pi);
    cairo_move_to(cr, 60, 86); cairo_line_to(cr, 60, 90);
    cairo_move_to(cr, 78, 86); cairo_line_to(cr, 78, 90);
    cairo_stroke(cr);
    cairo_rectangle(cr, 55, 90, 28, 21);
    cairo_fill(cr);
    password_color(cr, 0x0c090c);
    cairo_arc(cr, 69, 98, 3, 0, 2 * pi);
    cairo_fill(cr);
    cairo_rectangle(cr, 67.8, 99, 2.4, 7);
    cairo_fill(cr);
}

static void skynet_password_draw(cairo_t *cr, const char *operator_name,
                                 const char *prompt, const char *datetime,
                                 size_t count, int cursor_visible, int warning) {
    const double pi = 3.141592653589793;
    cairo_save(cr);
    cairo_rectangle(cr, 0, 0, SKYNET_PASSWORD_WIDTH, SKYNET_PASSWORD_HEIGHT);
    cairo_clip(cr);
    password_color(cr, 0x0c090c);
    cairo_paint(cr);
    /* Fine outer frame and short mechanical corner brackets (biometric style). */
    password_color(cr, 0x57232f);
    cairo_set_line_width(cr, 1);
    cairo_rectangle(cr, .5, .5, 519, 167);
    cairo_stroke(cr);
    password_color(cr, 0xde304c);
    cairo_set_line_width(cr, 2);
    for (int corner = 0; corner < 4; ++corner) {
        double x = corner & 1 ? 519 : 1;
        double y = corner & 2 ? 167 : 1;
        double dx = corner & 1 ? -1 : 1;
        double dy = corner & 2 ? -1 : 1;
        cairo_move_to(cr, x, y + dy * 12);
        cairo_line_to(cr, x, y);
        cairo_line_to(cr, x + dx * 18, y);
        cairo_stroke(cr);
    }
    password_text(cr, 19, 23, 10, 0xb59aa2, 0, "ACCESS KEY / 02");
    password_text(cr, 449, 23, 10, 0xe6d7dc, 1, "SKYNET");
    if (datetime && *datetime) {
        /* The clock moves into the header so the window stays compact. */
        cairo_text_extents_t extents;
        cairo_select_font_face(cr, "JetBrains Mono", CAIRO_FONT_SLANT_NORMAL,
                               CAIRO_FONT_WEIGHT_BOLD);
        cairo_set_font_size(cr, 11);
        cairo_text_extents(cr, datetime, &extents);
        double left = 260 - extents.x_advance / 2;
        if (left < 150) left = 150;
        password_text_fit(cr, left, 23, 11, 0xeee4e8, 1, datetime, 280);
    }
    password_color(cr, 0x38202a);
    cairo_set_line_width(cr, 1);
    cairo_move_to(cr, 18, 34.5); cairo_line_to(cr, 502, 34.5);
    cairo_stroke(cr);

    password_lock_icon(cr, count);

    /* Operator line and the PAM prompt text, verbatim. */
    password_text(cr, 127, 58, 9, 0x9e808a, 0, "OPERATOR");
    if (operator_name && *operator_name)
        password_text_fit(cr, 196, 58, 11, 0xeee4e8, 1, operator_name, 300);
    password_text_fit(cr, 127, 77, 9, warning ? 0xff6b80 : 0xc198a4, 0,
                      prompt && *prompt ? prompt : "Password:", 370);

    /* Input field. */
    password_color(cr, 0x140c10);
    cairo_rectangle(cr, 126, 88, 374, 32);
    cairo_fill(cr);
    password_color(cr, warning ? 0xa8283f : 0x57232f);
    cairo_rectangle(cr, 126.5, 88.5, 373, 31);
    cairo_stroke(cr);
    password_color(cr, 0xde304c);
    cairo_rectangle(cr, 126, 88, 3, 32);
    cairo_fill(cr);

    size_t shown = count;
    char overflow[24] = "";
    if (shown > SKYNET_PASSWORD_MARKS) {
        shown = SKYNET_PASSWORD_MARKS - 2;
        snprintf(overflow, sizeof(overflow), "+%zu", count - shown);
    }
    double x = 143;
    password_color(cr, 0xff4964);
    for (size_t i = 0; i < shown; ++i, x += 15) {
        /* A small diamond per masked character. */
        cairo_move_to(cr, x, 98);
        cairo_line_to(cr, x + 5, 104);
        cairo_line_to(cr, x, 110);
        cairo_line_to(cr, x - 5, 104);
        cairo_close_path(cr);
        cairo_fill(cr);
    }
    if (*overflow) {
        password_text(cr, x - 4, 109, 10, 0xd6abb6, 1, overflow);
        x += 30;
    }
    if (cursor_visible) {
        password_color(cr, 0xf0e7eb);
        cairo_rectangle(cr, x - 5, 96, 9, 16);
        cairo_fill(cr);
    }
    if (!count) password_text(cr, 156, 109, 9, 0x6e4d57, 0, "AWAITING INPUT");

    /* Status row. */
    password_color(cr, 0x38202a);
    cairo_set_line_width(cr, 1);
    cairo_move_to(cr, 20, 136.5); cairo_line_to(cr, 500, 136.5);
    cairo_stroke(cr);
    password_color(cr, 0xd02f49);
    cairo_arc(cr, 24, 151, 3, 0, 2 * pi);
    cairo_fill(cr);
    password_text(cr, 34, 155, 9, 0x9e808a, 0, "ENTER  /  VERIFY");
    /* Escape cancels the prompt; the next key starts the fingerprint again. */
    password_text(cr, 224, 155, 9, 0x9e808a, 0, "ESC  /  BACK");
    password_text(cr, 380, 155, 9, 0xb59aa2, 0, "CTRL-U  /  CLEAR");
    cairo_restore(cr);
}
#endif
