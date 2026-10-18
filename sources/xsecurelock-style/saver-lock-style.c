/* XSecureLock decoration, animated logo and battery: no input/authentication. */
#define _POSIX_C_SOURCE 200809L
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/Xft/Xft.h>
#include <X11/extensions/scrnsaver.h>
#include <X11/extensions/dpms.h>
#include <poll.h>
#include <time.h>
#include "battery-status.h"
#include <png.h>
#include <errno.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "skynet-logo.h"

static int xerror(Display *display, XErrorEvent *event) {
  (void)display;
  (void)event;
  _exit(0); /* A disappearing saver window must not cause retries or log spam. */
}

static void plain(void) {
  execl("/usr/libexec/xsecurelock/saver_blank", "saver_blank", (char *)NULL);
  _exit(1);
}

static XImage *load_image(Display *display, XWindowAttributes *attributes) {
  const char *path = getenv("XSECURELOCK_STYLE_IMAGE");
  if (!path || path[0] != '/') return NULL;
  png_image png = {0};
  png.version = PNG_IMAGE_VERSION;
  if (!png_image_begin_read_from_file(&png, path)) return NULL;
  if (!png.width || !png.height || png.width > 8192 || png.height > 8192 ||
      (uint64_t)png.width * png.height > 16777216) {
    png_image_free(&png);
    return NULL;
  }
  png.format = PNG_FORMAT_BGRA;
  void *pixels = malloc(PNG_IMAGE_SIZE(png));
  if (!pixels || !png_image_finish_read(&png, NULL, pixels, 0, NULL)) {
    free(pixels);
    png_image_free(&png);
    return NULL;
  }
  XImage *image = XCreateImage(display, attributes->visual, attributes->depth,
                              ZPixmap, 0, pixels, png.width, png.height, 32, 0);
  png_image_free(&png);
  if (!image) { free(pixels); return NULL; }
  /* PNG BGRA matches the installed X server's 24/32-bit TrueColor layout. */
  if (image->bits_per_pixel != 32 || image->byte_order != LSBFirst ||
      image->red_mask != 0xff0000 || image->green_mask != 0xff00 ||
      image->blue_mask != 0xff) {
    XDestroyImage(image);
    return NULL;
  }
  return image;
}

static Pixmap paint(Display *display, Window window, XWindowAttributes *attr,
                    XImage *image, Pixmap previous) {
  Pixmap pixmap = XCreatePixmap(display, window, (unsigned)attr->width,
                                (unsigned)attr->height, (unsigned)attr->depth);
  GC gc = XCreateGC(display, pixmap, 0, NULL);
  XSetForeground(display, gc, 0x000000);
  XFillRectangle(display, pixmap, gc, 0, 0, attr->width, attr->height);
  if (image) {
    int width = image->width < attr->width ? image->width : attr->width;
    int height = image->height < attr->height ? image->height : attr->height;
    XPutImage(display, pixmap, gc, image,
              (image->width-width)/2, (image->height-height)/2,
              (attr->width-width)/2, (attr->height-height)/2, width, height);
  }
  XSetWindowBackgroundPixmap(display, window, pixmap);
  XClearWindow(display, window);
  XFreeGC(display, gc);
  if (previous) XFreePixmap(display, previous);
  XFlush(display);
  return pixmap;
}

static long long now_ms(void) {
  struct timespec ts;
  if (clock_gettime(CLOCK_MONOTONIC, &ts)) return 0;
  return (long long)ts.tv_sec * 1000 + ts.tv_nsec / 1000000;
}

static int screen_is_dark(Display *display, int has_dpms,
                           XScreenSaverInfo *info) {
  if (info && XScreenSaverQueryInfo(display, DefaultRootWindow(display), info) &&
      info->state == ScreenSaverOn) return 1;
  if (has_dpms) {
    CARD16 level;
    BOOL enabled;
    if (DPMSInfo(display, &level, &enabled) && enabled && level != DPMSModeOn)
      return 1;
  }
  return 0;
}

static void paint_battery(Display *display, Window window, XWindowAttributes *attr,
                          Pixmap pixmap, XftFont *font, const char *label) {
  if (!font || attr->width < 480 || attr->height < 160) return;
  /* The terminal theme has a plain black top margin, away from authentication. */
  int left = attr->width - 460;
  GC gc = XCreateGC(display, pixmap, 0, NULL);
  XSetForeground(display, gc, 0x000000);
  XFillRectangle(display, pixmap, gc, left, 16, 444, 42);
  XFreeGC(display, gc);
  XftColor color;
  if (*label && XftColorAllocName(display, attr->visual, attr->colormap,
                                  "#bbbbbb", &color)) {
    XftDraw *draw = XftDrawCreate(display, pixmap, attr->visual, attr->colormap);
    if (draw) {
      XGlyphInfo extents;
      XftTextExtentsUtf8(display, font, (const FcChar8 *)label,
                        (int)strlen(label), &extents);
      XftDrawStringUtf8(draw, &color, font, attr->width - 28 - extents.xOff,
                        28 + font->ascent, (const FcChar8 *)label, (int)strlen(label));
      XftDrawDestroy(draw);
    }
    XftColorFree(display, attr->visual, attr->colormap, &color);
  }
  XClearArea(display, window, left, 16, 444, 42, False);
  XFlush(display);
}

