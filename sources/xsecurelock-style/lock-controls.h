/* Display-only hardware readout. Input remains exclusively in XSecureLock. */
#ifndef SKYNET_LOCK_CONTROLS_H
#define SKYNET_LOCK_CONTROLS_H
#include <cairo/cairo.h>
#include <fcntl.h>
#include <math.h>
#include <signal.h>
#include <sys/prctl.h>
#include <sys/wait.h>

#ifndef LOCK_CONTROLS_HELPER
#define LOCK_CONTROLS_HELPER "/usr/local/libexec/dwm-lock-controls"
#endif

typedef struct {
  int fd, values[5], used, changed;
  pid_t pid;
  char line[128];
  XftFont *small;
} Controls;

static void controls_start(Display *dpy, XWindowAttributes *attr, Controls *c) {
  memset(c, 0, sizeof(*c));
  c->fd = -1;
  for (int i = 0; i < 5; ++i) c->values[i] = -1;
  c->small = XftFontOpenName(dpy, XScreenNumberOfScreen(attr->screen),
                            "JetBrains Mono:style=Regular:size=10");
  int descriptors[2];
  if (pipe(descriptors)) return;
  pid_t parent = getpid();
  c->pid = fork();
  if (c->pid == 0) {
    /* A dead/terminated saver must never leave a background watcher behind. */
    if (prctl(PR_SET_PDEATHSIG, SIGTERM) || getppid() != parent) _exit(1);
    int nullfd = open("/dev/null", O_RDWR);
    if (nullfd < 0 || dup2(nullfd, STDIN_FILENO) < 0 ||
        dup2(descriptors[1], STDOUT_FILENO) < 0 ||
        dup2(nullfd, STDERR_FILENO) < 0) _exit(1);
    closefrom(3); /* No X11 or authentication/inhibitor descriptors in child. */
    execl(LOCK_CONTROLS_HELPER, LOCK_CONTROLS_HELPER, "--watch", (char *)NULL);
    _exit(1);
  }
  close(descriptors[1]);
  if (c->pid < 0) { close(descriptors[0]); return; }
  c->fd = descriptors[0];
  fcntl(c->fd, F_SETFD, FD_CLOEXEC);
  fcntl(c->fd, F_SETFL, O_NONBLOCK);
}

static int controls_parse(Controls *c, const char *line) {
  int values[5]; char extra;
  if (sscanf(line, "%d %d %d %d %d %c", &values[0], &values[1],
              &values[2], &values[3], &values[4], &extra) != 5) return 0;
  for (int i = 0; i < 5; ++i) {
    int maximum = (i == 1 || i == 3) ? 1 : (i == 4 ? 100 : 150);
    if (values[i] < -1 || values[i] > maximum) return 0;
  }
  if (memcmp(values, c->values, sizeof(values))) {
    memcpy(c->values, values, sizeof(values));
    c->changed = 1;
  }
  return 1;
}

static void controls_read(Controls *c) {
  if (c->fd < 0) return;
  char buffer[512]; ssize_t count;
  /* Bounded work per frame even if the producer misbehaves. */
  for (int batch = 0; batch < 4; ++batch) {
    count = read(c->fd, buffer, sizeof(buffer));
    if (count < 0) break;
    if (!count) {
      close(c->fd); c->fd = -1;
      for (int i = 0; i < 5; ++i) c->values[i] = -1;
      c->changed = 1;
      break;
    }
    for (ssize_t i = 0; i < count; ++i) {
      if (buffer[i] == '\n') {
        if (c->used < (int)sizeof(c->line) - 1) {
          c->line[c->used] = 0;
          controls_parse(c, c->line);
        }
        c->used = 0;
      } else if (c->used < (int)sizeof(c->line) - 1) {
        c->line[c->used++] = buffer[i];
      }
    }
  }
}

static void controls_text(Display *dpy, XWindowAttributes *attr, XftDraw *draw,
                          XftFont *font, int x, int y, const char *hex,
                          const char *text) {
  XftColor color;
  if (!font || !XftColorAllocName(dpy, attr->visual, attr->colormap, hex, &color)) return;
  XftDrawStringUtf8(draw, &color, font, x, y, (const FcChar8 *)text, strlen(text));
  XftColorFree(dpy, attr->visual, attr->colormap, &color);
}

