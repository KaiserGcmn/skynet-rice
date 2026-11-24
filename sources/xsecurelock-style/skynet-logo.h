/* Rotating SKYNET globe (skynet-globe.h) and scanning caption; saver pixmap only.
 * Drawn client-side with Cairo into a 480x260 buffer and sent with MIT-SHM
 * PutImage (plain PutImage as a fallback), like the HUD widgets: no
 * server-side anti-aliasing, no media decoder, input or authentication. */
#ifndef SKYNET_LOGO_H
#define SKYNET_LOGO_H
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/extensions/XShm.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include "skynet-globe.h"

#define LOGO_WIDTH 480
#define LOGO_HEIGHT 260
#define LOGO_GLOBE_DIAMETER 226
#define LOGO_GLOBE_CY 118          /* glow ends above the caption strip */
#define LOGO_STRIP_Y 240            /* caption strip: y 240..260 */
#define LOGO_GLOBE_FRAME_MS (1000.0 / 15) /* slow spin: 15 fps is plenty */
#define LOGO_CAPTION_PERIOD_MS 3800.0
#define LOGO_CAPTION_BASELINE 252

typedef struct {
  SkyGlobe globe;
  cairo_surface_t *frame;        /* RGB24, shares the XImage pixels */
  cairo_font_face_t *font;
  XImage *ximage;
  XShmSegmentInfo shm;
  GC gc;
  Pixmap pixmap;                 /* window background from paint() */
  long long globe_slot;          /* last globe frame drawn, -1 = none */
  int left, top, ready, shared, pushed;
} Logo;

static void logo_destroy(Display *dpy, Logo *logo) {
  if (logo->frame) cairo_surface_destroy(logo->frame);
  if (logo->font) cairo_font_face_destroy(logo->font);
  skyglobe_free(&logo->globe);
  if (logo->ximage) {
    if (logo->shared) {
      XShmDetach(dpy, &logo->shm);
      XSync(dpy, False);
      shmdt(logo->shm.shmaddr);
      logo->ximage->data = NULL;
    }
    XDestroyImage(logo->ximage);  /* frees malloc'd data in the plain case */
  }
  if (logo->gc) XFreeGC(dpy, logo->gc);
  memset(logo, 0, sizeof(*logo));
}

static void logo_init(Display *dpy, Window window, XWindowAttributes *attr,
                       XImage *image, Pixmap pixmap, Logo *logo) {
  (void)window;
  logo_destroy(dpy, logo);
  /* The current artwork is centered, not scaled, by paint(). */
  if (!image || image->width != 1920 || image->height != 1200) return;
  logo->left = attr->width/2 - LOGO_WIDTH/2;
  logo->top = (attr->height-image->height)/2 + 64;
  int stride = cairo_format_stride_for_width(CAIRO_FORMAT_RGB24, LOGO_WIDTH);
  int major, minor;
  Bool pixmaps;
  if (XShmQueryVersion(dpy, &major, &minor, &pixmaps) && !getenv("SKYNET_HUD_NO_SHM")) {
    logo->ximage = XShmCreateImage(dpy, attr->visual, (unsigned)attr->depth, ZPixmap,
                                   NULL, &logo->shm, LOGO_WIDTH, LOGO_HEIGHT);
    if (logo->ximage && logo->ximage->bytes_per_line == stride) {
      logo->shm.shmid = shmget(IPC_PRIVATE, (size_t)stride * LOGO_HEIGHT, IPC_CREAT | 0600);
      if (logo->shm.shmid >= 0) {
        logo->shm.shmaddr = logo->ximage->data = shmat(logo->shm.shmid, NULL, 0);
        logo->shm.readOnly = True;
        if (logo->shm.shmaddr != (char *)-1 && XShmAttach(dpy, &logo->shm)) {
          XSync(dpy, False);
          logo->shared = 1;
        }
        shmctl(logo->shm.shmid, IPC_RMID, NULL);
        if (!logo->shared && logo->shm.shmaddr != (char *)-1) shmdt(logo->shm.shmaddr);
      }
    }
    if (!logo->shared && logo->ximage) {
      logo->ximage->data = NULL;
      XDestroyImage(logo->ximage);
      logo->ximage = NULL;
    }
  }
  if (!logo->ximage) {
    char *data = calloc((size_t)stride, LOGO_HEIGHT);
    if (!data) return;
    logo->ximage = XCreateImage(dpy, attr->visual, (unsigned)attr->depth, ZPixmap, 0,
                                data, LOGO_WIDTH, LOGO_HEIGHT, 32, stride);
    if (!logo->ximage) { free(data); return; }
  }
  if (logo->ximage->bits_per_pixel != 32 || logo->ximage->byte_order != LSBFirst ||
      logo->ximage->bytes_per_line != stride) {
    logo_destroy(dpy, logo);
    return;
  }
  logo->frame = cairo_image_surface_create_for_data((unsigned char *)logo->ximage->data,
                                                   CAIRO_FORMAT_RGB24, LOGO_WIDTH,
                                                   LOGO_HEIGHT, stride);
  logo->font = cairo_toy_font_face_create("JetBrains Mono", CAIRO_FONT_SLANT_NORMAL,
                                          CAIRO_FONT_WEIGHT_BOLD);
  logo->gc = XCreateGC(dpy, pixmap, 0, NULL);
  logo->pixmap = pixmap;
  if (cairo_surface_status(logo->frame) || !logo->gc ||
      !skyglobe_init(&logo->globe, LOGO_GLOBE_DIAMETER)) {
    logo_destroy(dpy, logo);
    return;
  }
  logo->globe_slot = -1;
  logo->ready = 1;
}