int main(void) {
  const char *value = getenv("XSCREENSAVER_WINDOW");
  if (!value || !*value || *value == '-') plain();
  errno = 0;
  char *end;
  unsigned long id = strtoul(value, &end, 0);
  if (errno || *end || !id || id > UINT32_MAX) plain();
  Display *display = XOpenDisplay(NULL);
  if (!display) plain();
  XSetErrorHandler(xerror);
  XWindowAttributes attr;
  if (!XGetWindowAttributes(display, id, &attr) || attr.root == id ||
      attr.class != InputOutput || attr.visual->class != TrueColor ||
      (attr.depth != 24 && attr.depth != 32)) {
    XCloseDisplay(display);
    plain();
  }
  XImage *image = load_image(display, &attr);
  XSelectInput(display, id, StructureNotifyMask);
  Pixmap pixmap = paint(display, id, &attr, image, None);
  XftFont *font = XftFontOpenName(display, XScreenNumberOfScreen(attr.screen),
                                 "JetBrains Mono:style=Regular:size=12");
  char label[128];
  battery_label(label, sizeof(label));
  paint_battery(display, id, &attr, pixmap, font, label);
  Logo logo = {0};
  logo_init(display, id, &attr, image, pixmap, &logo);
  int event_base, error_base;
  int has_dpms = DPMSQueryExtension(display, &event_base, &error_base) &&
                 DPMSCapable(display);
  XScreenSaverInfo *screen_info = NULL;
  if (XScreenSaverQueryExtension(display, &event_base, &error_base))
    screen_info = XScreenSaverAllocInfo();
  long long started = now_ms(), next_check = started + 1000;
  long long next_frame = started, next_power_check = started;
  int dark = 0, mapped = attr.map_state == IsViewable;
  int alive = 1;
  while (alive) {
    /* Refresh live AC/battery state every second; repaint only on a change. */
    long long now = now_ms();
    if (now >= next_power_check) {
      int was_dark = dark;
      dark = screen_is_dark(display, has_dpms, screen_info);
      if (was_dark && !dark) next_check = now;
      next_power_check = now + 250;
    }
    if (now >= next_check) {
      char updated[sizeof(label)];
      battery_label(updated, sizeof(updated));
      if (strcmp(updated, label)) {
        memcpy(label, updated, sizeof(label));
        paint_battery(display, id, &attr, pixmap, font, label);
      }
      next_check = now + 1000;
    }
    int events = 0;
    while (XPending(display) && events++ < 64) {
      XEvent event;
      XNextEvent(display, &event);
      if (event.type == DestroyNotify) { alive = 0; break; }
      if (event.type == MapNotify) { mapped = 1; next_check = next_frame = now_ms(); }
      if (event.type == UnmapNotify) mapped = 0;
      if (event.type == ConfigureNotify && event.xconfigure.width > 0 &&
          event.xconfigure.height > 0 &&
          (event.xconfigure.width != attr.width || event.xconfigure.height != attr.height)) {
        attr.width = event.xconfigure.width;
        attr.height = event.xconfigure.height;
        logo_destroy(display, &logo);
        pixmap = paint(display, id, &attr, image, pixmap);
        paint_battery(display, id, &attr, pixmap, font, label);
        logo_init(display, id, &attr, image, pixmap, &logo);
        next_frame = now_ms();
      }
    }
    if (!alive) break;
    now = now_ms();
    int animate = mapped && !dark && logo_visible(&logo, &attr);
    if (animate && now >= next_frame) {
      logo_draw(display, id, &attr, &logo, (double)(now - started));
      /* About 30 fps, no backlog or catch-up burst after a pause. */
      next_frame = now_ms() + 33;
    }
    long long deadline = next_check < next_power_check ? next_check : next_power_check;
    if (animate && next_frame < deadline) deadline = next_frame;
    long long wait_ms = deadline - now_ms();
    if (wait_ms < 0) wait_ms = 0;
    if (wait_ms > 10000) wait_ms = 10000;
    struct pollfd connection = {ConnectionNumber(display), POLLIN, 0};
    if (!XPending(display)) {
      int result = poll(&connection, 1, (int)wait_ms);
      if ((result < 0 && errno != EINTR) ||
          (connection.revents & (POLLERR | POLLHUP | POLLNVAL))) break;
    }
  }
  if (font) XftFontClose(display, font);
  if (image) XDestroyImage(image);
  if (screen_info) XFree(screen_info);
  logo_destroy(display, &logo);
  XFreePixmap(display, pixmap);
  XCloseDisplay(display);
  return 0;
}
