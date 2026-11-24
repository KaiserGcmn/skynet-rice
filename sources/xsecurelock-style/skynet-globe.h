/* Rotating SKYNET globe with a fixed emblem and wordmark.
 * Shared by the lock decoration (saver-lock-style.c via skynet-logo.h) and
 * the greeter (gtkgreet-hud/skynet-logo.h). Drawing only: no files,
 * input, network or authentication. Rendered client-side with Cairo.
 *
 * The sphere is orthographic. Because the viewer, tilt and roll are fixed
 * and the Earth only spins about its own axis, every pixel's latitude and
 * base longitude are computed once; a frame only offsets the longitude and
 * samples the land mask, so a 230 px globe costs well under a millisecond. */
#ifndef SKYNET_GLOBE_H
#define SKYNET_GLOBE_H
#include <cairo.h>
#include <math.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "skynet-globe-land.h"

#define SKYGLOBE_PI 3.14159265358979323846

#define SKYGLOBE_PERIOD_MS 30000.0 /* one full turn */
#define SKYGLOBE_TILT_DEG 18.0     /* viewer above the equator */
#define SKYGLOBE_ROLL_DEG 18.0     /* polar axis leans left, as in the artwork */
#define SKYGLOBE_GRID_DEG 15.0
#define SKYGLOBE_START_LON -32.0   /* Atlantic-centred at t = 0, as in the artwork */
#define SKYGLOBE_GLOW 9            /* outer halo width in px */

typedef struct {
  float lat, lon, glat, glon;      /* degrees; glat/glon: px per degree (inverse gradients) */
} SkyGlobePoint;

typedef struct {
  int size, count;
  double radius;
  int *offset;                     /* pixel index in the surface */
  float *cover, *rim, *shade, *glow;
  SkyGlobePoint *front, *back;
  unsigned char *map;
  cairo_surface_t *surface;        /* ARGB32, size x size: the sphere */
  cairo_surface_t *overlay;        /* ARGB32, size x size: fixed emblem */
} SkyGlobe;

static void skyglobe_free(SkyGlobe *g) {
  if (g->surface) cairo_surface_destroy(g->surface);
  if (g->overlay) cairo_surface_destroy(g->overlay);
  free(g->offset); free(g->cover); free(g->rim); free(g->shade); free(g->glow);
  free(g->front); free(g->back); free(g->map);
  memset(g, 0, sizeof(*g));
}

static void skyglobe_project(double u, double v, int back, double *lat, double *lon) {
  const double roll = SKYGLOBE_ROLL_DEG * SKYGLOBE_PI / 180, tilt = SKYGLOBE_TILT_DEG * SKYGLOBE_PI / 180;
  double ru = u * cos(roll) - v * sin(roll), rv = u * sin(roll) + v * cos(roll);
  double rr = ru * ru + rv * rv;
  if (rr > 0.999999) { double k = sqrt(0.999999 / rr); ru *= k; rv *= k; rr = 0.999999; }
  double x = ru, y = -rv, z = sqrt(1 - rr) * (back ? -1 : 1);
  *lat = asin(y * cos(tilt) + z * sin(tilt)) * 180 / SKYGLOBE_PI;
  *lon = atan2(x, z * cos(tilt) - y * sin(tilt)) * 180 / SKYGLOBE_PI;
}

static double skyglobe_wrap(double d) { return d - 360 * floor((d + 180) / 360); }

static void skyglobe_point(double u, double v, double step, int back, SkyGlobePoint *p) {
  double la, lo, lax, lox, lay, loy;
  skyglobe_project(u, v, back, &la, &lo);
  skyglobe_project(u + step, v, back, &lax, &lox);
  skyglobe_project(u, v + step, back, &lay, &loy);
  p->lat = (float)la; p->lon = (float)lo;
  p->glat = (float)(1 / fmax(1e-4, hypot(lax - la, lay - la)));
  p->glon = (float)(1 / fmax(1e-4, hypot(skyglobe_wrap(lox - lo), skyglobe_wrap(loy - lo))));
}

