/* Display-only hardware readout. Input remains exclusively in XSecureLock. */
#ifndef SKYNET_LOCK_CONTROLS_H
#define SKYNET_LOCK_CONTROLS_H
#include <fcntl.h>
#include <signal.h>
#include <sys/prctl.h>
#include <sys/wait.h>

#ifndef LOCK_CONTROLS_HELPER
#define LOCK_CONTROLS_HELPER "/usr/local/libexec/skynet-lock-controls"
#endif

typedef struct {
  int fd, values[5], used, changed;
  pid_t pid;
  char line[128];
  XftFont *small, *large;
} Controls;

static void controls_start(Display *dpy, XWindowAttributes *attr, Controls *c) {
  memset(c, 0, sizeof(*c));
  c->fd = -1;
  for (int i = 0; i < 5; ++i) c->values[i] = -1;
  c->small = XftFontOpenName(dpy, XScreenNumberOfScreen(attr->screen),
                            "JetBrains Mono:style=Regular:size=10");
  c->large = XftFontOpenName(dpy, XScreenNumberOfScreen(attr->screen),
                            "JetBrains Mono:style=Bold:size=20");
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

static void controls_paint(Display *dpy, Window window, XWindowAttributes *attr,
                            Pixmap pixmap, Controls *c) {
  c->changed = 0;
  /* Keep the central authentication window and bottom power buttons clear. */
  if (!c->small || !c->large || attr->width < 640 || attr->height < 720) return;
  int width = attr->width - 64;
  if (width > 900) width = 900;
  int left = (attr->width - width) / 2;
  int top = attr->height - 254;
  if (top < attr->height / 2 + 206) top = attr->height / 2 + 206;
  int height = 124;
  /* At short resolutions shrink the readout, not the password UI. */
  int compact = attr->height < 900;
  if (compact) { top = attr->height - 196; height = 94; }
  GC gc = XCreateGC(dpy, pixmap, 0, NULL);
  XftDraw *draw = XftDrawCreate(dpy, pixmap, attr->visual, attr->colormap);
  if (!draw) { XFreeGC(dpy, gc); return; }
  XSetForeground(dpy, gc, 0x000000);
  XFillRectangle(dpy, pixmap, gc, left - 4, top - 24, width + 8, height + 48);
  controls_text(dpy, attr, draw, c->small, left, top - 8, "#9b777f",
                "LOCAL CONTROLS  /  HARDWARE KEYS");
  const char *titles[3] = {"01 / AUDIO", "02 / MICROPHONE", "03 / DISPLAY"};
  const char *hints[3] = {"VOLUME +/-   /   MUTE", "MIC MUTE", "BRIGHTNESS +/-"};
  int card = (width - 24) / 3;
  for (int i = 0; i < 3; ++i) {
    int x = left + i * (card + 12);
    int level = c->values[i == 0 ? 0 : (i == 1 ? 2 : 4)];
    int muted = i < 2 ? c->values[i * 2 + 1] : 0;
    XSetForeground(dpy, gc, 0x0d090b);
    XFillRectangle(dpy, pixmap, gc, x, top, card, height);
    XSetForeground(dpy, gc, 0x50202b);
    XDrawRectangle(dpy, pixmap, gc, x, top, card - 1, height - 1);
    XSetForeground(dpy, gc, 0xd92743);
    XFillRectangle(dpy, pixmap, gc, x, top, 3, 20);
    controls_text(dpy, attr, draw, c->small, x + 14, top + 22, "#c5afb3", titles[i]);
    if (i == 1) {
      /* This control only toggles mute; do not suggest adjustable gain. */
      const char *value = muted < 0 ? "--" : (muted ? "OFF" : "ON");
      controls_text(dpy, attr, draw, c->large, x + 14, top + 55,
                    muted == 0 ? "#eee6e7" : "#a98991", value);
      int indicator_y = top + (compact ? 68 : 75);
      XSetForeground(dpy, gc, muted == 0 ? 0xe62b49 : 0x66424c);
      XFillArc(dpy, pixmap, gc, x + 14, indicator_y - 1, 7, 7, 0, 360 * 64);
      controls_text(dpy, attr, draw, c->small, x + 29, indicator_y + 7,
                    muted == 0 ? "#dbb9c0" : "#9b858b",
                    muted < 0 ? "UNAVAILABLE" : (muted ? "INPUT MUTED" : "INPUT ENABLED"));
      if (!compact)
        controls_text(dpy, attr, draw, c->small, x + 14, top + 109, "#9b858b", hints[i]);
      continue;
    }
    char value[32];
    if (level < 0) snprintf(value, sizeof(value), "--");
    else snprintf(value, sizeof(value), "%d%%", level);
    controls_text(dpy, attr, draw, c->large, x + 14, top + 55,
                  muted == 1 ? "#a98991" : "#eee6e7", value);
    const char *state = level < 0 ? "N/A" : (muted == 1 ? "MUTED" : "");
    controls_text(dpy, attr, draw, c->small, x + card - 74, top + 51,
                  muted == 1 ? "#b9a4a9" : "#ff3955", state);
    int bar_y = top + (compact ? 68 : 75);
    int bar_width = card - 28;
    int count = 24, gap = 3;
    int segment = (bar_width - gap * (count - 1)) / count;
    if (segment < 1) { count = 16; segment = (bar_width-gap*(count-1))/count; }
    for (int j = 0; j < count; ++j) {
      int on = level > 0 && j * 100 < level * count;
      XSetForeground(dpy, gc, on ? (muted == 1 ? 0x66424c : 0xe62b49) : 0x2b1b20);
      XFillRectangle(dpy, pixmap, gc, x + 14 + j * (segment + gap), bar_y, segment, 5);
    }
    if (!compact)
      controls_text(dpy, attr, draw, c->small, x + 14, top + 109, "#9b858b", hints[i]);
  }
  XftDrawDestroy(draw);
  XFreeGC(dpy, gc);
  XClearArea(dpy, window, left - 4, top - 24, width + 8, height + 48, False);
  XFlush(dpy);
}

static void controls_stop(Display *dpy, Controls *c) {
  if (c->fd >= 0) close(c->fd);
  if (c->pid > 0) { kill(c->pid, SIGTERM); waitpid(c->pid, NULL, WNOHANG); }
  if (c->small) XftFontClose(dpy, c->small);
  if (c->large) XftFontClose(dpy, c->large);
}
#endif
