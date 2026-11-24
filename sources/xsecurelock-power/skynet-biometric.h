/* SKYNET lock-screen biometric presentation. No input or authentication.
 * The caller owns the deadline; zero is not a success/failure result.
 * SPDX-License-Identifier: MIT
 */
#ifndef SKYNET_BIOMETRIC_H
#define SKYNET_BIOMETRIC_H
#include <cairo/cairo.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

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

/* Layout of the 520x184 panel (HUD grid: 16 px outer margin). */
#define BIO_PI 3.141592653589793
#define BIO_VIEW_X 24.0     /* scanner viewport */
#define BIO_VIEW_Y 44.0
#define BIO_VIEW_W 108.0
#define BIO_VIEW_H 92.0
#define BIO_PRINT_X 78.0    /* fingertip centre */
#define BIO_PRINT_Y 90.0
#define BIO_TEXT_X 168.0
#define BIO_VALUE_X 240.0
#define BIO_TIMER_X 452.0   /* centre of the countdown block */
#define BIO_CELLS 40

static void biometric_rgba(cairo_t *cr, unsigned rgb, double alpha) {
    cairo_set_source_rgba(cr, ((rgb >> 16) & 255) / 255.,
                          ((rgb >> 8) & 255) / 255., (rgb & 255) / 255., alpha);
}

static void biometric_color(cairo_t *cr, unsigned rgb) {
    biometric_rgba(cr, rgb, 1);
}

static void biometric_font(cairo_t *cr, double size, int bold) {
    cairo_select_font_face(cr, "JetBrains Mono", CAIRO_FONT_SLANT_NORMAL,
                           bold ? CAIRO_FONT_WEIGHT_BOLD : CAIRO_FONT_WEIGHT_NORMAL);
    cairo_set_font_size(cr, size);
}

/* Letter-spaced HUD caption; align: 0 left, 1 centre, 2 right. Returns width. */
static double biometric_tracked(cairo_t *cr, double x, double y, double size,
                                unsigned color, int bold, double spacing,
                                int align, const char *text) {
    biometric_font(cr, size, bold);
    size_t count = strlen(text);
    double width = 0;
    char glyph[2] = {0, 0};
    cairo_text_extents_t ext;
    for (size_t i = 0; i < count; ++i) {
        glyph[0] = text[i];
        cairo_text_extents(cr, glyph, &ext);
        width += ext.x_advance + (i + 1 < count ? spacing : 0);
    }
    if (align == 1) x -= width / 2;
    else if (align == 2) x -= width;
    biometric_color(cr, color);
    for (size_t i = 0; i < count; ++i) {
        glyph[0] = text[i];
        cairo_move_to(cr, x, y);
        cairo_show_text(cr, glyph);
        cairo_text_extents(cr, glyph, &ext);
        x += ext.x_advance + spacing;
    }
    return width;
}

/* Wall-clock phase for purely decorative motion (beam, status lamp).
 * The caller repaints about five times a second while the timer runs. */
static double biometric_clock(void) {
    struct timespec now;
    clock_gettime(CLOCK_MONOTONIC, &now);
    return now.tv_sec + now.tv_nsec / 1e9;
}

/* Deterministic ridge breaks so the print looks natural but never flickers. */
static double biometric_hash(int a, int b) {
    unsigned v = (unsigned)(a * 73856093) ^ (unsigned)(b * 19349663);
    v ^= v >> 13; v *= 0x5bd1e995u; v ^= v >> 15;
    return (v & 0xffff) / 65535.0;
}

/* Natural breaks: each ridge gets its own short dash pattern, so the print
 * reads as skin rather than a target, and never flickers between repaints. */
static void biometric_ridge_dash(cairo_t *cr, int ridge) {
    double dash[4] = {
        9 + 22 * biometric_hash(ridge, 1), 1.4 + 1.6 * biometric_hash(ridge, 2),
        6 + 16 * biometric_hash(ridge, 3), 1.2 + 1.8 * biometric_hash(ridge, 4)};
    cairo_set_dash(cr, dash, 4, 30 * biometric_hash(ridge, 5));
}

/* A loop-type fingerprint: nested hairpins around the core, then ridges
 * running across the lower phalanx. Drawn around (0, 0); the caller clips
 * it to the fingertip outline. */