static void skyglobe_overlay(cairo_t *cr, double cx, double cy, double diameter);

/* Build the per-pixel tables for a globe of the given diameter. */
static int skyglobe_init(SkyGlobe *g, int diameter) {
  skyglobe_free(g);
  if (diameter < 16 || diameter > 2048) return 0;
  int size = diameter + 2 * SKYGLOBE_GLOW + 2;
  double r = diameter / 2.0, c = size / 2.0;
  int cap = 0;
  for (int y = 0; y < size; ++y)
    for (int x = 0; x < size; ++x)
      if (hypot(x + .5 - c, y + .5 - c) < r + SKYGLOBE_GLOW) ++cap;
  g->offset = malloc(sizeof(int) * cap);
  g->cover = malloc(sizeof(float) * cap); g->rim = malloc(sizeof(float) * cap);
  g->shade = malloc(sizeof(float) * cap); g->glow = malloc(sizeof(float) * cap);
  g->front = malloc(sizeof(SkyGlobePoint) * cap); g->back = malloc(sizeof(SkyGlobePoint) * cap);
  g->map = malloc(SKYGLOBE_MAP_W * SKYGLOBE_MAP_H);
  g->surface = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, size, size);
  if (!g->offset || !g->cover || !g->rim || !g->shade || !g->glow || !g->front ||
      !g->back || !g->map || cairo_surface_status(g->surface) != CAIRO_STATUS_SUCCESS) {
    skyglobe_free(g);
    return 0;
  }
  /* Decode the run-length land mask. */
  const unsigned short *run = skyglobe_land_runs;
  for (int y = 0; y < SKYGLOBE_MAP_H; ++y) {
    unsigned char *row = g->map + (size_t)y * SKYGLOBE_MAP_W, value = 0;
    int x = 0;
    for (; *run != 0xFFFF; ++run) {
      int n = *run;
      if (x + n > SKYGLOBE_MAP_W) n = SKYGLOBE_MAP_W - x;
      memset(row + x, value, (size_t)n);
      x += n;
      value = value ? 0 : 255;
    }
    ++run;
    if (x < SKYGLOBE_MAP_W) memset(row + x, 0, (size_t)(SKYGLOBE_MAP_W - x));
  }
  g->size = size; g->radius = r;
  int stride = cairo_image_surface_get_stride(g->surface) / 4, n = 0;
  for (int y = 0; y < size; ++y) {
    for (int x = 0; x < size; ++x) {
      double dx = x + .5 - c, dy = y + .5 - c, d = hypot(dx, dy);
      if (d >= r + SKYGLOBE_GLOW) continue;
      double u = dx / r, v = dy / r;
      g->offset[n] = y * stride + x;
      g->cover[n] = (float)fmin(1, fmax(0, r + .5 - d));
      g->rim[n] = (float)fmax(0, 1 - fabs(d - (r - .9)) / 1.3);
      g->shade[n] = (float)sqrt(fmax(0, 1 - fmin(1, (d * d) / (r * r))));
      g->glow[n] = d > r - 1 ? (float)(0.32 * exp(-(d - r) / 3.2)) : 0;
      skyglobe_point(u, v, 1 / r, 0, &g->front[n]);
      skyglobe_point(u, v, 1 / r, 1, &g->back[n]);
      ++n;
    }
  }
  g->count = n;
  /* The emblem never moves: draw it once. */
  g->overlay = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, size, size);
  cairo_t *cr = cairo_create(g->overlay);
  skyglobe_overlay(cr, c, c, diameter);
  int ok = cairo_status(cr) == CAIRO_STATUS_SUCCESS;
  cairo_destroy(cr);
  if (!ok) { skyglobe_free(g); return 0; }
  cairo_surface_flush(g->overlay);
  return 1;
}

