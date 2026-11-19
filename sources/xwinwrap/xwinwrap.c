/*
 * Copyright © 2005 Novell, Inc.
 *
 * Permission to use, copy, modify, distribute, and sell this software
 * and its documentation for any purpose is hereby granted without
 * fee, provided that the above copyright notice appear in all copies
 * and that both that copyright notice and this permission notice
 * appear in supporting documentation, and that the name of
 * Novell, Inc. not be used in advertising or publicity pertaining to
 * distribution of the software without specific, written prior permission.
 * Novell, Inc. makes no representations about the suitability of this
 * software for any purpose. It is provided "as is" without express or
 * implied warranty.
 *
 * NOVELL, INC. DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE,
 * INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS, IN
 * NO EVENT SHALL NOVELL, INC. BE LIABLE FOR ANY SPECIAL, INDIRECT OR
 * CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
 * OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT,
 * NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION
 * WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 * Author: David Reveman <davidr@novell.com>
 */

/*
 * Modified by: Shantanu Goel
 * Tech Blog: http://tech.shantanugoel.com
 * Blog: http://blog.shantanugoel.com
 * Home Page: http://tech.shantanugoel.com/projects/linux/shantz-xwinwrap
 *
 * Changelog:
 * 15-Jan-09:   1. Fixed the bug where XFetchName returning a NULL for "name"
 *                 resulted in a crash.
 *              2. Provided an option to specify the desktop window name.
 *              3. Added debug messages
 *
 * 24-Aug-08:   1. Fixed the geometry option (-g) so that it works
 *              2. Added override option (-ov), for seamless integration with
 *                 desktop like a background in non-fullscreen modes
 *              3. Added shape option (-sh), to create non-rectangular windows.
 *                 Currently supporting circlular and triangular windows
 */

/*
 * Picked up by Aaahh, https://github.com/Aaahh/xwinwrap
 */

#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/Xatom.h>
#include <X11/Xproto.h>

#include <X11/extensions/shape.h>
#include <X11/extensions/Xrender.h>

#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <stdio.h>
#include <stdbool.h>
#include <unistd.h>
#include <sys/wait.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <errno.h>
#include <poll.h>
#include <sys/signalfd.h>
#include <sys/socket.h>
#include <sys/un.h>

#define WIDTH 512
#define HEIGHT 384

#define OPAQUE 0xffffffff

#define NAME "xwinwrap"
#define VERSION "0.9"

#define ATOM(a) XInternAtom(display, #a, False)

Display *display = NULL;
int display_width;
int display_height;
int screen;

typedef enum {
  SHAPE_RECT = 0,
  SHAPE_CIRCLE,
  SHAPE_TRIG,
} win_shape;

struct window {
  Window root, window, desktop;
  Drawable drawable;
  Visual *visual;
  Colormap colourmap;

  unsigned int width;
  unsigned int height;
  int x;
  int y;
} window;

bool debug = false;

static pid_t pid = 0;

static char **childArgv = 0;
static int nChildArgv = 0;

static int addArguments(char **argv, int n) {
  char **newArgv;
  int i;

  newArgv = realloc(childArgv, sizeof(char *) * (nChildArgv + n));
  if (!newArgv)
    return 0;

  for (i = 0; i < n; i++)
    newArgv[nChildArgv + i] = argv[i];

  childArgv = newArgv;
  nChildArgv += n;

  return n;
}

static void setWindowOpacity(unsigned int opacity) {
  CARD32 o;

  o = opacity;

  XChangeProperty(display, window.window, ATOM(_NET_WM_WINDOW_OPACITY),
                  XA_CARDINAL, 32, PropModeReplace, (unsigned char *)&o, 1);
}

static void init_x11() {
  display = XOpenDisplay(NULL);
  if (!display) {
    fprintf(stderr, NAME ": Error: couldn't open display\n");
    return;
  }
  screen = DefaultScreen(display);
  display_width = DisplayWidth(display, screen);
  display_height = DisplayHeight(display, screen);
}