static void controls_centered(Display *dpy, XWindowAttributes *attr, XftDraw *draw,
                              XftFont *font, int y, const char *color, const char *text) {
  if (!font) return;
  XGlyphInfo extent;
  XftTextExtentsUtf8(dpy, font, (const FcChar8 *)text, strlen(text), &extent);
  controls_text(dpy, attr, draw, font, (attr->width - extent.xOff) / 2, y, color, text);
}

static void controls_decor(Display *dpy, XWindowAttributes *attr, Pixmap pixmap,
                            Controls *c) {
  if (attr->width < 800 || attr->height < 900) return;
  int offset = (attr->height - 1200) / 2;
  GC gc = XCreateGC(dpy, pixmap, 0, NULL);
  XftDraw *draw = XftDrawCreate(dpy, pixmap, attr->visual, attr->colormap);
  XftFont *wordmark = XftFontOpenName(dpy, XScreenNumberOfScreen(attr->screen),
                                      "JetBrains Mono:style=Bold:size=28");
  if (draw) {
    XSetForeground(dpy, gc, 0);
    XFillRectangle(dpy, pixmap, gc, attr->width/2 - 260, offset + 326, 520, 86);
    XFillRectangle(dpy, pixmap, gc, attr->width/2 - 180, offset + 415, 360, 28);
    XFillRectangle(dpy, pixmap, gc, attr->width/2 - 280, offset + 724, 560, 31);
    XFillRectangle(dpy, pixmap, gc, attr->width/2 - 204, offset + 800, 408, 34);
    controls_centered(dpy, attr, draw, wordmark, offset + 374, "#e6dbde", "S K Y N E T");
    controls_centered(dpy, attr, draw, c->small, offset + 405, "#ab7b85", "NEURAL SYSTEMS  /  ACCESS TERMINAL");
    controls_centered(dpy, attr, draw, c->small, offset + 435, "#dbb9c0", "SESSION LOCKED  /  AUTH REQUIRED");
    controls_centered(dpy, attr, draw, c->small, offset + 747, "#b3939b", "FINGERPRINT OR PASSWORD  /  ENTER TO VERIFY");
    controls_centered(dpy, attr, draw, c->small, offset + 823, "#9c6b76", "CYBERDYNE SYSTEMS CORPORATION");
    XftDrawDestroy(draw);
  }
  if (wordmark) XftFontClose(dpy, wordmark);
  XFreeGC(dpy, gc);
}

/* ---- Cairo readout, in the HUD panel language (render-cyberpunk.py) ---- */
#define CTL_RED 0xff4050
#define CTL_RED_MID 0xc42a3e
#define CTL_RED_DIM 0x5a1520
#define CTL_RED_FAINT 0x2a0a10
#define CTL_TEXT 0x9c6b76
#define CTL_TEXT_DIM 0x6e4750
#define CTL_TEXT_HI 0xe6dbde
#define CTL_STEEL 0x8a9099
#define CTL_STEEL_DIM 0x4a5058
#define CTL_SEGMENTS 25

static void ctl_rgb(cairo_t *cr, unsigned rgb) {
  cairo_set_source_rgb(cr, ((rgb >> 16) & 255) / 255., ((rgb >> 8) & 255) / 255.,
                       (rgb & 255) / 255.);
}

/* Tracked caps; align 0 left, 1 centre, 2 right. Returns the width. */
static double ctl_text(cairo_t *cr, int bold, double size, double x, double y,
                       unsigned rgb, double spacing, int align, const char *text) {
  cairo_select_font_face(cr, "JetBrains Mono", CAIRO_FONT_SLANT_NORMAL,
                         bold ? CAIRO_FONT_WEIGHT_BOLD : CAIRO_FONT_WEIGHT_NORMAL);
  cairo_set_font_size(cr, size);
  char glyph[2] = {0, 0};
  cairo_text_extents_t e;
  double width = 0;
  size_t count = strlen(text);
  for (size_t i = 0; i < count; ++i) {
    glyph[0] = text[i];
    cairo_text_extents(cr, glyph, &e);
    width += e.x_advance + (i + 1 < count ? spacing : 0);
  }
  if (align == 1) x -= width / 2;
  else if (align == 2) x -= width;
  ctl_rgb(cr, rgb);
  for (size_t i = 0; i < count; ++i) {
    glyph[0] = text[i];
    cairo_move_to(cr, x, y);
    cairo_show_text(cr, glyph);
    cairo_text_extents(cr, glyph, &e);
    x += e.x_advance + spacing;
  }
  return width;
}