/* Anti-aliased graticule coverage, ~1 px wide; meridians fade near the poles. */
static inline float skyglobe_frac(float v) {      /* degrees to the nearest line */
  float t = v * (float)(1.0 / SKYGLOBE_GRID_DEG) + 64.5f;  /* |v| < 900: stays positive */
  return fabsf(t - (float)(int)t - 0.5f) * (float)SKYGLOBE_GRID_DEG;
}
static inline float skyglobe_grid(const SkyGlobePoint *p, float spin) {
  float a = 1.0f - skyglobe_frac(p->lat) * p->glat;
  float b = 1.0f - skyglobe_frac(p->lon + spin) * p->glon;
  float pole = (82.0f - fabsf(p->lat)) * 0.1f;
  if (pole < b) b = pole;
  if (b > a) a = b;
  return a < 0 ? 0 : a > 1 ? 1 : a;
}

static inline uint32_t skyglobe_byte(float v) {
  return v <= 0 ? 0 : v >= 1 ? 255 : (uint32_t)(v * 255.0f + 0.5f);
}

/* Render the spinning sphere into g->surface. */
static void skyglobe_render(SkyGlobe *g, double elapsed_ms) {
  if (!g->surface) return;
  double turn = fmod(elapsed_ms, SKYGLOBE_PERIOD_MS) * (360.0 / SKYGLOBE_PERIOD_MS);
  /* The Earth turns eastward: the surface drifts left to right. */
  float spin = (float)skyglobe_wrap(SKYGLOBE_START_LON - turn), map_spin = spin;
  cairo_surface_flush(g->surface);
  uint32_t *px = (uint32_t *)cairo_image_surface_get_data(g->surface);
  const float kx = (float)SKYGLOBE_MAP_W / 360.0f, ky = (float)SKYGLOBE_MAP_H / 180.0f;
  const unsigned char *m = g->map;
  for (int i = 0; i < g->count; ++i) {
    float a = g->cover[i], r = 0, gr = 0, b = 0;
    if (a > 0) {
      const SkyGlobePoint *f = &g->front[i];
      float z = g->shade[i];
      /* Land: bilinear sample of the equirectangular mask. */
      /* Offset by one map width so the truncation below is a floor. */
      float fx = (f->lon + map_spin + 540.0f) * kx - 0.5f;
      float fy = (90.0f - f->lat) * ky + 0.5f;
      int x0 = (int)fx, y0 = (int)fy - 1;
      fy -= 1.0f;
      float ax = fx - (float)x0, ay = fy - (float)y0;
      int x1, y1 = y0 + 1;
      /* fx stays within one wrap of the map: lon and spin are both wrapped. */
      while (x0 < 0) x0 += SKYGLOBE_MAP_W;
      while (x0 >= SKYGLOBE_MAP_W) x0 -= SKYGLOBE_MAP_W;
      x1 = x0 + 1 == SKYGLOBE_MAP_W ? 0 : x0 + 1;
      if (y0 < 0) y0 = 0;
      if (y0 > SKYGLOBE_MAP_H - 1) y0 = SKYGLOBE_MAP_H - 1;
      if (y1 > SKYGLOBE_MAP_H - 1) y1 = SKYGLOBE_MAP_H - 1;
      const unsigned char *r0 = m + y0 * SKYGLOBE_MAP_W, *r1 = m + y1 * SKYGLOBE_MAP_W;
      float land = ((r0[x0] * (1 - ax) + r0[x1] * ax) * (1 - ay) +
                    (r1[x0] * (1 - ax) + r1[x1] * ax) * ay) * (1.0f / 255.0f);
      if (land < 0.995f) {
        /* Dark glass ocean, slightly lit toward the centre; the far-side
         * graticule shows through faintly: a hologram, not a photo. */
        r = 0.030f + 0.050f * z; gr = 0.002f; b = 0.010f + 0.012f * z;
        float back = skyglobe_grid(&g->back[i], spin) * 0.30f;
        r += 0.55f * back; gr += 0.04f * back; b += 0.08f * back;
        float grid = skyglobe_grid(f, spin) * (0.55f + 0.45f * z);
        r += (0.86f - r) * grid; gr += (0.07f - gr) * grid; b += (0.13f - b) * grid;
      }
      float lit = 0.62f + 0.38f * z;
      r += (0.98f * lit - r) * land; gr += (0.09f * lit - gr) * land; b += (0.14f * lit - b) * land;
      float rim = g->rim[i] * 0.85f;
      r += (1.00f - r) * rim; gr += (0.22f - gr) * rim; b += (0.28f - b) * rim;
    }
    /* Soft red halo outside the limb (premultiplied ARGB). */
    float glow = g->glow[i] * (1 - a);
    float oa = a + glow;
    if (oa > 1) oa = 1;
    px[g->offset[i]] = (skyglobe_byte(oa) << 24) |
                       (skyglobe_byte(fminf(r * a + 0.95f * glow, oa)) << 16) |
                       (skyglobe_byte(fminf(gr * a + 0.08f * glow, oa)) << 8) |
                       skyglobe_byte(fminf(b * a + 0.14f * glow, oa));
  }
  cairo_surface_mark_dirty(g->surface);
}

