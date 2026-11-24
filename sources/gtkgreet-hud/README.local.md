# SKYNET graphical greetd interface

Based on Debian gtkgreet 0.8-1 (binary package 0.8-1+b1), upstream GPL-3.0.
Source: https://deb.debian.org/debian/pool/main/g/gtkgreet/gtkgreet_0.8.orig.tar.gz
SHA256: e5c70219da191a60e2e009412603e05c36cee15bbbf7657dbbeaa1d21a692873

Cage runs this GTK3 front end as _greetd. Greetd and its PAM configuration
still perform authentication. The greetd IPC message format is unchanged;
the local protocol client now erases outgoing credential buffers (see below).
UI changes: native Cairo red-striped SKYNET emblem rotating about its vertical
axis once every four seconds (about 30 fps), the original 3.8-second travelling
caption highlight and a stationary SKYNET wordmark,
date/time/battery, masked password input,
readable red theme and safe systemctl reboot/poweroff buttons (F11/F12).
The drawing widget's frame callback stops while unmapped.
Sessions are read from /usr/share/xsessions and run through the existing
/usr/local/libexec/greetd/start-x wrapper. DWM is the default; Plasma remains
selectable. UID 1000's login name is prefilled and can be edited.
The selected session is displayed by name instead of a raw shell command.

/etc/greetd/config.toml invokes /usr/local/libexec/greetd/hud-greeter.
That launcher reads the system keyboard layout, creates a private runtime
directory and removes it when the greeter exits. If Cage fails, or the
installed gtkgreet version changes, it falls back to the existing themed
tuigreet command. The version check prevents silently retaining an old
locally built front end after a distribution update. Rebase/rebuild this
source against an updated gtkgreet before adjusting that guard.

As of 2026-11-11, a failed graphical launch gets up to two retries, one second
apart, before TTY fallback. Each attempt has a new private runtime; a healthy
launch gets no extra wait. Compositor errors and fallback reasons reach
syslog without redirecting GTK/authentication diagnostics into that log.
The version guard still selects TTY immediately. See
[GREETER-STARTUP.md](../../docs/GREETER-STARTUP.md) for tests and boot limits.

The login daemon is not restarted during installation. Reboot normally to
activate the changed config. No lock-screen or terminal settings are changed.

Build with `make` after installing the development packages listed in Makefile.
Build packages and test files were temporary and are not runtime requirements.
Verification: private Xvfb + Cage, fake greetd IPC for failed authentication,
cancellation, retry, masked input and DWM/Plasma session commands. These tests
do not replace a real login at the next boot. Power actions are not exercised
against the real machine during tests.


## Live AC/battery refresh — 2026-10-16

Battery labels refresh every 1000 ms in both GTK greetd and the lock decoration.
The internal BAT0 percentage is read afresh. ADP1/online takes precedence over
BAT0/status so unplugging cannot leave a stale Charging or Full label. While AC
is connected, a non-charging battery is labeled Plugged in; status is used as a
fallback only if AC information is unavailable. Invalid/absent battery data
clears the label instead of retaining the previous state. The lock decoration
also refreshes immediately on remap or when screen blanking ends.

Only the decoration's data reader and refresh timers changed. GTK authentication,
PAM, the locker core, keyboard grabs, animation and power actions are unchanged.
Tests: eleven sysfs fixture cases; live GTK-label and X11-pixel checks for unplug,
replug, percentage changes and stale status; remap refresh. Measured updates
were within one second in the private Xvfb test. No real credentials or power
actions were used. New binaries take effect the next time each screen opens.


## Native logo adaptation — 2026-10-23

The emblem described in this historical section now rotates, while the caption's
original highlight remains; see [Logo rotation](../../docs/LOGO.md).

The Skynet4.gif reference has a fixed red striped emblem and a travelling text
highlight. These are now drawn with existing Cairo/XRender/Xft primitives in the
greeter and lock decoration; no GIF/video file, decoder or media process is used.
The emblem remains still while a narrow white highlight traverses the dim red
CYBERDYNE caption. The decoration keeps its existing map/blanking checks.