static int get_argb_visual(Visual **visual, int *depth) {
  XVisualInfo visual_template;
  XVisualInfo *visual_list;
  int nxvisuals = 0, i;

  visual_template.screen = screen;
  visual_list =
      XGetVisualInfo(display, VisualScreenMask, &visual_template, &nxvisuals);
  for (i = 0; i < nxvisuals; i++) {
    if (visual_list[i].depth == 32 && (visual_list[i].red_mask == 0xff0000 &&
                                       visual_list[i].green_mask == 0x00ff00 &&
                                       visual_list[i].blue_mask == 0x0000ff)) {
      *visual = visual_list[i].visual;
      *depth = visual_list[i].depth;
      if (debug)
        fprintf(stderr, "Found ARGB Visual\n");
      XFree(visual_list);
      return 1;
    }
  }
  if (debug)
    fprintf(stderr, "No ARGB Visual found");
  XFree(visual_list);
  return 0;
}

static void sigHandler(int sig) { kill(pid, sig); }

/* Optional mpv control: retain the last frame when the wallpaper is completely
 * covered. This uses the existing wrapper process and X events, not a polling
 * daemon. mpv stays responsive to IPC, file changes and normal termination. */
static bool set_mpv_pause(const char *endpoint, bool paused) {
  struct sockaddr_un address = {.sun_family = AF_UNIX};
  if (strlen(endpoint) >= sizeof(address.sun_path))
    return false;
  strcpy(address.sun_path, endpoint);
  int fd = socket(AF_UNIX, SOCK_STREAM | SOCK_CLOEXEC | SOCK_NONBLOCK, 0);
  if (fd < 0)
    return false;
  const char *command = paused
      ? "{\"command\":[\"set_property\",\"pause\",true]}\n"
      : "{\"command\":[\"set_property\",\"pause\",false]}\n";
  bool ok = connect(fd, (struct sockaddr *)&address, sizeof(address)) == 0 &&
      send(fd, command, strlen(command), MSG_NOSIGNAL) == (ssize_t)strlen(command);
  if (ok) {
    /* Keep the connection open until mpv consumes the command. Closing it
     * immediately can make mpv discard a command along with the disconnected
     * client. A stalled player must never stall X event handling. */
    struct pollfd reply = {.fd = fd, .events = POLLIN};
    char response[256];
    ssize_t length = poll(&reply, 1, 100) > 0
        ? recv(fd, response, sizeof(response) - 1, 0) : -1;
    ok = length > 0;
    if (ok) {
      response[length] = '\0';
      ok = strstr(response, "\"success\"") != NULL;
    }
  }
  close(fd);
  return ok;
}

static void wait_with_visibility(const char *endpoint, int *status) {
  sigset_t child_mask, previous_mask;
  sigemptyset(&child_mask);
  sigaddset(&child_mask, SIGCHLD);
  if (sigprocmask(SIG_BLOCK, &child_mask, &previous_mask) < 0)
    goto plain_wait;
  int child_fd = signalfd(-1, &child_mask, SFD_CLOEXEC | SFD_NONBLOCK);
  if (child_fd < 0) {
    sigprocmask(SIG_SETMASK, &previous_mask, NULL);
    goto plain_wait;
  }
  bool hidden = false;
  int applied = -1;
  struct pollfd fds[] = {
      {.fd = ConnectionNumber(display), .events = POLLIN},
      {.fd = child_fd, .events = POLLIN},
  };
  for (;;) {
    pid_t result = waitpid(pid, status, WNOHANG);
    if (result == pid || (result < 0 && errno != EINTR))
      break;
    while (XPending(display)) {
      XEvent event;
      XNextEvent(display, &event);
      if (debug)
        fprintf(stderr, "visibility event type=%d state=%d\n", event.type,
                event.type == VisibilityNotify ? event.xvisibility.state : -1);
      if (event.type == VisibilityNotify)
        hidden = event.xvisibility.state == VisibilityFullyObscured;
      else if (event.type == UnmapNotify)
        hidden = true;
    }
    if (applied != (int)hidden) {
      bool success = set_mpv_pause(endpoint, hidden);
      if (debug)
        fprintf(stderr, "mpv pause=%d accepted=%d\n", hidden, success);
      if (success)
        applied = hidden;
    }
    /* Retry while mpv creates its socket, then sleep until an X/child event. */
    int ready = poll(fds, 2, applied == (int)hidden ? -1 : 250);
    if (ready < 0 && errno == EINTR)
      continue;
    if (ready < 0 || (fds[0].revents & (POLLERR | POLLHUP | POLLNVAL))) {
      set_mpv_pause(endpoint, false);
      break;
    }
    if (fds[1].revents & POLLIN) {
      struct signalfd_siginfo info;
      while (read(child_fd, &info, sizeof(info)) == sizeof(info)) {}
    }
  }
  close(child_fd);
  sigprocmask(SIG_SETMASK, &previous_mask, NULL);
plain_wait:
  while (waitpid(pid, status, 0) < 0 && errno == EINTR) {}
}