/* The three SKYNET plates (same geometry as the former rotating emblem). */
static const double skyglobe_plates[3][4][2] = {
  {{0,-104}, {62,-38}, {0,24}, {-62,-38}},
  {{-74,-32}, {-9,32}, {-9,102}, {-190,102}},
  {{74,-32}, {190,102}, {9,102}, {9,32}}
};

/* Geometric extended wordmark: strokes clipped to each letter box. */
static void skyglobe_letter(cairo_t *cr, char ch, double w, double t) {
  const double e = 0.2;  /* overshoot so the clip leaves square ends */
  switch (ch) {
  case 'S':
    cairo_move_to(cr, w + e, t / 2); cairo_line_to(cr, t / 2, t / 2);
    cairo_line_to(cr, t / 2, .5); cairo_line_to(cr, w - t / 2, .5);
    cairo_line_to(cr, w - t / 2, 1 - t / 2); cairo_line_to(cr, -e, 1 - t / 2);
    break;
  case 'K':
    cairo_move_to(cr, t / 2, -e); cairo_line_to(cr, t / 2, 1 + e);
    cairo_move_to(cr, w + e * .9, -e); cairo_line_to(cr, t * .9, .5);
    cairo_line_to(cr, w + e * .9, 1 + e);
    break;
  case 'Y':
    cairo_move_to(cr, -e * .6, -e); cairo_line_to(cr, w / 2, .52);
    cairo_line_to(cr, w + e * .6, -e);
    cairo_move_to(cr, w / 2, .5); cairo_line_to(cr, w / 2, 1 + e);
    break;
  case 'N': {
    double dx = w - t, dy = 1;
    cairo_move_to(cr, t / 2, -e); cairo_line_to(cr, t / 2, 1 + e);
    cairo_move_to(cr, w - t / 2, -e); cairo_line_to(cr, w - t / 2, 1 + e);
    cairo_move_to(cr, t / 2 - dx * e, -dy * e);
    cairo_line_to(cr, w - t / 2 + dx * e, 1 + dy * e);
    break;
  }
  case 'E':
    cairo_move_to(cr, t / 2, -e); cairo_line_to(cr, t / 2, 1 + e);
    cairo_move_to(cr, 0, t / 2); cairo_line_to(cr, w + e, t / 2);
    cairo_move_to(cr, 0, .5); cairo_line_to(cr, w - .14, .5);
    cairo_move_to(cr, 0, 1 - t / 2); cairo_line_to(cr, w + e, 1 - t / 2);
    break;
  case 'T':
    cairo_move_to(cr, -e, t / 2); cairo_line_to(cr, w + e, t / 2);
    cairo_move_to(cr, w / 2, 0); cairo_line_to(cr, w / 2, 1 + e);
    break;
  }
}

