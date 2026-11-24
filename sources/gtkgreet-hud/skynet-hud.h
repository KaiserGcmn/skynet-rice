/* Live SKYNET HUD behind the GTK login screen.
 *
 * The widgets, geometry, sampling and easing come from the lock screen's
 * cyber-hud.h (built without its X11 parts): CPU chip and readouts, memory
 * trace, load bars, subsystem states, battery ring, network graph,
 * thermometers, ticker and edge scanners. They show only aggregate counters
 * (CPU/memory/swap/disk load, byte rates, hardware temperatures, battery);
 * no host, user, address, device, interface or process names.
 *
 * The static frames are a pre-rendered 1920x1200 image
 * (render-cyberpunk.py --blank); without it the live parts are drawn on
 * black. The artwork is scaled to fit each monitor and centred. Only the
 * regions that are due are invalidated, so GTK repaints small rectangles,
 * and only in the ~30 fps frame slots the emblem uses (skynet-logo.h): one
 * repaint per slot rather than many interleaved ones.
 * Display only: no input, files beyond the image, or authentication.
 * SPDX-License-Identifier: MIT
 */
#ifndef SKYNET_GREETER_HUD_H
#define SKYNET_GREETER_HUD_H
#include <gtk/gtk.h>
#define HUD_NO_X11
#include "../xsecurelock-style/cyber-hud.h"

#define SKYNET_HUD_ART "/usr/local/share/hud-greeter/hud-background.png"
#define SKYNET_HUD_W 1920
#define SKYNET_HUD_H 1200
#ifndef SKYNET_FRAME_SLOT_US
#define SKYNET_FRAME_SLOT_US 33333
#endif

static struct {
    Hud hud;
    cairo_surface_t *art;    /* static frames, NULL if missing */
    gint64 start;
    double t;                /* ms; starts at 1000 (hover fade needs t > 0) */
    gint64 slot;             /* last frame slot processed */
    GPtrArray *windows;      /* toplevels showing the HUD (not owned) */
} skynet_hud;

static void skynet_hud_transform(double width, double height, double *scale,
                                 double *ox, double *oy) {
    double s = MIN(width / SKYNET_HUD_W, height / SKYNET_HUD_H);
    if (s <= 0) s = 1;
    *scale = s;
    *ox = (width - SKYNET_HUD_W * s) / 2;
    *oy = (height - SKYNET_HUD_H * s) / 2;
}

/* Hover/press state of the power buttons, as GTK sees it. Keyboard focus
 * highlights like hover. Fades exactly like the lock screen. */
static void skynet_hud_buttons_state(void) {
    Hud *hud = &skynet_hud.hud;
    int hover = -1, pressed = -1;
    static const char *const keys[2] = {"reboot-button", "poweroff-button"};
    for (guint i = 0; i < skynet_hud.windows->len; ++i)
        for (int a = 0; a < 2; ++a) {
            GtkWidget *b = g_object_get_data(G_OBJECT(g_ptr_array_index(skynet_hud.windows, i)), keys[a]);
            if (!b) continue;
            GtkStateFlags f = gtk_widget_get_state_flags(b);
            if (f & GTK_STATE_FLAG_ACTIVE) pressed = a;
            if ((f & GTK_STATE_FLAG_PRELIGHT) || gtk_widget_has_visible_focus(b)) hover = a;
        }
    if (pressed >= 0) hover = pressed;
    for (int a = 0; a < 2; ++a)
        if ((hover == a) != (hud->power.hover == a)) {
            hud->hover_from[a] = hud_hover_mix(hud, a, skynet_hud.t);
            hud->hover_t0[a] = skynet_hud.t;
        }
    hud->power.hover = hover;
    hud->power.pressed = pressed;
}