static void usage(void) {
  fprintf(stderr, "Optional: -pause-hidden SOCKET pauses mpv while fully covered.\n");
  fprintf(stderr, "%s v%s \n", NAME, VERSION);
  fprintf(stderr, "\nUsage: %s [-g {w}x{h}+{x}+{y}] [-ni] [-argb] [-fdt]\n \
               [-fs] [-un] [-s] [-st] [-sp] [-a] [-b] [-nf] [-o OPACITY]\n \
               [-sh SHAPE] [-ov] [-ovr] [-d] [-debug] -- COMMAND ARG1...\n",
          NAME);
  fprintf(stderr, "Options:\n \
            -g      - Specify Geometry (w=width, h=height, x=x-coord,\n \
                      y=y-coord. ex: -g 640x480+100+100)\n \
            -ni     - Ignore Input\n \
            -argb   - RGB\n \
            -fdt    - Force WID window a desktop type window\n \
            -fs     - Full Screen\n \
            -un     - Undecorated\n \
            -s      - Sticky\n \
            -st     - Skip Taskbar\n \
            -sp     - Skip Pager\n \
            -a      - Above\n \
            -b      - Below\n \
            -nf     - No Focus\n \
            -o      - Opacity value between 0 to 1 (ex: -o 0.20)\n \
            -sh     - Shape of window (choose between rectangle, circle or\n \
                      triangle. Default is rectangle)\n \
            -ov     - Set override_redirect flag (For seamless desktop\n \
                      background integration in non-fullscreenmode) (can cause\n \
                      artifacts on some environments)\n \
            -ovr    - Set override_redirect flag on root window (For seamless\n \
                      desktop background integration in fullscreenmode)\n \
            -d      - Daemonize\n \
            -debug  - Enable debug messages\n");
}

static Window find_subwindow(Window win, int w, int h) {
  unsigned int i, j;
  Window troot, parent, *children;
  unsigned int n;

  /* search subwindows with same size as display or work area */

  for (i = 0; i < 10; i++) {
    XQueryTree(display, win, &troot, &parent, &children, &n);

    for (j = 0; j < n; j++) {
      XWindowAttributes attrs;

      if (XGetWindowAttributes(display, children[j], &attrs)) {
        /* Window must be mapped and same size as display or
         * work space */
        if (attrs.map_state != 0 &&
            ((attrs.width == display_width && attrs.height == display_height) ||
             (attrs.width == w && attrs.height == h))) {
          win = children[j];
          break;
        }
      }
    }

    XFree(children);
    if (j == n) {
      break;
    }
  }

  return win;
}

