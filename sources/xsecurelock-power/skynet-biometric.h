/* SKYNET lock-screen biometric presentation. No input or authentication.
 * The caller owns the deadline; zero is not a success/failure result.
 * SPDX-License-Identifier: MIT
 */
#ifndef SKYNET_BIOMETRIC_H
#define SKYNET_BIOMETRIC_H
#include <cairo/cairo.h>
#include <stdio.h>
#include <string.h>

#define SKYNET_BIOMETRIC_WIDTH 520
#define SKYNET_BIOMETRIC_HEIGHT 184

/* Presentation only. Match known pam_fprintd English messages exactly;
 * unrelated PAM/password errors retain the standard error presentation. */
enum biometric_notice {
    BIOMETRIC_NONE, BIOMETRIC_NO_MATCH, BIOMETRIC_TIMEOUT,
    BIOMETRIC_RETRY, BIOMETRIC_READER_ERROR
};
static enum biometric_notice skynet_biometric_notice(const char *message) {
    if (!message) return BIOMETRIC_NONE;
    if (!strcmp(message, "Failed to match fingerprint")) return BIOMETRIC_NO_MATCH;
    if (!strcmp(message, "Verification timed out")) return BIOMETRIC_TIMEOUT;
    if (!strcmp(message, "An unexpected error happened during finger verification"))
        return BIOMETRIC_READER_ERROR;
    const char *retry[] = {
        "Swipe your finger again", "Place your finger on the reader again",
        "Swipe was too fast, try again", "Swipe was too short, try again",
        "Finger scan was too fast, try again",
        "Your finger was not centered, try swiping your finger again",
        "Your finger was not centered, try touching the sensor again",
        "Remove your finger, and try swiping your finger again",
        "Remove your finger, and try touching the sensor again"
    };
    for (size_t i = 0; i < sizeof(retry) / sizeof(retry[0]); ++i)
        if (!strcmp(message, retry[i])) return BIOMETRIC_RETRY;
    return BIOMETRIC_NONE;
}

static void biometric_color(cairo_t *cr, unsigned rgb) {
    cairo_set_source_rgb(cr, ((rgb >> 16) & 255) / 255.,
                         ((rgb >> 8) & 255) / 255., (rgb & 255) / 255.);
}

static void biometric_text(cairo_t *cr, double x, double y, double size,
                           unsigned color, int bold, const char *text) {
    cairo_select_font_face(cr, "JetBrains Mono", CAIRO_FONT_SLANT_NORMAL,
                           bold ? CAIRO_FONT_WEIGHT_BOLD : CAIRO_FONT_WEIGHT_NORMAL);
    cairo_set_font_size(cr, size);
    biometric_color(cr, color);
    cairo_move_to(cr, x, y);
    cairo_show_text(cr, text);
}

static void biometric_fingerprint(cairo_t *cr, int seconds, int duration) {
    const double pi = 3.141592653589793;
    cairo_set_line_cap(cr, CAIRO_LINE_CAP_BUTT);
    cairo_set_line_width(cr, 2);
    /* These segments mirror time remaining, never scan quality/progress. */
    for (int tick = 0; tick < 28; ++tick) {
        int lit = tick * duration < seconds * 28;
        biometric_color(cr, lit ? (seconds <= 3 ? 0xff4762 : 0xbe2941) : 0x36232a);
        double angle = -pi / 2 + tick * 2 * pi / 28;
        cairo_arc(cr, 69, 88, 39, angle, angle + 2 * pi / 28 - .07);
        cairo_stroke(cr);
    }
    biometric_color(cr, 0x21171c);
    cairo_set_line_width(cr, 1);
    cairo_arc(cr, 69, 88, 33, 0, 2 * pi);
    cairo_stroke(cr);
    /* Open, nested ridges with unequal tails: recognizable at small sizes. */
    cairo_set_line_cap(cr, CAIRO_LINE_CAP_ROUND);
    cairo_set_line_width(cr, 1.65);
    for (int ridge = 0; ridge < 5; ++ridge) {
        double r = 24 - ridge * 4.5;
        biometric_color(cr, seconds ? (ridge % 2 ? 0xd48f9c : 0xf04a65) : 0x875e69);
        cairo_move_to(cr, 69 - r, 91 + (4 - ridge) * 2);
        cairo_curve_to(cr, 69 - r - 1, 67 - r * .3,
                       69 + r, 65 - r * .3, 69 + r, 87);
        cairo_curve_to(cr, 69 + r, 99, 69 + r - 5, 107 - ridge * .4,
                       69 + r - 10, 113 - ridge);
        cairo_stroke(cr);
    }
    biometric_color(cr, seconds ? 0xf04a65 : 0x875e69);
    cairo_move_to(cr, 52, 105);
    cairo_curve_to(cr, 52, 111, 49, 115, 47, 117);
    cairo_move_to(cr, 60, 103);
    cairo_curve_to(cr, 59, 112, 56, 118, 54, 121);
    cairo_stroke(cr);
    cairo_set_line_cap(cr, CAIRO_LINE_CAP_BUTT);
}