/* 16x16 line icons: 0 speaker, 1 microphone, 2 brightness. */
static void ctl_icon(cairo_t *cr, int kind, double x, double y, int off, unsigned rgb) {
  const double pi = 3.14159265358979323846;
  cairo_save(cr);
  cairo_translate(cr, x, y);
  ctl_rgb(cr, rgb);
  cairo_set_line_width(cr, 1.5);
  cairo_set_line_cap(cr, CAIRO_LINE_CAP_ROUND);
  if (kind == 0) {
    cairo_move_to(cr, 1, 5.5); cairo_line_to(cr, 4.5, 5.5); cairo_line_to(cr, 9, 1.5);
    cairo_line_to(cr, 9, 14.5); cairo_line_to(cr, 4.5, 10.5); cairo_line_to(cr, 1, 10.5);
    cairo_close_path(cr);
    cairo_fill(cr);
    if (off) {
      cairo_move_to(cr, 11.5, 5.5); cairo_line_to(cr, 15.5, 10.5);
      cairo_move_to(cr, 15.5, 5.5); cairo_line_to(cr, 11.5, 10.5);
    } else {
      cairo_arc(cr, 9, 8, 3.4, -pi / 3.2, pi / 3.2);
      cairo_new_sub_path(cr);
      cairo_arc(cr, 9, 8, 6.4, -pi / 3.2, pi / 3.2);
    }
    cairo_stroke(cr);
  } else if (kind == 1) {
    cairo_new_sub_path(cr);
    cairo_arc(cr, 8, 4, 2.6, pi, 0);
    cairo_arc(cr, 8, 8, 2.6, 0, pi);
    cairo_close_path(cr);
    cairo_stroke(cr);
    cairo_arc(cr, 8, 8, 5.4, 0, pi);
    cairo_move_to(cr, 8, 13.4); cairo_line_to(cr, 8, 15.5);
    cairo_move_to(cr, 5, 15.5); cairo_line_to(cr, 11, 15.5);
    if (off) { cairo_move_to(cr, 2, 1.5); cairo_line_to(cr, 14, 14.5); }
    cairo_stroke(cr);
  } else {
    cairo_arc(cr, 8, 8, 3.2, 0, 2 * pi);
    cairo_fill(cr);
    for (int ray = 0; ray < 8; ++ray) {
      double a = ray * pi / 4;
      cairo_move_to(cr, 8 + 5.4 * cos(a), 8 + 5.4 * sin(a));
      cairo_line_to(cr, 8 + 7.4 * cos(a), 8 + 7.4 * sin(a));
    }
    cairo_stroke(cr);
  }
  cairo_restore(cr);
}

/* Small keycap: bordered label, returns the advance including a gap. */
static double ctl_key(cairo_t *cr, double x, double y, const char *label) {
  cairo_select_font_face(cr, "JetBrains Mono", CAIRO_FONT_SLANT_NORMAL,
                         CAIRO_FONT_WEIGHT_BOLD);
  cairo_set_font_size(cr, 9.5);
  cairo_text_extents_t e;
  cairo_text_extents(cr, label, &e);
  double w = e.x_advance + 10;
  if (w < 18) w = 18;
  ctl_rgb(cr, CTL_STEEL_DIM);
  cairo_set_line_width(cr, 1);
  cairo_rectangle(cr, x + .5, y - 11.5, w - 1, 15);
  cairo_stroke(cr);
  ctl_rgb(cr, 0x14101a);
  cairo_rectangle(cr, x + 1, y + 2, w - 2, 1);
  cairo_fill(cr);
  ctl_text(cr, 1, 9.5, x + w / 2, y, CTL_STEEL, 0, 1, label);
  return w + 5;
}