static void skynet_hud_queue(GtkWidget *window, const HudRegion *g) {
    double s, ox, oy;
    skynet_hud_transform(gtk_widget_get_allocated_width(window),
                         gtk_widget_get_allocated_height(window), &s, &ox, &oy);
    int x = (int)floor(ox + g->ax * s) - 1, y = (int)floor(oy + g->ay * s) - 1;
    int w = (int)ceil(g->w * s) + 3, h = (int)ceil(g->h * s) + 3;
    gtk_widget_queue_draw_area(window, x, y, w, h);
}

/* Frame-clock tick of every HUD window; the work runs once per slot. */
static gboolean skynet_hud_tick(GtkWidget *widget, GdkFrameClock *clock, gpointer unused) {
    Hud *hud = &skynet_hud.hud;
    gint64 now = gdk_frame_clock_get_frame_time(clock), slot = now / SKYNET_FRAME_SLOT_US;
    if (slot == skynet_hud.slot) return G_SOURCE_CONTINUE;
    skynet_hud.slot = slot;
    double t = (now - skynet_hud.start) / 1000.0 + 1000;
    skynet_hud.t = t;
    if (!hud->ready) return G_SOURCE_CONTINUE;
    hud_update(hud, t);
    for (int i = 0; i < HUD_REGIONS; ++i) {
        HudRegion *g = &hud->region[i];
        if (!g->w || t + 1 < g->next) continue;  /* slots are 33.3 ms */
        if (i == 1) {  /* memory trace: only when its content changes */
            int key = hud_hex_key(t);
            if (key == hud->hex_key) continue;
            hud->hex_key = key;
        }
        g->next = t + g->period;
        for (guint k = 0; k < skynet_hud.windows->len; ++k)
            skynet_hud_queue(g_ptr_array_index(skynet_hud.windows, k), g);
    }
    skynet_hud_buttons_state();
    static const char *const keys[2] = {"reboot-button", "poweroff-button"};
    for (guint k = 0; k < skynet_hud.windows->len; ++k)
        for (int a = 0; a < 2; ++a) {
            GtkWidget *b = g_object_get_data(G_OBJECT(g_ptr_array_index(skynet_hud.windows, k)), keys[a]);
            if (b) gtk_widget_queue_draw(b);
        }
    return G_SOURCE_CONTINUE;
}

static gboolean skynet_hud_draw(GtkWidget *window, cairo_t *cr, gpointer unused) {
    Hud *hud = &skynet_hud.hud;
    double s, ox, oy;
    skynet_hud_transform(gtk_widget_get_allocated_width(window),
                         gtk_widget_get_allocated_height(window), &s, &ox, &oy);
    cairo_save(cr);
    cairo_set_source_rgb(cr, 0, 0, 0);
    cairo_paint(cr);
    cairo_translate(cr, ox, oy);
    cairo_scale(cr, s, s);
    if (skynet_hud.art) {
        cairo_set_source_surface(cr, skynet_hud.art, 0, 0);
        if (s == 1) cairo_pattern_set_filter(cairo_get_source(cr), CAIRO_FILTER_NEAREST);
        cairo_paint(cr);
    }
    if (hud->ready) {
        double x1, y1, x2, y2;
        cairo_clip_extents(cr, &x1, &y1, &x2, &y2);  /* artwork coordinates */
        cairo_set_font_options(cr, hud->font_options);
        cairo_set_tolerance(cr, .5);
        for (int i = 0; i < HUD_REGIONS; ++i) {
            const HudRegion *g = &hud->region[i];
            if (!g->w || g->ax >= x2 || g->ay >= y2 || g->ax + g->w <= x1 || g->ay + g->h <= y1)
                continue;
            cairo_save(cr);
            cairo_rectangle(cr, g->ax, g->ay, g->w, g->h);
            cairo_clip(cr);
            hud_paint(hud, i, cr, skynet_hud.t);
            cairo_restore(cr);
        }
    }
    cairo_restore(cr);
    return FALSE;  /* children (emblem, login box, buttons) draw on top */
}

/* Power buttons drawn exactly like the lock screen's. Without fonts the
 * normal GTK button (with its text label) is drawn instead. */