static int logo_visible(const Logo *logo, const XWindowAttributes *attr) {
  return logo->ready && logo->left < attr->width && logo->top < attr->height &&
         logo->left+LOGO_WIDTH > 0 && logo->top+LOGO_HEIGHT > 0;
}

static void logo_render_globe(Logo *logo, double elapsed_ms) {
  cairo_t *cr = cairo_create(logo->frame);
  cairo_rectangle(cr, 0, 0, LOGO_WIDTH, LOGO_STRIP_Y);
  cairo_clip(cr);
  cairo_set_source_rgb(cr, 0, 0, 0);
  cairo_paint(cr);
  skyglobe_paint(cr, &logo->globe, LOGO_WIDTH / 2.0, LOGO_GLOBE_CY, elapsed_ms);
  cairo_destroy(cr);
}

/* Dim caption with an independent left-to-right highlight. */
static void logo_render_caption(Logo *logo, double elapsed_ms) {
  cairo_t *cr = cairo_create(logo->frame);
  cairo_rectangle(cr, 0, LOGO_STRIP_Y, LOGO_WIDTH, LOGO_HEIGHT - LOGO_STRIP_Y);
  cairo_clip(cr);
  cairo_set_source_rgb(cr, 0, 0, 0);
  cairo_paint(cr);
  const char *caption = "CYBERDYNE SYSTEMS CORPORATION";
  cairo_set_font_face(cr, logo->font);
  cairo_set_font_size(cr, 9);
  cairo_text_extents_t ext;
  cairo_text_extents(cr, caption, &ext);
  double x = round((LOGO_WIDTH - ext.x_advance) / 2);
  cairo_set_source_rgb(cr, 0x33 / 255., 0x06 / 255., 0x0a / 255.);
  cairo_move_to(cr, x, LOGO_CAPTION_BASELINE);
  cairo_show_text(cr, caption);
  double phase = fmod(elapsed_ms, LOGO_CAPTION_PERIOD_MS) / LOGO_CAPTION_PERIOD_MS;
  cairo_rectangle(cr, round(-10 + phase * 500), LOGO_STRIP_Y, 60, LOGO_HEIGHT - LOGO_STRIP_Y);
  cairo_clip(cr);
  cairo_set_source_rgb(cr, 0xef / 255., 0xef / 255., 0xf4 / 255.);
  cairo_move_to(cr, x, LOGO_CAPTION_BASELINE);
  cairo_show_text(cr, caption);
  cairo_destroy(cr);
}

/* Paint one full frame into logo->frame (no X calls; also used by the tests). */
static void logo_render(Logo *logo, double elapsed_ms) {
  logo_render_globe(logo, elapsed_ms);
  logo_render_caption(logo, elapsed_ms);
  cairo_surface_flush(logo->frame);
}

/* Copy part of the frame (logo coordinates) to the background pixmap,
 * clipped to the window: the logo may be partly off a small screen. */
static void logo_push(Display *dpy, Window window, XWindowAttributes *attr,
                      Logo *logo, int lx, int ly, int lw, int lh) {
  int x = logo->left + lx, y = logo->top + ly, right = x + lw, bottom = y + lh;
  if (x < 0) x = 0;
  if (y < 0) y = 0;
  if (right > attr->width) right = attr->width;
  if (bottom > attr->height) bottom = attr->height;
  if (right <= x || bottom <= y) return;
  if (logo->shared)
    XShmPutImage(dpy, logo->pixmap, logo->gc, logo->ximage, x - logo->left, y - logo->top,
                 x, y, (unsigned)(right - x), (unsigned)(bottom - y), False);
  else
    XPutImage(dpy, logo->pixmap, logo->gc, logo->ximage, x - logo->left, y - logo->top,
              x, y, (unsigned)(right - x), (unsigned)(bottom - y));
  XClearArea(dpy, window, x, y, (unsigned)(right - x), (unsigned)(bottom - y), False);
}

static void logo_draw(Display *dpy, Window window, XWindowAttributes *attr,
                       Logo *logo, double elapsed_ms) {
  if (!logo_visible(logo,attr)) return;
  long long slot = (long long)(elapsed_ms / LOGO_GLOBE_FRAME_MS);
  if (!logo->pushed) {
    /* First frame replaces the artwork's old emblem across the whole area. */
    logo_render(logo, elapsed_ms);
    logo_push(dpy, window, attr, logo, 0, 0, LOGO_WIDTH, LOGO_HEIGHT);
    logo->globe_slot = slot;
    logo->pushed = 1;
  } else {
    if (slot != logo->globe_slot) {
      logo_render_globe(logo, elapsed_ms);
      logo->globe_slot = slot;
      cairo_surface_flush(logo->frame);
      int box = logo->globe.size;
      logo_push(dpy, window, attr, logo, (LOGO_WIDTH - box) / 2, 0, box + 1, LOGO_STRIP_Y);
    }
    logo_render_caption(logo, elapsed_ms);
    cairo_surface_flush(logo->frame);
    logo_push(dpy, window, attr, logo, 0, LOGO_STRIP_Y, LOGO_WIDTH, LOGO_HEIGHT - LOGO_STRIP_Y);
  }
  /* The shared buffer is rewritten next frame: wait for the server's copy. */
  if (logo->shared) XSync(dpy, False);
  else XFlush(dpy);
}
#endif