static void skynet_biometric_draw(cairo_t *cr, double width, double height,
                                  int seconds, int duration,
                                  enum biometric_notice notice) {
    if (width <= 0 || height <= 0) return;
    if (duration < 1) duration = 10;
    if (duration > 60) duration = 60;
    if (seconds < 0) seconds = 0;
    if (seconds > duration) seconds = duration;
    double scale = width / SKYNET_BIOMETRIC_WIDTH;
    if (height / SKYNET_BIOMETRIC_HEIGHT < scale)
        scale = height / SKYNET_BIOMETRIC_HEIGHT;
    cairo_save(cr);
    cairo_translate(cr, (width - SKYNET_BIOMETRIC_WIDTH * scale) / 2,
                         (height - SKYNET_BIOMETRIC_HEIGHT * scale) / 2);
    cairo_scale(cr, scale, scale);
    cairo_rectangle(cr, 0, 0, SKYNET_BIOMETRIC_WIDTH, SKYNET_BIOMETRIC_HEIGHT);
    cairo_clip(cr);
    biometric_color(cr, 0x0c090c);
    cairo_paint(cr);
    /* Fine outer frame and short mechanical corner brackets. */
    biometric_color(cr, 0x57232f);
    cairo_set_line_width(cr, 1);
    cairo_rectangle(cr, .5, .5, 519, 183);
    cairo_stroke(cr);
    biometric_color(cr, 0xde304c);
    cairo_set_line_width(cr, 2);
    for (int corner = 0; corner < 4; ++corner) {
        double x = corner & 1 ? 519 : 1;
        double y = corner & 2 ? 183 : 1;
        double dx = corner & 1 ? -1 : 1;
        double dy = corner & 2 ? -1 : 1;
        cairo_move_to(cr, x, y + dy * 12);
        cairo_line_to(cr, x, y);
        cairo_line_to(cr, x + dx * 18, y);
        cairo_stroke(cr);
    }
    biometric_text(cr, 19, 23, 10, 0xb59aa2, 0, "BIOMETRIC / 01");
    biometric_text(cr, 449, 23, 10, 0xe6d7dc, 1, "SKYNET");
    biometric_color(cr, 0x38202a);
    cairo_set_line_width(cr, 1);
    cairo_move_to(cr, 18, 34.5); cairo_line_to(cr, 502, 34.5);
    cairo_move_to(cr, 395.5, 49); cairo_line_to(cr, 395.5, 126);
    cairo_stroke(cr);
    if (notice != BIOMETRIC_NONE) {
        const char *title = "PRINT NOT MATCHED";
        const char *hint = "LIFT AND REPOSITION YOUR FINGER";
        const char *tag = "NO MATCH";
        if (notice == BIOMETRIC_TIMEOUT) {
            title = "SCAN TIMED OUT"; hint = "NO RESULT WITHIN THE TIME LIMIT"; tag = "TIMEOUT";
        } else if (notice == BIOMETRIC_RETRY) {
            title = "ADJUST YOUR FINGER"; hint = "FOLLOW THE READER MESSAGE ABOVE"; tag = "RETRY";
        } else if (notice == BIOMETRIC_READER_ERROR) {
            title = "READER ERROR"; hint = "FINGERPRINT CHECK INTERRUPTED"; tag = "ERROR";
        }
        biometric_fingerprint(cr, 0, duration);
        /* A filled status badge, without flashing or a fake progress meter. */
        biometric_color(cr, 0x261019);
        cairo_arc(cr, 94, 112, 14, 0, 6.283185307179586); cairo_fill(cr);
        biometric_color(cr, 0xff4964); cairo_set_line_width(cr, 2);
        cairo_arc(cr, 94, 112, 14, 0, 6.283185307179586); cairo_stroke(cr);
        if (notice == BIOMETRIC_NO_MATCH) {
            cairo_move_to(cr, 89, 107); cairo_line_to(cr, 99, 117);
            cairo_move_to(cr, 99, 107); cairo_line_to(cr, 89, 117); cairo_stroke(cr);
        } else {
            biometric_text(cr, 90, 118, 18, 0xff6b80, 1, "!");
        }
        biometric_text(cr, 126, 72, 17, 0xff6b80, 1, title);
        biometric_text(cr, 127, 96, 9, 0xd6abb6, 0, hint);
        biometric_text(cr, 127, 115, 9, 0xb2959f, 0, "FOLLOW NEXT PROMPT TO CONTINUE");
        biometric_text(cr, 443, 99, 46, 0xff4964, 1, "!");
        biometric_text(cr, 424, 120, 9, 0xd6abb6, 1, tag);
        biometric_color(cr, 0x632334); cairo_set_line_width(cr, 1);
        cairo_move_to(cr, 20, 143.5); cairo_line_to(cr, 500, 143.5); cairo_stroke(cr);
        biometric_text(cr, 20, 169, 9, 0xff6b80, 1, "LOCK REMAINS ACTIVE");
        biometric_text(cr, 380, 169, 9, 0xb59aa2, 0, "PASSWORD FALLBACK");
    } else {
        biometric_fingerprint(cr, seconds, duration);
        biometric_text(cr, 126, 72, seconds ? 17 : 16, 0xeee4e8, 1,
                       seconds ? "VERIFY IDENTITY" : "WAITING FOR RESULT");
        biometric_text(cr, 127, 95, 10, 0xc198a4, 0,
                       seconds ? "PLACE FINGER ON SENSOR" : "FOLLOW THE NEXT PROMPT");
        biometric_text(cr, 127, 114, 9, 0x9e808a, 0,
                       seconds ? "HOLD YOUR FINGER STEADY" : "AUTHENTICATION IN PROGRESS");
        char number[8];
        snprintf(number, sizeof(number), "%02d", seconds);
        biometric_text(cr, 420, 99, 46,
                       seconds > 0 && seconds <= 3 ? 0xff6b80 : 0xf0e7eb, 1, number);
        biometric_text(cr, 416, 120, 8, 0xb2959f, 0, "SECONDS LEFT");
        /* Linear countdown, with a quiet empty track once time runs out. */
        for (int cell = 0; cell < 30; ++cell) {
            int lit = cell * duration < seconds * 30;
            biometric_color(cr, lit ? (seconds <= 3 ? 0xff4762 : 0xc82f48) : 0x2f1c24);
            cairo_rectangle(cr, 20 + cell * 16, 143, 12, 4);
            cairo_fill(cr);
        }
        biometric_text(cr, 20, 169, 9, 0x9e808a, 0, "FINGERPRINT READER");
        biometric_text(cr, 380, 169, 9, 0xb59aa2, 0, "PASSWORD FALLBACK");
    }
    cairo_restore(cr);
}
#endif