static void ctl_brackets(cairo_t *cr, double x, double y, double w, double h,
                         unsigned bright, unsigned dim) {
  for (int corner = 0; corner < 4; ++corner) {
    double cx = corner & 1 ? x + w - 1 : x + 1, cy = corner & 2 ? y + h - 1 : y + 1;
    double dx = corner & 1 ? -1 : 1, dy = corner & 2 ? -1 : 1;
    ctl_rgb(cr, corner == 0 || corner == 3 ? bright : dim);
    cairo_set_line_width(cr, 2);
    cairo_move_to(cr, cx, cy + dy * 10);
    cairo_line_to(cr, cx, cy);
    cairo_line_to(cr, cx + dx * 14, cy);
    cairo_stroke(cr);
  }
}

static void ctl_card(cairo_t *cr, double x, double y, double w, double h, int index,
                     const int *values, int compact) {
  static const char *titles[3] = {"AUDIO", "MICROPHONE", "DISPLAY"};
  int level = values[index == 0 ? 0 : (index == 1 ? 2 : 4)];
  int muted = index < 2 ? values[index * 2 + 1] : 0;
  int known = index == 1 ? muted >= 0 : level >= 0;
  int quiet = !known || muted == 1;
  /* Body: faint vertical sheen, hairline frame, HUD corner brackets. */
  cairo_pattern_t *sheen = cairo_pattern_create_linear(0, y, 0, y + h);
  cairo_pattern_add_color_stop_rgb(sheen, 0, 0x10 / 255., 0x09 / 255., 0x0c / 255.);
  cairo_pattern_add_color_stop_rgb(sheen, 1, 0x07 / 255., 0x05 / 255., 0x06 / 255.);
  cairo_rectangle(cr, x, y, w, h);
  cairo_set_source(cr, sheen);
  cairo_fill(cr);
  cairo_pattern_destroy(sheen);
  ctl_rgb(cr, 0x2e1219);
  cairo_set_line_width(cr, 1);
  cairo_rectangle(cr, x + .5, y + .5, w - 1, h - 1);
  cairo_stroke(cr);
  ctl_brackets(cr, x, y, w, h, quiet ? CTL_RED_DIM : CTL_RED_MID, CTL_RED_DIM);

  /* Title row. */
  ctl_icon(cr, index, x + 14, y + 10, muted == 1, quiet ? CTL_TEXT_DIM : CTL_RED);
  ctl_text(cr, 1, 11, x + 40, y + 22, quiet ? CTL_TEXT : CTL_TEXT_HI, 1.4, 0, titles[index]);
  static const char *tags[3] = {"01", "02", "03"};
  ctl_text(cr, 0, 10, x + w - 14, y + 22, CTL_TEXT_DIM, 1, 2, tags[index]);
  ctl_rgb(cr, CTL_RED_FAINT);
  cairo_rectangle(cr, x + 14, y + 31, w - 28, 1);
  cairo_fill(cr);

  /* Value and state badge. */
  double value_y = y + (compact ? 60 : 66);
  char value[16];
  if (index == 1) snprintf(value, sizeof(value), "%s", !known ? "--" : (muted ? "OFF" : "ON"));
  else if (!known) snprintf(value, sizeof(value), "--");
  else snprintf(value, sizeof(value), "%d", level);
  double vw = ctl_text(cr, 1, compact ? 24 : 30, x + 14, value_y,
                       quiet ? 0x8a6b75 : CTL_TEXT_HI, 0, 0, value);
  if (index != 1 && known)
    ctl_text(cr, 1, 14, x + 16 + vw, value_y, quiet ? CTL_TEXT_DIM : CTL_TEXT, 0, 0, "%");
  const char *badge = !known ? "N/A" : (muted == 1 ? "MUTED" :
                      (index == 1 ? "INPUT LIVE" : (index == 0 ? "OUTPUT" : "BACKLIGHT")));
  cairo_select_font_face(cr, "JetBrains Mono", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_BOLD);
  cairo_set_font_size(cr, 9.5);
  cairo_text_extents_t e;
  cairo_text_extents(cr, badge, &e);
  int dot = known && muted != 1;
  double bw = e.x_advance + strlen(badge) * 1.2 + (dot ? 26 : 14);
  double bx = x + w - 14 - bw, by = value_y - 16;
  if (muted == 1) {
    ctl_rgb(cr, CTL_RED_MID);
    cairo_rectangle(cr, bx, by, bw, 18);
    cairo_fill(cr);
    ctl_text(cr, 1, 9.5, bx + bw / 2, by + 13, 0x14060a, 1.2, 1, badge);
  } else {
    ctl_rgb(cr, known ? CTL_RED_DIM : CTL_STEEL_DIM);
    cairo_set_line_width(cr, 1);
    cairo_rectangle(cr, bx + .5, by + .5, bw - 1, 17);
    cairo_stroke(cr);
    if (dot) {
      ctl_rgb(cr, CTL_RED);
      cairo_arc(cr, bx + 9, by + 9, 2.2, 0, 6.283185307179586);
      cairo_fill(cr);
    }
    ctl_text(cr, 1, 9.5, bx + bw / 2 + (dot ? 6 : 0), by + 13,
             known ? 0xdbb9c0 : CTL_STEEL, 1.2, 1, badge);
  }

  /* Meter: level segments with quarter ticks; the mic is a two-state switch. */
  double meter_y = y + (compact ? 70 : 78), meter_w = w - 28;
  if (index == 1) {
    double half = (meter_w - 4) / 2;
    for (int side = 0; side < 2; ++side) {
      int active = known && (side == 0 ? muted == 0 : muted == 1);
      double sx = x + 14 + side * (half + 4);
      /* Labels sit inside the switch so the key-hint row stays clear. */
      ctl_rgb(cr, active ? (side == 0 ? CTL_RED_MID : 0x4a2630) : 0x1a0d12);
      cairo_rectangle(cr, sx, meter_y - 3, half, 14);
      cairo_fill(cr);
      ctl_text(cr, 1, 8, sx + half / 2, meter_y + 7,
               active ? (side == 0 ? 0x1a0508 : 0xe6c9cf) : CTL_TEXT_DIM, 1.6, 1,
               side == 0 ? "LIVE" : "MUTED");
    }
  } else {
    double gap = 3, segment = (meter_w - gap * (CTL_SEGMENTS - 1)) / CTL_SEGMENTS;
    for (int j = 0; j < CTL_SEGMENTS; ++j) {
      int on = known && level > 0 && j * 100 < level * CTL_SEGMENTS;
      unsigned color = !on ? 0x241218 : (muted == 1 ? 0x5a3440 :
                       (j >= CTL_SEGMENTS - 5 && index == 0 ? CTL_RED : CTL_RED_MID));
      ctl_rgb(cr, color);
      cairo_rectangle(cr, x + 14 + j * (segment + gap), meter_y, segment, 8);
      cairo_fill(cr);
    }
    ctl_rgb(cr, CTL_RED_DIM);
    for (int q = 0; q <= 4; ++q) {
      double tx = x + 14 + q * (meter_w - 1) / 4;
      cairo_rectangle(cr, tx, meter_y + 11, 1, q % 2 ? 3 : 5);
    }
    cairo_fill(cr);
  }
  if (compact) return;

  /* Hardware key hints as keycaps. */
  double ky = y + h - 10, kx = x + 14;
  if (index == 0) {
    kx += ctl_key(cr, kx, ky, "-");
    kx += ctl_key(cr, kx, ky, "+");
    kx += ctl_text(cr, 0, 9.5, kx, ky, CTL_TEXT_DIM, 1, 0, "VOLUME") + 12;
    kx += ctl_key(cr, kx, ky, "MUTE");
  } else if (index == 1) {
    kx += ctl_key(cr, kx, ky, "MIC");
    ctl_text(cr, 0, 9.5, kx, ky, CTL_TEXT_DIM, 1, 0, "TOGGLE INPUT");
  } else {
    kx += ctl_key(cr, kx, ky, "-");
    kx += ctl_key(cr, kx, ky, "+");
    ctl_text(cr, 0, 9.5, kx, ky, CTL_TEXT_DIM, 1, 0, "BRIGHTNESS");
  }
}