static Window find_desktop_window(Window *p_root, Window *p_desktop) {
  Atom type;
  int format, i;
  unsigned long nitems, bytes;
  unsigned int n;
  Window root = RootWindow(display, screen);
  Window win = root;
  Window troot, parent, *children;
  unsigned char *buf = NULL;

  if (!p_root || !p_desktop) {
    return 0;
  }

  /* some window managers set __SWM_VROOT to some child of root window */

  XQueryTree(display, root, &troot, &parent, &children, &n);
  for (i = 0; i < (int)n; i++) {
    if (XGetWindowProperty(display, children[i], ATOM(__SWM_VROOT), 0, 1, False,
                           XA_WINDOW, &type, &format, &nitems, &bytes,
                           &buf) == Success &&
        type == XA_WINDOW) {
      win = *(Window *)buf;
      XFree(buf);
      XFree(children);
      if (debug) {
        fprintf(stderr,
                NAME ": desktop window (%lx) found from __SWM_VROOT property\n",
                win);
      }
      fflush(stderr);
      *p_root = win;
      *p_desktop = win;
      return win;
    }

    if (buf) {
      XFree(buf);
      buf = 0;
    }
  }
  XFree(children);

  /* get subwindows from root */
  win = find_subwindow(root, -1, -1);

  display_width = DisplayWidth(display, screen);
  display_height = DisplayHeight(display, screen);

  win = find_subwindow(win, display_width, display_height);

  if (buf) {
    XFree(buf);
    buf = 0;
  }

  if (win != root && debug) {
    fprintf(stderr,
            NAME ": desktop window (%lx) is subwindow of root window (%lx)\n",
            win, root);
  } else if (debug) {
    fprintf(stderr, NAME ": desktop window (%lx) is root window\n", win);
  }

  fflush(stderr);

  *p_root = root;
  *p_desktop = win;

  return win;
}