static void biometric_ridges(cairo_t *cr) {
    for (int ridge = 0; ridge < 12; ++ridge) {
        double w = 2.2 + ridge * 3.2;
        double top = -(3.5 + ridge * 3.5);
        double foot = 7 + ridge * 1.1;          /* legs end above the lower ridges */
        double lean = ridge * .35;              /* loops lean slightly right */
        biometric_ridge_dash(cr, ridge);
        cairo_move_to(cr, -w + lean, foot);
        cairo_curve_to(cr, -w + lean, top * 1.33, w + lean, top * 1.33,
                       w + lean, foot);
        /* Outer ridges sweep down the right side of the fingertip. */
        if (ridge >= 8)
            cairo_curve_to(cr, w + lean, foot + 8, w + lean - 2, foot + 16,
                           w + lean - 6, foot + 26);
        cairo_stroke(cr);
    }
    /* Lower phalanx: low arches that nest under the loop. */
    for (int ridge = 0; ridge < 7; ++ridge) {
        double y = 13 + ridge * 4.0;
        double reach = 25 - ridge * 1.2;       /* stop short of the right sweep */
        biometric_ridge_dash(cr, 40 + ridge);
        cairo_move_to(cr, -44, y + 7);
        cairo_curve_to(cr, -24, y - 3 + ridge * .3, 6, y - 3 + ridge * .3,
                       reach, y + 1);
        cairo_stroke(cr);
    }
    cairo_set_dash(cr, NULL, 0, 0);
    /* Core: a short upright rod inside the innermost hairpin. */
    cairo_move_to(cr, 0, 5);
    cairo_line_to(cr, 0, -1);
    cairo_stroke(cr);
}

static void biometric_tip_path(cairo_t *cr) {
    cairo_save(cr);
    cairo_translate(cr, BIO_PRINT_X, BIO_PRINT_Y + 2);
    cairo_scale(cr, 31, 40);
    cairo_arc(cr, 0, 0, 1, 0, 2 * BIO_PI);
    cairo_restore(cr);
}

static void biometric_print(cairo_t *cr, unsigned color, double alpha) {
    cairo_save(cr);
    biometric_tip_path(cr);
    cairo_clip(cr);
    cairo_translate(cr, BIO_PRINT_X, BIO_PRINT_Y - 6);
    cairo_set_line_cap(cr, CAIRO_LINE_CAP_ROUND);
    cairo_set_line_width(cr, 1.45);
    biometric_rgba(cr, color, alpha);
    biometric_ridges(cr);
    cairo_restore(cr);
}

/* Square scanner viewport: dot grid, ruler ticks and corner brackets. */
static void biometric_viewport(cairo_t *cr, unsigned accent) {
    biometric_color(cr, 0x080506);
    cairo_rectangle(cr, BIO_VIEW_X, BIO_VIEW_Y, BIO_VIEW_W, BIO_VIEW_H);
    cairo_fill(cr);
    biometric_color(cr, 0x241318);
    for (double y = BIO_VIEW_Y + 6; y < BIO_VIEW_Y + BIO_VIEW_H; y += 8)
        for (double x = BIO_VIEW_X + 6; x < BIO_VIEW_X + BIO_VIEW_W; x += 8)
            cairo_rectangle(cr, x, y, 1, 1);
    cairo_fill(cr);
    biometric_color(cr, 0x3a1a22);
    cairo_set_line_width(cr, 1);
    cairo_rectangle(cr, BIO_VIEW_X + .5, BIO_VIEW_Y + .5, BIO_VIEW_W - 1, BIO_VIEW_H - 1);
    cairo_stroke(cr);
    for (int i = 1; i < 8; ++i) {
        double y = BIO_VIEW_Y + i * BIO_VIEW_H / 8;
        double len = i == 4 ? 6 : 3;
        cairo_move_to(cr, BIO_VIEW_X, y + .5); cairo_line_to(cr, BIO_VIEW_X + len, y + .5);
        cairo_move_to(cr, BIO_VIEW_X + BIO_VIEW_W - len, y + .5);
        cairo_line_to(cr, BIO_VIEW_X + BIO_VIEW_W, y + .5);
    }
    cairo_stroke(cr);
    biometric_color(cr, accent);
    cairo_set_line_width(cr, 2);
    for (int corner = 0; corner < 4; ++corner) {
        double x = corner & 1 ? BIO_VIEW_X + BIO_VIEW_W - 1 : BIO_VIEW_X + 1;
        double y = corner & 2 ? BIO_VIEW_Y + BIO_VIEW_H - 1 : BIO_VIEW_Y + 1;
        double dx = corner & 1 ? -1 : 1, dy = corner & 2 ? -1 : 1;
        cairo_move_to(cr, x, y + dy * 10);
        cairo_line_to(cr, x, y);
        cairo_line_to(cr, x + dx * 10, y);
    }
    cairo_stroke(cr);
}