/* Draw the whole readout into a client-side image and send it once. */
static void controls_render(cairo_t *cr, int region_w, int region_h, int width, int height,
                            const int *values, int compact) {
  ctl_rgb(cr, 0x000000);
  cairo_paint(cr);
  cairo_translate(cr, 4, 24);  /* region starts 4 px left of and 24 px above the cards */
  /* Section header, identical in form to the HUD's SEC 01..07 panels. */
  ctl_rgb(cr, CTL_RED);
  cairo_rectangle(cr, 0, -23, 3, 14);
  cairo_fill(cr);
  ctl_text(cr, 1, 12, 12, -11, CTL_TEXT_HI, 1.3, 0, "LOCAL CONTROLS  //  HARDWARE KEYS");
  ctl_text(cr, 0, 10.5, width, -11, CTL_TEXT_DIM, 0.6, 2, "SEC 08");
  ctl_rgb(cr, CTL_RED_DIM);
  cairo_rectangle(cr, 0, -3, width, 1);
  cairo_fill(cr);
  ctl_rgb(cr, CTL_RED_MID);
  cairo_rectangle(cr, 0, -3.25, 60, 1.5);
  cairo_fill(cr);
  int card = (width - 24) / 3;
  for (int i = 0; i < 3; ++i)
    ctl_card(cr, i * (card + 12), 8, card, height - 8, i, values, compact);
  (void)region_w; (void)region_h;
}