/* Fixed overlay: emblem, wordmark and underline, knocked out of the globe. */
static void skyglobe_overlay(cairo_t *cr, double cx, double cy, double diameter) {
  const double red[3] = {1.0, 0.13, 0.19};
  double s = 0.42 * diameter / 380.0;
  double oy = cy - 0.20 * diameter + 104 * s;
  cairo_save(cr);
  cairo_set_line_join(cr, CAIRO_LINE_JOIN_ROUND);
  /* Emblem: black knockout halo, then flat red plates. */
  for (int pass = 0; pass < 2; ++pass) {
    for (int p = 0; p < 3; ++p) {
      for (int k = 0; k < 4; ++k) {
        double x = cx + skyglobe_plates[p][k][0] * s, y = oy + skyglobe_plates[p][k][1] * s;
        if (k == 0) cairo_move_to(cr, x, y); else cairo_line_to(cr, x, y);
      }
      cairo_close_path(cr);
    }
    if (pass == 0) {
      cairo_set_source_rgb(cr, 0, 0, 0);
      cairo_set_line_width(cr, fmax(2.5, 0.030 * diameter));
      cairo_stroke_preserve(cr);
      cairo_fill(cr);
    } else {
      cairo_set_source_rgb(cr, red[0], red[1], red[2]);
      cairo_fill(cr);
    }
  }
  /* Wordmark band: a black plate interrupts the grid, as in the artwork. */
  const char *word = "SKYNET";
  double lw = 1.30, gap = 0.30, units = 6 * lw + 5 * gap;
  double width = 0.46 * diameter, u = width / units, h = u;
  double top = oy + 102 * s + 0.045 * diameter, left = cx - width / 2;
  double pad = 0.018 * diameter;
  cairo_set_source_rgba(cr, 0, 0, 0, 0.92);
  cairo_rectangle(cr, left - 2.2 * pad, top - pad, width + 4.4 * pad, h + 0.045 * diameter + 2 * pad);
  cairo_fill(cr);
  cairo_set_source_rgb(cr, red[0], red[1], red[2]);
  cairo_set_line_cap(cr, CAIRO_LINE_CAP_BUTT);
  cairo_set_line_join(cr, CAIRO_LINE_JOIN_MITER);
  for (int i = 0; i < 6; ++i) {
    cairo_save(cr);
    cairo_translate(cr, left + i * (lw + gap) * u, top);
    cairo_scale(cr, u, h);
    cairo_rectangle(cr, 0, 0, lw, 1);
    cairo_clip(cr);
    cairo_new_path(cr);
    skyglobe_letter(cr, word[i], lw, 0.27);
    cairo_set_line_width(cr, 0.27);
    cairo_stroke(cr);
    cairo_restore(cr);
  }
  /* Underline. */
  double uy = top + h + 0.024 * diameter;
  cairo_rectangle(cr, left, uy, width, fmax(1.2, 0.007 * diameter));
  cairo_fill(cr);
  cairo_restore(cr);
}

/* Paint the globe centred at (cx, cy); the globe must be built for diameter. */
static void skyglobe_paint(cairo_t *cr, SkyGlobe *g, double cx, double cy, double elapsed_ms) {
  if (!g->surface) return;
  skyglobe_render(g, elapsed_ms);
  cairo_save(cr);
  double x = round(cx - g->size / 2.0), y = round(cy - g->size / 2.0);
  cairo_set_source_surface(cr, g->surface, x, y);
  cairo_paint(cr);
  cairo_set_source_surface(cr, g->overlay, x, y);
  cairo_paint(cr);
  cairo_restore(cr);
}
#endif