static gboolean skynet_hud_button_draw(GtkWidget *button, cairo_t *cr, gpointer action) {
    Hud *hud = &skynet_hud.hud;
    if (!hud->ready) return FALSE;
    cairo_save(cr);
    cairo_set_font_options(cr, hud->font_options);
    cairo_set_tolerance(cr, .5);
    hud_button(hud, cr, skynet_hud.t, GPOINTER_TO_INT(action), 0, 0,
               gtk_widget_get_allocated_width(button), gtk_widget_get_allocated_height(button));
    cairo_restore(cr);
    return TRUE;
}

static void skynet_hud_start(void) {
    if (skynet_hud.windows) return;
    Hud *hud = &skynet_hud.hud;
    skynet_hud.windows = g_ptr_array_new();
    skynet_hud.start = g_get_monotonic_time();
    skynet_hud.slot = -1;
    skynet_hud.t = 1000;
    const char *path = g_getenv("SKYNET_HUD_ART");
    if (!path || !*path) path = SKYNET_HUD_ART;
    skynet_hud.art = cairo_image_surface_create_from_png(path);
    if (cairo_surface_status(skynet_hud.art) ||
        cairo_image_surface_get_width(skynet_hud.art) != SKYNET_HUD_W ||
        cairo_image_surface_get_height(skynet_hud.art) != SKYNET_HUD_H) {
        g_warning("SKYNET HUD artwork unavailable: %s", path);
        cairo_surface_destroy(skynet_hud.art);
        skynet_hud.art = NULL;
    }
    hud_layout(hud);  /* the power-button region stays empty: GTK owns them */
    hud->power = (HudPowerUi){.version = 2, .pressed = -1, .hover = -1};
    if (hud_assets(hud)) {
        stats_init(&hud->stats, "");
        for (int i = 0; i < 4; ++i) hud->subsys[i] = -1;
        for (int i = 0; i < STATS_T_COUNT; ++i) hud->therm[i] = hud->therm_peak[i] = -1;
        hud->bat_pct = hud->bat_watts = -1;
        hud->stats_live = 1;
        hud->hex_key = -1;
        hud->ready = 1;
    } else {
        g_warning("SKYNET HUD fonts unavailable; showing the static frame only");
    }
}

static void skynet_hud_window_gone(GtkWidget *window, gpointer unused) {
    g_ptr_array_remove(skynet_hud.windows, window);
}

static void skynet_hud_attach(GtkWidget *window) {
    skynet_hud_start();
    g_ptr_array_add(skynet_hud.windows, window);
    gtk_widget_set_app_paintable(window, TRUE);
    g_signal_connect(window, "draw", G_CALLBACK(skynet_hud_draw), NULL);
    g_signal_connect(window, "destroy", G_CALLBACK(skynet_hud_window_gone), NULL);
    gtk_widget_add_tick_callback(window, skynet_hud_tick, NULL, NULL);
}

/* Corner brackets and a top accent around the login box, as on the lock
 * screen's access panel. Drawn after the box's own CSS background/border. */
static gboolean skynet_hud_panel_draw(GtkWidget *panel, cairo_t *cr, gpointer unused) {
    double w = gtk_widget_get_allocated_width(panel), h = gtk_widget_get_allocated_height(panel);
    const double L = 14;
    cairo_save(cr);
    cairo_set_source_rgb(cr, 1, .25, .31);
    cairo_set_line_width(cr, 2);
    double c[4][4] = {{1, 1, 1, 1}, {w - 1, 1, -1, 1}, {1, h - 1, 1, -1}, {w - 1, h - 1, -1, -1}};
    for (int i = 0; i < 4; ++i) {
        cairo_move_to(cr, c[i][0] + c[i][2] * L, c[i][1]);
        cairo_line_to(cr, c[i][0], c[i][1]);
        cairo_line_to(cr, c[i][0], c[i][1] + c[i][3] * L);
    }
    cairo_stroke(cr);
    cairo_restore(cr);
    return FALSE;
}
#endif