static void controls_paint(Display *dpy, Window window, XWindowAttributes *attr,
                            Pixmap pixmap, Controls *c) {
  c->changed = 0;
  /* Keep the central authentication window and bottom power buttons clear. */
  if (attr->width < 640 || attr->height < 720) return;
  int width = attr->width - 64;
  if (width > 900) width = 900;
  int left = (attr->width - width) / 2;
  int top = attr->height - 254;
  if (top < attr->height / 2 + 206) top = attr->height / 2 + 206;
  int height = 124;
  /* At short resolutions shrink the readout, not the password UI. */
  int compact = attr->height < 900;
  if (compact) { top = attr->height - 196; height = 94; }
  int rw = width + 8, rh = height + 48;
  int stride = cairo_format_stride_for_width(CAIRO_FORMAT_RGB24, rw);
  char *data = calloc((size_t)stride, (size_t)rh);
  if (!data) return;
  XImage *image = XCreateImage(dpy, attr->visual, (unsigned)attr->depth, ZPixmap, 0,
                               data, (unsigned)rw, (unsigned)rh, 32, stride);
  if (!image) { free(data); return; }
  /* Same TrueColor layout check as the HUD: Cairo RGB24 == X 32 bpp BGRX. */
  if (image->bits_per_pixel == 32 && image->byte_order == LSBFirst &&
      image->bytes_per_line == stride && image->red_mask == 0xff0000) {
    cairo_surface_t *surface = cairo_image_surface_create_for_data(
        (unsigned char *)data, CAIRO_FORMAT_RGB24, rw, rh, stride);
    cairo_t *cr = cairo_create(surface);
    cairo_font_options_t *options = cairo_font_options_create();
    cairo_font_options_set_hint_metrics(options, CAIRO_HINT_METRICS_OFF);
    cairo_set_font_options(cr, options);
    controls_render(cr, rw, rh, width, height, c->values, compact);
    cairo_font_options_destroy(options);
    cairo_destroy(cr);
    cairo_surface_flush(surface);
    cairo_surface_destroy(surface);
    GC gc = XCreateGC(dpy, pixmap, 0, NULL);
    XPutImage(dpy, pixmap, gc, image, 0, 0, left - 4, top - 24, (unsigned)rw, (unsigned)rh);
    XFreeGC(dpy, gc);
    XClearArea(dpy, window, left - 4, top - 24, (unsigned)rw, (unsigned)rh, False);
    XFlush(dpy);
  }
  XDestroyImage(image);  /* frees data */
}

static void controls_stop(Display *dpy, Controls *c) {
  if (c->fd >= 0) close(c->fd);
  if (c->pid > 0) { kill(c->pid, SIGTERM); waitpid(c->pid, NULL, WNOHANG); }
  if (c->small) XftFontClose(dpy, c->small);
}
#endif