int main(int argc, char **argv) {
  char widArg[256];
  char *widArgv[] = {widArg};
  char *endArg = NULL;
  int status = 0;
  unsigned int opacity = OPAQUE;

  int i;
  bool have_argb_visual = false;
  bool noInput = false;
  bool argb = false;
  bool set_desktop_type = false;
  bool fullscreen = false;
  bool noFocus = false;
  bool override = false;
  bool overrideroot = false;
  bool undecorated = false;
  bool sticky = false;
  bool below = false;
  bool above = false;
  bool skip_taskbar = false;
  bool skip_pager = false;
  bool daemonize = false;
  const char *pause_socket = NULL;

  win_shape shape = SHAPE_RECT;
  Pixmap mask;
  GC mask_gc;
  XGCValues xgcv;

  window.width = WIDTH;
  window.height = HEIGHT;

  for (i = 1; i < argc; i++) {
    if (strcmp(argv[i], "-g") == 0) {
      if (++i < argc)
        XParseGeometry(argv[i], &window.x, &window.y, &window.width,
                       &window.height);
    } else if (strcmp(argv[i], "-ni") == 0) {
      noInput = 1;
    } else if (strcmp(argv[i], "-argb") == 0) {
      argb = true;
    } else if (strcmp(argv[i], "-fdt") == 0) {
      set_desktop_type = true;
    } else if (strcmp(argv[i], "-fs") == 0) {
      fullscreen = 1;
    } else if (strcmp(argv[i], "-un") == 0) {
      undecorated = true;
    } else if (strcmp(argv[i], "-s") == 0) {
      sticky = true;
    } else if (strcmp(argv[i], "-st") == 0) {
      skip_taskbar = true;
    } else if (strcmp(argv[i], "-sp") == 0) {
      skip_pager = true;
    } else if (strcmp(argv[i], "-a") == 0) {
      above = true;
    } else if (strcmp(argv[i], "-b") == 0) {
      below = true;
    } else if (strcmp(argv[i], "-nf") == 0) {
      noFocus = 1;
    } else if (strcmp(argv[i], "-o") == 0) {
      if (++i < argc)
        opacity = (unsigned int)(atof(argv[i]) * OPAQUE);
    } else if (strcmp(argv[i], "-sh") == 0) {
      if (++i < argc) {
        if (strcasecmp(argv[i], "circle") == 0) {
          shape = SHAPE_CIRCLE;
        } else if (strcasecmp(argv[i], "triangle") == 0) {
          shape = SHAPE_TRIG;
        }
      }
    } else if (strcmp(argv[i], "-ov") == 0) {
      override = true;
    } else if (strcmp(argv[i], "-ovr") == 0) {
      overrideroot = true;
    } else if (strcmp(argv[i], "-debug") == 0) {
      debug = true;
    } else if (strcmp(argv[i], "-d") == 0) {
      daemonize = true;
    } else if (strcmp(argv[i], "-pause-hidden") == 0) {
      if (++i >= argc || strlen(argv[i]) >= sizeof(((struct sockaddr_un *)0)->sun_path)) {
        fprintf(stderr, NAME ": -pause-hidden needs a valid local socket path\n");
        return 1;
      }
      pause_socket = argv[i];
    } else if (strcmp(argv[i], "--") == 0) {
      break;
    } else {
      usage();
      return 1;
    }
  }

  if (daemonize) {
    pid_t process_id = 0;
    pid_t sid = 0;
    process_id = fork();
    if (process_id < 0) {
      fprintf(stderr, "fork failed!\n");
      exit(1);
    }

    if (process_id > 0) {
      fprintf(stderr, "pid of child process %d \n", process_id);
      exit(0);
    }
    umask(0);
    sid = setsid();
    if (sid < 0) {
      exit(1);
    }

    if (chdir("/") < 0) {
      perror("chdir");
      return 1;
    }
    if (!debug) {
      close(STDIN_FILENO);
      close(STDOUT_FILENO);
      close(STDERR_FILENO);
    }
  }

  for (i = i + 1; i < argc; i++) {
    if (strcmp(argv[i], "WID") == 0)
      addArguments(widArgv, 1);
    else
      addArguments(&argv[i], 1);
  }

  if (!nChildArgv) {
    fprintf(stderr, "%s: Error: couldn't create command line\n", argv[0]);
    usage();

    return 1;
  }

  addArguments(&endArg, 1);

  init_x11();
  if (!display)
    return 1;

  if (fullscreen || overrideroot) {
    window.x = 0;
    window.y = 0;
    window.width = DisplayWidth(display, screen);
    window.height = DisplayHeight(display, screen);
  }
  int depth = 0, flags = CWOverrideRedirect | CWBackingStore;
  Visual *visual = NULL;

  if (!find_desktop_window(&window.root, &window.desktop)) {
    fprintf(stderr, NAME ": Error: couldn't find desktop window\n");
    return 1;
  }

  if (argb && get_argb_visual(&visual, &depth)) {
    have_argb_visual = true;
    window.visual = visual;
    window.colourmap = XCreateColormap(display, DefaultRootWindow(display),
                                       window.visual, AllocNone);
  } else {
    window.visual = DefaultVisual(display, screen);
    window.colourmap = DefaultColormap(display, screen);
    depth = CopyFromParent;
    visual = CopyFromParent;
  }

  Atom xa;
  if (overrideroot) {
    /* An override_redirect True window.
     * No WM hints or button processing needed. */
    XSetWindowAttributes attrs = {ParentRelative,
                                  0L,
                                  0,
                                  0L,
                                  0,
                                  0,
                                  Always,
                                  0L,
                                  0L,
                                  False,
                                  StructureNotifyMask | ExposureMask,
                                  0L,
                                  True,
                                  0,
                                  0};

    if (have_argb_visual) {
      attrs.colormap = window.colourmap;
      flags |= CWBorderPixel | CWColormap;
    } else {
      flags |= CWBackPixel;
    }

    window.window = XCreateWindow(display, window.root, window.x, window.y,
                                  window.width, window.height, 0, depth,
                                  InputOutput, visual, flags, &attrs);
    XLowerWindow(display, window.window);
    xa = ATOM(_NET_WM_WINDOW_TYPE);

    Atom prop;
    if (set_desktop_type) {
      prop = ATOM(_NET_WM_WINDOW_TYPE_DESKTOP);
    } else {
      prop = ATOM(_NET_WM_WINDOW_TYPE_NORMAL);
    }

    XChangeProperty(display, window.window, xa, XA_ATOM, 32, PropModeReplace,
                    (unsigned char *)&prop, 1);
    fprintf(stderr, NAME ": window type - override\n");
    fflush(stderr);
  } else if (override) {
    /* An override_redirect True window.
     * No WM hints or button processing needed. */
    XSetWindowAttributes attrs = {ParentRelative,
                                  0L,
                                  0,
                                  0L,
                                  0,
                                  0,
                                  Always,
                                  0L,
                                  0L,
                                  False,
                                  StructureNotifyMask | ExposureMask,
                                  0L,
                                  True,
                                  0,
                                  0};

    if (have_argb_visual) {
      attrs.colormap = window.colourmap;
      flags |= CWBorderPixel | CWColormap;
    } else {
      flags |= CWBackPixel;
    }

    window.window = XCreateWindow(display, window.desktop, window.x, window.y,
                                  window.width, window.height, 0, depth,
                                  InputOutput, visual, flags, &attrs);
    XLowerWindow(display, window.window);

    fprintf(stderr, NAME ": window type - override\n");
    fflush(stderr);
  } else {
    XSetWindowAttributes attrs = {ParentRelative,
                                  0L,
                                  0,
                                  0L,
                                  0,
                                  0,
                                  Always,
                                  0L,
                                  0L,
                                  False,
                                  StructureNotifyMask | ExposureMask |
                                      ButtonPressMask | ButtonReleaseMask,
                                  0L,
                                  False,
                                  0,
                                  0};

    XWMHints wmHint;

    if (have_argb_visual) {
      attrs.colormap = window.colourmap;
      flags |= CWBorderPixel | CWColormap;
    } else {
      flags |= CWBackPixel;
    }

    window.window = XCreateWindow(display, window.root, window.x, window.y,
                                  window.width, window.height, 0, depth,
                                  InputOutput, visual, flags, &attrs);

    wmHint.flags = InputHint | StateHint;
    // wmHint.input = undecorated ? False : True;
    wmHint.input = !noFocus;
    wmHint.initial_state = NormalState;

    XSetWMProperties(display, window.window, NULL, NULL, argv, argc, NULL,
                     &wmHint, NULL);

    xa = ATOM(_NET_WM_WINDOW_TYPE);
    Atom prop;
    if (set_desktop_type) {
      prop = ATOM(_NET_WM_WINDOW_TYPE_DESKTOP);
    } else {
      prop = ATOM(_NET_WM_WINDOW_TYPE_NORMAL);
    }

    XChangeProperty(display, window.window, xa, XA_ATOM, 32, PropModeReplace,
                    (unsigned char *)&prop, 1);

    if (undecorated) {
      xa = ATOM(_MOTIF_WM_HINTS);
      if (xa != None) {
        long prop[5] = {2, 0, 0, 0, 0};
        XChangeProperty(display, window.window, xa, xa, 32, PropModeReplace,
                        (unsigned char *)prop, 5);
      }
    }

    /* Below other windows */
    if (below) {

      xa = ATOM(_WIN_LAYER);
      if (xa != None) {
        long prop = 0;

        XChangeProperty(display, window.window, xa, XA_CARDINAL, 32,
                        PropModeAppend, (unsigned char *)&prop, 1);
      }

      xa = ATOM(_NET_WM_STATE);
      if (xa != None) {
        Atom xa_prop = ATOM(_NET_WM_STATE_BELOW);

        XChangeProperty(display, window.window, xa, XA_ATOM, 32, PropModeAppend,
                        (unsigned char *)&xa_prop, 1);
      }
    }

    /* Above other windows */
    if (above) {

      xa = ATOM(_WIN_LAYER);
      if (xa != None) {
        long prop = 6;

        XChangeProperty(display, window.window, xa, XA_CARDINAL, 32,
                        PropModeAppend, (unsigned char *)&prop, 1);
      }

      xa = ATOM(_NET_WM_STATE);
      if (xa != None) {
        Atom xa_prop = ATOM(_NET_WM_STATE_ABOVE);

        XChangeProperty(display, window.window, xa, XA_ATOM, 32, PropModeAppend,
                        (unsigned char *)&xa_prop, 1);
      }
    }

    /* Sticky */
    if (sticky) {

      xa = ATOM(_NET_WM_DESKTOP);
      if (xa != None) {
        CARD32 xa_prop = 0xFFFFFFFF;

        XChangeProperty(display, window.window, xa, XA_CARDINAL, 32,
                        PropModeAppend, (unsigned char *)&xa_prop, 1);
      }

      xa = ATOM(_NET_WM_STATE);
      if (xa != None) {
        Atom xa_prop = ATOM(_NET_WM_STATE_STICKY);

        XChangeProperty(display, window.window, xa, XA_ATOM, 32, PropModeAppend,
                        (unsigned char *)&xa_prop, 1);
      }
    }

    /* Skip taskbar */
    if (skip_taskbar) {

      xa = ATOM(_NET_WM_STATE);
      if (xa != None) {
        Atom xa_prop = ATOM(_NET_WM_STATE_SKIP_TASKBAR);

        XChangeProperty(display, window.window, xa, XA_ATOM, 32, PropModeAppend,
                        (unsigned char *)&xa_prop, 1);
      }
    }

    /* Skip pager */
    if (skip_pager) {

      xa = ATOM(_NET_WM_STATE);
      if (xa != None) {
        Atom xa_prop = ATOM(_NET_WM_STATE_SKIP_PAGER);

        XChangeProperty(display, window.window, xa, XA_ATOM, 32, PropModeAppend,
                        (unsigned char *)&xa_prop, 1);
      }
    }
  }

  if (opacity != OPAQUE)
    setWindowOpacity(opacity);

  if (noInput) {
    Region region;

    region = XCreateRegion();
    if (region) {
      XShapeCombineRegion(display, window.window, ShapeInput, 0, 0, region,
                          ShapeSet);
      XDestroyRegion(region);
    }
  }

  if (shape) {
    mask =
        XCreatePixmap(display, window.window, window.width, window.height, 1);
    mask_gc = XCreateGC(display, mask, 0, &xgcv);

    switch (shape) {
    // Nothing special to be done if it's a rectangle
    case SHAPE_CIRCLE:
      /* fill mask */
      XSetForeground(display, mask_gc, 0);
      XFillRectangle(display, mask, mask_gc, 0, 0, window.width, window.height);

      XSetForeground(display, mask_gc, 1);
      XFillArc(display, mask, mask_gc, 0, 0, window.width, window.height, 0,
               23040);
      break;

    case SHAPE_TRIG: {
      XPoint points[3] = {{0, window.height},
                          {window.width / 2, 0},
                          {window.width, window.height}};

      XSetForeground(display, mask_gc, 0);
      XFillRectangle(display, mask, mask_gc, 0, 0, window.width, window.height);

      XSetForeground(display, mask_gc, 1);
      XFillPolygon(display, mask, mask_gc, points, 3, Complex, CoordModeOrigin);
    }

    break;

    default:
      break;
    }
    /* combine */
    XShapeCombineMask(display, window.window, ShapeBounding, 0, 0, mask,
                      ShapeSet);
  }

  if (pause_socket) {
    /* Always backing-store can keep the window redirected and apparently
     * unobscured on Xorg. mpv owns the retained frame; request real visibility. */
    XSetWindowAttributes attributes = {.backing_store = NotUseful};
    XChangeWindowAttributes(display, window.window, CWBackingStore, &attributes);
    XSelectInput(display, window.window, VisibilityChangeMask | StructureNotifyMask);
  }

  XMapWindow(display, window.window);

  XSync(display, pause_socket ? False : True);

  sprintf(widArg, "0x%x", (int)window.window);

  pid = fork();

  switch (pid) {
  case -1:
    perror("fork");
    return 1;
  case 0:
    execvp(childArgv[0], childArgv);
    perror(childArgv[0]);
    exit(2);
    break;
  default:
    break;
  }

  signal(SIGTERM, sigHandler);
  signal(SIGINT, sigHandler);

  if (pause_socket) {
    wait_with_visibility(pause_socket, &status);
  } else for (;;) {
    if (waitpid(pid, &status, 0) != -1) {
      if (WIFEXITED(status))
        fprintf(stderr, "%s died, exit status %d\n", childArgv[0],
                WEXITSTATUS(status));

      break;
    }
  }

  XDestroyWindow(display, window.window);
  XCloseDisplay(display);

  return 0;
}
