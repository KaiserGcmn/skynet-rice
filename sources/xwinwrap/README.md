# Xwinwrap

Fork of xwinwrap.  
Xwinwrap allows you to stick an app such as a videoplayer or gif viewer to your desktop background.  
Gif as a background:

![demo gif](https://github.com/mmhobi7/xwinwrap/blob/readme/demo-gif.gif)

Video as a background (it is much smoother than the gif would make it appear):

![demo gif](https://github.com/mmhobi7/xwinwrap/blob/readme/demo-video.gif)

### Installing

```
sudo apt-get install xorg-dev build-essential libx11-dev x11proto-xext-dev libxrender-dev libxext-dev
git clone https://github.com/mmhobi7/xwinwrap.git
cd xwinwrap
make
sudo make install
make clean
```

### Uninstalling 

```
cd /path/to/xwinwrap
sudo make uninstall
cd ..
rm -r xwinwrap
```

### Usage

```
Usage: 
    xwinwrap [OPTIONS...] -- <video-player> [VIDEO-PLAYER OPTIONS...] <video-file>
 
Options:
             -g {w}x{h}+{x}+{y}    
                     - Specify Geometry (w=width, h=height, x=x-coord,
                       y=y-coord. ex: -g 640x480+100+100)
             -ni     - Ignore Input
             -argb   - RGB
             -fdt    - Force WID window a desktop type window
             -fs     - Full Screen
             -un     - Undecorated
             -s      - Sticky
             -st     - Skip Taskbar
             -sp     - Skip Pager
             -a      - Above
             -b      - Below
             -nf     - No Focus
             -o      - Opacity value between 0 to 1 (ex: -o 0.20)
             -sh     - Shape of window (choose between rectangle, circle or
                       triangle. Default is rectangle)
             -ov     - Set override_redirect flag (For seamless desktop
                       background integration in non-fullscreenmode) (can cause
                       artifacts on some environments)
             -ovr    - Set override_redirect flag on root window (For seamless
                       desktop background integration in fullscreenmode)
             -d      - Daemonize
             -pause-hidden SOCKET
                     - Pause mpv through its IPC socket while fully obscured
             -debug  - Enable debug messages
```
Example

`xwinwrap -g 400x400 -ni -s -nf -b -un -argb -sh circle -- gifview -w WID mygif.gif -a`

`nice xwinwrap -b -s -fs -st -sp -nf -ov -fdt -- mpv -wid WID --really-quiet --framedrop=vo --no-audio --panscan="1.0" /path/to/your/video`

### Local wallpaper power saving

The optional Linux-specific `-pause-hidden SOCKET` flag consumes X11 visibility
events in the existing wrapper process. A fully obscured or unmapped wallpaper
pauses mpv through its Unix IPC socket; partial or full visibility resumes it.
Pass the same socket path to mpv's `--input-ipc-server=SOCKET`. The bundled
`dwm-wallpaper` helper already supplies both arguments and must be installed
with this version of xwinwrap.

The wrapper requests `NotUseful` backing store so Xorg reports actual coverage,
retains initial visibility events, and waits on X11 plus a `signalfd` for child
exit. It retries IPC only while a pause/resume command has not been acknowledged;
once applied, it blocks without periodic wakeups. A 100 ms reply bound prevents
a stalled IPC client from blocking event handling indefinitely. mpv remains
responsive to file changes, IPC quit and forwarded termination signals.
Invocations without the new flag retain the original behavior.

This was validated on an opaque X11/DWM desktop and an isolated Xephyr server.
Transparent/composited desktops require separate validation. Display power-off
alone is not a trigger. See [wallpaper integration and tests](../../docs/WALLPAPER.md).

### Changes

* Added ability to make undecorated window
* Changed how desktop window is found
* Refactored window hints
* Add DESKTOP window type flag

----
Original source - https://launchpad.net/xwinwrap