/* Decorative sweep while the reader is armed. It loops, so it never reads
 * as scan quality or progress. Needs no libm: auth_x11 links without -lm. */
static void biometric_beam(cairo_t *cr, double phase) {
    double top = BIO_PRINT_Y - 40, span = 84;
    double y = top + span * phase;
    cairo_save(cr);
    biometric_tip_path(cr);
    cairo_clip(cr);
    cairo_rectangle(cr, BIO_VIEW_X, y - 9, BIO_VIEW_W, 12);
    cairo_clip(cr);
    biometric_print(cr, 0xff5a70, 1);
    cairo_restore(cr);
    cairo_pattern_t *glow = cairo_pattern_create_linear(0, y - 14, 0, y + 1);
    cairo_pattern_add_color_stop_rgba(glow, 0, 1, .25, .33, 0);
    cairo_pattern_add_color_stop_rgba(glow, 1, 1, .25, .33, .22);
    cairo_rectangle(cr, BIO_VIEW_X + 2, y - 14, BIO_VIEW_W - 4, 15);
    cairo_set_source(cr, glow);
    cairo_fill(cr);
    cairo_pattern_destroy(glow);
    biometric_rgba(cr, 0xff6b80, .9);
    cairo_set_line_width(cr, 1);
    cairo_move_to(cr, BIO_VIEW_X + 4, y + .5);
    cairo_line_to(cr, BIO_VIEW_X + BIO_VIEW_W - 4, y + .5);
    cairo_stroke(cr);
}

static void biometric_row(cairo_t *cr, double y, const char *label,
                          const char *value, unsigned color) {
    biometric_tracked(cr, BIO_TEXT_X, y, 8.5, 0x8a6b75, 0, 1.2, 0, label);
    biometric_tracked(cr, BIO_VALUE_X, y, 9.5, color, 1, .8, 0, value);
}