Only the two `skynet-logo.h` rendering headers changed. The installed greeter
was rebuilt on top of the machine's existing Devuan and fingerprint-countdown
patch in `~/.local/share/skynet-rice/devuan-source.patch`; those patched protocol,
action, countdown and power-control sources were preserved. A stock repository
build alone does not apply that machine-local patch.

Validation used an unmapped parent window and private Xephyr display, fake greetd
IPC, and Cage/Wayland. Wrong credentials stayed rejected, the password stayed
masked, the fingerprint countdown updated, and start_session was sent only after
mock authentication success. Pixel checks confirmed the decoration animation;
its process did not grab keyboard input. The real PAM configuration, authentication
helper, locker core and greeter launcher were not changed. No real login, lock,
power action or biometric enrollment was performed. Installation takes effect
when each screen next opens; the active desktop is not restarted.


## Biometric panel — 2026-10-23

The machine-local countdown now uses `skynet-biometric.h`: a native Cairo panel
with fingerprint ridges, large seconds, twenty red segments and corner brackets.
The last three seconds have stronger emphasis without blinking. The same header
is embedded in the machine-local XSecureLock patch for identical geometry.
The existing one-second GTK clock queues panel redraws; authentication, the
10-second monotonic deadline and asynchronous greetd requests are unchanged.
The display pointer is cleared when a monitor loses its input box.

The repository remains a captured baseline: apply the existing Devuan overlay
in `~/.local/share/skynet-rice/devuan-source.patch` to a temporary source copy
before compiling the installed variant. See `docs/BIOMETRIC.md` for the exact
source layering, build targets, validation and limits.


## Credential lifetime — 2026-10-24

The inherited protocol code allocated a JSON request without releasing it,
retaining a password response until the greeter exited. Requests now use one
bounded stack buffer instead of JSON-C request objects and cached serialized
strings. JSON quoting covers quotes, backslashes, control bytes and UTF-8.
The caller's request is consumed/cleared before transport; the wire buffer is
erased immediately after sending and on failure, before waiting for a reply.
Volatile byte writes keep the erasure from being optimized away. JSON-C is
still used for response parsing. Reply size is bounded; truncated, malformed
and incomplete replies fail without reporting authentication success.

`roundtrip` now takes a mutable request pointer. The machine's asynchronous
overlay passes its owned request by pointer, clears intermediate copies and
clears the GTK entry when submitting it. Its pending request destructor retains
its existing erase operation. These measures reduce the lifetime of copies
owned by this client; they do not promise to erase every copy held by GTK, PAM,
the daemon or the kernel, or protect a compromised desktop user account.

`tests/test_greeter_protocol.py` uses only synthetic credentials and private Unix
sockets. Instrumented send/read calls verify that both the request and complete
wire payload have been erased before response reading. It covers all message
types, Unicode/escaping, maximal input, partial/interrupted writes, connection
failure and malformed/oversized/closed replies. Separate hidden X11 and
Cage/Wayland fixtures verified rejection, cancellation/retry, fingerprint status,
password fallback and session handoff only after explicit backend success.

Build the live Devuan variant with the refreshed `devuan-source.patch`; rebuilding
the captured baseline alone omits the asynchronous fingerprint interface.
Install the paired source changes together, without restarting greetd or the
active desktop. The binary is used on the next normal login screen invocation.


## Live HUD — 2026-11-21

The window background shows the lock screen's live HUD panels. They come from
`skynet-hud.h`, which uses `../xsecurelock-style/cyber-hud.h` built with
`HUD_NO_X11`. Build with both directories side by side, as
`scripts/build.py` does.

- Static frames: `/usr/local/share/hud-greeter/hud-background.png`,
  produced by `render-cyberpunk.py --blank`. Without the image, only the live
  parts are drawn, on black.
- Values shown: aggregate counters only.
- Power buttons: drawn with the lock screen's `hud_button`, with hover,
  pending and refused states. A refusal is logged instead of opening a modal
  dialog.
- Test mode: `SKYNET_GREETER_POWER_TEST` disables power commands.

Details and measurements are in docs/CYBERPUNK-STYLE.md.