static void biometric_alert_glyph(cairo_t *cr, enum biometric_notice notice) {
    double cx = BIO_PRINT_X, cy = BIO_PRINT_Y;
    biometric_rgba(cr, 0x0b0709, .72);
    cairo_rectangle(cr, BIO_VIEW_X + 2, BIO_VIEW_Y + 2, BIO_VIEW_W - 4, BIO_VIEW_H - 4);
    cairo_fill(cr);
    biometric_color(cr, 0xff4964);
    cairo_set_line_width(cr, 2.5);
    if (notice == BIOMETRIC_NO_MATCH) {
        cairo_arc(cr, cx, cy, 22, 0, 2 * BIO_PI);
        cairo_stroke(cr);
        cairo_move_to(cr, cx - 9, cy - 9); cairo_line_to(cr, cx + 9, cy + 9);
        cairo_move_to(cr, cx + 9, cy - 9); cairo_line_to(cr, cx - 9, cy + 9);
        cairo_stroke(cr);
    } else {
        cairo_set_line_join(cr, CAIRO_LINE_JOIN_MITER);
        cairo_move_to(cr, cx, cy - 22);
        cairo_line_to(cr, cx + 24, cy + 18);
        cairo_line_to(cr, cx - 24, cy + 18);
        cairo_close_path(cr);
        cairo_stroke(cr);
        cairo_rectangle(cr, cx - 1.5, cy - 9, 3, 15);
        cairo_rectangle(cr, cx - 1.5, cy + 9, 3, 3);
        cairo_fill(cr);
    }
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
    double now = biometric_clock();
    int alert = notice != BIOMETRIC_NONE;
    int armed = !alert && seconds > 0;
    int urgent = armed && seconds <= 3;
    cairo_save(cr);
    cairo_translate(cr, (width - SKYNET_BIOMETRIC_WIDTH * scale) / 2,
                         (height - SKYNET_BIOMETRIC_HEIGHT * scale) / 2);
    cairo_scale(cr, scale, scale);
    cairo_rectangle(cr, 0, 0, SKYNET_BIOMETRIC_WIDTH, SKYNET_BIOMETRIC_HEIGHT);
    cairo_clip(cr);
    cairo_set_line_cap(cr, CAIRO_LINE_CAP_BUTT);
    biometric_color(cr, 0x0b0709);
    cairo_paint(cr);

    /* Frame and mechanical corner brackets, as on the lock HUD panels. */
    biometric_color(cr, alert ? 0x5e1f2c : 0x45202a);
    cairo_set_line_width(cr, 1);
    cairo_rectangle(cr, .5, .5, SKYNET_BIOMETRIC_WIDTH - 1, SKYNET_BIOMETRIC_HEIGHT - 1);
    cairo_stroke(cr);
    biometric_color(cr, 0xde304c);
    cairo_set_line_width(cr, 2);
    for (int corner = 0; corner < 4; ++corner) {
        double x = corner & 1 ? SKYNET_BIOMETRIC_WIDTH - 1 : 1;
        double y = corner & 2 ? SKYNET_BIOMETRIC_HEIGHT - 1 : 1;
        double dx = corner & 1 ? -1 : 1, dy = corner & 2 ? -1 : 1;
        cairo_move_to(cr, x, y + dy * 12);
        cairo_line_to(cr, x, y);
        cairo_line_to(cr, x + dx * 18, y);
    }
    cairo_stroke(cr);

    /* Header: red tab, tracked title, section index, accent underline. */
    biometric_color(cr, 0xff4050);
    cairo_rectangle(cr, 16, 12, 3, 12);
    cairo_fill(cr);
    biometric_tracked(cr, 26, 22, 9, 0xe6dbde, 1, 1.6, 0,
                      "BIOMETRIC  //  IDENTITY SCAN");
    biometric_tracked(cr, 504, 22, 8.5, 0x7f5c67, 0, 1, 2, "SEC 09");
    biometric_color(cr, 0x3a1820);
    cairo_set_line_width(cr, 1);
    cairo_move_to(cr, 16, 32.5); cairo_line_to(cr, 504, 32.5);
    cairo_stroke(cr);
    biometric_color(cr, 0xc42a3e);
    cairo_set_line_width(cr, 1.5);
    cairo_move_to(cr, 16, 32.5); cairo_line_to(cr, 76, 32.5);
    cairo_stroke(cr);

    /* Scanner viewport with the print. */
    biometric_viewport(cr, alert ? 0xff4964 : (armed ? 0xde304c : 0x6e4750));
    biometric_print(cr, alert ? 0x5a2c37 : (armed ? 0x9c3a4d : 0x6b4650), 1);
    if (armed) {
        double cycles = now / 1.8;
        biometric_beam(cr, cycles - (double)(long long)cycles);
    }
    if (alert) biometric_alert_glyph(cr, notice);

    /* Column dividers. */
    biometric_color(cr, 0x2e161d);
    cairo_set_line_width(cr, 1);
    cairo_move_to(cr, 150.5, 46); cairo_line_to(cr, 150.5, 134);
    cairo_move_to(cr, 392.5, 46); cairo_line_to(cr, 392.5, 134);
    cairo_stroke(cr);

    const char *title, *hint, *reader, *mode, *code = NULL, *tag = NULL;
    unsigned title_color = 0xf2e9ec, reader_color = 0xff5a70;
    if (alert) {
        title_color = 0xff6b80;
        mode = "LOCKED";
        if (notice == BIOMETRIC_NO_MATCH) {
            title = "PRINT NOT MATCHED"; hint = "LIFT AND REPOSITION YOUR FINGER";
            reader = "NO MATCH"; code = "E01"; tag = "NO MATCH";
        } else if (notice == BIOMETRIC_TIMEOUT) {
            title = "SCAN TIMED OUT"; hint = "NO RESULT WITHIN THE TIME LIMIT";
            reader = "TIMEOUT"; code = "E02"; tag = "TIMEOUT";
        } else if (notice == BIOMETRIC_RETRY) {
            title = "ADJUST YOUR FINGER"; hint = "FOLLOW THE READER MESSAGE ABOVE";
            reader = "RETRY"; code = "R01"; tag = "RETRY";
        } else {
            title = "READER ERROR"; hint = "FINGERPRINT CHECK INTERRUPTED";
            reader = "FAULT"; code = "E03"; tag = "READER FAULT";
        }
    } else if (armed) {
        title = "VERIFY IDENTITY"; hint = "PLACE FINGER ON THE SENSOR";
        reader = "ARMED"; mode = "TOUCH  /  HOLD STEADY";
    } else {
        title = "AWAITING RESULT"; hint = "FOLLOW THE NEXT PROMPT";
        reader = "PROCESSING"; reader_color = 0xd6abb6; mode = "STAND BY";
    }

    /* Status column. */
    biometric_tracked(cr, BIO_TEXT_X, 64, 16, title_color, 1, .6, 0, title);
    biometric_tracked(cr, BIO_TEXT_X, 82, 9.5, 0xc198a4, 0, 1, 0, hint);
    biometric_row(cr, 106, "READER", reader, reader_color);
    biometric_row(cr, 120, "MODE", mode, 0xd9cdd1);
    biometric_row(cr, 134, "FALLBACK", "PASSWORD", 0xd9cdd1);
    /* Steady status lamp next to the reader value: no blinking. */
    biometric_color(cr, alert || armed ? 0xff4050 : 0x8a6b75);
    cairo_arc(cr, BIO_VALUE_X - 9, 103, 2.5, 0, 2 * BIO_PI);
    cairo_fill(cr);

    /* Countdown / status code block. */
    if (alert) {
        biometric_tracked(cr, BIO_TIMER_X, 60, 8.5, 0x8a6b75, 0, 1.4, 1, "STATUS CODE");
        biometric_tracked(cr, BIO_TIMER_X, 102, 36, 0xff4964, 1, 1, 1, code);
        biometric_tracked(cr, BIO_TIMER_X, 122, 9, 0xd6abb6, 1, 1.2, 1, tag);
    } else {
        char number[8];
        snprintf(number, sizeof(number), "%02d", seconds);
        biometric_tracked(cr, BIO_TIMER_X, 60, 8.5, 0x8a6b75, 0, 1.4, 1, "T-MINUS");
        biometric_tracked(cr, BIO_TIMER_X, 104, 42,
                          urgent ? 0xff5a70 : (armed ? 0xf2e9ec : 0x6e4750),
                          1, 2, 1, number);
        biometric_tracked(cr, BIO_TIMER_X, 122, 8.5, 0xa98692, 0, 1.4, 1, "SECONDS");
    }

    /* Timeline: remaining time only. Alerts show a hazard band instead. */
    if (alert) {
        cairo_save(cr);
        cairo_rectangle(cr, 16, 146, 488, 8);
        cairo_clip(cr);
        biometric_rgba(cr, 0xff4050, .5);
        for (double x = 6; x < 520; x += 12) {
            cairo_move_to(cr, x, 146);
            cairo_line_to(cr, x + 6, 146);
            cairo_line_to(cr, x - 2, 154);
            cairo_line_to(cr, x - 8, 154);
            cairo_close_path(cr);
        }
        cairo_fill(cr);
        cairo_restore(cr);
    } else {
        for (int cell = 0; cell < BIO_CELLS; ++cell) {
            int lit = cell * duration < seconds * BIO_CELLS;
            biometric_color(cr, lit ? (urgent ? 0xff4762 : 0xc82f48) : 0x2a171e);
            cairo_rectangle(cr, 16 + cell * 12.2, 148, 9, 4);
            cairo_fill(cr);
        }
        biometric_color(cr, 0x3a1820);
        cairo_set_line_width(cr, 1);
        for (int mark = 0; mark <= 4; ++mark) {
            double x = 16 + mark * (12.2 * BIO_CELLS - 3.2) / 4;
            cairo_move_to(cr, x + .5, 155); cairo_line_to(cr, x + .5, 158);
        }
        cairo_stroke(cr);
    }

    /* Footer. */
    if (alert)
        biometric_tracked(cr, 16, 174, 8.5, 0xff6b80, 1, 1.4, 0, "LOCK REMAINS ACTIVE");
    else
        biometric_tracked(cr, 16, 174, 8.5, 0x8a6b75, 0, 1.4, 0, "CYBERDYNE  //  FPR-01");
    biometric_tracked(cr, 504, 174, 8.5, 0xa98692, 0, 1.4, 2, "PASSWORD FALLBACK");
    cairo_restore(cr);
}
#endif
